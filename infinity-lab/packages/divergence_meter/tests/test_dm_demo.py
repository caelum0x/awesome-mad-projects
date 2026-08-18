"""Tests for the runnable demo (divergence_meter.demo).

The demo shares one source of truth with the CLI and adapters, so a small render
must carry the headline, the measured worldline, and the ensemble views.
Stdlib + commons -> RUNS on both interpreters.
"""

from __future__ import annotations

from divergence_meter import demo


def test_render_demo_has_headline_and_sections() -> None:
    text = demo.render_demo(count=20, seed=42)
    assert "THE DIVERGENCE METER" in text
    assert "DIVERGENCE: 1.062031" in text
    assert "worldline divergence timeline" in text
    assert "attractor-field population" in text


def test_render_demo_is_deterministic() -> None:
    assert demo.render_demo(count=20, seed=1) == demo.render_demo(count=20, seed=1)


def test_demo_main_returns_zero(capsys) -> None:
    rc = demo.main()
    assert rc == 0
    assert "THE DIVERGENCE METER" in capsys.readouterr().out
