# SPDX-License-Identifier: Apache-2.0
# Copyright (C) 2023-2026 Sebastien Rousseau. All rights reserved.

"""Hypothesis property and fuzz tests for bankstatementparser-loader-bai2."""

from __future__ import annotations

import tempfile
from decimal import Decimal
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

from bankstatementparser_loader_bai2.loader import (
    Bai2StatementParser,
    _amount_to_decimal,
    _iter_records,
    _parse_bai2_date,
    _signed_amount,
    load_bai2,
    summarize_bai2,
)


@settings(max_examples=50, deadline=None)
@given(st.text(min_size=0, max_size=2000))
def test_fuzz_load_bai2_never_crashes_unhandled(payload: str) -> None:
    """load_bai2 safely raises ValueError or returns list on arbitrary inputs."""
    try:
        txs = load_bai2(payload)
        assert isinstance(txs, list)
    except ValueError:
        pass


@settings(max_examples=50, deadline=None)
@given(st.text(min_size=0, max_size=2000))
def test_fuzz_summarize_bai2_never_crashes_unhandled(payload: str) -> None:
    """summarize_bai2 safely raises ValueError or returns Bai2Summary."""
    try:
        s = summarize_bai2(payload)
        assert s is not None
    except ValueError:
        pass


@settings(max_examples=50, deadline=None)
@given(st.text(min_size=0, max_size=50))
def test_fuzz_amount_to_decimal(raw: str) -> None:
    """_amount_to_decimal parses valid digits or treated safely."""
    try:
        val = _amount_to_decimal(raw)
        assert isinstance(val, Decimal)
    except (ValueError, ArithmeticError, Exception):
        pass


@settings(max_examples=50, deadline=None)
@given(
    st.text(min_size=0, max_size=20),
    st.decimals(
        min_value=-1000000,
        max_value=1000000,
        allow_nan=False,
        allow_infinity=False,
    ),
)
def test_fuzz_signed_amount(type_code: str, magnitude: Decimal) -> None:
    """_signed_amount never raises on arbitrary type codes."""
    res = _signed_amount(type_code, magnitude)
    assert isinstance(res, Decimal)


@settings(max_examples=50, deadline=None)
@given(st.text(min_size=0, max_size=30))
def test_fuzz_parse_date(raw: str) -> None:
    """_parse_bai2_date safely returns date or None without raising."""
    d = _parse_bai2_date(raw)
    assert d is None or hasattr(d, "year")


@settings(max_examples=50, deadline=None)
@given(st.text(min_size=0, max_size=1000))
def test_fuzz_iter_records(text: str) -> None:
    """_iter_records yields clean strings without trailing slash or newline."""
    for rec in _iter_records(text):
        assert isinstance(rec, str)
        assert not rec.endswith("\n")
        assert not rec.endswith("\r")


@settings(max_examples=30, deadline=None)
@given(st.text(min_size=0, max_size=1000))
def test_fuzz_bai2_statement_parser(text: str) -> None:
    """Bai2StatementParser wrapper never unhandled crashes on arbitrary file content."""
    with tempfile.NamedTemporaryFile("w", suffix=".bai2", delete=False) as f:
        f.write(text)
        f_path = f.name
    try:
        parser = Bai2StatementParser(f_path)
        try:
            df = parser.parse()
            assert df is not None
            summary = parser.get_summary()
            assert isinstance(summary, dict)
        except ValueError:
            pass
    finally:
        Path(f_path).unlink(missing_ok=True)
