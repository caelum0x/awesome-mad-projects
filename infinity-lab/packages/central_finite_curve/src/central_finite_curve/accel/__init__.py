"""central_finite_curve.accel -- optional numpy fast-paths (lazily guarded).

numpy is NEVER imported at module top level: routines reach it through
:func:`commons.core.optional.try_import` and raise
:class:`~central_finite_curve.accel.numpy_backend.OptionalDependencyError` when it
is absent, so importing this package with the standard library alone never fails.
"""

from __future__ import annotations

from central_finite_curve.accel.numpy_backend import (
    OptionalDependencyError,
    complexity_values,
    entropy_values,
    penalty_values,
    project_2d_numpy,
    rickness_values,
)

__all__ = [
    "OptionalDependencyError",
    "complexity_values",
    "entropy_values",
    "penalty_values",
    "rickness_values",
    "project_2d_numpy",
]
