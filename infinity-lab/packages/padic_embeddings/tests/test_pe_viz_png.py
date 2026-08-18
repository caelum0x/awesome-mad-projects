"""Tests for the OPTIONAL matplotlib PNG export (padic_embeddings.adapters.viz).

DEFERRED behind ``commons.core.optional.try_import``: with no matplotlib installed the
exporter raises :class:`viz.OptionalDependencyError` rather than failing at import
time. This module ``importorskip("matplotlib")`` so it SKIPS on the
numpy/matplotlib-free system interpreter and RUNS on the venv.

matplotlib is forced onto the headless ``Agg`` backend by the renderer, so no display
is needed. Each test renders a small distance matrix to ``tmp_path`` and asserts the
file exists, begins with the 8-byte PNG signature, and is non-trivially sized. No PNGs
are committed -- they live only under the pytest tmp dir.
"""

from __future__ import annotations

import os

import pytest

pytest.importorskip("matplotlib")

from padic_embeddings.adapters import cli, viz

_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_MIN_PNG_BYTES = 1024
_COORDS = [1, 3, 5, 8, 16, 17, 24, 32]


def _assert_valid_png(path: str) -> None:
    assert os.path.exists(path), f"expected a rendered PNG at {path}"
    size = os.path.getsize(path)
    assert size > _MIN_PNG_BYTES, f"PNG too small ({size} bytes) at {path}"
    with open(path, "rb") as handle:
        header = handle.read(8)
    assert header == _PNG_SIGNATURE, f"not a PNG signature at {path}: {header!r}"


def test_save_distance_matrix_png_writes_valid_png(tmp_path) -> None:
    target = str(tmp_path / "matrix.png")
    out = viz.save_distance_matrix_png(target, _COORDS, 2)
    assert out == target
    _assert_valid_png(target)


def test_empty_coords_rejected() -> None:
    with pytest.raises(ValueError):
        viz.save_distance_matrix_png("unused.png", [], 2)


def test_cli_png_option_writes_matrix(tmp_path) -> None:
    outdir = tmp_path / "pngs"
    out = cli.run_cli(["--p", "2", "--ints", "8", "16", "32", "48", "--png", str(outdir)])
    assert "PNG export written" in out
    target = str(outdir / viz.DISTANCE_MATRIX_PNG)
    assert target in out
    _assert_valid_png(target)
