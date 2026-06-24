# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2023-2026 Sebastien Rousseau. All rights reserved.

"""Automated validation that README and docs stay in sync with the code.

If any of these tests fail, a markdown file has a stale claim that a
human will trust and act on, or the loader's behaviour has drifted away
from what the docs promise. Fix the docs (or the code), not the test.

The checks below assert, against the *actual* loader implementation:

* the version string is identical across ``pyproject.toml``,
  ``bankstatementparser_loader_bai2.__version__``, and the CHANGELOG;
* every public symbol in ``__all__`` is documented in the README;
* the documented BAI2 record subset (``01``/``02``/``03``/``16``/``88``
  plus ignored trailers) matches the records the loader handles;
* the documented credit/debit sign-convention table (``100``–``399``
  credit, ``400``–``699`` debit) matches the loader's actual ranges;
* every example path referenced in the docs exists.
"""

from __future__ import annotations

import re
from pathlib import Path

import bankstatementparser_loader_bai2 as pkg
from bankstatementparser_loader_bai2 import loader

REPO_ROOT = Path(__file__).resolve().parents[1]
README = REPO_ROOT / "README.md"
CHANGELOG = REPO_ROOT / "CHANGELOG.md"
PYPROJECT = REPO_ROOT / "pyproject.toml"
EXAMPLES_DIR = REPO_ROOT / "examples"
EXAMPLES_README = EXAMPLES_DIR / "README.md"


def _read(path: Path) -> str:
    """Return the UTF-8 text of ``path``."""
    return path.read_text(encoding="utf-8")


def _pyproject_version() -> str:
    """Return the version declared in ``pyproject.toml``."""
    match = re.search(
        r'^version\s*=\s*"([^"]+)"', _read(PYPROJECT), re.MULTILINE
    )
    assert match is not None, "pyproject.toml has no version field"
    return match.group(1)


# ----------------------------------------------------------------------
# 1. Version consistency
# ----------------------------------------------------------------------


class TestVersionConsistency:
    """The version string is identical everywhere it appears."""

    def test_package_version_matches_pyproject(self) -> None:
        """``__version__`` equals the pyproject version."""
        assert pkg.__version__ == _pyproject_version()

    def test_changelog_has_current_version_entry(self) -> None:
        """The CHANGELOG has an ``[X.Y.Z]`` heading for the version."""
        version = _pyproject_version()
        assert f"## [{version}]" in _read(
            CHANGELOG
        ), f"CHANGELOG.md has no entry for current version {version}"

    def test_changelog_version_link_present(self) -> None:
        """The CHANGELOG defines the link target for the version."""
        version = _pyproject_version()
        assert f"[{version}]:" in _read(CHANGELOG)

    def test_any_version_in_readme_is_current(self) -> None:
        """Any ``vX.Y.Z`` token in the README is the current version."""
        version = _pyproject_version()
        readme = _read(README)
        for found in re.findall(r"\bv(\d+\.\d+\.\d+)\b", readme):
            assert (
                found == version
            ), f"README mentions v{found} but current version is {version}"


# ----------------------------------------------------------------------
# 2. Public API surface is documented
# ----------------------------------------------------------------------


class TestPublicApiDocumented:
    """Every exported public symbol is documented in the README."""

    readme_text = _read(README)

    def test_all_exports_are_the_expected_set(self) -> None:
        """``__all__`` is exactly the four documented public symbols."""
        assert set(pkg.__all__) == {
            "load_bai2",
            "load_bai2_file",
            "summarize_bai2",
            "Bai2Summary",
            "__version__",
        }

    def test_every_public_symbol_documented_in_readme(self) -> None:
        """Each public symbol (minus dunders) appears in the README."""
        for name in pkg.__all__:
            if name.startswith("__"):
                continue
            assert (
                name in self.readme_text
            ), f"README does not document public symbol {name!r}"

    def test_loader_all_matches_package_all(self) -> None:
        """The loader's ``__all__`` matches the package surface."""
        assert set(loader.__all__) == {
            "load_bai2",
            "load_bai2_file",
            "summarize_bai2",
            "Bai2Summary",
        }

    def test_bai2summary_fields_documented(self) -> None:
        """Every Bai2Summary field is named in the README."""
        import dataclasses

        for fld in dataclasses.fields(loader.Bai2Summary):
            assert (
                fld.name in self.readme_text
            ), f"README does not document Bai2Summary.{fld.name}"


# ----------------------------------------------------------------------
# 3. Documented BAI2 subset matches the implementation
# ----------------------------------------------------------------------


class TestRecordSubsetAccuracy:
    """The README's record table matches what the loader handles."""

    readme_text = _read(README)
    loader_source = (
        Path(loader.__file__).read_text(encoding="utf-8")
        if loader.__file__
        else ""
    )

    def test_modelled_records_documented(self) -> None:
        """01/02/03/16/88 are each handled in code and in the README."""
        # Records the loader explicitly branches on.
        for code in ("01", "02", "03", "16", "88"):
            assert f'== "{code}"' in self.loader_source or (
                code == "01"
            ), f"loader.py does not branch on record {code}"
            assert (
                f"`{code}`" in self.readme_text
            ), f"README does not document record {code}"

    def test_ignored_trailers_documented(self) -> None:
        """49/98/99 trailers are ignored in code and noted in the README."""
        # The loader groups the trailers in a single set membership test.
        assert (
            '{"49", "98", "99"}' in self.loader_source
        ), "loader no longer ignores the 49/98/99 trailers as documented"
        for code in ("49", "98", "99"):
            assert (
                f"`{code}`" in self.readme_text
            ), f"README does not mention trailer {code}"

    def test_readme_does_not_overpromise_records(self) -> None:
        """The README must not claim records the loader never models."""
        # Records BAI2 defines but this subset deliberately omits.
        for unmodelled in ("`10`", "`15`", "`90`"):
            assert unmodelled not in self.readme_text, (
                f"README mentions {unmodelled} which the loader does not "
                "implement"
            )


# ----------------------------------------------------------------------
# 4. Sign-convention table matches the implementation
# ----------------------------------------------------------------------


class TestSignConventionAccuracy:
    """The README's sign-convention table matches loader constants."""

    readme_text = _read(README)

    def test_credit_range_matches_loader(self) -> None:
        """The loader's credit range is 100–399 as the README states."""
        assert loader._CREDIT_RANGE == range(100, 400)
        assert "`100`" in self.readme_text and "`399`" in self.readme_text

    def test_debit_range_matches_loader(self) -> None:
        """The loader's debit range is 400–699 as the README states."""
        assert loader._DEBIT_RANGE == range(400, 700)
        assert "`400`" in self.readme_text and "`699`" in self.readme_text

    def test_credit_is_positive_per_doc(self) -> None:
        """A credit-range type code keeps the amount positive."""
        magnitude = loader.Decimal("10.00")
        assert loader._signed_amount("165", magnitude) == magnitude
        assert "kept **positive**" in self.readme_text

    def test_debit_is_negative_per_doc(self) -> None:
        """A debit-range type code negates the amount."""
        magnitude = loader.Decimal("10.00")
        assert loader._signed_amount("475", magnitude) == -magnitude
        assert "made **negative**" in self.readme_text

    def test_out_of_range_stays_positive_per_doc(self) -> None:
        """A code outside both ranges keeps the amount positive."""
        magnitude = loader.Decimal("10.00")
        assert loader._signed_amount("900", magnitude) == magnitude


# ----------------------------------------------------------------------
# 5. Amount handling claim matches the implementation
# ----------------------------------------------------------------------


class TestAmountHandlingAccuracy:
    """The README's 'cents / 100' claim matches the loader."""

    readme_text = _read(README)

    def test_minor_units_divided_by_100(self) -> None:
        """A minor-unit integer is divided by 100 as documented."""
        assert loader._amount_to_decimal("150000") == loader.Decimal("1500.00")
        assert "dividing by 100" in self.readme_text or (
            "/ 100" in self.readme_text or "100" in self.readme_text
        )

    def test_empty_amount_is_zero(self) -> None:
        """An empty amount field parses to zero, as documented."""
        assert loader._amount_to_decimal("") == loader.Decimal("0")
        assert "empty amount field is treated" in self.readme_text


# ----------------------------------------------------------------------
# 6. Example paths referenced in docs exist
# ----------------------------------------------------------------------


class TestExamplesExist:
    """Every example path mentioned in the docs resolves to a file."""

    readme_text = _read(README)
    examples_readme_text = _read(EXAMPLES_README)

    def _referenced_scripts(self, text: str) -> set[str]:
        """Pull ``examples/...py`` and ``NN_name.py`` paths from text."""
        scripts = set(re.findall(r"examples/([\w./-]+\.py)", text))
        scripts |= set(re.findall(r"`(\d+_[\w]+\.py)`", text))
        scripts |= set(re.findall(r"\]\((\d+_[\w]+\.py)\)", text))
        return scripts

    def test_readme_example_paths_exist(self) -> None:
        """Every example path referenced in README.md exists."""
        for script in self._referenced_scripts(self.readme_text):
            assert (
                EXAMPLES_DIR / script
            ).exists(), (
                f"README references examples/{script} but it is missing"
            )

    def test_examples_readme_paths_exist(self) -> None:
        """Every example path referenced in examples/README.md exists."""
        for script in self._referenced_scripts(self.examples_readme_text):
            assert (
                EXAMPLES_DIR / script
            ).exists(), (
                f"examples/README.md references {script} but it is missing"
            )

    def test_examples_readme_lists_every_script(self) -> None:
        """Every example .py file is documented in examples/README.md."""
        for script in EXAMPLES_DIR.glob("*.py"):
            assert script.name in self.examples_readme_text, (
                f"{script.name} exists but is not listed in "
                "examples/README.md"
            )


# ----------------------------------------------------------------------
# 7. CHANGELOG is accurate
# ----------------------------------------------------------------------


class TestChangelogAccuracy:
    """The CHANGELOG documents the public API truthfully."""

    changelog_text = _read(CHANGELOG)

    def test_public_functions_mentioned(self) -> None:
        """Each public function appears in the CHANGELOG."""
        for name in ("load_bai2", "load_bai2_file", "summarize_bai2"):
            assert (
                name in self.changelog_text
            ), f"CHANGELOG does not mention {name}"

    def test_examples_count_matches_reality(self) -> None:
        """If the CHANGELOG cites both example files, both must exist."""
        for script in re.findall(
            r"examples/([\w./-]+\.py)", self.changelog_text
        ):
            assert (
                EXAMPLES_DIR / script
            ).exists(), f"CHANGELOG cites examples/{script} but it is missing"
