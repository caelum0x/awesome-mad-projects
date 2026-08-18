"""Tests for the ASCII renderers (calabi_yau_latent.adapters.ascii_viz).

Deterministic, pure-stdlib text output: same inputs -> byte-identical string.
Checks the torus grid places wrapped points, the naive number line shows the seam
split, and the holonomy trace renders. Stdlib-only -> RUNS on both interpreters.
"""

from __future__ import annotations

import math

import pytest

from calabi_yau_latent.adapters.ascii_viz import (
    render_holonomy,
    torus_grid,
    wrap_number_line,
)
from calabi_yau_latent.core.holonomy import loop_trace

TWO_PI = 2.0 * math.pi


def test_torus_grid_is_deterministic() -> None:
    points = [(0.1, 0.1), (math.pi, math.pi), (TWO_PI - 0.1, 0.2)]
    labels = [0, 1, 0]
    a = torus_grid(points, labels, width=20, height=10)
    b = torus_grid(points, labels, width=20, height=10)
    assert a == b
    assert "theta1" in a and "theta2" in a


def test_torus_grid_is_periodic_in_both_angles() -> None:
    # Adding a full 2*pi to either angle must render to the identical cell: the
    # grid identifies opposite edges (that IS the torus).
    base = torus_grid([(0.05, 0.10)], [3], width=20, height=10)
    shifted = torus_grid([(0.05 + TWO_PI, 0.10 + TWO_PI)], [3], width=20, height=10)
    assert base == shifted


def test_torus_grid_maps_zero_angle_to_left_edge() -> None:
    # An angle of exactly 2*pi wraps to column 0 (same cell as angle 0).
    grid = torus_grid([(TWO_PI, 0.0)], [3], width=20, height=10)
    body = grid.splitlines()[1]  # first interior row
    assert body.startswith("  |3")


def test_torus_grid_validates_lengths() -> None:
    with pytest.raises(ValueError):
        torus_grid([(0.0, 0.0)], [0, 1], width=10, height=10)


def test_wrap_number_line_marks_both_ends_for_seam_cluster() -> None:
    out = wrap_number_line([0.02, TWO_PI - 0.02], width=48)
    body = [ln for ln in out.splitlines() if ln.strip().startswith("[")][0]
    inner = body.strip()[1:-1]
    assert inner[0] == "*"      # near 0
    assert inner[-1] == "*"     # near 2*pi
    assert "naive" in out


def test_wrap_number_line_rejects_tiny_width() -> None:
    with pytest.raises(ValueError):
        wrap_number_line([0.0], width=3)


def test_render_holonomy_lists_each_sample() -> None:
    trace = loop_trace((1.0, 0.0), curvature=0.15, samples=8)
    out = render_holonomy(trace)
    assert out.count("\n") == 8  # header + 8 rows -> 8 newlines
    assert "vector" in out
