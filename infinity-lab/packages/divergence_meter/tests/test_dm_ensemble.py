"""Tests for seeded worldline ensembles (divergence_meter.core.ensemble).

Ensembles must be reproducible (seeded via commons.core.rng) and the field
histogram must account for every reading. Stdlib + commons.core -> RUNS on both.
"""

from __future__ import annotations

import pytest

from divergence_meter.core.ensemble import field_histogram, simulate_worldlines


def test_simulation_is_reproducible() -> None:
    a = simulate_worldlines(30, seed=7)
    b = simulate_worldlines(30, seed=7)
    assert [r.value for r in a] == [r.value for r in b]
    assert [r.digest for r in a] == [r.digest for r in b]


def test_different_seed_diverges() -> None:
    a = simulate_worldlines(30, seed=7)
    b = simulate_worldlines(30, seed=8)
    assert [r.value for r in a] != [r.value for r in b]


def test_count_and_range() -> None:
    readings = simulate_worldlines(50, seed=42)
    assert len(readings) == 50
    assert all(0.0 <= r.value < 2.0 for r in readings)


def test_negative_count_rejected() -> None:
    with pytest.raises(ValueError):
        simulate_worldlines(-1)


def test_histogram_accounts_for_every_reading() -> None:
    readings = simulate_worldlines(120, seed=42)
    hist = field_histogram(readings)
    assert sum(hist.values()) == len(readings)
    # Every field key is present even if a bucket is empty.
    assert set(hist) == {"Alpha-Low", "Alpha", "Beta", "Beta-High"}
