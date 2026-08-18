"""Parity tests: numpy fast-paths vs the pure float-valued core.

These tests RUN only where numpy is installed (the project venv) and SKIP on the
stdlib-only system interpreter, guarded by ``pytest.importorskip("numpy")``.

For each fast-path we recompute the pure-core result elementwise and compare:

* Exact-dyadic / power-of-two mirrors (covering lengths, Zeno partial sums and
  residuals) are asserted **bit-identical** (``==``).
* ``exp``-derived mirrors (Omega, the metric, felt steps) and the reduction-order
  quadratures (trapezoid / midpoint) are asserted equal to within
  ``numpy.allclose(atol=1e-12, rtol=0)``, and the observed max ULP distance is
  reported in the assertion message.
"""

from __future__ import annotations

import pytest

np = pytest.importorskip("numpy")

from commons.core import midpoint_integral, trapezoid_integral  # noqa: E402
from gojo_infinity.accel import numpy_backend as nb  # noqa: E402
from gojo_infinity.core.measure import cover_interval_length  # noqa: E402
from gojo_infinity.core.riemannian import (  # noqa: E402
    DEFAULT_LAMBDA,
    DEFAULT_SIGMA,
    X_GOJO,
    conformal_factor,
    felt_step,
    metric_g11,
)
from gojo_infinity.core.zeno import partial_sum, residual  # noqa: E402


# ---------------------------------------------------------------------------
# ULP helper (values under test are all strictly positive)
# ---------------------------------------------------------------------------

def _max_ulp(actual, expected) -> int:
    """Max ULP distance between two positive float arrays via IEEE-754 encoding.

    For positive doubles the int64 reinterpretation is monotone, so the absolute
    difference of the bit patterns is exactly the count of representable doubles
    between the two values (0 == bit-identical).
    """
    a = np.ascontiguousarray(actual, dtype=np.float64).view(np.int64)
    b = np.ascontiguousarray(expected, dtype=np.float64).view(np.int64)
    return int(np.max(np.abs(a - b))) if a.size else 0


# ---------------------------------------------------------------------------
# Riemannian: Omega(x), metric g = Omega^2, ds = Omega*dx  (<= few ULP)
# ---------------------------------------------------------------------------

_XS = [round(0.1 + 0.02 * i, 6) for i in range(45)]  # 0.10 .. 0.98, all < x_gojo


def test_omega_values_match_core_to_few_ulp() -> None:
    got = nb.omega_values(_XS)
    ref = np.array([conformal_factor(x) for x in _XS], dtype=np.float64)
    ulp = _max_ulp(got, ref)
    assert np.allclose(got, ref, atol=1e-12, rtol=0), f"max ULP diff = {ulp}"
    assert ulp <= 4, f"Omega parity drifted: max ULP diff = {ulp}"


def test_metric_g11_values_match_core_to_few_ulp() -> None:
    got = nb.metric_g11_values(_XS)
    ref = np.array([metric_g11(x) for x in _XS], dtype=np.float64)
    ulp = _max_ulp(got, ref)
    assert np.allclose(got, ref, atol=1e-12, rtol=0), f"max ULP diff = {ulp}"
    assert ulp <= 8, f"metric parity drifted: max ULP diff = {ulp}"


def test_felt_ds_values_match_core_to_few_ulp() -> None:
    dx = 0.1
    got = nb.felt_ds_values(_XS, dx)
    ref = np.array([felt_step(x, dx) for x in _XS], dtype=np.float64)
    ulp = _max_ulp(got, ref)
    assert np.allclose(got, ref, atol=1e-12, rtol=0), f"max ULP diff = {ulp}"
    assert ulp <= 4, f"felt-step parity drifted: max ULP diff = {ulp}"


def test_omega_values_reject_point_at_or_past_pole() -> None:
    with pytest.raises(ValueError):
        nb.omega_values([0.5, X_GOJO])
    with pytest.raises(ValueError):
        nb.omega_values([0.5, 1.5])


# ---------------------------------------------------------------------------
# Riemannian quadratures: finite pre-singularity geodesic length (<= few ULP)
# ---------------------------------------------------------------------------

def _omega(x: float) -> float:
    return conformal_factor(x, x_gojo=X_GOJO, sigma=DEFAULT_SIGMA, lam=DEFAULT_LAMBDA)


@pytest.mark.parametrize("a,b,n", [(0.1, 0.7, 1000), (0.0, 0.5, 500), (0.2, 0.9, 2048)])
def test_geodesic_trapezoid_matches_core_quadrature(a: float, b: float, n: int) -> None:
    got = nb.geodesic_partial_length(a, b, n=n)
    ref = trapezoid_integral(_omega, a, b, n)
    ulp = _max_ulp(got, ref)
    assert np.allclose(got, ref, atol=1e-12, rtol=0), f"max ULP diff = {ulp}"


@pytest.mark.parametrize("a,b,n", [(0.1, 0.7, 1000), (0.0, 0.5, 500), (0.2, 0.9, 2048)])
def test_geodesic_midpoint_matches_core_quadrature(a: float, b: float, n: int) -> None:
    got = nb.geodesic_partial_length_midpoint(a, b, n=n)
    ref = midpoint_integral(_omega, a, b, n)
    ulp = _max_ulp(got, ref)
    assert np.allclose(got, ref, atol=1e-12, rtol=0), f"max ULP diff = {ulp}"


def test_geodesic_rejects_pole_and_bad_bounds() -> None:
    with pytest.raises(ValueError):
        nb.geodesic_partial_length(0.1, X_GOJO)          # b at the pole
    with pytest.raises(ValueError):
        nb.geodesic_partial_length(0.7, 0.1)             # b < a
    with pytest.raises(ValueError):
        nb.geodesic_partial_length(0.1, 0.7, n=0)        # n < 1


def test_geodesic_zero_width_is_zero() -> None:
    assert nb.geodesic_partial_length(0.3, 0.3) == 0.0
    assert nb.geodesic_partial_length_midpoint(0.3, 0.3) == 0.0


# ---------------------------------------------------------------------------
# Measure: covering lengths eps/2^n  (bit-identical)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("eps", [0.1, 1.0, 0.001, 0.25])
def test_cover_interval_lengths_are_bit_identical(eps: float) -> None:
    count = 40
    got = nb.cover_interval_lengths(eps, count)
    ref = np.array(
        [float(cover_interval_length(n, eps)) for n in range(1, count + 1)],
        dtype=np.float64,
    )
    assert np.array_equal(got, ref), f"max ULP diff = {_max_ulp(got, ref)}"


def test_cover_interval_lengths_validate() -> None:
    with pytest.raises(ValueError):
        nb.cover_interval_lengths(0.0, 5)
    with pytest.raises(ValueError):
        nb.cover_interval_lengths(0.1, 0)


# ---------------------------------------------------------------------------
# Zeno: float views of S_n and (1/2)^n  (bit-identical)
# ---------------------------------------------------------------------------

def test_zeno_partial_sums_are_bit_identical() -> None:
    max_n = 60
    got = nb.zeno_partial_sums(max_n)
    ref = np.array([float(partial_sum(n)) for n in range(1, max_n + 1)],
                   dtype=np.float64)
    assert np.array_equal(got, ref), f"max ULP diff = {_max_ulp(got, ref)}"


def test_zeno_residuals_are_bit_identical() -> None:
    max_n = 60
    got = nb.zeno_residuals(max_n)
    ref = np.array([float(residual(n)) for n in range(1, max_n + 1)],
                   dtype=np.float64)
    assert np.array_equal(got, ref), f"max ULP diff = {_max_ulp(got, ref)}"


def test_zeno_validate() -> None:
    with pytest.raises(ValueError):
        nb.zeno_partial_sums(0)
    with pytest.raises(ValueError):
        nb.zeno_residuals(0)


# ---------------------------------------------------------------------------
# The fast-paths are genuinely lazy: importing the module never imports numpy
# ---------------------------------------------------------------------------

def test_module_has_no_top_level_numpy_binding() -> None:
    # numpy is reached only via commons.core.optional.try_import inside functions;
    # there must be no module-level ``numpy`` attribute on the backend.
    assert not hasattr(nb, "numpy")
    assert not hasattr(nb, "np")
