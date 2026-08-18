"""Parity: the numpy fast-paths must equal the pure core value-for-value.

These tests are OPTIONAL and DEFERRED. They begin with
``pytest.importorskip("numpy")`` so they SKIP on the stdlib-only system
interpreter (which has no numpy) and RUN on the venv interpreter (numpy 2.x).

Every fast-path in :mod:`mobius_rickness.accel.numpy_backend` evaluates a quantity
over a whole ``(u, v)`` mesh that the pure :mod:`mobius_rickness.core` computes
point-by-point. We assert they agree:

    * finite-difference curvature ``K`` to ``atol = 1e-9`` (the second-derivative
      stencil amplifies rounding by ``~1/h**2``, so a real tolerance is used), and
    * the analytic ``K``, the Rickness ``R``, the weighted ``K_Rick`` and the 3D
      point cloud EXACTLY (elementwise closed forms; max abs diff == 0).

Both meshes are sampled at the *same* Python-float nodes (built once with the
stdlib ``linspace`` and passed to both paths), so any difference is a genuine
numerical-path difference, not a difference in sample points.
"""

from __future__ import annotations

import pytest

np = pytest.importorskip("numpy")

from mobius_rickness.accel import numpy_backend as accel
from mobius_rickness.core import (
    U_MAX,
    U_MIN,
    V_MAX,
    V_MIN,
    gaussian_curvature,
    gaussian_curvature_numeric,
    k_rick,
    linspace,
    rickness,
    surface,
)

# A non-trivial mesh spanning the full u-domain (so FD stencils exercise the
# seam wrap at u = 0 / 2*pi) and the strip interior in v.
_N_U = 41
_N_V = 21
_US = linspace(U_MIN, U_MAX, _N_U)
_VS = linspace(V_MIN, V_MAX, _N_V)

# FD tolerance: the order-2 central difference divides by h**2 = 1e-8, so it
# amplifies ~1e-16 rounding to ~1e-8 unless the operation order matches the core
# exactly (it does here, giving ~0), but we assert against the required bound.
_FD_ATOL = 1e-9


def _scalar_field(func) -> "np.ndarray":
    """Evaluate a scalar ``func(u, v)`` over the shared mesh -> array [v, u]."""
    return np.array([[func(u, v) for u in _US] for v in _VS], dtype=float)


def _max_abs_diff(a: "np.ndarray", b: "np.ndarray") -> float:
    return float(np.max(np.abs(a - b)))


def test_curvature_fd_mesh_matches_core_within_atol() -> None:
    fast = accel.curvature_fd_mesh(_US, _VS)
    pure = _scalar_field(gaussian_curvature_numeric)
    assert fast.shape == pure.shape == (_N_V, _N_U)
    diff = _max_abs_diff(fast, pure)
    assert diff <= _FD_ATOL, (
        f"vectorised FD curvature diverges from pure per-point K: "
        f"max abs diff {diff:.3e} > atol {_FD_ATOL:.0e}"
    )


def test_curvature_analytic_mesh_matches_core_exactly() -> None:
    fast = accel.curvature_analytic_mesh(_US, _VS)
    pure = _scalar_field(gaussian_curvature)
    diff = _max_abs_diff(fast, pure)
    assert diff == 0.0, f"analytic K parity broken: max abs diff {diff:.3e} != 0"


def test_rickness_mesh_matches_core_exactly() -> None:
    fast = accel.rickness_mesh(_US, _VS)
    pure = _scalar_field(rickness)
    diff = _max_abs_diff(fast, pure)
    assert diff == 0.0, f"Rickness R parity broken: max abs diff {diff:.3e} != 0"


def test_k_rick_mesh_matches_core_exactly() -> None:
    fast = accel.k_rick_mesh(_US, _VS)
    pure = _scalar_field(k_rick)
    diff = _max_abs_diff(fast, pure)
    assert diff == 0.0, f"K_Rick = K*R parity broken: max abs diff {diff:.3e} != 0"


def test_surface_point_cloud_matches_core_exactly() -> None:
    fast = accel.mobius_surface_mesh(_US, _VS)
    assert fast.shape == (_N_V, _N_U, 3)
    pure = np.array(
        [[list(surface(u, v)) for u in _US] for v in _VS], dtype=float
    )
    diff = _max_abs_diff(fast, pure)
    assert diff == 0.0, f"surface point-cloud parity broken: max abs diff {diff:.3e} != 0"


def test_k_rick_mesh_equals_analytic_curvature_times_rickness() -> None:
    # Internal consistency of the fast-path: K_Rick == K_analytic * R elementwise.
    k_ana = accel.curvature_analytic_mesh(_US, _VS)
    r = accel.rickness_mesh(_US, _VS)
    k_rick_mesh = accel.k_rick_mesh(_US, _VS)
    assert _max_abs_diff(k_rick_mesh, k_ana * r) == 0.0


def test_fast_paths_require_numpy_module_symbol() -> None:
    # The deferred error type is exported for callers that catch missing numpy.
    assert issubclass(accel.OptionalDependencyError, RuntimeError)
