"""Tests for the ASCII render adapter (padic_embeddings.adapters.render).

The renderers are deterministic pure-text functions; these pin their key structural
markers. The heatmap DELEGATES to ``commons.adapters.ascii_art.render_heatmap``. Pure
stdlib + commons, so these RUN on both interpreters.
"""

from __future__ import annotations

from padic_embeddings.core import embedding
from padic_embeddings.adapters import render

_COORDS = [1, 3, 5, 8, 16, 17, 24, 32, 48, 64]
_LABELS = [str(c) for c in _COORDS]


def test_distance_matrix_has_labels_and_known_cell() -> None:
    out = render.format_distance_matrix(_LABELS, _COORDS, 2)
    assert "pairwise 2-adic distance matrix" in out
    for label in _LABELS:
        assert label in out
    # 1 and 17 are close: 17 - 1 = 16 = 2^4 -> distance 0.0625.
    assert "0.06250" in out


def test_distance_heatmap_delegates_to_commons() -> None:
    out = render.distance_heatmap(_COORDS, 2)
    assert "2-adic distance heatmap" in out
    assert "scale:" in out  # legend produced by commons render_heatmap
    assert render.distance_heatmap([], 2) == "(no coordinates)"


def test_valuation_table_reports_values() -> None:
    out = render.format_valuation_table(_LABELS, _COORDS, 2)
    assert "v_2(coord)" in out
    assert "0.015625" in out  # |64|_2 = 2^-6


def test_clusters_show_residue_balls() -> None:
    out = render.format_clusters(_COORDS, 2, [1, 2, 3])
    assert "level 1:" in out
    assert "level 3:" in out
    assert "residue" in out


def test_ultrametric_report_holds() -> None:
    out = render.format_ultrametric_report(_COORDS, 2)
    assert "violations found: 0" in out
    assert "HOLDS" in out


def test_nearest_neighbors_render() -> None:
    neighbors = embedding.nearest_neighbors(16, _COORDS, 2, k=3)
    out = render.format_nearest_neighbors("16", neighbors, 2)
    assert "nearest neighbors of '16'" in out
    assert "48" in out
