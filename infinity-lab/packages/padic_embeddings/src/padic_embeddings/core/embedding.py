"""A tiny p-adic "embedding" layer.

Instead of mapping items into ``R^d`` with a Euclidean metric, we map each item
to a single integer coordinate in ``Z`` and measure closeness with the p-adic
metric ``d_p``. Two items are close when their coordinates agree modulo a high
power of ``p`` (i.e. their difference is very divisible by ``p``).

Items can be:
  * integers supplied directly (used as-is -- they already live in ``Z``), or
  * short strings, hashed deterministically into a bounded integer range via
    SHA-256 mod ``2**k`` (deterministic across runs, unlike Python's salted
    ``hash()``).

This module provides:
  * :func:`embed_item` / :func:`embed`        -- map items to integer coordinates
  * :func:`distance_matrix`                   -- full pairwise p-adic distances
  * :func:`nearest_neighbors`                 -- k nearest items under ``d_p``
  * :func:`verify_ultrametric`                -- EXHAUSTIVE strong-triangle check
  * :func:`cluster_by_valuation`              -- residue-class balls of ``Z_p``
  * :func:`sample_integers`                   -- a seeded reproducible sample

Purity: imports only the standard library and :mod:`commons.core`.
"""

from __future__ import annotations

import hashlib
from typing import Dict, List, Sequence, Tuple, Union

from commons.core.rng import DeterministicRNG

from padic_embeddings.core import padic

Item = Union[int, str]

# SHA-256 reduced modulo this bound keeps string coordinates in a readable range
# while staying deterministic across processes (unlike the salted builtin hash).
DEFAULT_MODULUS = 2 ** 20


# ---------------------------------------------------------------------------
# Deterministic embedding of items -> integer coordinates
# ---------------------------------------------------------------------------

def embed_item(item: Item, modulus: int = DEFAULT_MODULUS) -> int:
    """Map an item to an integer coordinate in ``Z``.

    Integers pass through unchanged. Strings are hashed with SHA-256 and reduced
    modulo ``modulus``. Raises :class:`ValueError` for a non-positive modulus and
    :class:`TypeError` for an unsupported item type.
    """
    if modulus < 1:
        raise ValueError("modulus must be >= 1")
    if isinstance(item, bool):  # bool is an int subclass; reject as a likely mistake
        raise TypeError("bool is not a valid item")
    if isinstance(item, int):
        return item
    if isinstance(item, str):
        digest = hashlib.sha256(item.encode("utf-8")).hexdigest()
        return int(digest, 16) % modulus
    raise TypeError(f"unsupported item type: {type(item)!r}")


def embed(items: Sequence[Item], modulus: int = DEFAULT_MODULUS) -> List[int]:
    """Embed a sequence of items into their integer coordinates (new list)."""
    return [embed_item(it, modulus) for it in items]


# ---------------------------------------------------------------------------
# p-adic distance structures
# ---------------------------------------------------------------------------

def distance_matrix(coords: Sequence[int], p: int) -> List[List[float]]:
    """Full symmetric matrix of pairwise p-adic distances (as floats).

    The diagonal is zero. Symmetry is enforced by computing the upper triangle
    once and mirroring it.
    """
    n = len(coords)
    matrix = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            d = padic.distance(coords[i], coords[j], p)
            matrix[i][j] = d
            matrix[j][i] = d
    return matrix


def nearest_neighbors(
    query: Item,
    items: Sequence[Item],
    p: int,
    k: int = 3,
    modulus: int = DEFAULT_MODULUS,
) -> List[Tuple[Item, float]]:
    """Return the ``k`` items closest to ``query`` under the p-adic metric.

    Items whose coordinate equals the query's (distance ``0``) are excluded. Ties
    keep the original ordering (a stable sort). Raises :class:`ValueError` for
    ``k < 0``.
    """
    if k < 0:
        raise ValueError("k must be >= 0")
    q = embed_item(query, modulus)
    scored: List[Tuple[Item, float]] = []
    for it in items:
        c = embed_item(it, modulus)
        if c == q:
            continue
        scored.append((it, padic.distance(q, c, p)))
    scored.sort(key=lambda pair: pair[1])
    return scored[:k]


# ---------------------------------------------------------------------------
# Ultrametric verification (EXHAUSTIVE over all ordered triples)
# ---------------------------------------------------------------------------

def verify_ultrametric(
    coords: Sequence[int], p: int
) -> Tuple[bool, int, List[Tuple[int, int, int]]]:
    """Exhaustively check the strong triangle inequality on ALL ordered triples.

    Returns ``(all_hold, num_triples_checked, failures)``. A failure is the
    coordinate triple ``(a, b, c)`` that violates
    ``d_p(a, c) <= max(d_p(a, b), d_p(b, c))``; for a genuine ultrametric this
    list is always empty. Runs in ``O(n**3)`` -- intended for small samples.
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
# Hierarchical clustering induced by the p-adic metric (balls of Z_p)
# ---------------------------------------------------------------------------

def cluster_by_valuation(
    coords: Sequence[int], p: int, level: int
) -> Dict[int, List[int]]:
    """Group coordinates that agree modulo ``p**level``.

    Two integers ``a, b`` satisfy ``d_p(a, b) <= p**(-level)`` iff
    ``a == b (mod p**level)``. So the residue class modulo ``p**level`` is exactly
    a ball of radius ``p**(-level)`` in the p-adic metric. Increasing ``level``
    refines the clustering, producing the nested tree of balls characteristic of
    the p-adic integers ``Z_p``. Members are returned in ascending order; the
    input is not mutated. Raises :class:`ValueError` for a negative ``level``.
    """
    if level < 0:
        raise ValueError("level must be >= 0")
    if not padic.is_prime(p):
        raise ValueError(f"p must be prime, got {p}")
    mod = p ** level
    clusters: Dict[int, List[int]] = {}
    for c in coords:
        clusters.setdefault(c % mod, []).append(c)
    return {key: sorted(members) for key, members in clusters.items()}


# ---------------------------------------------------------------------------
# Reproducible sample generation (seeded via commons)
# ---------------------------------------------------------------------------

def sample_integers(
    count: int, low: int, high: int, seed: int
) -> List[int]:
    """Return ``count`` integers drawn reproducibly from ``[low, high]``.

    Uses a private :class:`commons.core.rng.DeterministicRNG`, so the same
    ``(count, low, high, seed)`` always yields the same list and the process-global
    RNG is never touched. Raises :class:`ValueError` for ``count < 0``.
    """
    if count < 0:
        raise ValueError("count must be >= 0")
    rng = DeterministicRNG(seed)
    return [rng.randint(low, high) for _ in range(count)]
