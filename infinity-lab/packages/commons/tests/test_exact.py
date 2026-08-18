"""Tests for commons.core.exact (exact Fraction arithmetic)."""

from __future__ import annotations

from fractions import Fraction

import pytest

from commons.core.exact import (
    geometric_partial_sum,
    geometric_series_limit,
    half_power,
    to_fraction,
)


def test_half_power_basic() -> None:
    assert half_power(0) == Fraction(1, 1)
    assert half_power(1) == Fraction(1, 2)
    assert half_power(10) == Fraction(1, 1024)


def test_half_power_1075_is_positive_unit_numerator() -> None:
    val = half_power(1075)
    assert isinstance(val, Fraction)
    assert val > 0  # strictly positive despite being below the smallest float
    assert val.numerator == 1
    assert val.denominator == 1 << 1075


def test_half_power_negative_raises() -> None:
    with pytest.raises(ValueError):
        half_power(-1)


def test_to_fraction_variants() -> None:
    assert to_fraction(3) == Fraction(3)
    assert to_fraction("0.1") == Fraction(1, 10)  # exact decimal via string
    assert to_fraction(0.5) == Fraction(1, 2)  # exact IEEE value
    assert to_fraction(Fraction(2, 7)) == Fraction(2, 7)


def test_to_fraction_rejects_bool() -> None:
    with pytest.raises(TypeError):
        to_fraction(True)


def test_geometric_partial_sum_zeno() -> None:
    # 1/2 + 1/4 + 1/8 + 1/16 = 15/16
    s = geometric_partial_sum(Fraction(1, 2), Fraction(1, 2), 4)
    assert s == Fraction(15, 16)


def test_geometric_partial_sum_zero_terms() -> None:
    assert geometric_partial_sum(5, Fraction(1, 3), 0) == Fraction(0)


def test_geometric_partial_sum_ratio_one() -> None:
    assert geometric_partial_sum(2, 1, 4) == Fraction(8)


def test_geometric_partial_sum_negative_terms_raises() -> None:
    with pytest.raises(ValueError):
        geometric_partial_sum(1, Fraction(1, 2), -1)


def test_geometric_series_limit_zeno_is_one() -> None:
    assert geometric_series_limit(Fraction(1, 2), Fraction(1, 2)) == Fraction(1)


def test_geometric_series_limit_diverges_raises() -> None:
    with pytest.raises(ValueError):
        geometric_series_limit(1, 1)
