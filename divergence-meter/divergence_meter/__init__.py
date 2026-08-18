"""Divergence Meter package.

A Steins;Gate inspired toolkit that computes a deterministic "worldline
divergence" number from a snapshot of world state, classifies it into an
attractor field, renders it on a nixie-style ASCII display, and lets you
save / recall named worldlines ("Reading Steiner").

Everything here is pure Python standard library. No external dependencies.
"""

from .divergence import DivergenceReading, compute_divergence
from .worldstate import Snapshot, snapshot_from_source

__all__ = [
    "DivergenceReading",
    "compute_divergence",
    "Snapshot",
    "snapshot_from_source",
    "__version__",
]

__version__ = "1.0.0"
