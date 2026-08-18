"""Tests for the ASCII renderers (domain_expansion.adapters.render)."""

from __future__ import annotations

import pytest

from domain_expansion.adapters import render
from domain_expansion.core import scenarios
from domain_expansion.core.clash import clash
from domain_expansion.core.domain import solve_domain


def test_format_field_is_deterministic_and_labelled() -> None:
    result = solve_domain(scenarios.make_refined_domain())
    text_a = render.format_field(result.field, "field:")
    text_b = render.format_field(result.field, "field:")
    assert text_a == text_b
    assert text_a.startswith("field:")
    # The hot left wall (100.0) shows up in the numeric grid.
    assert "100.0" in text_a


def test_field_heatmap_uses_commons_and_has_legend() -> None:
    result = solve_domain(scenarios.make_refined_domain())
    heat = render.field_heatmap(result.field, title="refined heat")
    assert heat.startswith("refined heat")
    assert "scale:" in heat  # commons render_heatmap legend line


def test_format_solve_report_fields() -> None:
    result = solve_domain(scenarios.make_refined_domain())
    report = render.format_solve_report("Refined Domain", result)
    assert "[Refined Domain]" in report
    assert "residual  (L2)" in report
    assert "rigidity  proxy" in report
    assert "refinement score" in report


def test_format_clash_report_shows_winner_and_field() -> None:
    result = clash(scenarios.make_crude_domain(), scenarios.make_refined_domain())
    report = render.format_clash_report(result)
    assert "WINNER : Refined Domain" in report
    assert "overwritten by Refined Domain" in report


def test_render_rejects_empty_field() -> None:
    with pytest.raises(ValueError):
        render.format_field([], "empty")
    with pytest.raises(ValueError):
        render.field_heatmap([])
