"""Tests for the optional matplotlib PNG exporters (gojo_infinity.adapters.viz).

These are DEFERRED behind the matplotlib guard: they must SKIP on the stdlib-only
system interpreter (no matplotlib) and RUN + PASS on the venv interpreter that
has matplotlib. Every test therefore starts with ``pytest.importorskip`` so the
whole module is skipped when matplotlib is absent.

Rendering is headless (Agg backend, selected inside the viz exporters) and writes
to pytest's ``tmp_path``; nothing is committed. Each PNG is validated by its
8-byte signature and a non-trivial file size.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

# Skip the entire module on the stdlib-only interpreter (no matplotlib).
pytest.importorskip("matplotlib")

from gojo_infinity.adapters import cli, viz  # noqa: E402

# The 8-byte PNG file signature (magic number) every valid PNG starts with.
_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_MIN_PNG_BYTES = 1024  # a real chart is comfortably larger than 1 KiB


def _assert_valid_png(path: str) -> None:
    """Assert ``path`` exists, has the PNG signature, and exceeds ``_MIN_PNG_BYTES``."""
    import os

    assert os.path.exists(path), f"expected PNG at {path}"
    with open(path, "rb") as handle:
        head = handle.read(8)
    assert head == _PNG_SIGNATURE, "file does not start with the 8-byte PNG signature"
    assert os.path.getsize(path) > _MIN_PNG_BYTES, "PNG is suspiciously small (< 1 KiB)"


# ---------------------------------------------------------------------------
# Each lens-specific exporter writes a valid PNG
# ---------------------------------------------------------------------------

def test_save_metric_blowup_png(tmp_path) -> None:
    path = str(tmp_path / "metric_blowup.png")
    out = viz.save_metric_blowup_png(path)
    assert out == path
    _assert_valid_png(path)


def test_save_series_convergence_png(tmp_path) -> None:
    path = str(tmp_path / "series_convergence.png")
    out = viz.save_series_convergence_png(path)
    assert out == path
    _assert_valid_png(path)


def test_save_covering_png(tmp_path) -> None:
    path = str(tmp_path / "covering.png")
    out = viz.save_covering_png(path, eps=Fraction(1, 10))
    assert out == path
    _assert_valid_png(path)


def test_generic_convergence_png(tmp_path) -> None:
    path = str(tmp_path / "generic.png")
    out = viz.save_convergence_png([0.5, 0.75, 0.875, 0.9375], 1.0, path)
    assert out == path
    _assert_valid_png(path)


# ---------------------------------------------------------------------------
# CLI --png OUTDIR triggers the exporters
# ---------------------------------------------------------------------------

def test_cli_png_flag_writes_single_lens(tmp_path) -> None:
    outdir = str(tmp_path / "one")
    text = cli.run(["riemannian", "--png", outdir])
    assert "PNG export ->" in text
    _, filename = cli._PNG_EXPORTERS["riemannian"]
    _assert_valid_png(str(tmp_path / "one" / filename))


def test_cli_png_flag_all_writes_three(tmp_path) -> None:
    outdir = str(tmp_path / "all")
    written = cli.export_pngs("all", outdir)
    assert len(written) == 3
    for path in written:
        _assert_valid_png(path)


# ---------------------------------------------------------------------------
# Determinism: re-rendering yields byte-identical PNGs
# ---------------------------------------------------------------------------

def test_metric_blowup_png_is_deterministic(tmp_path) -> None:
    p1 = str(tmp_path / "a.png")
    p2 = str(tmp_path / "b.png")
    viz.save_metric_blowup_png(p1)
    viz.save_metric_blowup_png(p2)
    with open(p1, "rb") as f1, open(p2, "rb") as f2:
        assert f1.read() == f2.read()
