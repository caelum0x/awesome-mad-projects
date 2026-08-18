"""Distances on the compactified latent space.

Key idea: on the compact (circular) factors, distance must respect wrap-around.
On a circle, the separation between two angles is the *shorter* arc, so an angle
of ``0.05`` and one of ``2*pi - 0.05`` are CLOSE, not far apart. A naive Euclidean
metric on the raw angle values gets this wrong (it splits seam-straddling
clusters). Everything here is pure stdlib (``math``).
"""

from __future__ import annotations

import math

from calabi_yau_latent.core.latent import (
    TWO_PI,
    CompactifiedLatentSpace,
    LatentPoint,
)


def circle_delta(a: float, b: float) -> float:
    """Shortest signed angular difference in ``(-pi, pi]``. Respects wrap-around."""
    d = (a - b) % TWO_PI
    if d > math.pi:
        d -= TWO_PI
    return d


def naive_distance(p: LatentPoint, q: LatentPoint) -> float:
    """Euclidean distance treating angles as plain numbers (WRONG topology).

    The "naive" observer: it ignores the periodicity of the compact dimensions
    and compares raw angle values as if they lived on the real line.
    """
    total = 0.0
    for a, b in zip(p.extended, q.extended):
        total += (a - b) ** 2
    for a, b in zip(p.angles, q.angles):
        total += (a - b) ** 2  # raw difference, no wrap-around
    return math.sqrt(total)


def naive_angular_distance(p: LatentPoint, q: LatentPoint) -> float:
    """Angle-only Euclidean distance with NO wrap-around (the naive view).

    Isolates the topology effect: compares raw angle values on the real line, so
    points straddling the ``0 / 2*pi`` seam look artificially far apart.
    """
    total = 0.0
    for a, b in zip(p.angles, q.angles):
        total += (a - b) ** 2
    return math.sqrt(total)


def toroidal_distance(
    space: CompactifiedLatentSpace, p: LatentPoint, q: LatentPoint
) -> float:
    """Topology-aware distance: Euclidean on ``R^k``, geodesic arc on each circle.

    Arc length on circle ``j`` is ``radii[j] * |shortest_angular_delta|``.
    """
    total = 0.0
    for a, b in zip(p.extended, q.extended):
        total += (a - b) ** 2
    for j, (a, b) in enumerate(zip(p.angles, q.angles)):
        arc = space.radii[j] * circle_delta(a, b)
        total += arc ** 2
    return math.sqrt(total)


def toroidal_angular_distance(p: LatentPoint, q: LatentPoint) -> float:
    """Pure angular (radius-independent) torus distance: ``sqrt(sum shortest^2)``.

    Useful when you care about *phase* structure regardless of the small radii.
    """
    total = 0.0
    for a, b in zip(p.angles, q.angles):
        total += circle_delta(a, b) ** 2
    return math.sqrt(total)
