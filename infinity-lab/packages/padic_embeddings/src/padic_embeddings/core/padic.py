"""Core p-adic arithmetic: valuation, absolute value, and metric.

The p-adic world replaces the usual notion of "size". Instead of a number being
large when it is far from zero on the real line, a number is *small* when it is
highly divisible by a fixed prime ``p``.

Definitions (honest math)
-------------------------
Let ``p`` be a prime.

  ``v_p(n)``   p-adic valuation of a nonzero integer ``n`` = the largest integer
               ``k`` such that ``p**k`` divides ``n``. By convention
               ``v_p(0) = +infinity``.

  For a rational ``a/b``:  ``v_p(a/b) = v_p(a) - v_p(b)``.

  ``|x|_p``    p-adic absolute value ``= p**(-v_p(x))``, and ``|0|_p = 0``.

  ``d_p(a,b)`` p-adic distance ``= |a - b|_p``.

Key facts this module lets you verify empirically:
  * ``d_p`` is a *metric* (non-negative, symmetric, zero iff ``a == b``).
  * ``d_p`` is an *ultrametric*: it obeys the STRONG triangle inequality
        ``d_p(a, c) <= max( d_p(a, b), d_p(b, c) )``.
    This is strictly stronger than the ordinary triangle inequality and is what
    gives the space its tree-like / hierarchical structure.

Absolute values and distances are computed EXACTLY as
:class:`fractions.Fraction` (the abs values are always exact powers of ``p``), so
the ultrametric verifier never depends on a floating-point tolerance. Float-facing
helpers are offered for display only.

Purity: imports only the standard library and :mod:`commons.core`.
"""

from __future__ import annotations

import math
from fractions import Fraction
from typing import Union

from commons.core.exact import to_fraction

Number = Union[int, Fraction]


def is_prime(p: int) -> bool:
    """Trial-division primality test (exact; fine for the primes used here).

    Raises :class:`TypeError` for a non-integer ``p`` so callers fail fast at the
    boundary rather than mis-computing a valuation.
    """
    if not isinstance(p, int) or isinstance(p, bool):
        raise TypeError(f"p must be int, got {type(p).__name__}")
    if p < 2:
        return False
    if p % 2 == 0:
        return p == 2
    i = 3
    while i * i <= p:
        if p % i == 0:
            return False
        i += 2
    return True


def _require_prime(p: int) -> None:
    """Raise :class:`ValueError` unless ``p`` is prime (shared boundary guard)."""
    if not is_prime(p):
        raise ValueError(f"p must be prime, got {p}")


def _valuation_int(n: int, p: int) -> int:
    """p-adic valuation of a NONZERO integer (largest ``k`` with ``p**k | n``)."""
    n = abs(n)
    k = 0
    while n % p == 0:
        n //= p
        k += 1
    return k


def valuation(x: Number, p: int) -> float:
    """p-adic valuation ``v_p(x)``.

    Returns ``math.inf`` for ``x == 0``; otherwise an integer value. Accepts
    ``int`` and :class:`fractions.Fraction`. Raises :class:`ValueError` when ``p``
    is not prime.
    """
    _require_prime(p)
    frac = to_fraction(x)
    if frac == 0:
        return math.inf
    return _valuation_int(frac.numerator, p) - _valuation_int(frac.denominator, p)


def p_adic_abs_exact(x: Number, p: int) -> Fraction:
    """Exact p-adic absolute value ``|x|_p = p**(-v_p(x))``; ``|0|_p = 0``.

    The result is always an exact power of ``p`` (a :class:`fractions.Fraction`),
    which is what lets the ultrametric checks be exact.
    """
    v = valuation(x, p)
    if v == math.inf:
        return Fraction(0)
    exponent = int(v)
    if exponent >= 0:
        return Fraction(1, p ** exponent)
    return Fraction(p ** (-exponent), 1)


def p_adic_abs(x: Number, p: int) -> float:
    """p-adic absolute value ``|x|_p`` as a float (display convenience)."""
    return float(p_adic_abs_exact(x, p))


def distance_exact(a: Number, b: Number, p: int) -> Fraction:
    """Exact p-adic distance ``d_p(a, b) = |a - b|_p`` as a :class:`Fraction`."""
    return p_adic_abs_exact(to_fraction(a) - to_fraction(b), p)


def distance(a: Number, b: Number, p: int) -> float:
    """p-adic distance ``d_p(a, b) = |a - b|_p`` as a float (display convenience)."""
    return float(distance_exact(a, b, p))


def is_ultrametric_triple(a: Number, b: Number, c: Number, p: int) -> bool:
    """Check the strong triangle inequality for one ordered triple, EXACTLY.

    Returns ``True`` iff ``d_p(a, c) <= max( d_p(a, b), d_p(b, c) )``. The
    comparison is over exact :class:`Fraction` distances, so there is no
    floating-point tolerance and no false positives/negatives.
    """
    d_ac = distance_exact(a, c, p)
    d_ab = distance_exact(a, b, p)
    d_bc = distance_exact(b, c, p)
    return d_ac <= max(d_ab, d_bc)
