"""The Incubator (Kyubey) energy/entropy harvesting model.

Canon: Incubators contract with girls to harvest the emotional energy released
during wishes and witch transformations, using it to fight the heat death of
the universe. In our accounting, the "emotion differential" is the karmic
SURPLUS of a wish -- the part of the global entropy increase beyond what was
removed locally. The incubator skims a fraction of that surplus as exported
negentropy (usable energy), while the remainder is irreversibly lost to the
global reservoir.

This module is intentionally tiny: it only computes how much of a given entropy
event the incubator can harvest. The simulation applies the bookkeeping.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Incubator:
    """Immutable harvesting policy for the incubator collective."""

    name: str = "Kyubey"
    harvest_fraction: float = 0.35   # share of the karmic surplus skimmed

    def harvest_from_wish(self, d_global: float, d_local: float) -> float:
        """Energy harvested from one wish.

        The karmic surplus is ``d_global + d_local`` (global gain minus the
        magnitude of local order imposed, since d_local is negative). The
        incubator skims ``harvest_fraction`` of that surplus.
        """
        surplus = d_global + d_local
        if surplus <= 0:
            return 0.0
        return self.harvest_fraction * surplus

    def harvest_from_witch(self, burst: float) -> float:
        """Energy harvested from a witch transformation burst.

        Witch bursts are the richest emotional yield in canon, so the incubator
        skims the same fraction of the raw burst.
        """
        if burst <= 0:
            return 0.0
        return self.harvest_fraction * burst
