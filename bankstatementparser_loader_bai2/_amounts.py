# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2023-2026 Sebastien Rousseau. All rights reserved.

"""BAI2 amount fields: integer minor units to a major-unit ``Decimal``."""

from __future__ import annotations

import re
from decimal import Decimal

# An optional sign then ASCII digits only: ``str.isdigit`` and
# ``Decimal`` both accept non-ASCII digits, and ``Decimal`` also takes
# exponents, ``NaN`` and ``Infinity``, none of which a BAI2 amount is.
_AMOUNT_RE = re.compile(r"[+-]?[0-9]+")


def _amount_to_decimal(raw: str) -> Decimal:
    """Convert a BAI2 minor-unit integer amount to a major-unit Decimal.

    BAI2 amounts are unsigned integers in the currency's minor units
    (cents) with no decimal point. An empty field is treated as ``0``,
    and a leading ``+`` or ``-`` is tolerated.

    Args:
        raw: The raw amount field (e.g. ``"150000"`` for 1500.00).

    Returns:
        The amount as a :class:`decimal.Decimal` in major units.

    Raises:
        ValueError: If the field is anything but an optional sign and
            ASCII digits (a decimal point, an exponent, ``NaN``, or
            letters), rather than letting ``decimal`` guess at it.
    """
    text = raw.strip()
    if not text:
        return Decimal("0")
    if _AMOUNT_RE.fullmatch(text) is None:
        raise ValueError(
            f"BAI2 amount {text!r} is not an integer number of minor units"
        )
    return Decimal(text) / Decimal(100)
