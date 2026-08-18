"""Tests for the runnable demo (calabi_yau_latent.demo).

The demo shares one source of truth with the CLI, so a small-config render must
carry the headline, the honest caveat, and every pipeline section. Stdlib-only ->
RUNS on both interpreters.
"""

from __future__ import annotations

from calabi_yau_latent import demo
from calabi_yau_latent.core.config import CYConfig

_SMALL = CYConfig(per_cluster=10, seed=7)


def test_render_demo_has_headline_and_sections() -> None:
    text = demo.render_demo(_SMALL)
    assert "COMPACTIFIED LATENT SPACE" in text
    assert "HONEST TOY" in text
    assert "seam problem" in text.lower()
    assert "Holonomy" in text


def test_render_demo_keeps_the_honest_caveat() -> None:
    text = demo.render_demo(_SMALL)
    assert "not a Ricci-flat" in text.lower() or "NOT a Ricci-flat" in text
    assert "TOY" in text


def test_demo_main_returns_zero(capsys) -> None:
    rc = demo.main()
    assert rc == 0
    out = capsys.readouterr().out
    assert "COMPACTIFIED LATENT SPACE" in out
