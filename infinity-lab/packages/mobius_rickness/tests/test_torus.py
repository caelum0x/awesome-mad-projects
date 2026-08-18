"""Torus: closed-form vs numeric curvature, sign-changing zero circles."""

from __future__ import annotations

import math

import pytest

from mobius_rickness.core import torus
from mobius_rickness.core.tracer import trace_torus_zero_circles


def test_numeric_matches_closed_form() -> None:
    for i in range(24):
        theta = i * (2.0 * math.pi) / 24.0
        assert torus.gaussian_curvature(theta, 0.0) == pytest.approx(
            torus.gaussian_curvature_closed(theta), abs=1e-4
        )


def test_zeros_exactly_at_pi_over_2_and_3pi_over_2() -> None:
    assert torus.gaussian_curvature_closed(math.pi / 2.0) == pytest.approx(0.0, abs=1e-12)
    assert torus.gaussian_curvature_closed(3.0 * math.pi / 2.0) == pytest.approx(
        0.0, abs=1e-12
    )


def test_sign_pattern() -> None:
    assert torus.sign_pattern(0.0) == 1
    assert torus.sign_pattern(math.pi / 4.0) == 1
    assert torus.sign_pattern(3.0 * math.pi / 4.0) == -1
    assert torus.sign_pattern(math.pi) == -1


def test_curvature_changes_sign() -> None:
    outer = torus.gaussian_curvature_closed(0.0)
    inner = torus.gaussian_curvature_closed(math.pi)
    assert outer > 0.0
    assert inner < 0.0


def test_require_ring_rejects_non_ring() -> None:
    with pytest.raises(ValueError):
        torus.gaussian_curvature_closed(0.0, r0_major=1.0, r0_minor=1.0)
    with pytest.raises(ValueError):
        torus.require_ring(0.5, 1.0)


def test_traced_zero_circles_match_exact() -> None:
    traced = sorted(trace_torus_zero_circles(n_theta=400, tol=1e-9))
    exact = sorted(torus.zero_circles())
    assert len(traced) == 2
    for t, e in zip(traced, exact):
        assert t == pytest.approx(e, abs=1e-6)
