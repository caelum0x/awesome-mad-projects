"""Tests for commons.core.rng (deterministic seeded PRNG)."""

from __future__ import annotations

import pytest

from commons.core.rng import DeterministicRNG, make_rng


def test_same_seed_same_sequence() -> None:
    a = make_rng(42)
    b = make_rng(42)
    assert [a.random() for _ in range(10)] == [b.random() for _ in range(10)]


def test_different_seed_different_sequence() -> None:
    a = [make_rng(1).random() for _ in range(5)]
    b = [make_rng(2).random() for _ in range(5)]
    assert a != b


def test_uniform_within_bounds() -> None:
    rng = make_rng(7)
    for _ in range(100):
        x = rng.uniform(-3.0, 5.0)
        assert -3.0 <= x <= 5.0


def test_randint_within_bounds_and_reproducible() -> None:
    rng1 = make_rng(9)
    rng2 = make_rng(9)
    vals1 = [rng1.randint(1, 6) for _ in range(20)]
    vals2 = [rng2.randint(1, 6) for _ in range(20)]
    assert vals1 == vals2
    assert all(1 <= v <= 6 for v in vals1)


def test_choice_from_population() -> None:
    rng = make_rng(3)
    pop = ["a", "b", "c"]
    assert rng.choice(pop) in pop


def test_choice_empty_raises() -> None:
    with pytest.raises(IndexError):
        make_rng(0).choice([])


def test_sample_distinct_and_immutable() -> None:
    rng = make_rng(11)
    pop = [1, 2, 3, 4, 5]
    original = list(pop)
    picked = rng.sample(pop, 3)
    assert len(picked) == 3
    assert len(set(picked)) == 3
    assert pop == original  # input not mutated


def test_sample_too_large_raises() -> None:
    with pytest.raises(ValueError):
        make_rng(1).sample([1, 2], 5)


def test_shuffled_is_permutation_and_immutable() -> None:
    rng = make_rng(5)
    pop = [1, 2, 3, 4, 5]
    original = list(pop)
    out = rng.shuffled(pop)
    assert sorted(out) == sorted(original)
    assert pop == original  # input not mutated


def test_reset_replays_stream() -> None:
    rng = make_rng(21)
    first = [rng.random() for _ in range(5)]
    fresh = rng.reset()
    assert [fresh.random() for _ in range(5)] == first


def test_seed_property() -> None:
    assert make_rng(99).seed == 99


def test_bool_seed_rejected() -> None:
    with pytest.raises(TypeError):
        DeterministicRNG(True)  # type: ignore[arg-type]
