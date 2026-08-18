"""Tests for the two-domain clash and the contested-region overwrite."""

from __future__ import annotations

import pytest

from domain_expansion.core import scenarios
from domain_expansion.core.clash import clash, contested_region
from domain_expansion.core.domain import solve_domain


def test_more_refined_domain_wins_the_clash() -> None:
    crude = scenarios.make_crude_domain()
    refined = scenarios.make_refined_domain()
    result = clash(crude, refined)
    assert result.winner == "Refined Domain"
    assert result.loser == "Crude Domain"


def test_winner_overwrites_contested_interior() -> None:
    crude = scenarios.make_crude_domain()
    refined = scenarios.make_refined_domain()
    result = clash(crude, refined)

    # The winner reasserts over the loser's field; the merged interior must equal
    # the winner's reasserted solution, NOT the loser's original interior.
    reasserted = solve_domain(refined, field_override=result.loser_result.field)
    loser_field = result.loser_result.field
    region = contested_region(refined.nx, refined.ny)

    changed = 0
    for (i, j) in region:
        assert result.merged_field[i][j] == pytest.approx(reasserted.field[i][j])
        if abs(result.merged_field[i][j] - loser_field[i][j]) > 1e-6:
            changed += 1
    # The takeover actually changed the interior (not a no-op overwrite).
    assert changed > 0


def test_loser_keeps_its_own_boundary() -> None:
    crude = scenarios.make_crude_domain()
    refined = scenarios.make_refined_domain()
    result = clash(crude, refined)
    # Crude's left/right walls (60 / 40) survive on the merged edges.
    assert result.merged_field[0][3] == pytest.approx(60.0)
    assert result.merged_field[crude.nx - 1][3] == pytest.approx(40.0)


def test_unlimited_void_dominates_on_rigidity() -> None:
    crude = scenarios.make_crude_domain()
    void = scenarios.make_void_domain()
    result = clash(crude, void)
    assert result.winner == "Unlimited Void"
    # It wins despite a huge residual, purely on rigidity.
    assert result.winner_result.rigidity > result.loser_result.rigidity
    assert result.winner_result.residual_l2 > result.loser_result.residual_l2


def test_clash_reason_is_greppable() -> None:
    result = clash(scenarios.make_crude_domain(), scenarios.make_refined_domain())
    assert "more refined" in result.reason
    assert "rigidity=" in result.reason


def test_clash_rejects_shape_mismatch() -> None:
    from domain_expansion.core.domain import Domain

    a = Domain(name="a", nx=7, ny=7, boundary=lambda i, j: 1.0)
    b = Domain(name="b", nx=5, ny=5, boundary=lambda i, j: 1.0)
    with pytest.raises(ValueError):
        clash(a, b)


def test_contested_region_is_the_interior() -> None:
    region = contested_region(7, 7)
    assert (0, 0) not in region
    assert (3, 3) in region
    assert len(region) == 25  # 5x5 interior of a 7x7 grid
