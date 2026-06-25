# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2023-2026 Sebastien Rousseau. All rights reserved.

"""BAI2 -> bankstatementparser ``Transaction`` loader.

`BAI2 <https://www.bai.org/>`_ (Bank Administration Institute, version 2)
is the de-facto US cash-management file format that banks ship for
intraday and prior-day balance reporting. The published
`bankstatementparser <https://pypi.org/project/bankstatementparser/>`_
library does **not** parse BAI2; this companion loader fills that gap by
turning a BAI2 payload into a flat list of
:class:`bankstatementparser.transaction_models.Transaction` objects that
downstream deterministic logic can consume.

Supported (pragmatic) subset
----------------------------

BAI2 files are line-oriented. Each physical record is a sequence of
comma-delimited fields and ends with a ``/`` record delimiter. Every
record begins with a numeric *type code* identifying the record kind.
This loader implements the following records:

``01`` File Header
    ``01,senderId,receiverId,fileDate,fileTime,fileId,...`` -- the file
    must start with this record. ``fileId`` is captured for the summary.

``02`` Group Header
    ``02,ultimateReceiver,originator,groupStatus,asOfDate,asOfTime,currency,...``
    -- the group ``currency`` and ``asOfDate`` are captured. The as-of
    date becomes each transaction's ``booking_date``; the group
    currency is the fallback currency for accounts that omit one.

``03`` Account Identifier
    ``03,accountNumber,currencyCode,typeCode,amount,itemCount,fundsType,...``
    -- ``accountNumber`` and the optional account ``currencyCode`` are
    captured. The account currency, when present, overrides the group
    currency for every transaction under this account.

``16`` Transaction Detail
    ``16,typeCode,amount,fundsType,[funds-type subfields,]bankRefNum,customerRefNum,text``
    -- one transaction. ``amount`` is an integer in the account
    currency's minor units (see "Amounts" below). ``text`` becomes the
    description.

    The ``text`` field is **free-form and runs to the end of the
    record, commas included**. Real-world BAI2 puts structured prose
    there (``ACH Credit Payment,Entry Description: EXP; -, SEC: CCD,
    ...``), so the loader splits only the fixed leading fields and keeps
    the remainder verbatim rather than naively splitting the whole
    record on commas.

    The ``fundsType`` field selects how many subfields sit between it
    and ``bankRefNum``: ``V`` (value-dated) inserts ``valueDate`` and
    ``valueTime``; ``S`` (distributed availability) inserts three
    availability amounts; everything else (``0``/``1``/``2``/``Z`` or
    empty) inserts none. The loader counts these so ``bankRefNum``,
    ``customerRefNum``, and ``text`` are located correctly regardless of
    funds type.

``88`` Continuation
    Continues the text of the immediately preceding ``03`` or ``16``
    record; its content (everything after the leading ``88`` field,
    commas included) is appended to that record's description. A ``88``
    that continues an ``03`` account summary, or one that has no
    preceding detail to attach to, is dropped rather than mis-attached.

``49`` Account Trailer, ``98`` Group Trailer, ``99`` File Trailer
    Control-total records. This loader **ignores** them -- it does not
    validate the control sums. Ignoring is a deliberate, documented
    choice: the goal is faithful transaction extraction, not file-level
    reconciliation.

Any other (or unknown) leading type code is ignored so that vendor
extensions do not abort the parse.

Amounts
-------

BAI2 amounts are unsigned integers expressed in the account currency's
**minor units** (e.g. cents), with no decimal point. They are converted
to :class:`decimal.Decimal` by dividing by 100 -- ``Decimal`` is used
throughout (never ``float``) to avoid binary rounding error. An empty
amount field is treated as ``0``.

Sign convention (debit / credit)
---------------------------------

BAI2 transaction *type codes* are grouped into documented numeric ranges
that encode the direction of funds. This loader applies the following
convention based on the numeric range of the ``16`` record's type code:

* ``100``-``399`` -> **credit** (amount kept **positive**)
* ``400``-``699`` -> **debit** (amount made **negative**)
* ``700``-``799`` -> **loan** detail. Loan codes describe disbursements,
  advances, and payments on the loan side of a relationship file. This
  loader treats them as a **debit**-side movement (amount made
  **negative**), matching the "money leaving the reported balance"
  reading used for the ``400``-``699`` range.
* ``900``-``999`` -> **custom / summary / status**. These are
  non-detail codes (institution-specific status and summary lines, not
  individual postings). This loader **does not emit a Transaction** for
  them; they are skipped so a status line never pollutes the posting
  list. Any continuations attached to a skipped status code are dropped
  with it.
* anything else (including non-numeric codes) -> kept **positive**; the
  raw type code is preserved.

The raw BAI2 type code is always preserved on every emitted
``Transaction`` in both the ``category`` field (as ``bai2:<code>``) and
the ``reference`` field, so no information is lost.

Type-code descriptions
----------------------

A small, optional lookup of well-known BAI2 transaction type codes (for
example ``142`` "ACH credit" or ``475`` "Check paid") is used to enrich
the ``Transaction.description`` when the ``16`` record itself carries no
free-text. When the lookup has no entry, or the record already has text,
the record's own text is used unchanged.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from bankstatementparser.transaction_models import Transaction

__all__ = [
    "load_bai2",
    "load_bai2_file",
    "summarize_bai2",
    "Bai2Summary",
]

# ─── Sign-convention boundaries ──────────────────────────────────────────────

# Type-code ranges, documented in the module docstring and kept here as
# the single source of truth so the loader, the README, and the tests all
# agree. Each ``range`` is half-open (its stop is exclusive), so e.g.
# ``range(100, 400)`` spans the inclusive BAI2 codes 100-399.
_CREDIT_RANGE = range(100, 400)  # 100-399 -> credit  (positive)
_DEBIT_RANGE = range(400, 700)  # 400-699 -> debit   (negative)
_LOAN_RANGE = range(700, 800)  # 700-799 -> loan    (debit-side, negative)
_STATUS_RANGE = range(900, 1000)  # 900-999 -> custom/summary/status (skipped)


# Optional, well-known BAI2 transaction type-code descriptions. Used only
# to enrich a transaction whose ``16`` record carries no free-text; never
# overrides text the bank supplied. Intentionally small and fully tested.
_TYPE_CODE_DESCRIPTIONS: dict[str, str] = {
    "142": "ACH credit",
    "165": "Wire transfer credit",
    "301": "Commercial deposit",
    "475": "Check paid",
    "501": "Wire transfer debit",
}


def _description_for_type_code(type_code: str) -> str | None:
    """Return the well-known description for a BAI2 type code, if any.

    Args:
        type_code: The raw BAI2 ``16`` record type code.

    Returns:
        The mapped human-readable description, or ``None`` when the code
        is not in the optional lookup table.
    """
    return _TYPE_CODE_DESCRIPTIONS.get(type_code)


def _is_status_type_code(type_code: str) -> bool:
    """Return ``True`` for a ``900``-``999`` custom/summary/status code.

    These non-detail codes do not represent an individual posting, so the
    loader skips them rather than emitting a misleading ``Transaction``.

    Args:
        type_code: The raw BAI2 ``16`` record type code.

    Returns:
        ``True`` when the code parses as an integer in ``900``-``999``,
        otherwise ``False`` (including for non-numeric codes).
    """
    try:
        return int(type_code) in _STATUS_RANGE
    except ValueError:
        return False


# ─── Record tokeniser ────────────────────────────────────────────────────────


def _iter_records(text: str) -> Iterator[str]:
    """Yield each BAI2 record as a single terminator-stripped line.

    Tolerates CRLF / LF line endings, blank lines, trailing spaces, and
    the optional trailing ``/`` record delimiter. Exactly one trailing
    ``/`` (after stripping surrounding whitespace) is removed: it is the
    record terminator. A ``/`` is *not* stripped from anywhere else in
    the line, because the free-text field of a ``16`` / ``88`` record can
    legitimately contain ``/`` (e.g. ``Client Ref ID: AB/GS/FILE0001``),
    and that text always sits mid-line, never at the record end.

    Returning the whole record line (rather than pre-split fields) lets
    each record type decide for itself how many leading fields to split
    and where its free-text begins, so commas inside a ``16`` / ``88``
    text field are preserved.

    Args:
        text: The raw BAI2 payload.

    Yields:
        One record string per non-empty line, in file order.
    """
    for raw_line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = raw_line.strip()
        if not line:
            continue
        # Drop exactly one trailing '/' record terminator (and any
        # whitespace around it). In-text slashes are never line-final.
        if line.endswith("/"):
            line = line[:-1].rstrip()
        if not line:
            continue
        yield line


def _record_code(record: str) -> str:
    """Return the leading numeric type code of a record line.

    The code is the first comma-delimited field. A handful of banks emit
    ``88:`` (colon) instead of ``88,``; the colon variant is normalised
    here so the continuation still routes correctly.

    Args:
        record: One terminator-stripped record line.

    Returns:
        The leading type code, trimmed.
    """
    head = record.split(",", 1)[0]
    # Tolerate the rare '88:' colon-delimited continuation form.
    head = head.split(":", 1)[0]
    return head.strip()


def _split_record(record: str) -> list[str]:
    """Split a non-text BAI2 record into its trimmed comma-delimited fields.

    Used for control records (``01``/``02``/``03``/``49``/``98``/``99``)
    whose fields never contain embedded commas. ``16`` and ``88`` records
    are parsed separately so their free-text field is preserved verbatim.

    Args:
        record: One terminator-stripped record line.

    Returns:
        The trimmed fields in order.
    """
    return [field.strip() for field in record.split(",")]


# Funds-type codes that insert extra subfields between the funds-type
# field and the bank reference in a ``16`` record. The value is the
# number of subfields inserted. Codes not listed here (``0``/``1``/``2``/
# ``Z`` or an empty funds type) insert none.
_FUNDS_TYPE_SUBFIELDS: dict[str, int] = {
    "V": 2,  # value-dated: valueDate, valueTime
    "S": 3,  # distributed availability: immediate, one-day, more-than-one-day
}


def _text_field_index(funds_type: str) -> int:
    """Return the field index at which a ``16`` record's free-text begins.

    The base layout is ``16,typeCode,amount,fundsType,bankRef,customerRef,
    text`` (text at index 6). A ``V`` or ``S`` funds type inserts extra
    subfields after ``fundsType``, pushing ``bankRef``/``customerRef``/
    ``text`` further right by that many positions.

    Args:
        funds_type: The raw funds-type field (index 3) of the ``16``
            record.

    Returns:
        The zero-based index of the first free-text field.
    """
    return 6 + _FUNDS_TYPE_SUBFIELDS.get(funds_type.strip().upper(), 0)


def _split_16(record: str) -> tuple[str, str, str, str, str]:
    """Split a ``16`` Transaction Detail into its parts, text kept verbatim.

    The leading fixed fields are split on commas; the free-text field is
    everything from its starting index onward, joined back with commas so
    embedded commas survive. The text's own leading / trailing whitespace
    is trimmed but its internal commas and slashes are preserved.

    Args:
        record: One terminator-stripped ``16`` record line.

    Returns:
        A ``(type_code, amount, bank_ref, customer_ref, text)`` tuple.
    """
    parts = record.split(",")
    type_code = parts[1].strip() if len(parts) > 1 else ""
    amount = parts[2].strip() if len(parts) > 2 else ""
    funds_type = parts[3] if len(parts) > 3 else ""
    text_index = _text_field_index(funds_type)
    bank_ref = (
        parts[text_index - 2].strip() if len(parts) > text_index - 2 else ""
    )
    customer_ref = (
        parts[text_index - 1].strip() if len(parts) > text_index - 1 else ""
    )
    text = (
        ",".join(parts[text_index:]).strip() if len(parts) > text_index else ""
    )
    return type_code, amount, bank_ref, customer_ref, text


def _continuation_text(record: str) -> str:
    """Return the verbatim text carried by an ``88`` continuation record.

    Everything after the leading ``88`` field is the continuation text,
    commas included. Some banks emit ``88:`` (colon) instead of ``88,``;
    both are tolerated. The text is trimmed at its ends only.

    Args:
        record: One terminator-stripped ``88`` record line.

    Returns:
        The continuation text, or ``""`` when the record carries none.
    """
    for separator in (",", ":"):
        head, found, tail = record.partition(separator)
        if found and head.strip() == "88":
            return tail.strip()
    return ""


# ─── Field helpers ───────────────────────────────────────────────────────────


def _field(fields: list[str], index: int) -> str:
    """Return the field at ``index`` or an empty string if absent.

    Args:
        fields: The split fields of one record.
        index: Zero-based field position.

    Returns:
        The trimmed field value, or ``""`` when the position is missing.
    """
    if 0 <= index < len(fields):
        return fields[index]
    return ""


def _amount_to_decimal(raw: str) -> Decimal:
    """Convert a BAI2 minor-unit integer amount to a major-unit Decimal.

    BAI2 amounts are unsigned integers in the currency's minor units
    (cents) with no decimal point. An empty field is treated as ``0``.

    Args:
        raw: The raw amount field (e.g. ``"150000"`` for 1500.00).

    Returns:
        The amount as a :class:`decimal.Decimal` in major units.
    """
    text = raw.strip()
    if not text:
        return Decimal("0")
    return Decimal(text) / Decimal(100)


def _signed_amount(type_code: str, magnitude: Decimal) -> Decimal:
    """Apply the documented sign convention to a transaction magnitude.

    Args:
        type_code: The raw BAI2 ``16`` record type code.
        magnitude: The non-negative amount in major units.

    Returns:
        The magnitude negated for debit type codes (``400``-``699``) and
        loan detail codes (``700``-``799``, treated as debit-side
        disbursements), otherwise returned unchanged (credits and unknown
        codes stay positive).
    """
    try:
        code = int(type_code)
    except ValueError:
        return magnitude
    if code in _DEBIT_RANGE or code in _LOAN_RANGE:
        return -magnitude
    return magnitude


def _parse_bai2_date(raw: str) -> date | None:
    """Parse a BAI2 ``YYMMDD`` date into a :class:`datetime.date`.

    Years are interpreted with a sliding window matching industry
    practice: ``00``-``79`` -> ``20YY``, ``80``-``99`` -> ``19YY``. An
    empty or malformed value yields ``None`` rather than raising, so a
    missing as-of date never aborts a parse.

    Args:
        raw: The raw 6-digit date field.

    Returns:
        The parsed date, or ``None`` when absent or unparseable.
    """
    text = raw.strip()
    if len(text) != 6 or not text.isdigit():
        return None
    year = int(text[0:2])
    century = 2000 if year < 80 else 1900
    try:
        return datetime.strptime(
            f"{century + year:04d}{text[2:4]}{text[4:6]}", "%Y%m%d"
        ).date()
    except ValueError:
        # Six digits that pass ``isdigit`` can still be an impossible
        # calendar date (e.g. month ``13`` or ``00``, or 30 February).
        # ``strptime`` rejects those, and a malformed as-of date must
        # never abort the parse, so we yield ``None`` instead of raising.
        return None


# ─── Working state ───────────────────────────────────────────────────────────


@dataclass
class _PendingTransaction:
    """Mutable accumulator for one ``16`` record and its continuations."""

    type_code: str
    amount: Decimal
    bank_ref: str
    customer_ref: str
    text_parts: list[str]
    account_number: str | None
    currency: str | None
    booking_date: date | None
    index: int

    def to_transaction(self) -> Transaction:
        """Materialise the accumulated state into a ``Transaction``.

        Returns:
            A frozen :class:`~bankstatementparser.transaction_models.Transaction`
            with the BAI2 sign convention applied and the raw type code
            preserved in both ``category`` and ``reference``.
        """
        description = " ".join(
            part for part in self.text_parts if part
        ).strip()
        # When the record carries no free-text, fall back to the optional
        # well-known type-code description (e.g. 475 -> "Check paid").
        if not description:
            description = _description_for_type_code(self.type_code) or ""
        transaction_id = self.bank_ref or self.customer_ref or None
        return Transaction(
            account_id=self.account_number,
            currency=self.currency,
            amount=_signed_amount(self.type_code, self.amount),
            booking_date=self.booking_date,
            description=description or None,
            reference=self.type_code or None,
            transaction_id=transaction_id,
            category=f"bai2:{self.type_code}" if self.type_code else None,
            source="bai2",
            source_index=self.index,
        )


# ─── Summary model ───────────────────────────────────────────────────────────


@dataclass
class Bai2Summary:
    """High-level counts and identifiers for a parsed BAI2 file.

    Attributes:
        file_id: The ``fileId`` field from the ``01`` File Header.
        group_count: Number of ``02`` Group Header records.
        account_count: Number of ``03`` Account Identifier records.
        transaction_count: Number of emitted transactions -- one per
            ``16`` Transaction Detail record, excluding skipped
            ``900``-``999`` custom/summary/status codes.
        currency: The first currency seen (account currency preferred,
            otherwise the group currency), or ``None`` if none was given.
    """

    file_id: str | None
    group_count: int
    account_count: int
    transaction_count: int
    currency: str | None


# ─── Public API ──────────────────────────────────────────────────────────────


def load_bai2(text: str) -> list[Transaction]:
    """Parse a BAI2 payload into a flat list of ``Transaction`` objects.

    Every ``16`` Transaction Detail record across all groups and
    accounts becomes one transaction, carrying its account number and
    currency. ``88`` continuation records extend the description of the
    preceding ``03`` or ``16`` record.

    Args:
        text: The raw BAI2 payload. CRLF / LF endings, blank lines, and
            an optional trailing ``/`` per record are all tolerated.

    Returns:
        The parsed transactions in file order. May be empty if the file
        contains headers but no ``16`` records.

    Raises:
        ValueError: If the file does not start with an ``01`` File
            Header record.
    """
    records = list(_iter_records(text))
    if not records or _split_record(records[0])[0] != "01":
        raise ValueError("BAI2 payload must start with an '01' File Header")

    transactions: list[Transaction] = []
    # The single in-progress ``16`` transaction, or ``None``. A live
    # ``pending`` is the *only* thing an ``88`` continuation attaches to:
    # every non-``16`` record (and a skipped status ``16``) flushes it to
    # ``None`` first, so a continuation after one of those is dropped.
    pending: _PendingTransaction | None = None
    group_currency: str | None = None
    group_as_of: date | None = None
    account_number: str | None = None
    account_currency: str | None = None

    def _flush() -> None:
        """Append any in-progress transaction to the output list."""
        nonlocal pending
        if pending is not None:
            transactions.append(pending.to_transaction())
            pending = None

    for record in records:
        code = _record_code(record)
        if code == "02":
            _flush()
            fields = _split_record(record)
            group_as_of = _parse_bai2_date(_field(fields, 4))
            group_currency = _field(fields, 6) or None
            account_number = None
            account_currency = None
        elif code == "03":
            _flush()
            fields = _split_record(record)
            account_number = _field(fields, 1) or None
            account_currency = _field(fields, 2) or None
        elif code == "16":
            _flush()
            type_code, amount, bank_ref, customer_ref, txt = _split_16(record)
            if _is_status_type_code(type_code):
                # 900-999 custom/summary/status codes are not postings:
                # emit nothing. The _flush above already cleared pending,
                # so any continuation that follows is dropped with it.
                continue
            pending = _PendingTransaction(
                type_code=type_code,
                amount=_amount_to_decimal(amount),
                bank_ref=bank_ref,
                customer_ref=customer_ref,
                text_parts=[txt],
                account_number=account_number,
                currency=account_currency or group_currency,
                booking_date=group_as_of,
                index=len(transactions),
            )
        elif code == "88":
            # Continuation text is everything after the leading '88',
            # commas and slashes included, kept verbatim.
            if pending is not None:
                pending.text_parts.append(_continuation_text(record))
            # A continuation of an '03' account note (or one with no
            # preceding detail) has no pending transaction to attach to;
            # it is informational and dropped here.
        elif code in {"49", "98", "99"}:
            # Trailer / control-total records are intentionally ignored.
            _flush()
        # 01 and any unknown code: nothing to accumulate.

    _flush()
    return transactions


def load_bai2_file(path: str | Path) -> list[Transaction]:
    """Parse a BAI2 file from disk into ``Transaction`` objects.

    Args:
        path: Filesystem path to the BAI2 file. UTF-8 is assumed.

    Returns:
        The parsed transactions, identical to calling :func:`load_bai2`
        on the file's text content.

    Raises:
        ValueError: If the file does not start with an ``01`` record.
        OSError: If the file cannot be read.
    """
    return load_bai2(Path(path).read_text(encoding="utf-8"))


def summarize_bai2(text: str) -> Bai2Summary:
    """Summarise a BAI2 payload without materialising every transaction.

    Args:
        text: The raw BAI2 payload.

    Returns:
        A :class:`Bai2Summary` with the file id, group / account /
        transaction counts, and the first currency observed.

    Raises:
        ValueError: If the file does not start with an ``01`` record.
    """
    records = list(_iter_records(text))
    if not records or _record_code(records[0]) != "01":
        raise ValueError("BAI2 payload must start with an '01' File Header")

    file_id = _field(_split_record(records[0]), 5) or None
    group_count = 0
    account_count = 0
    transaction_count = 0
    currency: str | None = None
    group_currency: str | None = None

    for record in records:
        code = _record_code(record)
        if code == "02":
            group_count += 1
            group_currency = _field(_split_record(record), 6) or None
            if currency is None and group_currency is not None:
                currency = group_currency
        elif code == "03":
            account_count += 1
            account_currency = _field(_split_record(record), 2) or None
            if account_currency is not None:
                currency = account_currency
        elif code == "16":
            # Count only emitted postings; 900-999 custom/summary/status
            # codes are skipped by load_bai2, so they are not counted here
            # either, keeping the summary and the transaction list in step.
            if not _is_status_type_code(_split_16(record)[0]):
                transaction_count += 1

    return Bai2Summary(
        file_id=file_id,
        group_count=group_count,
        account_count=account_count,
        transaction_count=transaction_count,
        currency=currency,
    )
