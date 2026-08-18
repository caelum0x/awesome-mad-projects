"""Deterministic, seeded pseudo-random number generation (stdlib only).

Wraps :class:`random.Random` so that every consumer draws from an *isolated*,
reproducibly-seeded stream. The global :mod:`random` state is never touched, so
concurrent components cannot perturb one another's sequences.

Determinism guarantee:
    Two :class:`DeterministicRNG` instances constructed with the same ``seed``
    produce identical sequences for identical call patterns.

Immutability note:
    Draw methods (:meth:`sample`, :meth:`shuffled`) return *new* lists and never
    mutate their inputs, following the project's no-shared-mutation rule.
"""

from __future__ import annotations

import random
from typing import List, Sequence, TypeVar

T = TypeVar("T")


class DeterministicRNG:
    """A reproducible PRNG bound to a fixed seed.

    Each instance owns a private :class:`random.Random`; nothing here reads or
    writes the process-global RNG.
    """

    __slots__ = ("_seed", "_rng")

    def __init__(self, seed: int) -> None:
        if not isinstance(seed, int) or isinstance(seed, bool):
            raise TypeError(f"seed must be int, got {type(seed).__name__}")
        self._seed = seed
        self._rng = random.Random(seed)

    @property
    def seed(self) -> int:
        """The immutable seed this generator was created with."""
        return self._seed

    def random(self) -> float:
        """A float in the half-open interval ``[0.0, 1.0)``."""
        return self._rng.random()

    def uniform(self, low: float, high: float) -> float:
        """A float drawn uniformly from ``[low, high]`` (order-independent)."""
        return self._rng.uniform(low, high)

    def randint(self, low: int, high: int) -> int:
        """An integer drawn uniformly from the inclusive range ``[low, high]``."""
        if low > high:
            raise ValueError(f"require low <= high, got ({low}, {high})")
        return self._rng.randint(low, high)

    def choice(self, population: Sequence[T]) -> T:
        """Return one element chosen uniformly from ``population``.

        Raises :class:`IndexError` (via the underlying RNG) if it is empty.
        """
        if len(population) == 0:
            raise IndexError("cannot choose from an empty sequence")
        return self._rng.choice(population)

    def sample(self, population: Sequence[T], k: int) -> List[T]:
        """Return a new list of ``k`` distinct elements sampled without
        replacement. ``population`` is not mutated.
        """
        if k < 0:
            raise ValueError("sample size k must be non-negative")
        if k > len(population):
            raise ValueError("sample size k exceeds population size")
        return self._rng.sample(list(population), k)

    def shuffled(self, population: Sequence[T]) -> List[T]:
        """Return a new, randomly permuted list; ``population`` is untouched."""
        items = list(population)
        self._rng.shuffle(items)
        return items

    def reset(self) -> "DeterministicRNG":
        """Return a *fresh* generator with the same seed (immutable restart).

        The current instance is left as-is; callers get a new stream that
        replays from the beginning.
        """
        return DeterministicRNG(self._seed)


def make_rng(seed: int) -> DeterministicRNG:
    """Convenience constructor for a :class:`DeterministicRNG`."""
    return DeterministicRNG(seed)
