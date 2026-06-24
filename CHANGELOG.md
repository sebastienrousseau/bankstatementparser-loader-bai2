# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.1] - 2026-06-24

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

[0.0.1]: https://github.com/sebastienrousseau/bankstatementparser-loader-bai2/releases/tag/v0.0.1
