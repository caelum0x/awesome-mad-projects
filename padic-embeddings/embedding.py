"""A tiny p-adic "embedding" layer.

Instead of mapping items into R^d with a Euclidean metric, we map each item
to a single integer coordinate in Z and measure closeness with the p-adic
metric d_p. Two items are close when their coordinates agree modulo a high
power of p (i.e. their difference is very divisible by p).

Items can be:
  * integers supplied directly, or
  * short strings, hashed deterministically into a bounded integer range.

This file provides:
  * embed_item / embed        - map items to integer coordinates
  * distance_matrix           - full pairwise p-adic distance matrix
  * nearest_neighbors         - k nearest items to a query under d_p
  * verify_ultrametric        - exhaustively check the strong triangle law
  * cluster_by_valuation      - hierarchical clusters induced by shared
                                factors of p (the tree structure of Z_p)

Standard library only.
"""

from __future__ import annotations

import hashlib
from fractions import Fraction
from typing import Dict, List, Sequence, Tuple, Union

import padic

Item = Union[int, str]


# ---------------------------------------------------------------------------
# Deterministic embedding of items -> integer coordinates
# ---------------------------------------------------------------------------

def embed_item(item: Item, modulus: int = 2 ** 20) -> int:
    """Map an item to an integer coordinate in Z.

    Integers are used as-is (they already live in Z). Strings are hashed with
    SHA-256 (deterministic across runs, unlike Python's salted hash()) and
    reduced modulo `modulus` so coordinates stay in a readable range.
    """
    if isinstance(item, int):
        return item
    if isinstance(item, str):
        digest = hashlib.sha256(item.encode("utf-8")).hexdigest()
        return int(digest, 16) % modulus
    raise TypeError(f"unsupported item type: {type(item)!r}")


def embed(items: Sequence[Item], modulus: int = 2 ** 20) -> List[int]:
    """Embed a sequence of items into their integer coordinates."""
    return [embed_item(it, modulus) for it in items]


# ---------------------------------------------------------------------------
# p-adic distance structures
# ---------------------------------------------------------------------------

def distance_matrix(coords: Sequence[int], p: int) -> List[List[float]]:
    """Full symmetric matrix of pairwise p-adic distances."""
    n = len(coords)
    matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            d = padic.distance(coords[i], coords[j], p)
            matrix[i][j] = d
            matrix[j][i] = d
    return matrix


def nearest_neighbors(query: Item, items: Sequence[Item], p: int,
                      k: int = 3, modulus: int = 2 ** 20
                      ) -> List[Tuple[Item, float]]:
    """Return the k items closest to `query` under the p-adic metric.

    Items equal to the query (distance 0) are excluded. Ties are broken by the
    original ordering, which is stable.
    """
    q = embed_item(query, modulus)
    scored: List[Tuple[Item, float]] = []
    for it in items:
        c = embed_item(it, modulus)
        d = padic.distance(q, c, p)
        if d == 0.0 and c == q:
            continue
        scored.append((it, d))
    scored.sort(key=lambda pair: pair[1])
    return scored[:k]


# ---------------------------------------------------------------------------
# Ultrametric verification
# ---------------------------------------------------------------------------

def verify_ultrametric(coords: Sequence[int], p: int
                       ) -> Tuple[bool, int, List[Tuple[int, int, int]]]:
    """Exhaustively check the strong triangle inequality on all triples.

    Returns (all_hold, num_triples_checked, list_of_failures). A failure is
    recorded as the coordinate triple (a, b, c) that violates the law; for a
    genuine ultrametric this list is always empty.
    """
    failures: List[Tuple[int, int, int]] = []
    checked = 0
    n = len(coords)
    for i in range(n):
        for j in range(n):
            for k in range(n):
                if len({i, j, k}) < 3:
                    continue
                checked += 1
                a, b, c = coords[i], coords[j], coords[k]
                if not padic.is_ultrametric_triple(a, b, c, p):
                    failures.append((a, b, c))
    return (len(failures) == 0, checked, failures)


# ---------------------------------------------------------------------------
# Hierarchical clustering induced by the p-adic metric
# ---------------------------------------------------------------------------

def cluster_by_valuation(coords: Sequence[int], p: int, level: int
                         ) -> Dict[int, List[int]]:
    """Group coordinates that agree modulo p**level.

    Two integers a, b satisfy d_p(a, b) <= p**(-level)  iff  a == b (mod p**level).
    So the residue class mod p**level is exactly a ball of radius p**(-level)
    in the p-adic metric. Increasing `level` refines the clustering, producing
    the nested tree of balls characteristic of the p-adic integers Z_p.
    """
    if level < 0:
        raise ValueError("level must be >= 0")
    mod = p ** level
    clusters: Dict[int, List[int]] = {}
    for c in coords:
        key = c % mod
        clusters.setdefault(key, []).append(c)
    return clusters
