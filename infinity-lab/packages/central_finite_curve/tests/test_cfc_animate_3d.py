"""Tests for the rotating 3-D projection animation (central_finite_curve.adapters.animate_3d).

DEFERRED behind the matplotlib / Pillow / ffmpeg guards, so these behave correctly on
both interpreters:

    * The rotating 3-D **GIF** needs matplotlib AND Pillow -> the whole module gate
      uses ``pytest.importorskip`` for both, so it SKIPS on the stdlib-only system
      interpreter and RUNS on the venv.
    * The **MP4** tests need matplotlib AND an ffmpeg binary; they :func:`pytest.skip`
      when the ffmpeg writer is unavailable, else render a short clip and validate the
      ISO-BMFF ``ftyp`` box.
    * The **negative** test forces ffmpeg unavailable (monkeypatching
      :func:`shutil.which` -> ``None``) and asserts :func:`save_cfc_rotating_mp4`
      raises :class:`OptionalDependencyError`.
    * A "sources real core" check asserts the 3-D scene draws its band size and
      acceptance from the genuine core under a fixed seed.

Every animation is rendered SHORT (a handful of frames, a tiny pipeline, a small
background cap) into ``tmp_path`` so the suite stays fast. GIFs are validated by their
magic signature; MP4s by the ``ftyp`` box at bytes 4..8. All rendering is headless
(Agg).
"""

from __future__ import annotations

import os

import pytest

pytest.importorskip("matplotlib")
pytest.importorskip("PIL")

from central_finite_curve.adapters import animate_3d, cli  # noqa: E402
from central_finite_curve.adapters.viz import OptionalDependencyError  # noqa: E402
from central_finite_curve.core.config import CurveConfig  # noqa: E402
from central_finite_curve.core.pipeline import run  # noqa: E402

_GIF_SIGNATURES = (b"GIF87a", b"GIF89a")
_MIN_BYTES = 1024

_SMALL = CurveConfig(n_universes=400, walk_steps=150, seed=137)
_FAST = dict(max_background=300, frames=5, fps=4)


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
    if not animate_3d.ffmpeg_is_available():
        pytest.skip("ffmpeg writer unavailable (no ffmpeg binary on PATH)")


# ---------------------------------------------------------------------------
# Sources the REAL pure core (pure projector, no matplotlib call)
# ---------------------------------------------------------------------------

def test_rotating_scene_sources_real_core() -> None:
    scene = animate_3d.rotating_scene_data(config=_SMALL, max_background=300)
    result = run(_SMALL, project=False)

    assert scene.curve_size == result.curve.size
    assert scene.total == result.curve.total == _SMALL.n_universes
    assert scene.acceptance_rate == result.walk.acceptance_rate
    # The highlighted band holds exactly the curve members (all three coord lists).
    assert len(scene.band_x) == result.curve.size
    assert len(scene.band_y) == len(scene.band_z) == result.curve.size
    # The walk overlay holds one 3-D point per walk state.
    assert len(scene.walk_x) == len(result.walk.points)
    # The faint background is strided down to the cap.
    assert len(scene.bg_x) <= 300


def test_rotating_scene_validates_arguments() -> None:
    with pytest.raises(ValueError):
        animate_3d.rotating_scene_data(config=_SMALL, max_background=0)


# ---------------------------------------------------------------------------
# Rotating 3-D GIF (matplotlib + Pillow -> runs on the venv)
# ---------------------------------------------------------------------------

def test_save_cfc_rotating_gif(tmp_path) -> None:
    path = str(tmp_path / "rotating.gif")
    out = animate_3d.save_cfc_rotating_gif(path, config=_SMALL, **_FAST)
    assert out == path
    _assert_valid_gif(path)


def test_cli_animate_rotate_flag_writes_rotating_gif(tmp_path) -> None:
    outdir = str(tmp_path / "rot")
    text = cli.run_cli(
        ["animate", outdir, "--rotate", "--universes", "400", "--walk-steps", "150"]
    )
    assert "rotating 3-D GIF" in text
    files = set(os.listdir(outdir))
    assert {
        "central_finite_curve_walk.gif",
        "central_finite_curve_rotating_3d.gif",
    } <= files
    _assert_valid_gif(os.path.join(outdir, "central_finite_curve_rotating_3d.gif"))


def test_rotating_gif_validates_arguments() -> None:
    with pytest.raises(ValueError):
        animate_3d.save_cfc_rotating_gif("unused.gif", config=_SMALL, frames=0)
    with pytest.raises(ValueError):
        animate_3d.save_cfc_rotating_gif("unused.gif", config=_SMALL, fps=0)


# ---------------------------------------------------------------------------
# MP4 (matplotlib + ffmpeg -> skip when ffmpeg writer unavailable)
# ---------------------------------------------------------------------------

def test_save_cfc_rotating_mp4(tmp_path) -> None:
    _require_ffmpeg()
    path = str(tmp_path / "rotating.mp4")
    out = animate_3d.save_cfc_rotating_mp4(path, config=_SMALL, **_FAST)
    assert out == path
    _assert_valid_mp4(path)


# ---------------------------------------------------------------------------
# Negative test: ffmpeg forced unavailable -> OptionalDependencyError
# ---------------------------------------------------------------------------

def test_rotating_mp4_raises_when_ffmpeg_unavailable(tmp_path, monkeypatch) -> None:
    import shutil

    monkeypatch.setattr(shutil, "which", lambda _name: None)
    assert animate_3d.ffmpeg_is_available() is False
    with pytest.raises(OptionalDependencyError):
        animate_3d.save_cfc_rotating_mp4(
            str(tmp_path / "nope.mp4"), config=_SMALL, **_FAST
        )


def test_rotating_mp4_validates_arguments() -> None:
    with pytest.raises(ValueError):
        animate_3d.save_cfc_rotating_mp4("unused.mp4", config=_SMALL, fps=0)
