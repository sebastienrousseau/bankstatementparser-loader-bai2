<!-- SPDX-License-Identifier: Apache-2.0 -->

# bankstatementparser-loader-bai2 Architecture

A map of the codebase for new contributors and maintainers. The goal is
that anyone can navigate, extend, and reason about
bankstatementparser-loader-bai2 without prior context.

## The pipeline

```
BAI2 payload (str / file)
        |  tokenise into comma-delimited records
        v
bankstatementparser_loader_bai2/loader.py   (_iter_records + record handlers)
        |  per-record accumulation; 88 continuations folded in
        v
bankstatementparser.transaction_models.Transaction   (source="bai2")
        |
        v
list[Transaction]  /  Bai2Summary
```

The loader is a pure, dependency-light string-to-dataclass
transformation. It reads a BAI2 payload, walks it record by record, and
produces a flat list of
[`bankstatementparser`](https://pypi.org/project/bankstatementparser/)
`Transaction` objects. There is no network, no XML, and no code
execution.

## Module map

| Area | Module | Responsibility |
| :--- | :--- | :--- |
| **Loader** | `bankstatementparser_loader_bai2/loader.py` | Record tokeniser, field helpers, sign convention, and the public `load_bai2` / `load_bai2_file` / `summarize_bai2` API plus the `Bai2Summary` dataclass |
| **Package entry** | `bankstatementparser_loader_bai2/__init__.py` | Re-exports the public API and defines `__version__` (single source of truth) |
| **Tests** | `tests/test_loader.py` | 100% line + branch coverage of the loader, including error and edge cases |
| **Examples** | `examples/` | Two runnable scripts: loading transactions and summarising / loading from disk |

## How a record becomes a transaction

1. `_iter_records` normalises line endings, drops blank lines and the
   trailing `/` delimiter, and yields each record as a list of trimmed
   fields.
2. `load_bai2` requires the first record to be an `01` File Header, then
   tracks the current group currency / as-of date and account number /
   currency as it walks the file.
3. Each `16` Transaction Detail starts a `_PendingTransaction`
   accumulator; subsequent `88` continuations append to its description.
4. The next record boundary (another `16`/`03`/`02`, or a trailer)
   flushes the accumulator into a frozen `Transaction`.

## Key design decisions

- **Documented pragmatic subset.** Only `01`/`02`/`03`/`16`/`88` are
  interpreted; `49`/`98`/`99` trailers and unknown codes are ignored so
  vendor extensions never abort a parse. The subset and the debit/credit
  sign convention are documented in the module docstring and the README.
- **Decimal everywhere.** BAI2 minor-unit integer amounts are converted
  with `Decimal(value) / Decimal(100)`. `float` is never used for money.
- **No information loss.** The raw BAI2 type code is preserved on every
  `Transaction` in both `category` (`bai2:<code>`) and `reference`, even
  for codes outside the credit/debit ranges.
- **Postel's law on input.** CRLF, blank lines, an optional trailing
  `/`, and short records are all tolerated; only a missing `01` File
  Header raises.
- **Coverage enforced at 100%** line + branch and docstring.

## Extension points

- **Interpret a new record type:** add a branch in the `load_bai2`
  record loop in `loader.py`; pair it with tests in
  `tests/test_loader.py`.
- **Change the sign convention:** edit `_CREDIT_RANGE` / `_DEBIT_RANGE`
  and `_signed_amount`; update the README convention table and tests.
- **Add a summary field:** extend the `Bai2Summary` dataclass and
  `summarize_bai2`.

## Where to look first

- Runnable examples: [`examples/`](examples/)
- Roadmap: [`ROADMAP.md`](ROADMAP.md)
- Release process: [`RELEASING.md`](RELEASING.md)
- Parent library: [`bankstatementparser`](https://github.com/sebastienrousseau/bankstatementparser)
