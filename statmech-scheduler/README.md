![Statistical-Mechanics Scheduler](./banner.png)

# Statistical-Mechanics Scheduler

**A CPU scheduler that picks the next task by sampling the Boltzmann distribution — one temperature knob slides continuously from strict priority to round-robin fairness.**

Concept & reference: the [Boltzmann (Gibbs) distribution](https://en.wikipedia.org/wiki/Boltzmann_distribution) from statistical mechanics, which gives the probability of a physical system occupying a state of energy `E_i` at temperature `T`. This project reuses that exact formula as a scheduling policy. It is a **pure numerical simulation** — it never touches the real operating-system scheduler and runs no privileged or destructive commands.

---

## TL;DR

- Tasks are "particles." Each task's **priority** maps to an **energy** (`E = -priority`); the system's **load** maps to a **temperature** `T`.
- The next task each tick is drawn with probability `p_i ∝ exp(-E_i / (kT))` — the Boltzmann weight.
- **Cold** (low load): all probability collapses onto the highest-priority task → behaves like a strict-priority scheduler.
- **Hot** (high load): the distribution flattens toward uniform → lower-priority tasks get CPU time, modelling anti-starvation/fairness pressure.
- The demo runs three load regimes at 200,000 decisions each and prints theory vs. empirical CPU share side by side. At 200k draws the maximum error is **~0.11%** and shrinks as draws grow — the law of large numbers in action.
- No third-party dependencies. Fully seeded and reproducible.

---

## The idea

Operating-system schedulers usually live at two extremes. *Strict priority* always runs the most important runnable task, which is simple but starves low-priority work. *Round-robin / fair* schedulers give everyone a slice, which is fair but ignores importance. Real schedulers glue these together with ad-hoc heuristics (priority boosting, aging, nice values, decay).

Statistical mechanics already solved the "how do I distribute a scarce resource across competing states as a function of one control parameter" problem more than a century ago. A gas at low temperature settles into its lowest-energy states; heat it up and higher-energy states become populated too. The **temperature** is the single knob that interpolates between "everything in the ground state" and "everything equally likely."

This scheduler borrows that machinery wholesale. Map importance to energy (important = low energy), map system load to temperature, and let the Boltzmann distribution decide who runs. One parameter now slides continuously between strict priority and fairness, with a precise, well-understood probability law behind every decision.

---

## The honest core

### The mathematics that is genuinely used

At thermal equilibrium the probability of a state `i` with energy `E_i` is the Boltzmann/Gibbs distribution:

```
p_i = exp(-E_i / (k·T)) / Z        where   Z = Σ_j exp(-E_j / (k·T))
```

`Z` is the **partition function** (the normaliser). The code implements this directly (`boltzmann/boltzmann.go`):

- **Energy from priority** (`scheduler/task.go`): `E = -priority`. A higher priority yields a lower (more negative) energy → a larger Boltzmann factor → selected more often. Any monotonically decreasing map would work; the linear one keeps the relationship between priority gaps and probability ratios easy to reason about, and the absolute offset cancels in normalisation.
- **Temperature from load** (`scheduler/temperature.go`): `T(load) = minT + load·(maxT − minT)`, with `load` clamped to `[0, 1]`.
- **Numerical stability**: `Z` and the probabilities are computed with the **log-sum-exp shift** — every exponent is taken relative to the minimum energy, `exp(-(E_i − E_min)·β)` with `β = 1/(kT)`. The shared factor cancels in the ratio, so probabilities are unchanged, but overflow/underflow is avoided when energies are large relative to `kT`.
- **Limits**:
  - `T → 0`: the distribution concentrates entirely on the minimum-energy state(s). `ProbabilitiesAtZeroT` returns the deterministic limit, splitting probability equally among tied minima — exactly a strict-priority scheduler.
  - `T → ∞`: the distribution flattens toward uniform (`1/N` each).
- **Sampling** (`boltzmann/sampler.go`): a precomputed cumulative distribution + inverse-CDF lookup on a seeded `math/rand` source. Empirical frequencies converge to `p_i` by the law of large numbers.

### What is real vs. simulated

| Aspect | Status |
|--------|--------|
| Boltzmann distribution, partition function `Z`, log-sum-exp, `T→0`/`T→∞` limits | **Real** — used correctly; empirical draws converge to theory |
| Boltzmann constant `k` | Set to `1` (natural units): a scheduler has no physical energy unit, so `k` is folded into the temperature scale. An honest simplification, not real thermodynamics. |
| "Energy" and "temperature" | **Chosen mappings** (`E = -priority`, linear `T(load)`), not measured physical quantities |
| Thermal dynamics | **None** — there is no reservoir, no time-evolution, no detailed balance; these are independent draws from the equilibrium distribution |
| The OS scheduler | **Never touched** — this is a numerical model that prints tables |

### Reproduced numbers (from `go run .`, seed 42, 200,000 decisions/regime)

Workload (energy `= −priority`):

| task | priority | energy |
|------|---------:|-------:|
| audio-daemon | 10 | −10.0 |
| ui-render | 7 | −7.0 |
| web-request | 5 | −5.0 |
| backup-job | 2 | −2.0 |
| log-rotate | 1 | −1.0 |

**LOW load (cold), T = 0.250** — almost all CPU to the top task (strict-priority limit):

| task | theory | empirical | abs.err |
|------|-------:|----------:|--------:|
| audio-daemon | 99.9994% | 100.0000% | 0.0006% |
| ui-render | 0.0006% | 0.0000% | 0.0006% |
| web-request | 0.0000% | 0.0000% | 0.0000% |
| backup-job | 0.0000% | 0.0000% | 0.0000% |
| log-rotate | 0.0000% | 0.0000% | 0.0000% |

**MED load (warm), T = 2.125** — priority dominates, others get time:

| task | theory | empirical | abs.err |
|------|-------:|----------:|--------:|
| audio-daemon | 72.6506% | 72.5440% | 0.1066% |
| ui-render | 17.7059% | 17.7795% | 0.0736% |
| web-request | 6.9083% | 6.9655% | 0.0572% |
| backup-job | 1.6836% | 1.6600% | 0.0236% |
| log-rotate | 1.0517% | 1.0510% | 0.0007% |

**HIGH load (hot), T = 4.000** — flattening toward uniform:

| task | theory | empirical | abs.err |
|------|-------:|----------:|--------:|
| audio-daemon | 50.0099% | 50.0220% | 0.0121% |
| ui-render | 23.6230% | 23.5090% | 0.1140% |
| web-request | 14.3281% | 14.3830% | 0.0549% |
| backup-job | 6.7681% | 6.8580% | 0.0899% |
| log-rotate | 5.2710% | 5.2280% | 0.0430% |

Across all three regimes the maximum theory-vs-empirical error stays around 0.11% at 200k decisions and shrinks further as the number of ticks grows — the empirical CPU split converges to the Boltzmann weights exactly as predicted.

---

## How it works

### File / package map

```
statmech-scheduler/
├── go.mod                        # module statmech-scheduler, Go 1.24.4, no deps
├── main.go                       # demo: three temperature regimes + comparison tables
├── boltzmann/                    # the statistical-mechanics core
│   ├── boltzmann.go              # Weight, PartitionFunction, Probabilities, ProbabilitiesAtZeroT
│   ├── sampler.go                # seeded inverse-CDF Sampler (reproducible draws)
│   ├── boltzmann_test.go
│   └── sampler_test.go
└── scheduler/                    # the scheduling layer built on top
    ├── task.go                   # Task particle, Energy() = -priority, Energies()
    ├── temperature.go            # TemperatureFromLoad(load, minT, maxT)
    └── scheduler.go              # selection loop + theory/empirical accounting
```

### Key algorithms

- **`boltzmann.Probabilities(energies, T)`** — computes `E_min`, then `w_i = exp(-(E_i − E_min)·β)`, sums to `Z`, returns `w_i / Z`. Returns a fresh slice; the input is never mutated. Errors on empty input (`ErrEmpty`) or `T ≤ 0` (`ErrNonPositiveTemperature`).
- **`boltzmann.PartitionFunction(energies, T)`** — the same shifted sum, exposed separately.
- **`boltzmann.ProbabilitiesAtZeroT(energies)`** — the deterministic `T→0` limit: equal share among tied minima, zero elsewhere.
- **`boltzmann.NewSampler(energies, T, seed)`** — precomputes the cumulative distribution once (pinning the last bucket to exactly `1.0` to defend against float drift) and owns a seeded PRNG. `Next()` does one `rng.Float64()` draw and an inverse-CDF scan.
- **`scheduler.New(tasks, T, quantumTicks, seed)`** — builds a sampler over the tasks' energies; defensively copies the task slice so caller mutation can't change the scheduler's view.
- **`Scheduler.Run(decisions)`** — draws `decisions` times, accounts `quantumTicks` per selection, then returns a `Result` with theoretical probabilities, empirical fractions, and per-task quanta.

---

## Install & run

Requires **Go 1.24+** (developed and verified on `go1.24.4`). No third-party dependencies.

```bash
cd statmech-scheduler
go build ./...     # compile everything
go test ./...      # run the unit tests
go run .           # run the three-regime demo
```

Flags (all optional; defaults shown):

```bash
go run . \
  -seed 42 \          # PRNG seed; identical seeds => identical runs
  -decisions 200000 \ # scheduling decisions per regime
  -quantum 1 \        # ticks accounted per selection (time-slice length)
  -minT 0.25 \        # temperature at zero load (cold: strict priority)
  -maxT 4.0           # temperature at full load (hot: near-uniform)
```

### Captured sample output

```
Statistical-Mechanics Scheduler (simulation only)
seed=42  decisions/regime=200000  quantum=1 ticks  minT=0.25  maxT=4.00
Higher priority => lower energy => selected more often when cold.

=== LOW load  (cold) | load=0.00 | T=0.250 | ticks=200000 ===
task             prio   energy     theory  empirical   abs.err
--------------------------------------------------------------
audio-daemon       10    -10.0   99.9994%  100.0000%   0.0006%
ui-render           7     -7.0    0.0006%    0.0000%   0.0006%
web-request         5     -5.0    0.0000%    0.0000%   0.0000%
backup-job          2     -2.0    0.0000%    0.0000%   0.0000%
log-rotate          1     -1.0    0.0000%    0.0000%   0.0000%
max abs error (theory vs empirical): 0.0006%

=== MED load  (warm) | load=0.50 | T=2.125 | ticks=200000 ===
task             prio   energy     theory  empirical   abs.err
--------------------------------------------------------------
audio-daemon       10    -10.0   72.6506%   72.5440%   0.1066%
ui-render           7     -7.0   17.7059%   17.7795%   0.0736%
web-request         5     -5.0    6.9083%    6.9655%   0.0572%
backup-job          2     -2.0    1.6836%    1.6600%   0.0236%
log-rotate          1     -1.0    1.0517%    1.0510%   0.0007%
max abs error (theory vs empirical): 0.1066%

=== HIGH load (hot) | load=1.00 | T=4.000 | ticks=200000 ===
task             prio   energy     theory  empirical   abs.err
--------------------------------------------------------------
audio-daemon       10    -10.0   50.0099%   50.0220%   0.0121%
ui-render           7     -7.0   23.6230%   23.5090%   0.1140%
web-request         5     -5.0   14.3281%   14.3830%   0.0549%
backup-job          2     -2.0    6.7681%    6.8580%   0.0899%
log-rotate          1     -1.0    5.2710%    5.2280%   0.0430%
max abs error (theory vs empirical): 0.1140%
```

Every run is seeded. `boltzmann.NewSampler(energies, T, seed)` owns its own `math/rand` source, so a given seed always produces the same sequence of task selections. Change `-seed` to get a different (but equally reproducible) run.

---

## Testing

```bash
go test ./...            # run the suite
go test -race ./...      # with the race detector
go test -cover ./...     # with coverage
```

Only the `boltzmann` package has tests; `main` and `scheduler` are exercised end-to-end by running the demo but carry no `_test.go` files.

- `boltzmann` package coverage: **85.1% of statements** (`go test -cover`).
- `statmech-scheduler` (main) and `scheduler`: **no test files** (0.0%).

The `boltzmann` tests verify:

- probabilities normalise to 1 across temperatures (`TestProbabilitiesSumToOne`, tolerance `1e-12`),
- lower energy ⇒ strictly higher probability (`TestLowerEnergyHasHigherProbability`),
- high temperature flattens toward uniform while cold concentrates on the top task (`TestHighTemperatureFlattens`),
- the partition function equals the summed shifted weights (`TestPartitionFunctionMatchesWeights`),
- the `T→0` limit splits probability equally across tied minima (`TestZeroTemperatureLimit`, e.g. two tied minima → `[0.5, 0.5, 0, 0]`),
- error paths (`ErrEmpty`, `ErrNonPositiveTemperature`),
- identical seeds reproduce draw sequences and different seeds diverge (`TestSamplerReproducible`),
- empirical sampling frequencies converge to the Boltzmann probabilities over 400,000 draws within `5e-3` (`TestSamplerConvergesToBoltzmann`).

---

## Limitations & honest caveats

- **It is a model, not a kernel.** Nothing here schedules real threads. It draws indices from a distribution and tabulates the result.
- **`k = 1` is a convention.** There is no physical energy unit in a scheduler, so the Boltzmann constant is absorbed into the temperature scale. The thermodynamic analogy is illustrative, not literal.
- **The mappings are choices.** `E = -priority` and the linear `T(load)` are picked for interpretability. Different monotone maps give different (but equally valid) policies.
- **No dynamics.** There is no reservoir, no relaxation, no detailed balance — just i.i.d. draws from the equilibrium distribution. A real scheduler would also need preemption, I/O blocking, fairness accounting over time, and so on.
- **Float precision.** Extremely cold temperatures push all probability onto one task; the `T→0` limit is available exactly via `ProbabilitiesAtZeroT`, but the sampler always runs at a strictly positive `T` (`minT`) to avoid dividing by zero.

---

## References

- Boltzmann distribution — https://en.wikipedia.org/wiki/Boltzmann_distribution
- Partition function (statistical mechanics) — https://en.wikipedia.org/wiki/Partition_function_(statistical_mechanics)
- Log-sum-exp / numerical stability — https://en.wikipedia.org/wiki/LogSumExp
- Softmax function (the same normalised-exponential form, widely used in ML) — https://en.wikipedia.org/wiki/Softmax_function
- Inverse transform sampling — https://en.wikipedia.org/wiki/Inverse_transform_sampling
