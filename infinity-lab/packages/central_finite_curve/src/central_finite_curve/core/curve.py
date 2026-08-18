"""Extract the Central Finite Curve: the near-maximal Rickness ridge.

The true supremum of Rickness is not known analytically (complexity and entropy
vary over the manifold), so we treat the maximum *observed* score as the practical
peak and keep every universe within an absolute epsilon band of it::

    band_low = max_score - eps_absolute
    curve    = { u : u.score >= band_low }

``eps_absolute`` is a small absolute Rickness tolerance, so the curve is a thin
ridge hugging the peak rather than a fat blob. Members are returned sorted by
descending score, so the best universe is first (a natural start for the walk).

Purity: imports only the standard library and :mod:`commons.core`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from central_finite_curve.core.config import DEFAULT, CurveConfig
from central_finite_curve.core.multiverse import Universe


@dataclass(frozen=True)
class Curve:
    """The extracted near-maximal ridge and the band that defines it."""

    members: List[Universe]
    max_score: float
    band_low: float
    epsilon: float
    total: int

    @property
    def size(self) -> int:
        """Number of universes on the curve."""
        return len(self.members)

    @property
    def fraction(self) -> float:
        """Share of the whole multiverse that lies on the curve."""
        return self.size / self.total if self.total else 0.0


def extract(universes: List[Universe], config: CurveConfig = DEFAULT) -> Curve:
    """Filter the multiverse down to its near-maximal ridge.

    Raises :class:`ValueError` for an empty ``universes`` list (there is no peak to
    band around).
    """
    if not universes:
        raise ValueError("cannot extract a curve from an empty multiverse")
    max_score = max(u.score for u in universes)
    epsilon = config.eps_absolute
    band_low = max_score - epsilon
    members = [u for u in universes if u.score >= band_low]
    # Sort descending so the best universe is first (a natural walk start).
    members.sort(key=lambda u: u.score, reverse=True)
    return Curve(
        members=members,
        max_score=max_score,
        band_low=band_low,
        epsilon=epsilon,
        total=len(universes),
    )
