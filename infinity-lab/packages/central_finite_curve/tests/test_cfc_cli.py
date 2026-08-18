"""Tests for the command-line adapter (central_finite_curve.adapters.cli).

Each subcommand must run on a small fast config and emit its stable headline plus
the key numeric evidence. The parser must reject a missing/unknown subcommand. All
runs here are stdlib-only (no --png / animate), so they RUN on both interpreters.
"""

from __future__ import annotations

import pytest

from central_finite_curve.adapters import cli

# Small, fast pipeline shared by the text tests.
_ARGS = ["--universes", "800", "--walk-steps", "300", "--seed", "137"]


def _run(command: str):
    return cli.run_cli([command, *_ARGS])


def test_generate_command_key_lines() -> None:
    out = _run("generate")
    assert "CENTRAL FINITE CURVE ENGINE" in out
    assert "universes generated  : 800" in out
    assert "max Rickness" in out
    assert "band lower bound" in out


def test_curve_command_reports_size_and_fraction() -> None:
    out = _run("curve")
    assert "curve size (universes):" in out
    assert "fraction of multiverse:" in out
    assert "best universe coords :" in out


def test_walk_command_reports_acceptance() -> None:
    out = _run("walk")
    assert "Portal gun (constrained MCMC walk)" in out
    assert "acceptance rate" in out
    assert "trajectory length    : 301 points" in out


def test_project_command_has_ascii_scatter() -> None:
    out = _run("project")
    assert "ASCII projection (top-2 principal components)" in out
    assert "portal-gun walk" in out  # legend line of the scatter
    assert "+" in out and "|" in out  # the framed grid


def test_all_command_contains_every_section() -> None:
    out = _run("all")
    for marker in (
        "CENTRAL FINITE CURVE ENGINE",
        "Rickness landscape",
        "Central Finite Curve",
        "Portal gun (constrained MCMC walk)",
        "ASCII projection",
    ):
        assert marker in out


def test_missing_subcommand_errors() -> None:
    with pytest.raises(SystemExit):
        cli.run_cli([])


def test_unknown_subcommand_errors() -> None:
    with pytest.raises(SystemExit):
        cli.run_cli(["nonsense"])


def test_main_prints_and_returns_zero(capsys) -> None:
    rc = cli.main(["generate", *_ARGS])
    assert rc == 0
    captured = capsys.readouterr()
    assert "CENTRAL FINITE CURVE ENGINE" in captured.out
