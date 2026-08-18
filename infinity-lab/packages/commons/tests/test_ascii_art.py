"""Tests for commons.adapters.ascii_art (text renderers)."""

from __future__ import annotations

import math

import pytest

from commons.adapters.ascii_art import (
    render_convergence,
    render_heatmap,
    render_line_plot,
    render_sign_map,
)


def test_line_plot_non_empty_and_deterministic() -> None:
    ys = [0.0, 0.5, 1.0, 0.5, 0.0]
    out1 = render_line_plot(ys, height=8, title="wave")
    out2 = render_line_plot(ys, height=8, title="wave")
    assert out1 == out2
    assert len(out1) > 0
    assert "wave" in out1
    assert "*" in out1


def test_line_plot_empty_raises() -> None:
    with pytest.raises(ValueError):
        render_line_plot([])


def test_convergence_reports_error() -> None:
    ys = [0.5, 0.75, 0.875, 0.9375, 0.96875]
    out = render_convergence(ys, target=1.0, height=6)
    assert "target=+1.000000" in out
    assert "final |error|" in out
    assert len(out) > 0


def test_heatmap_non_empty_with_legend() -> None:
    values = [[float(r * 3 + c) for c in range(3)] for r in range(3)]
    labels = [0.0, 0.5, 1.0]
    out = render_heatmap(values, row_labels=labels, title="field")
    assert "field" in out
    assert "scale:" in out
    assert len(out.splitlines()) >= 3


def test_heatmap_deterministic() -> None:
    values = [[1.0, 2.0], [3.0, 4.0]]
    assert render_heatmap(values) == render_heatmap(values)


def test_heatmap_ragged_raises() -> None:
    with pytest.raises(ValueError):
        render_heatmap([[1.0, 2.0], [3.0]])


def test_heatmap_empty_raises() -> None:
    with pytest.raises(ValueError):
        render_heatmap([])


def test_heatmap_label_mismatch_raises() -> None:
    with pytest.raises(ValueError):
        render_heatmap([[1.0, 2.0]], row_labels=[0.0, 1.0])


def test_sign_map_traces_zero_curve() -> None:
    # field(x, y) = x changes sign at x = 0 -> a vertical zero curve.
    xs = [-1.0, -0.5, 0.0, 0.5, 1.0]
    ys = [-1.0, 0.0, 1.0]
    out = render_sign_map(lambda x, y: x, xs, ys, title="signs")
    assert "signs" in out
    assert "+" in out and "-" in out and "O" in out
    assert "zero curve" in out


def test_sign_map_deterministic() -> None:
    xs = [-1.0, 0.0, 1.0]
    ys = [-1.0, 0.0, 1.0]
    f = lambda x, y: math.sin(x) - y  # noqa: E731
    assert render_sign_map(f, xs, ys) == render_sign_map(f, xs, ys)


def test_sign_map_empty_raises() -> None:
    with pytest.raises(ValueError):
        render_sign_map(lambda x, y: x, [], [1.0])
