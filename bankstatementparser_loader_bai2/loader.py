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
    ``16,typeCode,amount,fundsType,bankRefNum,customerRefNum,text`` --
    one transaction. ``amount`` is an integer in the account currency's
    minor units (see "Amounts" below). ``text`` becomes the
    description.

``88`` Continuation
    Continues the text of the immediately preceding ``03`` or ``16``
    record; its content is appended to that record's description.

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

BAI2 transaction *type codes* encode the direction of funds. This loader
applies the following documented convention based on the numeric range
of the ``16`` record's type code:

* ``100``-``399`` -> **credit** (amount kept **positive**)
* ``400``-``699`` -> **debit** (amount made **negative**)
* anything else -> kept **positive**; the raw type code is preserved.

The raw BAI2 type code is always preserved on the resulting
``Transaction`` in both the ``category`` field (as ``bai2:<code>``) and
the ``reference`` field, so no information is lost even for codes outside
the two ranges above.
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

# Inclusive lower/upper bounds for the credit and debit type-code ranges.
# Documented in the module docstring; kept here as the single source of
# truth so the loader and the tests agree.
_CREDIT_RANGE = range(100, 400)  # 100-399 -> credit (positive)
_DEBIT_RANGE = range(400, 700)  # 400-699 -> debit (negative)


# ─── Record tokeniser ────────────────────────────────────────────────────────


def _iter_records(text: str) -> Iterator[list[str]]:
    """Yield each BAI2 record as a list of its comma-delimited fields.

    Tolerates CRLF / LF line endings, blank lines, and an optional
    trailing ``/`` record delimiter. The trailing ``/`` (and anything a
    bank may append after it) is stripped before the fields are split.

    Args:
        text: The raw BAI2 payload.

    Yields:
        One ``list[str]`` of fields per non-empty record, in file order.
    """
    for raw_line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = raw_line.strip()
        if not line:
            continue
        # A record ends with the '/' delimiter; drop it (and any
        # trailing remainder) so the final field is clean.
        if "/" in line:
            line = line[: line.index("/")]
        line = line.rstrip()
        if not line:
            continue
        yield [field.strip() for field in line.split(",")]


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
        The magnitude negated for debit type codes (``400``-``699``),
        otherwise returned unchanged (credits and unknown codes stay
        positive).
    """
    try:
        code = int(type_code)
    except ValueError:
        return magnitude
    if code in _DEBIT_RANGE:
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
    except ValueError:  # pragma: no cover - guarded by the isdigit check
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
        transaction_count: Number of ``16`` Transaction Detail records.
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
    if not records or _field(records[0], 0) != "01":
        raise ValueError("BAI2 payload must start with an '01' File Header")

    transactions: list[Transaction] = []
    pending: _PendingTransaction | None = None
    # Continuation target: 0 = none, 3 = last account note, 16 = pending tx.
    continuation_target = 0
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

    for fields in records:
        code = _field(fields, 0)
        if code == "02":
            _flush()
            continuation_target = 0
            group_as_of = _parse_bai2_date(_field(fields, 4))
            group_currency = _field(fields, 6) or None
            account_number = None
            account_currency = None
        elif code == "03":
            _flush()
            continuation_target = 3
            account_number = _field(fields, 1) or None
            account_currency = _field(fields, 2) or None
        elif code == "16":
            _flush()
            continuation_target = 16
            pending = _PendingTransaction(
                type_code=_field(fields, 1),
                amount=_amount_to_decimal(_field(fields, 2)),
                bank_ref=_field(fields, 4),
                customer_ref=_field(fields, 5),
                text_parts=[_field(fields, 6)],
                account_number=account_number,
                currency=account_currency or group_currency,
                booking_date=group_as_of,
                index=len(transactions),
            )
        elif code == "88":
            # Continuation text is every field after the leading '88'.
            note = ",".join(fields[1:]).strip()
            if continuation_target == 16 and pending is not None:
                pending.text_parts.append(note)
            # A continuation of an '03' account note has no transaction
            # to attach to yet; it is informational and dropped here.
        elif code in {"49", "98", "99"}:
            # Trailer / control-total records are intentionally ignored.
            _flush()
            continuation_target = 0
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
    if not records or _field(records[0], 0) != "01":
        raise ValueError("BAI2 payload must start with an '01' File Header")

    file_id = _field(records[0], 5) or None
    group_count = 0
    account_count = 0
    transaction_count = 0
    currency: str | None = None
    group_currency: str | None = None

    for fields in records:
        code = _field(fields, 0)
        if code == "02":
            group_count += 1
            group_currency = _field(fields, 6) or None
            if currency is None and group_currency is not None:
                currency = group_currency
        elif code == "03":
            account_count += 1
            account_currency = _field(fields, 2) or None
            if account_currency is not None:
                currency = account_currency
        elif code == "16":
            transaction_count += 1

    return Bai2Summary(
        file_id=file_id,
        group_count=group_count,
        account_count=account_count,
        transaction_count=transaction_count,
        currency=currency,
    )
