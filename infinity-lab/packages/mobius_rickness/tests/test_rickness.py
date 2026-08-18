"""Rickness field: sign change, naive positivity, exact column root.

Note: ``from mobius_rickness.core import rickness`` yields the re-exported
*function* (it shadows the submodule attribute of the same name), so this test
imports the module members explicitly from ``mobius_rickness.core.rickness``.
"""

from __future__ import annotations

import math

import pytest

from commons.core.numerics import bisection
from mobius_rickness.core.field import linspace
from mobius_rickness.core.rickness import (
    V_MAX,
    V_MIN,
    column_coeffs,
    column_root,
    rickness,
    rickness_naive,
)


def test_rickness_changes_sign() -> None:
    vals = [
        rickness(u, v)
        for u in linspace(0.0, 2.0 * math.pi, 60)
        for v in (-0.5, -0.25, 0.0, 0.25, 0.5)
    ]
    assert min(vals) < 0.0
    assert max(vals) > 0.0


def test_naive_rickness_strictly_positive() -> None:
    vals = [
        rickness_naive(u, v)
        for u in linspace(0.0, 2.0 * math.pi, 60)
        for v in (-0.5, 0.0, 0.5)
    ]
    assert min(vals) > 0.0


def test_column_decomposition_matches_field() -> None:
    for u, v in [(0.7, 0.2), (2.1, -0.3), (4.4, 0.45)]:
        a, b = column_coeffs(u)
        assert a + b * v == pytest.approx(rickness(u, v), abs=1e-12)


def test_column_root_agrees_with_bisection() -> None:
    u = 1.7952
    v_star = column_root(u)
    assert v_star is not None
    assert rickness(u, v_star) == pytest.approx(0.0, abs=1e-12)
    v_bis = bisection(lambda v: rickness(u, v), V_MIN, V_MAX, tol=1e-12)
    assert v_star == pytest.approx(v_bis, abs=1e-9)


def test_column_root_none_outside_strip() -> None:
    # At u = 0: v* = -1/0.4 = -2.5, outside [-0.5, 0.5].
    assert column_root(0.0) is None


def test_seam_constraint_R0_minus_v_equals_R2pi_v() -> None:
    for v in (-0.4, 0.0, 0.3):
        assert rickness(0.0, -v) == pytest.approx(rickness(2.0 * math.pi, v), abs=1e-12)
