"""The portal gun: every sampled state stays in the band, plausible accept ratio.

Asserts the hard-constraint Metropolis contract:

* EVERY recorded state has ``score >= band_low`` (the walk never falls off the ridge),
* the acceptance ratio lies strictly in ``(0, 1)`` (it moves, but not freely),
* the trajectory has ``walk_steps + 1`` points, and
* the walk is reproducible under a fixed seed (identical points AND accept ratio).
"""

from __future__ import annotations

from central_finite_curve.core import curve as curve_mod
from central_finite_curve.core import multiverse as multiverse_mod
from central_finite_curve.core import portal_gun as portal_gun_mod
from central_finite_curve.core.config import CurveConfig
from central_finite_curve.core.sampling import child_rng

_CONFIG = CurveConfig(n_universes=1500, walk_steps=800, seed=137)


def _walk(config: CurveConfig):
    universes = multiverse_mod.generate(child_rng(config.seed, 1), config)
    curve = curve_mod.extract(universes, config)
    walk = portal_gun_mod.travel(curve, child_rng(config.seed, 2), config)
    return curve, walk


def test_every_sampled_point_stays_in_band() -> None:
    curve, walk = _walk(_CONFIG)
    assert walk.scores  # non-empty
    for score in walk.scores:
        assert score >= curve.band_low - 1e-9


def test_acceptance_ratio_in_open_unit_interval() -> None:
    _curve, walk = _walk(_CONFIG)
    assert 0.0 < walk.acceptance_rate < 1.0


def test_trajectory_length_matches_steps() -> None:
    _curve, walk = _walk(_CONFIG)
    assert walk.steps == _CONFIG.walk_steps
    assert len(walk.points) == _CONFIG.walk_steps + 1
    assert len(walk.scores) == _CONFIG.walk_steps + 1


def test_walk_is_reproducible_under_fixed_seed() -> None:
    _c1, w1 = _walk(_CONFIG)
    _c2, w2 = _walk(_CONFIG)
    assert w1.points == w2.points
    assert w1.acceptance_rate == w2.acceptance_rate
