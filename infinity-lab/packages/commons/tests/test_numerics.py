"""Tests for commons.core.numerics (integration, derivatives, root finding)."""

from __future__ import annotations

import cmath
import math

import pytest

from commons.core.numerics import (
    adaptive_integral,
    bisection,
    central_difference,
    complex_step_derivative,
    find_sign_changes,
    midpoint_integral,
    trapezoid_integral,
)


# --- Integration: integral_0^1 x^2 dx = 1/3 for each integrator ------------

def test_midpoint_x_squared() -> None:
    val = midpoint_integral(lambda x: x * x, 0.0, 1.0, n=2000)
    assert abs(val - 1.0 / 3.0) < 1e-6


def test_trapezoid_x_squared() -> None:
    val = trapezoid_integral(lambda x: x * x, 0.0, 1.0, n=2000)
    assert abs(val - 1.0 / 3.0) < 1e-6


def test_adaptive_x_squared() -> None:
    val = adaptive_integral(lambda x: x * x, 0.0, 1.0, tol=1e-12)
    assert abs(val - 1.0 / 3.0) < 1e-10


def test_adaptive_sin_over_pi() -> None:
    # integral_0^pi sin(x) dx = 2
    val = adaptive_integral(math.sin, 0.0, math.pi, tol=1e-12)
    assert abs(val - 2.0) < 1e-10


def test_integrators_zero_width() -> None:
    assert midpoint_integral(math.sin, 1.0, 1.0) == 0.0
    assert trapezoid_integral(math.sin, 1.0, 1.0) == 0.0
    assert adaptive_integral(math.sin, 1.0, 1.0) == 0.0


def test_integrator_bad_bounds() -> None:
    with pytest.raises(ValueError):
        midpoint_integral(math.sin, 1.0, 0.0)
    with pytest.raises(ValueError):
        trapezoid_integral(math.sin, 1.0, 0.0)
    with pytest.raises(ValueError):
        adaptive_integral(math.sin, 1.0, 0.0)


# --- Derivatives: d/dx sin(x) = cos(x) -------------------------------------

def test_central_difference_first() -> None:
    x = 0.7
    approx = central_difference(math.sin, x, h=1e-6, order=1)
    assert abs(approx - math.cos(x)) < 1e-7


def test_central_difference_second() -> None:
    # d^2/dx^2 sin(x) = -sin(x)
    x = 0.7
    approx = central_difference(math.sin, x, h=1e-4, order=2)
    assert abs(approx - (-math.sin(x))) < 1e-6


def test_central_difference_bad_order() -> None:
    with pytest.raises(ValueError):
        central_difference(math.sin, 0.0, order=3)


def test_central_difference_bad_h() -> None:
    with pytest.raises(ValueError):
        central_difference(math.sin, 0.0, h=0.0)


def test_complex_step_matches_analytic_to_1e12() -> None:
    x = 0.7
    approx = complex_step_derivative(cmath.sin, x, h=1e-20)
    assert abs(approx - math.cos(x)) < 1e-12


def test_complex_step_polynomial_exact() -> None:
    # d/dx x^3 = 3 x^2; at x=2 -> 12
    approx = complex_step_derivative(lambda z: z ** 3, 2.0, h=1e-20)
    assert abs(approx - 12.0) < 1e-12


# --- Root finding ----------------------------------------------------------

def test_bisection_finds_sqrt2() -> None:
    root = bisection(lambda x: x * x - 2.0, 0.0, 2.0, tol=1e-12)
    assert abs(root - math.sqrt(2.0)) < 1e-10


def test_bisection_finds_cos_root() -> None:
    # cos has a root at pi/2 in [0, 2]
    root = bisection(math.cos, 0.0, 2.0, tol=1e-12)
    assert abs(root - math.pi / 2.0) < 1e-10


def test_bisection_endpoint_root() -> None:
    assert bisection(lambda x: x, 0.0, 1.0) == 0.0


def test_bisection_no_sign_change_raises() -> None:
    with pytest.raises(ValueError):
        bisection(lambda x: x * x + 1.0, -1.0, 1.0)


def test_find_sign_changes_brackets() -> None:
    brackets = find_sign_changes(math.sin, -0.5, 7.0, n=200)
    # sin has roots at 0, pi, 2pi within [-0.5, 7]
    roots = [bisection(math.sin, lo, hi) for lo, hi in brackets]
    assert len(roots) >= 3
    for r in roots:
        assert abs(math.sin(r)) < 1e-9
