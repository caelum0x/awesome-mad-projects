"""Tests for the OPTIONAL walk animation (GIF + MP4 exporters).

DEFERRED behind the matplotlib / Pillow / ffmpeg guards:

    * The walk **GIF** needs matplotlib AND Pillow -> the module gate uses
      ``pytest.importorskip`` for both, so it SKIPS on the stdlib-only system
      interpreter and RUNS on the venv.
    * The **MP4** tests need matplotlib AND an ffmpeg binary; they
      :func:`pytest.skip` when the ffmpeg writer is unavailable.
    * The **negative** test forces ffmpeg unavailable (monkeypatching
      :func:`shutil.which` to ``None``) and asserts the MP4 saver raises
      :class:`OptionalDependencyError`.

Every animation is rendered SHORT (a handful of frames, low fps, a small pipeline)
into ``tmp_path`` so the suite stays fast. GIFs are validated by their magic
signature; MP4s by the ISO-BMFF ``ftyp`` box at bytes 4..8. All rendering is
headless (Agg).
"""

from __future__ import annotations

import os

import pytest

pytest.importorskip("matplotlib")
pytest.importorskip("PIL")

from central_finite_curve.adapters import animate, cli
from central_finite_curve.adapters.viz import OptionalDependencyError
from central_finite_curve.core.config import CurveConfig

_GIF_SIGNATURES = (b"GIF87a", b"GIF89a")
_MIN_BYTES = 1024

# Small render config shared by the tests to keep them fast.
_SMALL = CurveConfig(n_universes=400, walk_steps=150, seed=137)
_FAST = dict(frames=5, fps=4)


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


# ---------------------------------------------------------------------------
# Walk GIF (matplotlib + Pillow -> runs on the venv)
# ---------------------------------------------------------------------------

def test_save_walk_gif(tmp_path) -> None:
    path = str(tmp_path / "walk.gif")
    out = animate.save_walk_gif(path, config=_SMALL, **_FAST)
    assert out == path
    _assert_valid_gif(path)


def test_cli_animate_writes_walk_gif(tmp_path) -> None:
    outdir = str(tmp_path / "anim")
    text = cli.run_cli(["animate", outdir, "--universes", "400", "--walk-steps", "150"])
    assert "ANIMATE" in text
    files = sorted(os.listdir(outdir))
    assert files == ["central_finite_curve_walk.gif"]
    _assert_valid_gif(os.path.join(outdir, "central_finite_curve_walk.gif"))


def test_walk_gif_validates_arguments() -> None:
    with pytest.raises(ValueError):
        animate.save_walk_gif("unused.gif", config=_SMALL, frames=0)
    with pytest.raises(ValueError):
        animate.save_walk_gif("unused.gif", config=_SMALL, fps=0)


# ---------------------------------------------------------------------------
# MP4 export (matplotlib + ffmpeg -> skip when ffmpeg writer unavailable)
# ---------------------------------------------------------------------------

def _require_ffmpeg() -> None:
    if not animate.ffmpeg_is_available():
        pytest.skip("ffmpeg writer unavailable (no ffmpeg binary on PATH)")


def test_save_walk_mp4(tmp_path) -> None:
    _require_ffmpeg()
    path = str(tmp_path / "walk.mp4")
    out = animate.save_walk_mp4(path, config=_SMALL, **_FAST)
    assert out == path
    _assert_valid_mp4(path)


def test_cli_animate_mp4_flag_writes_gif_and_mp4(tmp_path) -> None:
    _require_ffmpeg()
    outdir = str(tmp_path / "mp4")
    text = cli.run_cli(
        ["animate", outdir, "--universes", "400", "--walk-steps", "150", "--mp4"]
    )
    assert "Rendered MP4" in text
    files = set(os.listdir(outdir))
    assert {"central_finite_curve_walk.gif", "central_finite_curve_walk.mp4"} <= files
    _assert_valid_mp4(os.path.join(outdir, "central_finite_curve_walk.mp4"))


# ---------------------------------------------------------------------------
# Negative test: ffmpeg forced unavailable -> OptionalDependencyError
# ---------------------------------------------------------------------------

def test_mp4_raises_when_ffmpeg_unavailable(tmp_path, monkeypatch) -> None:
    import shutil

    monkeypatch.setattr(shutil, "which", lambda _name: None)
    assert animate.ffmpeg_is_available() is False
    with pytest.raises(OptionalDependencyError):
        animate.save_walk_mp4(str(tmp_path / "nope.mp4"), config=_SMALL, **_FAST)
