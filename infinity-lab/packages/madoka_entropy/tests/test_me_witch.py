"""Witch transformations trigger at the purity threshold and inject a burst.

A girl becomes a witch exactly when her soul-gem purity falls to/below
``witch_threshold``; the transformation dumps a positive entropy burst into the
global reservoir (net total change > 0) while conserving the evacuated local
order. We drive a girl to the threshold directly and observe it in a full run.
"""

from __future__ import annotations

from madoka_entropy.core.config import SimConfig
from madoka_entropy.core.entropy import EntropyLedger
from madoka_entropy.core.incubator import Incubator
from madoka_entropy.core.magical_girl import MagicalGirl
from madoka_entropy.core.simulation import (
    _apply_witch_transformations,
    run_simulation,
)


def test_threshold_crossing_becomes_a_witch() -> None:
    cfg = SimConfig()
    # Purity already at the threshold -> should transform this step.
    girl = MagicalGirl("Sayaka", purity=cfg.witch_threshold, local_entropy=8.0)
    ledger = EntropyLedger(global_entropy=100.0, local_entropy=8.0, harvested_energy=0.0)
    before_total = ledger.total_entropy

    new_girls, new_ledger, witches = _apply_witch_transformations(
        (girl,), step=5, cfg=cfg, incubator=Incubator(), ledger=ledger,
        order_cast={"Sayaka": 4.0},
    )

    assert witches == ("Sayaka",)
    assert new_girls[0].is_witch
    assert new_girls[0].witch_step == 5
    # Net total change is the burst (base + per_order * order_cast) > 0.
    expected_burst = cfg.witch_burst_base + cfg.witch_burst_per_order * 4.0
    assert new_ledger.total_entropy - before_total > 0.0
    assert (new_ledger.total_entropy - before_total) == expected_burst


def test_pure_girl_does_not_transform() -> None:
    cfg = SimConfig()
    girl = MagicalGirl("Madoka", purity=1.0, local_entropy=8.0)
    ledger = EntropyLedger(global_entropy=100.0, local_entropy=8.0, harvested_energy=0.0)
    new_girls, new_ledger, witches = _apply_witch_transformations(
        (girl,), step=0, cfg=cfg, incubator=Incubator(), ledger=ledger,
        order_cast={"Madoka": 0.0},
    )
    assert witches == ()
    assert not new_girls[0].is_witch
    assert new_ledger.total_entropy == ledger.total_entropy


def test_burst_scales_with_order_cast() -> None:
    cfg = SimConfig()
    inc = Incubator()

    def burst_for(order: float) -> float:
        girl = MagicalGirl("K", purity=0.0, local_entropy=5.0)
        ledger = EntropyLedger(100.0, 5.0, 0.0)
        _, new_ledger, _ = _apply_witch_transformations(
            (girl,), step=1, cfg=cfg, incubator=inc, ledger=ledger,
            order_cast={"K": order},
        )
        return new_ledger.total_entropy - ledger.total_entropy

    assert burst_for(10.0) > burst_for(1.0)


def test_full_run_produces_witches_and_flags_steps() -> None:
    result = run_simulation(SimConfig(seed=42, steps=120))
    witch_names = {
        name for rec in result.records for name in rec.witches_this_step
    }
    assert witch_names, "expected at least one witch transformation on seed 42"
    # Each flagged step must coincide with a strictly positive entropy jump.
    for rec in result.records:
        if rec.witches_this_step:
            assert rec.d_total > 0.0
    # Girls flagged as witches in records are witches in the final roster.
    final_witches = {g.name for g in result.final_girls if g.is_witch}
    assert witch_names <= final_witches
