"""Weighted Mobius-Rickness curvature field ``K_Rick = K * R`` and grid evaluation.

Central theorem (see :mod:`mobius_rickness.core.rickness`): the Mobius strip is a
ruled surface, so ``K(u, v) < 0`` strictly on the interior. Multiplying by the
nowhere-vanishing ``K`` leaves the zero set of ``R`` exactly unchanged:

    K_Rick(u, v) = K(u, v) * R(u, v) = 0   <=>   R(u, v) = 0.

Hence the **Central Finite Curve is exactly ``R^{-1}(0)``** -- a genuine 1-D curve
on the strip separating the "Rick-positive" from the "Rick-negative" universes.
This module provides the sampled field (for downstream visualisation and the
"K_Rick straddles zero" invariant) and the strict-negativity certificate; the
real zero-set tracing lives in :mod:`mobius_rickness.core.tracer`.

Purity: imports only the standard library and sibling ``core`` modules.
"""

from __future__ import annotations

import math
from typing import List, NamedTuple, Tuple

from mobius_rickness.core.mobius import (
    U_MAX,
    U_MIN,
    V_MAX,
    V_MIN,
    gaussian_curvature,
)
from mobius_rickness.core.rickness import rickness


def linspace(a: float, b: float, n: int) -> List[float]:
    """Inclusive evenly spaced samples (stdlib-only, no numpy)."""
    if n <= 1:
        return [a]
    step = (b - a) / (n - 1)
    return [a + i * step for i in range(n)]


def k_rick(u: float, v: float) -> float:
    """Weighted curvature ``K_Rick(u, v) = K(u, v) * R(u, v)``.

    Uses the sign-changing :func:`rickness`, so ``K_Rick`` has a real zero set that
    coincides exactly with ``R^{-1}(0)``.
    """
    return gaussian_curvature(u, v) * rickness(u, v)


class Grid(NamedTuple):
    """Sampled fields over the Mobius ``(u, v)`` domain (rows = v, cols = u)."""

    us: List[float]
    vs: List[float]
    K: List[List[float]]
    R: List[List[float]]
    K_Rick: List[List[float]]


def evaluate_grid(n_u: int = 49, n_v: int = 17) -> Grid:
    """Evaluate ``K``, ``R`` and ``K_Rick`` over the ``(u, v)`` grid.

    Rows are indexed by ``v`` (outer list), columns by ``u`` (inner list).
    """
    us = linspace(U_MIN, U_MAX, n_u)
    vs = linspace(V_MIN, V_MAX, n_v)
    K = [[gaussian_curvature(u, v) for u in us] for v in vs]
    R = [[rickness(u, v) for u in us] for v in vs]
    K_Rick = [
        [K[j][i] * R[j][i] for i in range(len(us))] for j in range(len(vs))
    ]
    return Grid(us=us, vs=vs, K=K, R=R, K_Rick=K_Rick)


def field_range(values: List[List[float]]) -> Tuple[float, float]:
    """Return ``(min, max)`` over a 2D field (flattened)."""
    flat = [val for row in values for val in row]
    if not flat:
        raise ValueError("empty field")
    return min(flat), max(flat)


def assert_mobius_K_negative(
    n_u: int = 60, n_v: int = 15, tol: float = 1e-9
) -> float:
    """Assert ``K < 0`` strictly on the Mobius interior; return the worst (max) K.

    Interior excludes the two boundary edges ``v = +/-0.5``. Raises
    :class:`AssertionError` if any sampled interior ``K`` is not strictly negative.
    """
    us = linspace(U_MIN, U_MAX, n_u)
    vs = linspace(V_MIN, V_MAX, n_v + 2)[1:-1]  # interior v-samples only
    worst = -math.inf
    for u in us:
        for v in vs:
            k = gaussian_curvature(u, v)
            assert k < -tol, f"K not strictly negative at u={u}, v={v}: K={k}"
            if k > worst:
                worst = k
    return worst
