"""Nearest-neighbour + tiny clustering under a pluggable distance function.

We use a simple, dependency-free connected-components clustering: connect any two
points whose distance is below a threshold, then take connected components. This
is enough to show that the *choice of metric* (naive vs topology-aware) changes
which points are grouped together. Pure stdlib.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Callable, List, Sequence

from calabi_yau_latent.core.latent import LatentPoint

Distance = Callable[[LatentPoint, LatentPoint], float]


def nearest_neighbor(
    query: LatentPoint, points: Sequence[LatentPoint], dist: Distance
) -> int:
    """Return the index of the closest point under ``dist`` (excluding self).

    Identity is by object (``is``), so a point never matches itself. Returns
    ``-1`` if there is no other point.
    """
    best_idx = -1
    best_d = float("inf")
    for i, p in enumerate(points):
        if p is query:
            continue
        d = dist(query, p)
        if d < best_d:
            best_d = d
            best_idx = i
    return best_idx


def cluster(
    points: Sequence[LatentPoint], dist: Distance, threshold: float
) -> List[int]:
    """Connected-components clustering. Returns a label per point.

    Two points share a cluster if there is a path of ``<= threshold`` hops between
    them. Immutable style: builds fresh lists, never mutates the inputs. Raises
    :class:`ValueError` for a non-positive threshold.
    """
    if threshold <= 0.0:
        raise ValueError("threshold must be positive")
    n = len(points)
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]  # path compression (local array only)
            x = parent[x]
        return x

    def union(a: int, b: int) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for i in range(n):
        for j in range(i + 1, n):
            if dist(points[i], points[j]) <= threshold:
                union(i, j)

    roots: dict = {}
    labels: List[int] = []
    for i in range(n):
        r = find(i)
        if r not in roots:
            roots[r] = len(roots)
        labels.append(roots[r])
    return labels


def num_clusters(labels: Sequence[int]) -> int:
    """Number of distinct cluster labels."""
    return len(set(labels))


def purity(labels: Sequence[int], truth: Sequence[int]) -> float:
    """Cluster purity vs ground-truth labels in ``[0, 1]``. Higher is better.

    Each predicted cluster is credited with the count of its most common true
    label; the sum over clusters divided by the number of points is the purity.
    Returns ``0.0`` for empty input.
    """
    if not labels:
        return 0.0
    groups = defaultdict(list)
    for lab, t in zip(labels, truth):
        groups[lab].append(t)
    correct = 0
    for members in groups.values():
        correct += Counter(members).most_common(1)[0][1]
    return correct / len(labels)
