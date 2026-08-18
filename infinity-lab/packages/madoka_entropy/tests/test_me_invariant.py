"""The second-law-like invariant: ``dS_total >= 0`` at every step, many seeds.

The whole software claim is that the bookkeeping never accidentally lets total
entropy decrease. We check it on the default run, across many seeds, and confirm
the global reservoir is itself monotone non-decreasing (it only ever receives).
"""

from __future__ import annotations

from madoka_entropy.core.config import SimConfig
from madoka_entropy.core.simulation import run_simulation


def test_invariant_holds_default() -> None:
    result = run_simulation(SimConfig(seed=42, steps=120))
    assert result.invariant_holds
    assert result.min_d_total >= -1e-9


def test_invariant_holds_many_seeds() -> None:
    for seed in range(60):
        result = run_simulation(SimConfig(seed=seed, steps=150))
        assert result.invariant_holds, f"seed {seed} violated the invariant"
        assert result.min_d_total >= -1e-9


def test_every_step_record_flags_ok() -> None:
    result = run_simulation(SimConfig(seed=7, steps=140))
    assert all(rec.invariant_ok for rec in result.records)


def test_total_entropy_is_non_decreasing() -> None:
    result = run_simulation(SimConfig(seed=3, steps=120))
    totals = [rec.total_entropy for rec in result.records]
    for prev, cur in zip(totals, totals[1:]):
        assert cur >= prev - 1e-9


def test_global_entropy_is_non_decreasing() -> None:
    # The global reservoir only ever receives entropy, so it too is monotone.
    result = run_simulation(SimConfig(seed=1, steps=120))
    globals_ = [rec.global_entropy for rec in result.records]
    for prev, cur in zip(globals_, globals_[1:]):
        assert cur >= prev - 1e-9


def test_zero_steps_is_trivially_consistent() -> None:
    result = run_simulation(SimConfig(seed=1, steps=0))
    assert result.records == ()
    assert result.invariant_holds
    assert result.min_d_total == 0.0
