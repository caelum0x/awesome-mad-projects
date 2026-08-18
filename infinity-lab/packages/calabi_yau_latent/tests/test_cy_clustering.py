"""Tests for connected-components clustering (calabi_yau_latent.core.clustering).

The headline property: with the SAME threshold, the wrap-aware metric recovers
the true cluster count while the naive metric over-segments the seam-straddling
clusters. Also checks purity, nearest-neighbour, and fail-fast validation.
Stdlib-only -> RUNS on both interpreters.
"""

from __future__ import annotations

import pytest

from calabi_yau_latent.core.clustering import (
    cluster,
    nearest_neighbor,
    num_clusters,
    purity,
)
from calabi_yau_latent.core.config import DEFAULT
from calabi_yau_latent.core.data import generate, make_space
from calabi_yau_latent.core.distance import (
    naive_angular_distance,
    toroidal_angular_distance,
)


def _dataset():
    space = make_space(DEFAULT)
    return generate(space, DEFAULT)


def test_wrap_aware_recovers_true_cluster_count() -> None:
    points, truth, _ = _dataset()
    labels = cluster(points, toroidal_angular_distance, DEFAULT.cluster_threshold)
    assert num_clusters(labels) == len(DEFAULT.centers)
    assert purity(labels, truth) == pytest.approx(1.0)


def test_naive_over_segments() -> None:
    points, truth, _ = _dataset()
    labels = cluster(points, naive_angular_distance, DEFAULT.cluster_threshold)
    assert num_clusters(labels) > len(DEFAULT.centers)


def test_nearest_neighbor_prefers_same_cluster_under_wrap_aware() -> None:
    points, truth, _ = _dataset()
    correct = 0
    for i, p in enumerate(points):
        j = nearest_neighbor(p, points, toroidal_angular_distance)
        if j >= 0 and truth[j] == truth[i]:
            correct += 1
    assert correct == len(points)  # perfect NN recovery on the toy


def test_purity_of_empty_is_zero() -> None:
    assert purity([], []) == 0.0


def test_cluster_rejects_nonpositive_threshold() -> None:
    points, _, _ = _dataset()
    with pytest.raises(ValueError):
        cluster(points, toroidal_angular_distance, 0.0)


def test_nearest_neighbor_excludes_self() -> None:
    points, _, _ = _dataset()
    j = nearest_neighbor(points[0], points, toroidal_angular_distance)
    assert j != 0 and j >= 0
