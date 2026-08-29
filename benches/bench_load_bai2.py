#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Sebastien Rousseau <sebastian.rousseau@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR MIT
"""What a BAI2 file costs to load, as the file grows.

BAI2 is a bank-day file. A US corporate with a handful of accounts receives
one every morning containing every transaction on every account, and the
size is decided by how busy the business was — not by anything the caller
chose. Month-end and payroll days are several times an ordinary Tuesday,
and those are precisely the days the job must not fall over.

Two axes move in practice, so both are measured:

* **Transactions within one account** (``16`` records under one ``03``).
* **Accounts within one file** (several ``03`` groups under one ``02``).

Read ``us/txn``. Flat means linear, and a payroll-day file is fine.
Climbing means something rescans records it has already read — invisible
on the small fixtures, obvious on a real file.

``summarize_bai2`` is measured beside ``load_bai2`` because callers that
only want totals should not have to pay for the full transaction list. If
the two cost the same, the summary is building everything and then
discarding it, and the cheap path is not actually cheap.

Run::

    python benches/bench_load_bai2.py
    python benches/bench_load_bai2.py --json
    python benches/bench_load_bai2.py --quick     # what CI runs

Nothing here asserts a threshold: wall-clock is not comparable between
machines, and a flaky performance gate teaches people to ignore red. CI
runs ``--quick`` so a benchmark that has stopped compiling against the
current API fails the build instead of rotting into a file that reads as
verified and is not.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bankstatementparser_loader_bai2 import (  # noqa: E402
    load_bai2,
    summarize_bai2,
)

FILE_HEADER = "01,SENDER,RECEIVER,260601,1200,FILE001,,,/\n"
GROUP_HEADER = "02,RCVR,ORIG,1,260601,1200,USD,/\n"
ACCOUNT = "03,{account:010d},USD,010,150000,1,,/\n"
TXN = "16,165,{amount},Z,BANKREF{i},CUSTREF{i},Payment {i}/\n"
CONTINUATION = "88,continuation detail for payment {i}/\n"
ACCOUNT_TRAILER = "49,152500,{records}/\n"
GROUP_TRAILER = "98,152500,{accounts},{records}/\n"
FILE_TRAILER = "99,152500,1,{records}/\n"


def build(accounts: int, txns_each: int) -> str:
    """A BAI2 file with ``accounts`` accounts of ``txns_each`` transactions.

    Every other transaction carries an ``88`` continuation record, which is
    what real files look like and which the parser has to stitch back onto
    the preceding ``16``.
    """
    parts = [FILE_HEADER, GROUP_HEADER]
    for account in range(accounts):
        parts.append(ACCOUNT.format(account=account))
        for i in range(txns_each):
            parts.append(TXN.format(amount=(i % 900) + 100, i=i))
            if i % 2 == 0:
                parts.append(CONTINUATION.format(i=i))
        parts.append(ACCOUNT_TRAILER.format(records=txns_each + 2))
    total = accounts * (txns_each + 2) + 2
    parts.append(GROUP_TRAILER.format(accounts=accounts, records=total))
    parts.append(FILE_TRAILER.format(records=total + 1))
    return "".join(parts)


def _best(call, repeats: int) -> float:
    """Best-of timing after one untimed warm-up.

    The minimum is the least noisy estimator available; the mean follows
    whatever else the machine happens to be doing.
    """
    call()
    samples = []
    for _ in range(repeats):
        start = time.perf_counter()
        call()
        samples.append(time.perf_counter() - start)
    return min(samples)


def measure(accounts: int, txns_each: int, repeats: int) -> dict:
    text = build(accounts, txns_each)
    load = _best(lambda: load_bai2(text), repeats)
    summary = _best(lambda: summarize_bai2(text), repeats)
    transactions = len(load_bai2(text))
    return {
        "accounts": accounts,
        "txns_each": txns_each,
        "transactions": transactions,
        "bytes": len(text),
        "load_ms": load * 1e3,
        "summary_ms": summary * 1e3,
        "us_per_txn": load * 1e6 / transactions if transactions else 0.0,
        "summary_over_load": summary / load if load else 0.0,
    }


def run(quick: bool) -> list[dict]:
    if quick:
        shapes = [(1, 10), (1, 100)]
        repeats = 3
    else:
        shapes = [(1, 10), (1, 100), (1, 1_000), (10, 500), (50, 200)]
        repeats = 7
    return [measure(a, t, repeats) for a, t in shapes]


def render(rows: list[dict]) -> None:
    print(
        f"{'accounts':>9}{'txns each':>11}{'total':>8}{'KiB':>9}"
        f"{'load ms':>10}{'summary ms':>12}{'us/txn':>9}"
    )
    for row in rows:
        print(
            f"{row['accounts']:>9}{row['txns_each']:>11}"
            f"{row['transactions']:>8}{row['bytes'] / 1024:>9.1f}"
            f"{row['load_ms']:>10.2f}{row['summary_ms']:>12.2f}"
            f"{row['us_per_txn']:>9.2f}"
        )
    if len(rows) >= 2 and rows[0]["us_per_txn"]:
        drift = rows[-1]["us_per_txn"] / rows[0]["us_per_txn"]
        print(
            f"\n  us/txn at {rows[-1]['transactions']:,} transactions is "
            f"{drift:.2f}x the cost at {rows[0]['transactions']:,}. Flat is "
            f"linear, and a payroll-day file is fine. Climbing means "
            f"something rescans records it has already read."
        )
    ratios = [r["summary_over_load"] for r in rows if r["summary_over_load"]]
    if ratios:
        worst = max(ratios)
        print(
            f"\n  summarize_bai2 costs up to {worst:.2f}x load_bai2. A "
            f"caller that only wants totals should pay less than one that "
            f"wants every transaction; a ratio near 1.00 means the summary "
            f"builds the full list and then throws it away."
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="emit JSON")
    parser.add_argument(
        "--quick", action="store_true", help="small sizes, as CI runs"
    )
    args = parser.parse_args()

    rows = run(quick=args.quick)
    if args.json:
        json.dump(rows, sys.stdout, indent=1)
        print()
    else:
        render(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
