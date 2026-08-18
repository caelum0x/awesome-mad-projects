"""The closed-system simulation loop.

Each step:

  1. Every living girl may cast magic (make a wish) with some probability.

     - Local entropy of her subsystem drops; global entropy rises by a
       strictly larger karmic cost; her soul gem purity decays.
     - The incubator harvests a fraction of the karmic surplus.

  2. Any girl whose purity has crossed the witch threshold transforms into a
     witch: an entropy singularity that dumps a burst into the global
     reservoir. Her frozen local order is released back into the total as well.

  3. We verify the second-law-like invariant: total entropy this step is
     ``>=`` total entropy last step (``dS_total >= 0``), and record the result.

Everything is driven by a single seeded :class:`commons.core.rng.DeterministicRNG`
so runs are fully reproducible and the process-global RNG is never touched.

Purity: imports only the standard library and ``commons.core``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

from commons.core.rng import DeterministicRNG, make_rng

from madoka_entropy.core.config import DEFAULT, SimConfig
from madoka_entropy.core.entropy import EntropyLedger, wish_deltas
from madoka_entropy.core.incubator import Incubator
from madoka_entropy.core.magical_girl import MagicalGirl, make_girls

# Tiny tolerance so float noise never trips the strict-inequality invariant.
_EPS = 1e-9


@dataclass(frozen=True)
class StepRecord:
    """Immutable log entry for a single simulation step."""

    step: int
    total_entropy: float
    global_entropy: float
    local_entropy: float
    harvested_energy: float
    d_total: float                       # change in total entropy vs previous step
    invariant_ok: bool                   # d_total >= 0 ?
    witches_this_step: Tuple[str, ...] = ()  # names that transformed this step


@dataclass(frozen=True)
class SimResult:
    """Everything produced by a run (immutable)."""

    config: SimConfig
    records: Tuple[StepRecord, ...]
    final_girls: Tuple[MagicalGirl, ...]
    invariant_holds: bool                # True iff every step had d_total >= 0
    min_d_total: float                   # smallest per-step dS_total observed


def _order_cast_this_step(rng: DeterministicRNG, cfg: SimConfig) -> float:
    """Draw the amount of local order a girl imposes when she casts."""
    return rng.uniform(cfg.local_order_min, cfg.local_order_max)


def _apply_wishes(
    girls: Tuple[MagicalGirl, ...],
    rng: DeterministicRNG,
    cfg: SimConfig,
    incubator: Incubator,
    ledger: EntropyLedger,
    order_cast: Dict[str, float],
) -> Tuple[Tuple[MagicalGirl, ...], EntropyLedger]:
    """Phase 1: living girls cast wishes; returns new girls + new ledger."""
    new_girls: List[MagicalGirl] = []
    for girl in girls:
        if girl.is_witch:
            new_girls.append(girl)
            continue
        if rng.random() < cfg.wish_probability:
            order = _order_cast_this_step(rng, cfg)
            d_global, d_local = wish_deltas(order, cfg.karmic_multiplier)
            ledger = ledger.with_changes(
                d_global=d_global,
                d_local=d_local,
                d_harvest=incubator.harvest_from_wish(d_global, d_local),
            )
            girl = girl.cast(order, cfg.decay_per_order)
            order_cast[girl.name] += order
        new_girls.append(girl)
    return tuple(new_girls), ledger


def _apply_witch_transformations(
    girls: Tuple[MagicalGirl, ...],
    step: int,
    cfg: SimConfig,
    incubator: Incubator,
    ledger: EntropyLedger,
    order_cast: Dict[str, float],
) -> Tuple[Tuple[MagicalGirl, ...], EntropyLedger, Tuple[str, ...]]:
    """Phase 2: threshold crossings become witches, injecting entropy bursts.

    The singularity (a) evacuates her subsystem's local entropy into the global
    reservoir so the total is conserved for that move, then (b) dumps an
    additional ``burst`` of fresh entropy::

        d_local  = -girl.local_entropy       (subsystem removed)
        d_global = +girl.local_entropy + burst

    Net total change = ``+burst > 0``, preserving the invariant.
    """
    witches_this_step: List[str] = []
    transformed: List[MagicalGirl] = []
    for girl in girls:
        if (not girl.is_witch) and girl.purity <= cfg.witch_threshold:
            burst = (
                cfg.witch_burst_base
                + cfg.witch_burst_per_order * order_cast[girl.name]
            )
            ledger = ledger.with_changes(
                d_global=girl.local_entropy + burst,
                d_local=-girl.local_entropy,
                d_harvest=incubator.harvest_from_witch(burst),
            )
            transformed.append(girl.become_witch(step))
            witches_this_step.append(girl.name)
        else:
            transformed.append(girl)
    return tuple(transformed), ledger, tuple(witches_this_step)


def run_simulation(cfg: SimConfig = DEFAULT) -> SimResult:
    """Run the whole simulation and return an immutable :class:`SimResult`."""
    rng = make_rng(cfg.seed)
    incubator = Incubator()

    girls = make_girls(cfg.girl_names, cfg.base_local_entropy)
    ledger = EntropyLedger(
        global_entropy=cfg.base_global_entropy,
        local_entropy=sum(g.local_entropy for g in girls),
        harvested_energy=0.0,
    )

    # Track how much cumulative order each girl has cast (drives witch burst).
    order_cast: Dict[str, float] = {g.name: 0.0 for g in girls}

    records: List[StepRecord] = []
    prev_total = ledger.total_entropy
    invariant_holds = True
    min_d_total = float("inf")

    for step in range(cfg.steps):
        girls, ledger = _apply_wishes(
            girls, rng, cfg, incubator, ledger, order_cast
        )
        girls, ledger, witches_this_step = _apply_witch_transformations(
            girls, step, cfg, incubator, ledger, order_cast
        )

        total = ledger.total_entropy
        d_total = total - prev_total
        ok = d_total >= -_EPS
        if not ok:
            invariant_holds = False
        min_d_total = min(min_d_total, d_total)

        records.append(
            StepRecord(
                step=step,
                total_entropy=total,
                global_entropy=ledger.global_entropy,
                local_entropy=ledger.local_entropy,
                harvested_energy=ledger.harvested_energy,
                d_total=d_total,
                invariant_ok=ok,
                witches_this_step=witches_this_step,
            )
        )
        prev_total = total

    if not records:
        min_d_total = 0.0

    return SimResult(
        config=cfg,
        records=tuple(records),
        final_girls=girls,
        invariant_holds=invariant_holds,
        min_d_total=min_d_total,
    )
