"""Reproducibility: a fixed seed replays byte-identically; seeds differ.

All randomness flows through a single seeded
:class:`commons.core.rng.DeterministicRNG`, so ``(config, seed)`` fully
determines a run. Two runs with the same seed must match on every recorded
quantity, and the process-global RNG is never consulted.
"""

from __future__ import annotations

from madoka_entropy.core.config import SimConfig
from madoka_entropy.core.simulation import run_simulation


def _fingerprint(result) -> tuple:
    return tuple(
        (
            r.step,
            round(r.global_entropy, 9),
            round(r.local_entropy, 9),
            round(r.harvested_energy, 9),
            r.witches_this_step,
        )
        for r in result.records
    )


def test_same_seed_is_identical() -> None:
    cfg = SimConfig(seed=137, steps=120)
    a = run_simulation(cfg)
    b = run_simulation(cfg)
    assert _fingerprint(a) == _fingerprint(b)
    assert a.min_d_total == b.min_d_total
    assert a.invariant_holds == b.invariant_holds


def test_different_seeds_diverge() -> None:
    a = run_simulation(SimConfig(seed=1, steps=120))
    b = run_simulation(SimConfig(seed=2, steps=120))
    # Overwhelmingly likely to differ; assert they are not identical runs.
    assert _fingerprint(a) != _fingerprint(b)


def test_run_does_not_touch_global_random() -> None:
    import random

    state_before = random.getstate()
    run_simulation(SimConfig(seed=99, steps=80))
    assert random.getstate() == state_before
