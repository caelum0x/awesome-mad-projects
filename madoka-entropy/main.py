"""Demo entry point: Madoka Magica Entropy & Karmic Calculus.

Run:  python3 main.py            (default seed 42)
      python3 main.py --seed 7   (any integer seed, reproducible)
      python3 main.py --steps 200

Prints:
  * a per-run summary of the karmic parameters,
  * an ASCII chart of GLOBAL entropy rising over time with witch marks,
  * an ASCII chart of TOTAL entropy (must be monotonic non-decreasing),
  * the incubator energy harvest,
  * a verification report of the second-law invariant (dS_total >= 0).
"""

import argparse

from plot import ascii_line_chart
from simulation import SimConfig, run_simulation


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Madoka Magica entropy simulation.")
    p.add_argument("--seed", type=int, default=42, help="RNG seed (reproducible)")
    p.add_argument("--steps", type=int, default=120, help="number of steps")
    return p.parse_args()


def _witch_events(records) -> list:
    """Return (step, name) tuples for every witch transformation."""
    events = []
    for rec in records:
        for name in rec.witches_this_step:
            events.append((rec.step, name))
    return events


def main() -> None:
    args = _parse_args()
    cfg = SimConfig(seed=args.seed, steps=args.steps)
    result = run_simulation(cfg)
    records = result.records

    print("=" * 68)
    print(" MADOKA MAGICA  --  Entropy & Karmic Calculus")
    print("=" * 68)
    print(f" seed={cfg.seed}  steps={cfg.steps}  girls={', '.join(cfg.girl_names)}")
    print(
        f" karmic_multiplier={cfg.karmic_multiplier}  "
        f"(each wish: -x local, +{cfg.karmic_multiplier}x global => net >0)"
    )
    print(
        f" witch_threshold(purity)={cfg.witch_threshold}  "
        f"decay_per_order={cfg.decay_per_order}"
    )
    print()

    global_series = [r.global_entropy for r in records]
    total_series = [r.total_entropy for r in records]
    witch_steps = {r.step for r in records if r.witches_this_step}

    print(ascii_line_chart(
        global_series, marks=witch_steps,
        title="GLOBAL entropy (the universe's reservoir) -- climbs with karma:",
    ))
    print()
    print(ascii_line_chart(
        total_series, marks=witch_steps,
        title="TOTAL entropy S_global + sum(S_local) -- 2nd-law monotone:",
    ))
    print()

    # Witch cascade report.
    events = _witch_events(records)
    print("-" * 68)
    if events:
        print(f" WITCH TRANSFORMATIONS ({len(events)}):")
        for step, name in events:
            print(f"   step {step:>4}:  {name} -> witch (entropy singularity)")
    else:
        print(" No witch transformations this run.")
    print()

    final = records[-1]
    print("-" * 68)
    print(" FINAL ACCOUNTING")
    print(f"   global_entropy    : {final.global_entropy:12.3f}")
    print(f"   local_entropy     : {final.local_entropy:12.3f}")
    print(f"   TOTAL entropy     : {final.total_entropy:12.3f}")
    print(f"   incubator harvest : {final.harvested_energy:12.3f}  (negentropy)")
    print()

    # Invariant verification.
    print("=" * 68)
    print(" SECOND-LAW INVARIANT CHECK   (dS_total >= 0 every step)")
    print("=" * 68)
    violations = [r for r in records if not r.invariant_ok]
    print(f"   steps checked        : {len(records)}")
    print(f"   min per-step dS_total: {result.min_d_total:+.6f}")
    print(f"   violations           : {len(violations)}")
    if result.invariant_holds:
        print("   RESULT: PASS -- total entropy never decreased. 2nd law holds.")
    else:
        print("   RESULT: FAIL -- invariant violated (see steps below):")
        for r in violations[:10]:
            print(f"     step {r.step}: dS_total={r.d_total:+.6f}")
    print("=" * 68)


if __name__ == "__main__":
    main()
