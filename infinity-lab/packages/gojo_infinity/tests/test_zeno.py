"""Lens 1 (Zeno / geometric series) -- pinned exact targets."""

from __future__ import annotations

from fractions import Fraction

from commons.core import half_power

from gojo_infinity.core import zeno


def test_partial_sums_exact_fractions() -> None:
    expected = [
        Fraction(1, 2), Fraction(3, 4), Fraction(7, 8), Fraction(15, 16),
        Fraction(31, 32), Fraction(63, 64), Fraction(127, 128), Fraction(255, 256),
    ]
    assert zeno.partial_sum_table(8) == expected


def test_partial_sums_decimal_table_S1_to_S8() -> None:
    expected = [0.5, 0.75, 0.875, 0.9375, 0.96875, 0.984375, 0.9921875, 0.99609375]
    got = [float(zeno.partial_sum(n)) for n in range(1, 9)]
    assert got == expected


def test_geometric_sum_is_exactly_one() -> None:
    assert zeno.geometric_sum(Fraction(1, 2), Fraction(1, 2)) == Fraction(1)
    assert zeno.zeno_series_sum() == Fraction(1)


def test_general_geometric_sum_exact() -> None:
    assert zeno.geometric_sum(Fraction(1), Fraction(1, 3)) == Fraction(3, 2)


def test_residual_strictly_positive_including_1075_exact() -> None:
    # The headline strict-positivity certificate: (1/2)^1075 > 0 EXACTLY,
    # exactly where the float path underflows to 0.
    assert zeno.residual(1075) == half_power(1075)
    assert zeno.residual(1075) > 0
    assert zeno.residual_is_strictly_positive(1075) is True
    for n in (0, 1, 2, 10, 60, 1075, 10000):
        assert zeno.residual_is_strictly_positive(n) is True


def test_float_residual_underflows_but_exact_does_not() -> None:
    # Documented failure-mode witness (NOT a correctness gate).
    assert zeno.float_residual_underflows_at(1075) is True
    assert zeno.residual(1075) > 0


def test_residual_halves_each_step() -> None:
    for n in range(1, 50):
        assert zeno.residual(n) * 2 == zeno.residual(n - 1)


def test_epsilon_N_oracle_exact_bracket() -> None:
    res = zeno.epsilon_N(Fraction(1, 1000))
    assert res.N == 10  # ceil(log2(1000)) = 10
    # Exact Fraction confirmation of minimality:
    assert half_power(res.N) < Fraction(1, 1000)
    assert half_power(res.N - 1) >= Fraction(1, 1000)
    assert res.residual_at_N == half_power(10)
    assert res.residual_before_N == half_power(9)


def test_arrival_time_series_converges_finite() -> None:
    # Total distance is 1, so at constant speed v the arrival time is 1/v -- finite.
    assert zeno.total_arrival_time(speed=Fraction(2)) == Fraction(1, 2)
    assert zeno.total_arrival_time(speed=Fraction(1)) == Fraction(1)
    assert zeno.total_arrival_time(speed=Fraction(1, 3)) == Fraction(3)


def test_step_distances_sum_to_one() -> None:
    total = sum((zeno.step_distance(n) for n in range(1, 40)), Fraction(0))
    assert total == zeno.partial_sum(39)


def test_verdict_is_fragile() -> None:
    assert zeno.verdict().verdict == "Fragile"
