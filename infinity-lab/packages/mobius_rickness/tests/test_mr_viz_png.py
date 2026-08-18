"""Tests for the OPTIONAL matplotlib PNG exports (mobius_rickness.adapters.viz).

These renderers are DEFERRED behind ``commons.core.optional.try_import``: with no
matplotlib installed they must raise :class:`viz.OptionalDependencyError` rather
than fail at import time. Every test here therefore ``importorskip("matplotlib")``
so it SKIPS on the numpy/matplotlib-free system interpreter and RUNS on the venv.

matplotlib is forced onto the headless ``Agg`` backend by the renderers, so no
display is needed. Each test renders to ``tmp_path`` and asserts the output file
exists, begins with the 8-byte PNG signature, and is non-trivially sized
(> 1 KB). No PNGs are committed -- they live only under the pytest tmp dir.
"""

from __future__ import annotations

import pytest

pytest.importorskip("matplotlib")

from mobius_rickness.adapters import cli, viz

# The 8-byte PNG file signature (magic number) every valid PNG starts with.
_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_MIN_PNG_BYTES = 1024


def _assert_valid_png(path: str) -> None:
    """Assert ``path`` is an existing PNG with a valid signature and real size."""
    import os

    assert os.path.exists(path), f"expected a rendered PNG at {path}"
    size = os.path.getsize(path)
    assert size > _MIN_PNG_BYTES, f"PNG too small ({size} bytes) at {path}"
    with open(path, "rb") as handle:
        header = handle.read(8)
    assert header == _PNG_SIGNATURE, f"not a PNG signature at {path}: {header!r}"


# ---------------------------------------------------------------------------
# save_strip_3d_png -- surface + traced R^{-1}(0) line (needs numpy for grids)
# ---------------------------------------------------------------------------

def test_save_strip_3d_png_writes_valid_png(tmp_path) -> None:
    pytest.importorskip("numpy")
    target = str(tmp_path / "strip.png")
    out = viz.save_strip_3d_png(target)
    assert out == target
    _assert_valid_png(target)


# ---------------------------------------------------------------------------
# save_krick_heatmap_png -- K_Rick field + R=0 contour (needs numpy for the field)
# ---------------------------------------------------------------------------

def test_save_krick_heatmap_png_writes_valid_png(tmp_path) -> None:
    pytest.importorskip("numpy")
    target = str(tmp_path / "heatmap.png")
    out = viz.save_krick_heatmap_png(target)
    assert out == target
    _assert_valid_png(target)


# ---------------------------------------------------------------------------
# save_ridge_png -- surface + SCMS ridge overlay (guarded on numpy / ridge dep)
# ---------------------------------------------------------------------------

def test_save_ridge_png_writes_valid_png(tmp_path) -> None:
    target = str(tmp_path / "ridge.png")
    out = viz.save_ridge_png(target)
    assert out == target
    _assert_valid_png(target)


def test_save_ridge_png_still_renders_when_ridge_dep_missing(tmp_path, monkeypatch) -> None:
    # If the ridge backend cannot run (it raises its OptionalDependencyError), the
    # ridge overlay is skipped but the strip surface must still render to a valid
    # PNG -- the numpy/ridge guard the task requires.
    from mobius_rickness.ridge import OptionalDependencyError as RidgeError

    def _raise(*args, **kwargs):
        raise RidgeError("simulated: ridge backend unavailable")

    monkeypatch.setattr("mobius_rickness.ridge.trace_mobius_ridge", _raise)
    target = str(tmp_path / "ridge_guarded.png")
    out = viz.save_ridge_png(target)
    assert out == target
    _assert_valid_png(target)


# ---------------------------------------------------------------------------
# All three exports produce distinct, valid PNG files
# ---------------------------------------------------------------------------

def test_all_three_png_exports_are_distinct(tmp_path) -> None:
    pytest.importorskip("numpy")
    strip = str(tmp_path / "s.png")
    heat = str(tmp_path / "h.png")
    ridge = str(tmp_path / "r.png")
    viz.save_strip_3d_png(strip)
    viz.save_krick_heatmap_png(heat)
    viz.save_ridge_png(ridge)
    for path in (strip, heat, ridge):
        _assert_valid_png(path)
    contents = set()
    for path in (strip, heat, ridge):
        with open(path, "rb") as handle:
            contents.add(handle.read())
    assert len(contents) == 3, "the three renderers must produce distinct images"


# ---------------------------------------------------------------------------
# CLI --png OUTDIR renders the three PNGs and reports their paths
# ---------------------------------------------------------------------------

def test_cli_png_option_writes_all_three(tmp_path) -> None:
    pytest.importorskip("numpy")
    outdir = tmp_path / "pngs"
    out = cli.run(["trace", "--png", str(outdir)])
    assert "PNG exports written" in out
    for filename in ("mobius_strip_cfc.png", "k_rick_heatmap.png", "mobius_ridge.png"):
        target = str(outdir / filename)
        assert target in out
        _assert_valid_png(target)


def test_cli_png_creates_missing_outdir(tmp_path) -> None:
    pytest.importorskip("numpy")
    outdir = tmp_path / "nested" / "deeper"
    cli.run(["curvature", "--png", str(outdir)])
    _assert_valid_png(str(outdir / "k_rick_heatmap.png"))
