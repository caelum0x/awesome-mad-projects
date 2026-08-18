"""Immutable configuration for the Central Finite Curve engine.

Every tunable constant lives on a single frozen :class:`CurveConfig` so a run is
fully described by ``(config, seed)``. Nothing here mutates at runtime; functions
thread an explicit config (defaulting to :data:`DEFAULT`) instead of reading a
global, which keeps generation, filtering and the walk reproducible and testable.

Purity: imports only the standard library.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CurveConfig:
    """All tunable constants for one reproducible Central-Finite-Curve run.

    Fields mirror the physics of the model:

    * ``dim`` / ``n_universes`` / ``seed`` -- size and reproducibility.
    * ``near_manifold_fraction`` -- share of universes seeded *near* the genius
      manifold (the rare "Rick-ish" ones); the rest are uniform-box junk.
    * ``box`` / ``ring_radius`` -- geometry of the sampling box and the ring
      constraint radius.
    * ``w_complexity`` / ``w_entropy`` / ``w_penalty`` -- Rickness score weights.
    * ``eps_absolute`` -- half-width of the near-maximal Rickness band (the curve
      thickness).
    * ``walk_steps`` / ``proposal_sigma`` -- portal-gun (MCMC) length and step.
    * ``jitter_sigma`` -- Gaussian jitter applied to near-manifold seeds.
    * ``grid_w`` / ``grid_h`` -- ASCII render size.

    Validation happens in :meth:`__post_init__`; construction fails fast with a
    :class:`ValueError` on any nonsensical value.
    """

    dim: int = 8
    n_universes: int = 20000
    near_manifold_fraction: float = 0.18
    box: float = 3.0
    ring_radius: float = 2.0
    w_complexity: float = 1.0
    w_entropy: float = 1.0
    w_penalty: float = 6.0
    eps_absolute: float = 0.20
    walk_steps: int = 6000
    proposal_sigma: float = 0.045
    jitter_sigma: float = 0.02
    seed: int = 137
    grid_w: int = 70
    grid_h: int = 26

    def __post_init__(self) -> None:
        if self.dim < 2:
            raise ValueError("dim must be >= 2 (entropy needs at least two axes)")
        if self.dim < 8:
            # The four algebraic constraints reference dims 0..6 (dim 7 free).
            raise ValueError("dim must be >= 8 to host the four ridge constraints")
        if self.n_universes < 1:
            raise ValueError("n_universes must be >= 1")
        if not (0.0 <= self.near_manifold_fraction <= 1.0):
            raise ValueError("near_manifold_fraction must lie in [0, 1]")
        if self.box <= 0.0:
            raise ValueError("box must be positive")
        if self.ring_radius <= 0.0:
            raise ValueError("ring_radius must be positive")
        if self.eps_absolute <= 0.0:
            raise ValueError("eps_absolute must be positive")
        if self.walk_steps < 0:
            raise ValueError("walk_steps must be >= 0")
        if self.proposal_sigma <= 0.0:
            raise ValueError("proposal_sigma must be positive")
        if self.jitter_sigma < 0.0:
            raise ValueError("jitter_sigma must be >= 0")
        if self.grid_w < 1 or self.grid_h < 1:
            raise ValueError("grid_w and grid_h must be >= 1")


# The canonical run described in the README (D=8, N=20000, seed=137).
DEFAULT = CurveConfig()
