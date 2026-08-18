"""divergence_meter.core -- the pure engine (stdlib + commons.core only).

Every module here imports ONLY the standard library and :mod:`commons.core`;
nothing imports an adapter (nixie / cli / viz) or hard-imports numpy/matplotlib,
so the core stays deterministic and dependency free. The public API is
re-exported for convenient one-stop imports.

Pipeline:
    * :mod:`~divergence_meter.core.worldstate`  -- canonical bytes from a source.
    * :mod:`~divergence_meter.core.divergence`  -- SHA-256 -> value in [0, 2).
    * :mod:`~divergence_meter.core.attractor`   -- Alpha/Beta field classification.
    * :mod:`~divergence_meter.core.steiner`     -- Reading Steiner save/recall store.
    * :mod:`~divergence_meter.core.ensemble`    -- seeded worldline ensembles.
"""

from __future__ import annotations

from divergence_meter.core.attractor import (
    FIELDS,
    STEINS_GATE_TOLERANCE,
    FieldClassification,
    classify,
)
from divergence_meter.core.divergence import (
    DECIMAL_PLACES,
    STEINS_GATE_VALUE,
    DivergenceReading,
    compute_divergence,
)
from divergence_meter.core.ensemble import field_histogram, simulate_worldlines
from divergence_meter.core.steiner import (
    DEFAULT_STORE_PATH,
    SteinerError,
    WorldlineRecord,
    divergence_delta,
    get_line,
    list_lines,
    save_line,
)
from divergence_meter.core.worldstate import (
    MAX_READ_BYTES,
    Snapshot,
    WorldStateError,
    snapshot_from_numbers,
    snapshot_from_source,
)

__all__ = [
    # worldstate
    "Snapshot",
    "WorldStateError",
    "MAX_READ_BYTES",
    "snapshot_from_source",
    "snapshot_from_numbers",
    # divergence
    "DivergenceReading",
    "compute_divergence",
    "STEINS_GATE_VALUE",
    "DECIMAL_PLACES",
    # attractor
    "FieldClassification",
    "classify",
    "FIELDS",
    "STEINS_GATE_TOLERANCE",
    # steiner
    "WorldlineRecord",
    "SteinerError",
    "DEFAULT_STORE_PATH",
    "save_line",
    "get_line",
    "list_lines",
    "divergence_delta",
    # ensemble
    "simulate_worldlines",
    "field_histogram",
]
