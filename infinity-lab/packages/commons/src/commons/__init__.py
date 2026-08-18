"""commons -- shared internal package for the infinity-lab monorepo.

Public API is re-exported here for convenient one-stop imports::

    from commons import bisection, adaptive_integral, render_heatmap

The layering rule (enforced by convention and tests):
    * :mod:`commons.core` -- pure stdlib building blocks (numerics, exact
      arithmetic, RNG, immutable config, optional-dependency detection).
    * :mod:`commons.adapters` -- text/visualisation adapters over the core.

``core`` modules must import only the standard library and other ``core``
modules; they must never import ``adapters``.
"""

from __future__ import annotations

from commons.adapters import (
    render_convergence,
    render_heatmap,
    render_line_plot,
    render_sign_map,
)
from commons.core import (
    DeterministicRNG,
    FrozenConfig,
    adaptive_integral,
    bisection,
    central_difference,
    complex_step_derivative,
    find_sign_changes,
    geometric_partial_sum,
    geometric_series_limit,
    half_power,
    has_matplotlib,
    has_numpy,
    immutable_replace,
    make_rng,
    midpoint_integral,
    to_fraction,
    trapezoid_integral,
    try_import,
)

__version__ = "0.1.0"

__all__ = [
    "__version__",
    # config
    "FrozenConfig",
    "immutable_replace",
    # exact
    "to_fraction",
    "half_power",
    "geometric_partial_sum",
    "geometric_series_limit",
    # numerics
    "midpoint_integral",
    "trapezoid_integral",
    "adaptive_integral",
    "central_difference",
    "complex_step_derivative",
    "bisection",
    "find_sign_changes",
    # optional
    "try_import",
    "has_numpy",
    "has_matplotlib",
    # rng
    "DeterministicRNG",
    "make_rng",
    # adapters
    "render_line_plot",
    "render_convergence",
    "render_heatmap",
    "render_sign_map",
]
