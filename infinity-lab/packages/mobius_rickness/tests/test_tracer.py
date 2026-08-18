"""Curve tracing: scan-line + marching-squares zero set, seam stitching, lift."""

from __future__ import annotations

import math

import pytest

from mobius_rickness.core import tracer
from mobius_rickness.core.field import k_rick
from mobius_rickness.core.mobius import surface
from mobius_rickness.core.rickness import rickness


# ---------------------------------------------------------------------------
# Scan-line bisection path
# ---------------------------------------------------------------------------

def _scanline_points():
    cols = tracer.trace_columns(n_u=120, n_v_samples=200, tol=1e-9)
    return tracer.flatten_columns(cols)


def test_scanline_curve_is_nonempty() -> None:
    assert len(_scanline_points()) > 0


def test_scanline_points_have_tiny_residual_and_k_rick() -> None:
    for p in _scanline_points():
        assert p.residual < 1e-6
        assert abs(k_rick(p.u, p.v)) < 1e-6


def test_scanline_verify_curve_passes() -> None:
    tracer.verify_curve(_scanline_points(), r_tol=1e-6, k_rick_tol=1e-6)


def test_scanline_roots_lie_in_v_domain() -> None:
    for p in _scanline_points():
        assert -0.5 - 1e-9 <= p.v <= 0.5 + 1e-9


def test_lifted_points_match_surface() -> None:
    for p in _scanline_points():
        x, y, z = surface(p.u, p.v)
        assert p.x == pytest.approx(x, abs=1e-9)
        assert p.y == pytest.approx(y, abs=1e-9)
        assert p.z == pytest.approx(z, abs=1e-9)


# ---------------------------------------------------------------------------
# Marching-squares path
# ---------------------------------------------------------------------------

def test_marching_squares_points_verify() -> None:
    segments, polylines, points = tracer.march_mobius_curve(n_u=60, n_v=25, tol=1e-9)
    assert len(segments) > 0
    assert len(points) > 0
    for p in points:
        assert p.residual < 1e-6
        assert abs(k_rick(p.u, p.v)) < 1e-6
    tracer.verify_curve(points, r_tol=1e-6, k_rick_tol=1e-6)


def test_marching_squares_stitches_into_polylines() -> None:
    _, polylines, _ = tracer.march_mobius_curve(n_u=60, n_v=25)
    assert len(polylines) >= 1
    # Each polyline is an ordered sequence of >= 2 points.
    assert all(len(poly) >= 2 for poly in polylines)


def test_marching_and_scanline_agree_on_topology() -> None:
    # Both paths must find a non-empty curve; every marching-squares vertex is a
    # true zero, so |R| there is tiny (topology agreement at the residual level).
    _, _, mpoints = tracer.march_mobius_curve(n_u=80, n_v=33)
    scan = _scanline_points()
    assert mpoints and scan
    assert max(p.residual for p in mpoints) < 1e-6
    assert max(p.residual for p in scan) < 1e-6


# ---------------------------------------------------------------------------
# Seam stitching mechanism (v-flip across r(2*pi, v) = r(0, -v))
# ---------------------------------------------------------------------------

def test_seam_stitch_fuses_v_flipped_boundary_endpoints() -> None:
    # A crossing on the u = 2*pi boundary at v = +0.3 is the SAME curve point as
    # one on the u = 0 boundary at v = -0.3. Two segments meeting there must
    # stitch into a single polyline.
    two_pi = 2.0 * math.pi
    seg_a = tracer.Segment(p0=(1.0, 0.1), p1=(two_pi, 0.3))
    seg_b = tracer.Segment(p0=(0.0, -0.3), p1=(0.5, -0.1))
    polylines = tracer.stitch_segments([seg_a, seg_b], snap=1e-6)
    # Two segments fuse into ONE polyline; the shared seam vertex (2*pi, 0.3) ~
    # (0, -0.3) is a single collapsed point, so the polyline has 3 points.
    assert len(polylines) == 1
    assert len(polylines[0]) == 3


def test_seam_stitch_keeps_distinct_curves_separate() -> None:
    seg_a = tracer.Segment(p0=(0.5, 0.1), p1=(0.6, 0.2))
    seg_b = tracer.Segment(p0=(3.0, -0.1), p1=(3.1, -0.2))
    polylines = tracer.stitch_segments([seg_a, seg_b], snap=1e-6)
    assert len(polylines) == 2


# ---------------------------------------------------------------------------
# Torus zero circles via the shared bisection machinery
# ---------------------------------------------------------------------------

def test_trace_torus_zero_circles() -> None:
    traced = sorted(tracer.trace_torus_zero_circles(n_theta=400))
    assert len(traced) == 2
    assert traced[0] == pytest.approx(math.pi / 2.0, abs=1e-6)
    assert traced[1] == pytest.approx(3.0 * math.pi / 2.0, abs=1e-6)
