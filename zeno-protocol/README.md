# Zeno's Paradox Transport Protocol

A tiny, self-contained Go prototype that delivers a message by moving it **half
of the remaining distance to the destination on every tick** — a toy transport
built directly on Zeno of Elea's *dichotomy paradox*.

## The concept: Zeno's dichotomy paradox

To reach a destination, you must first travel half the distance. Then you must
travel half of what remains. Then half of *that*. And so on, forever. Zeno
argued that because this requires completing infinitely many steps, motion is
impossible — you can never truly arrive.

This protocol takes the paradox literally: a "message" is delivered by covering
half of the remaining gap on each tick. The receiver accumulates the progress.

## The honest math

Model the journey as a normalized position in `[0, 1)`. On tick `k` the sender
covers **half of the remaining gap**, which is `(1/2)^k` of the whole journey.
Cumulative progress after `k` ticks is the partial sum of a geometric series:

```
progress(k) = 1/2 + 1/4 + 1/8 + ... + (1/2)^k
            = sum_{i=1..k} (1/2)^i
            = 1 - (1/2)^k
```

The remaining gap ("residual") after `k` ticks is exactly:

```
residual(k) = (1/2)^k
```

Key honest facts:

- The series **converges to 1** as `k -> infinity`.
- For **every finite `k`, progress(k) < 1**: there is always a residual gap of
  `(1/2)^k > 0`. In exact arithmetic the message *never* fully arrives. It only
  gets arbitrarily close.
- Doubling `k` squares how close you are: the residual halves every tick.

### Making real payloads actually complete: the epsilon threshold

A real transport must eventually deliver bytes. We introduce an epsilon
"close enough to deliver" threshold: once `residual(k) <= eps`, the receiver
accepts the payload as delivered. Solving for the number of ticks needed:

```
(1/2)^k <= eps
2^-k     <= eps
-k       <= log2(eps)
k        >= log2(1/eps)

  =>  k = ceil( log2(1/eps) )        // TicksForEpsilon(eps)
```

This is the load-bearing relationship. Some reference points:

| epsilon   | 1/epsilon | k = ceil(log2(1/eps)) | residual at k = (1/2)^k |
|-----------|-----------|------------------------|--------------------------|
| 0.5       | 2         | 1                      | 0.5                      |
| 0.25      | 4         | 2                      | 0.25                     |
| 0.1       | 10        | 4                      | 0.0625                   |
| 1e-3      | 1 000     | 10                     | ~9.77e-04                |
| 1e-6      | 1 000 000 | 20                     | ~9.54e-07                |
| 1e-9      | 1e9       | 30                     | ~9.31e-10                |

Halving the residual each tick means the tick cost grows only **logarithmically**
in the precision you demand — convergence is fast even though it is never exact.

### Pure paradox mode (`eps = 0`)

With `eps = 0` the threshold can never be met, so delivery never completes. The
run is capped at `MaxTicks` and reports the residual gap `(1/2)^MaxTicks` that
always remains — a direct, runnable illustration of the paradox.

## Layout

```
zeno-protocol/
├── go.mod
├── main.go              # demo: convergence trace + pure-paradox mode
└── zeno/
    ├── math.go          # Progress, Residual, StepFraction, TicksForEpsilon
    ├── transport.go     # in-process channel transport (sender + receiver)
    └── zeno_test.go     # unit tests for the math and the transport
```

The transport is fully **in-process**: the sender runs in a goroutine and emits
one packet per tick over a Go channel to the receiver. No network, no sockets,
no permissions required. (The channel plays the role of a lossless loopback.)

## Run it

Requires Go 1.24+.

```bash
cd zeno-protocol
go build ./...     # compile
go test ./...      # run unit tests
go run .           # run the demo
```

## Sample output

```
=== Zeno's Paradox Transport Protocol ===
Each tick moves the message HALF of the remaining distance.
Cumulative progress after k ticks = 1 - (1/2)^k.

--- Delivery mode (epsilon = 1e-06) ---
Closed form: k = ceil(log2(1/eps)) = ceil(log2(1e+06)) = 20
Residual gap at k=20 is (1/2)^20 = 9.5367431640625e-07 (<= eps, so we deliver)

tick  step           progress       residual
----------------------------------------------------
1     0.5000000000   0.5000000000   5.000e-01
2     0.2500000000   0.7500000000   2.500e-01
3     0.1250000000   0.8750000000   1.250e-01
4     0.0625000000   0.9375000000   6.250e-02
5     0.0312500000   0.9687500000   3.125e-02
6     0.0156250000   0.9843750000   1.562e-02
  ...
18    0.0000038147   0.9999961853   3.815e-06
19    0.0000019073   0.9999980927   1.907e-06
20    0.0000009537   0.9999990463   9.537e-07       <- close enough: DELIVERED

Converged within epsilon in 20 ticks.
Final progress = 0.999999046326 (residual gap = 9.537e-07)
Receiver holds: "Hello, Elea!" (delivered=true)

--- Pure paradox mode (epsilon = 0, capped at 20 ticks) ---
tick  progress         residual
----------------------------------------
1     0.500000000000   5.000e-01
2     0.750000000000   2.500e-01
3     0.875000000000   1.250e-01
4     0.937500000000   6.250e-02
5     0.968750000000   3.125e-02
  ...
18    0.999996185303   3.815e-06
19    0.999998092651   1.907e-06
20    0.999999046326   9.537e-07

Stopped after the 20-tick cap. Delivered = false.
Progress = 0.999999046326, but a residual gap of 9.537e-07 always remains.
In exact arithmetic the message "Hello, Elea!" never fully arrives.
```

## Notes on honesty and scope

- This is a **toy**. It is "reliable-ish": the in-process channel is lossless,
  so there is no retransmission, ACK, or congestion logic — the interesting part
  is the Zeno delivery schedule, not production networking.
- The math uses `math.Ldexp(1, -k)` to compute `2^-k` exactly (no repeated
  multiplication rounding). Around `k = 53` the residual underflows the float64
  mantissa and progress becomes indistinguishable from `1.0` in floating point —
  a practical limit of the machine, not of the exact-arithmetic argument, which
  is why the closed-form `k = ceil(log2(1/eps))` is reported alongside the trace.
