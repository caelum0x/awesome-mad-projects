"""Shared numerical differential-geometry engine (stdlib + commons.core only).

This module computes the first and second fundamental forms ``E, F, G, L, M, N``
of any smooth parametric surface ``r(u, v) -> (x, y, z)`` and, from them, the
Gaussian curvature ``K = (L*N - M**2) / (E*G - F**2)``.

It exposes THREE independent, cross-validating curvature paths that must agree
to tolerance on the Mobius parametrization:

    (a) :func:`mobius_curvature_analytic` -- the exact closed-form oracle
        ``K = -1 / (4 E**2)`` with ``E = (1 + v cos(u/2))**2 + v**2/4``.
    (b) :func:`gaussian_curvature_fd` -- central finite differences of the
        fundamental forms (built on :func:`commons.core.numerics.central_difference`).
    (c) :func:`gaussian_curvature_cs` -- a cancellation-free complex-step path
        for the first derivatives (built on
        :func:`commons.core.numerics.complex_step_derivative`), with a single real
        difference layer for the second derivatives.

The Mobius SEAM v-flip ``r(2*pi, v) = r(0, -v)`` is load-bearing: any periodic
stencil that samples a neighbour outside ``[0, 2*pi]`` must wrap ``u`` modulo
``2*pi`` AND flip ``v`` for an odd number of wraps. This is provided by
:func:`mobius_seam_wrap` and applied inside every finite-difference stencil via a
caller-supplied ``wrap`` callable (default :func:`identity_wrap` for ordinary,
non-seamed surfaces such as the torus).

Purity: imports only the standard library and :mod:`commons.core`.
"""

from __future__ import annotations

import math
from typing import Callable, Tuple

from commons.core.numerics import central_difference, complex_step_derivative

Vec3 = Tuple[float, float, float]
CVec3 = Tuple[complex, complex, complex]
Surface = Callable[[float, float], Vec3]
ComplexSurface = Callable[[complex, complex], CVec3]
Wrap = Callable[[float, float], Tuple[float, float]]

TWO_PI = 2.0 * math.pi

# Finite-difference steps. Research optima (eps = 2.22e-16):
#   first derivative  h ~ (3 eps)**(1/3)  ~ 1e-5
#   second derivative h ~ (48 eps)**(1/4) ~ 1e-4
_H_FIRST = 1e-5
_H_SECOND = 1e-4


# ---------------------------------------------------------------------------
# Immutable 3D vector helpers (each returns a fresh tuple, never mutates)
# ---------------------------------------------------------------------------

def sub(a: Vec3, b: Vec3) -> Vec3:
    """Vector subtraction ``a - b``."""
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def scale(a: Vec3, s: float) -> Vec3:
    """Scalar multiplication ``s * a``."""
    return (a[0] * s, a[1] * s, a[2] * s)


def dot(a: Vec3, b: Vec3) -> float:
    """Dot product ``a . b``."""
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a: Vec3, b: Vec3) -> Vec3:
    """Cross product ``a x b``."""
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def norm(a: Vec3) -> float:
    """Euclidean length ``|a|``."""
    return math.sqrt(dot(a, a))


def unit_normal(r_u: Vec3, r_v: Vec3) -> Vec3:
    """Unit surface normal ``(r_u x r_v) / |r_u x r_v|`` (zero if degenerate)."""
    n = cross(r_u, r_v)
    mag = norm(n)
    if mag == 0.0:
        return (0.0, 0.0, 0.0)
    return scale(n, 1.0 / mag)


# ---------------------------------------------------------------------------
# Seam handling
# ---------------------------------------------------------------------------

def identity_wrap(u: float, v: float) -> Tuple[float, float]:
    """No-op domain wrap for ordinary (non-seamed) surfaces such as the torus."""
    return (u, v)


def mobius_seam_wrap(u: float, v: float) -> Tuple[float, float]:
    """Mobius seam gluing ``r(2*pi, v) = r(0, -v)``.

    Reduce ``u`` modulo ``2*pi`` and flip ``v -> -v`` for an odd number of
    wraps. The Mobius parametrization is globally smooth under this map, so
    evaluating ``surf(*mobius_seam_wrap(u, v))`` in a finite-difference stencil
    keeps it second-order accurate right across the ``u = 0 / 2*pi`` seam --
    instead of producing a spurious high-curvature discontinuity there.
    """
    k = math.floor(u / TWO_PI)
    u_wrapped = u - TWO_PI * k
    v_wrapped = v if k % 2 == 0 else -v
    return (u_wrapped, v_wrapped)


def _wrapped(surf: Surface, wrap: Wrap) -> Surface:
    """Return ``surf`` composed with the domain ``wrap`` map."""

    def w(u: float, v: float) -> Vec3:
        wu, wv = wrap(u, v)
        return surf(wu, wv)

    return w


# ---------------------------------------------------------------------------
# Path (b): central finite differences
# ---------------------------------------------------------------------------

def partials_fd(
    surf: Surface,
    u: float,
    v: float,
    wrap: Wrap = identity_wrap,
    h1: float = _H_FIRST,
    h2: float = _H_SECOND,
) -> Tuple[Vec3, Vec3, Vec3, Vec3, Vec3]:
    """Central-difference first/second partials ``(r_u, r_v, r_uu, r_uv, r_vv)``.

    Every sample goes through ``wrap`` so periodic/seamed stencils are correct.
    First derivatives use step ``h1``; second and mixed derivatives use ``h2``.
    Built on :func:`commons.core.numerics.central_difference`.
    """
    w = _wrapped(surf, wrap)

    def r_u_comp(i: int) -> float:
        return central_difference(lambda t: w(t, v)[i], u, h1)

    def r_v_comp(i: int) -> float:
        return central_difference(lambda t: w(u, t)[i], v, h1)

    def r_uu_comp(i: int) -> float:
        return central_difference(lambda t: w(t, v)[i], u, h2, order=2)

    def r_vv_comp(i: int) -> float:
        return central_difference(lambda t: w(u, t)[i], v, h2, order=2)

    def r_uv_comp(i: int) -> float:
        # Mixed partial: d/dv of (d/du r), both via central differences.
        def du_at(vv: float) -> float:
            return central_difference(lambda t: w(t, vv)[i], u, h2)

        return central_difference(du_at, v, h2)

    r_u = (r_u_comp(0), r_u_comp(1), r_u_comp(2))
    r_v = (r_v_comp(0), r_v_comp(1), r_v_comp(2))
    r_uu = (r_uu_comp(0), r_uu_comp(1), r_uu_comp(2))
    r_vv = (r_vv_comp(0), r_vv_comp(1), r_vv_comp(2))
    r_uv = (r_uv_comp(0), r_uv_comp(1), r_uv_comp(2))
    return r_u, r_v, r_uu, r_uv, r_vv


def _forms_from_partials(
    r_u: Vec3, r_v: Vec3, r_uu: Vec3, r_uv: Vec3, r_vv: Vec3
) -> Tuple[float, float, float, float, float, float]:
    """Assemble ``(E, F, G, L, M, N)`` from the five partial-derivative vectors."""
    E = dot(r_u, r_u)
    F = dot(r_u, r_v)
    G = dot(r_v, r_v)
    n = unit_normal(r_u, r_v)
    L = dot(r_uu, n)
    M = dot(r_uv, n)
    N = dot(r_vv, n)
    return E, F, G, L, M, N


def fundamental_forms_fd(
    surf: Surface, u: float, v: float, wrap: Wrap = identity_wrap
) -> Tuple[float, float, float, float, float, float]:
    """Central-difference first/second fundamental forms ``(E, F, G, L, M, N)``."""
    r_u, r_v, r_uu, r_uv, r_vv = partials_fd(surf, u, v, wrap)
    return _forms_from_partials(r_u, r_v, r_uu, r_uv, r_vv)


def gaussian_curvature_fd(
    surf: Surface, u: float, v: float, wrap: Wrap = identity_wrap
) -> float:
    """Numeric Gaussian curvature via central differences (path b)."""
    E, F, G, L, M, N = fundamental_forms_fd(surf, u, v, wrap)
    denom = E * G - F * F
    if denom == 0.0:
        raise ValueError("degenerate first fundamental form (E*G - F**2 == 0)")
    return (L * N - M * M) / denom


# ---------------------------------------------------------------------------
# Path (c): complex-step first derivatives (+ one real difference for seconds)
# ---------------------------------------------------------------------------

def _cs_first_u(csurf: ComplexSurface, u: float, v: float) -> Vec3:
    """Cancellation-free ``r_u`` via the complex-step method (per component)."""
    return (
        complex_step_derivative(lambda t: csurf(t, v)[0], u),
        complex_step_derivative(lambda t: csurf(t, v)[1], u),
        complex_step_derivative(lambda t: csurf(t, v)[2], u),
    )


def _cs_first_v(csurf: ComplexSurface, u: float, v: float) -> Vec3:
    """Cancellation-free ``r_v`` via the complex-step method (per component)."""
    return (
        complex_step_derivative(lambda t: csurf(u, t)[0], v),
        complex_step_derivative(lambda t: csurf(u, t)[1], v),
        complex_step_derivative(lambda t: csurf(u, t)[2], v),
    )


def partials_cs(
    csurf: ComplexSurface, u: float, v: float, h2: float = _H_SECOND
) -> Tuple[Vec3, Vec3, Vec3, Vec3, Vec3]:
    """Partials with complex-step first derivatives and central-difference seconds.

    First derivatives ``r_u, r_v`` are cancellation-free (complex step, entire
    trig). Second derivatives are one real central difference of the complex-step
    first derivative -- a genuinely different numerical path from :func:`partials_fd`,
    yet agreeing with it (and the analytic oracle) to tolerance.
    """

    def ru_i(uu: float, i: int) -> float:
        return complex_step_derivative(lambda t: csurf(t, v)[i], uu)

    def rv_i(vv: float, i: int) -> float:
        return complex_step_derivative(lambda t: csurf(u, t)[i], vv)

    def ru_at_v_i(vv: float, i: int) -> float:
        return complex_step_derivative(lambda t: csurf(t, vv)[i], u)

    r_u = _cs_first_u(csurf, u, v)
    r_v = _cs_first_v(csurf, u, v)
    r_uu = tuple(central_difference(lambda t, i=i: ru_i(t, i), u, h2) for i in range(3))
    r_vv = tuple(central_difference(lambda t, i=i: rv_i(t, i), v, h2) for i in range(3))
    r_uv = tuple(
        central_difference(lambda t, i=i: ru_at_v_i(t, i), v, h2) for i in range(3)
    )
    return r_u, r_v, r_uu, r_uv, r_vv  # type: ignore[return-value]


def fundamental_forms_cs(
    csurf: ComplexSurface, u: float, v: float
) -> Tuple[float, float, float, float, float, float]:
    """Complex-step first/second fundamental forms ``(E, F, G, L, M, N)``."""
    r_u, r_v, r_uu, r_uv, r_vv = partials_cs(csurf, u, v)
    return _forms_from_partials(r_u, r_v, r_uu, r_uv, r_vv)


def gaussian_curvature_cs(csurf: ComplexSurface, u: float, v: float) -> float:
    """Numeric Gaussian curvature via the complex-step path (path c)."""
    E, F, G, L, M, N = fundamental_forms_cs(csurf, u, v)
    denom = E * G - F * F
    if denom == 0.0:
        raise ValueError("degenerate first fundamental form (E*G - F**2 == 0)")
    return (L * N - M * M) / denom


# ---------------------------------------------------------------------------
# Path (a): Mobius analytic curvature oracle
# ---------------------------------------------------------------------------

def mobius_E(u: float, v: float) -> float:
    """First fundamental-form coefficient ``E = (1 + v cos(u/2))**2 + v**2/4``.

    For the standard Mobius parametrization ``F = 0`` and ``G = 1`` exactly, so
    the whole metric is carried by ``E``. It is bounded below by
    ``(1 - |v|)**2 + v**2/4 > 0`` for ``|v| < 1`` (embedded strip).
    """
    f = 1.0 + v * math.cos(u / 2.0)
    return f * f + v * v / 4.0


def mobius_curvature_analytic(u: float, v: float) -> float:
    """Exact Gaussian curvature of the Mobius strip, ``K = -1 / (4 E**2)`` (path a).

    Because ``M = -1/(2 sqrt(E))`` never vanishes and ``N = 0`` (ruled surface),
    ``K = -M**2 / E = -1 / (4 E**2) < 0`` strictly for every ``|v| < 1``.
    """
    E = mobius_E(u, v)
    return -1.0 / (4.0 * E * E)
