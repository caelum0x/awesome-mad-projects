"""Tests for the command-line adapter (mobius_rickness.adapters.cli).

Each subcommand must run without error and emit its stable headline plus the
report's key evidence lines. The parser must reject a missing / unknown
subcommand, and ``main`` must print and return 0.
"""

from __future__ import annotations

import pytest

from mobius_rickness.adapters import cli


# ---------------------------------------------------------------------------
# Every subcommand runs and prints its headline + key evidence
# ---------------------------------------------------------------------------

def test_curvature_command_key_lines() -> None:
    out = cli.run(["curvature"])
    assert "CURVATURE -- Mobius strip: K < 0 strictly (ruled surface)" in out
    assert "K < 0 strictly on the interior" in out
    assert "Three curvature paths" in out
    # reproduced original sample table + its punchline
    assert "Original curvature sample table" in out
    assert "Every K < 0 and every R_naive > 0  =>  K_Rick < 0 with NO zero." in out


def test_trace_command_key_lines() -> None:
    out = cli.run(["trace"])
    assert "TRACE -- Central Finite Curve = R^-1(0)" in out
    assert "K_Rick = K*R = 0  <=>  R = 0." in out
    assert "All traced points verified: |R| < 1e-6 and |K_Rick| < 1e-6." in out
    # the (u, v, x, y, z, |R|) table header is present
    header = f"{'u':>10} {'v':>10} {'x':>10} {'y':>10} {'z':>10} {'|R|':>10}"
    assert header in out


def test_torus_command_key_lines() -> None:
    out = cli.run(["torus"])
    assert "TORUS -- geometry-driven zero set (K changes sign)" in out
    assert "K_closed" in out and "K_numeric" in out
    # the two geometry-driven zero circles are located near pi/2 and 3pi/2
    assert "1.570796, 4.712389" in out  # pi/2, 3pi/2 to 6 dp
    assert "(pi/2, 3pi/2)" in out


def test_all_command_contains_every_report() -> None:
    out = cli.run(["all"])
    for headline in (
        "CURVATURE -- Mobius strip: K < 0 strictly (ruled surface)",
        "TRACE -- Central Finite Curve = R^-1(0)",
        "TORUS -- geometry-driven zero set (K changes sign)",
    ):
        assert headline in out


# ---------------------------------------------------------------------------
# --ascii option appends the deterministic pictures
# ---------------------------------------------------------------------------

def test_ascii_flag_appends_pictures_for_curvature() -> None:
    plain = cli.run(["curvature"])
    with_ascii = cli.run(["curvature", "--ascii"])
    assert len(with_ascii) > len(plain)
    assert "Rickness R(u,v) sign map" in with_ascii
    assert "K_Rick(u,v) = K*R heatmap" in with_ascii


def test_ascii_flag_appends_sign_map_for_trace() -> None:
    out = cli.run(["trace", "--ascii"])
    assert "Rickness R(u,v) sign map" in out


def test_torus_has_no_ascii_flag() -> None:
    # torus has no ASCII picture of its own, so --ascii is not a valid option.
    with pytest.raises(SystemExit):
        cli.run(["torus", "--ascii"])


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("command", ["curvature", "trace", "torus", "all"])
def test_commands_are_deterministic(command: str) -> None:
    assert cli.run([command]) == cli.run([command])


# ---------------------------------------------------------------------------
# Parser behaviour + main() entry point
# ---------------------------------------------------------------------------

def test_missing_subcommand_errors() -> None:
    with pytest.raises(SystemExit):
        cli.run([])


def test_unknown_subcommand_errors() -> None:
    with pytest.raises(SystemExit):
        cli.run(["nonsense"])


def test_main_prints_and_returns_zero(capsys) -> None:
    rc = cli.main(["torus"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "TORUS -- geometry-driven zero set (K changes sign)" in captured.out
