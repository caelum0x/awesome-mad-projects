"""Tests for the metrics (calabi_yau_latent.core.distance).

The headline property: the wrap-aware (toroidal) metric respects periodicity, so
a pair straddling the 0 / 2*pi seam is CLOSE under the toroidal metric but FAR
under the naive one. Also checks circle_delta correctness and the radius-scaled
arc. Stdlib-only -> RUNS on both interpreters.
"""

from __future__ import annotations

import math

from calabi_yau_latent.core.distance import (
    circle_delta,
    naive_angular_distance,
    toroidal_angular_distance,
    toroidal_distance,
)
from calabi_yau_latent.core.latent import (
    TWO_PI,
    CompactifiedLatentSpace,
    LatentPoint,
)


def test_circle_delta_respects_wraparound() -> None:
    assert abs(circle_delta(0.05, TWO_PI - 0.05) - 0.10) < 1e-9


def test_circle_delta_is_antisymmetric() -> None:
    assert abs(circle_delta(1.0, 2.0) + circle_delta(2.0, 1.0)) < 1e-9


def test_circle_delta_in_half_open_pi_range() -> None:
    for a, b in [(0.0, math.pi), (0.3, 6.0), (5.9, 0.1)]:
        d = circle_delta(a, b)
        assert -math.pi < d <= math.pi


def test_seam_pair_close_under_toroidal_far_under_naive() -> None:
    # Same planted cluster, opposite sides of the theta1 = 0 / 2*pi seam.
    a = LatentPoint(extended=(), angles=(0.02, 0.0))
    b = LatentPoint(extended=(), angles=(TWO_PI - 0.02, 0.0))
    naive = naive_angular_distance(a, b)
    wrap = toroidal_angular_distance(a, b)
    assert naive > 6.0, "naive metric should see the seam pair as far apart"
    assert wrap < 0.1, "wrap-aware metric should see the seam pair as close"
    assert naive / wrap > 50.0


def test_toroidal_distance_uses_radius_scaled_arc() -> None:
    space = CompactifiedLatentSpace(k=0, radii=(0.5,))
    q0 = LatentPoint(extended=(), angles=(0.0,))
    q1 = LatentPoint(extended=(), angles=(math.pi,))
    assert abs(toroidal_distance(space, q0, q1) - 0.5 * math.pi) < 1e-9


def test_toroidal_distance_includes_extended_euclidean() -> None:
    space = CompactifiedLatentSpace(k=2, radii=(0.1,))
    p = LatentPoint(extended=(0.0, 0.0), angles=(0.0,))
    q = LatentPoint(extended=(3.0, 4.0), angles=(0.0,))
    assert abs(toroidal_distance(space, p, q) - 5.0) < 1e-9


def test_toroidal_metric_is_periodic() -> None:
    # Shifting an angle by exactly 2*pi must not change the toroidal distance.
    space = CompactifiedLatentSpace(k=0, radii=(0.3,))
    p = LatentPoint(extended=(), angles=(0.4,))
    q = LatentPoint(extended=(), angles=(1.1,))
    q_shift = LatentPoint(extended=(), angles=(1.1 + TWO_PI,))
    assert abs(
        toroidal_distance(space, p, q) - toroidal_distance(space, p, q_shift)
    ) < 1e-9
