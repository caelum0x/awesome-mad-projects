"""Tests for the four-panel composite explainer (central_finite_curve.adapters.animate_panels).

DEFERRED and layered so the suite behaves on both interpreters:

    * The composite **GIF** needs matplotlib AND Pillow -> the module gate uses
      ``pytest.importorskip`` for both, so the whole module SKIPS on the stdlib-only
      system interpreter and RUNS on the venv.
    * The **MP4** test additionally requires an ffmpeg writer; it skips (via
      :func:`pytest.skip`) when the ffmpeg writer is unavailable, else renders a short
      clip and validates the ISO-BMFF ``ftyp`` box.
    * The **negative** test forces ffmpeg unavailable (monkeypatching
      :func:`shutil.which` -> ``None``) and asserts :func:`save_cfc_four_panels_mp4`
      raises :class:`OptionalDependencyError`.
    * A "sources real core" check asserts the scene draws its numbers from the genuine
      core: the band size equals ``core.curve``'s and the acceptance equals
      ``core.portal_gun``'s under a fixed seed.

Every animation is rendered SHORT (a handful of frames, a tiny pipeline) into
``tmp_path`` so the suite stays fast. GIFs are validated by their magic signature
(``GIF87a`` / ``GIF89a``); MP4s by the ``ftyp`` box at bytes 4..8. All rendering is
headless (Agg).
"""

from __future__ import annotations

import os

import pytest

pytest.importorskip("matplotlib")
pytest.importorskip("PIL")

from central_finite_curve.adapters import animate_panels, cli  # noqa: E402
from central_finite_curve.adapters.viz import OptionalDependencyError  # noqa: E402
from central_finite_curve.core.config import CurveConfig  # noqa: E402
from central_finite_curve.core.pipeline import run  # noqa: E402

_GIF_SIGNATURES = (b"GIF87a", b"GIF89a")
_MIN_BYTES = 1024

# Small render config shared by the tests to keep them fast.
_SMALL = CurveConfig(n_universes=400, walk_steps=150, seed=137)
_FAST = dict(frames=5, hold=2, fps=4)


def _assert_valid_gif(path: str) -> None:
    assert os.path.exists(path), f"expected GIF at {path}"
    with open(path, "rb") as handle:
        head = handle.read(6)
    assert head in _GIF_SIGNATURES, f"not a GIF signature: {head!r}"
    assert os.path.getsize(path) > _MIN_BYTES, "GIF suspiciously small (< 1 KiB)"


def _assert_valid_mp4(path: str) -> None:
    assert os.path.exists(path), f"expected MP4 at {path}"
    with open(path, "rb") as handle:
        head = handle.read(12)
    assert head[4:8] == b"ftyp", f"not ISO-BMFF/MP4 (bytes 4..8): {head[4:8]!r}"
    assert os.path.getsize(path) > _MIN_BYTES, "MP4 suspiciously small (< 1 KiB)"


def _require_ffmpeg() -> None:
    if not animate_panels.ffmpeg_is_available():
        pytest.skip("ffmpeg writer unavailable (no ffmpeg binary on PATH)")


# ---------------------------------------------------------------------------
# Sources the REAL pure core (dependency-light: pure projector, no matplotlib call)
# ---------------------------------------------------------------------------

def test_frame_data_sources_real_core() -> None:
    data = animate_panels.four_panel_frame_data(5, config=_SMALL)
    result = run(_SMALL, project=False)

    # Band size and acceptance ratio come straight from the genuine core objects.
    assert data.curve_size == result.curve.size
    assert data.total == result.curve.total == _SMALL.n_universes
    assert data.acceptance_rate == result.walk.acceptance_rate
    assert data.walk_steps == result.walk.steps

    # The highlighted band is exactly the near-maximal super-level set.
    assert data.band_low == result.curve.band_low
    assert sum(1 for hot in data.in_band if hot) == result.curve.size
    # One projected point per universe (colour source) and per walk point.
    assert len(data.uni_scores) == data.total == len(data.uni_x)
    assert len(data.walk_x) == len(result.walk.points)


def test_frame_data_validates_arguments() -> None:
    with pytest.raises(ValueError):
        animate_panels.four_panel_frame_data(0, config=_SMALL)


# ---------------------------------------------------------------------------
# GIF (matplotlib + Pillow -> runs on the venv)
# ---------------------------------------------------------------------------

def test_save_cfc_four_panels_gif(tmp_path) -> None:
    path = str(tmp_path / "four_panels.gif")
    out = animate_panels.save_cfc_four_panels_gif(path, config=_SMALL, **_FAST)
    assert out == path
    _assert_valid_gif(path)


def test_cli_animate_panels_flag_writes_composite_gif(tmp_path) -> None:
    outdir = str(tmp_path / "panels")
    text = cli.run_cli(
        ["animate", outdir, "--panels", "--universes", "400", "--walk-steps", "150"]
    )
    assert "four-panel explainer GIF" in text
    files = set(os.listdir(outdir))
    assert {
        "central_finite_curve_walk.gif",
        "central_finite_curve_four_panels.gif",
    } <= files
    _assert_valid_gif(os.path.join(outdir, "central_finite_curve_four_panels.gif"))


def test_panels_gif_validates_arguments() -> None:
    with pytest.raises(ValueError):
        animate_panels.save_cfc_four_panels_gif("unused.gif", config=_SMALL, frames=0)
    with pytest.raises(ValueError):
        animate_panels.save_cfc_four_panels_gif("unused.gif", config=_SMALL, hold=-1)
    with pytest.raises(ValueError):
        animate_panels.save_cfc_four_panels_gif("unused.gif", config=_SMALL, fps=0)


# ---------------------------------------------------------------------------
# MP4 (matplotlib + ffmpeg -> skip when ffmpeg writer unavailable)
# ---------------------------------------------------------------------------

def test_save_cfc_four_panels_mp4(tmp_path) -> None:
    _require_ffmpeg()
    path = str(tmp_path / "four_panels.mp4")
    out = animate_panels.save_cfc_four_panels_mp4(path, config=_SMALL, **_FAST)
    assert out == path
    _assert_valid_mp4(path)


# ---------------------------------------------------------------------------
# Negative test: ffmpeg forced unavailable -> OptionalDependencyError
# ---------------------------------------------------------------------------

def test_panels_mp4_raises_when_ffmpeg_unavailable(tmp_path, monkeypatch) -> None:
    import shutil

    monkeypatch.setattr(shutil, "which", lambda _name: None)
    assert animate_panels.ffmpeg_is_available() is False
    with pytest.raises(OptionalDependencyError):
        animate_panels.save_cfc_four_panels_mp4(
            str(tmp_path / "nope.mp4"), config=_SMALL, **_FAST
        )


def test_panels_mp4_validates_arguments() -> None:
    with pytest.raises(ValueError):
        animate_panels.save_cfc_four_panels_mp4("unused.mp4", config=_SMALL, fps=0)
