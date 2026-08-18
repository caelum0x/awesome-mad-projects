"""Lens 2 (Lebesgue measure) -- pinned exact targets."""

from __future__ import annotations

from fractions import Fraction

from gojo_infinity.core import measure


def test_subdivision_points_exact() -> None:
    assert measure.subdivision_set(4) == [
        Fraction(1, 2), Fraction(3, 4), Fraction(7, 8), Fraction(15, 16),
    ]


def test_cover_interval_length_exact() -> None:
    eps = Fraction(1, 10)
    assert measure.cover_interval_length(1, eps) == eps * Fraction(1, 2)
    assert measure.cover_interval_length(3, eps) == eps * Fraction(1, 8)


def test_total_cover_length_equals_eps_times_one_minus_tail() -> None:
    eps = Fraction(1, 10)
    for terms in (1, 2, 5, 10, 20):
        total = measure.total_cover_length(eps, terms)
        assert total == eps * (Fraction(1) - Fraction(1, 2) ** terms)
        assert total + measure.cover_tail_length(eps, terms) == eps


def test_total_cover_length_converges_exactly_to_eps() -> None:
    # The headline m(Z) target: the full cover length is EXACTLY eps.
    eps = Fraction(1, 10)
    assert measure.outer_measure_upper_bound(eps) == eps
    # partial totals strictly increase toward eps, never exceeding it.
    prev = Fraction(0)
    for terms in range(1, 30):
        total = measure.total_cover_length(eps, terms)
        assert prev < total < eps
        prev = total


def test_infimum_over_eps_drives_measure_to_zero() -> None:
    eps_values = [Fraction(1, 10 ** k) for k in range(1, 8)]
    assert measure.infimum_over_eps(eps_values) == Fraction(1, 10 ** 7)
    # As eps -> 0 the achievable cover length -> 0, hence m(Z) = 0.
    assert measure.lebesgue_measure_of_Z() == Fraction(0)


def test_documented_lebesgue_facts() -> None:
    assert measure.measure_interval(Fraction(1, 3), Fraction(3, 4)) == Fraction(5, 12)
    assert measure.measure_empty() == Fraction(0)
    assert measure.measure_singleton(Fraction(1, 2)) == Fraction(0)
    assert measure.measure_countable_union_of_null_sets(
        [Fraction(0), Fraction(0), Fraction(0)]
    ) == Fraction(0)


def test_verdict_is_fragile() -> None:
    assert measure.verdict().verdict == "Fragile"
