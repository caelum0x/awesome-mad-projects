"""Mobius strip: parametrization, seam identity, strict negativity of K."""

from __future__ import annotations

import math

import pytest

from mobius_rickness.core import mobius
from mobius_rickness.core.field import linspace


def test_center_line_curvature_is_minus_quarter() -> None:
    # On v = 0, E = 1 so K = -1/(4*1) = -0.25 exactly.
    for u in linspace(mobius.U_MIN, mobius.U_MAX, 13):
        assert mobius.gaussian_curvature(u, 0.0) == pytest.approx(-0.25, abs=1e-12)


def test_K_strictly_negative_on_interior() -> None:
    worst = mobius.assert_curvature_negative(n_u=40, n_v=11)
    assert worst < 0.0


def test_seam_identity_r_2pi_v_equals_r_0_minus_v() -> None:
    for v in (-0.5, -0.2, 0.0, 0.3, 0.5):
        assert mobius.seam_identity_error(v) < 1e-12


def test_surface_matches_known_points() -> None:
    # u = 0: r = (1 + v, 0, 0).
    assert mobius.surface(0.0, 0.4) == pytest.approx((1.4, 0.0, 0.0), abs=1e-12)
    # u = 2*pi: r = (1 - v, 0, 0).
    assert mobius.surface(2.0 * math.pi, 0.4) == pytest.approx((0.6, 0.0, 0.0), abs=1e-12)


def test_complex_surface_agrees_with_real_on_reals() -> None:
    for u, v in [(0.7, 0.2), (3.1, -0.3)]:
        real = mobius.surface(u, v)
        cx = mobius.surface_complex(u, v)
        for r, c in zip(real, cx):
            assert c.real == pytest.approx(r, abs=1e-12)
            assert abs(c.imag) < 1e-12
