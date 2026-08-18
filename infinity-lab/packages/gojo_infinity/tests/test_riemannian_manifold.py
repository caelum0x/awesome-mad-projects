"""Tests for the 2-D Riemannian-manifold geodesic solver (pure core).

These are pure stdlib + ``commons.core`` tests, so they RUN on BOTH the
stdlib-only system interpreter and the venv (no numpy/matplotlib needed). They
cover: the metric far from Gojo, positive-definiteness, the Christoffel
closed-form vs general cross-check, affine-energy conservation, flat-region
straightness, RADIAL PARITY with the existing 1-D lens, the felt-length
divergence, and grazing deflection.
"""

from __future__ import annotations

import math

import pytest

from commons.core import central_difference
from gojo_infinity.core.riemannian import DEFAULT_LAMBDA, geodesic_length
from gojo_infinity.core.riemannian_manifold import (
    ConformalMetric,
    max_christoffel_difference,
    signed_angle,
    verdict,
)

_METRIC = ConformalMetric()  # Gojo at origin, sigma/lam from the 1-D lens

# A spread of test points (all away from Gojo where Omega is finite).
_POINTS = [
    (0.5, 0.3), (1.0, -0.4), (2.0, 0.1), (0.3, 0.0),
    (-0.7, 0.9), (-1.2, -0.6), (0.2, -0.25), (1.5, 1.5),
]


# ---------------------------------------------------------------------------
# 1. Metric far from Gojo ~ identity; SPD and symmetric everywhere
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("p", [(5.0, 3.0), (10.0, 0.0), (-8.0, 6.0)])
def test_metric_far_from_gojo_is_identity(p) -> None:
    g = _METRIC.metric_tensor(p)
    assert math.isclose(_METRIC.omega(p), 1.0, abs_tol=1e-9)
    assert math.isclose(g[0][0], 1.0, abs_tol=1e-9)
    assert math.isclose(g[1][1], 1.0, abs_tol=1e-9)
    assert g[0][1] == 0.0 and g[1][0] == 0.0


@pytest.mark.parametrize("p", _POINTS)
def test_metric_is_symmetric_positive_definite(p) -> None:
    g = _METRIC.metric_tensor(p)
    # symmetric
    assert g[0][1] == g[1][0]
    # positive-definite (diagonal conformal): both entries > 0 and det > 0
    assert g[0][0] > 0.0 and g[1][1] > 0.0
    det = g[0][0] * g[1][1] - g[0][1] * g[1][0]
    assert det > 0.0
    # inverse really inverts
    inv = _METRIC.inverse_metric(p)
    assert math.isclose(g[0][0] * inv[0][0], 1.0, rel_tol=1e-12)


def test_omega_diverges_toward_gojo() -> None:
    near = _METRIC.omega((1e-3, 0.0))
    far = _METRIC.omega((3.0, 0.0))
    assert near > far > 1.0 - 1e-12
    with pytest.raises(ValueError):
        _METRIC.omega((0.0, 0.0))  # exactly at Gojo -> singular


# ---------------------------------------------------------------------------
# 2. Christoffel closed form matches the general finite-difference formula
# ---------------------------------------------------------------------------

def test_christoffel_conformal_matches_general() -> None:
    worst = max_christoffel_difference(_METRIC, _POINTS, h=1e-5)
    assert worst < 1e-6, f"closed-form vs general Christoffel diff too large: {worst}"


@pytest.mark.parametrize("p", _POINTS)
def test_christoffel_symmetric_in_lower_indices(p) -> None:
    gamma = _METRIC.christoffel_conformal(p)
    for k in range(2):
        assert gamma[k][0][1] == gamma[k][1][0]


@pytest.mark.parametrize("p", _POINTS)
def test_grad_phi_analytic_matches_finite_difference(p) -> None:
    ana = _METRIC.grad_phi(p)
    fd0 = central_difference(lambda t: _METRIC.phi((t, p[1])), p[0], 1e-6)
    fd1 = central_difference(lambda t: _METRIC.phi((p[0], t)), p[1], 1e-6)
    assert math.isclose(ana[0], fd0, rel_tol=1e-5, abs_tol=1e-8)
    assert math.isclose(ana[1], fd1, rel_tol=1e-5, abs_tol=1e-8)


# ---------------------------------------------------------------------------
# 3. Affine-parameter invariant Omega^2 |v|^2 conserved along a geodesic
# ---------------------------------------------------------------------------

def test_affine_energy_is_conserved_along_geodesic() -> None:
    res = _METRIC.integrate_geodesic((-3.0, 0.5), (1.0, 0.0), dtau=1e-3, max_steps=6000)
    assert res.energy_drift < 1e-6, f"energy drift too large: {res.energy_drift}"


# ---------------------------------------------------------------------------
# 4. Flat region: where Omega ~ 1 the geodesic is ~straight
# ---------------------------------------------------------------------------

def test_flat_region_geodesic_is_straight() -> None:
    res = _METRIC.integrate_geodesic((6.0, 3.0), (1.0, 0.0), dtau=1e-2, max_steps=400)
    # direction preserved: essentially no turning
    assert abs(res.deflection_angle) < 1e-6
    # points stay collinear with the initial ray (y ~ const = 3.0)
    max_dy = max(abs(p[1] - 3.0) for p in res.points)
    assert max_dy < 1e-6


# ---------------------------------------------------------------------------
# 5. PARITY with the 1-D lens: a radial approach matches exactly, stays radial
# ---------------------------------------------------------------------------

def test_radial_geodesic_matches_1d_lens_and_stays_radial() -> None:
    d0 = 0.5
    res = _METRIC.integrate_geodesic(
        (d0, 0.0), (-1.0, 0.0), dtau=1e-3, target_radius=0.05, max_steps=500_000
    )
    assert res.stop_reason == "reached_target"

    # stays exactly radial by symmetry: no tangential drift at all
    assert max(abs(p[1]) for p in res.points) == 0.0
    assert res.final_velocity[1] == 0.0

    # felt length equals the radial integral AND the existing 1-D lens length
    ref_radial = _METRIC.felt_length_to_reach(res.final_radius, start_radius=d0)
    ref_1d = geodesic_length(1.0 - d0, 1.0 - res.final_radius)
    assert math.isclose(res.arc_length, ref_radial, rel_tol=1e-6, abs_tol=1e-9)
    assert math.isclose(res.arc_length, ref_1d, rel_tol=1e-6, abs_tol=1e-9)


def test_felt_length_to_reach_matches_1d_lens_directly() -> None:
    # A grid of (start, target) radii, compared to the 1-D geodesic_length.
    for d0, delta in [(0.9, 0.1), (0.8, 0.2), (0.5, 0.01), (0.95, 0.001)]:
        got = _METRIC.felt_length_to_reach(delta, start_radius=d0)
        ref = geodesic_length(1.0 - d0, 1.0 - delta)
        assert math.isclose(got, ref, rel_tol=1e-8, abs_tol=1e-10)


# ---------------------------------------------------------------------------
# 6. Divergence: felt length to reach within delta is monotone and unbounded
# ---------------------------------------------------------------------------

def test_felt_length_divergence_is_monotone_and_unbounded() -> None:
    deltas = [10.0 ** (-k) for k in range(1, 9)]  # 1e-1 .. 1e-8
    table = _METRIC.felt_length_divergence(deltas, start_radius=0.9)
    lengths = [L for _, L in table]
    # strictly increasing as delta shrinks
    for prev, nxt in zip(lengths, lengths[1:]):
        assert nxt > prev
    # exceeds any bound: the deepest length is far above the shallowest
    assert lengths[-1] - lengths[0] > 4.0
    # per-decade increment approaches lam * ln(10)
    per_decade = lengths[-1] - lengths[-2]
    assert math.isclose(per_decade, DEFAULT_LAMBDA * math.log(10.0), abs_tol=5e-3)


def test_felt_length_exceeds_arbitrary_bound() -> None:
    # For any bound M there is a delta small enough to exceed it (Infinity).
    for bound in (5.0, 10.0, 20.0):
        # -lam ln(delta) ~ bound  =>  delta ~ exp(-bound/lam)
        delta = math.exp(-(bound + 5.0) / DEFAULT_LAMBDA)
        length = _METRIC.felt_length_to_reach(delta, start_radius=0.9)
        assert length > bound


# ---------------------------------------------------------------------------
# 7. Deflection: a grazing geodesic bends TOWARD Gojo (light-bending analog)
# ---------------------------------------------------------------------------

def test_grazing_geodesic_deflects_toward_gojo() -> None:
    # Ray passes above Gojo (y = 0.5 > 0), moving in +x. It must bend downward
    # (toward Gojo), acquiring a negative y-velocity and a non-zero turning angle.
    res = _METRIC.integrate_geodesic((-3.0, 0.5), (1.0, 0.0), dtau=1e-3, max_steps=6000)
    assert res.final_velocity[1] < 0.0, "ray did not bend toward Gojo"
    assert abs(res.deflection_angle) > 1e-2, "no measurable deflection"


def test_straight_ray_far_away_does_not_deflect() -> None:
    # Control: the same ray but far from Gojo barely deflects.
    res = _METRIC.integrate_geodesic((-3.0, 6.0), (1.0, 0.0), dtau=1e-3, max_steps=6000)
    assert abs(res.deflection_angle) < 1e-6


# ---------------------------------------------------------------------------
# Constructor validation, helpers, and the verdict
# ---------------------------------------------------------------------------

def test_constructor_rejects_bad_parameters() -> None:
    with pytest.raises(ValueError):
        ConformalMetric(sigma=0.0)
    with pytest.raises(ValueError):
        ConformalMetric(lam=-1.0)


def test_felt_length_to_reach_validates_arguments() -> None:
    with pytest.raises(ValueError):
        _METRIC.felt_length_to_reach(0.0, start_radius=0.5)
    with pytest.raises(ValueError):
        _METRIC.felt_length_to_reach(0.6, start_radius=0.5)  # target >= start


def test_signed_angle_basic() -> None:
    assert math.isclose(signed_angle((1.0, 0.0), (0.0, 1.0)), math.pi / 2, rel_tol=1e-12)
    assert math.isclose(signed_angle((1.0, 0.0), (0.0, -1.0)), -math.pi / 2, rel_tol=1e-12)


def test_verdict_is_formidable() -> None:
    assert verdict().verdict == "Formidable"


def test_integrate_geodesic_validates_arguments() -> None:
    with pytest.raises(ValueError):
        _METRIC.integrate_geodesic((0.5, 0.0), (-1.0, 0.0), dtau=0.0)
    with pytest.raises(ValueError):
        _METRIC.integrate_geodesic((0.5, 0.0), (-1.0, 0.0), max_steps=0)
