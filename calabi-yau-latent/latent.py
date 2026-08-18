"""Compactified latent space: extended R^k coords x compact T^m (torus) coords.

This is an HONEST TOY, not a real Calabi-Yau manifold. See README.md.

numpy is optional here: this module deliberately uses only the standard
library (math) so the prototype runs anywhere. If numpy is installed you
could vectorize `encode_batch` / `decode_batch`, but we keep pure Python for
zero-dependency runnability.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Sequence

# --- optional numpy note (import-guarded) -----------------------------------
try:  # pragma: no cover - purely informational
    import numpy as _np  # noqa: F401
    HAVE_NUMPY = True
except Exception:  # numpy not required
    HAVE_NUMPY = False

TWO_PI = 2.0 * math.pi


@dataclass(frozen=True)
class LatentPoint:
    """A point in the compactified latent space.

    extended : coordinates in R^k (the "large", non-compact directions).
    angles   : m angles in [0, 2*pi) living on the compact torus T^m.

    We keep this immutable (frozen dataclass): operations return new points,
    never mutate in place.
    """

    extended: tuple  # length k
    angles: tuple    # length m, each in [0, 2*pi)

    def __post_init__(self) -> None:
        # Normalize angles into [0, 2*pi) without mutating the input.
        wrapped = tuple(a % TWO_PI for a in self.angles)
        object.__setattr__(self, "angles", wrapped)


@dataclass(frozen=True)
class CompactifiedLatentSpace:
    """Defines the geometry: k extended dims, m compact circles with small radii.

    radii[j] is the (small) radius of the j-th compact circle. Small radii are
    the analogy for "compactified" extra dimensions: they exist, but a naive
    Euclidean observer that ignores wrap-around barely "sees" them.
    """

    k: int                 # number of extended dimensions
    radii: tuple           # length m; small positive radii of each circle

    @property
    def m(self) -> int:
        return len(self.radii)

    # --- encode: raw feature vector -> LatentPoint --------------------------
    def encode(self, raw: Sequence[float]) -> LatentPoint:
        """Map a raw vector into the latent space.

        The first k entries become extended coordinates. The remaining entries
        are interpreted as phases and wrapped onto the circles (mod 2*pi).
        """
        if len(raw) < self.k:
            raise ValueError(f"raw needs at least k={self.k} entries, got {len(raw)}")
        extended = tuple(float(x) for x in raw[: self.k])
        phase_src = list(raw[self.k :])
        # Pad/truncate phases to exactly m entries (fail-soft, but explicit).
        if len(phase_src) < self.m:
            phase_src = phase_src + [0.0] * (self.m - len(phase_src))
        angles = tuple(float(phase_src[j]) % TWO_PI for j in range(self.m))
        return LatentPoint(extended=extended, angles=angles)

    # --- decode: LatentPoint -> observable embedding ------------------------
    def decode(self, p: LatentPoint) -> tuple:
        """Map a latent point back to an observable Euclidean embedding.

        Each compact angle theta_j is embedded as (r_j*cos, r_j*sin). Because
        the radii are small, the compact structure contributes little Euclidean
        magnitude -- that is exactly why a naive Euclidean view "misses" it.
        """
        emb: List[float] = list(p.extended)
        for j, theta in enumerate(p.angles):
            r = self.radii[j]
            emb.append(r * math.cos(theta))
            emb.append(r * math.sin(theta))
        return tuple(emb)

    # Round-trip sanity: encode(decode-ish) preserves angles up to 2*pi.
    def roundtrip_angles_ok(self, p: LatentPoint, tol: float = 1e-9) -> bool:
        emb = self.decode(p)
        base = self.k
        for j, theta in enumerate(p.angles):
            r = self.radii[j]
            cx, cy = emb[base + 2 * j], emb[base + 2 * j + 1]
            rec = math.atan2(cy, cx) % TWO_PI
            if abs((rec - theta + math.pi) % TWO_PI - math.pi) > tol + 1e-6:
                return False
        return True
