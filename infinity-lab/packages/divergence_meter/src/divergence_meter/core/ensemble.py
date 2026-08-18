"""Deterministic ensembles of worldlines for timelines and field statistics.

A single divergence reading is one worldline. To *visualise* how worldlines
scatter across the ``[0, 2)`` divergence range -- and how they populate the
Alpha/Beta attractor fields -- we simulate an ensemble of experiments. Each
experiment draws a reproducible random token from a seeded generator
(:class:`commons.core.rng.DeterministicRNG`, so nothing touches global RNG state)
and hashes it into a worldline via the honest SHA-256 core.

The result is fully reproducible: same ``count`` and ``seed`` -> identical
readings, always. This module is part of the pure ``core`` layer (stdlib +
``commons.core`` only).
"""

from __future__ import annotations

from typing import Dict, Tuple

from commons.core.rng import make_rng

from divergence_meter.core.attractor import FIELDS, classify
from divergence_meter.core.divergence import DivergenceReading, compute_divergence
from divergence_meter.core.worldstate import snapshot_from_source

# Token space each experiment samples from (kept small and explicit so the byte
# payloads -- and therefore the worldlines -- are stable across machines).
_TOKEN_MIN = 0
_TOKEN_MAX = 2 ** 31 - 1


def simulate_worldlines(count: int, *, seed: int = 42) -> Tuple[DivergenceReading, ...]:
    """Return ``count`` reproducible worldline readings drawn from ``seed``.

    Each reading is the SHA-256 divergence of a token string
    ``"worldline-<n>"`` where ``n`` is a seeded pseudo-random integer. The
    generator is a private :class:`~commons.core.rng.DeterministicRNG`, so the
    process-global RNG is never read or written and results are identical on
    every machine.

    Raises:
        ValueError: If ``count`` is negative.
    """
    if count < 0:
        raise ValueError("count must be non-negative")
    rng = make_rng(seed)
    readings = []
    for _ in range(count):
        token = rng.randint(_TOKEN_MIN, _TOKEN_MAX)
        snapshot = snapshot_from_source(f"worldline-{token}")
        readings.append(compute_divergence(snapshot))
    return tuple(readings)


def field_histogram(readings: Tuple[DivergenceReading, ...]) -> Dict[str, int]:
    """Count how many ``readings`` fall into each named attractor field.

    Returns a dict keyed by every field name in :data:`attractor.FIELDS` (zero
    for empty fields), so the histogram shape is stable regardless of the sample.
    """
    counts: Dict[str, int] = {name: 0 for name, _, _ in FIELDS}
    for reading in readings:
        counts[classify(reading.value).field] += 1
    return counts
