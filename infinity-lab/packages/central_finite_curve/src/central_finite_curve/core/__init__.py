"""central_finite_curve.core -- the pure engine (stdlib + commons.core only).

Every module here imports ONLY the standard library and :mod:`commons.core`;
nothing imports an adapter (cli / render / viz) or hard-imports numpy/matplotlib,
so the core stays deterministic and dependency free. The public API is re-exported
for convenient one-stop imports.

Pipeline:
    * :mod:`~central_finite_curve.core.multiverse`  -- seed N high-dim universes.
    * :mod:`~central_finite_curve.core.rickness`    -- the Rickness score + ridge.
    * :mod:`~central_finite_curve.core.curve`       -- the near-maximal epsilon band.
    * :mod:`~central_finite_curve.core.portal_gun`  -- the constrained MCMC walk.
    * :mod:`~central_finite_curve.core.projection`  -- power-iteration PCA to 2-D.
    * :mod:`~central_finite_curve.core.pipeline`    -- the end-to-end orchestrator.
"""

from __future__ import annotations

from central_finite_curve.core.config import DEFAULT, CurveConfig
from central_finite_curve.core.curve import Curve, extract
from central_finite_curve.core.multiverse import Universe, generate
from central_finite_curve.core.pipeline import PipelineResult, run
from central_finite_curve.core.portal_gun import Walk, travel
from central_finite_curve.core.projection import project_2d, top2_axes
from central_finite_curve.core.rickness import (
    complexity,
    entropy,
    penalty,
    project_onto_manifold,
    residuals,
    rickness,
)
from central_finite_curve.core.sampling import (
    child_rng,
    child_seed,
    gauss,
    gauss_vector,
    uniform_vector,
)

__all__ = [
    # config
    "CurveConfig",
    "DEFAULT",
    # sampling
    "child_seed",
    "child_rng",
    "gauss",
    "gauss_vector",
    "uniform_vector",
    # rickness
    "complexity",
    "entropy",
    "residuals",
    "penalty",
    "rickness",
    "project_onto_manifold",
    # multiverse
    "Universe",
    "generate",
    # curve
    "Curve",
    "extract",
    # portal gun
    "Walk",
    "travel",
    # projection
    "project_2d",
    "top2_axes",
    # pipeline
    "PipelineResult",
    "run",
]
