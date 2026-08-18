"""Tests for the OPTIONAL matplotlib PNG export (calabi_yau_latent.adapters.viz).

DEFERRED behind ``commons.core.optional.try_import``: with no matplotlib installed
the exporter raises :class:`viz.OptionalDependencyError` rather than failing at
import time. This module ``importorskip("matplotlib")`` so it SKIPS on the
matplotlib-free system interpreter and RUNS on the venv.

matplotlib is forced onto the headless ``Agg`` backend by the renderer, so no
display is needed. Each test renders a SMALL-config torus PNG to ``tmp_path`` and
asserts the file exists, begins with the 8-byte PNG signature, and is
non-trivially sized. No PNGs are committed -- they live only under the pytest tmp
dir.
"""

from __future__ import annotations

import os

import pytest

pytest.importorskip("matplotlib")

from calabi_yau_latent.adapters import cli, viz
from calabi_yau_latent.core.config import CYConfig

_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_MIN_PNG_BYTES = 1024

_SMALL = CYConfig(per_cluster=10, seed=7)


def _assert_valid_png(path: str) -> None:
    assert os.path.exists(path), f"expected a rendered PNG at {path}"
    size = os.path.getsize(path)
    assert size > _MIN_PNG_BYTES, f"PNG too small ({size} bytes) at {path}"
    with open(path, "rb") as handle:
        header = handle.read(8)
    assert header == _PNG_SIGNATURE, f"not a PNG signature at {path}: {header!r}"


def test_save_torus_png_writes_valid_png(tmp_path) -> None:
    target = str(tmp_path / "torus.png")
    out = viz.save_torus_png(target, config=_SMALL)
    assert out == target
    _assert_valid_png(target)


def test_cli_png_option_writes_torus(tmp_path) -> None:
    outdir = tmp_path / "pngs"
    out = cli.run_cli(
        ["torus", "--per-cluster", "10", "--seed", "7", "--png", str(outdir)]
    )
    assert "PNG export written" in out
    target = str(outdir / "calabi_yau_latent_torus.png")
    assert target in out
    _assert_valid_png(target)


def test_cli_png_creates_missing_outdir(tmp_path) -> None:
    outdir = tmp_path / "nested" / "deeper"
    cli.run_cli(
        ["all", "--per-cluster", "10", "--seed", "7", "--png", str(outdir)]
    )
    _assert_valid_png(str(outdir / "calabi_yau_latent_torus.png"))
