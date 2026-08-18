"""Tests for the 2-D manifold PNG exporters (gojo_infinity.adapters.viz).

DEFERRED behind the matplotlib guard: SKIP on the stdlib-only system interpreter,
RUN + PASS on the venv. Each test starts with ``pytest.importorskip`` so the whole
module skips when matplotlib is absent. Rendering is headless (Agg) into
``tmp_path``; each PNG is validated by its 8-byte signature and size.
"""

from __future__ import annotations

import os

import pytest

pytest.importorskip("matplotlib")

from gojo_infinity.adapters import cli, viz  # noqa: E402

_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_MIN_PNG_BYTES = 1024


def _assert_valid_png(path: str) -> None:
    assert os.path.exists(path), f"expected PNG at {path}"
    with open(path, "rb") as handle:
        head = handle.read(8)
    assert head == _PNG_SIGNATURE, "file does not start with the 8-byte PNG signature"
    assert os.path.getsize(path) > _MIN_PNG_BYTES, "PNG is suspiciously small (< 1 KiB)"


def test_save_geodesic_bundle_png(tmp_path) -> None:
    path = str(tmp_path / "bundle.png")
    out = viz.save_geodesic_bundle_png(path)
    assert out == path
    _assert_valid_png(path)


def test_save_length_divergence_png(tmp_path) -> None:
    path = str(tmp_path / "divergence.png")
    out = viz.save_length_divergence_png(path)
    assert out == path
    _assert_valid_png(path)


def test_cli_manifold_png_writes_two(tmp_path) -> None:
    outdir = str(tmp_path / "manifold")
    written = cli.export_pngs("manifold", outdir)
    assert len(written) == 2
    for path in written:
        _assert_valid_png(path)


def test_cli_manifold_png_flag(tmp_path) -> None:
    outdir = str(tmp_path / "viacli")
    text = cli.run(["manifold", "--png", outdir])
    assert "PNG export ->" in text
    assert "verdict: FORMIDABLE" in text


def test_save_geodesic_3d_png(tmp_path) -> None:
    path = str(tmp_path / "geodesic_3d.png")
    out = viz.save_geodesic_3d_png(path)
    assert out == path
    _assert_valid_png(path)
