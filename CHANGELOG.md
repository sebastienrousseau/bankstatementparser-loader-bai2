# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[0.0.12]: https://github.com/sebastienrousseau/bankstatementparser-loader-bai2/releases/tag/v0.0.12
[0.0.11]: https://github.com/sebastienrousseau/bankstatementparser-loader-bai2/releases/tag/v0.0.11
[0.0.10]: https://github.com/sebastienrousseau/bankstatementparser-loader-bai2/releases/tag/v0.0.10
