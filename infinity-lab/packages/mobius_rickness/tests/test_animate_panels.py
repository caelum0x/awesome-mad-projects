"""Tests for the four-panel composite explainer (mobius_rickness.adapters.animate_panels).

DEFERRED and layered so the suite behaves on both interpreters:

    * The composite **GIF** needs matplotlib AND Pillow AND numpy -> the module
      gate uses ``pytest.importorskip`` for all three, so the whole module SKIPS on
      the stdlib-only system interpreter and RUNS on the venv.
    * The **MP4** test additionally requires an ffmpeg writer; it skips (via
      :func:`pytest.skip`) when the ffmpeg writer is unavailable, else renders a
      short clip and validates the ISO-BMFF ``ftyp`` box.
    * The **negative** test forces ffmpeg unavailable (monkeypatching
      :func:`shutil.which` -> ``None``) and asserts :func:`save_four_panels_mp4`
      raises :class:`OptionalDependencyError`.
    * A pure-ish check asserts the panels source the REAL core values: the torus
      ``K = 0`` marks equal ``(pi/2, 3*pi/2)`` from :func:`zero_circles`, the torus
      scan reproduces :func:`gaussian_curvature_closed` and changes sign, the K
      sign-map uses the core ``K < 0`` (via :func:`evaluate_grid`), and Panel 1's
      three curvature paths agree.

Every animation is rendered SHORT (a handful of frames, tiny grids/seed counts)
into ``tmp_path`` so the suite stays fast. GIFs are validated by their magic
signature (``GIF87a`` / ``GIF89a``); MP4s by the ``ftyp`` box at bytes 4..8. All
rendering is headless (Agg).
"""

from __future__ import annotations

import math
import os

import pytest

pytest.importorskip("matplotlib")
pytest.importorskip("PIL")
pytest.importorskip("numpy")

from mobius_rickness.adapters import animate_panels, cli  # noqa: E402
from mobius_rickness.adapters.viz import OptionalDependencyError  # noqa: E402
from mobius_rickness.core import (  # noqa: E402
    evaluate_grid,
    gaussian_curvature_closed,
    zero_circles,
)

_GIF_SIGNATURES = (b"GIF87a", b"GIF89a")
_MIN_BYTES = 1024

# Small render parameters shared by the animation tests to keep them fast.
_FAST = dict(
    frames=5,
    hold=2,
    fps=4,
    grid_n_u=13,
    grid_n_v=7,
    trace_n_u=16,
    trace_n_v_samples=40,
    seed_n_u=5,
    seed_n_v=2,
    scms_tol=1e-6,
    scms_max_iter=20,
    curve_samples=24,
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


def _require_ffmpeg() -> None:
    from mobius_rickness.adapters.animate_3d import ffmpeg_is_available

    if not ffmpeg_is_available():
        pytest.skip("ffmpeg writer unavailable (no ffmpeg binary on PATH)")


# ---------------------------------------------------------------------------
# Pure-ish check: the panels source the REAL pure core
# ---------------------------------------------------------------------------

def test_frame_data_sources_real_core() -> None:
    data = animate_panels.four_panel_frame_data(
        6, curve_samples=24, trace_n_u=16, trace_n_v_samples=40
    )
    assert data.active == 6

    # Panel 4: the torus K=0 marks equal (pi/2, 3pi/2) from core zero_circles().
    assert data.p4_zero_circles == zero_circles()
    assert math.isclose(data.p4_zero_circles[0], math.pi / 2.0)
    assert math.isclose(data.p4_zero_circles[1], 3.0 * math.pi / 2.0)
    # ... and the torus scan reproduces the closed-form K(theta) and changes sign.
    for theta, k in zip(data.p4_scan_theta, data.p4_scan_k):
        assert k == gaussian_curvature_closed(theta)
    assert max(data.p4_k) > 0.0 and min(data.p4_k) < 0.0, "torus K must change sign"

    # Panel 1: the K sign-map uses the core K < 0 certificate (worst interior K < 0)
    # and the three curvature paths agree at every scan position.
    assert data.p1_k_worst < 0.0
    assert all(k < 0.0 for k in data.p1_k_analytic), "Mobius K < 0 everywhere"
    assert all(delta < 1e-4 for delta in data.p1_max_delta), "three paths must agree"

    # The background K field the renderer uses is the same pure core grid, all < 0.
    grid = evaluate_grid(n_u=13, n_v=7)
    assert all(k < 0.0 for row in grid.K for k in row), "core K < 0 on the grid"

    # Panel 2: the zero-set reveal is monotone and ends fully revealed.
    assert data.p2_reveal[-1] == len(data.p2_curve_u)
    assert all(b >= a for a, b in zip(data.p2_reveal, data.p2_reveal[1:]))


def test_frame_data_validates_arguments() -> None:
    with pytest.raises(ValueError):
        animate_panels.four_panel_frame_data(0)


# ---------------------------------------------------------------------------
# GIF (matplotlib + Pillow + numpy -> runs on the venv)
# ---------------------------------------------------------------------------

def test_save_four_panels_gif(tmp_path) -> None:
    path = str(tmp_path / "four_panels.gif")
    out = animate_panels.save_four_panels_gif(path, **_FAST)
    assert out == path
    _assert_valid_gif(path)


def test_cli_animate_panels_flag_writes_composite_gif(tmp_path) -> None:
    outdir = str(tmp_path / "panels")
    text = cli.run(["animate", outdir, "--panels"])
    assert "four-panel explainer GIF" in text
    files = set(os.listdir(outdir))
    assert {"mobius_rotating.gif", "mobius_four_panels.gif"} <= files
    _assert_valid_gif(os.path.join(outdir, "mobius_four_panels.gif"))


def test_gif_validates_arguments() -> None:
    with pytest.raises(ValueError):
        animate_panels.save_four_panels_gif("unused.gif", frames=0)
    with pytest.raises(ValueError):
        animate_panels.save_four_panels_gif("unused.gif", hold=-1)
    with pytest.raises(ValueError):
        animate_panels.save_four_panels_gif("unused.gif", fps=0)


# ---------------------------------------------------------------------------
# MP4 (matplotlib + numpy + ffmpeg -> skip when ffmpeg writer unavailable)
# ---------------------------------------------------------------------------

def test_save_four_panels_mp4(tmp_path) -> None:
    _require_ffmpeg()
    path = str(tmp_path / "four_panels.mp4")
    out = animate_panels.save_four_panels_mp4(path, **_FAST)
    assert out == path
    _assert_valid_mp4(path)


# ---------------------------------------------------------------------------
# Negative test: ffmpeg forced unavailable -> OptionalDependencyError
# ---------------------------------------------------------------------------

def test_mp4_raises_when_ffmpeg_unavailable(tmp_path, monkeypatch) -> None:
    import shutil

    from mobius_rickness.adapters.animate_3d import ffmpeg_is_available

    monkeypatch.setattr(shutil, "which", lambda _name: None)
    assert ffmpeg_is_available() is False
    with pytest.raises(OptionalDependencyError):
        animate_panels.save_four_panels_mp4(str(tmp_path / "nope.mp4"), **_FAST)


def test_mp4_validates_arguments() -> None:
    with pytest.raises(ValueError):
        animate_panels.save_four_panels_mp4("unused.mp4", fps=0)
