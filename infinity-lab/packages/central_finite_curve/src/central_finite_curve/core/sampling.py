"""Seeded, reproducible random draws built on ``commons.core.rng`` (stdlib only).

All randomness in this package flows through :class:`commons.core.rng.Deterministic
RNG` -- never the bare :mod:`random` global -- so two runs with the same seed
produce byte-identical multiverses and trajectories.

``DeterministicRNG`` exposes ``random`` / ``uniform`` but no Gaussian draw, so the
Gaussian primitives here are synthesised from its uniform stream via the
Box-Muller transform. That keeps every draw on the single seeded stream and needs
no third-party dependency.

Purity: imports only the standard library and :mod:`commons.core`.
"""

from __future__ import annotations

import math
from typing import List

from commons.core.rng import DeterministicRNG, make_rng

# Mask keeping derived seeds inside a comfortable positive 63-bit range.
_SEED_MASK = 0x7FFFFFFFFFFFFFFF


def child_seed(seed: int, tag: int) -> int:
    """Deterministically derive an independent child seed from ``(seed, tag)``.

    Order-independent (unlike consuming draws from a shared parent stream): the
    same ``(seed, tag)`` always maps to the same child seed, so callers can build
    e.g. a generation stream and a walk stream without coupling their order.
    """
    return (seed * 1000003 + tag) & _SEED_MASK


def child_rng(seed: int, tag: int) -> DeterministicRNG:
    """Return a fresh :class:`DeterministicRNG` seeded from ``child_seed``."""
    return make_rng(child_seed(seed, tag))


def gauss(rng: DeterministicRNG, mu: float = 0.0, sigma: float = 1.0) -> float:
    """A single Gaussian draw ``N(mu, sigma^2)`` via Box-Muller (two uniforms).

    ``sigma`` must be non-negative. Uses ``1 - random()`` for the first uniform so
    the argument to :func:`math.log` is strictly positive (``random()`` can return
    ``0.0`` but never ``1.0``).
    """
    if sigma < 0.0:
        raise ValueError("sigma must be >= 0")
    u1 = 1.0 - rng.random()  # (0, 1]
    u2 = rng.random()        # [0, 1)
    radius = math.sqrt(-2.0 * math.log(u1))
    return mu + sigma * radius * math.cos(2.0 * math.pi * u2)


def gauss_vector(rng: DeterministicRNG, dim: int, sigma: float) -> List[float]:
    """A ``dim``-vector of independent zero-mean Gaussian perturbations."""
    if dim < 1:
        raise ValueError("dim must be >= 1")
    return [gauss(rng, 0.0, sigma) for _ in range(dim)]


def uniform_vector(rng: DeterministicRNG, dim: int, box: float) -> List[float]:
    """A point drawn uniformly from the box ``[-box, box]^dim``."""
    if dim < 1:
        raise ValueError("dim must be >= 1")
    if box <= 0.0:
        raise ValueError("box must be positive")
    return [rng.uniform(-box, box) for _ in range(dim)]
