"""Holonomy-flavored demo: parallel transport of a vector around a compact loop.

ANALOGY DISCLAIMER: Calabi-Yau manifolds are special precisely because they
have restricted ("special") holonomy (SU(n)), which is what preserves
supersymmetry in string compactifications. That is deep Riemannian geometry.

Here we do something MUCH simpler and purely illustrative: transport a 2D
vector around a closed loop on our toy torus under a chosen connection, and
measure the net rotation (the "holonomy angle") it picks up. On a flat torus
with the trivial connection the holonomy is zero; we add a small position
-dependent rotation rate so a loop accumulates a nonzero, measurable angle --
just to make the concept tangible. This is a teaching cartoon, not CY geometry.
"""
from __future__ import annotations

import math
from typing import List, Tuple

TWO_PI = 2.0 * math.pi


def _rotate(v: Tuple[float, float], angle: float) -> Tuple[float, float]:
    c, s = math.cos(angle), math.sin(angle)
    x, y = v
    return (c * x - s * y, s * x + c * y)


def transport_around_loop(
    v0: Tuple[float, float],
    curvature: float = 0.15,
    steps: int = 720,
) -> Tuple[Tuple[float, float], float]:
    """Parallel-transport v0 once around a compact loop (theta: 0 -> 2*pi).

    We model a toy connection whose rotation rate is `curvature` per radian of
    loop travel, so one full loop rotates the vector by curvature * 2*pi.
    Returns (final_vector, net_holonomy_angle).

    Immutable style: we rebuild the vector each step, never mutate in place.
    """
    v = v0
    dtheta = TWO_PI / steps
    accumulated = 0.0
    for _ in range(steps):
        rot = curvature * dtheta
        v = _rotate(v, rot)
        accumulated += rot
    return v, accumulated % TWO_PI


def holonomy_angle(curvature: float = 0.15) -> float:
    """Closed-form net rotation after one loop: (curvature * 2*pi) mod 2*pi."""
    return (curvature * TWO_PI) % TWO_PI


def loop_trace(
    v0: Tuple[float, float],
    curvature: float = 0.15,
    samples: int = 8,
) -> List[Tuple[float, Tuple[float, float]]]:
    """Sample the transported vector at a few points around the loop.

    Returns list of (theta, vector) for visualization/inspection.
    """
    out: List[Tuple[float, Tuple[float, float]]] = []
    v = v0
    step_theta = TWO_PI / samples
    theta = 0.0
    for _ in range(samples):
        out.append((theta, v))
        v = _rotate(v, curvature * step_theta)
        theta += step_theta
    return out
