"""Tests for the core p-adic arithmetic (padic_embeddings.core.padic).

Covers the valuation ``v_p``, the absolute value ``|x|_p`` (exact and float), and
the distance ``d_p`` on known values -- integers and :class:`fractions.Fraction` --
plus prime validation and the ``v_p(0) = inf`` convention. Pure stdlib + commons, so
these RUN on both interpreters.
"""

from __future__ import annotations

import math
from fractions import Fraction

import pytest

from padic_embeddings.core import padic


def test_valuation_of_prime_powers() -> None:
    assert padic.valuation(8, 2) == 3       # 8 = 2^3
    assert padic.valuation(12, 2) == 2      # 12 = 2^2 * 3
    assert padic.valuation(12, 3) == 1      # 12 = 3 * 4
    assert padic.valuation(49, 7) == 2      # 49 = 7^2
    assert padic.valuation(5, 2) == 0       # odd -> unit


def test_valuation_of_zero_is_infinite() -> None:
    assert padic.valuation(0, 2) == math.inf


def test_valuation_of_rationals() -> None:
    # v_2(3/4) = v_2(3) - v_2(4) = 0 - 2 = -2
    assert padic.valuation(Fraction(3, 4), 2) == -2
    # v_2(4/3) = 2 - 0 = 2
    assert padic.valuation(Fraction(4, 3), 2) == 2


def test_non_prime_rejected() -> None:
    with pytest.raises(ValueError):
        padic.valuation(10, 4)
    with pytest.raises(ValueError):
        padic.valuation(10, 1)


def test_non_integer_prime_rejected() -> None:
    with pytest.raises(TypeError):
        padic.is_prime(2.0)  # type: ignore[arg-type]


def test_abs_values_float_and_exact() -> None:
    assert padic.p_adic_abs(8, 2) == pytest.approx(2 ** -3)
    assert padic.p_adic_abs(0, 2) == 0.0
    assert padic.p_adic_abs(3, 2) == pytest.approx(1.0)   # unit
    assert padic.p_adic_abs_exact(8, 2) == Fraction(1, 8)
    assert padic.p_adic_abs_exact(0, 2) == Fraction(0)
    # A negative valuation makes |x|_p large: |3/4|_2 = 2^2 = 4.
    assert padic.p_adic_abs_exact(Fraction(3, 4), 2) == Fraction(4)


def test_distance_symmetry_and_identity() -> None:
    assert padic.distance(5, 5, 2) == 0.0
    assert padic.distance(5, 13, 2) == padic.distance(13, 5, 2)


def test_distance_known_value() -> None:
    # |5 - 13|_2 = |-8|_2 = 2^-3
    assert padic.distance(5, 13, 2) == pytest.approx(2 ** -3)
    assert padic.distance_exact(5, 13, 2) == Fraction(1, 8)


def test_distance_zero_iff_equal() -> None:
    assert padic.distance_exact(7, 7, 3) == Fraction(0)
    assert padic.distance_exact(7, 10, 3) > 0
