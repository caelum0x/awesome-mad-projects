"""Generate the multiverse: many universes as points in ``R^dim``.

The population is a deterministic mixture:

  * a small ``near_manifold_fraction`` drawn close to the genius manifold (the rare
    universes that could ever be "Rick"), and
  * the rest drawn uniformly from the box ``[-box, box]^dim`` (mostly low-Rickness
    junk).

This mirrors the premise: infinitely many universes exist, but only a thin ridge
of them are near-maximally Rick. Every draw flows through the seeded ``rng`` so the
whole multiverse is reproducible.

Purity: imports only the standard library and :mod:`commons.core`.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Tuple

from commons.core.rng import DeterministicRNG

import central_finite_curve.core.rickness as rickness_mod
from central_finite_curve.core.config import DEFAULT, CurveConfig
from central_finite_curve.core.sampling import uniform_vector


@dataclass(frozen=True)
class Universe:
    """One universe: immutable coordinates plus its cached Rickness score."""

    coords: Tuple[float, ...]
    score: float


def _near_manifold_point(rng: DeterministicRNG, config: CurveConfig) -> List[float]:
    """Sample four free manifold parameters and solve onto the ridge."""
    free = (
        rng.uniform(-math.pi, math.pi),          # t : angle on the ring
        rng.uniform(-2.0, 2.0),                   # a : mirror-pair magnitude
        rng.uniform(-2.0, 2.0),                   # b : reciprocal-pair seed
        rng.uniform(-config.box, config.box),     # c : the free dim 7
    )
    return rickness_mod.project_onto_manifold(free, rng, config)


def generate(
    rng: DeterministicRNG, config: CurveConfig = DEFAULT
) -> List[Universe]:
    """Build the full multiverse deterministically from the given ``rng``.

    The first ``round(n_universes * near_manifold_fraction)`` universes are seeded
    near the manifold; the remainder are uniform-box junk. Returns a new list of
    frozen :class:`Universe` records (nothing is mutated in place).
    """
    universes: List[Universe] = []
    n_near = int(config.n_universes * config.near_manifold_fraction)
    for i in range(config.n_universes):
        if i < n_near:
            coords = _near_manifold_point(rng, config)
        else:
            coords = uniform_vector(rng, config.dim, config.box)
        score = rickness_mod.rickness(coords, config)
        universes.append(Universe(coords=tuple(coords), score=score))
    return universes
