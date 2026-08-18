"""Immutable configuration for the compactified-latent-space TOY.

Every tunable constant lives on a single frozen :class:`CYConfig`, so a run is
fully described by that config. Nothing here mutates at runtime; functions thread
an explicit config (defaulting to :data:`DEFAULT`) instead of reading a global,
which keeps data generation, clustering and the holonomy cartoon reproducible.

Honesty: this configures a flat ``R^k x T^m`` product space, NOT a Ricci-flat
Calabi-Yau manifold. See the package README for the full caveat.

Purity: imports only the standard library.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Tuple

from commons.core.config import FrozenConfig

# Ground-truth phase centres on the 2-torus. Two of them sit on a 0 / 2*pi seam
# (a coordinate is 0 or pi) so their members straddle the wrap-around edge -- the
# whole point of the demonstration.
_DEFAULT_CENTERS: Tuple[Tuple[float, float], ...] = (
    (0.0, math.pi),      # cluster 0: straddles the theta1 seam
    (math.pi, 0.0),      # cluster 1: straddles the theta2 seam
    (math.pi, math.pi),  # cluster 2: interior, no seam
)


@dataclass(frozen=True)
class CYConfig(FrozenConfig):
    """All tunable constants for one reproducible compactified-latent-space run.

    Extends :class:`commons.core.config.FrozenConfig`, so an updated copy is made
    with :meth:`~commons.core.config.FrozenConfig.with_changes` (the original is
    never mutated).

    Fields:

    * ``k`` -- number of extended (large, non-compact) ``R^k`` dimensions.
    * ``radii`` -- small positive radii of the ``m`` compact circles (``T^m``).
    * ``centers`` -- ground-truth phase centres on the torus, one per cluster.
    * ``per_cluster`` / ``spread`` -- points per cluster and angular jitter.
    * ``seed`` -- reproducibility seed for the deterministic RNG.
    * ``cluster_threshold`` -- connected-components distance threshold.
    * ``curvature`` -- toy holonomy connection rate (analogy only).
    * ``grid_w`` / ``grid_h`` -- ASCII torus render size.

    Validation happens in :meth:`__post_init__`; construction fails fast with a
    :class:`ValueError` on any nonsensical value.
    """

    k: int = 2
    radii: Tuple[float, ...] = (0.10, 0.10)
    centers: Tuple[Tuple[float, float], ...] = field(default=_DEFAULT_CENTERS)
    per_cluster: int = 12
    spread: float = 0.30
    seed: int = 7
    cluster_threshold: float = 0.9
    curvature: float = 0.15
    grid_w: int = 48
    grid_h: int = 18

    def __post_init__(self) -> None:
        if self.k < 0:
            raise ValueError("k (extended dimensions) must be >= 0")
        if len(self.radii) < 1:
            raise ValueError("radii must describe at least one compact circle")
        if any(r <= 0.0 for r in self.radii):
            raise ValueError("every compact radius must be positive")
        if len(self.centers) < 1:
            raise ValueError("centers must contain at least one cluster centre")
        if any(len(c) != len(self.radii) for c in self.centers):
            raise ValueError("each centre must have one angle per compact circle")
        if self.per_cluster < 1:
            raise ValueError("per_cluster must be >= 1")
        if self.spread < 0.0:
            raise ValueError("spread must be >= 0")
        if self.cluster_threshold <= 0.0:
            raise ValueError("cluster_threshold must be positive")
        if self.grid_w < 1 or self.grid_h < 1:
            raise ValueError("grid_w and grid_h must be >= 1")

    @property
    def m(self) -> int:
        """Number of compact circles (the torus dimension ``T^m``)."""
        return len(self.radii)


# The canonical run described in the README (k=2, T^2, seed=7, 3 clusters).
DEFAULT = CYConfig()
