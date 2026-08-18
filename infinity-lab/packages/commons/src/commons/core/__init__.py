"""commons.core -- pure, stdlib-only building blocks.

Modules here import ONLY the standard library (and one another). They never
import adapters (``commons.adapters``) or any optional scientific dependency at
module top level; optional deps are reached exclusively through
:mod:`commons.core.optional`.
"""

from __future__ import annotations

from commons.core.config import FrozenConfig, immutable_replace
from commons.core.exact import (
    geometric_partial_sum,
    geometric_series_limit,
    half_power,
    to_fraction,
)
from commons.core.numerics import (
    adaptive_integral,
    bisection,
    central_difference,
    complex_step_derivative,
    find_sign_changes,
    midpoint_integral,
    trapezoid_integral,
)
from commons.core.optional import has_matplotlib, has_numpy, try_import
from commons.core.rng import DeterministicRNG, make_rng

__all__ = [
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
]
