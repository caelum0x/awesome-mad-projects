"""madoka_entropy.core -- the pure engine (stdlib + commons.core only).

Every module here imports ONLY the standard library and :mod:`commons.core`;
nothing imports an adapter (plot / cli / viz) or hard-imports numpy/matplotlib,
so the core stays deterministic and dependency free. The public API is
re-exported for convenient one-stop imports.

Pipeline:
    * :mod:`~madoka_entropy.core.config`       -- frozen :class:`SimConfig`.
    * :mod:`~madoka_entropy.core.entropy`      -- the entropy ledger + wish rule.
    * :mod:`~madoka_entropy.core.magical_girl` -- purity decay + witch flag.
    * :mod:`~madoka_entropy.core.incubator`    -- Kyubey's harvest accounting.
    * :mod:`~madoka_entropy.core.simulation`   -- seeded loop + invariant check.
"""

from __future__ import annotations

from madoka_entropy.core.config import DEFAULT, SimConfig
from madoka_entropy.core.entropy import EntropyLedger, wish_deltas
from madoka_entropy.core.incubator import Incubator
from madoka_entropy.core.magical_girl import MagicalGirl, make_girls
from madoka_entropy.core.simulation import (
    SimResult,
    StepRecord,
    run_simulation,
)

__all__ = [
    # config
    "SimConfig",
    "DEFAULT",
    # entropy
    "EntropyLedger",
    "wish_deltas",
    # magical girl
    "MagicalGirl",
    "make_girls",
    # incubator
    "Incubator",
    # simulation
    "StepRecord",
    "SimResult",
    "run_simulation",
]
