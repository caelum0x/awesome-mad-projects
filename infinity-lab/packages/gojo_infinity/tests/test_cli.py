"""Tests for the command-line adapter (gojo_infinity.adapters.cli).

Each subcommand must run without error and emit its stable headline plus the
lens's key evidence lines. The parser must reject a missing subcommand.
"""

from __future__ import annotations

import pytest

from gojo_infinity.adapters import cli


# ---------------------------------------------------------------------------
# Every subcommand runs and prints its verdict headline + key evidence
# ---------------------------------------------------------------------------

def test_zeno_command_key_lines() -> None:
    out = cli.run(["zeno"])
    assert "LENS 1 -- GEOMETRIC SERIES (Zeno)   verdict: FRAGILE" in out
    assert "255/256" in out  # S_8 exact
    assert "= 1  (exactly 1)" in out  # geometric sum limit
    assert "Total arrival time at speed 1/2 = 2" in out  # finite arrival


def test_measure_command_key_lines() -> None:
    out = cli.run(["measure"])
    assert "LENS 2 -- LEBESGUE MEASURE   verdict: FRAGILE" in out
    assert "{1/2, 3/4, 7/8, 15/16, ...}" in out
    assert "m(Z) = 0" in out


def test_riemannian_command_key_lines() -> None:
    out = cli.run(["riemannian"])
    assert "LENS 3 -- RIEMANNIAN GEOMETRY   verdict: FORMIDABLE" in out
    assert "to the barrier = inf" in out  # math.inf reported explicitly
    assert "lambda DERIVED by bisection" in out


def test_topology_command_key_lines() -> None:
    out = cli.run(["topology"])
    assert "LENS 4 -- TOPOLOGY   verdict: FALLS" in out
    assert "felt length = None" in out  # UNDEFINED, type-distinct
    assert "DISCONNECTED into 2 pieces" in out
    assert "severed metric @ c=0.5: continuous = False" in out


def test_all_command_contains_every_lens_and_conclusion() -> None:
    out = cli.run(["all"])
    for headline in (
        "LENS 1 -- GEOMETRIC SERIES (Zeno)   verdict: FRAGILE",
        "LENS 2 -- LEBESGUE MEASURE   verdict: FRAGILE",
        "LENS 3 -- RIEMANNIAN GEOMETRY   verdict: FORMIDABLE",
        "LENS 4 -- TOPOLOGY   verdict: FALLS",
        "CONCLUSION -- four lenses, four verdicts",
    ):
        assert headline in out
    # the four canonical verdict labels appear in the conclusion table
    for label in ("Fragile", "Formidable", "Falls"):
        assert label in out
    assert "'cursed energy'".lower() in out.lower()


# ---------------------------------------------------------------------------
# --ascii option appends the deterministic chart
# ---------------------------------------------------------------------------

def test_ascii_flag_appends_chart_for_zeno() -> None:
    plain = cli.run(["zeno"])
    with_ascii = cli.run(["zeno", "--ascii"])
    assert len(with_ascii) > len(plain)
    assert "target=+1.000000" in with_ascii


def test_ascii_flag_appends_chart_for_riemannian() -> None:
    out = cli.run(["riemannian", "--ascii"])
    assert "Omega(x) blow-up" in out


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
    rc = cli.main(["measure"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "LENS 2 -- LEBESGUE MEASURE   verdict: FRAGILE" in captured.out
