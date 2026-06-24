<!-- SPDX-License-Identifier: Apache-2.0 -->

<p align="center">
  <img
    src="https://cloudcdn.pro/bankstatementparser/v1/logos/bankstatementparser.svg"
    alt="bankstatementparser-loader-bai2 logo"
    width="120"
    height="120"
  />
</p>

<h1 align="center">bankstatementparser-loader-bai2</h1>

<p align="center">
  <b>A BAI2 (Bank Administration Institute, version 2) cash-management loader that parses BAI2 files into <code>bankstatementparser</code> <code>Transaction</code> objects.</b>
</p>

<p align="center">
  <a href="https://pypi.org/project/bankstatementparser-loader-bai2/"><img src="https://img.shields.io/pypi/v/bankstatementparser-loader-bai2?style=for-the-badge" alt="PyPI version" /></a>
  <a href="https://pypi.org/project/bankstatementparser-loader-bai2/"><img src="https://img.shields.io/pypi/pyversions/bankstatementparser-loader-bai2.svg?style=for-the-badge" alt="Python versions" /></a>
  <a href="https://pypi.org/project/bankstatementparser-loader-bai2/"><img src="https://img.shields.io/pypi/dm/bankstatementparser-loader-bai2.svg?style=for-the-badge" alt="PyPI downloads" /></a>
  <a href="https://github.com/sebastienrousseau/bankstatementparser-loader-bai2/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/sebastienrousseau/bankstatementparser-loader-bai2/ci.yml?branch=main&label=Tests&style=for-the-badge" alt="Tests" /></a>
  <a href="#license"><img src="https://img.shields.io/pypi/l/bankstatementparser-loader-bai2?style=for-the-badge" alt="License" /></a>
</p>

---

## Contents

- [What is bankstatementparser-loader-bai2?](#what-is-bankstatementparser-loader-bai2) — the problem it solves
- [Install](#install) — PyPI, virtualenv
- [Quick start](#quick-start) — parse a file in three lines
- [Public API](#public-api) — `load_bai2`, `load_bai2_file`, `summarize_bai2`
- [Supported BAI2 subset](#supported-bai2-subset) — exactly which records are handled
- [Amount and sign convention](#amount-and-sign-convention) — how cents and debit/credit map
- [When not to use this loader](#when-not-to-use-this-loader) — honest boundaries
- [Development](#development) — gates, make targets
- [Security](#security) — input-handling posture
- [Contributing](#contributing) — how to get changes in
- [License](#license) — Apache-2.0

---

## What is bankstatementparser-loader-bai2?

**BAI2** (Bank Administration Institute, version 2) is the de-facto US
cash-management file format that banks ship for intraday and prior-day
balance and transaction reporting. The published
[`bankstatementparser`](https://pypi.org/project/bankstatementparser/)
library parses PDF and other statement formats but **does not support
BAI2**.

**bankstatementparser-loader-bai2** is a small, dependency-light companion
that fills that gap: give it a BAI2 payload and it returns a flat list of
[`bankstatementparser.transaction_models.Transaction`](https://pypi.org/project/bankstatementparser/)
objects (`source="bai2"`) that the rest of your deterministic pipeline
can consume unchanged.

| Concern | How this loader handles it |
| :--- | :--- |
| Record model | A documented, pragmatic subset of BAI2 (`01`/`02`/`03`/`16`/`88` plus ignored trailers) |
| Amounts | BAI2 minor-unit integers (cents) converted to `Decimal` (never `float`) |
| Debit / credit | Derived from the `16` type-code range, with the raw code preserved |
| Multiple accounts | All `16` records across every group / account are flattened into one list |
| Robustness | Tolerates CRLF, blank lines, and an optional trailing `/` per record |
| Errors | A clear `ValueError` if the file does not start with an `01` File Header |

---

## Install

| Channel | Command | Notes |
| :--- | :--- | :--- |
| PyPI | `pip install bankstatementparser-loader-bai2` | Pulls in `bankstatementparser >= 0.0.9` |
| Source | `git clone https://github.com/sebastienrousseau/bankstatementparser-loader-bai2 && cd bankstatementparser-loader-bai2 && poetry install` | For development |

Requires Python 3.10 or later. Works on macOS, Linux, and Windows.

<details>
<summary>Using an isolated virtual environment (recommended)</summary>

```sh
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows
python -m pip install -U bankstatementparser-loader-bai2
```

</details>

---

## Quick start

```python
from bankstatementparser_loader_bai2 import load_bai2_file

transactions = load_bai2_file("statement.bai")
for txn in transactions:
    print(txn.account_id, txn.currency, txn.amount, txn.description)
```

Or parse an in-memory payload:

```python
from bankstatementparser_loader_bai2 import load_bai2

payload = (
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

for txn in load_bai2(payload):
    print(txn.amount, txn.category, txn.description)
# 1500 bai2:165 Incoming wire payment from ACME Corp invoice 42
# -25 bai2:475 ATM withdrawal
```

Runnable versions live in [`examples/`](examples/).

---

## Public API

```python
from bankstatementparser_loader_bai2 import (
    load_bai2,
    load_bai2_file,
    summarize_bai2,
    Bai2Summary,
)
```

| Function | Signature | Returns |
| :--- | :--- | :--- |
| `load_bai2` | `load_bai2(text: str)` | `list[Transaction]` |
| `load_bai2_file` | `load_bai2_file(path)` | `list[Transaction]` |
| `summarize_bai2` | `summarize_bai2(text: str)` | `Bai2Summary` |

`Bai2Summary` is a dataclass with the fields `file_id`, `group_count`,
`account_count`, `transaction_count`, and `currency`.

Each produced `Transaction` is populated as follows:

| `Transaction` field | Source |
| :--- | :--- |
| `account_id` | `03` Account Identifier — `accountNumber` |
| `currency` | `03` `currencyCode`, falling back to the `02` group currency |
| `amount` | `16` `amount` (cents / 100), signed per the convention below |
| `booking_date` | `02` Group Header as-of date, when present |
| `description` | `16` text plus any `88` continuations |
| `transaction_id` | `16` `bankRefNum`, falling back to `customerRefNum` |
| `reference` / `category` | The raw `16` type code (`category` as `bai2:<code>`) |
| `source` | Always `"bai2"` |

---

## Supported BAI2 subset

BAI2 records are comma-delimited fields ending with a `/` delimiter,
each beginning with a numeric type code. This loader implements a
**documented, pragmatic subset**:

| Record | Meaning | Handling |
| :--- | :--- | :--- |
| `01` | File Header | **Required first record.** `fileId` captured for the summary. |
| `02` | Group Header | Group `currency` and as-of date captured. |
| `03` | Account Identifier | `accountNumber` + optional `currencyCode` captured; account currency overrides group currency. |
| `16` | Transaction Detail | One transaction. |
| `88` | Continuation | Appended to the preceding `03`/`16` record's text. |
| `49` / `98` / `99` | Account / Group / File trailers | **Ignored** — control totals are not validated. |

Any other (or unknown) leading type code is ignored so that vendor
extensions do not abort the parse. Ignoring control-total trailers is a
deliberate, documented choice: the goal is faithful transaction
extraction, not file-level reconciliation.

---

## Amount and sign convention

BAI2 amounts are unsigned integers in the account currency's **minor
units** (cents), with no decimal point. They are converted to
`decimal.Decimal` by dividing by 100. An empty amount field is treated
as `0`.

Debit / credit direction is derived from the documented numeric ranges
of the `16` record's type code (this is the loader's chosen, documented
convention):

| Type-code range | Meaning | Behaviour |
| :--- | :--- | :--- |
| `100`–`399` | Credit | amount kept **positive** |
| `400`–`699` | Debit | amount made **negative** |
| `700`–`799` | Loan detail | treated as a debit-side disbursement: amount made **negative** |
| `900`–`999` | Custom / summary / status | **no `Transaction` emitted** — these non-detail status/summary codes are skipped (and any continuation attached to one is dropped with it) |
| anything else | Unknown (incl. non-numeric) | amount kept **positive** |

The raw BAI2 type code is always preserved on every emitted
`Transaction` in both `category` (as `bai2:<code>`) and `reference`, so
no information is lost.

A small, optional lookup of well-known type codes (for example `142`
"ACH credit", `301` "Commercial deposit", `475` "Check paid", `501`
"Wire transfer debit") enriches the `description` of a `16` record that
carries no free-text of its own; a record that already has text keeps
its own text unchanged.

---

## When not to use this loader

- **You have ISO 20022 camt.053 or SWIFT MT940, not BAI2.** Those are
  different formats with their own dedicated loaders.
- **You need control-total reconciliation.** This loader extracts
  transactions and deliberately ignores the `49`/`98`/`99` trailers; if
  you must validate file sums, do so before or after loading.
- **You need the full BAI2 specification.** This is a documented subset
  focused on transaction extraction, not an exhaustive BAI2 parser.

---

## Development

This project uses [Poetry](https://python-poetry.org/) and
[mise](https://mise.jdx.dev/).

```bash
git clone https://github.com/sebastienrousseau/bankstatementparser-loader-bai2.git
cd bankstatementparser-loader-bai2
poetry env use python3.12
poetry install
```

A `Makefile` orchestrates the quality gates (kept in lockstep with CI):

| Target | What it runs |
| :--- | :--- |
| `make check` | All gates (REQUIRED before commit) |
| `make test` | `pytest --cov=bankstatementparser_loader_bai2 --cov-branch --cov-fail-under=100` |
| `make lint` | `ruff check` + `black --check` |
| `make type-check` | `mypy --strict` |
| `make doc-coverage` | `interrogate --fail-under=100` (docstring coverage) |

Current state (v0.0.11): **all tests passing, 100% line + branch
coverage** against a 100% enforced floor, `mypy --strict` clean,
interrogate 100%.

---

## Security

- **Read-only.** The loader only reads text / files you pass it; it
  writes nothing.
- **No XML, no network, no code execution.** Parsing is a pure
  string-to-dataclass transformation.
- **Decimal arithmetic** is used throughout, avoiding `float` rounding
  surprises in financial amounts.
- **Dependencies** are pinned via `poetry.lock` and audited in CI.

To report a vulnerability, please use
[GitHub private vulnerability reporting](https://github.com/sebastienrousseau/bankstatementparser-loader-bai2/security)
rather than a public issue.

---

## Contributing

Contributions are welcome — see the
[contributing instructions](https://github.com/sebastienrousseau/bankstatementparser-loader-bai2/blob/main/CONTRIBUTING.md).
Thanks to all the
[contributors](https://github.com/sebastienrousseau/bankstatementparser-loader-bai2/graphs/contributors)
who have helped build `bankstatementparser-loader-bai2`.

---

## License

Licensed under the [Apache License, Version 2.0](https://opensource.org/license/apache-2-0/).
Any contribution submitted for inclusion shall be licensed as above,
without additional terms.

---

<p align="center">
  <a href="https://bankstatementparser.com">bankstatementparser.com</a> ·
  <a href="https://pypi.org/project/bankstatementparser-loader-bai2/">PyPI</a> ·
  <a href="https://github.com/sebastienrousseau/bankstatementparser-loader-bai2">GitHub</a>
</p>
