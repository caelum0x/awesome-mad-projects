"""Tests for the Domain model, both solvers, and the constraint metrics."""

from __future__ import annotations

import pytest

from domain_expansion.core import scenarios
from domain_expansion.core.domain import (
    direct_solve_domain,
    max_grid_diff,
    rigidity,
    solve_domain,
)


def test_relaxation_and_direct_solve_agree() -> None:
    domain = scenarios.make_refined_domain()
    relaxed = solve_domain(domain)
    direct = direct_solve_domain(domain)
    assert relaxed.converged
    assert max_grid_diff(relaxed.field, direct) < 1e-6


def test_residual_decreases_with_iterations() -> None:
    domain = scenarios.make_refined_domain()
    # Tight tol so relaxation does NOT early-converge before the last budget.
    residuals = [
        solve_domain(domain, max_iters=n, tol=1e-15).residual_l2
        for n in (1, 2, 4, 8, 16, 32)
    ]
    # Monotone non-increasing, and strictly better overall.
    for earlier, later in zip(residuals, residuals[1:]):
        assert later <= earlier + 1e-15
    assert residuals[-1] < residuals[0]


def test_refined_field_matches_boundary() -> None:
    domain = scenarios.make_refined_domain()
    result = solve_domain(domain)
    # Left wall hot (100), right wall cold (0) -- the sure-hit condition holds.
    assert result.field[0][3] == pytest.approx(100.0)
    assert result.field[domain.nx - 1][3] == pytest.approx(0.0)
    # Interior is bounded by the boundary extremes (discrete maximum principle).
    for i in range(1, domain.nx - 1):
        for j in range(1, domain.ny - 1):
            assert 0.0 <= result.field[i][j] <= 100.0


def test_refined_more_rigid_than_crude() -> None:
    refined = scenarios.make_refined_domain()
    crude = scenarios.make_crude_domain()
    assert rigidity(refined) > rigidity(crude)


def test_refined_more_refined_than_crude() -> None:
    refined = solve_domain(scenarios.make_refined_domain())
    crude = solve_domain(scenarios.make_crude_domain())
    assert refined.refinement > crude.refinement


def test_void_pin_dominates_rigidity() -> None:
    void = scenarios.make_void_domain()
    crude = scenarios.make_crude_domain()
    refined = scenarios.make_refined_domain()
    # The Unlimited Void pin makes rigidity astronomically higher than any
    # smooth domain's.
    assert rigidity(void) > rigidity(crude)
    assert rigidity(void) > rigidity(refined)


def test_void_field_holds_the_pin() -> None:
    void = scenarios.make_void_domain()
    result = solve_domain(void)
    assert result.field[3][3] == pytest.approx(999.0)


def test_solve_domain_rejects_bad_arguments() -> None:
    domain = scenarios.make_refined_domain()
    with pytest.raises(ValueError):
        solve_domain(domain, max_iters=0)
    with pytest.raises(ValueError):
        solve_domain(domain, tol=0.0)


def test_domain_rejects_tiny_grid() -> None:
    from domain_expansion.core.domain import Domain

    # A valid domain builds fine; a 2x2 grid (no interior cell) is rejected.
    assert scenarios.make_refined_domain().nx == 7
    with pytest.raises(ValueError):
        Domain(name="too small", nx=2, ny=2, boundary=lambda i, j: 0.0)
