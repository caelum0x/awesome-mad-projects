"""Tests for Reading Steiner save/recall (divergence_meter.core.steiner).

Round-trip a saved worldline and check the signed divergence delta. Uses an
explicit ``store_path`` under pytest's ``tmp_path`` so nothing is written into the
repo. Stdlib-only -> RUNS on both interpreters.
"""

from __future__ import annotations

import json

import pytest

from divergence_meter.core.divergence import compute_divergence
from divergence_meter.core.steiner import (
    SteinerError,
    divergence_delta,
    get_line,
    list_lines,
    save_line,
)
from divergence_meter.core.worldstate import snapshot_from_source


def _store(tmp_path) -> str:
    return str(tmp_path / "worldlines.json")


def test_save_and_recall_round_trip(tmp_path) -> None:
    store = _store(tmp_path)
    reading = compute_divergence(snapshot_from_source("alpha-line"))
    saved = save_line("alpha", reading, store_path=store)
    recalled = get_line("alpha", store_path=store)
    assert recalled.value == reading.value
    assert recalled.display == reading.display
    assert recalled.digest == reading.digest
    assert saved.name == "alpha"


def test_save_overwrites_and_does_not_mutate_on_disk(tmp_path) -> None:
    store = _store(tmp_path)
    save_line("l", compute_divergence(snapshot_from_source("one")), store_path=store)
    save_line("l", compute_divergence(snapshot_from_source("two")), store_path=store)
    on_disk = json.loads(open(store, encoding="utf-8").read())
    assert set(on_disk) == {"l"}
    assert on_disk["l"]["origin"] == "text:literal"


def test_missing_line_raises(tmp_path) -> None:
    with pytest.raises(SteinerError):
        get_line("does-not-exist", store_path=_store(tmp_path))


def test_empty_name_rejected(tmp_path) -> None:
    reading = compute_divergence(snapshot_from_source("x"))
    with pytest.raises(SteinerError):
        save_line("   ", reading, store_path=_store(tmp_path))


def test_list_lines_sorted(tmp_path) -> None:
    store = _store(tmp_path)
    save_line("beta", compute_divergence(snapshot_from_source("b")), store_path=store)
    save_line("alpha", compute_divergence(snapshot_from_source("a")), store_path=store)
    names = [rec.name for rec in list_lines(store_path=store)]
    assert names == ["alpha", "beta"]


def test_divergence_delta_signs(tmp_path) -> None:
    a = compute_divergence(snapshot_from_source("line-A"))
    b = compute_divergence(snapshot_from_source("line-B"))
    delta = divergence_delta(a.value, b.value)
    assert delta == pytest.approx(round(b.value - a.value, 6), abs=1e-9)
    assert divergence_delta(0.5, 0.5) == 0.0
