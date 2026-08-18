"""Vectorised numpy fast-paths mirroring the pure float-valued core.

Every routine here reproduces, over a whole array at once, a scalar computation
that the pure :mod:`gojo_infinity.core` performs one element at a time. numpy is
NEVER imported at module top level: each function calls
:func:`commons.core.optional.try_import` lazily and raises
:class:`OptionalDependencyError` (a clear, deferred error) when numpy is absent,
so importing this module with the standard library alone never fails.

Parity honesty (what "mirrors" means for each group)
----------------------------------------------------
The mirrored operations fall into two buckets:

* **Bit-identical (exact)** -- operations that are pure exact-dyadic / power-of-two
  arithmetic, where numpy and the exact core round to the *same* IEEE-754 double:

  - :func:`cover_interval_lengths` -> ``eps / 2**n``. Division by a power of two
    is exact (an exponent shift), and matches ``float(eps * Fraction(1, 2**n))``.
  - :func:`zeno_residuals` -> ``(1/2)**n``. A power of two is exactly
    representable, matching ``float(half_power(n))``.
  - :func:`zeno_partial_sums` -> ``1 - (1/2)**n``. Because ``(1/2)**n`` is exact,
    ``1.0 - (1/2)**n`` rounds identically to ``float(1 - Fraction(1, 2**n))``.

  For these the parity test asserts **exact** elementwise equality.

* **Identical to <= 1 ULP** -- operations that route through the transcendental
  ``exp``. The pure core uses libm's :func:`math.exp`; numpy uses its own
  vectorised ``exp``. The two are *correctly rounded to within ~1 ULP of each
  other* (not guaranteed bit-identical by IEEE-754), so any value derived from
  the conformal factor may differ from the scalar core by at most a few ULP:

  - :func:`omega_values`     -> ``Omega(x)`` (one ``exp`` per element).
  - :func:`metric_g11_values`-> ``Omega(x)**2``.
  - :func:`felt_ds_values`   -> ``Omega(x) * dx``.

  The parity test asserts ``numpy.allclose(atol=1e-12, rtol=0)`` and reports the
  observed max ULP distance in the assertion message.

* **Identical to <= a few ULP (reduction order differs)** -- the quadratures sum
  many terms. The pure ``commons.core`` quadratures reduce with exact
  :func:`math.fsum`; numpy reduces with pairwise summation. Same summands (up to
  the per-element ``exp`` ULP above), different reduction order, so the totals
  agree to a few ULP rather than bit-for-bit:

  - :func:`geodesic_partial_length`          -> composite TRAPEZOID, mirroring
    :func:`commons.core.trapezoid_integral` of ``Omega`` on ``[a, b]``.
  - :func:`geodesic_partial_length_midpoint` -> composite MIDPOINT, mirroring
    :func:`commons.core.midpoint_integral` of ``Omega`` on ``[a, b]``.

  These are the FINITE, pre-singularity geodesic partial lengths (``b < x_gojo``);
  the improper divergence to the pole stays the pure core's explicit ``math.inf``.
"""

from __future__ import annotations

from typing import Any

from commons.core.optional import try_import

from gojo_infinity.core.riemannian import (
    DEFAULT_LAMBDA,
    DEFAULT_SIGMA,
    X_GOJO,
)


class OptionalDependencyError(RuntimeError):
    """Raised when a numpy fast-path is requested but numpy is unavailable.

    The pure core never raises this; only these deferred accel routines do, and
    only when the caller invokes them without numpy installed.
    """


def _numpy() -> Any:
    """Return the numpy module, or raise :class:`OptionalDependencyError`.

    numpy is imported LAZILY (inside the call) via
    :func:`commons.core.optional.try_import`, so this module stays importable
    with the standard library alone.
    """
    np = try_import("numpy")
    if np is None:
        raise OptionalDependencyError(
            "numpy is required for gojo_infinity.accel fast-paths but is not "
            "installed; install the 'viz' extra (pip install -e '.[viz]') or use "
            "the pure gojo_infinity.core functions instead"
        )
    return np


# ---------------------------------------------------------------------------
# Riemannian: Omega(x), the metric g = Omega^2, and ds = Omega * dx
# ---------------------------------------------------------------------------

def omega_values(xs: Any, *, x_gojo: float = X_GOJO, sigma: float = DEFAULT_SIGMA,
                 lam: float = DEFAULT_LAMBDA) -> Any:
    """Vectorised conformal factor ``Omega(x) = 1 + lam*K(x, x_gojo)/(x_gojo - x)``.

    Mirrors :func:`gojo_infinity.core.conformal_factor` elementwise, with the
    RIKEN Gaussian kernel ``K(x, x_gojo) = exp(-(x - x_gojo)**2 / sigma**2)``.
    Every ``x`` must satisfy ``x < x_gojo`` (the metric has a simple pole at
    ``x_gojo``). Identical to the scalar core to within ~1 ULP (libm ``exp`` vs
    numpy ``exp``). Raises :class:`ValueError` for ``lam < 0``, ``sigma <= 0`` or
    any ``x >= x_gojo``; :class:`OptionalDependencyError` when numpy is absent.
    """
    if lam < 0:
        raise ValueError("lam must be non-negative")
    if sigma <= 0:
        raise ValueError("sigma must be positive")
    np = _numpy()
    arr = np.asarray(xs, dtype=np.float64)
    gap = x_gojo - arr
    if np.any(gap <= 0.0):
        raise ValueError("omega_values is defined only for x < x_gojo")
    d = arr - x_gojo
    kernel = np.exp(-(d * d) / (sigma * sigma))
    return 1.0 + lam * kernel / gap


def metric_g11_values(xs: Any, *, x_gojo: float = X_GOJO, sigma: float = DEFAULT_SIGMA,
                      lam: float = DEFAULT_LAMBDA) -> Any:
    """Vectorised metric component ``g_11(x) = Omega(x)**2``.

    Mirrors :func:`gojo_infinity.core.metric_g11` elementwise (identical to the
    scalar core to within a few ULP through the shared ``exp``).
    """
    omega = omega_values(xs, x_gojo=x_gojo, sigma=sigma, lam=lam)
    return omega * omega


def felt_ds_values(xs: Any, dx: float, *, x_gojo: float = X_GOJO,
                   sigma: float = DEFAULT_SIGMA, lam: float = DEFAULT_LAMBDA) -> Any:
    """Vectorised felt step ``ds = Omega(x) * dx`` over a grid of ``x`` values.

    Mirrors :func:`gojo_infinity.core.felt_step` elementwise. Raises
    :class:`ValueError` for ``dx < 0`` (matching the scalar core).
    """
    if dx < 0:
        raise ValueError("dx must be non-negative")
    omega = omega_values(xs, x_gojo=x_gojo, sigma=sigma, lam=lam)
    return omega * dx


def _quadrature_abscissae(np: Any, a: float, b: float, n: int) -> Any:
    """Uniform grid ``a + i*h`` for ``i in 0..n`` with ``h = (b - a)/n``.

    Built as ``a + h * arange(n + 1)`` so each abscissa equals the scalar core's
    ``a + i * h`` bit-for-bit (``i*h`` and ``h*i`` round identically).
    """
    h = (b - a) / n
    return a + h * np.arange(n + 1, dtype=np.float64)


def geodesic_partial_length(a: float, b: float, *, n: int = 1000,
                            x_gojo: float = X_GOJO, sigma: float = DEFAULT_SIGMA,
                            lam: float = DEFAULT_LAMBDA) -> float:
    """Finite geodesic partial length ``integral_a^b Omega(x) dx`` (TRAPEZOID rule).

    Composite trapezoid on ``n`` uniform panels, mirroring
    :func:`commons.core.trapezoid_integral` applied to ``Omega``. This is the
    FINITE, pre-singularity length: ``b`` must satisfy ``b < x_gojo`` (the
    improper divergence to the pole stays the pure core's explicit ``math.inf``).

    numpy reduces with pairwise summation while the pure quadrature uses exact
    :func:`math.fsum`, so the totals agree to a few ULP (see the module
    docstring). Raises :class:`ValueError` for ``n < 1``, ``b < a`` or
    ``b >= x_gojo``.
    """
    if n < 1:
        raise ValueError("n must be >= 1")
    if b < a:
        raise ValueError("require a <= b")
    if b >= x_gojo:
        raise ValueError("geodesic_partial_length is finite only for b < x_gojo")
    np = _numpy()
    if a == b:
        return 0.0
    xs = _quadrature_abscissae(np, a, b, n)
    ys = omega_values(xs, x_gojo=x_gojo, sigma=sigma, lam=lam)
    h = (b - a) / n
    return float(np.trapezoid(ys, dx=h))


def geodesic_partial_length_midpoint(a: float, b: float, *, n: int = 1000,
                                     x_gojo: float = X_GOJO,
                                     sigma: float = DEFAULT_SIGMA,
                                     lam: float = DEFAULT_LAMBDA) -> float:
    """Finite geodesic partial length ``integral_a^b Omega(x) dx`` (MIDPOINT rule).

    Composite midpoint on ``n`` uniform panels, mirroring
    :func:`commons.core.midpoint_integral` applied to ``Omega``. Same finite,
    pre-singularity contract as :func:`geodesic_partial_length` (``b < x_gojo``).
    numpy pairwise summation vs the pure ``math.fsum`` gives a few-ULP agreement.
    Raises :class:`ValueError` for ``n < 1``, ``b < a`` or ``b >= x_gojo``.
    """
    if n < 1:
        raise ValueError("n must be >= 1")
    if b < a:
        raise ValueError("require a <= b")
    if b >= x_gojo:
        raise ValueError("geodesic_partial_length is finite only for b < x_gojo")
    np = _numpy()
    if a == b:
        return 0.0
    h = (b - a) / n
    mids = a + (np.arange(n, dtype=np.float64) + 0.5) * h
    ys = omega_values(mids, x_gojo=x_gojo, sigma=sigma, lam=lam)
    return float(h * np.sum(ys))


# ---------------------------------------------------------------------------
# Measure: the covering lengths eps / 2^n
# ---------------------------------------------------------------------------

def cover_interval_lengths(eps: float, count: int) -> Any:
    """Vectorised covering lengths ``[eps/2, eps/4, ..., eps/2**count]``.

    Mirrors ``float(gojo_infinity.core.cover_interval_length(n, eps))`` for
    ``n = 1..count``. Because each divisor is a power of two, the division is
    exact, so this is **bit-identical** to the exact core's float view. Requires
    ``eps > 0`` and ``count >= 1``. Raises :class:`OptionalDependencyError` when
    numpy is absent.
    """
    if eps <= 0:
        raise ValueError("eps must be positive")
    if count < 1:
        raise ValueError("count must be >= 1")
    np = _numpy()
    n = np.arange(1, count + 1, dtype=np.float64)
    return float(eps) / np.power(2.0, n)


# ---------------------------------------------------------------------------
# Zeno: float views of the partial sums S_n and residuals (1/2)^n
# ---------------------------------------------------------------------------

def zeno_partial_sums(max_n: int) -> Any:
    """Vectorised Zeno partial sums ``[S_1, ..., S_max_n]`` with ``S_n = 1-(1/2)**n``.

    Mirrors ``float(gojo_infinity.core.partial_sum(n))`` for ``n = 1..max_n``.
    Because ``(1/2)**n`` is exactly representable, ``1 - (1/2)**n`` rounds
    identically to the exact-Fraction float view, so this is **bit-identical**.
    The EXACT-Fraction partial sums stay in the pure core; this only mirrors the
    float view. Requires ``max_n >= 1``.
    """
    if max_n < 1:
        raise ValueError("max_n must be >= 1")
    np = _numpy()
    n = np.arange(1, max_n + 1, dtype=np.float64)
    return 1.0 - np.power(0.5, n)


def zeno_residuals(max_n: int) -> Any:
    """Vectorised Zeno residual gaps ``[(1/2)**1, ..., (1/2)**max_n]``.

    Mirrors ``float(gojo_infinity.core.residual(n))`` for ``n = 1..max_n``. A
    power of two is exactly representable, so this is **bit-identical** to the
    exact core's float view. The exact strict-positivity certificate (which stays
    positive past float underflow at ``n = 1075``) lives in the pure core; this
    float mirror underflows to ``0.0`` for large ``n`` by design. Requires
    ``max_n >= 1``.
    """
    if max_n < 1:
        raise ValueError("max_n must be >= 1")
    np = _numpy()
    n = np.arange(1, max_n + 1, dtype=np.float64)
    return np.power(0.5, n)
