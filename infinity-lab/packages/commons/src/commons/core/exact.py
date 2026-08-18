"""Exact rational arithmetic helpers over :class:`fractions.Fraction`.

These routines never lose precision: every result is an exact
:class:`~fractions.Fraction`. They underpin the essay-style proofs shared by the
downstream packages (Zeno partial sums, Lebesgue cover lengths, dyadic
subdivision points), where floating point would silently round away the point
being demonstrated.

Error behaviour is fail-fast: out-of-domain arguments raise :class:`ValueError`
or :class:`TypeError` rather than returning an approximate or bogus value.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Union

Number = Union[int, float, str, Fraction]


def to_fraction(x: Number) -> Fraction:
    """Convert ``x`` to an exact :class:`~fractions.Fraction`.

    Accepts ``int``, ``Fraction``, decimal ``str`` (e.g. ``"0.1"`` -> 1/10 with
    no binary rounding), and ``float``. Floats are converted via their exact
    IEEE-754 value (``Fraction(float)``), so ``0.5`` is exactly ``1/2`` but
    ``0.1`` is the true machine value, not ``1/10`` -- pass a string for exact
    decimals. ``bool`` is rejected as a likely mistake.
    """
    if isinstance(x, bool):
        raise TypeError("bool is not a valid numeric input for to_fraction")
    if isinstance(x, Fraction):
        return x
    if isinstance(x, (int, float, str)):
        return Fraction(x)
    raise TypeError(f"cannot convert {type(x).__name__} to Fraction")


def half_power(n: int) -> Fraction:
    """Return the exact dyadic rational ``1 / 2**n`` for ``n >= 0``.

    Uses an integer bit-shift (``1 << n``) for the denominator, so the result is
    exact for arbitrarily large ``n`` (e.g. ``half_power(1075)`` -- below the
    smallest positive float -- is still a valid strictly-positive Fraction with
    numerator 1). Raises :class:`ValueError` for negative ``n``.
    """
    if not isinstance(n, int) or isinstance(n, bool):
        raise TypeError(f"n must be int, got {type(n).__name__}")
    if n < 0:
        raise ValueError("n must be non-negative")
    return Fraction(1, 1 << n)


def geometric_partial_sum(a: Number, r: Number, n: int) -> Fraction:
    """Exact partial sum ``sum_{k=0}^{n-1} a * r**k`` of a geometric series.

    Returns ``Fraction(0)`` when ``n == 0``. Uses the closed form
    ``a * (1 - r**n) / (1 - r)`` when ``r != 1`` and ``a * n`` when ``r == 1``.
    All arithmetic is exact. Raises :class:`ValueError` for negative ``n``.
    """
    if not isinstance(n, int) or isinstance(n, bool):
        raise TypeError(f"n must be int, got {type(n).__name__}")
    if n < 0:
        raise ValueError("number of terms n must be non-negative")
    a_f = to_fraction(a)
    r_f = to_fraction(r)
    if n == 0:
        return Fraction(0)
    if r_f == 1:
        return a_f * n
    return a_f * (Fraction(1) - r_f ** n) / (Fraction(1) - r_f)


def geometric_series_limit(a: Number, r: Number) -> Fraction:
    """Exact limit ``a / (1 - r)`` of ``sum_{k=0}^inf a * r**k`` for ``|r| < 1``.

    Raises :class:`ValueError` if ``|r| >= 1`` (the series diverges).
    """
    r_f = to_fraction(r)
    if not (-1 < r_f < 1):
        raise ValueError(f"|r| must be < 1 for convergence, got {r_f}")
    return to_fraction(a) / (Fraction(1) - r_f)
