"""Runnable demo: naive vs topology-aware view of a compactified latent space.

Run:  python3 demo.py

Shows, on toy data whose real structure lives entirely in the small COMPACT
(periodic) dimensions:
  1. Why a naive number-line view tears a seam-straddling cluster apart.
  2. Nearest-neighbor accuracy: naive vs wrap-aware.
  3. Connected-components clustering: naive vs wrap-aware (#clusters + purity).
  4. An ASCII torus showing wrap-aware clusters.
  5. A holonomy-flavored parallel-transport cartoon (labeled ANALOGY).

This is a TOY. It is NOT a Calabi-Yau manifold. See README.md.
"""
from __future__ import annotations

from data import make_space, generate
from distance import (
    naive_angular_distance,
    toroidal_angular_distance,
)
from clustering import cluster, nearest_neighbor, num_clusters, purity
from ascii_viz import torus_grid, wrap_number_line, render_holonomy
from holonomy import transport_around_loop, holonomy_angle, loop_trace
from latent import HAVE_NUMPY


def _rule(title: str) -> None:
    print("\n" + "=" * 68)
    print(title)
    print("=" * 68)


def nn_accuracy(points, truth, dist) -> float:
    """Fraction of points whose nearest neighbor shares the true cluster."""
    correct = 0
    for i, p in enumerate(points):
        j = nearest_neighbor(p, points, dist)
        if j >= 0 and truth[j] == truth[i]:
            correct += 1
    return correct / len(points)


def main() -> None:
    space = make_space()
    points, truth, torus_xy = generate(space, per_cluster=12, seed=7)
    n = len(points)

    print("Compactified latent space (TOY analogy for CY compactification)")
    print(f"  extended dims k = {space.k}   compact circles m = {space.m}   "
          f"radii = {space.radii}")
    print(f"  points = {n}   ground-truth clusters = {num_clusters(truth)}")
    print(f"  numpy available: {HAVE_NUMPY} (not required; pure-Python core)")

    # --- 1. The seam problem -------------------------------------------------
    _rule("1) The seam problem: cluster 0 straddles theta1 = 0 / 2*pi")
    seam_angles = [p.angles[0] for p, t in zip(points, truth) if t == 0]
    print(wrap_number_line(seam_angles))
    print("\n  On the CIRCLE these are one tight blob near 0; on the naive")
    print("  number line they split into two far-apart groups.")

    # --- 2. Two points that straddle the seam --------------------------------
    _rule("2) Same cluster, opposite sides of the seam: metric disagreement")
    idxs = [i for i, t in enumerate(truth) if t == 0]
    lo = min(idxs, key=lambda i: points[i].angles[0])   # theta1 ~ 0+
    hi = max(idxs, key=lambda i: points[i].angles[0])   # theta1 ~ 2*pi-
    p_lo, p_hi = points[lo], points[hi]
    print(f"  point A theta = ({p_lo.angles[0]:.3f}, {p_lo.angles[1]:.3f})  "
          f"(true cluster {truth[lo]})")
    print(f"  point B theta = ({p_hi.angles[0]:.3f}, {p_hi.angles[1]:.3f})  "
          f"(true cluster {truth[hi]})")
    d_naive = naive_angular_distance(p_lo, p_hi)
    d_wrap = toroidal_angular_distance(p_lo, p_hi)
    print(f"  naive distance      : {d_naive:6.3f}  (looks FAR -> wrong)")
    print(f"  wrap-aware distance : {d_wrap:6.3f}  (correctly CLOSE)")
    print(f"  ratio naive/wrap    : {d_naive / d_wrap:6.1f}x overestimate")

    # Aggregate nearest-neighbor accuracy for completeness.
    acc_naive = nn_accuracy(points, truth, naive_angular_distance)
    acc_wrap = nn_accuracy(points, truth, toroidal_angular_distance)
    print(f"\n  aggregate NN same-cluster accuracy: "
          f"naive {acc_naive:.0%} vs wrap {acc_wrap:.0%}")

    # --- 3. Clustering -------------------------------------------------------
    _rule("3) Connected-components clustering (target = 3 clusters)")
    thr = 0.9  # angular threshold; same for both metrics for fairness
    lab_naive = cluster(points, naive_angular_distance, thr)
    lab_wrap = cluster(points, toroidal_angular_distance, thr)
    print(f"  threshold = {thr}")
    print(f"  naive      : #clusters = {num_clusters(lab_naive):2d}   "
          f"purity = {purity(lab_naive, truth):.2f}")
    print(f"  wrap-aware : #clusters = {num_clusters(lab_wrap):2d}   "
          f"purity = {purity(lab_wrap, truth):.2f}")
    print("  (Naive over-segments: it breaks seam-straddling clusters into")
    print("   extra pieces. Wrap-aware recovers the true count.)")

    # --- 4. ASCII torus ------------------------------------------------------
    _rule("4) The compact 2-torus (wrap-aware cluster labels)")
    print(torus_grid(torus_xy, lab_wrap))

    # --- 5. Holonomy analogy -------------------------------------------------
    _rule("5) Holonomy-flavored parallel transport (ANALOGY, not real CY)")
    curvature = 0.15
    final_v, holo = transport_around_loop((1.0, 0.0), curvature=curvature)
    print(f"  transport (1,0) once around a compact loop, curvature={curvature}")
    print(f"  net holonomy angle (measured) = {holo:.4f} rad")
    print(f"  net holonomy angle (closed form) = {holonomy_angle(curvature):.4f} rad")
    print(f"  final vector = ({final_v[0]:+.4f}, {final_v[1]:+.4f})")
    print("\n  A nonzero holonomy means the loop is not contractible-to-trivial")
    print("  under this toy connection. Real Calabi-Yau spaces are prized for")
    print("  their SPECIAL (SU(n)) holonomy -- deep geometry we do NOT claim to")
    print("  reproduce here. This is a tangible cartoon of the idea only.")
    print()
    print(render_holonomy(loop_trace((1.0, 0.0), curvature=curvature, samples=8)))

    _rule("Summary")
    print("  Structure planted in the small COMPACT dimensions is invisible to")
    print("  a naive Euclidean view (it tears wrap-around clusters), but fully")
    print("  recovered once the periodic torus topology is respected.")
    print("  Reminder: TOY analogy. Not a real Calabi-Yau metric. See README.md.")


if __name__ == "__main__":
    main()
