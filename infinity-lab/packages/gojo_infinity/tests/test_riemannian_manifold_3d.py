"""Tests for the 3-D (n-D) Riemannian-manifold geodesic solver (pure core).

Pure stdlib + ``commons.core`` tests, so they RUN on BOTH the stdlib-only system
interpreter and the venv (no numpy/matplotlib needed). They exercise the SAME
dimension-agnostic solver (:mod:`gojo_infinity.core.riemannian_manifold_nd`) in
3-D and cover the six required properties:

1. ``christoffel_conformal`` matches ``christoffel_general`` (finite differences).
2. The affine invariant ``Omega^2 |v|^2`` is conserved along a 3-D geodesic.
3. Radial parity: a radial 3-D approach matches the 1-D lens felt length.
4. Planarity: a 3-D geodesic stays in the plane of (p0, v0, Gojo).
5. Deflection: a grazing 3-D geodesic bends toward Gojo (velocity tilts inward).
6. Divergence: felt length within ``delta`` of Gojo is monotone and unbounded.
"""

from __future__ import annotations

import math

import pytest

from commons.core import central_difference
from gojo_infinity.core.riemannian import DEFAULT_LAMBDA, geodesic_length
from gojo_infinity.core.riemannian_manifold import ConformalMetric
from gojo_infinity.core.riemannian_manifold_nd import (
    ConformalMetricND,
    max_christoffel_difference_nd,
    unsigned_angle,
    verdict,
)

_METRIC = ConformalMetricND()  # Gojo at the origin of R^3, sigma/lam from 1-D lens

# A spread of 3-D test points (all away from Gojo where Omega is finite).
_POINTS_3D = [
    (0.5, 0.3, 0.2), (1.0, -0.4, 0.3), (2.0, 0.1, -0.5), (0.3, 0.0, 0.4),
    (-0.7, 0.9, 0.5), (-1.2, -0.6, 0.8), (0.2, -0.25, -0.15), (1.5, 1.5, -1.0),
]


# ---------------------------------------------------------------------------
# 0. Dimension is inferred; metric is SPD; far from Gojo it is the identity
# ---------------------------------------------------------------------------

def test_dimension_inferred_from_gojo() -> None:
    assert _METRIC.dim == 3
    assert ConformalMetricND(gojo=(0.0, 0.0)).dim == 2
    assert ConformalMetricND(gojo=(0.0,)).dim == 1


@pytest.mark.parametrize("p", _POINTS_3D)
def test_metric_is_symmetric_positive_definite_3d(p) -> None:
    g = _METRIC.metric_tensor(p)
    w = _METRIC.omega(p) ** 2
    for i in range(3):
        for j in range(3):
            assert g[i][j] == g[j][i]
            assert g[i][j] == (w if i == j else 0.0)
    assert w > 0.0


def test_metric_far_from_gojo_is_identity_3d() -> None:
    p = (8.0, 6.0, 5.0)
    assert math.isclose(_METRIC.omega(p), 1.0, abs_tol=1e-9)


# ---------------------------------------------------------------------------
# 1. Christoffel closed form matches the general finite-difference formula
# ---------------------------------------------------------------------------

def test_christoffel_conformal_matches_general_3d() -> None:
    worst = max_christoffel_difference_nd(_METRIC, _POINTS_3D, h=1e-5)
    assert worst < 1e-6, f"3-D closed-form vs general Christoffel diff too large: {worst}"


@pytest.mark.parametrize("p", _POINTS_3D)
def test_christoffel_symmetric_in_lower_indices_3d(p) -> None:
    gamma = _METRIC.christoffel_conformal(p)
    for k in range(3):
        for i in range(3):
            for j in range(3):
                assert gamma[k][i][j] == gamma[k][j][i]


@pytest.mark.parametrize("p", _POINTS_3D)
def test_grad_phi_analytic_matches_finite_difference_3d(p) -> None:
    ana = _METRIC.grad_phi(p)
    for axis in range(3):
        def component(t: float, axis: int = axis) -> float:
            q = tuple(t if k == axis else p[k] for k in range(3))
            return _METRIC.phi(q)

        fd = central_difference(component, p[axis], 1e-6)
        assert math.isclose(ana[axis], fd, rel_tol=1e-5, abs_tol=1e-8)


# ---------------------------------------------------------------------------
# 2. Affine invariant Omega^2 |v|^2 conserved along a 3-D geodesic (~1e-12)
# ---------------------------------------------------------------------------

def test_affine_energy_is_conserved_along_3d_geodesic() -> None:
    res = _METRIC.integrate_geodesic(
        (-3.0, 0.5, 0.4), (1.0, 0.0, 0.0), dtau=1e-3, max_steps=6000
    )
    assert res.energy_drift < 1e-11, f"3-D energy drift too large: {res.energy_drift}"


# ---------------------------------------------------------------------------
# 3. Radial parity: a radial 3-D geodesic matches the 1-D lens felt length
# ---------------------------------------------------------------------------

def test_radial_3d_geodesic_matches_1d_lens() -> None:
    d0 = 0.5
    res = _METRIC.integrate_geodesic(
        (d0, 0.0, 0.0), (-1.0, 0.0, 0.0),
        dtau=1e-3, target_radius=0.05, max_steps=500_000,
    )
    assert res.stop_reason == "reached_target"
    # stays exactly on the radial axis (all off-axis components identically 0)
    assert max(max(abs(p[1]), abs(p[2])) for p in res.points) == 0.0
    assert res.final_velocity[1] == 0.0 and res.final_velocity[2] == 0.0

    ref_radial = _METRIC.felt_length_to_reach(res.final_radius, start_radius=d0)
    ref_1d = geodesic_length(1.0 - d0, 1.0 - res.final_radius)
    assert abs(res.arc_length - ref_radial) < 1e-9
    assert abs(res.arc_length - ref_1d) < 1e-9


# ---------------------------------------------------------------------------
# 4. PLANARITY: the geodesic stays in the plane spanned by (p0, v0, Gojo)
# ---------------------------------------------------------------------------

def test_geodesic_stays_in_orbital_plane() -> None:
    p0 = (-3.0, 0.5, 0.4)
    v0 = (1.0, 0.0, 0.0)
    res = _METRIC.integrate_geodesic(p0, v0, dtau=1e-3, max_steps=6000)
    normal = _METRIC.orbital_plane_normal(p0, v0)
    drift = _METRIC.max_out_of_plane_drift(res.points, normal)
    assert drift < 1e-9, f"geodesic left its (p0, v0, Gojo) plane by {drift}"


def test_orbital_plane_normal_rejects_radial_launch() -> None:
    # p0 - gojo parallel to v0 => no unique plane.
    with pytest.raises(ValueError):
        _METRIC.orbital_plane_normal((2.0, 0.0, 0.0), (-1.0, 0.0, 0.0))


# ---------------------------------------------------------------------------
# 5. Deflection: a grazing 3-D geodesic bends toward Gojo (tilts inward)
# ---------------------------------------------------------------------------

def test_grazing_3d_geodesic_deflects_toward_gojo() -> None:
    p0 = (-3.0, 0.5, 0.4)
    v0 = (1.0, 0.0, 0.0)
    res = _METRIC.integrate_geodesic(p0, v0, dtau=1e-3, max_steps=6000)
    # positive turning
    assert res.deflection_angle > 1e-2, "no measurable 3-D deflection"
    # the final velocity tilts INWARD: its component along the initial
    # perpendicular offset (away from Gojo) is negative.
    offset = (0.0, 0.5, 0.4)
    off_norm = math.hypot(offset[1], offset[2])
    unit = (0.0, offset[1] / off_norm, offset[2] / off_norm)
    inward = sum(res.final_velocity[k] * unit[k] for k in range(3))
    assert inward < 0.0, "grazing ray did not tilt toward Gojo"


def test_straight_ray_far_away_does_not_deflect_3d() -> None:
    res = _METRIC.integrate_geodesic(
        (-3.0, 6.0, 6.0), (1.0, 0.0, 0.0), dtau=1e-3, max_steps=6000
    )
    assert res.deflection_angle < 1e-6


# ---------------------------------------------------------------------------
# 6. Divergence: felt length to within delta of Gojo is monotone and unbounded
# ---------------------------------------------------------------------------

def test_felt_length_divergence_is_monotone_and_unbounded_3d() -> None:
    deltas = [10.0 ** (-k) for k in range(1, 9)]  # 1e-1 .. 1e-8
    table = _METRIC.felt_length_divergence(deltas, start_radius=0.9)
    lengths = [L for _, L in table]
    for prev, nxt in zip(lengths, lengths[1:]):
        assert nxt > prev
    assert lengths[-1] - lengths[0] > 4.0
    per_decade = lengths[-1] - lengths[-2]
    assert math.isclose(per_decade, DEFAULT_LAMBDA * math.log(10.0), abs_tol=5e-3)


def test_felt_length_exceeds_arbitrary_bound_3d() -> None:
    for bound in (5.0, 10.0, 20.0):
        delta = math.exp(-(bound + 5.0) / DEFAULT_LAMBDA)
        length = _METRIC.felt_length_to_reach(delta, start_radius=0.9)
        assert length > bound


# ---------------------------------------------------------------------------
# Cross-dimension parity: the n-D solver reproduces the 2-D solver in 2-D
# ---------------------------------------------------------------------------

def test_nd_solver_matches_2d_solver_in_2d() -> None:
    metric_2d = ConformalMetric()          # legacy 2-D solver
    metric_nd = ConformalMetricND(gojo=(0.0, 0.0))  # same metric via n-D solver
    res2 = metric_2d.integrate_geodesic((-3.0, 0.5), (1.0, 0.0), dtau=1e-3, max_steps=4000)
    resn = metric_nd.integrate_geodesic((-3.0, 0.5), (1.0, 0.0), dtau=1e-3, max_steps=4000)
    # Same shared RHS math; the two agree to a few ULP (the legacy 2-D solver
    # reduces norms with math.hypot, the n-D solver with sqrt(sum), so the
    # trajectories match to floating-point round-off rather than bit-for-bit).
    for a, b in zip(resn.final_velocity, res2.final_velocity):
        assert math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-12)
    for a, b in zip(resn.points[-1], res2.points[-1]):
        assert math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-12)
    assert math.isclose(resn.arc_length, res2.arc_length, rel_tol=1e-12)


# ---------------------------------------------------------------------------
# Constructor validation, helpers, and the verdict
# ---------------------------------------------------------------------------

def test_constructor_rejects_bad_parameters_3d() -> None:
    with pytest.raises(ValueError):
        ConformalMetricND(sigma=0.0)
    with pytest.raises(ValueError):
        ConformalMetricND(lam=-1.0)
    with pytest.raises(ValueError):
        ConformalMetricND(gojo=())


def test_dimension_mismatch_is_rejected() -> None:
    with pytest.raises(ValueError):
        _METRIC.omega((1.0, 2.0))  # 2-vector into a 3-D metric


def test_unsigned_angle_basic() -> None:
    assert math.isclose(unsigned_angle((1.0, 0.0, 0.0), (0.0, 1.0, 0.0)), math.pi / 2)
    assert math.isclose(unsigned_angle((1.0, 0.0, 0.0), (-1.0, 0.0, 0.0)), math.pi)
    with pytest.raises(ValueError):
        unsigned_angle((0.0, 0.0, 0.0), (1.0, 0.0, 0.0))


def test_verdict_is_formidable_3d() -> None:
    assert verdict().verdict == "Formidable"
