"""Compactified latent space: extended R^k coords x compact T^m (torus) coords.

This is an HONEST TOY, not a real Calabi-Yau manifold. A real Calabi-Yau space
is a compact Kaehler manifold with vanishing first Chern class and a Ricci-flat
metric of special SU(n) holonomy; nothing here reproduces that. What we build is
a flat product space ``R^k x T^m`` -- a few ordinary "extended" real dimensions
times a product of small circles. See the package README for the full caveat.

Purity: this module uses only the standard library (``math``). Optional numpy
vectorisation of ``encode`` / ``decode`` over batches lives in
:mod:`calabi_yau_latent.accel`; it is never imported here.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Sequence, Tuple

TWO_PI = 2.0 * math.pi


@dataclass(frozen=True)
class LatentPoint:
    """A point in the compactified latent space.

    ``extended`` are coordinates in ``R^k`` (the large, non-compact directions).
    ``angles`` are ``m`` angles in ``[0, 2*pi)`` living on the compact torus
    ``T^m``.

    Immutable (frozen dataclass): operations return new points, never mutate in
    place. Angles are normalised into ``[0, 2*pi)`` at construction without
    mutating the caller's input.
    """

    extended: Tuple[float, ...]  # length k
    angles: Tuple[float, ...]    # length m, each in [0, 2*pi)

    def __post_init__(self) -> None:
        wrapped = tuple(a % TWO_PI for a in self.angles)
        object.__setattr__(self, "angles", wrapped)


@dataclass(frozen=True)
class CompactifiedLatentSpace:
    """Geometry: ``k`` extended dims and ``m`` compact circles with small radii.

    ``radii[j]`` is the (small) radius of the j-th compact circle. Small radii are
    the analogy for "compactified" extra dimensions: they exist, but a naive
    Euclidean observer that ignores wrap-around barely "sees" them.
    """

    k: int                        # number of extended dimensions
    radii: Tuple[float, ...]      # length m; small positive radii of each circle

    def __post_init__(self) -> None:
        if self.k < 0:
            raise ValueError("k (extended dimensions) must be >= 0")
        if len(self.radii) < 1:
            raise ValueError("radii must describe at least one compact circle")
        if any(r <= 0.0 for r in self.radii):
            raise ValueError("every compact radius must be positive")

    @property
    def m(self) -> int:
        """Number of compact circles (the torus dimension ``T^m``)."""
        return len(self.radii)

    def encode(self, raw: Sequence[float]) -> LatentPoint:
        """Map a raw feature vector into the latent space.

        The first ``k`` entries become extended coordinates. The remaining entries
        are interpreted as phases and wrapped onto the circles (mod ``2*pi``).
        Missing phases are padded with ``0.0`` (fail-soft but explicit); a raw
        vector shorter than ``k`` raises :class:`ValueError`.
        """
        if len(raw) < self.k:
            raise ValueError(
                f"raw needs at least k={self.k} entries, got {len(raw)}"
            )
        extended = tuple(float(x) for x in raw[: self.k])
        phase_src = [float(x) for x in raw[self.k:]]
        if len(phase_src) < self.m:
            phase_src = phase_src + [0.0] * (self.m - len(phase_src))
        angles = tuple(phase_src[j] % TWO_PI for j in range(self.m))
        return LatentPoint(extended=extended, angles=angles)

    def decode(self, p: LatentPoint) -> Tuple[float, ...]:
        """Map a latent point to an observable Euclidean embedding.

        Each compact angle ``theta_j`` is embedded as ``(r_j*cos, r_j*sin)``.
        Because the radii are small, the compact structure contributes little
        Euclidean magnitude -- exactly why a naive Euclidean view "misses" it.
        The embedding has length ``k + 2*m``.
        """
        emb: List[float] = list(p.extended)
        for j, theta in enumerate(p.angles):
            r = self.radii[j]
            emb.append(r * math.cos(theta))
            emb.append(r * math.sin(theta))
        return tuple(emb)

    def roundtrip_angles_ok(self, p: LatentPoint, tol: float = 1e-9) -> bool:
        """Return ``True`` iff decoding then re-reading each angle recovers it.

        Reconstructs ``theta_j`` from the embedded ``(r*cos, r*sin)`` via
        ``atan2`` and checks it matches modulo ``2*pi``.
        """
        emb = self.decode(p)
        base = self.k
        for j, theta in enumerate(p.angles):
            cx, cy = emb[base + 2 * j], emb[base + 2 * j + 1]
            rec = math.atan2(cy, cx) % TWO_PI
            if abs((rec - theta + math.pi) % TWO_PI - math.pi) > tol + 1e-6:
                return False
        return True
