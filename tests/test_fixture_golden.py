# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2023-2026 Sebastien Rousseau. All rights reserved.

"""Golden-style tests pinning the exact output of a realistic corpus.

The ``tests/fixtures/multi_group_multi_account.bai`` fixture is a
deliberately broad BAI2 file: two ``02`` groups, three ``03`` accounts
(one inheriting the group currency), every documented ``16`` type-code
range (credit ``100``–``399``, debit ``400``–``699``, loan
``700``–``799``, and skipped status ``900``–``999``), ``88``
continuations on both a kept transaction and a skipped status code, and
the ignored ``49``/``98``/``99`` trailers.

These tests assert the *entire* parsed result field-by-field (signed
``Decimal`` amounts, account id, currency, description including
continuations and type-code enrichment, and the raw type code) plus the
full :class:`Bai2Summary`, so any drift in the loader is caught exactly.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

from bankstatementparser_loader_bai2 import (
    Bai2Summary,
    load_bai2_file,
    summarize_bai2,
)

FIXTURE = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "multi_group_multi_account.bai"
)

# The exact transactions the fixture must produce, in file order. Each
# tuple is (account_id, currency, amount, booking_date, description,
# category, reference, transaction_id). The 905 status code is absent on
# purpose: it is a non-detail code and emits nothing.
_EXPECTED = (
    (
        "ACC100",
        "USD",
        Decimal("5000.00"),
        date(2026, 6, 1),
        "Payroll deposit from ACME Corp run 2026-06",
        "bai2:142",
        "142",
        "BANKREF1",
    ),
    (
        "ACC100",
        "USD",
        Decimal("-1250.00"),
        date(2026, 6, 1),
        "Check paid",  # enriched: the 475 record carries no free-text
        "bai2:475",
        "475",
        "BANKREF2",
    ),
    (
        "ACC200",
        "EUR",  # 03 account currency overrides the USD group currency
        Decimal("2000.00"),
        date(2026, 6, 1),
        "Branch deposit batch 88",
        "bai2:301",
        "301",
        "BANKREF3",
    ),
    (
        "ACC200",
        "EUR",
        Decimal("-3000.00"),  # 710 loan -> debit-side, negative
        date(2026, 6, 1),
        "Loan advance",
        "bai2:710",
        "710",
        "BANKREF4",
    ),
    (
        "ACC300",
        "GBP",  # 03 has no currency -> inherits the GBP group currency
        Decimal("-750.00"),  # 501 wire debit -> negative
        date(2026, 6, 2),
        "Wire transfer debit",  # enriched: the 501 record carries no text
        "bai2:501",
        "501",
        "BANKREF5",
    ),
)


def test_fixture_transactions_match_golden() -> None:
    """The fixture parses to exactly the pinned transaction list."""
    txns = load_bai2_file(FIXTURE)
    actual = [
        (
            t.account_id,
            t.currency,
            t.amount,
            t.booking_date,
            t.description,
            t.category,
            t.reference,
            t.transaction_id,
        )
        for t in txns
    ]
    assert actual == list(_EXPECTED)


def test_fixture_source_index_is_emission_order() -> None:
    """source_index is the contiguous emission position, skips excluded."""
    txns = load_bai2_file(FIXTURE)
    assert [t.source_index for t in txns] == [0, 1, 2, 3, 4]
    assert all(t.source == "bai2" for t in txns)


def test_fixture_status_code_emits_no_transaction() -> None:
    """The 905 status code (and its 88) produce no transaction at all."""
    txns = load_bai2_file(FIXTURE)
    assert all(t.category != "bai2:905" for t in txns)
    assert len(txns) == 5


def test_fixture_summary_matches_golden() -> None:
    """The full Bai2Summary for the fixture is pinned exactly."""
    summary = summarize_bai2(FIXTURE.read_text(encoding="utf-8"))
    assert summary == Bai2Summary(
        file_id="FILE777",
        group_count=2,
        account_count=3,
        transaction_count=5,  # the 905 status code is not counted
        # summarize_bai2 tracks the most recent account currency it sees
        # (falling back to the first group currency): ACC200's EUR is the
        # last account currency in the file.
        currency="EUR",
    )


def test_fixture_covers_every_sign_range() -> None:
    """The golden set spans credit, debit, and loan sign outcomes."""
    amounts = [row[2] for row in _EXPECTED]
    assert any(a > 0 for a in amounts), "no credit-side amount"
    assert any(a < 0 for a in amounts), "no debit/loan-side amount"
