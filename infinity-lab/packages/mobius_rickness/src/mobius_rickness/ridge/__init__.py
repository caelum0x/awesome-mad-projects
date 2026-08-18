"""mobius_rickness.ridge -- the SCMS / Eberly crest of maximal Rickness.

This is the SECOND, distinct formalization of the Central Finite Curve. The pure
:mod:`mobius_rickness.core.tracer` traces the *zero set* ``R^{-1}(0)`` -- the
boundary wall between Rick-positive and Rick-negative universes. This subpackage
traces the complementary *ridge*: the intrinsic 1-D crest line of maximal Rickness
via Subspace-Constrained Mean Shift (Ozertem-Erdogmus) on the Eberly height-ridge
conditions. Along a genuine crest ``R`` is far from ``0`` -- the ridge is NOT a
level set, so the two curves are genuinely different CFC readings.

numpy is optional and reached exclusively through
:func:`commons.core.optional.try_import`; it is never hard-imported at module top
level, so importing this package needs only the standard library. Calling any
ridge routine without numpy raises a clear :class:`OptionalDependencyError`. This
subpackage lives OUTSIDE ``core`` and is never imported by ``core``.
"""

from __future__ import annotations

from mobius_rickness.ridge.scms import (
    MobiusRidgePoint,
    OptionalDependencyError,
    RidgeConvergence,
    RidgePoint,
    dedupe_ridge,
    identity_wrap,
    mobius_seeds,
    ridge_condition,
    scms_point,
    scms_point_history,
    scms_ridge,
    scms_ridge_history,
    trace_mobius_ridge,
    verify_ridge,
)

__all__ = [
    "OptionalDependencyError",
    "RidgePoint",
    "MobiusRidgePoint",
    "RidgeConvergence",
    "identity_wrap",
    "ridge_condition",
    "scms_point",
    "scms_point_history",
    "scms_ridge",
    "scms_ridge_history",
    "dedupe_ridge",
    "mobius_seeds",
    "trace_mobius_ridge",
    "verify_ridge",
]
