# Statistical-Mechanics Scheduler

A **simulation-only** CPU scheduler that borrows the mathematics of
statistical mechanics. Tasks are treated as particles; each has an *energy*
derived from its priority, and the system has a *temperature* derived from its
load. The next task to run each tick is drawn from the **Boltzmann
distribution**.

> This program is a pure numerical simulation. It **never** touches the real
> operating-system scheduler and runs no privileged or destructive commands.

## Concept

In a physical system at thermal equilibrium, the probability of finding the
system in a state `i` with energy `E_i` follows the Boltzmann (Gibbs)
distribution:

```
p_i = exp(-E_i / (k*T)) / Z        Z = sum_j exp(-E_j / (k*T))
```

`Z` is the **partition function** (the normaliser). We reuse this exact formula
to pick tasks:

- **Energy from priority.** A high-priority task should be favoured, so it must
  sit *low* in the energy landscape. We map `E = -priority`. Higher priority =>
  lower (more negative) energy => larger Boltzmann factor => picked more often.
- **Temperature from load.** Temperature is a knob on randomness.
  - **Cold (low load):** the distribution collapses onto the lowest-energy
    (highest-priority) task — effectively a strict-priority scheduler.
  - **Hot (high load):** the distribution flattens toward uniform, so
    lower-priority tasks occasionally get the CPU. This models the
    fairness / anti-starvation pressure that shows up when the run queue is
    saturated.

The temperature knob is the whole point: one parameter continuously
interpolates between "strict priority" and "round-robin-ish fairness".

## Honest physics (what is real and what is analogy)

- **Real:** the Boltzmann distribution, the partition function `Z`, the
  log-sum-exp trick for numerical stability, and the T→0 / T→∞ limits are all
  used correctly. Empirical sampling frequencies genuinely converge to the
  theoretical weights (law of large numbers).
- **Analogy / simplification (not real thermodynamics):**
  - Boltzmann's constant `k` is set to `1`. A scheduler has no physical energy
    unit, so `k` is folded into the temperature scale (natural units).
  - "Energy" and "temperature" are chosen mappings (`E = -priority`,
    `T = minT + load*(maxT-minT)`), not measured physical quantities. Any
    monotonic maps would do; these are picked for interpretability.
  - There is no real thermal reservoir, no dynamics, no detailed balance being
    simulated — just independent draws from the equilibrium distribution.

## Layout

```
statmech-scheduler/
├── go.mod
├── main.go                     # demo: runs low/medium/high temperature regimes
├── boltzmann/
│   ├── boltzmann.go            # Z, weights, probabilities, T->0 limit
│   ├── sampler.go              # deterministic seeded inverse-CDF sampler
│   ├── boltzmann_test.go
│   └── sampler_test.go
└── scheduler/
    ├── task.go                 # Task particle + priority->energy mapping
    ├── temperature.go          # load->temperature mapping
    └── scheduler.go            # the selection loop + theory/empirical accounting
```

## Requirements

- Go 1.24+ (developed and verified on `go1.24.4`). No third-party dependencies.

## Run

```bash
cd statmech-scheduler
go build ./...     # compile everything
go test ./...      # run the unit tests
go run .           # run the three-regime demo
```

Flags (all optional, shown with defaults):

```bash
go run . \
  -seed 42 \          # PRNG seed; identical seeds => identical runs
  -decisions 200000 \ # scheduling decisions per regime
  -quantum 1 \        # ticks accounted per selection (time-slice length)
  -minT 0.25 \        # temperature at zero load (cold: strict priority)
  -maxT 4.0           # temperature at full load (hot: near-uniform)
```

## Sample output (theory vs empirical)

Actual run: `go run .` with `seed=42`, `decisions=200000`, `quantum=1`,
`minT=0.25`, `maxT=4.0`. Workload:

| task          | priority | energy |
|---------------|---------:|-------:|
| audio-daemon  |       10 |  -10.0 |
| ui-render     |        7 |   -7.0 |
| web-request   |        5 |   -5.0 |
| backup-job    |        2 |   -2.0 |
| log-rotate    |        1 |   -1.0 |

**LOW load (cold), T = 0.250** — almost all CPU goes to the top-priority task:

| task          |    theory |  empirical |  abs.err |
|---------------|----------:|-----------:|---------:|
| audio-daemon  | 99.9994%  | 100.0000%  | 0.0006%  |
| ui-render     |  0.0006%  |   0.0000%  | 0.0006%  |
| web-request   |  0.0000%  |   0.0000%  | 0.0000%  |
| backup-job    |  0.0000%  |   0.0000%  | 0.0000%  |
| log-rotate    |  0.0000%  |   0.0000%  | 0.0000%  |

**MED load (warm), T = 2.125** — priority still dominates but others get time:

| task          |   theory | empirical | abs.err |
|---------------|---------:|----------:|--------:|
| audio-daemon  | 72.6506% | 72.5440%  | 0.1066% |
| ui-render     | 17.7059% | 17.7795%  | 0.0736% |
| web-request   |  6.9083% |  6.9655%  | 0.0572% |
| backup-job    |  1.6836% |  1.6600%  | 0.0236% |
| log-rotate    |  1.0517% |  1.0510%  | 0.0007% |

**HIGH load (hot), T = 4.000** — the distribution flattens toward uniform:

| task          |   theory | empirical | abs.err |
|---------------|---------:|----------:|--------:|
| audio-daemon  | 50.0099% | 50.0220%  | 0.0121% |
| ui-render     | 23.6230% | 23.5090%  | 0.1140% |
| web-request   | 14.3281% | 14.3830%  | 0.0549% |
| backup-job    |  6.7681% |  6.8580%  | 0.0899% |
| log-rotate    |  5.2710% |  5.2280%  | 0.0430% |

Across all regimes the maximum theory-vs-empirical error stays around 0.1% at
200k decisions, and shrinks further as the number of ticks grows — the
empirical CPU split converges to the Boltzmann weights, exactly as the theory
predicts.

## Reproducibility

Every run is seeded. `boltzmann.NewSampler(energies, T, seed)` owns its own
`math/rand` source, so a given seed always produces the same sequence of task
selections. Change `-seed` to get a different (but equally reproducible) run.

## Tests

`go test ./...` covers:

- probabilities normalise to 1 across temperatures,
- lower energy => higher probability,
- high temperature flattens toward uniform,
- the partition function matches the summed weights,
- the T→0 limit shares probability across tied minima,
- identical seeds reproduce draw sequences and different seeds diverge,
- empirical sampling frequencies converge to the Boltzmann probabilities.
