"""mobius_rickness.accel -- optional numpy fast-paths (never imported by core).

The pure :mod:`mobius_rickness.core` computes every quantity point-by-point with
the standard library alone. This package provides *vectorised* numpy fast-paths
that evaluate the same quantities over a whole ``(u, v)`` mesh at once and agree
with the pure core to floating-point parity.

numpy is optional and is reached exclusively through
:func:`commons.core.optional.try_import` -- it is never hard-imported at module
top level, so importing this package needs only the standard library. Calling any
fast-path without numpy installed raises a clear :class:`OptionalDependencyError`.
"""

from __future__ import annotations

from mobius_rickness.accel.numpy_backend import (
    OptionalDependencyError,
    curvature_analytic_mesh,
    curvature_fd_mesh,
    k_rick_mesh,
    mobius_surface_mesh,
    rickness_mesh,
)

__all__ = [
    "OptionalDependencyError",
    "curvature_fd_mesh",
    "curvature_analytic_mesh",
    "rickness_mesh",
    "k_rick_mesh",
    "mobius_surface_mesh",
]
