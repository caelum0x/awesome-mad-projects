"""central_finite_curve -- the Central Finite Curve of the multiverse.

Inspired by the *Rick and Morty* "Central Finite Curve": the region of the
multiverse containing every reality in which a Rick is the smartest being. This
package models that concretely as a thin, near-maximal ridge of a deterministic
Rickness score over a cloud of high-dimensional universes, then walks a
hard-constraint portal gun (MCMC) along it.

The pure math lives under :mod:`central_finite_curve.core` (stdlib +
``commons.core`` only) and its public API is re-exported here. Optional numpy
fast-paths live in :mod:`central_finite_curve.accel`; matplotlib/Pillow rendering
lives in :mod:`central_finite_curve.adapters` -- all lazily guarded.
"""

from __future__ import annotations

from central_finite_curve import core
from central_finite_curve.core import (
    Curve,
    CurveConfig,
    DEFAULT,
    PipelineResult,
    Universe,
    Walk,
    complexity,
    entropy,
    extract,
    generate,
    penalty,
    project_2d,
    project_onto_manifold,
    residuals,
    rickness,
    run,
    top2_axes,
    travel,
)

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "core",
    # config
    "CurveConfig",
    "DEFAULT",
    # rickness
    "complexity",
    "entropy",
    "residuals",
    "penalty",
    "rickness",
    "project_onto_manifold",
    # multiverse / curve / walk
    "Universe",
    "generate",
    "Curve",
    "extract",
    "Walk",
    "travel",
    # projection / pipeline
    "project_2d",
    "top2_axes",
    "PipelineResult",
    "run",
]
