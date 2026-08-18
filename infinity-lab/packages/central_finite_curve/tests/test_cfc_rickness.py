"""The Rickness score: deterministic, bounded proxies, higher near the manifold.

Asserts the honest-math contract:

* ``complexity`` in ``[0, 1)`` and ``entropy`` in ``[0, 1]`` (bounded proxies).
* ``penalty`` is zero exactly on the manifold and positive off it.
* ``rickness`` is a pure deterministic function (same input -> same output).
* near-manifold points score STRICTLY higher than uniform-box junk (the ridge is
  where the genius lives).
"""

from __future__ import annotations

import math

from central_finite_curve.core.rickness import (
    complexity,
    entropy,
    penalty,
    project_onto_manifold,
    rickness,
)
from central_finite_curve.core.config import CurveConfig
from central_finite_curve.core.sampling import child_rng, uniform_vector

_CONFIG = CurveConfig()


def _on_manifold_free(rng, config):
    free = (
        rng.uniform(-math.pi, math.pi),
        rng.uniform(-2.0, 2.0),
        rng.uniform(-2.0, 2.0),
        rng.uniform(-config.box, config.box),
    )
    return free


def test_complexity_bounded() -> None:
    rng = child_rng(1, 1)
    for _ in range(50):
        x = uniform_vector(rng, _CONFIG.dim, _CONFIG.box)
        c = complexity(x)
        assert 0.0 <= c < 1.0


def test_entropy_bounded() -> None:
    rng = child_rng(2, 1)
    for _ in range(50):
        x = uniform_vector(rng, _CONFIG.dim, _CONFIG.box)
        e = entropy(x)
        assert 0.0 <= e <= 1.0 + 1e-12


def test_penalty_zero_on_manifold_positive_off() -> None:
    rng = child_rng(3, 1)
    # A point solved onto the manifold with zero jitter has ~zero penalty.
    cfg0 = CurveConfig(jitter_sigma=0.0)
    on = project_onto_manifold(_on_manifold_free(rng, cfg0), rng, cfg0)
    assert penalty(on, cfg0) < 1e-9
    junk = uniform_vector(rng, _CONFIG.dim, _CONFIG.box)
    assert penalty(junk, _CONFIG) > 0.0


def test_rickness_is_deterministic() -> None:
    rng = child_rng(4, 1)
    x = uniform_vector(rng, _CONFIG.dim, _CONFIG.box)
    assert rickness(x, _CONFIG) == rickness(list(x), _CONFIG)


def test_rickness_higher_near_manifold_than_junk() -> None:
    rng = child_rng(5, 1)
    near_scores = []
    junk_scores = []
    for _ in range(80):
        near = project_onto_manifold(_on_manifold_free(rng, _CONFIG), rng, _CONFIG)
        junk = uniform_vector(rng, _CONFIG.dim, _CONFIG.box)
        near_scores.append(rickness(near, _CONFIG))
        junk_scores.append(rickness(junk, _CONFIG))
    mean_near = sum(near_scores) / len(near_scores)
    mean_junk = sum(junk_scores) / len(junk_scores)
    assert mean_near > mean_junk
    # The best near-manifold point beats every junk point handily.
    assert max(near_scores) > max(junk_scores)
