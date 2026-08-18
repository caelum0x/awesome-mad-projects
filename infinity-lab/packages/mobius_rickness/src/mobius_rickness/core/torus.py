"""Torus geometry: the non-ruled counterpoint with sign-changing curvature.

Standard ring-torus parametrization (major radius ``R0``, minor radius ``r0``):

    x = (R0 + r0 cos(theta)) cos(phi)
    y = (R0 + r0 cos(theta)) sin(phi)
    z = r0 sin(theta)

Unlike the Mobius strip (ruled, ``K <= 0``), the torus has the exact closed form

    K(theta) = cos(theta) / (r0 (R0 + r0 cos(theta)))

which is POSITIVE on the outer half, NEGATIVE on the inner half, and ZERO exactly
on the two circles ``theta = pi/2`` and ``theta = 3*pi/2`` -- a genuine,
geometry-driven zero set (no weighting needed).

The numeric curvature reuses the surface-agnostic central-difference engine in
:mod:`mobius_rickness.core.geometry` and matches the closed form.

Purity: imports only the standard library and :mod:`mobius_rickness.core.geometry`.
"""

from __future__ import annotations

import math
from typing import Tuple

from mobius_rickness.core.geometry import Vec3, gaussian_curvature_fd

# Default radii used across the project (outer/inner "donut").
R0_DEFAULT = 2.0
R_MINOR_DEFAULT = 1.0


def require_ring(r0_major: float, r0_minor: float) -> None:
    """Validate a genuine ring torus ``R0 > r0 > 0`` (fail fast otherwise).

    For a ring torus the denominator ``R0 + r0 cos(theta)`` is strictly positive,
    so ``K`` is bounded. For ``R0 <= r0`` the torus self-intersects and ``K`` has a
    real singularity -- raising here is honest rather than masking it with a
    ``denom == 0 -> 0`` guard.
    """
    if r0_minor <= 0.0:
        raise ValueError("minor radius r0 must be positive")
    if r0_major <= r0_minor:
        raise ValueError("ring torus requires R0 > r0 > 0")


def surface(
    theta: float,
    phi: float,
    r0_major: float = R0_DEFAULT,
    r0_minor: float = R_MINOR_DEFAULT,
) -> Vec3:
    """Return the 3D point ``r(theta, phi)`` on the torus."""
    radial = r0_major + r0_minor * math.cos(theta)
    x = radial * math.cos(phi)
    y = radial * math.sin(phi)
    z = r0_minor * math.sin(theta)
    return (x, y, z)


def gaussian_curvature_closed(
    theta: float,
    r0_major: float = R0_DEFAULT,
    r0_minor: float = R_MINOR_DEFAULT,
) -> float:
    """Exact closed-form Gaussian curvature ``K(theta)``.

    ``K(theta) = cos(theta) / (r0 (R0 + r0 cos(theta)))``. Validates the ring-torus
    condition so a real singularity is never silently returned as zero.
    """
    require_ring(r0_major, r0_minor)
    denom = r0_minor * (r0_major + r0_minor * math.cos(theta))
    return math.cos(theta) / denom


def gaussian_curvature(
    theta: float,
    phi: float = 0.0,
    r0_major: float = R0_DEFAULT,
    r0_minor: float = R_MINOR_DEFAULT,
) -> float:
    """Numeric Gaussian curvature via central differences (surface-agnostic engine).

    Independent of ``phi`` up to numerical error (surface of revolution). Matches
    :func:`gaussian_curvature_closed`.
    """
    require_ring(r0_major, r0_minor)

    def surf(a: float, b: float) -> Vec3:
        return surface(a, b, r0_major, r0_minor)

    return gaussian_curvature_fd(surf, theta, phi)


def sign_pattern(
    theta: float, r0_major: float = R0_DEFAULT, r0_minor: float = R_MINOR_DEFAULT
) -> int:
    """Return ``+1 / -1 / 0`` for the sign of the closed-form ``K`` at ``theta``."""
    k = gaussian_curvature_closed(theta, r0_major, r0_minor)
    if k > 0.0:
        return 1
    if k < 0.0:
        return -1
    return 0


def zero_circles() -> Tuple[float, float]:
    """The two ``theta`` values where ``K = 0``: ``(pi/2, 3*pi/2)``."""
    return (math.pi / 2.0, 3.0 * math.pi / 2.0)
