"""Tests for the runnable demo (padic_embeddings.demo).

The demo shares one source of truth with the CLI; it must render the headline plus
the full canonical report and its ``main`` must print and return 0. Pure stdlib +
commons, so these RUN on both interpreters.
"""

from __future__ import annotations

from padic_embeddings import demo


def test_render_demo_has_headline_and_report() -> None:
    out = demo.render_demo()
    assert "THE p-ADIC EMBEDDING SPACE" in out
    assert "p-adic Embedding Space   (prime p = 2)" in out
    assert "HOLDS (this is a true ultrametric)" in out


def test_demo_main_prints_and_returns_zero(capsys) -> None:
    rc = demo.main()
    assert rc == 0
    captured = capsys.readouterr()
    assert "p-adic Embedding Space" in captured.out
