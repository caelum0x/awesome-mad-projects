"""Real numerical routines: integration, differentiation, root finding.

Everything here is pure Python / stdlib (``math``, ``cmath``) so it runs with no
third-party dependency. Each routine documents its convergence order and error
behaviour. Callables are treated as black boxes: pass a plain
``Callable[[float], float]`` (or complex-accepting for the complex-step
derivative).

Conventions:
    * Integrators take ``[a, b]`` with ``a <= b`` and a sub-interval count ``n``.
    * Derivatives take an evaluation point ``x`` and a step ``h``.
    * The root finder brackets a sign change and refines by bisection.
"""

from __future__ import annotations

import cmath
import math
from typing import Callable

RealFunc = Callable[[float], float]
ComplexFunc = Callable[[complex], complex]


# ---------------------------------------------------------------------------
# Integration
# ---------------------------------------------------------------------------

def midpoint_integral(f: RealFunc, a: float, b: float, n: int = 1000) -> float:
    """Composite midpoint rule for ``integral_a^b f(x) dx`` using ``n`` panels.

    Second-order accurate: the error scales like ``O((b-a)^3 f''/n^2)``. Exact
    for linear integrands. Raises :class:`ValueError` for ``n < 1`` or ``b < a``.
    """
    if n < 1:
        raise ValueError("n must be >= 1")
    if b < a:
        raise ValueError("require a <= b")
    if a == b:
        return 0.0
    h = (b - a) / n
    total = math.fsum(f(a + (i + 0.5) * h) for i in range(n))
    return h * total


def trapezoid_integral(f: RealFunc, a: float, b: float, n: int = 1000) -> float:
    """Composite trapezoidal rule for ``integral_a^b f(x) dx`` using ``n`` panels.

    Second-order accurate: error ``O((b-a)^3 f''/n^2)``. Exact for linear
    integrands. Raises :class:`ValueError` for ``n < 1`` or ``b < a``.
    """
    if n < 1:
        raise ValueError("n must be >= 1")
    if b < a:
        raise ValueError("require a <= b")
    if a == b:
        return 0.0
    h = (b - a) / n
    interior = math.fsum(f(a + i * h) for i in range(1, n))
    return h * (0.5 * f(a) + interior + 0.5 * f(b))


def _adaptive_simpson(
    f: RealFunc,
    a: float,
    b: float,
    fa: float,
    fb: float,
    fm: float,
    whole: float,
    tol: float,
    depth: int,
) -> float:
    """Recursive adaptive Simpson helper (see :func:`adaptive_integral`)."""
    m = 0.5 * (a + b)
    lm = 0.5 * (a + m)
    rm = 0.5 * (m + b)
    flm = f(lm)
    frm = f(rm)
    left = (m - a) / 6.0 * (fa + 4.0 * flm + fm)
    right = (b - m) / 6.0 * (fm + 4.0 * frm + fb)
    delta = left + right - whole
    # Richardson-extrapolated error estimate: |delta|/15 < tol accepts.
    if depth <= 0 or abs(delta) <= 15.0 * tol:
        return left + right + delta / 15.0
    return (
        _adaptive_simpson(f, a, m, fa, fm, flm, left, tol / 2.0, depth - 1)
        + _adaptive_simpson(f, m, b, fm, fb, frm, right, tol / 2.0, depth - 1)
    )


def adaptive_integral(
    f: RealFunc,
    a: float,
    b: float,
    tol: float = 1e-10,
    max_depth: int = 50,
) -> float:
    """Adaptive Simpson quadrature for ``integral_a^b f(x) dx``.

    Recursively bisects sub-intervals until the local Richardson error estimate
    falls below ``tol`` (or ``max_depth`` is hit, bounding the work). Achieves
    near machine precision for smooth integrands and concentrates effort where
    the integrand varies fastest. Raises :class:`ValueError` for ``b < a`` or a
    non-positive ``tol``.
    """
    if b < a:
        raise ValueError("require a <= b")
    if tol <= 0.0:
        raise ValueError("tol must be positive")
    if a == b:
        return 0.0
    m = 0.5 * (a + b)
    fa, fb, fm = f(a), f(b), f(m)
    whole = (b - a) / 6.0 * (fa + 4.0 * fm + fb)
    return _adaptive_simpson(f, a, b, fa, fb, fm, whole, tol, max_depth)


# ---------------------------------------------------------------------------
# Differentiation
# ---------------------------------------------------------------------------

def central_difference(
    f: RealFunc,
    x: float,
    h: float = 1e-5,
    order: int = 1,
) -> float:
    """Central finite-difference derivative of ``f`` at ``x``.

    ``order=1``: ``(f(x+h) - f(x-h)) / (2h)`` -- second-order accurate,
    error ``O(h^2)``, but subject to subtractive cancellation for tiny ``h``
    (a floating-point noise floor near ``h ~ 1e-5`` for well-scaled ``f``).

    ``order=2``: ``(f(x+h) - 2 f(x) + f(x-h)) / h^2`` -- the second derivative,
    also ``O(h^2)`` and more cancellation-sensitive (noise floor near
    ``h ~ 1e-3``..``1e-4``).

    Raises :class:`ValueError` for ``h <= 0`` or an unsupported ``order``.
    """
    if h <= 0.0:
        raise ValueError("step h must be positive")
    if order == 1:
        return (f(x + h) - f(x - h)) / (2.0 * h)
    if order == 2:
        return (f(x + h) - 2.0 * f(x) + f(x - h)) / (h * h)
    raise ValueError("order must be 1 or 2")


def complex_step_derivative(
    f: ComplexFunc,
    x: float,
    h: float = 1e-20,
) -> float:
    """First derivative of ``f`` at ``x`` by the complex-step method.

    Returns ``Im(f(x + i h)) / h``. Because no subtraction of nearly-equal
    quantities occurs, there is *no* subtractive cancellation: ``h`` can be made
    as small as ``1e-20`` and the result is accurate to ~machine precision
    (~1e-12 or better) without the tuning that finite differences require.

    Requirement: ``f`` must be *analytic* and implemented so it accepts a
    complex argument (use ``cmath`` internally, not ``math``). Raises
    :class:`ValueError` for ``h <= 0``.
    """
    if h <= 0.0:
        raise ValueError("step h must be positive")
    return f(complex(x, h)).imag / h


# ---------------------------------------------------------------------------
# Root finding
# ---------------------------------------------------------------------------

def bisection(
    f: RealFunc,
    a: float,
    b: float,
    tol: float = 1e-12,
    max_iter: int = 200,
) -> float:
    """Find a root of ``f`` in ``[a, b]`` by bisection (sign-change bracketing).

    Requires ``f(a)`` and ``f(b)`` to straddle zero (opposite signs), or one of
    them to be exactly zero. Fails fast with :class:`ValueError` if the endpoints
    do not bracket a sign change -- it never returns a bogus root. Converges
    linearly, halving the bracket each step; stops once the half-width is below
    ``tol`` or ``max_iter`` iterations elapse. The final estimate is within
    ``tol`` of a true root.

    Raises :class:`ValueError` for ``b < a``, ``tol <= 0``, or ``max_iter < 1``.
    """
    if b < a:
        raise ValueError("require a <= b")
    if tol <= 0.0:
        raise ValueError("tol must be positive")
    if max_iter < 1:
        raise ValueError("max_iter must be >= 1")

    fa = f(a)
    fb = f(b)
    if fa == 0.0:
        return a
    if fb == 0.0:
        return b
    if fa * fb > 0.0:
        raise ValueError("f(a) and f(b) must bracket a sign change")

    lo, hi = a, b
    f_lo = fa
    for _ in range(max_iter):
        mid = 0.5 * (lo + hi)
        f_mid = f(mid)
        if f_mid == 0.0 or 0.5 * (hi - lo) < tol:
            return mid
        if f_lo * f_mid < 0.0:
            hi = mid
        else:
            lo = mid
            f_lo = f_mid
    return 0.5 * (lo + hi)


def find_sign_changes(
    f: RealFunc,
    a: float,
    b: float,
    n: int = 100,
) -> list[tuple[float, float]]:
    """Scan ``[a, b]`` on ``n`` sub-intervals and return bracketing pairs.

    Each returned ``(lo, hi)`` has ``f(lo) * f(hi) <= 0`` and can be handed to
    :func:`bisection`. Detects only sign changes visible at the sampling
    resolution (roots of even multiplicity, or pairs closer than the step, may
    be missed). Raises :class:`ValueError` for ``n < 1`` or ``b < a``.
    """
    if n < 1:
        raise ValueError("n must be >= 1")
    if b < a:
        raise ValueError("require a <= b")
    step = (b - a) / n
    brackets: list[tuple[float, float]] = []
    prev_x = a
    prev_f = f(prev_x)
    for i in range(1, n + 1):
        cur_x = a + i * step
        cur_f = f(cur_x)
        if prev_f == 0.0 or prev_f * cur_f < 0.0:
            brackets.append((prev_x, cur_x))
        prev_x, prev_f = cur_x, cur_f
    return brackets
