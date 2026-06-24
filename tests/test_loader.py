# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2023-2026 Sebastien Rousseau. All rights reserved.

"""Tests for the bankstatementparser-loader-bai2 loader."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from bankstatementparser_loader_bai2 import (
    Bai2Summary,
    __version__,
    load_bai2,
    load_bai2_file,
    summarize_bai2,
)


def _sample_bai2() -> str:
    """Return a realistic multi-record BAI2 payload.

    Covers a File Header (01), Group Header (02), Account Identifier
    (03), a credit Transaction Detail (16), a continuation (88), a debit
    Transaction Detail (16), an unknown-type Transaction Detail (16),
    and the Account / Group / File trailers (49 / 98 / 99).
    """
    return (
        "01,SENDER,RECEIVER,260601,1200,FILE001,,,/\n"
        "02,RCVR,ORIG,1,260601,1200,USD,/\n"
        "03,0123456789,USD,010,150000,1,,/\n"
        "16,165,150000,Z,BANKREF1,CUSTREF1,Incoming wire payment/\n"
        "88,from ACME Corp invoice 42/\n"
        "16,475,2500,Z,BANKREF2,,ATM withdrawal/\n"
        "16,900,1000,Z,BANKREF3,,Misc adjustment/\n"
        "49,152500,3/\n"
        "98,152500,1,5/\n"
        "99,152500,1,7/\n"
    )


def test_version_exposed() -> None:
    """The package exposes a non-empty semantic-style version string."""
    assert isinstance(__version__, str)
    assert __version__.count(".") >= 2


def test_transaction_count() -> None:
    """Every 16 record across the file becomes one transaction."""
    txns = load_bai2(_sample_bai2())
    assert len(txns) == 3


def test_credit_amount_is_positive_decimal() -> None:
    """A 100-399 type code yields a positive Decimal in major units."""
    credit = load_bai2(_sample_bai2())[0]
    assert credit.amount == Decimal("1500.00")
    assert credit.amount > 0


def test_debit_amount_is_negative_decimal() -> None:
    """A 400-699 type code yields a negative Decimal in major units."""
    debit = load_bai2(_sample_bai2())[1]
    assert debit.amount == Decimal("-25.00")
    assert debit.amount < 0


def test_unknown_type_code_stays_positive() -> None:
    """A type code outside both ranges keeps the amount positive."""
    other = load_bai2(_sample_bai2())[2]
    assert other.amount == Decimal("10.00")


def test_raw_type_code_preserved_in_category_and_reference() -> None:
    """The raw BAI2 type code is preserved so nothing is lost."""
    credit = load_bai2(_sample_bai2())[0]
    assert credit.category == "bai2:165"
    assert credit.reference == "165"


def test_description_includes_continuation() -> None:
    """An 88 continuation is appended to the prior 16 description."""
    credit = load_bai2(_sample_bai2())[0]
    assert credit.description == (
        "Incoming wire payment from ACME Corp invoice 42"
    )


def test_account_id_and_currency_from_account_record() -> None:
    """The account number and currency come from the 03 record."""
    txn = load_bai2(_sample_bai2())[0]
    assert txn.account_id == "0123456789"
    assert txn.currency == "USD"


def test_booking_date_from_group_as_of_date() -> None:
    """The 02 as-of date becomes each transaction's booking_date."""
    txn = load_bai2(_sample_bai2())[0]
    assert txn.booking_date == date(2026, 6, 1)


def test_transaction_id_prefers_bank_ref() -> None:
    """transaction_id uses the bank reference when present."""
    txn = load_bai2(_sample_bai2())[0]
    assert txn.transaction_id == "BANKREF1"


def test_source_is_bai2() -> None:
    """Every transaction is tagged with source='bai2'."""
    txns = load_bai2(_sample_bai2())
    assert all(t.source == "bai2" for t in txns)


def test_summary_fields() -> None:
    """summarize_bai2 reports file id and group/account/tx counts."""
    summary = summarize_bai2(_sample_bai2())
    assert isinstance(summary, Bai2Summary)
    assert summary.file_id == "FILE001"
    assert summary.group_count == 1
    assert summary.account_count == 1
    assert summary.transaction_count == 3
    assert summary.currency == "USD"


def test_missing_file_header_raises() -> None:
    """A payload not starting with 01 raises a clear ValueError."""
    bad = "02,RCVR,ORIG,1,260601,1200,USD,/\n"
    with pytest.raises(ValueError, match="01"):
        load_bai2(bad)


def test_empty_payload_raises() -> None:
    """An empty payload (no records) also raises ValueError."""
    with pytest.raises(ValueError, match="01"):
        load_bai2("\n\n")


def test_summary_missing_file_header_raises() -> None:
    """summarize_bai2 enforces the same 01-first rule as load_bai2."""
    with pytest.raises(ValueError, match="01"):
        summarize_bai2("16,165,100,Z,REF,,Text/\n")


def test_account_currency_overrides_group_currency() -> None:
    """A currency on the 03 record overrides the 02 group currency."""
    payload = (
        "01,S,R,260601,1200,F1,/\n"
        "02,RCVR,ORIG,1,260601,1200,USD,/\n"
        "03,ACC1,EUR,010,100,1,,/\n"
        "16,165,100,Z,REF,,Euro credit/\n"
    )
    txn = load_bai2(payload)[0]
    assert txn.currency == "EUR"


def test_account_without_currency_falls_back_to_group() -> None:
    """An 03 record with no currency inherits the group currency."""
    payload = (
        "01,S,R,260601,1200,F1,/\n"
        "02,RCVR,ORIG,1,260601,1200,GBP,/\n"
        "03,ACC1,,010,100,1,,/\n"
        "16,165,100,Z,REF,,Pound credit/\n"
    )
    txn = load_bai2(payload)[0]
    assert txn.currency == "GBP"


def test_empty_amount_treated_as_zero() -> None:
    """An empty amount field parses as Decimal('0')."""
    payload = (
        "01,S,R,260601,1200,F1,/\n"
        "02,RCVR,ORIG,1,260601,1200,USD,/\n"
        "03,ACC1,USD,010,0,1,,/\n"
        "16,165,,Z,REF,,No amount/\n"
    )
    txn = load_bai2(payload)[0]
    assert txn.amount == Decimal("0")


def test_transaction_id_falls_back_to_customer_ref() -> None:
    """When the bank ref is empty, the customer ref is used."""
    payload = (
        "01,S,R,260601,1200,F1,/\n"
        "02,RCVR,ORIG,1,260601,1200,USD,/\n"
        "03,ACC1,USD,010,100,1,,/\n"
        "16,165,100,Z,,CUST9,Customer ref only/\n"
    )
    txn = load_bai2(payload)[0]
    assert txn.transaction_id == "CUST9"


def test_transaction_id_none_when_no_refs() -> None:
    """A 16 record with neither reference leaves transaction_id None."""
    payload = (
        "01,S,R,260601,1200,F1,/\n"
        "02,RCVR,ORIG,1,260601,1200,USD,/\n"
        "03,ACC1,USD,010,100,1,,/\n"
        "16,165,100,Z,,,No refs/\n"
    )
    txn = load_bai2(payload)[0]
    assert txn.transaction_id is None


def test_non_numeric_type_code_keeps_amount_positive() -> None:
    """A non-numeric type code can't be ranged, so it stays positive."""
    payload = (
        "01,S,R,260601,1200,F1,/\n"
        "02,RCVR,ORIG,1,260601,1200,USD,/\n"
        "03,ACC1,USD,010,100,1,,/\n"
        "16,ABC,100,Z,REF,,Odd code/\n"
    )
    txn = load_bai2(payload)[0]
    assert txn.amount == Decimal("1.00")
    assert txn.category == "bai2:ABC"


def test_empty_type_code_yields_no_category_or_reference() -> None:
    """An empty type code leaves category and reference None."""
    payload = (
        "01,S,R,260601,1200,F1,/\n"
        "02,RCVR,ORIG,1,260601,1200,USD,/\n"
        "03,ACC1,USD,010,100,1,,/\n"
        "16,,100,Z,REF,,Blank code/\n"
    )
    txn = load_bai2(payload)[0]
    assert txn.category is None
    assert txn.reference is None


def test_empty_text_yields_none_description() -> None:
    """A 16 record with no text leaves the description None."""
    payload = (
        "01,S,R,260601,1200,F1,/\n"
        "02,RCVR,ORIG,1,260601,1200,USD,/\n"
        "03,ACC1,USD,010,100,1,,/\n"
        "16,165,100,Z,REF,,/\n"
    )
    txn = load_bai2(payload)[0]
    assert txn.description is None


def test_crlf_and_blank_lines_tolerated() -> None:
    """CRLF endings and blank lines do not break parsing."""
    payload = (
        "01,S,R,260601,1200,F1,/\r\n"
        "\r\n"
        "02,RCVR,ORIG,1,260601,1200,USD,/\r\n"
        "03,ACC1,USD,010,100,1,,/\r\n"
        "\r\n"
        "16,165,100,Z,REF,,Carriage returns/\r\n"
    )
    txns = load_bai2(payload)
    assert len(txns) == 1
    assert txns[0].description == "Carriage returns"


def test_missing_trailing_slash_tolerated() -> None:
    """Records without the trailing '/' delimiter still parse."""
    payload = (
        "01,S,R,260601,1200,F1\n"
        "02,RCVR,ORIG,1,260601,1200,USD\n"
        "03,ACC1,USD,010,100,1,\n"
        "16,165,100,Z,REF,,No slash here\n"
    )
    txns = load_bai2(payload)
    assert len(txns) == 1
    assert txns[0].description == "No slash here"


def test_continuation_on_account_record_is_dropped() -> None:
    """An 88 after an 03 (not a 16) has no transaction to attach to."""
    payload = (
        "01,S,R,260601,1200,F1,/\n"
        "02,RCVR,ORIG,1,260601,1200,USD,/\n"
        "03,ACC1,USD,010,100,1,,/\n"
        "88,account level note/\n"
        "16,165,100,Z,REF,,Real transaction/\n"
    )
    txns = load_bai2(payload)
    assert len(txns) == 1
    assert txns[0].description == "Real transaction"


def test_orphan_continuation_before_any_record_is_ignored() -> None:
    """An 88 before any 16 (target still none) is safely ignored."""
    payload = (
        "01,S,R,260601,1200,F1,/\n"
        "88,floating note/\n"
        "02,RCVR,ORIG,1,260601,1200,USD,/\n"
        "03,ACC1,USD,010,100,1,,/\n"
        "16,165,100,Z,REF,,Tx/\n"
    )
    txns = load_bai2(payload)
    assert len(txns) == 1


def test_unknown_record_type_is_ignored() -> None:
    """A leading type code the loader doesn't model is skipped."""
    payload = (
        "01,S,R,260601,1200,F1,/\n"
        "02,RCVR,ORIG,1,260601,1200,USD,/\n"
        "03,ACC1,USD,010,100,1,,/\n"
        "17,vendor,extension,record/\n"
        "16,165,100,Z,REF,,Tx/\n"
    )
    txns = load_bai2(payload)
    assert len(txns) == 1


def test_missing_as_of_date_leaves_booking_date_none() -> None:
    """A blank or malformed 02 as-of date yields booking_date None."""
    payload = (
        "01,S,R,260601,1200,F1,/\n"
        "02,RCVR,ORIG,1,,1200,USD,/\n"
        "03,ACC1,USD,010,100,1,,/\n"
        "16,165,100,Z,REF,,No date/\n"
    )
    txn = load_bai2(payload)[0]
    assert txn.booking_date is None


def test_old_century_date_window() -> None:
    """A YY >= 80 as-of date maps to the 1900s."""
    payload = (
        "01,S,R,950601,1200,F1,/\n"
        "02,RCVR,ORIG,1,950601,1200,USD,/\n"
        "03,ACC1,USD,010,100,1,,/\n"
        "16,165,100,Z,REF,,Old/\n"
    )
    txn = load_bai2(payload)[0]
    assert txn.booking_date == date(1995, 6, 1)


def test_multiple_groups_and_accounts_flattened() -> None:
    """16 records across several 03/02 records flatten into one list."""
    payload = (
        "01,S,R,260601,1200,F1,/\n"
        "02,RCVR,ORIG,1,260601,1200,USD,/\n"
        "03,ACC1,USD,010,100,1,,/\n"
        "16,165,100,Z,R1,,Tx1/\n"
        "03,ACC2,EUR,010,200,1,,/\n"
        "16,165,200,Z,R2,,Tx2/\n"
        "02,RCVR,ORIG,1,260602,1200,GBP,/\n"
        "03,ACC3,GBP,010,300,1,,/\n"
        "16,165,300,Z,R3,,Tx3/\n"
    )
    txns = load_bai2(payload)
    assert [t.account_id for t in txns] == ["ACC1", "ACC2", "ACC3"]
    assert [t.currency for t in txns] == ["USD", "EUR", "GBP"]
    assert [t.source_index for t in txns] == [0, 1, 2]


def test_file_with_no_transactions_returns_empty_list() -> None:
    """Headers without any 16 records yield an empty transaction list."""
    payload = (
        "01,S,R,260601,1200,F1,/\n"
        "02,RCVR,ORIG,1,260601,1200,USD,/\n"
        "03,ACC1,USD,010,0,0,,/\n"
        "49,0,2/\n"
        "98,0,1,3/\n"
        "99,0,1,4/\n"
    )
    assert load_bai2(payload) == []


def test_summary_with_no_currency_is_none() -> None:
    """A file that never specifies a currency reports currency None."""
    payload = (
        "01,S,R,260601,1200,F1,/\n"
        "02,RCVR,ORIG,1,260601,1200,,/\n"
        "03,ACC1,,010,100,1,,/\n"
        "16,165,100,Z,REF,,Tx/\n"
    )
    summary = summarize_bai2(payload)
    assert summary.currency is None


def test_summary_empty_file_id_is_none() -> None:
    """An empty fileId field in the 01 record reports file_id None."""
    payload = (
        "01,S,R,260601,1200,,/\n"
        "02,RCVR,ORIG,1,260601,1200,USD,/\n"
        "03,ACC1,USD,010,100,1,,/\n"
        "16,165,100,Z,REF,,Tx/\n"
    )
    summary = summarize_bai2(payload)
    assert summary.file_id is None


def test_summary_prefers_group_currency_before_account() -> None:
    """The first currency seen is the group currency when it comes first."""
    payload = (
        "01,S,R,260601,1200,F1,/\n"
        "02,RCVR,ORIG,1,260601,1200,JPY,/\n"
        "03,ACC1,,010,100,1,,/\n"
        "16,165,100,Z,REF,,Tx/\n"
    )
    summary = summarize_bai2(payload)
    assert summary.currency == "JPY"


def test_slash_only_line_is_skipped() -> None:
    """A line consisting solely of the '/' delimiter is skipped."""
    payload = (
        "01,S,R,260601,1200,F1,/\n"
        "/\n"
        "02,RCVR,ORIG,1,260601,1200,USD,/\n"
        "03,ACC1,USD,010,100,1,,/\n"
        "16,165,100,Z,REF,,Tx/\n"
    )
    txns = load_bai2(payload)
    assert len(txns) == 1


def test_short_transaction_record_uses_empty_fields() -> None:
    """A 16 record missing trailing fields yields empty defaults."""
    payload = (
        "01,S,R,260601,1200,F1,/\n"
        "02,RCVR,ORIG,1,260601,1200,USD,/\n"
        "03,ACC1,USD,010,100,1,,/\n"
        "16,165,100\n"
    )
    txn = load_bai2(payload)[0]
    assert txn.amount == Decimal("1.00")
    assert txn.transaction_id is None
    assert txn.description is None


def test_load_bai2_file_reads_from_disk(tmp_path) -> None:
    """load_bai2_file reads a file and parses it like load_bai2."""
    path = tmp_path / "statement.bai"
    path.write_text(_sample_bai2(), encoding="utf-8")
    txns = load_bai2_file(path)
    assert len(txns) == 3
    assert txns[0].amount == Decimal("1500.00")
