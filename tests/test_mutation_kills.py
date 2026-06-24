# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2023-2026 Sebastien Rousseau. All rights reserved.

"""Targeted tests that pin behaviour mutation testing found unguarded.

Each test here kills a specific class of mutant surfaced by ``mutmut``
(boundary conditions on field-length guards, the date century window and
date slicing, exact error-message text, and the funds-type text-index
arithmetic). They exercise the private helpers directly where a payload
round-trip cannot reach the boundary cheaply. See ``tests/MUTATION.md``.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from bankstatementparser_loader_bai2 import load_bai2, loader, summarize_bai2


def _wrap(detail_records: str) -> str:
    """Wrap one or more 16/88 record lines in a minimal valid file."""
    return (
        "01,S,R,260601,1200,F1,/\n"
        "02,RCVR,ORIG,1,260601,1200,USD,/\n"
        "03,ACC1,USD,010,100,1,,/\n"
        f"{detail_records}"
    )


# ── _field boundary conditions ───────────────────────────────────────


def test_field_returns_index_zero() -> None:
    """_field(…, 0) returns the first element (kills 0<= -> 1<= / 0<)."""
    assert loader._field(["AA", "BB"], 0) == "AA"


def test_field_out_of_range_high_returns_empty() -> None:
    """_field at exactly len(fields) returns '' (kills < -> <=)."""
    assert loader._field(["AA", "BB"], 2) == ""


def test_field_negative_index_returns_empty() -> None:
    """A negative index is out of range and yields '' (kills 0<= guard)."""
    assert loader._field(["AA"], -1) == ""


# ── _parse_bai2_date century window + slicing ────────────────────────


def test_date_year_79_is_2000s() -> None:
    """YY=79 maps to 2079 (lower edge of the 20YY window)."""
    assert loader._parse_bai2_date("790601") == date(2079, 6, 1)


def test_date_year_80_is_1900s() -> None:
    """YY=80 maps to 1980 (kills year<80 -> year<=80 / year<81)."""
    assert loader._parse_bai2_date("800601") == date(1980, 6, 1)


def test_date_month_and_day_slices_are_correct() -> None:
    """The month and day come from the right slices (kills slice shifts)."""
    # 26-11-07: month must be 11 (text[2:4]) and day 07 (text[4:6]).
    assert loader._parse_bai2_date("261107") == date(2026, 11, 7)


def test_date_wrong_length_rejected() -> None:
    """A non-6-char value is rejected (kills the 'or' -> 'and' mutant)."""
    # 5 digits: length is wrong though it is all digits, so 'or' is
    # required (an 'and' would wrongly accept it and then raise/mis-slice).
    assert loader._parse_bai2_date("12345") is None


def test_date_non_digit_rejected() -> None:
    """A 6-char non-digit value is rejected (kills 'or' -> 'and')."""
    assert loader._parse_bai2_date("2026-1") is None


# ── _text_field_index / funds-type arithmetic ───────────────────────


def test_text_index_default_is_six() -> None:
    """A plain/empty funds type puts text at index 6."""
    assert loader._text_field_index("Z") == 6
    assert loader._text_field_index("") == 6


def test_text_index_value_dated_is_eight() -> None:
    """'V' funds type shifts text to index 8 (kills the +2 arithmetic)."""
    assert loader._text_field_index("V") == 8


def test_text_index_distributed_is_nine() -> None:
    """'S' funds type shifts text to index 9 (kills the +3 arithmetic)."""
    assert loader._text_field_index("S") == 9


# ── _split_16 short-record boundaries ────────────────────────────────


def test_split_16_bare_record_all_empty() -> None:
    """A bare '16' yields empty parts (kills the len-guard boundaries)."""
    assert loader._split_16("16") == ("", "", "", "", "")


def test_split_16_type_code_only() -> None:
    """'16,409' returns just the type code (kills len>1 -> len>2/>=1)."""
    assert loader._split_16("16,409") == ("409", "", "", "", "")


def test_split_16_type_and_amount_only() -> None:
    """'16,409,2500' returns type + amount (kills len>2 boundary)."""
    assert loader._split_16("16,409,2500") == ("409", "2500", "", "", "")


def test_split_16_through_funds_type_only() -> None:
    """'16,409,2500,Z' returns no refs/text (kills len>3 boundary)."""
    assert loader._split_16("16,409,2500,Z") == ("409", "2500", "", "", "")


def test_split_16_bank_ref_present_customer_and_text_absent() -> None:
    """A record ending at the bank ref leaves customer ref + text empty.

    Pins ``bank_ref`` at ``text_index - 2`` and the two trailing guards.
    """
    assert loader._split_16("16,165,100,Z,BANKONLY") == (
        "165",
        "100",
        "BANKONLY",
        "",
        "",
    )


def test_split_16_customer_ref_present_text_absent() -> None:
    """A record ending at the customer ref leaves the text empty."""
    assert loader._split_16("16,165,100,Z,BANK,CUST") == (
        "165",
        "100",
        "BANK",
        "CUST",
        "",
    )


def test_split_16_full_record_with_comma_text() -> None:
    """A full record keeps every field, commas in text included."""
    assert loader._split_16("16,165,100,Z,BANK,CUST,a, b, c") == (
        "165",
        "100",
        "BANK",
        "CUST",
        "a, b, c",
    )


# ── Exact error-message text ─────────────────────────────────────────


def test_load_bai2_error_message_is_exact() -> None:
    """The 01-missing error text is pinned (kills case/empty mutations)."""
    with pytest.raises(ValueError) as exc:
        load_bai2("02,RCVR,ORIG,1,260601,1200,USD,/\n")
    assert str(exc.value) == "BAI2 payload must start with an '01' File Header"


def test_summarize_bai2_error_message_is_exact() -> None:
    """summarize_bai2 raises the same exact text as load_bai2."""
    with pytest.raises(ValueError) as exc:
        summarize_bai2("16,165,100,Z,REF,,Text/\n")
    assert str(exc.value) == "BAI2 payload must start with an '01' File Header"


# ── Trailing-slash whitespace handling (rstrip, not lstrip) ──────────


def test_trailing_space_after_terminator_preserves_leading_text() -> None:
    """A '/ ' terminator keeps leading text (kills rstrip -> lstrip).

    With ``lstrip`` the leading characters of a record whose terminator
    is followed by a space would be stripped; ``rstrip`` keeps them.
    """
    payload = _wrap("16,165,100,Z,REF,,  spaced text  / \n")
    txn = load_bai2(payload)[0]
    # Internal/leading spaces of the text are trimmed by _split_16's own
    # .strip(); what matters is the type code and value survive intact.
    assert txn.reference == "165"
    assert txn.amount == Decimal("1.00")
    assert txn.description == "spaced text"


# ── Continuation only attaches to a live pending 16 ──────────────────


def test_continuation_after_account_is_dropped_not_attached() -> None:
    """An 88 right after an 03 attaches to nothing (kills pending guard)."""
    payload = (
        "01,S,R,260601,1200,F1,/\n"
        "02,RCVR,ORIG,1,260601,1200,USD,/\n"
        "03,ACC1,USD,010,100,1,,/\n"
        "88,must not appear/\n"
        "16,165,100,Z,REF,,real text/\n"
    )
    txn = load_bai2(payload)[0]
    assert txn.description == "real text"
    assert "must not appear" not in (txn.description or "")


# ── Group / account state is reset to None, not "" ───────────────────


def test_transaction_before_any_account_has_none_account_id() -> None:
    """A 16 before any 03 has account_id None, not '' (kills None -> '').

    Pins the initial ``account_number``/``account_currency`` state: a
    transaction seen before any ``03`` carries ``None``, and the group
    currency (set by ``02``) is still its currency.
    """
    payload = (
        "01,S,R,260601,1200,F1,/\n"
        "02,RCVR,ORIG,1,260601,1200,USD,/\n"
        "16,165,100,Z,REF,,Orphan before account/\n"
    )
    txn = load_bai2(payload)[0]
    assert txn.account_id is None
    assert txn.currency == "USD"


def test_account_state_reset_to_none_on_new_group() -> None:
    """A new 02 resets account_id to None (kills the 02-reset None -> '').

    The second group has a 16 with no 03 of its own; its account_id must
    fall back to None, not the empty string, and not leak group one's.
    """
    payload = (
        "01,S,R,260601,1200,F1,/\n"
        "02,RCVR,ORIG,1,260601,1200,USD,/\n"
        "03,ACC1,USD,010,100,1,,/\n"
        "16,165,100,Z,REF,,Group one tx/\n"
        "02,RCVR,ORIG,1,260602,1200,GBP,/\n"
        "16,165,200,Z,REF2,,Group two orphan/\n"
    )
    txns = load_bai2(payload)
    assert txns[0].account_id == "ACC1"
    assert txns[1].account_id is None
    assert txns[1].currency == "GBP"


def test_transaction_before_any_group_has_none_currency() -> None:
    """A 16 before any 02 has currency None (kills group_currency '' init)."""
    payload = (
        "01,S,R,260601,1200,F1,/\n" "16,165,100,Z,REF,,Orphan before group/\n"
    )
    txn = load_bai2(payload)[0]
    assert txn.currency is None
    assert txn.account_id is None


# ── Trailer flushing is exact (49/98/99 each, nothing else) ──────────


def test_trailer_flushes_pending_before_continuation() -> None:
    """An 88 after a 49 trailer is dropped (kills the trailer-set members).

    Each of 49/98/99 must flush the live 16 so a following 88 has nothing
    to attach to. If a trailer code were removed from the set, the 16
    would still be pending and wrongly absorb the post-trailer 88.
    """
    for trailer in ("49,100,1/", "98,100,1,2/", "99,100,1,3/"):
        payload = (
            "01,S,R,260601,1200,F1,/\n"
            "02,RCVR,ORIG,1,260601,1200,USD,/\n"
            "03,ACC1,USD,010,100,1,,/\n"
            "16,165,100,Z,REF,,base/\n"
            f"{trailer}\n"
            "88,leaked continuation/\n"
        )
        txn = load_bai2(payload)[0]
        assert txn.description == "base", trailer
        assert "leaked" not in (txn.description or ""), trailer


def test_unknown_record_does_not_flush_pending() -> None:
    """An unknown record keeps the 16 pending (kills 'in' -> 'not in').

    The 88 after an unknown 17 record must still extend the preceding 16.
    The 'not in' mutant would flush on the 17 and drop the continuation.
    """
    payload = (
        "01,S,R,260601,1200,F1,/\n"
        "02,RCVR,ORIG,1,260601,1200,USD,/\n"
        "03,ACC1,USD,010,100,1,,/\n"
        "16,165,100,Z,REF,,base/\n"
        "17,vendor,extension/\n"
        "88,and continuation/\n"
    )
    txn = load_bai2(payload)[0]
    assert txn.description == "base and continuation"
