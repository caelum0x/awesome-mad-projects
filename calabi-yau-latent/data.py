"""Generate structured toy data whose real structure lives in the COMPACT dims.

We create several ground-truth clusters. Each cluster is defined by a *phase
center* on the torus (angles). Crucially some clusters straddle the 0 / 2*pi
seam, so their members have raw angle values at BOTH ends of [0, 2*pi). A naive
Euclidean-on-raw-angles view will tear such a cluster apart; a wrap-aware view
keeps it together.

The extended (large) coordinates are deliberately noisy / non-informative, so
the only recoverable structure is in the compact factor -- the whole point.
"""
from __future__ import annotations

import math
import random
from typing import List, Tuple

from latent import CompactifiedLatentSpace, LatentPoint, TWO_PI


def make_space() -> CompactifiedLatentSpace:
    # 2 extended dims, 2 small compact circles (a 2-torus factor).
    return CompactifiedLatentSpace(k=2, radii=(0.10, 0.10))


def generate(
    space: CompactifiedLatentSpace,
    per_cluster: int = 12,
    seed: int = 7,
) -> Tuple[List[LatentPoint], List[int], List[Tuple[float, float]]]:
    """Return (points, ground_truth_labels, torus_coords_for_viz)."""
    rng = random.Random(seed)

    # Phase centers chosen to be well-separated ON THE TORUS (~pi apart), yet
    # two of them straddle a 0 / 2*pi seam so the naive view mis-handles them.
    centers = [
        (0.0, math.pi),             # cluster 0: straddles the theta1 seam
        (math.pi, 0.0),             # cluster 1: straddles the theta2 seam
        (math.pi, math.pi),         # cluster 2: interior, no seam
    ]
    spread = 0.30  # angular jitter around each center (tight clusters)

    points: List[LatentPoint] = []
    truth: List[int] = []
    torus_xy: List[Tuple[float, float]] = []

    for c_idx, (c1, c2) in enumerate(centers):
        for _ in range(per_cluster):
            t1 = (c1 + rng.gauss(0.0, spread)) % TWO_PI
            t2 = (c2 + rng.gauss(0.0, spread)) % TWO_PI
            # Extended coords: pure noise -> non-informative "large" dimensions.
            ext = [rng.gauss(0.0, 1.0), rng.gauss(0.0, 1.0)]
            raw = ext + [t1, t2]
            points.append(space.encode(raw))
            truth.append(c_idx)
            torus_xy.append((t1, t2))

    return points, truth, torus_xy
