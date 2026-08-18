"""Tests for the embedding layer (padic_embeddings.core.embedding).

Covers deterministic string embedding, residue-class clustering that refines with
the level (the nested p-adic balls), nearest-neighbour behaviour (numbers sharing
more factors of ``p`` cluster together), the distance matrix's shape/symmetry, and
the seeded reproducible sampler. Pure stdlib + commons, so these RUN on both
interpreters.
"""

from __future__ import annotations

import pytest

from padic_embeddings.core import embedding


def test_string_embedding_is_deterministic() -> None:
    assert embedding.embed_item("cat") == embedding.embed_item("cat")
    # Distinct strings almost surely map to distinct coordinates.
    assert embedding.embed_item("cat") != embedding.embed_item("dog")


def test_integer_embedding_is_identity() -> None:
    assert embedding.embed([1, 42, -7]) == [1, 42, -7]


def test_bad_item_and_modulus_rejected() -> None:
    with pytest.raises(TypeError):
        embedding.embed_item(3.14)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        embedding.embed_item(True)  # bool rejected
    with pytest.raises(ValueError):
        embedding.embed_item("x", modulus=0)


def test_clusters_are_refined_by_level() -> None:
    coords = [0, 4, 8, 16, 2, 6]
    c1 = embedding.cluster_by_valuation(coords, 2, level=1)
    # all even -> single residue class mod 2
    assert sorted(c1.keys()) == [0]
    c2 = embedding.cluster_by_valuation(coords, 2, level=2)
    # split by residue mod 4
    assert sorted(c2.keys()) == [0, 2]
    # members are returned sorted and cover the input
    assert c2[0] == [0, 4, 8, 16]
    assert c2[2] == [2, 6]


def test_cluster_negative_level_rejected() -> None:
    with pytest.raises(ValueError):
        embedding.cluster_by_valuation([1, 2], 2, level=-1)


def test_nearest_neighbor_prefers_shared_factors() -> None:
    # 16 shares more factors of 2 with 48 (both divisible by 16) than with 17.
    nn = embedding.nearest_neighbors(16, [17, 48, 5, 3], 2, k=1)
    assert nn[0][0] == 48


def test_nearest_neighbor_excludes_self_and_orders() -> None:
    nn = embedding.nearest_neighbors(16, [16, 48, 32, 64, 17], 2, k=3)
    labels = [it for it, _ in nn]
    assert 16 not in labels           # self excluded
    assert labels[0] == 48            # 48-16 = 32 = 2^5, the most divisible
    dists = [d for _, d in nn]
    assert dists == sorted(dists)     # ascending by distance


def test_distance_matrix_is_symmetric_with_zero_diagonal() -> None:
    coords = [1, 3, 8, 16]
    m = embedding.distance_matrix(coords, 2)
    n = len(coords)
    for i in range(n):
        assert m[i][i] == 0.0
        for j in range(n):
            assert m[i][j] == m[j][i]


def test_sample_integers_is_reproducible() -> None:
    a = embedding.sample_integers(20, 0, 1000, seed=137)
    b = embedding.sample_integers(20, 0, 1000, seed=137)
    c = embedding.sample_integers(20, 0, 1000, seed=999)
    assert a == b
    assert a != c
    assert len(a) == 20
    assert all(0 <= x <= 1000 for x in a)
