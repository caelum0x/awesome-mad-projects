"""mobius_rickness -- Mobius/torus differential geometry + the Central Finite Curve.

Built on :mod:`commons`, this package computes the Gaussian curvature of the
Mobius strip (three cross-validating paths: analytic oracle, central-difference
finite differences, complex-step) and the torus, layers the sign-changing
"Rickness" field ``R`` onto the curvature, and traces the Central Finite Curve as
the honest zero set ``R^{-1}(0)`` (scan-line bisection + seam-aware marching
squares).

The pure math lives in :mod:`mobius_rickness.core` (stdlib + ``commons.core``
only). Its public API is re-exported here for convenience.
"""

from __future__ import annotations

from mobius_rickness import core
from mobius_rickness.core import (
    ColumnResult,
    CurvePoint,
    Grid,
    Segment,
    assert_curvature_negative,
    assert_mobius_K_negative,
    column_root,
    evaluate_grid,
    gaussian_curvature,
    gaussian_curvature_closed,
    gaussian_curvature_complex_step,
    gaussian_curvature_numeric,
    k_rick,
    march_mobius_curve,
    mobius_curvature_analytic,
    rickness,
    rickness_naive,
    sign_pattern,
    surface,
    trace_columns,
    trace_torus_zero_circles,
    verify_curve,
    zero_circles,
)

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "core",
    # curvature
    "surface",
    "gaussian_curvature",
    "gaussian_curvature_numeric",
    "gaussian_curvature_complex_step",
    "mobius_curvature_analytic",
    "assert_curvature_negative",
    # torus
    "gaussian_curvature_closed",
    "sign_pattern",
    "zero_circles",
    # rickness / field
    "rickness",
    "rickness_naive",
    "column_root",
    "k_rick",
    "Grid",
    "evaluate_grid",
    "assert_mobius_K_negative",
    # tracer
    "CurvePoint",
    "ColumnResult",
    "Segment",
    "trace_columns",
    "march_mobius_curve",
    "trace_torus_zero_circles",
    "verify_curve",
]
