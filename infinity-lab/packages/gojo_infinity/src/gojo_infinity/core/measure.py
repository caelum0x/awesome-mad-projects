"""Lens 2 -- Lebesgue measure. Verdict: FRAGILE.

How "big" is the barrier really? The subdivision points of Lens 1 form the set

    Z = { z_n = 1 - 1/2^n : n >= 1 } = { 1/2, 3/4, 7/8, 15/16, ... },

a COUNTABLY INFINITE set of isolated points. Its Lebesgue outer measure is

    m*(A) = inf { sum_n |I_n| : A subset of union of open intervals I_n }.

Cover each point ``z_n`` by an interval of width ``eps/2^n`` centred on it,

    I_n = ( z_n - eps/2^(n+1), z_n + eps/2^(n+1) ),   so   |I_n| = eps/2^n,

and the total length telescopes to

    sum_{n=1}^inf eps/2^n = eps * sum_{n=1}^inf 1/2^n = eps * 1 = eps.

Since ``eps > 0`` is arbitrary, the infimum -- hence ``m(Z)`` -- is ``0``. The
barrier is countably many points of TOTAL LENGTH ZERO: measure-theoretically
negligible. Infinity is FRAGILE.

Exact covering lengths use :class:`fractions.Fraction`. Pure core: stdlib +
``commons.core`` only.
"""

from __future__ import annotations

from fractions import Fraction
from typing import List

from commons.core import geometric_partial_sum, half_power, to_fraction

from gojo_infinity.core.verdicts import MEASURE_VERDICT, Verdict


# ---------------------------------------------------------------------------
# The subdivision set Z
# ---------------------------------------------------------------------------

def subdivision_point(n: int) -> Fraction:
    """The n-th subdivision point ``z_n = 1 - 1/2^n`` (exact). Requires ``n >= 1``."""
    if n < 1:
        raise ValueError("n must be >= 1")
    return Fraction(1) - half_power(n)


def subdivision_set(count: int) -> List[Fraction]:
    """First ``count`` points of ``Z`` = {1/2, 3/4, 7/8, ...} (exact)."""
    if count < 1:
        raise ValueError("count must be >= 1")
    return [subdivision_point(n) for n in range(1, count + 1)]


# ---------------------------------------------------------------------------
# Covering length: the essay's m(Z) = 0 proof
# ---------------------------------------------------------------------------

def cover_interval_length(n: int, eps: Fraction) -> Fraction:
    """Length ``eps/2^n`` of the open interval ``I_n`` covering ``z_n`` (exact).

    ``I_n = (z_n - eps/2^(n+1), z_n + eps/2^(n+1))`` has width ``eps/2^n``.
    Requires ``n >= 1`` and ``eps > 0``.
    """
    if n < 1:
        raise ValueError("n must be >= 1")
    eps_f = to_fraction(eps)
    if eps_f <= 0:
        raise ValueError("eps must be positive")
    return eps_f * half_power(n)


def total_cover_length(eps: Fraction, terms: int) -> Fraction:
    """Exact total ``sum_{n=1}^terms eps/2^n = eps * (1 - 1/2^terms)``.

    Assembled through :func:`commons.core.geometric_partial_sum` on the geometric
    series with first term ``eps/2`` and ratio ``1/2``. The partial totals
    increase toward ``eps`` (never exceeding it) as ``terms -> infinity``,
    witnessing ``m*(Z) <= eps``. Requires ``eps > 0`` and ``terms >= 1``.
    """
    eps_f = to_fraction(eps)
    if eps_f <= 0:
        raise ValueError("eps must be positive")
    if terms < 1:
        raise ValueError("terms must be >= 1")
    first = eps_f * Fraction(1, 2)
    return geometric_partial_sum(first, Fraction(1, 2), terms)


def cover_tail_length(eps: Fraction, terms: int) -> Fraction:
    """Exact uncovered tail ``eps - total_cover_length = eps / 2^terms``.

    The gap between the finite cover and its limit ``eps`` shrinks to ``0`` as
    ``terms -> infinity``, so the full cover length is exactly ``eps``.
    """
    eps_f = to_fraction(eps)
    if eps_f <= 0:
        raise ValueError("eps must be positive")
    if terms < 1:
        raise ValueError("terms must be >= 1")
    return eps_f * half_power(terms)


def outer_measure_upper_bound(eps: Fraction) -> Fraction:
    """The whole-cover length ``sum_{n>=1} eps/2^n = eps`` -- an upper bound on ``m*(Z)``."""
    eps_f = to_fraction(eps)
    if eps_f <= 0:
        raise ValueError("eps must be positive")
    return eps_f


def infimum_over_eps(eps_values: List[Fraction]) -> Fraction:
    """Infimum of the achievable cover lengths over shrinking ``eps``.

    Because ``outer_measure_upper_bound(eps) = eps`` for every ``eps``, the
    infimum over the supplied values is ``min(eps_values)``; as ``eps -> 0`` it
    tends to ``0``, proving ``m(Z) = 0``. Requires a non-empty list of positive
    ``eps``.
    """
    if not eps_values:
        raise ValueError("eps_values must be non-empty")
    fractions = [to_fraction(e) for e in eps_values]
    for e in fractions:
        if e <= 0:
            raise ValueError("every eps must be positive")
    return min(fractions)


def lebesgue_measure_of_Z() -> Fraction:
    """The Lebesgue measure of ``Z`` is exactly ``0`` (a countable null set)."""
    return Fraction(0)


# ---------------------------------------------------------------------------
# Documented basic Lebesgue facts (helpers)
# ---------------------------------------------------------------------------

def measure_interval(a: Fraction, b: Fraction) -> Fraction:
    """``m([a, b]) = b - a`` for ``a <= b`` (exact)."""
    a_f, b_f = to_fraction(a), to_fraction(b)
    if b_f < a_f:
        raise ValueError("require a <= b")
    return b_f - a_f


def measure_empty() -> Fraction:
    """``m(empty set) = 0``."""
    return Fraction(0)


def measure_singleton(_x: Fraction) -> Fraction:
    """``m({x}) = 0``: a single point has measure zero (covered by intervals of any width)."""
    return Fraction(0)


def measure_countable_union_of_null_sets(null_measures: List[Fraction]) -> Fraction:
    """Countable additivity for null sets: a countable union of measure-zero sets
    has measure ``0`` (``sum of zeros = 0``). Every summand must be ``0``.
    """
    for m in null_measures:
        if to_fraction(m) != 0:
            raise ValueError("this helper documents additivity over NULL sets only")
    return Fraction(0)


# ---------------------------------------------------------------------------
# Verdict
# ---------------------------------------------------------------------------

def verdict() -> Verdict:
    """Lebesgue verdict: FRAGILE -- ``m(Z) = 0``, the barrier is negligible."""
    return MEASURE_VERDICT
