"""The Rickness score and the algebraic constraints that carve the ridge.

Rickness is a *deterministic* function of a universe's coordinates -- a weighted
combination of two bounded "genius" proxies minus a heavily-weighted "harmony
penalty"::

    rickness(x) = w_complexity * complexity(x)
                + w_entropy    * entropy(x)
                - w_penalty    * penalty(x)

The honest math:

* ``complexity(x)`` -- ``tanh(std(x) / 2)`` in ``[0, 1)``. Rewards a universe whose
  coordinates are *spread out* (a bland uniform universe is boring). Bounded, so it
  cannot run away to infinity.
* ``entropy(x)`` -- normalised Shannon entropy of ``softmax(|x|)`` in ``[0, 1]``.
  Rewards universes that distribute their "mass" across many dimensions.
* ``penalty(x)`` -- sum of squared residuals of algebraic constraints
  ``g_k(x) = 0``. Their common zero-set is a lower-dimensional MANIFOLD embedded in
  ``R^D``. Because the penalty is heavily weighted, the near-maximal set is a thin
  tube hugging that manifold -- this is what makes the maximum a *ridge* (a whole
  sub-manifold) rather than an isolated point.

With ``dim = 8`` the four constraints pin ~4 of the 8 degrees of freedom, leaving a
~4-dimensional ridge; dim 7 is entirely free.

Purity: imports only the standard library and :mod:`commons.core`.
"""

from __future__ import annotations

import math
from typing import List, Sequence

from commons.core.rng import DeterministicRNG

from central_finite_curve.core.config import DEFAULT, CurveConfig
from central_finite_curve.core.sampling import gauss_vector

Vector = Sequence[float]


def complexity(x: Vector) -> float:
    """Spread proxy in ``[0, 1)``: ``tanh`` of the coordinate standard deviation."""
    n = len(x)
    if n == 0:
        return 0.0
    mean = sum(x) / n
    var = sum((xi - mean) ** 2 for xi in x) / n
    std = math.sqrt(var)
    return math.tanh(std / 2.0)


def entropy(x: Vector) -> float:
    """Normalised Shannon entropy of ``softmax(|x|)``, in ``[0, 1]``."""
    n = len(x)
    if n < 2:
        return 0.0
    mags = [abs(xi) for xi in x]
    m = max(mags)
    # Numerically stable softmax over magnitudes.
    exps = [math.exp(mi - m) for mi in mags]
    total = sum(exps)
    if total <= 0.0:
        return 0.0
    probs = [e / total for e in exps]
    h = -sum(p * math.log(p) for p in probs if p > 0.0)
    return h / math.log(n)


def residuals(x: Vector, config: CurveConfig = DEFAULT) -> List[float]:
    """Algebraic constraints whose common zero-set defines the manifold.

    With ``dim = 8`` these four constraints pin ~4 of the 8 degrees of freedom:

      * ``g0``: dims (0, 1) lie on a circle of radius ``ring_radius`` (the "ring").
      * ``g1``: dim 2 is tied to dim 0 via a sine wave.
      * ``g2``: dims (3, 4) are mirror images (sum to zero).
      * ``g3``: dims (5, 6) form a reciprocal pair (product = 1).

    Dim 7 is entirely free.
    """
    r = config.ring_radius
    g0 = x[0] * x[0] + x[1] * x[1] - r * r
    g1 = x[2] - math.sin(math.pi * x[0])
    g2 = x[3] + x[4]
    g3 = x[5] * x[6] - 1.0
    return [g0, g1, g2, g3]


def penalty(x: Vector, config: CurveConfig = DEFAULT) -> float:
    """Sum of squared constraint residuals. Zero exactly on the manifold."""
    return sum(r * r for r in residuals(x, config))


def rickness(x: Vector, config: CurveConfig = DEFAULT) -> float:
    """The full weighted Rickness score of a universe ``x``."""
    return (
        config.w_complexity * complexity(x)
        + config.w_entropy * entropy(x)
        - config.w_penalty * penalty(x, config)
    )


def project_onto_manifold(
    free: Sequence[float],
    rng: DeterministicRNG,
    config: CurveConfig = DEFAULT,
) -> List[float]:
    """Construct a point that lies (near) exactly on the manifold.

    Given four free parameters ``(t, a, b, c)`` this solves the constraints so the
    penalty is ~0, then adds a tiny reproducible Gaussian jitter (drawn from
    ``rng``) so the near-manifold band stays populated rather than degenerate. Used
    by the generator to seed the rare "Rick-ish" universes.
    """
    t, a, b, c = free
    r = config.ring_radius
    x0 = r * math.cos(t)
    x1 = r * math.sin(t)
    x2 = math.sin(math.pi * x0)
    x3 = a
    x4 = -a
    # Keep b away from zero so the reciprocal pair is well-conditioned.
    b = b if abs(b) > 0.3 else 0.3
    x5 = b
    x6 = 1.0 / b
    x7 = c
    point = [x0, x1, x2, x3, x4, x5, x6, x7]
    if config.dim > 8:
        point.extend(0.0 for _ in range(config.dim - 8))
    jitter = gauss_vector(rng, config.dim, config.jitter_sigma)
    return [p + j for p, j in zip(point, jitter)]
