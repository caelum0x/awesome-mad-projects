"""gojo_infinity.accel -- OPTIONAL numpy fast-paths (never imported by core).

This subpackage holds vectorised numpy mirrors of the pure float-valued core.
It is NOT part of the pure core: every function reaches numpy lazily through
:func:`commons.core.optional.try_import` and raises
:class:`~gojo_infinity.accel.numpy_backend.OptionalDependencyError` when numpy
is unavailable. ``core`` never imports this package, so core purity is preserved.
"""

from __future__ import annotations

from gojo_infinity.accel.manifold_backend import (
    BatchGeodesicResult,
    integrate_geodesics_batch,
)
from gojo_infinity.accel.numpy_backend import (
    OptionalDependencyError,
    cover_interval_lengths,
    felt_ds_values,
    geodesic_partial_length,
    geodesic_partial_length_midpoint,
    metric_g11_values,
    omega_values,
    zeno_partial_sums,
    zeno_residuals,
)

__all__ = [
    "OptionalDependencyError",
    "omega_values",
    "metric_g11_values",
    "felt_ds_values",
    "geodesic_partial_length",
    "geodesic_partial_length_midpoint",
    "cover_interval_lengths",
    "zeno_partial_sums",
    "zeno_residuals",
    "integrate_geodesics_batch",
    "BatchGeodesicResult",
]
