"""Weighted field K_Rick = K * R: zero set = R^{-1}(0), grid straddles zero."""

from __future__ import annotations

import pytest

from mobius_rickness.core import field
from mobius_rickness.core.mobius import gaussian_curvature
from mobius_rickness.core.rickness import rickness


def test_k_rick_equals_K_times_R() -> None:
    for u, v in [(1.7952, 0.11), (3.0, -0.2), (5.5, 0.3)]:
        assert field.k_rick(u, v) == pytest.approx(
            gaussian_curvature(u, v) * rickness(u, v), abs=1e-15
        )


def test_k_rick_zero_iff_rickness_zero() -> None:
    # Where R = 0, K_Rick = 0 (K is finite and negative); where R != 0, K_Rick != 0.
    from mobius_rickness.core.rickness import column_root

    u = 1.7952
    v0 = column_root(u)
    assert v0 is not None
    assert abs(field.k_rick(u, v0)) < 1e-9
    assert field.k_rick(u, v0 + 0.1) != 0.0


def test_k_rick_grid_straddles_zero() -> None:
    grid = field.evaluate_grid(n_u=49, n_v=17)
    lo, hi = field.field_range(grid.K_Rick)
    assert lo < 0.0
    assert hi > 0.0


def test_K_strictly_negative_on_interior() -> None:
    worst = field.assert_mobius_K_negative(n_u=40, n_v=11)
    assert worst < 0.0


def test_grid_shapes() -> None:
    grid = field.evaluate_grid(n_u=7, n_v=5)
    assert len(grid.vs) == 5
    assert len(grid.us) == 7
    assert len(grid.K) == 5 and all(len(row) == 7 for row in grid.K)
