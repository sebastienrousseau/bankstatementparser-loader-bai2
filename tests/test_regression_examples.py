# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2023-2026 Sebastien Rousseau. All rights reserved.

"""Regression suite: execute every shipped example end-to-end.

Each script under ``examples/`` is run as a real subprocess, exactly as
a user would run it from the repository root. A script that crashes,
prints to stderr, or exits non-zero fails the suite — so an example can
never silently rot away from the public API.

The scripts are self-contained (they embed their own inline BAI2 sample
and use only the standard library plus the package), so no fixtures,
network, or optional extras are required.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_DIR = REPO_ROOT / "examples"

# Every example script, discovered dynamically so a newly added example
# is automatically covered (and a deleted one cannot leave a dead test).
EXAMPLE_SCRIPTS = sorted(
    p for p in EXAMPLES_DIR.glob("*.py") if "__pycache__" not in str(p)
)


def _run_example(script: Path) -> subprocess.CompletedProcess[str]:
    """Run one example script as a subprocess and return the result."""
    return subprocess.run(
        [sys.executable, str(script)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )


def test_example_scripts_discovered() -> None:
    """At least the three shipped examples are present and discovered."""
    names = {p.name for p in EXAMPLE_SCRIPTS}
    assert {
        "01_load_transactions.py",
        "02_summarize_file.py",
        "03_full_tour.py",
    } <= names


@pytest.mark.parametrize(
    "script", EXAMPLE_SCRIPTS, ids=[p.name for p in EXAMPLE_SCRIPTS]
)
def test_example_runs_clean(script: Path) -> None:
    """Every example exits 0, prints something, and writes no stderr."""
    result = _run_example(script)
    assert result.returncode == 0, (
        f"{script.name} exited {result.returncode}\n"
        f"--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
    )
    assert result.stdout.strip(), f"{script.name} printed nothing"
    assert (
        not result.stderr
    ), f"{script.name} wrote to stderr:\n{result.stderr}"


def test_full_tour_exercises_every_public_function() -> None:
    """The full-tour example names every public symbol in its output."""
    result = _run_example(EXAMPLES_DIR / "03_full_tour.py")
    assert result.returncode == 0
    for needle in (
        "summarize_bai2",
        "Bai2Summary",
        "load_bai2 (from string)",
        "load_bai2_file (from disk)",
    ):
        assert needle in result.stdout, f"missing {needle!r} in tour output"
    # Every Bai2Summary field is printed.
    for field in (
        "file_id",
        "group_count",
        "account_count",
        "transaction_count",
        "currency",
    ):
        assert field in result.stdout, f"missing summary field {field!r}"
