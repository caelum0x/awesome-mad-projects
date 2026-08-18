"""The closed-system simulation loop.

Each step:
  1. Every living girl may cast magic (make a wish) with some probability.
     - Local entropy of her subsystem drops; global entropy rises by a
       strictly larger karmic cost; her soul gem purity decays.
     - The incubator harvests a fraction of the karmic surplus.
  2. Any girl whose purity has crossed the witch threshold transforms into a
     witch: an entropy singularity that dumps a burst into the global reservoir.
     Her frozen local order is released back into the total as well.
  3. We verify the second-law-like invariant: total entropy this step is
     >= total entropy last step (dS_total >= 0), and record the result.

Everything is driven by a single seeded random.Random instance so runs are
fully reproducible.
"""

import random
from dataclasses import dataclass, field

from entropy import EntropyLedger, wish_deltas
from incubator import Incubator
from magical_girl import MagicalGirl, make_girls


@dataclass(frozen=True)
class SimConfig:
    """All tunable parameters for a run (immutable)."""

    seed: int = 42
    steps: int = 120
    girl_names: tuple = ("Madoka", "Homura", "Sayaka", "Mami", "Kyoko")
    base_local_entropy: float = 20.0     # starting subsystem entropy per girl
    base_global_entropy: float = 100.0   # starting reservoir entropy

    wish_probability: float = 0.55       # chance a living girl casts per step
    local_order_min: float = 0.4         # min order imposed per cast
    local_order_max: float = 1.6         # max order imposed per cast
    karmic_multiplier: float = 1.8       # global cost factor (> 1 => 2nd law)

    decay_per_order: float = 0.06        # purity lost per unit of order imposed
    witch_threshold: float = 0.15        # purity at/below which she turns
    witch_burst_base: float = 12.0       # base entropy dumped on transformation
    witch_burst_per_order: float = 1.5   # extra burst per unit of order she cast


@dataclass(frozen=True)
class StepRecord:
    """Immutable log entry for a single simulation step."""

    step: int
    total_entropy: float
    global_entropy: float
    local_entropy: float
    harvested_energy: float
    d_total: float                 # change in total entropy vs previous step
    invariant_ok: bool             # d_total >= 0 ?
    witches_this_step: tuple = ()  # names that transformed on this step


@dataclass(frozen=True)
class SimResult:
    """Everything produced by a run."""

    config: SimConfig
    records: tuple
    final_girls: tuple
    invariant_holds: bool          # True iff every step had d_total >= 0
    min_d_total: float             # smallest per-step dS_total observed


def _order_cast_this_step(rng: random.Random, cfg: SimConfig) -> float:
    """Draw the amount of local order a girl imposes when she casts."""
    return rng.uniform(cfg.local_order_min, cfg.local_order_max)


def run_simulation(cfg: SimConfig = SimConfig()) -> SimResult:
    """Run the whole simulation and return an immutable SimResult."""
    rng = random.Random(cfg.seed)
    incubator = Incubator()

    girls = make_girls(cfg.girl_names, cfg.base_local_entropy)
    ledger = EntropyLedger(
        global_entropy=cfg.base_global_entropy,
        local_entropy=sum(g.local_entropy for g in girls),
        harvested_energy=0.0,
    )

    # Track how much cumulative order each girl has cast (drives witch burst).
    order_cast = {g.name: 0.0 for g in girls}

    records = []
    prev_total = ledger.total_entropy
    invariant_holds = True
    min_d_total = float("inf")

    for step in range(cfg.steps):
        # --- Phase 1: wishes / magic casting ---------------------------------
        new_girls = []
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
        girls = tuple(new_girls)

        # --- Phase 2: witch transformations ----------------------------------
        witches_this_step = []
        transformed = []
        for girl in girls:
            if (not girl.is_witch) and girl.purity <= cfg.witch_threshold:
                burst = (
                    cfg.witch_burst_base
                    + cfg.witch_burst_per_order * order_cast[girl.name]
                )
                # The singularity (a) evacuates her subsystem's local entropy
                # into the global reservoir so the total is conserved for that
                # move, then (b) dumps an additional `burst` of fresh entropy.
                #   d_local  = -girl.local_entropy       (subsystem removed)
                #   d_global = +girl.local_entropy + burst
                # Net total change = +burst > 0, preserving the invariant.
                ledger = ledger.with_changes(
                    d_global=girl.local_entropy + burst,
                    d_local=-girl.local_entropy,
                    d_harvest=incubator.harvest_from_witch(burst),
                )
                transformed.append(girl.become_witch(step))
                witches_this_step.append(girl.name)
            else:
                transformed.append(girl)
        girls = tuple(transformed)

        # --- Phase 3: invariant check + logging ------------------------------
        total = ledger.total_entropy
        d_total = total - prev_total
        ok = d_total >= -1e-9  # tiny tolerance for float noise
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
                witches_this_step=tuple(witches_this_step),
            )
        )
        prev_total = total

    return SimResult(
        config=cfg,
        records=tuple(records),
        final_girls=girls,
        invariant_holds=invariant_holds,
        min_d_total=min_d_total,
    )
