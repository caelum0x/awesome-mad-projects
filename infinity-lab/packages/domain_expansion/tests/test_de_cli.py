"""Tests for the argparse CLI (domain_expansion.adapters.cli)."""

from __future__ import annotations

import pytest

from domain_expansion.adapters import cli


def test_refined_command_reports_direct_check() -> None:
    out = cli.run_cli(["refined"])
    assert "refined domain" in out
    assert "direct-solve check" in out
    assert "refinement score" in out


def test_crude_command_reports_metrics() -> None:
    out = cli.run_cli(["crude"])
    assert "[Crude Domain]" in out
    assert "residual  (L2)" in out


def test_clash_command_names_winner() -> None:
    out = cli.run_cli(["clash"])
    assert "WINNER : Refined Domain" in out
    assert "overwritten by Refined Domain" in out


def test_void_command_shows_void_dominates() -> None:
    out = cli.run_cli(["void"])
    assert "UNLIMITED VOID" in out
    assert "Void vs Crude winner: Unlimited Void" in out


def test_all_command_runs_full_report() -> None:
    out = cli.run_cli(["all"])
    for marker in (
        "refined domain",
        "[Crude Domain]",
        "WINNER : Refined Domain",
        "UNLIMITED VOID",
        "Summary",
    ):
        assert marker in out


def test_run_cli_requires_subcommand() -> None:
    with pytest.raises(SystemExit):
        cli.run_cli([])


def test_main_prints_and_returns_zero(capsys) -> None:
    rc = cli.main(["refined"])
    captured = capsys.readouterr()
    assert rc == 0
    assert "DOMAIN EXPANSION" in captured.out
