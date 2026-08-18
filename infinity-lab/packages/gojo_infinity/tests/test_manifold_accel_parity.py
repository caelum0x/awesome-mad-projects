"""Parity: the numpy batch geodesic integrator vs the pure core integrator.

RUNS only where numpy is installed (the venv); SKIPS on the stdlib-only system
interpreter via ``pytest.importorskip("numpy")``. For each initial condition the
batch RK4 result (final position, final velocity, accumulated felt length) is
compared elementwise to the pure :meth:`ConformalMetric.integrate_geodesic` run
over the SAME fixed number of steps. Agreement is to a few ULP (numpy ``exp`` /
pairwise reduction vs libm ``exp`` / Python floats), asserted with a tight
tolerance rather than bit-for-bit.
"""

from __future__ import annotations

import pytest

np = pytest.importorskip("numpy")

from gojo_infinity.accel import manifold_backend as mb  # noqa: E402
from gojo_infinity.core.riemannian_manifold import ConformalMetric  # noqa: E402

_METRIC = ConformalMetric()

_INITIAL = [
    ((-3.0, 0.5), (1.0, 0.0)),
    ((-3.0, 0.8), (1.0, 0.0)),
    ((2.0, 2.0), (-1.0, -0.3)),
    ((0.9, 0.0), (-1.0, 0.0)),   # radial
    ((-2.0, -1.0), (0.8, 0.2)),
]


def test_batch_matches_pure_integrator() -> None:
    steps = 3000
    dtau = 1e-3
    p0 = np.array([ic[0] for ic in _INITIAL], dtype=np.float64)
    v0 = np.array([ic[1] for ic in _INITIAL], dtype=np.float64)
    batch = mb.integrate_geodesics_batch(p0, v0, dtau=dtau, steps=steps)

    for k, (p, v) in enumerate(_INITIAL):
        pure = _METRIC.integrate_geodesic(
            p, v, dtau=dtau, max_steps=steps, min_radius=0.0
        )
        assert pure.steps == steps
        fp = batch.final_positions[k]
        fv = batch.final_velocities[k]
        assert np.allclose(fp, pure.points[-1], atol=1e-8, rtol=0), (
            f"position mismatch for IC {k}: {fp} vs {pure.points[-1]}"
        )
        assert np.allclose(fv, pure.final_velocity, atol=1e-8, rtol=0), (
            f"velocity mismatch for IC {k}"
        )
        assert abs(float(batch.arc_lengths[k]) - pure.arc_length) < 1e-8, (
            f"arc-length mismatch for IC {k}"
        )


def test_batch_conserves_affine_energy() -> None:
    steps = 3000
    p0 = np.array([ic[0] for ic in _INITIAL], dtype=np.float64)
    v0 = np.array([ic[1] for ic in _INITIAL], dtype=np.float64)
    batch = mb.integrate_geodesics_batch(p0, v0, dtau=1e-3, steps=steps)
    drift = np.abs(batch.energy_end - batch.energy_start) / np.abs(batch.energy_start)
    assert float(np.max(drift)) < 1e-6, f"batch energy drift too large: {np.max(drift)}"


def test_batch_validates_shapes_and_args() -> None:
    with pytest.raises(ValueError):
        mb.integrate_geodesics_batch([[0.0, 0.0, 0.0]], [[1.0, 0.0, 0.0]])
    with pytest.raises(ValueError):
        mb.integrate_geodesics_batch([[0.5, 0.0]], [[1.0, 0.0]], dtau=0.0)
    with pytest.raises(ValueError):
        mb.integrate_geodesics_batch([[0.5, 0.0]], [[1.0, 0.0]], steps=0)


def test_batch_backend_has_no_top_level_numpy_binding() -> None:
    # numpy is reached only via commons.core.optional.try_import inside functions.
    assert not hasattr(mb, "numpy")
    assert not hasattr(mb, "np")
