"""Tests for the nixie-tube ASCII renderer (divergence_meter.adapters.nixie).

The render must be a non-empty, deterministic, rectangular framed block.
Stdlib-only adapter -> RUNS on both interpreters.
"""

from __future__ import annotations

import pytest

from divergence_meter.adapters.nixie import render, render_reading


def test_render_is_nonempty_and_deterministic() -> None:
    a = render("1.048596")
    b = render("1.048596")
    assert a
    assert a == b


def test_render_shape_is_framed_rectangle() -> None:
    art = render("1.048596")
    lines = art.splitlines()
    # Top border + 5 body rows + bottom border = 7 lines.
    assert len(lines) == 7
    assert all(len(line) == len(lines[0]) for line in lines)
    assert lines[0].startswith("+") and lines[0].endswith("+")


def test_render_reading_has_caption() -> None:
    out = render_reading("1.048596")
    assert "DIVERGENCE: 1.048596" in out
    assert out.splitlines()[0].startswith("+")


def test_render_empty_rejected() -> None:
    with pytest.raises(ValueError):
        render("")


def test_unknown_chars_render_blank_not_crash() -> None:
    # Non-digit characters degrade to blank tubes rather than raising.
    art = render("1x2")
    assert art.splitlines()  # produced something
