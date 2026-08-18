"""The Portal Gun: a hard-constraint Metropolis walk along the curve.

Starting from a universe on the ridge, we repeatedly propose a Gaussian step. A
proposal is ACCEPTED only if the new universe stays inside the Rickness band
(``score >= band_low``); otherwise we stay put. The result is a trajectory that
slides ALONG the Central Finite Curve without ever falling off it -- exactly the
"travel between Rick universes" fantasy.

This is a hard-constraint Metropolis walk: the acceptance rule is the indicator of
the band region, so the walk explores the ridge (near-)uniformly rather than
climbing to a single point. The acceptance ratio is tracked as the fraction of
proposed steps that were accepted.

Purity: imports only the standard library and :mod:`commons.core`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

from commons.core.rng import DeterministicRNG

import central_finite_curve.core.rickness as rickness_mod
from central_finite_curve.core.config import DEFAULT, CurveConfig
from central_finite_curve.core.curve import Curve
from central_finite_curve.core.sampling import gauss_vector

Point = Tuple[float, ...]


@dataclass(frozen=True)
class Walk:
    """A portal-gun trajectory: accepted states, their scores, and the accept ratio."""

    points: List[Point]
    scores: List[float]
    acceptance_rate: float
    steps: int


def travel(curve: Curve, rng: DeterministicRNG, config: CurveConfig = DEFAULT) -> Walk:
    """Walk along the ridge starting from its best-known universe.

    Every recorded state has ``score >= curve.band_low`` (the hard constraint): the
    start is the peak, accepted moves keep the score in the band, and a rejected
    move leaves the walker on its previous in-band state. Returns an empty walk when
    the curve has no members.
    """
    if not curve.members:
        return Walk(points=[], scores=[], acceptance_rate=0.0, steps=0)

    current = list(curve.members[0].coords)
    current_score = curve.members[0].score
    points: List[Point] = [tuple(current)]
    scores: List[float] = [current_score]
    accepted = 0

    for _ in range(config.walk_steps):
        step = gauss_vector(rng, config.dim, config.proposal_sigma)
        proposal = [c + s for c, s in zip(current, step)]
        prop_score = rickness_mod.rickness(proposal, config)
        # Hard-constraint acceptance: stay strictly inside the band.
        if prop_score >= curve.band_low:
            current = proposal
            current_score = prop_score
            accepted += 1
        points.append(tuple(current))
        scores.append(current_score)

    rate = accepted / config.walk_steps if config.walk_steps else 0.0
    return Walk(
        points=points, scores=scores, acceptance_rate=rate, steps=config.walk_steps
    )
