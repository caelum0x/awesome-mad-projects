"""Tests for the command-line adapter (divergence_meter.adapters.cli).

Each subcommand emits a stable, greppable report. The store lives under pytest's
``tmp_path`` so nothing is written into the repo. Stdlib-only -> RUNS on both.
"""

from __future__ import annotations

import pytest

from divergence_meter.adapters import cli


def _store(tmp_path) -> str:
    return str(tmp_path / "store.json")


def test_measure_reports_nixie_field_and_origin() -> None:
    out = cli.run_cli(["measure", "El Psy Congroo"])
    assert "DIVERGENCE: 1.062031" in out
    assert "origin   : text:literal" in out
    assert "sha256   :" in out
    assert "Field: Beta" in out


def test_field_reports_classification() -> None:
    out = cli.run_cli(["field", "El Psy Congroo"])
    assert "Divergence : 1.062031" in out
    assert "nearest boundary 1.000000" in out


def test_save_then_lines_then_jump(tmp_path) -> None:
    store = _store(tmp_path)
    save_out = cli.run_cli(["--store", store, "save", "alpha", "worldline alpha"])
    assert "Saved worldline 'alpha' @ 0.120241" in save_out

    cli.run_cli(["--store", store, "save", "beta", "worldline beta"])
    lines_out = cli.run_cli(["--store", store, "lines"])
    assert "Saved worldlines (2):" in lines_out
    assert "alpha" in lines_out and "beta" in lines_out

    jump_out = cli.run_cli(["--store", store, "jump", "alpha", "worldline beta"])
    assert "Jump target: 'alpha'" in jump_out
    assert "divergence delta : +0.003987" in jump_out
    assert "Beta-ward (+)" in jump_out


def test_lines_empty_store(tmp_path) -> None:
    out = cli.run_cli(["--store", _store(tmp_path), "lines"])
    assert out == "No worldlines saved yet."


def test_missing_subcommand_errors() -> None:
    with pytest.raises(SystemExit):
        cli.run_cli([])


def test_unknown_subcommand_errors() -> None:
    with pytest.raises(SystemExit):
        cli.run_cli(["nonsense"])


def test_main_prints_and_returns_zero(capsys) -> None:
    rc = cli.main(["measure", "El Psy Congroo"])
    assert rc == 0
    assert "DIVERGENCE: 1.062031" in capsys.readouterr().out


def test_main_reports_store_error(tmp_path, capsys) -> None:
    rc = cli.main(["--store", _store(tmp_path), "jump", "ghost", "now"])
    assert rc == 1
    assert "error:" in capsys.readouterr().err
