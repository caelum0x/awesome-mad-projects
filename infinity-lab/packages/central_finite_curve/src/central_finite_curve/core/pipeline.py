"""End-to-end orchestration: multiverse -> curve -> walk -> 2-D projection.

A single :func:`run` ties the pure core together so the CLI, the demo, the viz PNG
and the walk animation all share exactly one source of truth. Two independent
seeded streams are derived from ``config.seed`` -- one for generation, one for the
walk -- via :func:`central_finite_curve.core.sampling.child_rng`, so the run is
fully reproducible from ``(config, seed)`` alone.

Purity: imports only the standard library and :mod:`commons.core`.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

from central_finite_curve.core import curve as curve_mod
from central_finite_curve.core import multiverse as multiverse_mod
from central_finite_curve.core import portal_gun as portal_gun_mod
from central_finite_curve.core import projection as projection_mod
from central_finite_curve.core.config import DEFAULT, CurveConfig
from central_finite_curve.core.curve import Curve
from central_finite_curve.core.portal_gun import Walk
from central_finite_curve.core.sampling import child_rng

# Stream tags: distinct so generation and the walk never share a sequence.
_GEN_TAG = 1
_WALK_TAG = 2

Point2D = Tuple[float, float]


@dataclass(frozen=True)
class PipelineResult:
    """Everything one reproducible run produces (immutable)."""

    config: CurveConfig
    curve: Curve
    walk: Walk
    proj_curve: List[Point2D]
    proj_walk: List[Point2D]


def run(config: CurveConfig = DEFAULT, *, project: bool = True) -> PipelineResult:
    """Run the full pipeline for ``config`` and return an immutable result.

    ``project=False`` skips the (relatively expensive) 2-D PCA projection when only
    the curve/walk statistics are needed. When projecting, the top-2 principal axes
    are fit on the *combined* curve+walk cloud and applied to both, so they share a
    single frame.
    """
    gen_rng = child_rng(config.seed, _GEN_TAG)
    walk_rng = child_rng(config.seed, _WALK_TAG)

    universes = multiverse_mod.generate(gen_rng, config)
    the_curve = curve_mod.extract(universes, config)
    the_walk = portal_gun_mod.travel(the_curve, walk_rng, config)

    proj_curve: List[Point2D] = []
    proj_walk: List[Point2D] = []
    if project and the_curve.members:
        curve_coords = [list(u.coords) for u in the_curve.members]
        walk_coords = [list(p) for p in the_walk.points]
        combined = curve_coords + walk_coords
        proj_all = projection_mod.project_2d(combined)
        n_curve = len(curve_coords)
        proj_curve = proj_all[:n_curve]
        proj_walk = proj_all[n_curve:]

    return PipelineResult(
        config=config,
        curve=the_curve,
        walk=the_walk,
        proj_curve=proj_curve,
        proj_walk=proj_walk,
    )
