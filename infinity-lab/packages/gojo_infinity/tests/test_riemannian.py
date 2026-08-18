"""Lens 3 (Riemannian conformal geometry) -- pinned Figure-8 targets."""

from __future__ import annotations

import math

import pytest

from gojo_infinity.core import riemannian as rm


def test_gaussian_kernel_basic() -> None:
    assert rm.gaussian_kernel(1.0, 1.0, sigma=0.35) == 1.0
    assert 0.0 < rm.gaussian_kernel(0.0, 1.0, sigma=0.35) < 1.0


def test_conformal_factor_raises_at_and_past_the_pole() -> None:
    with pytest.raises(ValueError):
        rm.conformal_factor(1.0)   # x == x_gojo
    with pytest.raises(ValueError):
        rm.conformal_factor(1.5)   # x > x_gojo


def test_calibrate_derives_lambda_and_hits_targets() -> None:
    res = rm.calibrate()
    # lambda is DERIVED (not hardcoded); reproduces the documented default.
    assert math.isclose(res.lam, rm.DEFAULT_LAMBDA, abs_tol=1e-9)
    assert 0.27 < res.lam < 0.30
    # Figure-8 near target: g(0.8) ~ 4.1 and felt ds ~ 0.20.
    assert math.isclose(res.g_near, 4.1, abs_tol=1e-6)
    assert math.isclose(res.ds_near, 0.20, abs_tol=0.01)
    # Figure-8 far target: g(0.1) ~ 1.0 and felt ds ~ 0.10.
    assert math.isclose(res.g_far, 1.0, abs_tol=0.01)
    assert math.isclose(res.ds_far, 0.10, abs_tol=0.01)


def test_metric_g11_reproduces_figure8_with_calibrated_lambda() -> None:
    res = rm.calibrate()
    g_far = rm.metric_g11(0.1, sigma=res.sigma, lam=res.lam)
    g_near = rm.metric_g11(0.8, sigma=res.sigma, lam=res.lam)
    assert math.isclose(g_far, 1.0, abs_tol=0.01)
    assert math.isclose(g_near, 4.1, abs_tol=1e-6)
    ds_far = rm.felt_step(0.1, 0.1, sigma=res.sigma, lam=res.lam)
    ds_near = rm.felt_step(0.8, 0.1, sigma=res.sigma, lam=res.lam)
    assert math.isclose(ds_far, 0.10, abs_tol=0.01)
    assert math.isclose(ds_near, 0.20, abs_tol=0.01)


def test_calibrate_hard_fails_on_impossible_target() -> None:
    with pytest.raises(rm.CalibrationError):
        rm.calibrate(g_near_target=1.0)  # Omega must exceed 1 near the pole
    with pytest.raises(rm.CalibrationError):
        rm.calibrate(g_near_target=1e9, lam_hi=1e-6)  # bracket cannot reach it


def test_geodesic_to_barrier_is_exactly_math_inf() -> None:
    d = rm.geodesic_to_barrier(0.0)
    assert d == math.inf
    assert math.isinf(d)
    assert isinstance(d, float)
    # explicit return of the improper integral through geodesic_length too
    assert rm.geodesic_length(0.0, rm.X_GOJO) == math.inf


def test_geodesic_below_barrier_is_finite() -> None:
    d = rm.geodesic_length(0.0, 0.9)
    assert math.isfinite(d)
    assert d > 0.9  # felt length exceeds the flat length


def test_naive_quadrature_is_finite_and_labelled_failure_mode() -> None:
    # DEMO ONLY: the weak finite sum reports a finite "distance" and grows as the
    # truncation shrinks, never reaching the true +inf -- that is the point.
    near = rm.naive_geodesic_to_barrier(0.0, eps=1e-3)
    nearer = rm.naive_geodesic_to_barrier(0.0, eps=1e-6)
    assert math.isfinite(near) and math.isfinite(nearer)
    assert nearer > near  # keeps growing but never becomes inf


def test_divergence_by_decade_increment_tends_to_lambda_ln10() -> None:
    res = rm.calibrate()
    deltas = [1e-2, 1e-3, 1e-4, 1e-5, 1e-6]
    rows = rm.divergence_by_decade(0.0, deltas, sigma=res.sigma, lam=res.lam)
    lengths = [L for _, L in rows]
    # deepest decades approach the analytic lam*ln(10) increment.
    last_increment = lengths[-1] - lengths[-2]
    assert math.isclose(last_increment, rm.per_decade_increment(res.lam), rel_tol=0.02)


def test_geodesic_ball_solution_strictly_inside() -> None:
    res = rm.calibrate()
    x_star = rm.geodesic_ball_radius_solve(0.0, 5.0, sigma=res.sigma, lam=res.lam)
    assert 0.0 < x_star < rm.X_GOJO


def test_verdict_is_formidable() -> None:
    assert rm.verdict().verdict == "Formidable"
