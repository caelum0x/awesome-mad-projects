"""Tests for the planted-cluster data generator (calabi_yau_latent.core.data).

Checks reproducibility (seed determinism via commons.core.rng), the shape of the
output, and that at least one cluster genuinely straddles the 0 / 2*pi seam (raw
angles at BOTH ends of the circle). Stdlib-only -> RUNS on both interpreters.
"""

from __future__ import annotations

from calabi_yau_latent.core.config import DEFAULT, CYConfig
from calabi_yau_latent.core.data import generate, make_space
from calabi_yau_latent.core.latent import TWO_PI


def test_generate_shapes_match_config() -> None:
    space = make_space(DEFAULT)
    points, truth, torus_xy = generate(space, DEFAULT)
    expected = DEFAULT.per_cluster * len(DEFAULT.centers)
    assert len(points) == expected
    assert len(truth) == expected
    assert len(torus_xy) == expected
    assert set(truth) == set(range(len(DEFAULT.centers)))


def test_generation_is_deterministic_for_a_fixed_seed() -> None:
    space = make_space(DEFAULT)
    a = generate(space, DEFAULT)[2]
    b = generate(space, DEFAULT)[2]
    assert a == b


def test_different_seeds_give_different_data() -> None:
    space = make_space(DEFAULT)
    a = generate(space, DEFAULT)[2]
    b = generate(space, DEFAULT.with_changes(seed=DEFAULT.seed + 1))[2]
    assert a != b


def test_a_cluster_straddles_the_seam() -> None:
    # Cluster 0 is centred at theta1 = 0, so its members' theta1 spans both the
    # low end (near 0) and the high end (near 2*pi) of the raw angle range.
    space = make_space(DEFAULT)
    points, truth, _ = generate(space, DEFAULT)
    theta1 = [p.angles[0] for p, t in zip(points, truth) if t == 0]
    assert min(theta1) < 0.5
    assert max(theta1) > TWO_PI - 0.5


def test_extended_dims_present_and_sized() -> None:
    cfg = CYConfig(k=3)
    space = make_space(cfg)
    points, _, _ = generate(space, cfg)
    assert all(len(p.extended) == 3 for p in points)
