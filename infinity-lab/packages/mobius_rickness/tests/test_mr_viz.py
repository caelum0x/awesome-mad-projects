"""Tests for the ASCII/PNG visualisation adapter (mobius_rickness.adapters.viz).

The ASCII renderers must always work with the standard library alone, return
non-empty strings, and be byte-for-byte deterministic. The 3D PNG export is
optional and DEFERRED: with no matplotlib it must raise a clear error rather than
fail at import time.
"""

from __future__ import annotations

import pytest

from commons.core.optional import try_import
from mobius_rickness.adapters import viz


# ---------------------------------------------------------------------------
# ASCII renderers: non-empty + titled
# ---------------------------------------------------------------------------

def test_sign_map_non_empty_and_marks_zero_curve() -> None:
    out = viz.render_rickness_sign_map()
    assert out  # non-empty
    assert "Rickness R(u,v) sign map" in out
    assert "Central Finite Curve" in out
    # all three region markers appear: + region, - region, and the zero curve.
    assert "+" in out and "-" in out and "O" in out


def test_k_rick_heatmap_non_empty_and_titled() -> None:
    out = viz.render_k_rick_heatmap()
    assert out
    assert "K_Rick(u,v) = K*R heatmap" in out
    assert "scale:" in out  # legend line from the shared heatmap renderer


def test_curvature_table_non_empty_and_reproduces_original() -> None:
    out = viz.render_curvature_table()
    assert out
    assert "Original curvature sample table" in out
    assert "R_naive = 1.5 +" in out
    assert "Every K < 0 and every R_naive > 0  =>  K_Rick < 0 with NO zero." in out
    # sampled u-labels from the original table are present.
    for label in ("pi/2", "3pi/2", "7pi/4"):
        assert label in out


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "call",
    [
        viz.render_rickness_sign_map,
        viz.render_k_rick_heatmap,
        viz.render_curvature_table,
    ],
)
def test_renderers_are_deterministic(call) -> None:
    assert call() == call()


# ---------------------------------------------------------------------------
# Optional 3D PNG export -- DEFERRED behind the matplotlib guard
# ---------------------------------------------------------------------------

class _FakePoint:
    """Minimal duck-typed curve point exposing x/y/z for the PNG export."""

    def __init__(self, x: float, y: float, z: float) -> None:
        self.x = x
        self.y = y
        self.z = z


def test_png_export_guarded_on_optional_dependency(tmp_path) -> None:
    target = str(tmp_path / "curve.png")
    points = [_FakePoint(1.0, 0.0, 0.0), _FakePoint(0.0, 1.0, 0.1)]
    if try_import("matplotlib") is None:
        # matplotlib absent (the offline default): must raise, never crash-import.
        with pytest.raises(viz.OptionalDependencyError):
            viz.save_curve_png(points, target)
    else:  # pragma: no cover - only runs where matplotlib is installed
        import os

        out = viz.save_curve_png(points, target)
        assert out == target
        assert os.path.exists(target)
