"""Parity: the n-D numpy batch geodesic integrator vs the pure n-D core (3-D).

RUNS only where numpy is installed (the venv); SKIPS on the stdlib-only system
interpreter via ``pytest.importorskip("numpy")``. For each 3-D initial condition
the batch RK4 result (final position, final velocity, accumulated felt length) is
compared elementwise to the pure
:meth:`ConformalMetricND.integrate_geodesic` run over the SAME fixed number of
steps. Agreement is to a few ULP (numpy ``exp`` / pairwise reduction vs libm
``exp`` / Python floats), asserted with a tight tolerance rather than bit-for-bit.
"""

from __future__ import annotations

import pytest

np = pytest.importorskip("numpy")

from gojo_infinity.accel import manifold_backend as mb  # noqa: E402
from gojo_infinity.core.riemannian_manifold_nd import ConformalMetricND  # noqa: E402

_METRIC = ConformalMetricND()  # Gojo at the origin of R^3

_INITIAL_3D = [
    ((-3.0, 0.5, 0.4), (1.0, 0.0, 0.0)),
    ((-3.0, 0.8, -0.3), (1.0, 0.0, 0.0)),
    ((2.0, 2.0, 1.0), (-1.0, -0.3, -0.2)),
    ((0.9, 0.0, 0.0), (-1.0, 0.0, 0.0)),   # radial
    ((-2.0, -1.0, 0.7), (0.8, 0.2, 0.1)),
]


def test_batch_nd_matches_pure_integrator_3d() -> None:
    steps = 3000
    dtau = 1e-3
    p0 = np.array([ic[0] for ic in _INITIAL_3D], dtype=np.float64)
    v0 = np.array([ic[1] for ic in _INITIAL_3D], dtype=np.float64)
    batch = mb.integrate_geodesics_batch_nd(p0, v0, dtau=dtau, steps=steps)

    for k, (p, v) in enumerate(_INITIAL_3D):
        pure = _METRIC.integrate_geodesic(p, v, dtau=dtau, max_steps=steps, min_radius=0.0)
        assert pure.steps == steps
        assert np.allclose(batch.final_positions[k], pure.points[-1], atol=1e-8, rtol=0), (
            f"position mismatch for 3-D IC {k}"
        )
        assert np.allclose(batch.final_velocities[k], pure.final_velocity, atol=1e-8, rtol=0), (
            f"velocity mismatch for 3-D IC {k}"
        )
        assert abs(float(batch.arc_lengths[k]) - pure.arc_length) < 1e-8, (
            f"arc-length mismatch for 3-D IC {k}"
        )


def test_batch_nd_conserves_affine_energy_3d() -> None:
    steps = 3000
    p0 = np.array([ic[0] for ic in _INITIAL_3D], dtype=np.float64)
    v0 = np.array([ic[1] for ic in _INITIAL_3D], dtype=np.float64)
    batch = mb.integrate_geodesics_batch_nd(p0, v0, dtau=1e-3, steps=steps)
    drift = np.abs(batch.energy_end - batch.energy_start) / np.abs(batch.energy_start)
    assert float(np.max(drift)) < 1e-6, f"3-D batch energy drift too large: {np.max(drift)}"


def test_batch_nd_also_serves_2d() -> None:
    # The same n-D batch routine works in 2-D (D inferred from the arrays).
    metric_2d = ConformalMetricND(gojo=(0.0, 0.0))
    steps = 2000
    p0 = np.array([[-3.0, 0.5], [2.0, 1.0]], dtype=np.float64)
    v0 = np.array([[1.0, 0.0], [-1.0, -0.2]], dtype=np.float64)
    batch = mb.integrate_geodesics_batch_nd(p0, v0, dtau=1e-3, steps=steps, gojo=(0.0, 0.0))
    for k in range(2):
        pure = metric_2d.integrate_geodesic(
            tuple(p0[k]), tuple(v0[k]), dtau=1e-3, max_steps=steps, min_radius=0.0
        )
        assert np.allclose(batch.final_positions[k], pure.points[-1], atol=1e-8, rtol=0)


def test_batch_nd_validates_shapes_and_args() -> None:
    with pytest.raises(ValueError):  # dimension mismatch with default 3-D gojo
        mb.integrate_geodesics_batch_nd([[0.0, 0.0]], [[1.0, 0.0]])
    with pytest.raises(ValueError):
        mb.integrate_geodesics_batch_nd([[0.5, 0.0, 0.0]], [[1.0, 0.0, 0.0]], dtau=0.0)
    with pytest.raises(ValueError):
        mb.integrate_geodesics_batch_nd([[0.5, 0.0, 0.0]], [[1.0, 0.0, 0.0]], steps=0)
