# Madoka Magica: Entropy & Karmic Calculus

A small, self-contained Python simulation of a closed system of magical girls,
a global entropy budget, and the incubators who harvest the difference. It is a
deliberate caricature of thermodynamics used to dramatize the story of *Puella
Magi Madoka Magica*, not a physics derivation.

## The concept (and its source material)

In *Madoka Magica*, the incubator Kyubey grants a girl one **wish** in exchange
for becoming a magical girl. A wish bends reality into a more ordered, more
desirable local state -- a healed body, an undone accident, a rescued life. But
that miracle is never free: it accrues **karmic destiny**. Every use of magic
clouds the girl's **soul gem**, and when the gem is fully corrupted she becomes
a **witch** -- a burst of despair released into the world.

Kyubey's species harvests the emotional energy of these transformations to
**fight the heat death of the universe** (the ultimate entropy maximum). The
show is, quite literally, about buying local order by exporting a larger cost
somewhere the buyer cannot see.

This project models that bargain as an entropy ledger.

## The model

We track one scalar "entropy" (dimensionless units), partitioned into:

- `S_local`  -- the summed entropy of each magical girl's subsystem. A wish
  imposes order here, so it **decreases** local entropy.
- `S_global` -- the universe's reservoir. The karmic cost is dumped here.

Total entropy is `S_total = S_global + sum(S_local)`.

### A wish (the karmic calculus)

For a wish that imposes `x > 0` units of local order:

```
d(S_local)  = -x                       # local order created (entropy down)
d(S_global) = +k * x   with k > 1      # strictly larger karmic cost
------------------------------------------------------------------
d(S_total)  = (k - 1) * x  >  0         # net entropy ALWAYS rises
```

That single inequality (`k > 1`) is the engine of the whole simulation. It is a
second-law-like invariant: **a local decrease in entropy must be paid for by a
strictly larger global increase.** The default `k = 1.8`.

### Soul gem purity -> witch transformation

Each girl starts at `purity = 1.0`. Every cast decays purity in proportion to
the order she forced onto the world (`decay_per_order * x`). When purity falls
to the `witch_threshold` (default `0.15`), she becomes a **witch**: an entropy
singularity that

1. evacuates her subsystem's local entropy into the global reservoir
   (total conserved for that move), then
2. dumps an additional **burst** of fresh entropy (`d(S_total) = +burst > 0`).

The burst scales with how much magic she cast in life -- the more miracles, the
bigger the despair.

### Incubators

The incubator (`Kyubey`) skims a fixed `harvest_fraction` (default `0.35`) of
the **karmic surplus** of each wish (`d_global + d_local`, i.e. the part of the
global increase beyond the local order removed) and of each witch burst. This
accumulates as `harvested_energy` -- the negentropy the incubators export to
delay heat death. It is bookkeeping *on top of* the ledger; it does not change
the total-entropy invariant.

## Honest framing (what this is and isn't)

This is a **measure/accounting caricature**, not real thermodynamics:

- "Entropy" here is a single made-up scalar with no units, temperature, or
  microstate count. There is no Boltzmann `S = k_B ln W`, no free energy, no
  actual heat.
- The second law is *imposed by construction* (`k > 1` per wish, `burst > 0`
  per witch), not *derived* from statistics. We enforce the invariant and then
  verify that our bookkeeping never accidentally breaks it -- that is the real
  software claim being tested.
- Real thermodynamics allows a subsystem's entropy to drop only when the
  surroundings' entropy rises by at least as much; our wish rule is the same
  spirit rendered as a strict, deliberately lossy inequality.
- The incubator "harvest" is a narrative label on a fraction of the surplus; it
  is not a Maxwell's-demon claim and does not reduce total entropy.

Treat the numbers as a story-shaped ledger whose one honest, checkable property
is: **total entropy is non-decreasing at every step.**

## Files

| File | Purpose |
|------|---------|
| `entropy.py`        | Immutable `EntropyLedger`; `wish_deltas()` karmic rule |
| `magical_girl.py`   | Immutable `MagicalGirl`; purity decay + witch flag |
| `incubator.py`      | `Incubator` harvest accounting |
| `simulation.py`     | Seeded simulation loop + per-step invariant check |
| `plot.py`           | Dependency-free ASCII line chart |
| `main.py`           | Demo entry point / CLI |
| `test_invariant.py` | `unittest` checks (model + invariant across 50 seeds) |

Pure standard library. `numpy` is **not** required.

## Run it

```bash
cd madoka-entropy
python3 main.py                 # default: seed 42, 120 steps
python3 main.py --seed 7        # any integer seed, fully reproducible
python3 main.py --steps 200

python3 -m unittest -v test_invariant   # run the test suite
```

## Sample output (`python3 main.py`, seed 42)

```
====================================================================
 MADOKA MAGICA  --  Entropy & Karmic Calculus
====================================================================
 seed=42  steps=120  girls=Madoka, Homura, Sayaka, Mami, Kyoko
 karmic_multiplier=1.8  (each wish: -x local, +1.8x global => net >0)
 witch_threshold(purity)=0.15  decay_per_order=0.06

GLOBAL entropy (the universe's reservoir) -- climbs with karma:
   433.0 |                 *oooooooooooooooooooooooooooooooooooooooooo
         |               **                                           
         |            *oo                                             
         |          o*                                                
         |        *o                                                  
         |      o*                                                    
         |    oo                                                      
   103.6 |ooo                                                         
         +------------------------------------------------------------
                 ^^  ^^  ^^^                                          
          step 0 .. 119   ('^' = witch transformation)

--------------------------------------------------------------------
 WITCH TRANSFORMATIONS (5):
   step   15:  Sayaka -> witch (entropy singularity)
   step   23:  Mami -> witch (entropy singularity)
   step   30:  Madoka -> witch (entropy singularity)
   step   30:  Kyoko -> witch (entropy singularity)
   step   33:  Homura -> witch (entropy singularity)

--------------------------------------------------------------------
 FINAL ACCOUNTING
   global_entropy    :      432.994
   local_entropy     :        0.000
   TOTAL entropy     :      432.994
   incubator harvest :       81.548  (negentropy)

====================================================================
 SECOND-LAW INVARIANT CHECK   (dS_total >= 0 every step)
====================================================================
   steps checked        : 120
   min per-step dS_total: +0.000000
   violations           : 0
   RESULT: PASS -- total entropy never decreased. 2nd law holds.
====================================================================
```

(The chart above is trimmed vertically for the README; the program prints a
taller chart plus a second chart for TOTAL entropy.)

### Reading the result

- **Global entropy rises monotonically** as girls spend wishes -- karma
  accumulating in the reservoir. Steep jumps (`*` columns) are witch bursts.
- The `^` marks on the x-axis are **witch transformations**: note the cascade
  around steps 15-33 as several gems corrupt in quick succession.
- Once every girl has become a witch, no more wishes are cast, so entropy
  flatlines -- `dS_total = 0`, which still satisfies "non-decreasing." That is
  why the reported `min per-step dS_total` is exactly `+0.000000`.
- **Invariant verification:** across the run (and across 200 seeds in the test
  suite) `dS_total >= 0` at every single step, with **0 violations**. The
  second-law-like invariant holds by construction and is checked empirically.

## Verifying the invariant yourself

The invariant is checked three ways:

1. **Per step, at runtime** (`simulation.py`): every step compares `S_total`
   against the previous step and flags any decrease.
2. **In the demo summary** (`main.py`): prints steps checked, min `dS_total`,
   and violation count.
3. **In the test suite** (`test_invariant.py`): asserts the invariant holds for
   50 different seeds, that the global reservoir is non-decreasing, and that the
   per-wish net entropy change is strictly positive.
```
