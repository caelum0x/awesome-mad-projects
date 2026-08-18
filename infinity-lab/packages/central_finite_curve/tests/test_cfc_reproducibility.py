"""Reproducibility: same seed -> identical multiverse and identical curve size.

Every draw flows through ``commons.core.rng`` seeded from ``config.seed``, so two
runs with the same config must produce byte-identical universes (coords AND scores)
and, consequently, an EXACTLY equal curve size. A different seed must change them.
"""

from __future__ import annotations

from central_finite_curve.core import curve as curve_mod
from central_finite_curve.core import multiverse as multiverse_mod
from central_finite_curve.core.config import CurveConfig
from central_finite_curve.core.sampling import child_rng

_SMALL = CurveConfig(n_universes=600, walk_steps=100, seed=137)


def _generate(config: CurveConfig):
    return multiverse_mod.generate(child_rng(config.seed, 1), config)


def test_same_seed_identical_multiverse() -> None:
    a = _generate(_SMALL)
    b = _generate(_SMALL)
    assert len(a) == len(b) == _SMALL.n_universes
    assert [u.coords for u in a] == [u.coords for u in b]
    assert [u.score for u in a] == [u.score for u in b]


def test_same_seed_identical_curve_size_exact() -> None:
    size_a = curve_mod.extract(_generate(_SMALL), _SMALL).size
    size_b = curve_mod.extract(_generate(_SMALL), _SMALL).size
    assert size_a == size_b


def test_different_seed_changes_multiverse() -> None:
    other = CurveConfig(n_universes=600, walk_steps=100, seed=999)
    a = _generate(_SMALL)
    c = _generate(other)
    assert [u.coords for u in a] != [u.coords for u in c]
