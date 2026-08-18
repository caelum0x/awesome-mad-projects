"""Tests for the EXHAUSTIVE ultrametric verifier (padic_embeddings.core.embedding).

The defining p-adic property is the STRONG triangle inequality
``d_p(a, c) <= max(d_p(a, b), d_p(b, c))``. These tests assert it holds with ZERO
violations on real samples, checked exhaustively over every ordered triple, for
several primes -- and that a single triple can be probed directly. Pure stdlib +
commons, so they RUN on both interpreters.
"""

from __future__ import annotations

from fractions import Fraction

from padic_embeddings.core import embedding, padic


def test_strong_triangle_holds_on_2adic_sample() -> None:
    coords = [1, 3, 5, 8, 16, 17, 24, 32, 48, 64]
    ok, checked, failures = embedding.verify_ultrametric(coords, 2)
    assert ok
    assert failures == []
    # n * (n-1) * (n-2) ordered distinct triples for n = 10.
    assert checked == 10 * 9 * 8


def test_strong_triangle_holds_for_prime_7() -> None:
    coords = [7, 14, 49, 50, 98, 100, 343]
    ok, checked, failures = embedding.verify_ultrametric(coords, 7)
    assert ok
    assert failures == []
    assert checked > 0


def test_strong_triangle_holds_on_hashed_strings() -> None:
    words = ["cat", "cot", "cog", "dog", "log", "apple", "tree"]
    coords = embedding.embed(words)
    ok, _, failures = embedding.verify_ultrametric(coords, 2)
    assert ok
    assert failures == []


def test_single_triple_probe_is_exact() -> None:
    # d_2(0, 4) = 1/4, d_2(0, 2) = 1/2, d_2(2, 4) = 1/2; 1/4 <= max(1/2, 1/2).
    assert padic.is_ultrametric_triple(0, 2, 4, 2) is True
    assert padic.distance_exact(0, 4, 2) == Fraction(1, 4)
