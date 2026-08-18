"""Tests for the CLI adapter and the ASCII plot (stdlib-only; run on both interps).

The CLI honours ``--seed`` / ``--steps``, emits the stable section headlines plus
the invariant verdict, and the ASCII chart marks witch events with ``'^'``. The
demo shares the CLI's single source of truth.
"""

from __future__ import annotations

import pytest

from madoka_entropy import demo
from madoka_entropy.adapters import cli, plot
from madoka_entropy.core.config import SimConfig
from madoka_entropy.core.simulation import run_simulation


def test_cli_default_report_has_every_section() -> None:
    out = cli.run_cli(["--seed", "42", "--steps", "60"])
    for marker in (
        "MADOKA MAGICA",
        "seed=42  steps=60",
        "GLOBAL entropy",
        "TOTAL entropy",
        "FINAL ACCOUNTING",
        "SECOND-LAW INVARIANT CHECK",
    ):
        assert marker in out


def test_cli_reports_invariant_pass() -> None:
    out = cli.run_cli(["--seed", "42", "--steps", "120"])
    assert "RESULT: PASS" in out
    assert "violations           : 0" in out


def test_cli_seed_changes_output() -> None:
    a = cli.run_cli(["--seed", "1", "--steps", "120"])
    b = cli.run_cli(["--seed", "2", "--steps", "120"])
    assert a != b


def test_cli_main_prints_and_returns_zero(capsys) -> None:
    rc = cli.main(["--seed", "7", "--steps", "40"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "MADOKA MAGICA" in captured.out


def test_ascii_chart_marks_witch_events() -> None:
    result = run_simulation(SimConfig(seed=42, steps=120))
    chart = plot.global_entropy_chart(result.records)
    assert "witch transformation" in chart
    assert "^" in chart  # at least one witch column flagged on the x-axis


def test_witch_steps_helper_matches_records() -> None:
    result = run_simulation(SimConfig(seed=42, steps=120))
    steps = plot.witch_steps(result.records)
    expected = {r.step for r in result.records if r.witches_this_step}
    assert steps == expected


def test_total_chart_empty_is_graceful() -> None:
    assert "no data" in plot.total_entropy_chart([])


def test_demo_renders_headline() -> None:
    text = demo.render_demo(SimConfig(seed=42, steps=40))
    assert "MADOKA MAGICA" in text
    assert "SECOND-LAW INVARIANT CHECK" in text


def test_bad_config_is_rejected() -> None:
    with pytest.raises(ValueError):
        SimConfig(karmic_multiplier=1.0)
