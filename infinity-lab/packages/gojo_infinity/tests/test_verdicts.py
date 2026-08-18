"""The assembled four-lens conclusion table."""

from __future__ import annotations

from gojo_infinity.core import measure, riemannian, topology, verdicts, zeno


def test_verdict_labels_are_fragile_fragile_formidable_falls() -> None:
    assert verdicts.verdict_labels() == ["Fragile", "Fragile", "Formidable", "Falls"]


def test_conclusion_table_matches_each_lens_verdict() -> None:
    table = verdicts.conclusion_table()
    assert len(table) == 4
    assert table[0] == zeno.verdict()
    assert table[1] == measure.verdict()
    assert table[2] == riemannian.verdict()
    assert table[3] == topology.verdict()


def test_verdict_is_immutable() -> None:
    import dataclasses

    import pytest

    v = verdicts.conclusion_table()[0]
    with pytest.raises(dataclasses.FrozenInstanceError):
        v.verdict = "Changed"  # type: ignore[misc]


def test_format_table_is_deterministic_ascii() -> None:
    out = verdicts.format_table()
    assert out == verdicts.format_table()
    assert out.isascii()
    for label in ("Fragile", "Formidable", "Falls"):
        assert label in out
