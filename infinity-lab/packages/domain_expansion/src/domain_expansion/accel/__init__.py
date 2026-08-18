"""domain_expansion.accel -- optional numpy fast-paths (lazily guarded).

numpy is NEVER imported at module top level: routines reach it through
:func:`commons.core.optional.try_import` and raise
:class:`~domain_expansion.accel.numpy_backend.OptionalDependencyError` when it is
absent, so importing this package with the standard library alone never fails.
"""

from __future__ import annotations

from domain_expansion.accel.numpy_backend import (
    OptionalDependencyError,
    gaussian_solve_numpy,
    spectral_radius_numpy,
)

__all__ = [
    "OptionalDependencyError",
    "gaussian_solve_numpy",
    "spectral_radius_numpy",
]
