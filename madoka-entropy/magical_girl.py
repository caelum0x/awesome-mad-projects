"""The MagicalGirl subsystem and her soul gem purity dynamics.

Each girl carries a "soul gem purity" in [0, 1]. Purity 1.0 is a freshly
contracted girl; purity 0.0 is total corruption -> witch transformation. Every
act of magic (every wish/spell that imposes local order) muddies the gem in
proportion to how much order was forced onto the world, because fighting local
entropy is what accrues karmic corruption.
"""

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class MagicalGirl:
    """Immutable state for one magical girl (a local-order subsystem)."""

    name: str
    purity: float          # soul gem clarity in [0, 1]; 0 => becomes a witch
    local_entropy: float   # current entropy of her subsystem (lower = more order)
    is_witch: bool = False
    witch_step: int = -1   # simulation step at which she turned (or -1)

    def cast(self, local_order: float, decay_per_order: float) -> "MagicalGirl":
        """Return a NEW girl after casting magic requested at ``local_order``
        units.

        A subsystem cannot export more local order than the entropy it still
        holds, so the amount actually applied is ``local_order`` capped to
        ``self.local_entropy``. Her subsystem entropy drops by that applied
        amount (never below 0) and her purity decays by
        ``decay_per_order * applied``. Purity is clamped at 0 so downstream
        code can detect the witch threshold crossing; local_entropy gets the
        same non-negative floor so a subsystem's entropy -- a physical,
        honest quantity in this model -- can never go negative.
        """
        applied = max(0.0, min(local_order, self.local_entropy))
        new_purity = max(0.0, self.purity - decay_per_order * applied)
        return replace(
            self,
            purity=new_purity,
            local_entropy=self.local_entropy - applied,
        )

    def become_witch(self, step: int) -> "MagicalGirl":
        """Return a NEW girl flagged as a witch at ``step``."""
        return replace(self, is_witch=True, witch_step=step)


def make_girls(names, base_local_entropy: float) -> tuple:
    """Build the initial roster. Returns an immutable tuple of MagicalGirl."""
    return tuple(
        MagicalGirl(name=n, purity=1.0, local_entropy=base_local_entropy)
        for n in names
    )
