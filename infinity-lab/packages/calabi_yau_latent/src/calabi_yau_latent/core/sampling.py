"""Seeded, reproducible random draws built on ``commons.core.rng`` (stdlib only).

All randomness in this package flows through
:class:`commons.core.rng.DeterministicRNG` -- never the bare :mod:`random` global
-- so two runs with the same seed produce byte-identical data.

``DeterministicRNG`` exposes ``random`` / ``uniform`` but no Gaussian draw, so the
Gaussian primitive here is synthesised from its uniform stream via the Box-Muller
transform. That keeps every draw on the single seeded stream with no third-party
dependency.

Purity: imports only the standard library and :mod:`commons.core`.
"""

from __future__ import annotations

import math

from commons.core.rng import DeterministicRNG, make_rng


def make_stream(seed: int) -> DeterministicRNG:
    """Return a fresh :class:`DeterministicRNG` seeded with ``seed``."""
    return make_rng(seed)


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
