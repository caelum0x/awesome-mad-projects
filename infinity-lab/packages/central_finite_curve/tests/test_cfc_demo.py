"""Tests for the runnable demo (central_finite_curve.demo).

The demo shares one source of truth with the CLI, so a small-config render must
carry the headline, the subtitle, and every pipeline section. Stdlib-only -> RUNS on
both interpreters.
"""

from __future__ import annotations

from central_finite_curve import demo
from central_finite_curve.core.config import CurveConfig

_SMALL = CurveConfig(n_universes=600, walk_steps=200, seed=137)


def test_render_demo_has_headline_and_sections() -> None:
    text = demo.render_demo(_SMALL)
    assert "THE CENTRAL FINITE CURVE" in text
    assert "portal gun" in text.lower()
    assert "CENTRAL FINITE CURVE ENGINE" in text
    assert "ASCII projection" in text


def test_demo_main_returns_zero(capsys) -> None:
    # main() uses the canonical (larger) config; assert it runs and prints.
    rc = demo.main()
    assert rc == 0
    out = capsys.readouterr().out
    assert "THE CENTRAL FINITE CURVE" in out
