"""Tests for snapshot gathering (divergence_meter.core.worldstate).

Sources must produce canonical, immutable bytes; empty inputs fail fast.
Stdlib-only -> RUNS on both interpreters.
"""

from __future__ import annotations

import dataclasses
import io

import pytest

from divergence_meter.core.worldstate import (
    Snapshot,
    WorldStateError,
    snapshot_from_numbers,
    snapshot_from_source,
)


def test_text_literal_snapshot() -> None:
    snap = snapshot_from_source("Kurisu Makise")
    assert snap.origin == "text:literal"
    assert snap.payload == b"Kurisu Makise"


def test_snapshot_is_frozen() -> None:
    snap = snapshot_from_source("x")
    with pytest.raises(dataclasses.FrozenInstanceError):
        snap.origin = "mutated"  # type: ignore[misc]


def test_empty_source_rejected() -> None:
    with pytest.raises(WorldStateError):
        snapshot_from_source("   ")


def test_stdin_source() -> None:
    stream = io.BytesIO(b"time travel")
    snap = snapshot_from_source("-", stdin=stream)
    assert snap.origin == "stdin"
    assert snap.payload == b"time travel"


def test_empty_stdin_rejected() -> None:
    with pytest.raises(WorldStateError):
        snapshot_from_source("-", stdin=io.BytesIO(b""))


def test_numbers_snapshot() -> None:
    snap = snapshot_from_numbers([1, 2, 3])
    assert "numbers" in snap.origin
    assert isinstance(snap, Snapshot)
    with pytest.raises(WorldStateError):
        snapshot_from_numbers([])


def test_directory_snapshot_is_order_independent(tmp_path) -> None:
    (tmp_path / "b.txt").write_text("bbb")
    (tmp_path / "a.txt").write_text("aa")
    snap = snapshot_from_source(str(tmp_path))
    assert snap.origin.startswith("dir:")
    # Deterministic: re-snapshotting the same tree yields identical bytes.
    assert snapshot_from_source(str(tmp_path)).payload == snap.payload


def test_json_normalisation_via_snapshot() -> None:
    a = snapshot_from_source('{"a":1,"b":2}')
    b = snapshot_from_source('{"b":2,"a":1}')
    assert a.origin == "json:literal"
    assert a.payload == b.payload
