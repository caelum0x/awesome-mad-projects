"""Lens 3 -- Riemannian conformal geometry. Verdict: FORMIDABLE.

The essay's strongest reading (echoed by the RIKEN "Jujutsu Kaisen: Abyss of
Math" course). Instead of flat space ``ds^2 = dx^2``, space near Gojo carries a
conformal Riemannian metric

    ds = Omega(x) dx,     g_11(x) = Omega(x)^2,

whose factor is built from the RIKEN Gaussian (RBF) kernel of width ``sigma``:

    K(x, y) = exp(-|x - y|^2 / sigma^2),
    Omega(x) = 1 + lambda * K(x, x_g) / (x_g - x),     x_g = 1.

Far from Gojo ``Omega ~ 1`` (space is Euclidean); as ``x -> x_g`` the simple pole
``1/(x_g - x)`` drives ``Omega -> +infinity``. The felt geodesic length

    L(x0) = integral_{x0}^{x_g} Omega(x) dx

is an IMPROPER integral that DIVERGES: near ``x_g`` the integrand behaves like
``lambda / (x_g - x)``, whose antiderivative ``-lambda * ln(x_g - x)`` runs off to
``+infinity``. An attacker must cross an infinite amount of *felt* distance, so
every strike slows to a halt. Infinity is FORMIDABLE.

Design notes honoured here:
  * The improper geodesic to the barrier returns ``math.inf`` **explicitly** --
    it is never approximated by a large finite number.
  * A weak finite quadrature is kept ONLY as a clearly-labelled
    "float fails here" demonstration (:func:`naive_geodesic_to_barrier`); it is
    never the source of truth.
  * ``calibrate`` DERIVES ``lambda`` from the essay's Figure-8 targets via
    bisection (``commons.core.bisection``) rather than hardcoding it.

Pure core: stdlib + ``commons.core`` only (uses commons ``bisection`` and
``adaptive_integral``).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from commons.core import adaptive_integral, bisection

from gojo_infinity.core.verdicts import RIEMANNIAN_VERDICT, Verdict

# ---------------------------------------------------------------------------
# Calibration constants (defaults reproduce the essay's Figure-8 numbers)
# ---------------------------------------------------------------------------

X_GOJO: float = 1.0        # Gojo stands at x = 1.0; attackers approach from x < 1
DEFAULT_SIGMA: float = 0.35  # RIKEN Gaussian-kernel width

# Derived by calibrate() (bisection on the g(0.8) = 4.1 target); this literal is
# only a convenience default and is asserted against calibrate() in the tests.
DEFAULT_LAMBDA: float = 0.28411810581225466

# Figure-8 targets used for calibration / assertions:
#   FAR  (Step A): x = 0.1, dx = 0.1  ->  g = Omega^2 ~ 1.0,  felt ds ~ 0.10
#   NEAR (Step B): x = 0.8, dx = 0.1  ->  g = Omega^2 ~ 4.1,  felt ds ~ 0.20


class CalibrationError(RuntimeError):
    """Raised when :func:`calibrate` cannot fit the requested targets.

    Chosen policy: **hard fail with a clear message** (rather than silently
    falling back to defaults). Callers that want the documented defaults can use
    :data:`DEFAULT_SIGMA` / :data:`DEFAULT_LAMBDA` directly.
    """


# ---------------------------------------------------------------------------
# Metrics and the RIKEN Gaussian kernel
# ---------------------------------------------------------------------------

def euclidean_line_element(dx: float, dy: float = 0.0, dz: float = 0.0) -> float:
    """Flat line element ``ds = sqrt(dx^2 + dy^2 + dz^2)`` (for contrast)."""
    return math.sqrt(dx * dx + dy * dy + dz * dz)


def gaussian_kernel(x: float, y: float, sigma: float = DEFAULT_SIGMA) -> float:
    """RIKEN Gaussian (RBF) kernel ``K(x, y) = exp(-|x - y|^2 / sigma^2)``.

    Raises :class:`ValueError` for ``sigma <= 0``.
    """
    if sigma <= 0:
        raise ValueError("sigma must be positive")
    d = x - y
    return math.exp(-(d * d) / (sigma * sigma))


def conformal_factor(x: float, *, x_gojo: float = X_GOJO,
                     sigma: float = DEFAULT_SIGMA,
                     lam: float = DEFAULT_LAMBDA) -> float:
    """Conformal factor ``Omega(x) = 1 + lam * K(x, x_gojo) / (x_gojo - x)``.

    Defined only for ``x < x_gojo`` (the metric has a simple pole exactly at
    ``x_gojo``). It is ``~1`` far away and diverges to ``+infinity`` as
    ``x -> x_gojo``. Raises :class:`ValueError` for ``lam < 0`` or ``gap <= 0``.
    """
    if lam < 0:
        raise ValueError("lam must be non-negative")
    gap = x_gojo - x
    if gap <= 0:
        raise ValueError("conformal_factor is defined only for x < x_gojo")
    return 1.0 + lam * gaussian_kernel(x, x_gojo, sigma) / gap


def metric_g11(x: float, *, x_gojo: float = X_GOJO,
               sigma: float = DEFAULT_SIGMA,
               lam: float = DEFAULT_LAMBDA) -> float:
    """Metric component ``g_11(x) = Omega(x)^2`` (the essay's "g")."""
    omega = conformal_factor(x, x_gojo=x_gojo, sigma=sigma, lam=lam)
    return omega * omega


def felt_step(x: float, dx: float, *, x_gojo: float = X_GOJO,
              sigma: float = DEFAULT_SIGMA, lam: float = DEFAULT_LAMBDA) -> float:
    """Felt (Riemannian) length of a small physical step: ``ds = Omega(x) * dx``."""
    if dx < 0:
        raise ValueError("dx must be non-negative")
    return conformal_factor(x, x_gojo=x_gojo, sigma=sigma, lam=lam) * dx


def near_pole_asymptote(x: float, *, x_gojo: float = X_GOJO,
                        lam: float = DEFAULT_LAMBDA) -> float:
    """Leading asymptotic behaviour of ``Omega`` near the pole: ``lam / (x_gojo - x)``."""
    gap = x_gojo - x
    if gap <= 0:
        raise ValueError("asymptote is defined only for x < x_gojo")
    return lam / gap


# ---------------------------------------------------------------------------
# Calibration: DERIVE lambda from the Figure-8 targets by bisection
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CalibrationResult:
    """Result of fitting the conformal factor to the essay's Figure-8 targets."""

    sigma: float
    lam: float
    g_far: float     # achieved g_11 at x_far  (target ~ 1.0)
    ds_far: float    # achieved felt step at x_far with dx  (target ~ 0.10)
    g_near: float    # achieved g_11 at x_near (target ~ 4.1)
    ds_near: float   # achieved felt step at x_near with dx (target ~ 0.20)


def calibrate(*, sigma: float = DEFAULT_SIGMA,
              x_far: float = 0.1, g_far_target: float = 1.0,
              x_near: float = 0.8, g_near_target: float = 4.1,
              dx: float = 0.1, x_gojo: float = X_GOJO,
              lam_hi: float = 10.0, far_abs_tol: float = 0.05) -> CalibrationResult:
    """Fit ``(sigma, lam)`` to the essay's Figure-8 targets.

    Strategy: ``sigma`` is taken from the RIKEN default; ``lam`` is DERIVED by
    bisection so that ``g_11(x_near) = g_near_target`` (default ``g(0.8) = 4.1``).
    Because ``Omega`` is strictly increasing in ``lam``, the target is bracketed
    by ``lam in [0, lam_hi]`` and solved with :func:`commons.core.bisection`.

    The far target ``g_11(x_far) ~ g_far_target`` (default ``g(0.1) ~ 1.0``) is
    then *verified* -- it is satisfied automatically for sensible ``sigma`` since
    the kernel is negligible far from the pole. If either the bracket fails or
    the far target is missed, this **raises** :class:`CalibrationError` with a
    clear message (no silent fallback).
    """
    if g_near_target <= 1.0:
        raise CalibrationError("g_near_target must exceed 1 (Omega > 1 near the pole)")

    omega_target = math.sqrt(g_near_target)

    def residual(lam: float) -> float:
        return conformal_factor(x_near, x_gojo=x_gojo, sigma=sigma, lam=lam) - omega_target

    # residual is monotone increasing in lam: residual(0) = 1 - omega_target < 0.
    if residual(lam_hi) <= 0.0:
        raise CalibrationError(
            f"bracket [0, {lam_hi}] does not straddle g_near_target={g_near_target}; "
            "increase lam_hi or lower the target"
        )

    lam = bisection(residual, 0.0, lam_hi)

    g_far = metric_g11(x_far, x_gojo=x_gojo, sigma=sigma, lam=lam)
    if not math.isclose(g_far, g_far_target, abs_tol=far_abs_tol):
        raise CalibrationError(
            f"far target missed: g_11({x_far})={g_far:.4f} not within "
            f"{far_abs_tol} of {g_far_target}"
        )

    return CalibrationResult(
        sigma=sigma,
        lam=lam,
        g_far=g_far,
        ds_far=felt_step(x_far, dx, x_gojo=x_gojo, sigma=sigma, lam=lam),
        g_near=metric_g11(x_near, x_gojo=x_gojo, sigma=sigma, lam=lam),
        ds_near=felt_step(x_near, dx, x_gojo=x_gojo, sigma=sigma, lam=lam),
    )


# ---------------------------------------------------------------------------
# Geodesic (felt) length and its divergence
# ---------------------------------------------------------------------------

def geodesic_length(x0: float, cutoff: float, *, x_gojo: float = X_GOJO,
                    sigma: float = DEFAULT_SIGMA, lam: float = DEFAULT_LAMBDA,
                    tol: float = 1e-9) -> float:
    """Felt length ``integral_{x0}^{cutoff} Omega(x) dx``.

    * If ``cutoff >= x_gojo`` the integral is IMPROPER (the integrand has a
      non-integrable simple pole at ``x_gojo``) and diverges -- this returns
      ``math.inf`` **explicitly**, a genuine float distinct from any finite value.
    * If ``x0 < cutoff < x_gojo`` the integrand is bounded, and the finite value
      is computed with :func:`commons.core.adaptive_integral`.

    Raises :class:`ValueError` for ``cutoff < x0`` or ``x0 >= x_gojo``.
    """
    if x0 >= x_gojo:
        raise ValueError("require x0 < x_gojo (attacker starts before the barrier)")
    if cutoff < x0:
        raise ValueError("require cutoff >= x0")
    if cutoff >= x_gojo:
        return math.inf

    def integrand(x: float) -> float:
        return conformal_factor(x, x_gojo=x_gojo, sigma=sigma, lam=lam)

    return adaptive_integral(integrand, x0, cutoff, tol=tol)


def geodesic_to_barrier(x0: float, *, x_gojo: float = X_GOJO,
                        sigma: float = DEFAULT_SIGMA,
                        lam: float = DEFAULT_LAMBDA) -> float:
    """The felt distance all the way to Gojo: ``math.inf`` (the barrier is infinite).

    Convenience alias for ``geodesic_length(x0, x_gojo, ...)`` documenting that
    the improper integral to the pole diverges. The return is the literal
    ``math.inf``, type-distinct from the ``None`` returned across a topological
    cut (Lens 4) and from any finite proper length.
    """
    return geodesic_length(x0, x_gojo, x_gojo=x_gojo, sigma=sigma, lam=lam)


def naive_geodesic_to_barrier(x0: float, *, eps: float = 1e-9, steps: int = 200000,
                              x_gojo: float = X_GOJO, sigma: float = DEFAULT_SIGMA,
                              lam: float = DEFAULT_LAMBDA) -> float:
    """FAILURE-mode DEMO: a weak finite midpoint sum stopped ``eps`` short of the pole.

    This returns a large but FINITE number and is kept ONLY to demonstrate that
    naive float quadrature cannot see the divergence -- it silently reports a
    finite "distance" no matter how the truncation ``eps`` is chosen. It is
    **never** the source of truth; the honest answer is
    :func:`geodesic_to_barrier` (``math.inf``). The true tail beyond the cutoff
    is ``-lam * ln(eps) -> +infinity`` as ``eps -> 0``, which this sum omits.
    """
    if not (0 < eps < x_gojo - x0):
        raise ValueError("require 0 < eps < x_gojo - x0")
    if steps < 1:
        raise ValueError("steps must be >= 1")
    cutoff = x_gojo - eps
    h = (cutoff - x0) / steps
    total = 0.0
    for i in range(steps):
        x = x0 + (i + 0.5) * h
        total += conformal_factor(x, x_gojo=x_gojo, sigma=sigma, lam=lam) * h
    return total


def divergence_by_decade(x0: float, deltas: list[float], *,
                         x_gojo: float = X_GOJO, sigma: float = DEFAULT_SIGMA,
                         lam: float = DEFAULT_LAMBDA,
                         tol: float = 1e-11) -> list[tuple[float, float]]:
    """Felt length to cutoff ``x_gojo - delta`` for each ``delta`` (finite, growing).

    Returns ``[(delta, L), ...]``. As ``delta -> 0`` the length keeps growing; the
    increment per DECADE of ``delta`` tends to ``lam * ln(10)`` (the
    ``-lam * ln(delta)`` tail of the improper integral). This unbounded growth is
    the quantitative statement of "every attack slows to a halt".
    """
    out: list[tuple[float, float]] = []
    for delta in deltas:
        if not (0 < delta < x_gojo - x0):
            raise ValueError("each delta must satisfy 0 < delta < x_gojo - x0")
        cutoff = x_gojo - delta
        out.append((delta, geodesic_length(x0, cutoff, x_gojo=x_gojo,
                                            sigma=sigma, lam=lam, tol=tol)))
    return out


def per_decade_increment(lam: float = DEFAULT_LAMBDA) -> float:
    """Asymptotic felt-length gain per decade of the cutoff: ``lam * ln(10)``."""
    return lam * math.log(10.0)


def geodesic_ball_radius_solve(x0: float, felt_radius: float, *,
                               x_gojo: float = X_GOJO, sigma: float = DEFAULT_SIGMA,
                               lam: float = DEFAULT_LAMBDA,
                               edge_eps: float = 1e-9, tol: float = 1e-9) -> float:
    """Find ``x* in (x0, x_gojo)`` whose felt distance from ``x0`` equals ``felt_radius``.

    Because ``L(x0, x)`` is continuous and strictly increasing from ``0`` toward
    ``+infinity`` as ``x -> x_gojo``, every finite ``felt_radius > 0`` is achieved
    at a unique interior ``x*``. Solved by bisection on
    ``L(x0, x) - felt_radius``. Raises :class:`ValueError` for non-positive
    ``felt_radius`` or if the (huge) upper bracket still cannot reach it.
    """
    if felt_radius <= 0:
        raise ValueError("felt_radius must be positive")

    hi = x_gojo - edge_eps

    def residual(x: float) -> float:
        return geodesic_length(x0, x, x_gojo=x_gojo, sigma=sigma, lam=lam, tol=tol) - felt_radius

    if residual(hi) < 0.0:
        raise ValueError(
            "felt_radius exceeds the length reachable before edge_eps; "
            "shrink edge_eps to reach larger radii"
        )
    return bisection(residual, x0, hi, tol=tol)


# ---------------------------------------------------------------------------
# Verdict
# ---------------------------------------------------------------------------

def verdict() -> Verdict:
    """Riemannian verdict: FORMIDABLE -- the felt geodesic length diverges."""
    return RIEMANNIAN_VERDICT
