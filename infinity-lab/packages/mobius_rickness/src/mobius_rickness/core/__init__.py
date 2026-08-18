"""mobius_rickness.core -- pure differential-geometry core (stdlib + commons.core).

Every module here imports ONLY the standard library and :mod:`commons.core`; none
of them import adapters or hard-import numpy/matplotlib. The public API is
re-exported for convenient one-stop imports.
"""

from __future__ import annotations

from mobius_rickness.core.field import (
    Grid,
    assert_mobius_K_negative,
    evaluate_grid,
    field_range,
    k_rick,
    linspace,
)
from mobius_rickness.core.geometry import (
    fundamental_forms_cs,
    fundamental_forms_fd,
    gaussian_curvature_cs,
    gaussian_curvature_fd,
    identity_wrap,
    mobius_curvature_analytic,
    mobius_E,
    mobius_seam_wrap,
)
from mobius_rickness.core.mobius import (
    U_MAX,
    U_MIN,
    V_MAX,
    V_MIN,
    assert_curvature_negative,
    fundamental_forms,
    gaussian_curvature,
    gaussian_curvature_complex_step,
    gaussian_curvature_numeric,
    seam_identity_error,
    surface,
    surface_complex,
)
from mobius_rickness.core.rickness import (
    column_coeffs,
    column_root,
    rickness,
    rickness_naive,
)
from mobius_rickness.core.torus import (
    R0_DEFAULT,
    R_MINOR_DEFAULT,
    gaussian_curvature_closed,
    require_ring,
    sign_pattern,
    zero_circles,
)
from mobius_rickness.core.tracer import (
    ColumnResult,
    CurvePoint,
    Segment,
    find_roots_in_v,
    flatten_columns,
    lift,
    march_mobius_curve,
    march_zero_segments,
    segment_points,
    stitch_segments,
    trace_columns,
    trace_torus_zero_circles,
    verify_curve,
)

__all__ = [
    # geometry
    "mobius_E",
    "mobius_curvature_analytic",
    "mobius_seam_wrap",
    "identity_wrap",
    "gaussian_curvature_fd",
    "gaussian_curvature_cs",
    "fundamental_forms_fd",
    "fundamental_forms_cs",
    # mobius
    "surface",
    "surface_complex",
    "gaussian_curvature",
    "gaussian_curvature_numeric",
    "gaussian_curvature_complex_step",
    "fundamental_forms",
    "seam_identity_error",
    "assert_curvature_negative",
    "U_MIN",
    "U_MAX",
    "V_MIN",
    "V_MAX",
    # torus
    "gaussian_curvature_closed",
    "sign_pattern",
    "zero_circles",
    "require_ring",
    "R0_DEFAULT",
    "R_MINOR_DEFAULT",
    # rickness
    "rickness",
    "rickness_naive",
    "column_coeffs",
    "column_root",
    # field
    "k_rick",
    "Grid",
    "evaluate_grid",
    "field_range",
    "assert_mobius_K_negative",
    "linspace",
    # tracer
    "CurvePoint",
    "ColumnResult",
    "Segment",
    "lift",
    "find_roots_in_v",
    "trace_columns",
    "flatten_columns",
    "march_zero_segments",
    "stitch_segments",
    "segment_points",
    "march_mobius_curve",
    "verify_curve",
    "trace_torus_zero_circles",
]
