"""calabi_yau_latent.accel -- optional numpy fast-paths (lazily guarded).

numpy is NEVER imported at module top level: routines reach it through
:func:`commons.core.optional.try_import` and raise
:class:`~calabi_yau_latent.accel.numpy_backend.OptionalDependencyError` when it is
absent, so importing this package with the standard library alone never fails.
"""

from __future__ import annotations

from calabi_yau_latent.accel.numpy_backend import (
    OptionalDependencyError,
    naive_angular_distance_matrix,
    toroidal_angular_distance_matrix,
    toroidal_distance_matrix,
)

__all__ = [
    "OptionalDependencyError",
    "naive_angular_distance_matrix",
    "toroidal_angular_distance_matrix",
    "toroidal_distance_matrix",
]
