"""The sign-changing "Rickness" field whose zero set is the Central Finite Curve.

Concept (Rick & Morty): the Citadel sits on the "Central Finite Curve", the only
arc of infinite realities where a Rick exists. Here a scalar Rickness field
``R(u, v)`` is layered onto the differential-geometric Gaussian curvature of a
Mobius strip.

Because the Mobius strip is ruled, ``K < 0`` strictly on the interior, so for ANY
weighting ``K_Rick = K * R = 0 <=> R = 0``. The sign-changing field

    R(u, v) = cos(u) + 0.4 v cos(u/2) + 0.2 sin(u)

therefore makes the Central Finite Curve EXACTLY the zero set ``R^{-1}(0)``. The
legacy positive weighting :func:`rickness_naive` (with a ``+1.5`` constant) is kept
to document why the earlier design had no genuine zero.

For fixed ``u`` the field is affine in ``v``: ``R = A(u) + B(u) v`` with
``A(u) = cos(u) + 0.2 sin(u)`` and ``B(u) = 0.4 cos(u/2)``, giving an exact
per-column root ``v* = -A/B`` that never depends on grid resolution.

Purity: imports only the standard library.
"""

from __future__ import annotations

import math
from typing import Optional, Tuple

# Mobius v-domain half-width (the strip is v in [-0.5, 0.5]).
V_MIN, V_MAX = -0.5, 0.5


def rickness(u: float, v: float) -> float:
    """Sign-changing Rickness weighting ``R(u, v)``.

    ``R(u, v) = cos(u) + 0.4 v cos(u/2) + 0.2 sin(u)``.

    Satisfies the Mobius seam constraint ``R(0, -v) = R(2*pi, v)`` so its zero set
    is a continuous curve on the band: at ``u = 0`` it is ``1 + 0.4 v``, and at
    ``u = 2*pi`` it is ``1 + 0.4 v cos(pi) = 1 - 0.4 v``, which equals ``R(0, -v)``.
    """
    return math.cos(u) + 0.4 * v * math.cos(u / 2.0) + 0.2 * math.sin(u)


def rickness_naive(u: float, v: float) -> float:
    """Legacy strictly-positive Rickness (kept to show why it had no zero).

    ``R_naive(u, v) = 1.5 + R(u, v)``. The ``+1.5`` constant keeps this positive,
    so ``K_Rick`` never reaches zero -- the "curve" could only be reported as a
    minimal-``|K_Rick|`` locus (a cop-out).
    """
    return 1.5 + rickness(u, v)


def column_coeffs(u: float) -> Tuple[float, float]:
    """Return ``(A, B)`` in the affine-in-v decomposition ``R = A(u) + B(u) v``."""
    a = math.cos(u) + 0.2 * math.sin(u)
    b = 0.4 * math.cos(u / 2.0)
    return a, b


def column_root(u: float, v_min: float = V_MIN, v_max: float = V_MAX) -> Optional[float]:
    """Exact per-column root ``v* = -A/B`` if it lies in ``[v_min, v_max]``.

    Returns ``None`` when ``B(u) = 0`` (no unique root) or the root falls outside
    the strip. Removes any grid-resolution miss risk in the tracer.
    """
    a, b = column_coeffs(u)
    if b == 0.0:
        return None
    v_star = -a / b
    if v_min <= v_star <= v_max:
        return v_star
    return None
