"""Tests for the ASCII timeline adapter (divergence_meter.adapters.timeline).

It delegates to commons.adapters.ascii_art; output must be non-empty,
deterministic, and reject empty input. Stdlib + commons -> RUNS on both.
"""

from __future__ import annotations

import pytest

from divergence_meter.adapters import timeline
from divergence_meter.core.ensemble import simulate_worldlines


def test_timeline_is_nonempty_and_deterministic() -> None:
    readings = simulate_worldlines(40, seed=42)
    a = timeline.render_worldline_timeline(readings)
    b = timeline.render_worldline_timeline(readings)
    assert a == b
    assert "worldline divergence timeline" in a
    assert "Steins;Gate line" in a


def test_field_histogram_render_has_all_fields() -> None:
    readings = simulate_worldlines(60, seed=42)
    out = timeline.render_field_histogram(readings)
    for name in ("Alpha-Low", "Alpha", "Beta", "Beta-High"):
        assert name in out


def test_empty_readings_rejected() -> None:
    with pytest.raises(ValueError):
        timeline.render_worldline_timeline([])
    with pytest.raises(ValueError):
        timeline.render_field_histogram([])
