"""Test for the runnable demo (domain_expansion.demo)."""

from __future__ import annotations

from domain_expansion import demo


def test_render_demo_contains_headline_and_report() -> None:
    text = demo.render_demo()
    assert demo._HEADLINE in text
    assert "WINNER : Refined Domain" in text
    assert "UNLIMITED VOID" in text


def test_demo_main_returns_zero(capsys) -> None:
    rc = demo.main()
    captured = capsys.readouterr()
    assert rc == 0
    assert "DOMAIN EXPANSION" in captured.out
