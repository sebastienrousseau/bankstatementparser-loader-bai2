# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2023-2026 Sebastien Rousseau. All rights reserved.

"""Load a BAI2 payload into bankstatementparser Transaction objects.

Run with::

    python examples/01_load_transactions.py
"""

from __future__ import annotations

from bankstatementparser_loader_bai2 import load_bai2

SAMPLE = (
    "01,SENDER,RECEIVER,260601,1200,FILE001,,,/\n"
    "02,RCVR,ORIG,1,260601,1200,USD,/\n"
    "03,0123456789,USD,010,150000,1,,/\n"
    "16,165,150000,Z,BANKREF1,CUSTREF1,Incoming wire payment/\n"
    "88,from ACME Corp invoice 42/\n"
    "16,475,2500,Z,BANKREF2,,ATM withdrawal/\n"
    "16,710,1000,Z,BANKREF3,,Loan disbursement/\n"
    "49,152500,3/\n"
    "98,152500,1,5/\n"
    "99,152500,1,7/\n"
)


def main() -> None:
    """Parse the sample payload and print each transaction."""
    transactions = load_bai2(SAMPLE)
    print(f"Parsed {len(transactions)} transaction(s):\n")
    for txn in transactions:
        sign = "CR" if txn.amount >= 0 else "DR"
        print(
            f"  [{sign}] {txn.amount:>10} {txn.currency} "
            f"acct={txn.account_id} type={txn.category} "
            f"ref={txn.transaction_id}"
        )
        print(f"        {txn.description}")


if __name__ == "__main__":
    main()
