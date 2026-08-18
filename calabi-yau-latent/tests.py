"""Lightweight self-tests (no pytest required):  python3 tests.py

Covers: angle wrapping, encode/decode round-trip, wrap vs naive metric
behavior at the seam, clustering recovery, and holonomy closed-form.
"""
from __future__ import annotations

import math

from latent import CompactifiedLatentSpace, LatentPoint, TWO_PI
from distance import (
    circle_delta,
    naive_angular_distance,
    toroidal_angular_distance,
    toroidal_distance,
)
from clustering import cluster, num_clusters, purity
from holonomy import holonomy_angle, transport_around_loop
from data import make_space, generate

_failures = []


def check(name: str, cond: bool) -> None:
    status = "ok  " if cond else "FAIL"
    if not cond:
        _failures.append(name)
    print(f"  [{status}] {name}")


def main() -> None:
    print("Running self-tests...")

    # Angle normalization is applied and never mutates the input tuple.
    src = (TWO_PI + 0.5, -0.25)
    p = LatentPoint(extended=(1.0,), angles=src)
    check("angles wrapped into [0, 2*pi)",
          all(0.0 <= a < TWO_PI for a in p.angles))
    check("wrap of 2*pi+0.5 == 0.5", abs(p.angles[0] - 0.5) < 1e-9)

    # circle_delta respects wrap-around.
    check("circle_delta(0.05, 2*pi-0.05) is small",
          abs(circle_delta(0.05, TWO_PI - 0.05) - 0.10) < 1e-9)
    check("circle_delta antisymmetric",
          abs(circle_delta(1.0, 2.0) + circle_delta(2.0, 1.0)) < 1e-9)

    # Encode/decode round-trip preserves angles.
    space = CompactifiedLatentSpace(k=2, radii=(0.1, 0.2))
    pt = space.encode([0.3, -1.2, 5.9, 0.1])
    check("decode embedding length = k + 2m",
          len(space.decode(pt)) == space.k + 2 * space.m)
    check("angle round-trip ok", space.roundtrip_angles_ok(pt))

    # Seam: naive overestimates, wrap stays small.
    a = LatentPoint(extended=(), angles=(0.02, 0.0))
    b = LatentPoint(extended=(), angles=(TWO_PI - 0.02, 0.0))
    check("naive seam distance is large", naive_angular_distance(a, b) > 6.0)
    check("wrap seam distance is small", toroidal_angular_distance(a, b) < 0.1)

    # toroidal_distance uses radii (arc = r * delta).
    s1 = CompactifiedLatentSpace(k=0, radii=(0.5,))
    q0 = LatentPoint(extended=(), angles=(0.0,))
    q1 = LatentPoint(extended=(), angles=(math.pi,))
    check("radius-scaled arc = r*pi",
          abs(toroidal_distance(s1, q0, q1) - 0.5 * math.pi) < 1e-9)

    # Clustering: wrap recovers 3, naive over-segments.
    sp = make_space()
    pts, truth, _ = generate(sp, per_cluster=12, seed=7)
    lab_naive = cluster(pts, naive_angular_distance, 0.9)
    lab_wrap = cluster(pts, toroidal_angular_distance, 0.9)
    check("wrap-aware recovers 3 clusters", num_clusters(lab_wrap) == 3)
    check("wrap-aware purity == 1.0", purity(lab_wrap, truth) == 1.0)
    check("naive over-segments (>3 clusters)", num_clusters(lab_naive) > 3)

    # Holonomy closed form matches measured transport.
    _, measured = transport_around_loop((1.0, 0.0), curvature=0.15, steps=720)
    check("holonomy measured == closed form",
          abs(measured - holonomy_angle(0.15)) < 1e-6)

    print()
    if _failures:
        print(f"FAILED: {len(_failures)} -> {_failures}")
        raise SystemExit(1)
    print("All tests passed.")


if __name__ == "__main__":
    main()
