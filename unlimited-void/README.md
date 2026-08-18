# Unlimited Void — as a Container Runtime (simulation)

A small, self-contained Go simulation that models Satoru Gojo's Domain Expansion
**"Unlimited Void"** (from *Jujutsu Kaisen*) as if it were a container runtime
primitive: a privileged "caster" process opens a domain over other processes and
paralyzes them by showing them **infinity**.

> **This is a bounded SIMULATION, not a real denial-of-service tool.** No real
> memory is exhausted, no real CPU is flooded, no fork bombs are spawned, and no
> real logs are flooded. "Infinity" is represented entirely as integer counters.
> See [Safety model](#safety-model).

## The concept (JJK)

In *Jujutsu Kaisen*, Gojo's **Unlimited Void** traps victims and feeds their
minds an infinite stream of information. They receive so much that they cannot
process any of it, so they are frozen — "shown infinity, and unable to act" —
for as long as the domain is open. Gojo himself, the caster, is immune.

## The systems core (honest description)

Each "process" is a simulated **goroutine-actor** with a **finite attention
budget** per tick — the number of virtual information units it can attend to in
one step. This is the honest core of the model:

- **Normal tick** (`tickNormal`): useful tasks arrive (`UsefulInflow`, kept below
  the budget) and are completed, so the process does useful work every tick.
- **Domain Expansion** (`Domain.Expand`): the caster floods every victim with
  `FloodPerTick` virtual info units, where `FloodPerTick = maxVictimBudget * 1000`.
  Because the flood dwarfs the budget, **all** of a victim's attention is spent
  just perceiving the flood, and useful-work throughput drops to **~0**.
- **Immunity**: the caster is never a victim of its own domain, so it keeps
  working normally.
- **Domain close** (`Domain.Close`): the flood was an illusion, so it vanishes —
  each victim's virtual queue is dispelled to 0 and throughput **recovers** on
  the next tick.

Ticks are driven concurrently: on every step the orchestrator fans a tick out to
one goroutine per actor (`sim.go`), waits for all of them, then prints. Each
actor only mutates its own state, so the model is race-free (verified with
`go run -race .`).

### Files

| File | Responsibility |
|------|----------------|
| `process.go` | `Process` actor: attention budget, virtual queue, counters, per-tick logic |
| `domain.go`  | `Domain` (Unlimited Void): open/close, flood rate, victim membership |
| `sim.go`     | Orchestration: concurrent goroutine-actor ticks, per-tick printing |
| `metrics.go` | Per-phase throughput measurement and tables |
| `main.go`    | Demo: normal → Unlimited Void → recovery, plus summary |

## Safety model

The whole point of the prompt is danger; the whole point of this code is that it
is **safe**:

- The victim's backlog is a single integer `VirtualQueue`, **capped** at
  `QueueCap = 10_000`. Anything beyond the cap is added to an `Overflow` counter
  (a number) instead of being stored. **The model never holds "infinity" in
  memory — it holds a growing integer.**
- `injectFlood` never allocates memory proportional to the flood size; it only
  updates counters.
- No unbounded goroutines: exactly one goroutine per actor per tick, joined via a
  `WaitGroup` before the next tick.
- No real I/O flooding, no host resource exhaustion.

## Run

Requires Go 1.24+.

```bash
cd unlimited-void
go build ./...      # compile
go vet ./...        # static checks
go run .            # run the demo
go run -race .      # run with the race detector (clean)
```

## Sample output

Per-tick snapshot (abridged) — `*` = caster, `!` = flooded victim,
`q` = capped virtual queue, `ovf` = overflow counter:

```
[t=05 normal    ] * gojo (caster) work=400   q=0    ovf=0       |   worker-a work=400 q=0    ovf=0      | ...

>>> DOMAIN EXPANSION: UNLIMITED VOID  (caster: gojo (caster))
    Victims are shown infinity: 120000 virtual info units / tick vs. budgets ~120/tick.

[t=06 VOID      ] * gojo (caster) work=480   q=0    ovf=0       | ! worker-a work=400 q=9900 ovf=110000 | ...
[t=13 VOID      ] * gojo (caster) work=1040  q=0    ovf=0       | ! worker-a work=400 q=9900 ovf=949300 | ...

<<< DOMAIN CLOSED  (caster: gojo (caster)). The flood vanishes; victims recover throughput.

[t=14 recover   ] * gojo (caster) work=1120  q=0    ovf=0       |   worker-a work=480 q=0    ovf=949300 | ...
```

### Throughput tables

Useful work per tick, per phase. Victims **flatline** while the domain is open;
the caster is unaffected; victims **recover** after close.

**Phase 1 — normal operation**

| process       | role   | work/tick | work(total) | budget/tick |
|---------------|--------|-----------|-------------|-------------|
| gojo (caster) | caster | 80.0      | 400         | 100         |
| worker-a      | victim | 80.0      | 400         | 100         |
| worker-b      | victim | 90.0      | 450         | 120         |
| worker-c      | victim | 60.0      | 300         | 80          |

**Phase 2 — Unlimited Void open** (victims shown infinity)

| process       | role   | work/tick | work(total) | budget/tick |
|---------------|--------|-----------|-------------|-------------|
| gojo (caster) | caster | 80.0      | 640         | 100         |
| worker-a      | victim | **0.0**   | **0**       | 100         |
| worker-b      | victim | **0.0**   | **0**       | 120         |
| worker-c      | victim | **0.0**   | **0**       | 80          |

**Phase 3 — recovery** (domain closed)

| process       | role   | work/tick | work(total) | budget/tick |
|---------------|--------|-----------|-------------|-------------|
| gojo (caster) | caster | 80.0      | 480         | 100         |
| worker-a      | victim | 80.0      | 480         | 100         |
| worker-b      | victim | 90.0      | 540         | 120         |
| worker-c      | victim | 60.0      | 360         | 80          |

**Virtual flood accounting** (nothing was actually allocated)

| process       | virt-injected | queue-capped | overflow |
|---------------|---------------|--------------|----------|
| gojo (caster) | 0             | 0            | 0        |
| worker-a      | 960000        | 0            | 949300   |
| worker-b      | 960000        | 0            | 949160   |
| worker-c      | 960000        | 0            | 949440   |

Each victim had ~960,000 virtual units "injected" over 8 ticks, but the stored
queue never exceeded `QueueCap = 10,000`; the rest is just the `overflow`
integer. That is how the simulation shows "infinity" without ever allocating it.

## Tuning

Edit the constants:

- `warmupTicks`, `domainTicks`, `recoveryTicks` in `main.go` — phase lengths.
- `FloodMultiplier` in `domain.go` — how overwhelming the flood is.
- `QueueCap` in `process.go` — the modeled backlog cap.
- Process budgets / inflows in `NewSimulation` (`sim.go`).
