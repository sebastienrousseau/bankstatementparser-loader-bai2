# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.37] - 2026-11-28

### Changed

- Require `bankstatementparser >= 0.0.36`, the newest core release, and
  align the version with the suite's 0.0.37 release; `poetry.lock`
  moves core to 0.0.36.
- CI: four pinned actions move to their latest releases:
  codeql-action 4.39.5, markdownlint-cli2-action 25.1.0,
  cosign-installer 4.1.4 and sbom-action 0.24.4.

### Fixed

- The suite consistency check authenticates its GitHub API request
  with the workflow token, so the shared anonymous rate limit no
  longer fails it.

## [0.0.36] - 2026-11-27

### Fixed

- A `16` amount that is not an optional sign and ASCII digits (letters,
  a decimal point, an exponent, `NaN`, non-ASCII digits) now raises
  `ValueError` naming the field. Before, letters escaped as
  `decimal.InvalidOperation`, which callers catching the documented
  `ValueError` did not expect, `NaN` surfaced as a pydantic error, and
  `1e5` or `12.50` were loaded as 1000.00 or 0.125. The conversion
  moves to `bankstatementparser_loader_bai2/_amounts.py`.
- `make mutation` ran no mutant: the suite's 100% coverage floor
  applied inside mutmut's trampoline and failed its stats run. The run
  now passes `--no-cov`, and new tests pin
  `Bai2StatementParser.get_summary` and the malformed-amount message;
  `tests/MUTATION.md` records 455 of 481 mutants killed, every survivor
  a documented equivalent.

### Added

- An Atheris fuzz target, `fuzz/fuzz_load_bai2.py`, for `load_bai2`
  and `summarize_bai2`, with a seed corpus; it fails on any exception
  but `ValueError` and on a malformed `Transaction`. CI runs it for
  120 s on every change; `make fuzz` locally.
- A MkDocs Material user manual (`mkdocs.yml`, `docs/`) with an
  mkdocstrings API reference, built with `--strict` on every pull
  request and deployed to GitHub Pages from `main`
  (`.github/workflows/docs.yml`, `make docs`). It replaces a Sphinx
  configuration that nothing built.
- `docs/POLICIES.md`, `docs/BENCHMARKS.md` (a run of
  `benches/bench_load_bai2.py` with its environment),
  `docs/COMPARISON.md`, `docs/format.md` and `docs/suite.md`.
- Signed releases: keyless cosign `.sig` and `.pem` per distribution,
  SLSA provenance
  (`bankstatementparser-loader-bai2-vX.Y.Z.intoto.jsonl`,
  slsa-github-generator 2.1.0), CycloneDX and SPDX SBOMs and a licence
  manifest on every GitHub release, and PEP 740 attestations on PyPI.
- The OpenSSF Scorecard workflow, the suite's Docs Lint workflow
  (`scripts/readme-check.sh` and markdownlint), a Security workflow
  (Bandit and `pip-audit` on the locked sets), the portfolio pull
  request template, and `.github/demo.gif` rendered by `make demo` from
  `.github/demo.tape`.
- Hash-pinned requirement sets exported from the lock
  (`requirements/{runtime,ci,fuzz,docs}.txt`, by the suite's
  `scripts/export_locked_requirements.py`) and compiled release tooling
  (`requirements/{build,sbom}.txt`).

### Changed

- Require `bankstatementparser >= 0.0.35`, the newest core release, and
  align the version with the suite's 0.0.36 release; `poetry.lock`
  moves core to 0.0.35.
- CI pins every action by commit SHA, installs only the hashed lock
  exports, and tests CPython 3.10 to 3.14 on Ubuntu, macOS and Windows.
  Write permissions sit on the jobs that need them.
- `README.md` follows the portfolio template and states the
  Apache-2.0 OR MIT licence; it no longer claims the core cannot parse
  BAI2 (it has shipped a `Bai2Parser` since 0.0.26). The suite table
  moves to `docs/suite.md`. `CODE-OF-CONDUCT.md` is now
  `CODE_OF_CONDUCT.md`, and the issue templates follow the suite kit.
- `ROADMAP.md` no longer calls v0.0.10 current; `ARCHITECTURE.md`
  lists every module and tool.

## [0.0.35] - 2026-11-26

### Added

- `scripts/check_complexity.py`, the suite's standard-library
  complexity gate, copied byte for byte from `bankstatementparser`:
  cyclomatic 10, cognitive 15, Halstead difficulty 30 and 60 lines per
  function, 500 lines per file. The 7 functions and files already over
  a ceiling are recorded in `scripts/complexity_baseline.json`; CI and
  `make check` fail when one gets worse, a new one appears, or an
  improvement is left unrecorded, so the baseline can only shrink.

### Changed

- Require `bankstatementparser >= 0.0.34`, the newest core release, and
  align the version with the suite's 0.0.35 release, in which all
  fourteen packages and bankstatementparser.com share one version.
- `scripts/check_suite_consistency.py` now checks all fourteen suite
  packages on PyPI and the bankstatementparser.com GitHub release.
- Development dependency `ruff` updated from 0.17.5 to 0.17.6.

## [0.0.34] - 2026-11-18

### Changed

- Require `bankstatementparser >= 0.0.33`, the newest core release, and
  align the version with the suite's 0.0.34 release. No other changes.

## [0.0.33] - 2026-11-18

### Changed

- Require `bankstatementparser >= 0.0.32`, the newest core release, and
  align the version with the suite's 0.0.33 release. No other changes.

## [0.0.32] - 2026-11-18

### Changed

- Require `bankstatementparser >= 0.0.31`, the newest core release, and
  align the version with the suite's 0.0.32 release.
- Release notes are written by the release workflow. A final
  `release-notes` job runs after every asset is attached and rewrites
  the GitHub release in the suite's format: Highlights, What's Changed,
  New Contributors (when any), Checksums of every asset, and the Full
  Changelog link. Until now the body was the CHANGELOG section,
  with no Highlights or Checksums, so 0.0.31 had to be corrected by
  hand. `softprops/action-gh-release` is no longer used.
- The Highlights are the one hand-written part, kept in
  `.github/releases/<tag>.md`. The build refuses to publish when that
  file is missing, has fewer than 2 or more than 4
  `* **Headline**: text` bullets, or contains an em dash.
- `scripts/release_notes.py`, shared with every suite repository,
  composes the body from the GitHub API and the downloaded assets.

## [0.0.31] - 2026-11-18

### Changed

- Require `bankstatementparser >= 0.0.30`, the newest core release, and
  align the version with the suite's 0.0.31 release.
- Release titles read `bankstatementparser-loader-bai2 <version>` instead of the bare tag.

## [0.0.30] - 2026-11-18

### Changed

- Bumped dependency to `bankstatementparser >= 0.0.29`.
- Aligned version with `bankstatementparser` 0.0.30 suite release.
- Updated ruff to 0.17.5 (dev).
- 0.0.29 was prepared but never published; its changes ship in 0.0.30.

## [0.0.28] - 2026-10-11

### Changed

- Bumped dependency to `bankstatementparser >= 0.0.28`.
- Aligned version with `bankstatementparser` 0.0.28 suite release.

## [0.0.19] - 2026-08-31

### Added

- `Bai2StatementParser` implementing `BankStatementParser` interface.
- Registered entry point `bankstatementparser.loaders` for `bai2`.
- Bumped dependency to `bankstatementparser >= 0.0.19`.

## [0.0.18] - 2026-08-29

Aligns the `bankstatementparser` suite on one version number, and adds
the scheduled drift check this repository was missing.

### Added

- `scripts/check_suite_consistency.py` and a scheduled `Suite
  Consistency` workflow compare this tree, and every published member of
  the suite, against PyPI. A member left a release behind still installs
  and still passes its own tests; only the index disagrees, and only if
  somebody looks.

### Changed

- Version aligned to `0.0.18` across all six `bankstatementparser`
  packages, which had drifted to `0.0.14`, `0.0.15`, `0.0.17`, `0.0.16`,
  `0.0.16` and `0.0.15`.
- Refreshed the vendored `tests/test_suite_conformance.py` to the current
  canonical copy. Its drift-check probe now matches the bare word `pypi`
  rather than the hostname, which CodeQL read as an incomplete URL
  sanitisation.

## [0.0.16] - 2026-08-29

Brings this repository onto the **suite conformance gate**.

### Added

- **`benches/bench_load_bai2.py`** — a BAI2 bank-day file is sized by how
  busy the business was, not by anything the caller chose, and month-end
  is several times an ordinary Tuesday.

  **Loading is linear** — `us/txn` moves 1.07x between 10 and 10,000
  transactions across one account and across fifty. **`summarize_bai2`
  costs 0.26–0.62x `load_bai2`**, so a caller that only wants totals
  genuinely pays less; a ratio near 1.00 would have meant the summary
  builds the full transaction list and discards it.

  Nothing asserts a timing threshold — wall-clock is not comparable
  between machines, and a flaky performance gate teaches people to ignore
  red. CI runs `--quick`, so a benchmark that stops compiling fails the
  build rather than rotting into a file that reads as verified.

- **`tests/test_suite_conformance.py`** — invariants shared by every
  repository in the suite, vendored from one canonical copy and
  checksummed by its own test.

### Changed

- CI lints, formats and runs `benches/` alongside everything else.
- `tomli` (on 3.10) and `packaging` are named as dev dependencies; the
  conformance gate parses `pyproject.toml` and needs both.
- `tests/test_suite_conformance.py` is excluded from black: it is
  generated, and the suite uses three different line lengths.

## [0.0.15] - 2026-08-28

### Changed

- **A plain `pytest` now enforces the same 100% coverage floor CI does.**
  `--cov`, `--cov-branch` and `--cov-report=term-missing` move into
  `[tool.pytest.ini_options] addopts`. Before this, running `pytest`
  locally measured no coverage at all: the developer saw green and learned
  otherwise from the build.

  The gate itself was never missing — CI has always run
  `--cov-fail-under=100`, so nothing could regress onto `main` unnoticed.
  What was missing was the local half of it.

- **The floor is stated once.** It was in two places, the
  `--cov-fail-under` flag in `ci.yml` and `fail_under` under
  `[tool.coverage.report]`, which is how two numbers meant to be equal stop
  being equal. pytest-cov honours `fail_under` from the coverage config, so
  the flag is gone from both `addopts` and the workflow and the number lives
  in exactly one place.

  CI now runs `pytest tests/ --cov-report=xml -v`; only the XML report is
  CI-specific.

### Verification

Coverage was already 100% and remains so. The gate was mutation-tested:
adding a function no test calls drops coverage below the floor and fails
the run, locally as well as in CI.

## [0.0.14] - 2026-07-18

### Changed

- chore(deps): require `bankstatementparser>=0.0.11` (was `>=0.0.9`),
  keeping the loader in lockstep with the 0.0.11 core release. No
  functional or API changes.

## [0.0.13] - 2026-06-25

### Changed

- **Audit pass.** Removed a false 'unreachable' `# pragma: no cover` on the date-parse guard and added impossible-calendar-date tests (a genuinely reachable branch).

## [0.0.12] - 2026-06-24

### Fixed

- **Commas inside the `16` Transaction Detail free-text field are now
  preserved.** Previously the loader split the *entire* `16` record on
  commas, so a real-world text field such as `ACH Credit
  Payment,Entry Description: EXP; -, SEC: CCD, Client Ref ID: 1111` was
  truncated/mangled after its first comma. The parser now splits only
  the fixed leading fields (type code, amount, funds type, bank ref,
  customer ref) and keeps the remainder — the `text` field — verbatim,
  commas and all. This is a genuine bug fix that changes parsed
  `description` output for any file with commas in transaction text.
- **A `/` inside a `16`/`88` field is no longer mistaken for the record
  terminator.** Only a single *trailing* `/` (the real terminator) is
  stripped, so references and text containing slashes (e.g.
  `Client Ref ID: AB/GS/TEST0001/RPBA0001`) survive intact.
- **Funds-type-aware field positions.** A `V` (value-dated) or `S`
  (distributed-availability) funds type inserts extra subfields before
  the references; the loader now counts them so `bankRefNum`,
  `customerRefNum`, and `text` are located correctly (real moov-io
  `sample1` uses `V`).

### Added

- **Real-world BAI2 fixtures** vendored verbatim from the third-party
  Apache-2.0 [moov-io/bai2](https://github.com/moov-io/bai2) test corpus
  (`sample1.txt` and `sample5-issue113.txt`) under
  `tests/fixtures/real/`, with an honest `PROVENANCE.md`. Golden tests
  (`tests/test_real_fixtures_golden.py`) pin the exact `Transaction`
  list and `Bai2Summary` for both files, proving the messy real data —
  commas/slashes in text, `88` continuations carrying structured
  sub-data (`EREF:`/`DBNM:`/...), a `88:` colon-delimited continuation,
  trailing spaces after the terminator, and `88` continuations on an
  `03` summary — parses correctly.
- **`88` continuations carrying structured sub-data** are appended to
  the preceding `16` description verbatim (commas included); the rare
  `88:` colon-delimited form is tolerated. `88` continuations on an `03`
  account summary are dropped rather than corrupting transactions.
- **Mutation testing** with [`mutmut`](https://github.com/boxed/mutmut)
  (`make mutation`, `[tool.mutmut]` config, and a `test_mutation_kills.py`
  kill-suite). Score: 317/336 mutants killed; the 19 survivors are all
  documented equivalent mutants in `tests/MUTATION.md` (100% of
  non-equivalent mutants killed).

### Changed

- Simplified the continuation-routing state: an `88` now attaches solely
  to the live pending `16` (every other record flushes it first),
  removing a redundant target variable while keeping behaviour identical.

### Removed

- Pruned the heavy `codeql` and `security` GitHub Actions workflows.
  `ci`, `pr`, and `release` remain.

## [0.0.11] - 2026-06-24

### Changed

- **Type-code classification refined to the BAI2 spec's documented code
  ranges.** The `16` Transaction Detail type code now maps to a
  direction by range: `100`–`399` → credit (positive), `400`–`699` →
  debit (negative), `700`–`799` → loan detail treated as a debit-side
  disbursement (negative), and `900`–`999` → custom/summary/status codes
  that are **not** emitted as transactions (any continuation attached to
  a skipped status code is dropped with it). Non-numeric and otherwise
  out-of-range codes keep the amount positive. The raw type code is
  still preserved on every emitted `Transaction` in both `category`
  (`bai2:<code>`) and `reference`. `summarize_bai2`'s
  `transaction_count` now excludes skipped `900`–`999` codes so the
  summary and the `load_bai2` list stay in step.

### Added

- Optional, fully-tested lookup of well-known BAI2 type-code
  descriptions (`142` "ACH credit", `165` "Wire transfer credit", `301`
  "Commercial deposit", `475` "Check paid", `501` "Wire transfer debit")
  used to enrich a `16` record's `description` only when that record
  carries no free-text of its own.
- Install smoke-test CI job that builds the wheel, installs it (pulling
  `bankstatementparser` from PyPI) into a fresh virtual environment, and
  imports the package plus runs an example from a neutral working
  directory.
- A multi-group / multi-account BAI2 fixture under `tests/fixtures/`
  exercising every type-code range (credit, debit, loan, status), `88`
  continuations, and multiple `03` accounts, with golden-style tests
  pinning the exact signed `Transaction` list and the full
  `Bai2Summary`.

### Removed

- Pruned the `nightly` and `docs` GitHub Actions workflows (the project
  is a small library; `ci`, `pr`, `codeql`, `security`, and `release`
  remain).

## [0.0.10] - 2026-06-24

### Added

- Initial release of `bankstatementparser-loader-bai2`, a companion
  loader that parses **BAI2** (Bank Administration Institute, version 2)
  cash-management files into
  [`bankstatementparser`](https://github.com/sebastienrousseau/bankstatementparser)
  `Transaction` objects (`source="bai2"`) — a format the core library
  does not support.
- Public API:
  - `load_bai2(text)` — parse a BAI2 payload into `list[Transaction]`.
  - `load_bai2_file(path)` — parse a BAI2 file from disk.
  - `summarize_bai2(text)` — return a `Bai2Summary` dataclass with
    `file_id`, `group_count`, `account_count`, `transaction_count`, and
    `currency`.
- Documented, pragmatic BAI2 subset:
  - `01` File Header (required first record; `fileId` captured).
  - `02` Group Header (currency and as-of date captured).
  - `03` Account Identifier (`accountNumber` + optional `currencyCode`;
    account currency overrides the group currency).
  - `16` Transaction Detail (one transaction).
  - `88` Continuation (appended to the preceding `03`/`16` text).
  - `49`/`98`/`99` trailers and unknown codes are ignored (control
    totals are not validated — a deliberate, documented choice).
- Amount handling: BAI2 minor-unit integer amounts converted to
  `Decimal` via `value / 100`; empty amounts treated as `0`.
- Documented debit/credit sign convention from the `16` type-code range:
  `100`–`399` → credit (positive), `400`–`699` → debit (negative),
  anything else kept positive. The raw type code is preserved on every
  transaction in both `category` (`bai2:<code>`) and `reference`.
- Tolerant input handling: CRLF/LF, blank lines, optional trailing `/`,
  short records, and `88` continuations. A clear `ValueError` is raised
  when the file does not start with an `01` record.
- Three runnable, self-contained examples covering the full public API
  (`examples/01_load_transactions.py`, `examples/02_summarize_file.py`,
  and `examples/03_full_tour.py`).

### Quality gates

- pytest: 100% line + branch coverage against a 100% enforced floor.
- Documentation regression suites: `tests/test_docs_accuracy.py` asserts
  the README, CHANGELOG, and examples stay in lockstep with the loader
  (version, public symbols, record subset, and sign-convention table);
  `tests/test_regression_docs.py` executes every README python block; and
  `tests/test_regression_examples.py` runs every `examples/*.py` script.
- interrogate: 100% docstring coverage.
- ruff + black + mypy (`--strict`) all clean.

[0.0.37]: https://github.com/sebastienrousseau/bankstatementparser-loader-bai2/releases/tag/v0.0.37
[0.0.36]: https://github.com/sebastienrousseau/bankstatementparser-loader-bai2/releases/tag/v0.0.36
[0.0.35]: https://github.com/sebastienrousseau/bankstatementparser-loader-bai2/releases/tag/v0.0.35
[0.0.34]: https://github.com/sebastienrousseau/bankstatementparser-loader-bai2/releases/tag/v0.0.34
[0.0.33]: https://github.com/sebastienrousseau/bankstatementparser-loader-bai2/releases/tag/v0.0.33
[0.0.32]: https://github.com/sebastienrousseau/bankstatementparser-loader-bai2/releases/tag/v0.0.32
[0.0.31]: https://github.com/sebastienrousseau/bankstatementparser-loader-bai2/releases/tag/v0.0.31
[0.0.30]: https://github.com/sebastienrousseau/bankstatementparser-loader-bai2/releases/tag/v0.0.30
[0.0.28]: https://github.com/sebastienrousseau/bankstatementparser-loader-bai2/releases/tag/v0.0.28
[0.0.19]: https://github.com/sebastienrousseau/bankstatementparser-loader-bai2/releases/tag/v0.0.19
[0.0.18]: https://github.com/sebastienrousseau/bankstatementparser-loader-bai2/releases/tag/v0.0.18
[0.0.16]: https://github.com/sebastienrousseau/bankstatementparser-loader-bai2/releases/tag/v0.0.16
[0.0.15]: https://github.com/sebastienrousseau/bankstatementparser-loader-bai2/releases/tag/v0.0.15
[0.0.14]: https://github.com/sebastienrousseau/bankstatementparser-loader-bai2/releases/tag/v0.0.14
[0.0.13]: https://github.com/sebastienrousseau/bankstatementparser-loader-bai2/releases/tag/v0.0.13
[0.0.12]: https://github.com/sebastienrousseau/bankstatementparser-loader-bai2/releases/tag/v0.0.12
[0.0.11]: https://github.com/sebastienrousseau/bankstatementparser-loader-bai2/releases/tag/v0.0.11
[0.0.10]: https://github.com/sebastienrousseau/bankstatementparser-loader-bai2/releases/tag/v0.0.10
