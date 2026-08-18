"""The curve filter: a non-empty, sanely-sized band with every member near the max.

Asserts the near-maximal band contract:

* the band is non-empty and a sane fraction of the multiverse (not the whole thing),
* EVERY member's Rickness is within ``epsilon`` of the observed maximum,
* members are sorted best-first, and ``band_low == max_score - epsilon``,
* an empty multiverse raises rather than silently returning junk.
"""

from __future__ import annotations

import pytest

from central_finite_curve.core import curve as curve_mod
from central_finite_curve.core import multiverse as multiverse_mod
from central_finite_curve.core.config import CurveConfig
from central_finite_curve.core.sampling import child_rng

_CONFIG = CurveConfig(n_universes=1500, walk_steps=0, seed=137)


def _extract(config: CurveConfig):
    universes = multiverse_mod.generate(child_rng(config.seed, 1), config)
    return curve_mod.extract(universes, config)


def test_band_non_empty_and_sane_fraction() -> None:
    curve = _extract(_CONFIG)
    assert curve.size > 0
    # A thin ridge, not the whole multiverse: strictly between 0 and a sane cap.
    assert 0.0 < curve.fraction < 0.5
    assert curve.total == _CONFIG.n_universes


def test_every_member_within_epsilon_of_max() -> None:
    curve = _extract(_CONFIG)
    for member in curve.members:
        assert member.score >= curve.band_low - 1e-12
        assert curve.max_score - member.score <= curve.epsilon + 1e-12


def test_band_low_definition_and_sorting() -> None:
    curve = _extract(_CONFIG)
    assert curve.band_low == pytest.approx(curve.max_score - curve.epsilon)
    scores = [m.score for m in curve.members]
    assert scores == sorted(scores, reverse=True)
    assert curve.members[0].score == pytest.approx(curve.max_score)


def test_empty_multiverse_raises() -> None:
    with pytest.raises(ValueError):
        curve_mod.extract([], _CONFIG)
