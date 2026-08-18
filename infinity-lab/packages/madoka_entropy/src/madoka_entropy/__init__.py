"""madoka_entropy -- an entropy & karmic-calculus caricature of Madoka Magica.

A small, seeded simulation of a closed system of magical girls, a global entropy
budget, and the incubators (Kyubey) who harvest the karmic surplus. A *wish*
exports local order at a strictly larger global cost (``k > 1``), so the total
entropy is non-decreasing at every step -- a second-law-like invariant that is
imposed by construction and then verified empirically.

The pure math lives under :mod:`madoka_entropy.core` (stdlib + ``commons.core``
only) and its public API is re-exported here. Presentation lives in
:mod:`madoka_entropy.adapters`; the optional matplotlib PNG export is lazily
guarded via :func:`commons.core.optional.try_import`.

This is a deliberate accounting caricature of thermodynamics, not a physics
derivation -- see ``README.md`` for the honest framing.
"""

from __future__ import annotations

from madoka_entropy import core
from madoka_entropy.core import (
    DEFAULT,
    EntropyLedger,
    Incubator,
    MagicalGirl,
    SimConfig,
    SimResult,
    StepRecord,
    make_girls,
    run_simulation,
    wish_deltas,
)

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "core",
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
