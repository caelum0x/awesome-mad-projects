"""Tests for the rotating 3-D Mobius animation (GIF + MP4 exporters).

DEFERRED behind the matplotlib / Pillow / ffmpeg guards, so these behave correctly
on both interpreters:

    * The rotating 3-D **GIF** needs matplotlib AND Pillow -> the whole GIF test
      module gate uses ``pytest.importorskip`` for both, so it SKIPS on the
      stdlib-only system interpreter and RUNS on the venv.
    * The **MP4** tests need matplotlib AND an ffmpeg binary. They ``importorskip``
      matplotlib, then :func:`pytest.skip` when the ffmpeg writer is unavailable. On
      this machine ffmpeg 8.x is on PATH, so they RUN on the venv.
    * The **negative** test forces ffmpeg unavailable (monkeypatching
      :func:`shutil.which` to ``None``) and asserts the MP4 saver raises
      :class:`OptionalDependencyError` -- a real deferred-dependency check.

Every animation is rendered SHORT (a handful of frames, low fps, small trace/ridge
samples and a coarse surface) into ``tmp_path`` so the suite stays fast. GIFs are
validated by their magic signature (``GIF87a`` / ``GIF89a``); MP4s by the ISO-BMFF
``ftyp`` box at bytes 4..8. All rendering is headless (Agg).
"""

from __future__ import annotations

import os

import pytest

pytest.importorskip("matplotlib")
pytest.importorskip("PIL")

from mobius_rickness.adapters import animate_3d, cli  # noqa: E402
from mobius_rickness.adapters.viz import OptionalDependencyError  # noqa: E402

_GIF_SIGNATURES = (b"GIF87a", b"GIF89a")
_MIN_BYTES = 1024

# Small render parameters shared by the tests to keep them fast.
_FAST = dict(
    frames=5,
    fps=4,
    n_u_surface=30,
    n_v_surface=9,
    cfc_n_u=40,
    cfc_n_v_samples=60,
    ridge_n_u=8,
    ridge_n_v=3,
)


def _assert_valid_gif(path: str) -> None:
    assert os.path.exists(path), f"expected GIF at {path}"
    with open(path, "rb") as handle:
        head = handle.read(6)
    assert head in _GIF_SIGNATURES, f"not a GIF signature: {head!r}"
    assert os.path.getsize(path) > _MIN_BYTES, "GIF is suspiciously small (< 1 KiB)"


def _assert_valid_mp4(path: str) -> None:
    assert os.path.exists(path), f"expected MP4 at {path}"
    with open(path, "rb") as handle:
        head = handle.read(12)
    assert head[4:8] == b"ftyp", f"not an ISO-BMFF/MP4 (bytes 4..8): {head[4:8]!r}"
    assert os.path.getsize(path) > _MIN_BYTES, "MP4 is suspiciously small (< 1 KiB)"


# ---------------------------------------------------------------------------
# Rotating 3-D GIF (matplotlib + Pillow -> runs on the venv)
# ---------------------------------------------------------------------------

def test_save_mobius_rotating_gif(tmp_path) -> None:
    path = str(tmp_path / "rotating.gif")
    out = animate_3d.save_mobius_rotating_gif(path, **_FAST)
    assert out == path
    _assert_valid_gif(path)


def test_cli_animate_writes_rotating_gif(tmp_path) -> None:
    outdir = str(tmp_path / "anim")
    text = cli.run(["animate", outdir])
    assert "ANIMATE" in text
    files = sorted(os.listdir(outdir))
    assert files == ["mobius_rotating.gif"]
    _assert_valid_gif(os.path.join(outdir, "mobius_rotating.gif"))


def test_rotating_gif_validates_arguments() -> None:
    with pytest.raises(ValueError):
        animate_3d.save_mobius_rotating_gif("unused.gif", frames=0)
    with pytest.raises(ValueError):
        animate_3d.save_mobius_rotating_gif("unused.gif", fps=0)


def test_rotating_gif_still_renders_without_numpy_ridge(tmp_path, monkeypatch) -> None:
    # When the ridge backend cannot run (numpy absent), the ridge overlay is skipped
    # but the strip surface + R^-1(0) zero curve must still render to a valid GIF.
    from mobius_rickness.ridge import OptionalDependencyError as RidgeError

    def _raise(*args, **kwargs):
        raise RidgeError("simulated: ridge backend unavailable")

    monkeypatch.setattr("mobius_rickness.ridge.trace_mobius_ridge", _raise)
    path = str(tmp_path / "rotating_noridge.gif")
    out = animate_3d.save_mobius_rotating_gif(path, **_FAST)
    assert out == path
    _assert_valid_gif(path)


# ---------------------------------------------------------------------------
# MP4 export (matplotlib + ffmpeg -> skip when ffmpeg writer unavailable)
# ---------------------------------------------------------------------------

def _require_ffmpeg() -> None:
    if not animate_3d.ffmpeg_is_available():
        pytest.skip("ffmpeg writer unavailable (no ffmpeg binary on PATH)")


def test_save_mobius_rotating_mp4(tmp_path) -> None:
    _require_ffmpeg()
    path = str(tmp_path / "rotating.mp4")
    out = animate_3d.save_mobius_rotating_mp4(path, **_FAST)
    assert out == path
    _assert_valid_mp4(path)


def test_cli_animate_mp4_flag_writes_gif_and_mp4(tmp_path) -> None:
    _require_ffmpeg()
    outdir = str(tmp_path / "mp4")
    text = cli.run(["animate", outdir, "--mp4"])
    assert "Rendered MP4" in text
    files = set(os.listdir(outdir))
    assert {"mobius_rotating.gif", "mobius_rotating.mp4"} <= files
    _assert_valid_mp4(os.path.join(outdir, "mobius_rotating.mp4"))


# ---------------------------------------------------------------------------
# Negative test: ffmpeg forced unavailable -> OptionalDependencyError
# ---------------------------------------------------------------------------

def test_mp4_raises_when_ffmpeg_unavailable(tmp_path, monkeypatch) -> None:
    # Force shutil.which("ffmpeg") -> None so the availability probe fails, even
    # though ffmpeg is really installed here.
    import shutil

    monkeypatch.setattr(shutil, "which", lambda _name: None)
    assert animate_3d.ffmpeg_is_available() is False

    with pytest.raises(OptionalDependencyError):
        animate_3d.save_mobius_rotating_mp4(str(tmp_path / "nope.mp4"), **_FAST)


def test_mp4_validates_arguments() -> None:
    with pytest.raises(ValueError):
        animate_3d.save_mobius_rotating_mp4("unused.mp4", fps=0)
