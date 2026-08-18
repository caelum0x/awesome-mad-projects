"""Immutable configuration for the Madoka entropy simulation.

Every tunable constant lives on a single frozen :class:`SimConfig` so a run is
fully described by ``(config, seed)``. Nothing here mutates at runtime; the
simulation threads an explicit config (defaulting to :data:`DEFAULT`) instead of
reading a global, which keeps the wish/witch dynamics reproducible and testable.

Validation happens in :meth:`__post_init__`; construction fails fast with a
:class:`ValueError` on any nonsensical value.

Purity: imports only the standard library.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class SimConfig:
    """All tunable parameters for one reproducible run (immutable)."""

    seed: int = 42
    steps: int = 120
    girl_names: Tuple[str, ...] = ("Madoka", "Homura", "Sayaka", "Mami", "Kyoko")
    base_local_entropy: float = 20.0     # starting subsystem entropy per girl
    base_global_entropy: float = 100.0   # starting reservoir entropy

    wish_probability: float = 0.55       # chance a living girl casts per step
    local_order_min: float = 0.4         # min order imposed per cast
    local_order_max: float = 1.6         # max order imposed per cast
    karmic_multiplier: float = 1.8       # global cost factor (> 1 => 2nd law)

    decay_per_order: float = 0.06        # purity lost per unit of order imposed
    witch_threshold: float = 0.15        # purity at/below which she turns
    witch_burst_base: float = 12.0       # base entropy dumped on transformation
    witch_burst_per_order: float = 1.5   # extra burst per unit of order she cast

    def __post_init__(self) -> None:
        if self.steps < 0:
            raise ValueError("steps must be >= 0")
        if len(self.girl_names) < 1:
            raise ValueError("girl_names must contain at least one girl")
        if self.base_local_entropy < 0.0:
            raise ValueError("base_local_entropy must be >= 0")
        if not (0.0 <= self.wish_probability <= 1.0):
            raise ValueError("wish_probability must lie in [0, 1]")
        if self.local_order_min <= 0.0:
            raise ValueError("local_order_min must be > 0")
        if self.local_order_max < self.local_order_min:
            raise ValueError("local_order_max must be >= local_order_min")
        if self.karmic_multiplier <= 1.0:
            raise ValueError("karmic_multiplier must be > 1 to preserve the 2nd law")
        if self.decay_per_order < 0.0:
            raise ValueError("decay_per_order must be >= 0")
        if not (0.0 <= self.witch_threshold <= 1.0):
            raise ValueError("witch_threshold must lie in [0, 1]")
        if self.witch_burst_base < 0.0:
            raise ValueError("witch_burst_base must be >= 0")
        if self.witch_burst_per_order < 0.0:
            raise ValueError("witch_burst_per_order must be >= 0")


# The canonical run described in the README (seed 42, 120 steps, five girls).
DEFAULT = SimConfig()
