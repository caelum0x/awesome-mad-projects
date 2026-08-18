"""Tests for the ASCII/PNG visualisation adapter (gojo_infinity.adapters.viz).

The ASCII renderers must always work with the standard library alone, return
non-empty strings, and be byte-for-byte deterministic. The PNG export is
optional and DEFERRED: with no matplotlib it must raise a clear error rather
than fail at import time.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from commons.core.optional import try_import
from gojo_infinity.adapters import viz


# ---------------------------------------------------------------------------
# ASCII renderers: non-empty + deterministic
# ---------------------------------------------------------------------------

def test_zeno_convergence_non_empty_and_titled() -> None:
    out = viz.render_zeno_convergence(12)
    assert out  # non-empty
    assert "Zeno" in out
    assert "target=+1.000000" in out


def test_omega_blowup_non_empty_and_titled() -> None:
    out = viz.render_omega_blowup()
    assert out
    assert "Omega(x) blow-up" in out
    assert "*" in out  # a plotted series is present


def test_cover_convergence_non_empty_and_targets_eps() -> None:
    out = viz.render_cover_convergence(Fraction(1, 10), 12)
    assert out
    assert "cover length" in out
    assert "target=+0.100000" in out


@pytest.mark.parametrize(
    "call",
    [
        lambda: viz.render_zeno_convergence(12),
        lambda: viz.render_omega_blowup(),
        lambda: viz.render_cover_convergence(Fraction(1, 10), 12),
    ],
)
def test_renderers_are_deterministic(call) -> None:
    assert call() == call()


def test_zeno_values_use_exact_core() -> None:
    ys = viz.zeno_series_values(4)
    assert ys == [0.5, 0.75, 0.875, 0.9375]


def test_cover_length_values_climb_toward_eps() -> None:
    ys = viz.cover_length_values(Fraction(1, 10), 8)
    assert ys[0] == pytest.approx(0.05)
    assert all(a < b for a, b in zip(ys, ys[1:]))  # strictly increasing
    assert ys[-1] < 0.1  # never exceeds eps


def test_omega_profile_is_increasing_toward_pole() -> None:
    ys = viz.omega_profile(0.1, 0.98, 20)
    assert ys[0] < ys[-1]
    assert ys[-1] > 5.0  # blowing up near the barrier


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------

def test_zeno_values_rejects_bad_max_n() -> None:
    with pytest.raises(ValueError):
        viz.zeno_series_values(0)


def test_omega_profile_rejects_range_touching_pole() -> None:
    with pytest.raises(ValueError):
        viz.omega_profile(0.1, 1.0, 10)  # x1 == x_gojo


# ---------------------------------------------------------------------------
# Optional PNG export -- DEFERRED behind the matplotlib guard
# ---------------------------------------------------------------------------

def test_png_export_empty_series_rejected() -> None:
    with pytest.raises(ValueError):
        viz.save_convergence_png([], 1.0, "unused.png")


def test_png_export_guarded_on_optional_dependency(tmp_path) -> None:
    target = str(tmp_path / "conv.png")
    if try_import("matplotlib") is None:
        # matplotlib absent (the offline default): must raise, never crash-import.
        with pytest.raises(viz.OptionalDependencyError):
            viz.save_convergence_png([0.5, 0.75, 0.875], 1.0, target)
    else:  # pragma: no cover - only runs where matplotlib is installed
        out = viz.save_convergence_png([0.5, 0.75, 0.875], 1.0, target)
        assert out == target
        import os

        assert os.path.exists(target)
