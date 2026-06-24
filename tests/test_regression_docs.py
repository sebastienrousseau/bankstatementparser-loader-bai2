# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2023-2026 Sebastien Rousseau. All rights reserved.

"""Regression suite: every code example in the docs must actually work.

``test_docs_accuracy`` checks that *claims* in the docs match the
codebase; this module goes further and **executes** the documented
python examples themselves:

* Every fenced ``python`` block in README.md (and any ``docs/*.md``)
  must be classified in ``BLOCK_SPECS`` below. Adding a new block to the
  docs without classifying it fails the suite — examples cannot silently
  rot.
* ``run`` blocks are executed in-process. Blocks that read a file path
  have that path materialised as a real file in a temp directory first.
* ``imports`` blocks (import-only API tours) have every import statement
  executed, so a renamed or removed public symbol still fails fast.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

# All markdown docs that may contain executable python blocks. README is
# the primary surface; docs/*.md are scanned so a future snippet there is
# caught by the "every block is classified" guard.
DOC_FILES: tuple[str, ...] = (
    "README.md",
    *sorted(
        str(p.relative_to(REPO_ROOT))
        for p in (REPO_ROOT / "docs").glob("*.md")
    ),
)

# A self-contained BAI2 payload reused by the file-reading block.
_SAMPLE_BAI2 = (
    "01,SENDER,RECEIVER,260601,1200,FILE001,,,/\n"
    "02,RCVR,ORIG,1,260601,1200,USD,/\n"
    "03,0123456789,USD,010,150000,1,,/\n"
    "16,165,150000,Z,BANKREF1,CUSTREF1,Incoming wire payment/\n"
    "88,from ACME Corp invoice 42/\n"
    "16,475,2500,Z,BANKREF2,,ATM withdrawal/\n"
    "49,152500,2/\n"
    "98,152500,1,4/\n"
    "99,152500,1,6/\n"
)


# ----------------------------------------------------------------------
# Block extraction
# ----------------------------------------------------------------------


@dataclass(frozen=True)
class DocBlock:
    """One fenced code block discovered in a markdown doc."""

    doc: str
    line: int
    lang: str
    body: str

    @property
    def location(self) -> str:
        """A ``file:line`` label used as the parametrised test id."""
        return f"{self.doc}:{self.line}"


def _extract_blocks() -> list[DocBlock]:
    """Return every fenced code block across the scanned docs."""
    blocks: list[DocBlock] = []
    for rel in DOC_FILES:
        text = (REPO_ROOT / rel).read_text(encoding="utf-8")
        for match in re.finditer(
            r"^```(\w*)\n(.*?)^```", text, re.DOTALL | re.MULTILINE
        ):
            blocks.append(
                DocBlock(
                    doc=rel,
                    line=text[: match.start()].count("\n") + 1,
                    lang=match.group(1),
                    body=match.group(2),
                )
            )
    return blocks


ALL_BLOCKS = _extract_blocks()
PYTHON_BLOCKS = [b for b in ALL_BLOCKS if b.lang == "python"]


# ----------------------------------------------------------------------
# Classification registry
# ----------------------------------------------------------------------


@dataclass(frozen=True)
class BlockSpec:
    """How to exercise one documented python block.

    ``marker`` is a substring unique to exactly one block across all
    scanned docs. ``files`` maps placeholder paths used inside the block
    to the text content that should be materialised at that path in the
    working directory before the block runs.
    """

    marker: str
    mode: str = "run"  # "run" | "imports"
    files: tuple[tuple[str, str], ...] = ()
    reason: str = ""  # why a block is imports-only
    requires: tuple[str, ...] = field(default_factory=tuple)


BLOCK_SPECS: tuple[BlockSpec, ...] = (
    # README — Quick start: load_bai2_file reads a path from disk.
    BlockSpec(
        marker='load_bai2_file("statement.bai")',
        files=(("statement.bai", _SAMPLE_BAI2),),
    ),
    # README — Quick start: in-memory load_bai2 with an inline payload.
    BlockSpec(
        marker="for txn in load_bai2(payload):",
    ),
    # README — Public API import surface.
    BlockSpec(
        marker="from bankstatementparser_loader_bai2 import (",
        mode="imports",
        reason="documents the public import surface only",
    ),
)


def _matching_blocks(spec: BlockSpec) -> list[DocBlock]:
    """Return the python blocks whose body contains ``spec.marker``."""
    return [b for b in PYTHON_BLOCKS if spec.marker in b.body]


# ----------------------------------------------------------------------
# Structural guarantees
# ----------------------------------------------------------------------


@pytest.mark.parametrize(
    "block", PYTHON_BLOCKS, ids=[b.location for b in PYTHON_BLOCKS]
)
def test_python_block_is_valid_syntax(block: DocBlock) -> None:
    """Every documented python block is syntactically valid."""
    ast.parse(block.body, filename=block.location)


def test_every_python_block_is_classified() -> None:
    """Each documented python block maps to exactly one BlockSpec."""
    unmatched = [
        b.location
        for b in PYTHON_BLOCKS
        if not any(spec.marker in b.body for spec in BLOCK_SPECS)
    ]
    assert not unmatched, (
        "Unclassified python blocks in docs (add a BlockSpec so the "
        f"example is executed by the regression suite): {unmatched}"
    )

    for spec in BLOCK_SPECS:
        matches = _matching_blocks(spec)
        assert len(matches) == 1, (
            f"BlockSpec marker {spec.marker!r} must match exactly one "
            f"block, matched {[b.location for b in matches]}"
        )


# ----------------------------------------------------------------------
# Execution
# ----------------------------------------------------------------------


def _spec_id(spec: BlockSpec) -> str:
    """Return a stable parametrise id for a BlockSpec."""
    blocks = _matching_blocks(spec)
    return blocks[0].location if blocks else spec.marker[:30]


@pytest.mark.parametrize(
    "spec", BLOCK_SPECS, ids=[_spec_id(s) for s in BLOCK_SPECS]
)
def test_documented_python_block(
    spec: BlockSpec,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Execute (or import-verify) one classified documented block."""
    blocks = _matching_blocks(spec)
    assert len(blocks) == 1
    block = blocks[0]

    if spec.mode == "imports":
        tree = ast.parse(block.body)
        import_lines = [
            ast.unparse(node)
            for node in tree.body
            if isinstance(node, ast.Import | ast.ImportFrom)
        ]
        assert import_lines, (
            f"{block.location} is imports-only ({spec.reason}) but has "
            "no imports to verify"
        )
        namespace: dict[str, object] = {}
        exec(
            compile("\n".join(import_lines), block.location, "exec"),
            namespace,
        )
        return

    monkeypatch.chdir(tmp_path)
    for placeholder, content in spec.files:
        target = tmp_path / placeholder
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    namespace = {"__name__": "bai2_doc_example"}
    exec(compile(block.body, block.location, "exec"), namespace)
    capsys.readouterr()  # examples are allowed to print
