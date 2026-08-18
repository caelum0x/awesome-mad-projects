"""Mobius strip: parametrization and Gaussian curvature (three agreeing paths).

Standard parametrization (a ruled surface ``r(u, v) = alpha(u) + v beta(u)``):

    x = (1 + v cos(u/2)) cos(u)
    y = (1 + v cos(u/2)) sin(u)
    z = v sin(u/2)

with ``u in [0, 2*pi]`` and ``v in [-0.5, 0.5]``.

Because the strip is ruled (``r_vv = 0`` so ``N = 0``) and ``M = -1/(2 sqrt(E))``
never vanishes, the Gaussian curvature ``K = -1/(4 E**2)`` is STRICTLY negative on
the whole open interior. Three independent curvature paths (analytic oracle,
central-difference FD, complex-step) are exposed and cross-validate.

The seam ``r(2*pi, v) = r(0, -v)`` is handled by :func:`mobius_rickness.core.geometry.mobius_seam_wrap`,
which is passed into every finite-difference stencil so curvature stays accurate
across the ``u = 0 / 2*pi`` seam.

Purity: imports only the standard library and :mod:`mobius_rickness.core.geometry`.
"""

from __future__ import annotations

import cmath
import math
from typing import Tuple

from mobius_rickness.core.geometry import (
    CVec3,
    Vec3,
    gaussian_curvature_cs,
    gaussian_curvature_fd,
    fundamental_forms_fd,
    mobius_curvature_analytic,
    mobius_seam_wrap,
)

U_MIN, U_MAX = 0.0, 2.0 * math.pi
V_MIN, V_MAX = -0.5, 0.5


def surface(u: float, v: float) -> Vec3:
    """Return the real 3D point ``r(u, v)`` on the Mobius strip."""
    half = u / 2.0
    radial = 1.0 + v * math.cos(half)
    x = radial * math.cos(u)
    y = radial * math.sin(u)
    z = v * math.sin(half)
    return (x, y, z)


def surface_complex(u: complex, v: complex) -> CVec3:
    """Complex-capable Mobius map for the complex-step derivative path.

    Uses :mod:`cmath` so a purely-imaginary perturbation of ``u`` (or ``v``)
    propagates analytically -- the precondition for cancellation-free
    complex-step differentiation (``cos``/``sin`` are entire).
    """
    half = u / 2.0
    radial = 1.0 + v * cmath.cos(half)
    x = radial * cmath.cos(u)
    y = radial * cmath.sin(u)
    z = v * cmath.sin(half)
    return (x, y, z)


def gaussian_curvature(u: float, v: float) -> float:
    """Gaussian curvature ``K`` of the Mobius strip (analytic oracle, default)."""
    return mobius_curvature_analytic(u, v)


def gaussian_curvature_numeric(u: float, v: float) -> float:
    """Gaussian curvature via seam-aware central finite differences (path b)."""
    return gaussian_curvature_fd(surface, u, v, wrap=mobius_seam_wrap)


def gaussian_curvature_complex_step(u: float, v: float) -> float:
    """Gaussian curvature via the complex-step path (path c)."""
    return gaussian_curvature_cs(surface_complex, u, v)


def fundamental_forms(
    u: float, v: float
) -> Tuple[float, float, float, float, float, float]:
    """Seam-aware central-difference ``(E, F, G, L, M, N)`` at ``(u, v)``."""
    return fundamental_forms_fd(surface, u, v, wrap=mobius_seam_wrap)


def seam_identity_error(v: float) -> float:
    """Max coordinate mismatch of ``r(2*pi, v)`` vs ``r(0, -v)`` (should be ~0)."""
    a = surface(U_MAX, v)
    b = surface(U_MIN, -v)
    return max(abs(a[i] - b[i]) for i in range(3))


def assert_curvature_negative(
    n_u: int = 60, n_v: int = 15, tol: float = 1e-9
) -> float:
    """Assert ``K < 0`` strictly on the Mobius interior; return the worst (max) K.

    Interior means the open ``v``-range (endpoints ``v = +/-0.5`` excluded).
    Raises :class:`AssertionError` if any sampled interior ``K`` is not strictly
    negative (below ``-tol``).
    """
    if n_u < 2 or n_v < 1:
        raise ValueError("need n_u >= 2 and n_v >= 1")
    du = (U_MAX - U_MIN) / (n_u - 1)
    dv = (V_MAX - V_MIN) / (n_v + 1)
    worst = -math.inf
    for i in range(n_u):
        u = U_MIN + i * du
        for j in range(1, n_v + 1):
            v = V_MIN + j * dv
            k = gaussian_curvature(u, v)
            assert k < -tol, f"K not strictly negative at u={u}, v={v}: K={k}"
            if k > worst:
                worst = k
    return worst
