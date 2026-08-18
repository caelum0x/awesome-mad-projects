"""Tests for attractor-field classification (divergence_meter.core.attractor).

Alpha < 1.0, Beta >= 1.0; nearest-boundary distance; the 1.048596 Steins;Gate
flag. Stdlib-only -> RUNS on both interpreters.
"""

from __future__ import annotations

import pytest

from divergence_meter.core.attractor import FIELDS, classify
from divergence_meter.core.divergence import STEINS_GATE_VALUE


def test_alpha_vs_beta_cluster() -> None:
    assert classify(0.337187).cluster == "Alpha"
    assert classify(1.048596).cluster == "Beta"
    assert classify(0.0).cluster == "Alpha"
    assert classify(1.999999).cluster == "Beta"


def test_field_bins() -> None:
    assert classify(0.25).field == "Alpha-Low"
    assert classify(0.75).field == "Alpha"
    assert classify(1.25).field == "Beta"
    assert classify(1.75).field == "Beta-High"


def test_boundary_distance_on_steins_gate_line() -> None:
    result = classify(1.048596)
    assert result.nearest_boundary == 1.0
    assert result.distance_to_boundary == pytest.approx(0.048596, abs=1e-6)


def test_steins_gate_flag() -> None:
    assert classify(STEINS_GATE_VALUE).on_steins_gate is True
    assert classify(1.5).on_steins_gate is False


def test_describe_mentions_field_and_boundary() -> None:
    text = classify(1.048596).describe()
    assert "Beta" in text
    assert "STEINS;GATE" in text
    assert "nearest boundary" in text


def test_rejects_non_finite() -> None:
    with pytest.raises(ValueError):
        classify(float("inf"))
    with pytest.raises(ValueError):
        classify(float("nan"))


def test_fields_span_full_range() -> None:
    assert FIELDS[0][1] == 0.0
    assert FIELDS[-1][2] == 2.0
