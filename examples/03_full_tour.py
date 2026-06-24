# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2023-2026 Sebastien Rousseau. All rights reserved.

"""Full feature tour of the BAI2 loader's public API.

Exercises every public symbol exported by
``bankstatementparser_loader_bai2`` against a single self-contained,
inline BAI2 payload that includes every record type the loader models:

* ``01`` File Header (required first record)
* ``02`` Group Header (currency + as-of date)
* ``03`` Account Identifier (account number + currency)
* ``16`` credit Transaction Detail (type code ``165`` -> positive)
* ``16`` debit Transaction Detail (type code ``475`` -> negative)
* ``88`` Continuation (appended to the preceding ``16`` description)
* ``49`` / ``98`` / ``99`` trailers (ignored control totals)

It calls:

* ``summarize_bai2`` and prints **every** :class:`Bai2Summary` field;
* ``load_bai2`` to parse the same payload from a string;
* ``load_bai2_file`` to parse the same payload written to a temp file.

Run with::

    python examples/03_full_tour.py
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from bankstatementparser_loader_bai2 import (
    Bai2Summary,
    load_bai2,
    load_bai2_file,
    summarize_bai2,
)

# A single payload exercising every modelled record type.
SAMPLE = (
    "01,SENDER,RECEIVER,260601,1200,FILE042,,,/\n"  # 01 File Header
    "02,RCVR,ORIG,1,260601,1200,USD,/\n"  # 02 Group Header
    "03,0123456789,USD,010,150000,1,,/\n"  # 03 Account Identifier
    "16,165,150000,Z,BANKREF1,CUSTREF1,Incoming wire payment/\n"  # credit
    "88,from ACME Corp invoice 42/\n"  # 88 Continuation
    "16,475,2500,Z,BANKREF2,,ATM withdrawal/\n"  # debit
    "49,152500,2/\n"  # 49 Account Trailer (ignored)
    "98,152500,1,4/\n"  # 98 Group Trailer (ignored)
    "99,152500,1,6/\n"  # 99 File Trailer (ignored)
)


def show_summary(summary: Bai2Summary) -> None:
    """Print every field of a :class:`Bai2Summary`."""
    print("summarize_bai2 -> Bai2Summary:")
    print(f"  file_id           = {summary.file_id}")
    print(f"  group_count       = {summary.group_count}")
    print(f"  account_count     = {summary.account_count}")
    print(f"  transaction_count = {summary.transaction_count}")
    print(f"  currency          = {summary.currency}\n")


def show_transactions(label: str, transactions: list[object]) -> None:
    """Print a labelled list of parsed transactions."""
    print(f"{label} -> {len(transactions)} transaction(s):")
    for txn in transactions:
        sign = "CR" if txn.amount >= 0 else "DR"  # type: ignore[attr-defined]
        print(
            f"  [{sign}] {txn.amount} {txn.currency} "  # type: ignore[attr-defined]
            f"acct={txn.account_id} type={txn.category} "  # type: ignore[attr-defined]
            f"ref={txn.transaction_id}"  # type: ignore[attr-defined]
        )
        print(f"        {txn.description}")  # type: ignore[attr-defined]
    print()


def main() -> None:
    """Run summarize_bai2, load_bai2, and load_bai2_file on one payload."""
    show_summary(summarize_bai2(SAMPLE))

    show_transactions("load_bai2 (from string)", load_bai2(SAMPLE))

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "statement.bai"
        path.write_text(SAMPLE, encoding="utf-8")
        show_transactions("load_bai2_file (from disk)", load_bai2_file(path))


if __name__ == "__main__":
    main()
