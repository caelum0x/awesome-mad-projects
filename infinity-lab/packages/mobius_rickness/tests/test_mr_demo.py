"""Tests for the runnable demo (mobius_rickness.demo).

The demo must assemble the headline, all three reports (the reproduced curvature
table, the traced Central Finite Curve points, the torus sign pattern) and the
ASCII gallery into one deterministic, non-empty string.
"""

from __future__ import annotations

from mobius_rickness import demo


def test_render_demo_headline() -> None:
    out = demo.render_demo()
    assert out.startswith(
        "MOBIUS-RICKNESS: THE CENTRAL FINITE CURVE AS A REAL ZERO SET"
    )


def test_render_demo_reproduces_curvature_table() -> None:
    out = demo.render_demo()
    assert "Original curvature sample table" in out
    assert "Every K < 0 and every R_naive > 0  =>  K_Rick < 0 with NO zero." in out


def test_render_demo_traces_curve_points() -> None:
    out = demo.render_demo()
    assert "TRACE -- Central Finite Curve = R^-1(0)" in out
    assert "All traced points verified: |R| < 1e-6 and |K_Rick| < 1e-6." in out
    # the lifted (u, v, x, y, z, |R|) table header must be present
    header = f"{'u':>10} {'v':>10} {'x':>10} {'y':>10} {'z':>10} {'|R|':>10}"
    assert header in out


def test_render_demo_shows_torus_sign_pattern() -> None:
    out = demo.render_demo()
    assert "TORUS -- geometry-driven zero set (K changes sign)" in out
    assert "Sign pattern: POSITIVE outer half, NEGATIVE inner half" in out
    assert "1.570796, 4.712389" in out  # traced zero circles pi/2, 3pi/2


def test_render_demo_ascii_gallery_present() -> None:
    out = demo.render_demo()
    assert "ASCII GALLERY" in out
    assert "Rickness R(u,v) sign map" in out
    assert "K_Rick(u,v) = K*R heatmap" in out


def test_render_demo_is_deterministic() -> None:
    assert demo.render_demo() == demo.render_demo()


def test_main_prints_and_returns_zero(capsys) -> None:
    rc = demo.main()
    assert rc == 0
    captured = capsys.readouterr()
    assert "MOBIUS-RICKNESS: THE CENTRAL FINITE CURVE" in captured.out
