"""Vectorised numpy fast-paths mirroring the pure Mobius-Rickness core.

Every function here evaluates, over a whole ``(u, v)`` mesh at once, a quantity
that :mod:`mobius_rickness.core` computes point-by-point with the standard library
alone -- and reproduces the pure result to floating-point parity:

    * :func:`curvature_fd_mesh` -- Gaussian curvature ``K`` via seam-aware central
      finite differences of the surface map, matching the pure per-point
      :func:`mobius_rickness.core.gaussian_curvature_numeric` (path b) EXACTLY. The
      mixed-partial stencil replicates the core's *nested* central difference so
      the ``1/h**2`` second-derivative amplification cancels identically rather
      than leaking ``~1e-8`` libm-rounding noise.
    * :func:`curvature_analytic_mesh` -- the closed-form oracle
      ``K = -1 / (4 E**2)``, matching :func:`mobius_rickness.core.gaussian_curvature`.
    * :func:`rickness_mesh` -- the sign-changing field ``R(u, v)``.
    * :func:`k_rick_mesh` -- the weighted field ``K_Rick = K * R`` built from the
      analytic ``K`` (as the core :func:`mobius_rickness.core.k_rick` does).
    * :func:`mobius_surface_mesh` -- the 3D Mobius point cloud ``r(u, v)``.

numpy is OPTIONAL: it is reached only through
:func:`commons.core.optional.try_import`, never hard-imported at module top level.
Calling any fast-path without numpy raises :class:`OptionalDependencyError`.

This is an accelerator, not core: it imports ``core`` (for the shared constants
and finite-difference step sizes, so parity never silently drifts) but is never
imported by ``core``.
"""

from __future__ import annotations

from typing import Any, Sequence, Tuple

from commons.core.optional import try_import

# Import the exact step sizes the pure core uses so the fast-path can never
# silently drift out of parity with the per-point finite-difference stencils.
from mobius_rickness.core.geometry import (
    TWO_PI,
    _H_FIRST as H_FIRST,
    _H_SECOND as H_SECOND,
)
from mobius_rickness.core.mobius import U_MAX, U_MIN, V_MAX, V_MIN

# numpy arrays are typed as ``Any`` -- numpy is optional and never imported at
# module top level, so a precise annotation cannot be spelled here.
NDArray = Any

__all__ = [
    "OptionalDependencyError",
    "curvature_fd_mesh",
    "curvature_analytic_mesh",
    "rickness_mesh",
    "k_rick_mesh",
    "mobius_surface_mesh",
    "U_MIN",
    "U_MAX",
    "V_MIN",
    "V_MAX",
]


class OptionalDependencyError(RuntimeError):
    """Raised when a numpy fast-path is used but numpy is not installed.

    The pure :mod:`mobius_rickness.core` never raises this; only the deferred
    accelerator does, and only when the caller invokes it without the dependency.
    """


def _require_numpy() -> Any:
    """Return the numpy module or raise a clear :class:`OptionalDependencyError`."""
    numpy = try_import("numpy")
    if numpy is None:
        raise OptionalDependencyError(
            "the numpy fast-path backend requires numpy, which is not installed. "
            "Install the optional 'accel' extra, or use the pure core "
            "(mobius_rickness.core), which needs no third-party dependencies."
        )
    return numpy


def _mesh(np: Any, us: Sequence[float], vs: Sequence[float]) -> Tuple[NDArray, NDArray]:
    """Build ``(U, V)`` meshgrids (rows = ``v``, cols = ``u``) as float64 arrays."""
    u_axis = np.asarray(us, dtype=float)
    v_axis = np.asarray(vs, dtype=float)
    if u_axis.ndim != 1 or v_axis.ndim != 1:
        raise ValueError("us and vs must each be one-dimensional")
    if u_axis.size == 0 or v_axis.size == 0:
        raise ValueError("us and vs must be non-empty")
    return np.meshgrid(u_axis, v_axis)


# ---------------------------------------------------------------------------
# Surface maps (raw + seam-wrapped), vectorised
# ---------------------------------------------------------------------------

def _surface_points(np: Any, U: NDArray, V: NDArray) -> NDArray:
    """Vectorised raw Mobius map ``r(u, v)`` -> array of shape ``(..., 3)``.

    Mirrors :func:`mobius_rickness.core.surface` component-for-component (same
    operation order), so it reproduces the scalar map bit-for-bit.
    """
    half = U / 2.0
    radial = 1.0 + V * np.cos(half)
    x = radial * np.cos(U)
    y = radial * np.sin(U)
    z = V * np.sin(half)
    return np.stack((x, y, z), axis=-1)


def _seam_wrap(np: Any, U: NDArray, V: NDArray) -> Tuple[NDArray, NDArray]:
    """Vectorised Mobius seam gluing ``r(2*pi, v) = r(0, -v)``.

    Reduces ``u`` modulo ``2*pi`` and flips ``v -> -v`` for an odd number of
    wraps -- the elementwise image of
    :func:`mobius_rickness.core.geometry.mobius_seam_wrap`. Python's ``k % 2`` and
    numpy's ``mod(k, 2)`` agree for negative ``k`` (both non-negative), so the
    flip parity matches the scalar path exactly.
    """
    k = np.floor(U / TWO_PI)
    u_wrapped = U - TWO_PI * k
    odd = np.mod(k.astype(np.int64), 2) != 0
    v_wrapped = np.where(odd, -V, V)
    return u_wrapped, v_wrapped


def _wrapped_surface(np: Any, U: NDArray, V: NDArray) -> NDArray:
    """Seam-wrapped surface ``surface(mobius_seam_wrap(u, v))`` (for FD stencils)."""
    u_wrapped, v_wrapped = _seam_wrap(np, U, V)
    return _surface_points(np, u_wrapped, v_wrapped)


# ---------------------------------------------------------------------------
# Fundamental forms -> Gaussian curvature (from vectorised partials)
# ---------------------------------------------------------------------------

def _unit_normal(np: Any, r_u: NDArray, r_v: NDArray) -> NDArray:
    """Unit surface normal ``(r_u x r_v) / |r_u x r_v|`` (zero where degenerate).

    Uses ``n * (1 / mag)`` (not ``n / mag``) to match
    :func:`mobius_rickness.core.geometry.unit_normal` to the last bit.
    """
    n = np.cross(r_u, r_v)
    mag = np.sqrt(np.sum(n * n, axis=-1))
    safe = np.where(mag == 0.0, 1.0, mag)
    unit = n * (1.0 / safe)[..., None]
    return np.where((mag == 0.0)[..., None], 0.0, unit)


def _curvature_from_partials(
    np: Any,
    r_u: NDArray,
    r_v: NDArray,
    r_uu: NDArray,
    r_uv: NDArray,
    r_vv: NDArray,
) -> NDArray:
    """Assemble ``K = (L*N - M**2) / (E*G - F**2)`` from the five partial fields."""
    E = np.sum(r_u * r_u, axis=-1)
    F = np.sum(r_u * r_v, axis=-1)
    G = np.sum(r_v * r_v, axis=-1)
    normal = _unit_normal(np, r_u, r_v)
    L = np.sum(r_uu * normal, axis=-1)
    M = np.sum(r_uv * normal, axis=-1)
    N = np.sum(r_vv * normal, axis=-1)
    denom = E * G - F * F
    if bool(np.any(denom == 0.0)):
        raise ValueError("degenerate first fundamental form (E*G - F**2 == 0)")
    return (L * N - M * M) / denom


# ---------------------------------------------------------------------------
# Public fast-paths
# ---------------------------------------------------------------------------

def curvature_fd_mesh(us: Sequence[float], vs: Sequence[float]) -> NDArray:
    """Seam-aware central-difference Gaussian curvature ``K`` over the mesh.

    Returns a 2D array of shape ``(len(vs), len(us))`` (rows = ``v``, cols = ``u``)
    that reproduces the pure per-point
    :func:`mobius_rickness.core.gaussian_curvature_numeric` at every node.

    First derivatives use step ``H_FIRST``; second and mixed derivatives use
    ``H_SECOND`` -- the same constants the core uses. The mixed partial ``r_uv`` is
    a *nested* central difference (an inner ``u``-difference divided by ``2 h``,
    then differenced in ``v`` and divided by ``2 h``), matching the core's
    operation order so the second-derivative rounding cancels identically.
    """
    np = _require_numpy()
    U, V = _mesh(np, us, vs)
    h1 = H_FIRST
    h2 = H_SECOND

    def w(a: NDArray, b: NDArray) -> NDArray:
        return _wrapped_surface(np, a, b)

    center = w(U, V)
    r_u = (w(U + h1, V) - w(U - h1, V)) / (2.0 * h1)
    r_v = (w(U, V + h1) - w(U, V - h1)) / (2.0 * h1)
    r_uu = (w(U + h2, V) - 2.0 * center + w(U - h2, V)) / (h2 * h2)
    r_vv = (w(U, V + h2) - 2.0 * center + w(U, V - h2)) / (h2 * h2)
    du_plus = (w(U + h2, V + h2) - w(U - h2, V + h2)) / (2.0 * h2)
    du_minus = (w(U + h2, V - h2) - w(U - h2, V - h2)) / (2.0 * h2)
    r_uv = (du_plus - du_minus) / (2.0 * h2)
    return _curvature_from_partials(np, r_u, r_v, r_uu, r_uv, r_vv)


def _curvature_analytic(np: Any, U: NDArray, V: NDArray) -> NDArray:
    """Closed-form ``K = -1 / (4 E**2)`` with ``E = (1 + v cos(u/2))**2 + v**2/4``."""
    f = 1.0 + V * np.cos(U / 2.0)
    E = f * f + V * V / 4.0
    return -1.0 / (4.0 * E * E)


def curvature_analytic_mesh(us: Sequence[float], vs: Sequence[float]) -> NDArray:
    """Analytic Gaussian curvature ``K`` over the mesh.

    Returns a 2D array of shape ``(len(vs), len(us))`` reproducing the pure
    :func:`mobius_rickness.core.gaussian_curvature` (the analytic oracle) at every
    node.
    """
    np = _require_numpy()
    U, V = _mesh(np, us, vs)
    return _curvature_analytic(np, U, V)


def _rickness(np: Any, U: NDArray, V: NDArray) -> NDArray:
    """Sign-changing Rickness ``R = cos(u) + 0.4 v cos(u/2) + 0.2 sin(u)``."""
    return np.cos(U) + 0.4 * V * np.cos(U / 2.0) + 0.2 * np.sin(U)


def rickness_mesh(us: Sequence[float], vs: Sequence[float]) -> NDArray:
    """Rickness field ``R(u, v)`` over the mesh.

    Returns a 2D array of shape ``(len(vs), len(us))`` reproducing the pure
    :func:`mobius_rickness.core.rickness` at every node.
    """
    np = _require_numpy()
    U, V = _mesh(np, us, vs)
    return _rickness(np, U, V)


def k_rick_mesh(us: Sequence[float], vs: Sequence[float]) -> NDArray:
    """Weighted field ``K_Rick = K * R`` over the mesh (analytic ``K``).

    Returns a 2D array of shape ``(len(vs), len(us))`` reproducing the pure
    :func:`mobius_rickness.core.k_rick` at every node -- like the core, it weights
    the *analytic* Gaussian curvature by the sign-changing Rickness, so the mesh
    zero set coincides exactly with ``R^{-1}(0)``.
    """
    np = _require_numpy()
    U, V = _mesh(np, us, vs)
    return _curvature_analytic(np, U, V) * _rickness(np, U, V)


def mobius_surface_mesh(us: Sequence[float], vs: Sequence[float]) -> NDArray:
    """3D Mobius surface point cloud ``r(u, v)`` over the mesh.

    Returns an array of shape ``(len(vs), len(us), 3)`` whose ``[j, i]`` entry is
    the ``(x, y, z)`` point reproducing the pure
    :func:`mobius_rickness.core.surface` at ``(us[i], vs[j])``.
    """
    np = _require_numpy()
    U, V = _mesh(np, us, vs)
    return _surface_points(np, U, V)
