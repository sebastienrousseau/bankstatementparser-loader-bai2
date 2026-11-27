# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2023-2026 Sebastien Rousseau. All rights reserved.

"""A malformed ``16`` amount is refused with ``ValueError``.

BAI2 amounts are integers in minor units. Before this was pinned, a
non-numeric amount escaped as ``decimal.InvalidOperation`` (not a
``ValueError``, so callers catching the documented error crashed), and
an exponent such as ``1e5`` was silently accepted as 1000.00.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from bankstatementparser_loader_bai2 import load_bai2
from bankstatementparser_loader_bai2.loader import _amount_to_decimal


def _payload(amount: str) -> str:
    """Return a minimal BAI2 file whose one ``16`` record has ``amount``."""
    return (
        "01,S,R,260601,1200,F1,,,/\n"
        "02,R,O,1,260601,1200,USD,/\n"
        "03,0123456789,USD,/\n"
        f"16,165,{amount},Z,REF1,,Wire/\n"
    )


@pytest.mark.parametrize(
    "amount",
    ["abc", "12.50", "1e5", "NaN", "Infinity", "١٢٣", "1 000", "--5"],
)
def test_malformed_amount_raises_value_error(amount: str) -> None:
    """Anything but optional sign + ASCII digits is a ValueError."""
    with pytest.raises(ValueError, match="BAI2 amount"):
        load_bai2(_payload(amount))


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("150000", Decimal("1500.00")),
        (" 2500 ", Decimal("25.00")),
        ("+100", Decimal("1.00")),
        ("-5", Decimal("-0.05")),
        ("", Decimal("0")),
    ],
)
def test_well_formed_amounts_still_parse(raw: str, expected: Decimal) -> None:
    """Integer minor units (signed or not, blank as zero) still convert."""
    assert _amount_to_decimal(raw) == expected
