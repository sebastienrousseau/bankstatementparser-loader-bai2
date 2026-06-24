# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2023-2026 Sebastien Rousseau. All rights reserved.

"""Summarise a BAI2 file written to disk, then load it from a path.

Run with::

    python examples/02_summarize_file.py
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from bankstatementparser_loader_bai2 import load_bai2_file, summarize_bai2

SAMPLE = (
    "01,SENDER,RECEIVER,260601,1200,FILE007,,,/\n"
    "02,RCVR,ORIG,1,260601,1200,USD,/\n"
    "03,0123456789,USD,010,200000,1,,/\n"
    "16,165,200000,Z,WIRE1,,Salary deposit/\n"
    "03,9876543210,EUR,010,50000,1,,/\n"
    "16,475,50000,Z,SEPA1,,Supplier payment/\n"
    "49,250000,4/\n"
    "98,250000,2,6/\n"
    "99,250000,1,8/\n"
)


def main() -> None:
    """Write the sample to a temp file, summarise it, then load it."""
    summary = summarize_bai2(SAMPLE)
    print("Summary (without materialising transactions):")
    print(f"  file_id           = {summary.file_id}")
    print(f"  group_count       = {summary.group_count}")
    print(f"  account_count     = {summary.account_count}")
    print(f"  transaction_count = {summary.transaction_count}")
    print(f"  currency          = {summary.currency}\n")

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "statement.bai"
        path.write_text(SAMPLE, encoding="utf-8")
        transactions = load_bai2_file(path)

    print(f"Loaded {len(transactions)} transaction(s) from disk:")
    for txn in transactions:
        print(
            f"  {txn.account_id} {txn.currency} {txn.amount} "
            f"-> {txn.description}"
        )


if __name__ == "__main__":
    main()
