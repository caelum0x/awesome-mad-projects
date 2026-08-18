"""divergence_meter -- a Steins;Gate Divergence Meter for the infinity-lab monorepo.

Computes a deterministic "worldline divergence" number from a snapshot of world
state, classifies it into an attractor field (Alpha < 1.0 / Beta >= 1.0), renders
it on a nixie-style ASCII display, and lets you save / recall named worldlines
("Reading Steiner"). The famous ``1.048596`` Steins;Gate line is flagged when a
reading lands on it.

The pure math lives under :mod:`divergence_meter.core` (stdlib + ``commons.core``
only) and its public API is re-exported here. ASCII rendering and the optional
matplotlib PNG timeline live in :mod:`divergence_meter.adapters` -- the latter
lazily guarded, so the package always imports with the standard library alone.
"""

from __future__ import annotations

from divergence_meter import core
from divergence_meter.core import (
    STEINS_GATE_VALUE,
    DivergenceReading,
    FieldClassification,
    Snapshot,
    WorldlineRecord,
    classify,
    compute_divergence,
    divergence_delta,
    field_histogram,
    get_line,
    list_lines,
    save_line,
    simulate_worldlines,
    snapshot_from_numbers,
    snapshot_from_source,
)

__version__ = "1.0.0"

__all__ = [
    "__version__",
    "core",
    # worldstate
    "Snapshot",
    "snapshot_from_source",
    "snapshot_from_numbers",
    # divergence
    "DivergenceReading",
    "compute_divergence",
    "STEINS_GATE_VALUE",
    # attractor
    "FieldClassification",
    "classify",
    # steiner
    "WorldlineRecord",
    "save_line",
    "get_line",
    "list_lines",
    "divergence_delta",
    # ensemble
    "simulate_worldlines",
    "field_histogram",
]
