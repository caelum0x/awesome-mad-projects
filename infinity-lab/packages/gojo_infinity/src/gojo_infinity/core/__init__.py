"""gojo_infinity.core -- the pure math core of the four Infinity lenses.

Every module here imports ONLY the standard library and :mod:`commons.core`.
Nothing in this package imports an adapter (cli / viz / io) or hard-imports an
optional scientific dependency -- the core stays deterministic and dependency
free so the essay's exact targets are reproducible offline.

Lenses:
    * :mod:`gojo_infinity.core.zeno`       -- geometric series / Zeno   (FRAGILE)
    * :mod:`gojo_infinity.core.measure`    -- Lebesgue measure          (FRAGILE)
    * :mod:`gojo_infinity.core.riemannian` -- conformal geometry        (FORMIDABLE)
    * :mod:`gojo_infinity.core.topology`   -- World-Cutting Slash        (FALLS)
    * :mod:`gojo_infinity.core.verdicts`   -- the four-lens conclusion table
"""

from __future__ import annotations

from gojo_infinity.core.measure import (
    infimum_over_eps,
    lebesgue_measure_of_Z,
    outer_measure_upper_bound,
    subdivision_point,
    subdivision_set,
    total_cover_length,
)
from gojo_infinity.core.riemannian import (
    CalibrationError,
    CalibrationResult,
    X_GOJO,
    calibrate,
    conformal_factor,
    divergence_by_decade,
    gaussian_kernel,
    geodesic_length,
    geodesic_to_barrier,
    metric_g11,
    per_decade_increment,
)
from gojo_infinity.core.riemannian_manifold import (
    DEFAULT_GOJO,
    ConformalMetric,
    GeodesicResult,
    GeodesicState,
    max_christoffel_difference,
    signed_angle,
)
from gojo_infinity.core.riemannian_manifold_nd import (
    DEFAULT_GOJO_3D,
    ConformalMetricND,
    GeodesicResultND,
    PhaseStateND,
    conformal_acceleration,
    max_christoffel_difference_nd,
    unsigned_angle,
)
from gojo_infinity.core.topology import (
    Continuity,
    ContinuityReport,
    component_count,
    connected_components,
    continuity_at,
    make_severed_factor,
    same_component,
    severed_geodesic_length,
)
from gojo_infinity.core.verdicts import (
    Verdict,
    conclusion_table,
    format_table,
    verdict_labels,
)
from gojo_infinity.core.zeno import (
    EpsilonN,
    epsilon_N,
    geometric_sum,
    partial_sum,
    partial_sum_table,
    residual,
    residual_is_strictly_positive,
    total_arrival_time,
    zeno_series_sum,
)

__all__ = [
    # verdicts
    "Verdict",
    "conclusion_table",
    "verdict_labels",
    "format_table",
    # zeno
    "partial_sum",
    "partial_sum_table",
    "residual",
    "residual_is_strictly_positive",
    "geometric_sum",
    "zeno_series_sum",
    "EpsilonN",
    "epsilon_N",
    "total_arrival_time",
    # measure
    "subdivision_point",
    "subdivision_set",
    "total_cover_length",
    "outer_measure_upper_bound",
    "infimum_over_eps",
    "lebesgue_measure_of_Z",
    # riemannian
    "X_GOJO",
    "gaussian_kernel",
    "conformal_factor",
    "metric_g11",
    "calibrate",
    "CalibrationResult",
    "CalibrationError",
    "geodesic_length",
    "geodesic_to_barrier",
    "divergence_by_decade",
    "per_decade_increment",
    # riemannian manifold (2-D)
    "ConformalMetric",
    "GeodesicState",
    "GeodesicResult",
    "DEFAULT_GOJO",
    "signed_angle",
    "max_christoffel_difference",
    # riemannian manifold (n-D generalisation)
    "ConformalMetricND",
    "PhaseStateND",
    "GeodesicResultND",
    "DEFAULT_GOJO_3D",
    "conformal_acceleration",
    "unsigned_angle",
    "max_christoffel_difference_nd",
    # topology
    "Continuity",
    "ContinuityReport",
    "continuity_at",
    "make_severed_factor",
    "severed_geodesic_length",
    "connected_components",
    "component_count",
    "same_component",
]
