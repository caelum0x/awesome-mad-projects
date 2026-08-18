"""Entropy accounting primitives for the Madoka Magica closed system.

We track a single scalar "entropy" in dimensionless units. The system is
partitioned into subsystems (each magical girl's local order) plus a global
reservoir (the rest of the universe). The invariant we care about is the
second-law-like statement::

    d(S_total) / d(step) >= 0

where ``S_total = S_global + sum(S_local_i)``.

A *wish* is an act of local entropy export: it lowers a subsystem's local
entropy (imposes order / grants a miracle) but must pay a strictly larger
karmic cost dumped into the global reservoir. That asymmetry is what keeps the
total non-decreasing. See ``README.md`` for the honest framing of why this is a
caricature of thermodynamics rather than a literal derivation.

Purity: imports only the standard library.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Tuple


@dataclass(frozen=True)
class EntropyLedger:
    """Immutable snapshot of the whole system's entropy accounting.

    All fields are in the same dimensionless entropy units.
    """

    global_entropy: float          # S in the global reservoir (the universe)
    local_entropy: float           # sum of S_local over living magical girls
    harvested_energy: float        # cumulative negentropy exported by incubators

    @property
    def total_entropy(self) -> float:
        """Total system entropy = global + all local subsystems."""
        return self.global_entropy + self.local_entropy

    def with_changes(
        self,
        d_global: float = 0.0,
        d_local: float = 0.0,
        d_harvest: float = 0.0,
    ) -> "EntropyLedger":
        """Return a NEW ledger with the given deltas applied (never mutates)."""
        return replace(
            self,
            global_entropy=self.global_entropy + d_global,
            local_entropy=self.local_entropy + d_local,
            harvested_energy=self.harvested_energy + d_harvest,
        )


def wish_deltas(local_order: float, karmic_multiplier: float) -> Tuple[float, float]:
    """Compute the entropy deltas produced by a single wish.

    A wish imposes ``local_order`` (> 0) units of order on a subsystem, so the
    subsystem's local entropy DECREASES by that amount. The karmic cost dumped
    into the global reservoir is strictly larger::

        d_global = karmic_multiplier * local_order   (multiplier > 1)
        d_local  = -local_order

    Net total change = ``(karmic_multiplier - 1) * local_order > 0``, which is
    the per-wish guarantee behind the global invariant.

    Returns ``(d_global, d_local)``. Raises :class:`ValueError` on invalid
    parameters so the invariant can never be silently violated by bad input.
    """
    if local_order <= 0:
        raise ValueError(f"local_order must be > 0, got {local_order}")
    if karmic_multiplier <= 1.0:
        raise ValueError(
            "karmic_multiplier must be > 1 to preserve the 2nd law, "
            f"got {karmic_multiplier}"
        )
    d_global = karmic_multiplier * local_order
    d_local = -local_order
    return d_global, d_local
