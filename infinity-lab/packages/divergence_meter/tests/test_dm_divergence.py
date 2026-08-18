"""Tests for the honest SHA-256 divergence core (divergence_meter.core.divergence).

Determinism is the whole premise: a fixed input yields a fixed, machine-stable
worldline. These are stdlib + commons.core only, so they RUN on both interpreters.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from divergence_meter.core.divergence import (
    DECIMAL_PLACES,
    STEINS_GATE_VALUE,
    DivergenceReading,
    compute_divergence,
)
from divergence_meter.core.worldstate import Snapshot, snapshot_from_source


def test_deterministic_fixed_input() -> None:
    a = compute_divergence(snapshot_from_source("El Psy Congroo"))
    b = compute_divergence(snapshot_from_source("El Psy Congroo"))
    assert a.value == b.value
    assert a.digest == b.digest
    assert a.word == b.word


def test_fixed_input_pins_known_value() -> None:
    # Machine-stable golden value: SHA-256, not Python's salted hash().
    reading = compute_divergence(snapshot_from_source("El Psy Congroo"))
    assert reading.display == "1.062031"
    assert reading.word == 9795511409617762124


def test_value_in_half_open_range() -> None:
    for source in ("a", "b", "c", "hello world", "12345", "Kurisu"):
        reading = compute_divergence(snapshot_from_source(source))
        assert 0.0 <= reading.value < 2.0


def test_display_format_and_digits() -> None:
    reading = compute_divergence(snapshot_from_source("test"))
    assert DECIMAL_PLACES == 6
    # 1 integer digit + '.' + 6 fractional digits.
    import re

    assert re.match(r"^\d\.\d{6}$", reading.display)
    assert reading.digits == reading.display.replace(".", "")


def test_exact_value_is_lossless_fraction() -> None:
    reading = compute_divergence(snapshot_from_source("Kurisu"))
    # exact_value = word / 2**63, an exact rational in [0, 2).
    assert isinstance(reading.exact_value, Fraction)
    assert reading.exact_value == Fraction(reading.word, 2 ** 63)
    assert 0 <= reading.exact_value < 2
    # value is that rational rounded to 6 dp.
    assert round(float(reading.exact_value), 6) == reading.value


def test_input_change_changes_value() -> None:
    a = compute_divergence(snapshot_from_source("worldline-A"))
    b = compute_divergence(snapshot_from_source("worldline-B"))
    assert a.value != b.value


def test_json_key_order_is_normalised() -> None:
    a = compute_divergence(snapshot_from_source('{"a":1,"b":2}'))
    b = compute_divergence(snapshot_from_source('{"b":2,"a":1}'))
    assert a.value == b.value


def test_is_steins_gate_flag() -> None:
    on = DivergenceReading(value=STEINS_GATE_VALUE, digest="", word=0, origin="x")
    off = DivergenceReading(value=1.5, digest="", word=0, origin="x")
    assert on.is_steins_gate()
    assert not off.is_steins_gate()


def test_rejects_non_snapshot() -> None:
    with pytest.raises(TypeError):
        compute_divergence("not a snapshot")  # type: ignore[arg-type]


def test_accepts_snapshot_instance() -> None:
    snap = Snapshot(origin="text:literal", payload=b"payload")
    reading = compute_divergence(snap)
    assert reading.origin == "text:literal"
