"""Core p-adic arithmetic: valuation, absolute value, and metric.

The p-adic world replaces the usual notion of "size". Instead of a number
being large when it is far from zero on the real line, a number is *small*
when it is highly divisible by a fixed prime p.

Definitions (honest math)
-------------------------
Let p be a prime.

  v_p(n)   p-adic valuation of a nonzero integer n = the largest integer k
           such that p^k divides n. By convention v_p(0) = +infinity.

  For a rational a/b (in lowest terms or not):
           v_p(a/b) = v_p(a) - v_p(b).

  |x|_p    p-adic absolute value = p^(-v_p(x)), and |0|_p = 0.

  d_p(a,b) p-adic distance = |a - b|_p.

Key facts this module lets you verify empirically:
  * d_p is a *metric* (non-negative, symmetric, d(a,b)=0 iff a=b).
  * d_p is an *ultrametric*: it obeys the STRONG triangle inequality
        d_p(a, c) <= max( d_p(a, b), d_p(b, c) ).
    This is strictly stronger than the ordinary triangle inequality and is
    what gives the space its tree-like / hierarchical structure.

Only the Python standard library is used (fractions, math).
"""

from __future__ import annotations

import math
from fractions import Fraction
from typing import Union

Number = Union[int, Fraction]


def is_prime(p: int) -> bool:
    """Trial-division primality test (fine for the small primes used here)."""
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


def _valuation_int(n: int, p: int) -> int:
    """p-adic valuation of a nonzero integer."""
    n = abs(n)
    k = 0
    while n % p == 0:
        n //= p
        k += 1
    return k


def valuation(x: Number, p: int) -> float:
    """p-adic valuation v_p(x).

    Returns math.inf for x == 0, otherwise an integer (as a float only when
    infinite). Accepts ints and fractions.Fraction.
    """
    if not is_prime(p):
        raise ValueError(f"p must be prime, got {p}")
    if x == 0:
        return math.inf
    frac = Fraction(x)
    return _valuation_int(frac.numerator, p) - _valuation_int(frac.denominator, p)


def p_adic_abs(x: Number, p: int) -> float:
    """p-adic absolute value |x|_p = p^(-v_p(x)); |0|_p = 0."""
    v = valuation(x, p)
    if v == math.inf:
        return 0.0
    return float(p) ** (-v)


def distance(a: Number, b: Number, p: int) -> float:
    """p-adic distance d_p(a, b) = |a - b|_p."""
    return p_adic_abs(Fraction(a) - Fraction(b), p)


def is_ultrametric_triple(a: Number, b: Number, c: Number, p: int,
                          tol: float = 1e-12) -> bool:
    """Check the strong triangle inequality for one ordered triple."""
    d_ac = distance(a, c, p)
    d_ab = distance(a, b, p)
    d_bc = distance(b, c, p)
    return d_ac <= max(d_ab, d_bc) + tol
