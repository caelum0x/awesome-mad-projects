"""Tests for the OPTIONAL matplotlib PNG export (divergence_meter.adapters.viz).

DEFERRED behind ``commons.core.optional.try_import``: with no matplotlib installed
the exporter raises :class:`viz.OptionalDependencyError` rather than failing at
import time. This module ``importorskip("matplotlib")`` so it SKIPS on the
matplotlib-free system interpreter and RUNS on the venv.

matplotlib is forced onto the headless ``Agg`` backend by the renderer, so no
display is needed. Each test renders a SMALL ensemble to ``tmp_path`` and asserts
the file exists, begins with the 8-byte PNG signature, and is non-trivially sized.
No PNGs are committed -- they live only under the pytest tmp dir.
"""

from __future__ import annotations

import os

import pytest

pytest.importorskip("matplotlib")

from divergence_meter.adapters import viz

_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_MIN_PNG_BYTES = 1024


def _assert_valid_png(path: str) -> None:
    assert os.path.exists(path), f"expected a rendered PNG at {path}"
    size = os.path.getsize(path)
    assert size > _MIN_PNG_BYTES, f"PNG too small ({size} bytes) at {path}"
    with open(path, "rb") as handle:
        header = handle.read(8)
    assert header == _PNG_SIGNATURE, f"not a PNG signature at {path}: {header!r}"


def test_save_worldlines_png_writes_valid_png(tmp_path) -> None:
    target = str(tmp_path / "worldlines.png")
    out = viz.save_worldlines_png(target, count=60, seed=42)
    assert out == target
    _assert_valid_png(target)


def test_save_worldlines_png_creates_missing_outdir(tmp_path) -> None:
    target = str(tmp_path / "nested" / "deeper" / "worldlines.png")
    viz.save_worldlines_png(target, count=40, seed=7)
    _assert_valid_png(target)


def test_default_artifact_path_points_at_repo_artifacts() -> None:
    assert viz.DEFAULT_ARTIFACT_PATH.endswith(
        os.path.join("artifacts", "divergence_meter_worldlines.png")
    )
