"""Lens 1 -- Geometric series (Zeno's dichotomy). Verdict: FRAGILE.

To reach Gojo an attacker must first cover half the gap, then half the
remainder, then half of *that*, and so on. The fraction of the gap crossed
after ``n`` steps is

    S_n = 1/2 + 1/4 + ... + 1/2^n = 1 - (1/2)^n,

with residual gap ``(1/2)^n`` still uncrossed. That residual is strictly
positive for **every finite** ``n`` -- so no finite number of steps completes
the crossing -- yet the infinite series converges to exactly ``1``. Moreover the
*time* for each step is itself a convergent geometric series (``a/(1-r)`` with
``0 < r < 1``), so total travel time is finite and the attacker arrives.
Infinity, under this lens, is a real but FRAGILE limit, not an impassable wall.

All exact results use :class:`fractions.Fraction`; the strict-positivity
certificate uses :func:`commons.core.half_power` so ``(1/2)^n`` stays an exact
positive rational even at ``n = 1075`` (below the smallest positive float, where
the float path silently underflows to ``0``).

Pure core: stdlib + ``commons.core`` only.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction
from typing import List

from commons.core import (
    geometric_series_limit,
    half_power,
    to_fraction,
)

from gojo_infinity.core.verdicts import ZENO_VERDICT, Verdict

# The Zeno ratio: each step covers half of what remains.
ZENO_RATIO: Fraction = Fraction(1, 2)


# ---------------------------------------------------------------------------
# Partial sums and residuals of the Zeno geometric series
# ---------------------------------------------------------------------------

def partial_sum(n: int, *, ratio: Fraction = ZENO_RATIO) -> Fraction:
    """Exact partial sum ``S_n = 1 - ratio**n``.

    For ``ratio = 1/2`` this is ``1/2 + 1/4 + ... + 1/2^n``. Raises
    :class:`ValueError` for ``n < 0`` or ``ratio`` outside ``(0, 1)``.
    """
    if n < 0:
        raise ValueError("n (number of steps) must be non-negative")
    if not (0 < ratio < 1):
        raise ValueError(f"ratio must satisfy 0 < ratio < 1, got {ratio!r}")
    return Fraction(1) - ratio ** n


def partial_sum_table(max_n: int, *, ratio: Fraction = ZENO_RATIO) -> List[Fraction]:
    """Return ``[S_1, S_2, ..., S_max_n]`` as exact fractions."""
    if max_n < 1:
        raise ValueError("max_n must be >= 1")
    return [partial_sum(n, ratio=ratio) for n in range(1, max_n + 1)]


def residual(n: int) -> Fraction:
    """Exact residual gap ``(1/2)^n`` still uncrossed after ``n`` steps.

    Delegates to :func:`commons.core.half_power`, which builds ``1 / 2**n`` with
    an integer bit-shift, so the value is an exact strictly-positive Fraction for
    arbitrarily large ``n``. Raises :class:`ValueError` for ``n < 0``.
    """
    return half_power(n)


def residual_is_strictly_positive(n: int) -> bool:
    """Strict-positivity certificate: ``(1/2)^n > 0`` exactly, for every finite ``n``.

    This is an *exact rational* comparison (never a float), so it stays ``True``
    at ``n = 1075`` and beyond -- precisely where ``0.5**n`` underflows to ``0.0``
    and a float-based check would wrongly report the gap as closed.
    """
    return residual(n) > 0


def float_residual_underflows_at(n: int) -> bool:
    """Documented FAILURE-mode witness: ``True`` where the float path reads ``0``.

    ``0.5 ** n == 0.0`` for large ``n`` (underflow), even though the exact
    residual is strictly positive. Kept to contrast with the exact certificate
    in :func:`residual_is_strictly_positive`; it is a demonstration of why the
    exact core is necessary, never a correctness path.
    """
    return (0.5 ** n) == 0.0


# ---------------------------------------------------------------------------
# The geometric series limit: the whole gap is covered
# ---------------------------------------------------------------------------

def geometric_sum(a: Fraction, r: Fraction) -> Fraction:
    """Exact limit ``sum_{k=1}^inf a * r^(k-1) = a / (1 - r)`` for ``|r| < 1``.

    Thin exact wrapper over :func:`commons.core.geometric_series_limit`. The
    Zeno case ``a = 1/2, r = 1/2`` gives exactly ``1``.
    """
    return geometric_series_limit(a, r)


def zeno_series_sum() -> Fraction:
    """The Zeno crossing sums to exactly ``1`` -- the whole gap is covered."""
    return geometric_sum(ZENO_RATIO, ZENO_RATIO)


# ---------------------------------------------------------------------------
# Epsilon-N convergence oracle
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class EpsilonN:
    """Result of the epsilon-N oracle: the smallest ``N`` with residual < eps."""

    eps: Fraction
    N: int
    residual_at_N: Fraction        # (1/2)^N,     must be  < eps
    residual_before_N: Fraction    # (1/2)^(N-1), must be >= eps


def epsilon_N(eps: Fraction) -> EpsilonN:
    """Smallest ``N`` with ``(1/2)^N < eps``: ``N = ceil(log2(1/eps))``.

    The closed form is computed with :func:`math.log2` and then **verified
    exactly** with Fraction arithmetic: the returned ``N`` is guaranteed to
    satisfy ``(1/2)^N < eps <= (1/2)^(N-1)`` (the exact witnesses are returned in
    the :class:`EpsilonN` record). The float log2 is only a starting guess; a
    small exact correction loop makes the answer independent of rounding.

    Raises :class:`ValueError` unless ``0 < eps <= 1``.
    """
    eps_f = to_fraction(eps)
    if not (0 < eps_f <= 1):
        raise ValueError(f"eps must satisfy 0 < eps <= 1, got {eps_f}")

    # Float starting guess for ceil(log2(1/eps)); may be off by one due to
    # rounding, so correct it exactly against the Fraction residual.
    guess = max(0, math.ceil(math.log2(1.0 / float(eps_f))))

    # Ensure (1/2)^N < eps (increase N while the residual is too big).
    n = guess
    while half_power(n) >= eps_f:
        n += 1
    # Ensure minimality: (1/2)^(N-1) >= eps (decrease N while we can).
    while n > 0 and half_power(n - 1) < eps_f:
        n -= 1

    return EpsilonN(
        eps=eps_f,
        N=n,
        residual_at_N=half_power(n),
        residual_before_N=half_power(n - 1) if n >= 1 else Fraction(1),
    )


# ---------------------------------------------------------------------------
# Arrival-TIME series: distance converges AND time converges
# ---------------------------------------------------------------------------

def step_distance(n: int, *, ratio: Fraction = ZENO_RATIO) -> Fraction:
    """Physical length of the ``n``-th step ``ratio^(n-1) * (1 - ratio)``.

    For ``ratio = 1/2`` these are ``1/2, 1/4, 1/8, ...`` -- the crossed pieces
    whose partial sums are :func:`partial_sum`. Raises for ``n < 1``.
    """
    if n < 1:
        raise ValueError("step index n must be >= 1")
    if not (0 < ratio < 1):
        raise ValueError(f"ratio must satisfy 0 < ratio < 1, got {ratio!r}")
    return (ratio ** (n - 1)) * (Fraction(1) - ratio)


def step_time(n: int, *, speed: Fraction, ratio: Fraction = ZENO_RATIO) -> Fraction:
    """Time for the ``n``-th step at constant ``speed``: ``distance / speed``.

    ``speed`` is an explicit Fraction parameter (``> 0``). Because the step
    distances form a geometric series with ratio ``< 1``, so do the step times.
    """
    if speed <= 0:
        raise ValueError("speed must be positive")
    return step_distance(n, ratio=ratio) / speed


def total_arrival_time(*, speed: Fraction, ratio: Fraction = ZENO_RATIO) -> Fraction:
    """Exact total arrival time ``sum_n step_time(n) = 1 / speed`` (finite).

    The total distance is ``1`` (the whole gap), so at constant ``speed`` the
    total time is ``1 / speed`` -- finite. This is the key point of Lens 1: not
    only does the *distance* series converge, the *time* series converges too, so
    the attacker genuinely arrives in finite time.
    """
    if speed <= 0:
        raise ValueError("speed must be positive")
    # sum_n ratio^(n-1)*(1-ratio) = 1; divided by speed -> 1/speed. Assemble
    # from the exact geometric limit so the identity is demonstrated, not asserted.
    first = (Fraction(1) - ratio) / speed
    return geometric_series_limit(first, ratio)


# ---------------------------------------------------------------------------
# Verdict
# ---------------------------------------------------------------------------

def verdict() -> Verdict:
    """Geometric-series verdict: FRAGILE (the attacker arrives; series -> finite)."""
    return ZENO_VERDICT
