"""Geometry engine: three cross-validating curvature paths and the seam wrap."""

from __future__ import annotations

import math

import pytest

from mobius_rickness.core import geometry as geo
from mobius_rickness.core import mobius


def _grid(n_u: int, n_v: int):
    us = [i * (2.0 * math.pi) / (n_u - 1) for i in range(n_u)]
    vs = [-0.4 + j * 0.8 / (n_v - 1) for j in range(n_v)]  # interior |v| <= 0.4
    return us, vs


def test_three_curvature_paths_agree() -> None:
    us, vs = _grid(13, 9)
    worst_fd = 0.0
    worst_cs = 0.0
    for u in us:
        for v in vs:
            a = mobius.gaussian_curvature(u, v)  # analytic oracle (path a)
            b = mobius.gaussian_curvature_numeric(u, v)  # central diff (path b)
            c = mobius.gaussian_curvature_complex_step(u, v)  # complex step (path c)
            worst_fd = max(worst_fd, abs(a - b))
            worst_cs = max(worst_cs, abs(a - c))
    assert worst_fd < 1e-5
    assert worst_cs < 1e-9


def test_analytic_curvature_strictly_negative() -> None:
    us, vs = _grid(20, 11)
    for u in us:
        for v in vs:
            assert mobius.gaussian_curvature(u, v) < 0.0


def test_mobius_E_matches_definition() -> None:
    for u, v in [(0.3, 0.2), (2.0, -0.3), (5.1, 0.45)]:
        expected = (1.0 + v * math.cos(u / 2.0)) ** 2 + v * v / 4.0
        assert geo.mobius_E(u, v) == pytest.approx(expected, rel=0, abs=1e-15)


def test_seam_wrap_flips_v_for_odd_wraps() -> None:
    # r(2*pi + eps, v) == r(0, -v): one wrap -> v flipped.
    u, v = 2.0 * math.pi + 0.3, 0.25
    wu, wv = geo.mobius_seam_wrap(u, v)
    assert wu == pytest.approx(0.3, abs=1e-12)
    assert wv == pytest.approx(-0.25, abs=1e-15)
    # Two wraps -> v restored.
    wu2, wv2 = geo.mobius_seam_wrap(4.0 * math.pi + 0.3, 0.25)
    assert wv2 == pytest.approx(0.25, abs=1e-15)


def test_identity_wrap_is_noop() -> None:
    assert geo.identity_wrap(1.23, -0.4) == (1.23, -0.4)


def test_fundamental_forms_collapse() -> None:
    # Ruled orthogonal parametrization: F = 0, G = 1, N = 0, M = -1/(2 sqrt E).
    for u, v in [(0.7, 0.2), (3.3, -0.25), (5.0, 0.15)]:
        E, F, G, L, M, N = mobius.fundamental_forms(u, v)
        assert F == pytest.approx(0.0, abs=1e-6)
        assert G == pytest.approx(1.0, abs=1e-6)
        assert N == pytest.approx(0.0, abs=1e-6)
        assert M == pytest.approx(-1.0 / (2.0 * math.sqrt(geo.mobius_E(u, v))), abs=1e-5)
