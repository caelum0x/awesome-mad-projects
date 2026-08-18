"""Tests for the animated GIF renderers (gojo_infinity.adapters.animate).

DEFERRED behind BOTH the matplotlib and Pillow guards: SKIP on the stdlib-only
system interpreter, RUN + PASS on the venv. Each test starts with
``pytest.importorskip`` for matplotlib AND PIL so the whole module skips when
either is absent. A SHORT animation (few frames, low fps) is rendered headless
(Agg) into ``tmp_path``; each GIF is validated by its magic signature
(``GIF87a`` / ``GIF89a``) and a > 1 KiB size. Frame counts are kept tiny so the
tests stay fast.
"""

from __future__ import annotations

import os

import pytest

pytest.importorskip("matplotlib")
pytest.importorskip("PIL")

from gojo_infinity.adapters import animate, cli  # noqa: E402

_GIF_SIGNATURES = (b"GIF87a", b"GIF89a")
_MIN_GIF_BYTES = 1024


def _assert_valid_gif(path: str) -> None:
    assert os.path.exists(path), f"expected GIF at {path}"
    with open(path, "rb") as handle:
        head = handle.read(6)
    assert head in _GIF_SIGNATURES, f"file does not begin with a GIF signature: {head!r}"
    assert os.path.getsize(path) > _MIN_GIF_BYTES, "GIF is suspiciously small (< 1 KiB)"


def test_save_geodesic_approach_gif(tmp_path) -> None:
    path = str(tmp_path / "approach.gif")
    out = animate.save_geodesic_approach_gif(path, frames=5, fps=4, target_radius=0.1)
    assert out == path
    _assert_valid_gif(path)


def test_save_never_arrives_gif(tmp_path) -> None:
    path = str(tmp_path / "never.gif")
    out = animate.save_never_arrives_gif(path, max_n=6, fps=4)
    assert out == path
    _assert_valid_gif(path)


def test_cli_animate_writes_two_gifs(tmp_path) -> None:
    outdir = str(tmp_path / "gifs")
    written = cli.export_gifs(outdir)
    assert len(written) == 2
    for path in written:
        _assert_valid_gif(path)


def test_cli_animate_subcommand(tmp_path) -> None:
    outdir = str(tmp_path / "viacli")
    text = cli.run(["animate", outdir])
    assert "ANIMATIONS" in text
    assert os.path.isdir(outdir)
    assert len(os.listdir(outdir)) == 2


def test_renderers_validate_arguments() -> None:
    with pytest.raises(ValueError):
        animate.save_geodesic_approach_gif("unused.gif", frames=0)
    with pytest.raises(ValueError):
        animate.save_never_arrives_gif("unused.gif", max_n=0)
    with pytest.raises(ValueError):
        animate.save_never_arrives_gif("unused.gif", start=1.5)  # start >= x_gojo
