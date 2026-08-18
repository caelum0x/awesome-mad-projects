"""Tests for the rotating 3-D GIF and the MP4 exporters.

DEFERRED behind the matplotlib / Pillow / ffmpeg guards, so these behave
correctly on both interpreters:

    * The rotating 3-D **GIF** needs matplotlib AND Pillow -> the whole GIF test
      module gate uses ``pytest.importorskip`` for both, so it SKIPS on the
      stdlib-only system interpreter and RUNS on the venv.
    * The **MP4** tests need matplotlib AND an ffmpeg binary. They
      ``importorskip`` matplotlib, then :func:`pytest.skip` when the ffmpeg writer
      is unavailable. On this machine ffmpeg 8.x is on PATH, so they RUN on the
      venv.
    * The **negative** test forces ffmpeg unavailable (monkeypatching
      :func:`shutil.which` to ``None``) and asserts the MP4 savers raise
      :class:`OptionalDependencyError` -- a real deferred-dependency check.

Every animation is rendered SHORT (a handful of frames, low fps) into
``tmp_path`` so the suite stays fast. GIFs are validated by their magic
signature (``GIF87a`` / ``GIF89a``); MP4s by the ISO-BMFF ``ftyp`` box at bytes
4..8. All rendering is headless (Agg).
"""

from __future__ import annotations

import os

import pytest

pytest.importorskip("matplotlib")
pytest.importorskip("PIL")

from gojo_infinity.adapters import animate, animate_3d, cli  # noqa: E402
from gojo_infinity.adapters.viz import OptionalDependencyError  # noqa: E402

_GIF_SIGNATURES = (b"GIF87a", b"GIF89a")
_MIN_BYTES = 1024


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

def test_save_geodesic_3d_rotating_gif(tmp_path) -> None:
    path = str(tmp_path / "rotating.gif")
    out = animate_3d.save_geodesic_3d_rotating_gif(
        path, frames=6, fps=4, max_steps=1500
    )
    assert out == path
    _assert_valid_gif(path)


def test_cli_animate_rotate_flag_writes_three_gifs(tmp_path) -> None:
    outdir = str(tmp_path / "rotate")
    text = cli.run(["animate", outdir, "--rotate"])
    assert "ANIMATIONS" in text
    files = sorted(os.listdir(outdir))
    assert files == [
        "gojo_geodesic_3d_rotating.gif",
        "gojo_geodesic_approach.gif",
        "gojo_never_arrives.gif",
    ]


def test_rotating_gif_validates_arguments() -> None:
    with pytest.raises(ValueError):
        animate_3d.save_geodesic_3d_rotating_gif("unused.gif", frames=0)
    with pytest.raises(ValueError):
        animate_3d.save_geodesic_3d_rotating_gif("unused.gif", fps=0)


# ---------------------------------------------------------------------------
# MP4 exports (matplotlib + ffmpeg -> skip when ffmpeg writer unavailable)
# ---------------------------------------------------------------------------

def _require_ffmpeg() -> None:
    if not animate.ffmpeg_is_available():
        pytest.skip("ffmpeg writer unavailable (no ffmpeg binary on PATH)")


def test_save_geodesic_approach_mp4(tmp_path) -> None:
    _require_ffmpeg()
    path = str(tmp_path / "approach.mp4")
    out = animate.save_geodesic_approach_mp4(
        path, frames=5, fps=4, target_radius=0.1
    )
    assert out == path
    _assert_valid_mp4(path)


def test_save_geodesic_3d_rotating_mp4(tmp_path) -> None:
    _require_ffmpeg()
    path = str(tmp_path / "rotating.mp4")
    out = animate_3d.save_geodesic_3d_rotating_mp4(
        path, frames=6, fps=4, max_steps=1500
    )
    assert out == path
    _assert_valid_mp4(path)


def test_cli_animate_mp4_flag_writes_gifs_and_mp4s(tmp_path) -> None:
    _require_ffmpeg()
    outdir = str(tmp_path / "mp4")
    text = cli.run(["animate", outdir, "--mp4"])
    assert "Rendered MP4s" in text
    files = set(os.listdir(outdir))
    assert {
        "gojo_geodesic_approach.gif",
        "gojo_never_arrives.gif",
        "gojo_geodesic_approach.mp4",
        "gojo_geodesic_3d_rotating.mp4",
    } <= files
    _assert_valid_mp4(os.path.join(outdir, "gojo_geodesic_approach.mp4"))
    _assert_valid_mp4(os.path.join(outdir, "gojo_geodesic_3d_rotating.mp4"))


# ---------------------------------------------------------------------------
# Negative test: ffmpeg forced unavailable -> OptionalDependencyError
# ---------------------------------------------------------------------------

def test_mp4_raises_when_ffmpeg_unavailable(tmp_path, monkeypatch) -> None:
    # Force shutil.which("ffmpeg") -> None so the availability probe fails, even
    # though ffmpeg is really installed here.
    import shutil

    monkeypatch.setattr(shutil, "which", lambda _name: None)
    assert animate.ffmpeg_is_available() is False

    with pytest.raises(OptionalDependencyError):
        animate.save_geodesic_approach_mp4(
            str(tmp_path / "nope.mp4"), frames=3, fps=4, target_radius=0.1
        )
    with pytest.raises(OptionalDependencyError):
        animate_3d.save_geodesic_3d_rotating_mp4(
            str(tmp_path / "nope3d.mp4"), frames=3, fps=4, max_steps=1000
        )


def test_mp4_validates_arguments() -> None:
    with pytest.raises(ValueError):
        animate.save_geodesic_approach_mp4("unused.mp4", fps=0)
    with pytest.raises(ValueError):
        animate_3d.save_geodesic_3d_rotating_mp4("unused.mp4", fps=0)
