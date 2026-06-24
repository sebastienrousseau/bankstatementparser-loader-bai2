# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2023-2026 Sebastien Rousseau. All rights reserved.

"""Golden tests pinning the exact parse of real-world BAI2 fixtures.

The two fixtures under ``tests/fixtures/real/`` are vendored verbatim
from the third-party moov-io/bai2 test corpus (see that directory's
``PROVENANCE.md``). They are deliberately messy real-world-format files:
``16`` free-text fields full of commas, slashes inside reference and text
fields, ``88`` continuations carrying structured sub-data, a ``88:``
colon-delimited continuation, value-dated (``V``) funds types, trailing
spaces after the ``/`` terminator, and ``88`` continuations on an ``03``
summary.

These tests pin the *entire* resulting :class:`Transaction` list (signed
``Decimal`` amounts, account id, currency, full description including
continuations and embedded commas / slashes, and raw type code) plus the
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

REAL_DIR = Path(__file__).resolve().parent / "fixtures" / "real"
SAMPLE1 = REAL_DIR / "moov_bai2_sample1.bai"
SAMPLE5 = REAL_DIR / "moov_bai2_sample5_issue113.bai"

# Each row: (account_id, currency, amount, booking_date, reference,
# transaction_id, description).
_SAMPLE1_EXPECTED = (
    (
        "10200123456",
        "CAD",
        Decimal("-25"),
        date(2006, 3, 17),
        "409",
        None,
        "RETURNED CHEQUE",
    ),
    (
        "10200123456",
        "CAD",
        Decimal("-900"),
        date(2006, 3, 17),
        "409",
        None,
        "RTN-UNKNOWN",
    ),
    (
        "10200123456",
        "CAD",
        Decimal("-5"),
        date(2006, 3, 17),
        "409",
        None,
        "RTD CHQ SERVICE CHRG",
    ),
    (
        "10200123456",
        "CAD",
        Decimal("2035"),
        date(2006, 3, 17),
        "108",
        None,
        "TFR 1020 0345678",
    ),
    (
        "10200123456",
        "CAD",
        Decimal("25"),
        date(2006, 3, 17),
        "108",
        None,
        "MACLEOD MALL",
    ),
    (
        "10200123456",
        "CAD",
        Decimal("25"),
        date(2006, 3, 17),
        "108",
        None,
        "MASCOUCHE QUE",
    ),
    (
        "10200123456",
        "CAD",
        Decimal("-200"),
        date(2006, 3, 17),
        "409",
        None,
        "1000 ISLANDS MALL",
    ),
    (
        "10200123456",
        "CAD",
        Decimal("-900"),
        date(2006, 3, 17),
        "409",
        None,
        "PENHORA MALL",
    ),
    (
        "10200123456",
        "CAD",
        Decimal("-20"),
        date(2006, 3, 17),
        "409",
        None,
        "CAPILANO MALL",
    ),
    (
        "10200123456",
        "CAD",
        Decimal("-25"),
        date(2006, 3, 17),
        "409",
        None,
        "GALERIES LA CAPITALE",
    ),
    (
        "10200123456",
        "CAD",
        Decimal("-10"),
        date(2006, 3, 17),
        "409",
        None,
        "PLAZA ROCK FOREST",
    ),
    (
        "10200123456",
        "CAD",
        Decimal("115"),
        date(2006, 3, 17),
        "108",
        None,
        "TFR 1020 0345678",
    ),
    (
        "10200123456",
        "CAD",
        Decimal("1000"),
        date(2006, 3, 17),
        "108",
        None,
        "MONTREAL",
    ),
    (
        "10200123456",
        "CAD",
        Decimal("-1000"),
        date(2006, 3, 17),
        "409",
        None,
        "GRANDFALL NB",
    ),
    (
        "10200123456",
        "CAD",
        Decimal("-90"),
        date(2006, 3, 17),
        "409",
        None,
        "HAMILTON ON",
    ),
    (
        "10200123456",
        "CAD",
        Decimal("-20"),
        date(2006, 3, 17),
        "409",
        None,
        "WOODSTOCK NB",
    ),
    (
        "10200123456",
        "CAD",
        Decimal("-5"),
        date(2006, 3, 17),
        "409",
        None,
        "GALERIES RICHELIEU",
    ),
)

_SAMPLE5_EXPECTED = (
    (
        "107049932",
        "USD",
        Decimal("-600"),
        date(2023, 9, 6),
        "447",
        "SPB2322984714570",
        "ACH Credit Payment,Entry Description: EXP; -, SEC: CCD, Client Ref "
        "ID: 1111, GS ID: SPB2322984714570 EREF: 1111 DBNM: TEST INC CACT: "
        "ACHCONTROLOUTUSD01",
    ),
    (
        "107049932",
        "USD",
        Decimal("1435"),
        date(2023, 9, 6),
        "261",
        "SB2322600000404",
        'ACH Credit Reject,From: TEST INC, Remittance Info: "ACH- Test - '
        'Addenda Record", Entry Description: TRADE; -, SEC: CTX, Client Ref '
        "ID: GSQ4FBGFDGWGKY, GS ID: SB2322600000404 CREF: REMI: ACH- Test - "
        "Addenda Record EREF: GSQ4FBGFDGWGKY CRNM: Test DBNM: SAMPLE INC "
        "DACT: 101152046 DABA: 026015079",
    ),
    (
        "107049932",
        "USD",
        Decimal("-9286.5"),
        date(2023, 9, 6),
        "447",
        "SPB2322684598521",
        "ACH Credit Payment,Entry Description: TRADE; -, SEC: CTX, Client "
        "Ref ID: AB/GS/TEST0001/RPBA0001, GS ID: SPB2322684598521 EREF: "
        "AB/GS/RPFILERP0001/RPBA0001 DBNM: SAMPLE INC CACT: "
        "ACHCONTROLOUTUSD01",
    ),
    (
        "104108339",
        "USD",
        Decimal("-2000"),
        date(2023, 9, 6),
        "557",
        "SB2322600000214",
        "ACH Credit Receipt Return,Return To: Test, Remittance Info: "
        '"SB2322300000052", Entry Description: EXP; -, SEC: CCD, Reason: '
        '"R02", Return of Client Ref ID: 021000080000030, GS ID: '
        "SB2322600000214 CREF: 026015076104300 IDNM: 1114 EREF: "
        "021000080000030 CRNM: Test DBNM: SAMPLE INC. CABA: 021000089",
    ),
    (
        "104108339",
        "USD",
        Decimal("-555.55"),
        date(2023, 9, 6),
        "451",
        "SB2322600000455",
        "ACH Debit Payment,To: TEST, Entry Description: INVOICES; 210630, "
        "SEC: CCD, Client Ref ID: 021000020000021, GS ID: SB2322600000455 "
        "CREF: 021000020000021 IDNM: 2009282 EREF: 021000020000021 CRNM: "
        "TEST DBNM: SAMPLE INC CABA: 021000021",
    ),
    (
        "104108339",
        "USD",
        Decimal("19.12"),
        date(2023, 9, 6),
        "266",
        "GI2118700002010",
        "Outgoing Wire Return,- CREF: 20210706MMQFMPU8000001 EREF: "
        "20210706MMQFMPU8000001 DBIC: GSCRUS33 CRNM: ABC Company DBNM: "
        "SAMPLE INC.",
    ),
    (
        "104108339",
        "USD",
        Decimal("-505"),
        date(2023, 9, 6),
        "495",
        "GI2321400000090",
        'Outgoing Wire,To: TEST COMPANY, Remittance Info: "QWERTIOP", '
        "Client Ref ID: GSV0DL6RKT, GS ID: GI2321400000090, Settled Amt: "
        "EUR 322.00, FX Rate: 156.833677 REMI: QWERTIOP EREF: GSV0DL6RKT "
        "CBIC: COBADEFF CRNM: TEST COMPANY DBNM: SAMPLE TEST",
    ),
    (
        "104108339",
        "USD",
        Decimal("11.25"),
        date(2023, 9, 6),
        "195",
        "GI2229300000187",
        "Incoming Wire,- EREF: GS0D9VGMP1IWPLW DBIC: CITIUS30XXX CRNM: ABC "
        "CORPORATION DACT: 8348572423 CHKN: GSIL2X6103UNCRSF",
    ),
    (
        "104108339",
        "USD",
        Decimal("600"),
        date(2023, 9, 6),
        "257",
        "SB2225800001203",
        "ACH Debit Payment Return,Return From: Company1, Entry Description: "
        'TRADE; -, SEC: CCD, Reason: "R02", Return of Client Ref ID: '
        "028000020000335, GS ID: SB2225800001203 IDNM: 1 EREF: "
        "028000020000335 CRNM: TEST INC DBNM: Company1 DABA: 028000024",
    ),
    (
        "104108339",
        "USD",
        Decimal("9.31"),
        date(2023, 9, 6),
        "255",
        "SC2134800001999",
        "Check Return,Return From: Test2 Customer, Check Serial Number: "
        '0009000000, Return Reason: "Payee does not exist", Client Ref ID: '
        "74564762445, GS ID: SC213480000120999 EREF: 07370568132 CRNM: Test "
        "Inc. DBNM: Test2 Customer CABA: 12345 CHKN: 0009000000",
    ),
    (
        "104108339",
        "USD",
        Decimal("500.5"),
        date(2023, 9, 6),
        "195",
        "GI2228400005800",
        'RTP Incoming,From: SAMPLE INC, Remittance Info: "Test '
        'Remittance", Client Ref ID: RTR60880840833, GS ID: '
        "GI2228400005800, Clearing Ref: 001 REMI: Test Remittance EREF: "
        "RTR60880840833 CRNM: RTR-CdtrName DBNM: SAMPLE INC DACT: "
        "02122056789012205 DABA: 000000010",
    ),
    (
        "104108339",
        "USD",
        Decimal("5.27"),
        date(2023, 9, 6),
        "175",
        "SX22293073766088",
        "Check Deposit,- EREF: GS4N04L1COP45VY DACT: 100168723",
    ),
    (
        "104108339",
        "USD",
        Decimal("-101"),
        date(2023, 9, 6),
        "475",
        "SC2229300000152",
        "Check Paid,- REMI: UAT testing for Checks EREF: 01030340329 CRNM: "
        "TEST INC DBNM: ABC CORP CABA: 12345 CHKN: 006034594478",
    ),
    (
        "104108339",
        "USD",
        Decimal("3376.86"),
        date(2023, 9, 6),
        "275",
        "GI2318000014342",
        "Cash Concentration,From: SAMPLE INC, Account: 290000020437, GS "
        'Cash Concentration, "Structure ID: CC0000000", GS ID: '
        "GI2318000212121 REMI: Structure ID: CC0000082 EREF: "
        "e123456786d411eeaf020a58a9feac02 DBIC: GSCRUS33VIA CRNM: SAMPLE INC "
        "DBNM: SAMPLE INC DACT: 290000020437",
    ),
    (
        "104108339",
        "USD",
        Decimal("50"),
        date(2023, 9, 6),
        "165",
        "SPB2321284264201",
        "ACH Debit Collection,Entry Description: BILL PMT; -, SEC: CCD, "
        "Client Ref ID: AB/GS/DDFILEAB0001/DDBAB0001, GS ID: "
        "SPB2321284264201 EREF: AB/GS/DDFILEAB0001/DDBAB0001 CRNM: SAMPLE "
        "LLP DACT: ACHCONTROLINUSD01",
    ),
    (
        "104108339",
        "USD",
        Decimal("-442.5"),
        date(2023, 9, 6),
        "475",
        "SC2323300002416",
        "Check Paid,To: TEST AND COMPANY LLC, Check Serial Number: 24108, "
        "GS ID: SC2323300002416 EREF: 8ce1829175a74ec88d67010dd7fb6132 CRNM: "
        "TEST AND COMPANY LLC DBNM: Sample Inc. CABA: 0 CHKN: 24108",
    ),
    (
        "104108339",
        "USD",
        Decimal("-300000"),
        date(2023, 9, 6),
        "495",
        "GI2323300009168",
        'Outgoing Wire,To: TEST AND COMPANY, Remittance Info: "08/18/23 '
        'Invoice - Sample", Client Ref ID: 3785726, GS ID: GI2323300009168, '
        "Clearing Ref: 20230821MMQFMPU7004100 CREF: 20230821MMQFMPU7004100 "
        "REMI: 08/18/23 Invoice - Sample EREF: 3785726 CRNM: TEST AND "
        "COMPANY DBNM: Sample Inc. CACT: 609873838 CABA: 021000021",
    ),
    (
        "104108339",
        "USD",
        Decimal("37979996.24"),
        date(2023, 9, 6),
        "195",
        "GI2323300007089",
        "Incoming Wire,From: TEST AND COMPANY, Client Ref ID: "
        "20230821J1Q5040C000707, GS ID: GI2323300007089, Clearing Ref: "
        "20230821J1Q5040C000707 CREF: 20230821J1Q5040C000707 EREF: "
        "20230821J1Q5040C000707 CRNM: SAMPLE INC DBNM: TEST AND COMPANY "
        "DACT: 000001000600427",
    ),
    (
        "104108339",
        "USD",
        Decimal("-4634.62"),
        date(2023, 9, 6),
        "698",
        "M8916_20230818_001",
        "Fees,Fees For Account: XXXXXXXX-0186",
    ),
    (
        "104108339",
        "USD",
        Decimal("17.64"),
        date(2023, 9, 6),
        "354",
        "SBD85710_20230731_0021",
        "Interest,Interest For Account: XXXXXXXX-3074, Period: Jul 1, 2023 "
        "to Jul 31, 2023",
    ),
)


def _rows(path: Path) -> list[tuple[object, ...]]:
    """Return the parsed transactions of ``path`` as comparable tuples."""
    return [
        (
            t.account_id,
            t.currency,
            t.amount,
            t.booking_date,
            t.reference,
            t.transaction_id,
            t.description,
        )
        for t in load_bai2_file(path)
    ]


def test_sample1_transactions_match_golden() -> None:
    """sample1 (value-dated V records, CAD) parses to the pinned list."""
    assert _rows(SAMPLE1) == list(_SAMPLE1_EXPECTED)


def test_sample1_summary_matches_golden() -> None:
    """sample1's full Bai2Summary is pinned exactly."""
    summary = summarize_bai2(SAMPLE1.read_text(encoding="utf-8"))
    assert summary == Bai2Summary(
        file_id="001",
        group_count=1,
        account_count=2,
        transaction_count=17,
        currency="CAD",
    )


def test_sample1_account_continuations_do_not_corrupt() -> None:
    """The 88 records continuing the 03 summary emit no transaction.

    sample1's ``88,100,000000000208500,...`` lines continue an ``03``
    account summary, not a ``16``. They must be dropped, leaving exactly
    the 17 real postings with clean descriptions (no leaked ``100,...``).
    """
    txns = load_bai2_file(SAMPLE1)
    assert len(txns) == 17
    assert all(
        t.description is not None and "000000000208500" not in t.description
        for t in txns
    )


def test_sample5_transactions_match_golden() -> None:
    """sample5 (issue #113: commas/slashes in text) parses exactly."""
    assert _rows(SAMPLE5) == list(_SAMPLE5_EXPECTED)


def test_sample5_summary_matches_golden() -> None:
    """sample5's full Bai2Summary is pinned exactly."""
    summary = summarize_bai2(SAMPLE5.read_text(encoding="utf-8"))
    assert summary == Bai2Summary(
        file_id="1",
        group_count=1,
        account_count=5,
        transaction_count=20,
        currency="USD",
    )


def test_sample5_commas_in_text_preserved_verbatim() -> None:
    """The free-text field keeps its internal commas (the core bug fix).

    Before the fix the loader split the whole ``16`` record on commas, so
    everything after the first comma in the text was lost or mangled.
    """
    first = load_bai2_file(SAMPLE5)[0]
    assert first.description is not None
    # The full structured text, commas included, must survive.
    assert (
        "Entry Description: EXP; -, SEC: CCD, Client Ref ID: 1111"
        in first.description
    )


def test_sample5_slashes_in_text_and_ref_preserved() -> None:
    """A '/' inside a reference / text field is not treated as terminator.

    sample5 has ``Client Ref ID: AB/GS/TEST0001/RPBA0001`` and a bank ref
    ``AB/GS/RPFILERP0001/RPBA0001``; both contain slashes mid-record.
    """
    txns = load_bai2_file(SAMPLE5)
    slashed = next(t for t in txns if t.reference == "165")
    assert slashed.transaction_id == "SPB2321284264201"
    assert slashed.description is not None
    assert "AB/GS/DDFILEAB0001/DDBAB0001" in slashed.description


def test_sample5_colon_continuation_captured() -> None:
    """A '88:' colon-delimited continuation is still attached as text."""
    txns = load_bai2_file(SAMPLE5)
    check_return = next(t for t in txns if t.reference == "255")
    assert check_return.description is not None
    # 'EREF: 07370568132' arrives via a '88:EREF: ...' colon-form line.
    assert "EREF: 07370568132" in check_return.description
