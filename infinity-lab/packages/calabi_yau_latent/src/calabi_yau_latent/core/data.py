"""Generate structured toy data whose real structure lives in the COMPACT dims.

We create several ground-truth clusters. Each cluster is defined by a *phase
centre* on the torus (angles). Crucially some clusters straddle the ``0 / 2*pi``
seam, so their members have raw angle values at BOTH ends of ``[0, 2*pi)``. A
naive Euclidean-on-raw-angles view tears such a cluster apart; a wrap-aware view
keeps it together.

The extended (large) coordinates are deliberately noisy / non-informative, so the
only recoverable structure is in the compact factor -- the whole point.

Purity: imports only the standard library, :mod:`commons.core` (via
:mod:`calabi_yau_latent.core.sampling`) and sibling core modules.
"""

from __future__ import annotations

from typing import List, Tuple

from calabi_yau_latent.core.config import DEFAULT, CYConfig
from calabi_yau_latent.core.latent import (
    TWO_PI,
    CompactifiedLatentSpace,
    LatentPoint,
)
from calabi_yau_latent.core.sampling import gauss, make_stream


def make_space(config: CYConfig = DEFAULT) -> CompactifiedLatentSpace:
    """Build the compactified latent space described by ``config``."""
    return CompactifiedLatentSpace(k=config.k, radii=config.radii)


def generate(
    space: CompactifiedLatentSpace,
    config: CYConfig = DEFAULT,
) -> Tuple[List[LatentPoint], List[int], List[Tuple[float, float]]]:
    """Return ``(points, ground_truth_labels, torus_coords_for_viz)``.

    Phase centres come from ``config.centers`` (some straddling a ``0 / 2*pi``
    seam). Each cluster gets ``config.per_cluster`` points jittered by
    ``config.spread`` radians; the extended coordinates are pure Gaussian noise so
    the recoverable structure lives entirely in the compact factor.

    The returned ``torus_coords_for_viz`` are the first two raw angles per point,
    convenient for the 2-torus ASCII / PNG renderers.
    """
    rng = make_stream(config.seed)

    points: List[LatentPoint] = []
    truth: List[int] = []
    torus_xy: List[Tuple[float, float]] = []

    for c_idx, center in enumerate(config.centers):
        for _ in range(config.per_cluster):
            angles = [
                (mu + gauss(rng, 0.0, config.spread)) % TWO_PI for mu in center
            ]
            ext = [gauss(rng, 0.0, 1.0) for _ in range(space.k)]
            raw = ext + angles
            points.append(space.encode(raw))
            truth.append(c_idx)
            torus_xy.append((angles[0], angles[1] if len(angles) > 1 else 0.0))

    return points, truth, torus_xy
