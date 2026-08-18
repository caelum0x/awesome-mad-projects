"""Tests for the four-lens composite explainer (gojo_infinity.adapters.animate_lenses).

DEFERRED behind the matplotlib / Pillow / ffmpeg guards, so they behave correctly
on both interpreters:

    * The composite **GIF** needs matplotlib AND Pillow -> the module gate uses
      ``pytest.importorskip`` for both, so the whole module SKIPS on the
      stdlib-only system interpreter and RUNS on the venv.
    * The **MP4** test needs matplotlib AND an ffmpeg binary. It skips (via
      :func:`pytest.skip`) when the ffmpeg writer is unavailable, else renders a
      short clip and validates the ISO-BMFF ``ftyp`` box.
    * The **negative** test forces ffmpeg unavailable (monkeypatching
      :func:`shutil.which` -> ``None``) and asserts :func:`save_four_lenses_mp4`
      raises :class:`OptionalDependencyError`.
    * A pure-ish check asserts the panels source the REAL core values (the Zeno
      ``S_n`` sequence equals :func:`gojo_infinity.core.partial_sum`, the topology
      component counts equal :func:`gojo_infinity.core.component_count`).

Every animation is rendered SHORT (a handful of frames, low fps) into ``tmp_path``
so the suite stays fast. GIFs are validated by their magic signature (``GIF87a`` /
``GIF89a``); MP4s by the ``ftyp`` box at bytes 4..8. All rendering is headless
(Agg).
"""

from __future__ import annotations

import os

import pytest

pytest.importorskip("matplotlib")
pytest.importorskip("PIL")

from gojo_infinity.adapters import animate, animate_lenses, cli  # noqa: E402
from gojo_infinity.adapters.viz import OptionalDependencyError  # noqa: E402
from gojo_infinity.core import component_count, partial_sum  # noqa: E402

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


def _require_ffmpeg() -> None:
    if not animate.ffmpeg_is_available():
        pytest.skip("ffmpeg writer unavailable (no ffmpeg binary on PATH)")


# ---------------------------------------------------------------------------
# Pure-ish check: the panels source the REAL pure core (no matplotlib needed)
# ---------------------------------------------------------------------------

def test_frame_data_sources_real_core() -> None:
    data = animate_lenses.four_lens_frame_data(6)
    assert data.active == 6
    # Panel 1: the S_n sequence used equals zeno's exact partial sums.
    assert data.zeno_S == [float(partial_sum(n)) for n in range(1, 7)]
    # Panel 4: the component counts equal the topology core (1 intact -> 2 cut).
    expected = [
        component_count(data.topo_x0, data.topo_x1,
                        None if p < data.topo_cut_frame else data.topo_cut)
        for p in range(6)
    ]
    assert data.topo_components == expected
    assert data.topo_components[0] == 1 and data.topo_components[-1] == 2
    # Panel 3: felt geodesic length climbs monotonically toward +infinity.
    assert all(b > a for a, b in zip(data.riem_felt, data.riem_felt[1:]))


def test_frame_data_validates_arguments() -> None:
    with pytest.raises(ValueError):
        animate_lenses.four_lens_frame_data(0)


# ---------------------------------------------------------------------------
# GIF (matplotlib + Pillow -> runs on the venv)
# ---------------------------------------------------------------------------

def test_save_four_lenses_gif(tmp_path) -> None:
    path = str(tmp_path / "four_lenses.gif")
    out = animate_lenses.save_four_lenses_gif(path, frames=5, hold=2, fps=4)
    assert out == path
    _assert_valid_gif(path)


def test_cli_animate_lenses_flag_writes_composite_gif(tmp_path) -> None:
    outdir = str(tmp_path / "lenses")
    text = cli.run(["animate", outdir, "--lenses"])
    assert "ANIMATIONS" in text
    files = set(os.listdir(outdir))
    assert "gojo_four_lenses.gif" in files
    _assert_valid_gif(os.path.join(outdir, "gojo_four_lenses.gif"))


def test_gif_validates_arguments() -> None:
    with pytest.raises(ValueError):
        animate_lenses.save_four_lenses_gif("unused.gif", frames=0)
    with pytest.raises(ValueError):
        animate_lenses.save_four_lenses_gif("unused.gif", fps=0)


# ---------------------------------------------------------------------------
# MP4 (matplotlib + ffmpeg -> skip when ffmpeg writer unavailable)
# ---------------------------------------------------------------------------

def test_save_four_lenses_mp4(tmp_path) -> None:
    _require_ffmpeg()
    path = str(tmp_path / "four_lenses.mp4")
    out = animate_lenses.save_four_lenses_mp4(path, frames=5, hold=2, fps=4)
    assert out == path
    _assert_valid_mp4(path)


# ---------------------------------------------------------------------------
# Negative test: ffmpeg forced unavailable -> OptionalDependencyError
# ---------------------------------------------------------------------------

def test_mp4_raises_when_ffmpeg_unavailable(tmp_path, monkeypatch) -> None:
    import shutil

    monkeypatch.setattr(shutil, "which", lambda _name: None)
    assert animate.ffmpeg_is_available() is False
    with pytest.raises(OptionalDependencyError):
        animate_lenses.save_four_lenses_mp4(
            str(tmp_path / "nope.mp4"), frames=3, hold=1, fps=4
        )


def test_mp4_validates_arguments() -> None:
    with pytest.raises(ValueError):
        animate_lenses.save_four_lenses_mp4("unused.mp4", fps=0)
