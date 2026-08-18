"""Tests for the runnable demo (gojo_infinity.demo).

The demo must assemble the headline, all four lens reports, the ASCII gallery,
the four-verdict conclusion table, and the honest cursed-energy caveat into one
deterministic, non-empty string.
"""

from __future__ import annotations

from gojo_infinity import demo


def test_render_demo_headline_and_all_verdicts() -> None:
    out = demo.render_demo()
    assert out.startswith("MATHEMATICS BEHIND JUJUTSU KAISEN: GOJO SATORU'S INFINITY")
    for headline in (
        "verdict: FRAGILE",
        "verdict: FORMIDABLE",
        "verdict: FALLS",
    ):
        assert headline in out


def test_render_demo_conclusion_table_and_caveat() -> None:
    out = demo.render_demo()
    assert "CONCLUSION -- four lenses, four verdicts" in out
    # the honest caveat from the essay
    assert "'cursed energy'".lower() in out.lower()
    assert "do not govern it" in out


def test_render_demo_ascii_gallery_present() -> None:
    out = demo.render_demo()
    assert "ASCII GALLERY" in out
    assert "Omega(x) blow-up" in out
    assert "target=+1.000000" in out  # Zeno chart
    assert "target=+0.100000" in out  # cover chart


def test_render_demo_is_deterministic() -> None:
    assert demo.render_demo() == demo.render_demo()


def test_main_prints_and_returns_zero(capsys) -> None:
    rc = demo.main()
    assert rc == 0
    captured = capsys.readouterr()
    assert "GOJO SATORU'S INFINITY" in captured.out
