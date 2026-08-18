"""Tests for the command-line adapter (calabi_yau_latent.adapters.cli).

Each subcommand must run on a small fast config and emit its stable headline plus
the key numeric evidence, and the parser must reject a missing/unknown subcommand.
All runs here are stdlib-only (no --png), so they RUN on both interpreters.
"""

from __future__ import annotations

import pytest

from calabi_yau_latent.adapters import cli

_ARGS = ["--per-cluster", "10", "--seed", "7"]


def _run(command: str) -> str:
    return cli.run_cli([command, *_ARGS])


def test_seam_command_reports_metric_disagreement() -> None:
    out = _run("seam")
    assert "The seam problem" in out
    assert "naive angular distance" in out
    assert "wrap-aware angular distance" in out
    assert "overestimate" in out


def test_cluster_command_recovers_and_over_segments() -> None:
    out = _run("cluster")
    assert "connected-components clustering".upper() in out.upper()
    assert "wrap-aware :" in out
    assert "naive      :" in out


def test_holonomy_command_reports_measured_and_closed_form() -> None:
    out = _run("holonomy")
    assert "Holonomy" in out
    assert "measured" in out
    assert "closed form" in out
    assert "ANALOGY" in out


def test_torus_command_prints_ascii_torus() -> None:
    out = _run("torus")
    assert "compact 2-torus" in out
    assert "theta1" in out


def test_all_command_has_every_section_and_caveat() -> None:
    out = _run("all")
    assert "COMPACTIFIED LATENT SPACE" in out
    assert "seam problem" in out.lower()
    assert "Holonomy" in out
    assert "TOY analogy" in out


def test_parser_requires_a_subcommand() -> None:
    with pytest.raises(SystemExit):
        cli.run_cli([])


def test_parser_rejects_unknown_subcommand() -> None:
    with pytest.raises(SystemExit):
        cli.run_cli(["nonsense"])
