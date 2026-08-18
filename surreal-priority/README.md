# Surreal Priority

A small, self-contained Rust prototype that uses a usable subset of
**Conway's surreal numbers** as **process priorities**, and drives a
deterministic scheduler *simulation* with them.

The point: surreal numbers give you a single ordered number line that contains
finite integers, dyadic fractions, *infinities* (`omega`), and *infinitesimals*
(`1/omega`) all at once. Encoding scheduler priorities as surreals lets you say
things ordinary integer priorities cannot:

- a task with priority `omega` outranks **every** finite-priority task, so it
  starves them until it finishes;
- a task with priority `1/omega` is positive but below **every** positive finite
  priority, so it only runs when literally nothing else is runnable (a perfect
  "idle / best-effort" band);
- you still get the whole finite spectrum in between, plus lexicographic
  combinations like `omega + 3` or `2*omega`.

> This is a **simulation**. It never touches the OS scheduler, spawns no
> processes, and runs no privileged calls. It is a pure in-memory model.

---

## Concept and reference

Surreal numbers were introduced by John H. Conway and popularized in Donald
Knuth's book *Surreal Numbers* (1974). Each surreal is a pair `{ L | R }` of
sets of previously-created surreal numbers, built up over "days":

- Day 0 creates `0 = { | }`.
- Finite days create every **dyadic rational** `n / 2^k` (e.g. `1`, `-2`,
  `1/2`, `3/4`).
- Day `omega` (the first infinite ordinal) creates the infinite number
  `omega = { 0, 1, 2, 3, ... | }` and, shortly after, its infinitesimal
  reciprocal `1/omega = { 0 | 1, 1/2, 1/4, ... }`.

Reference reading:

- J. H. Conway, *On Numbers and Games* (1976) — the original construction.
- D. E. Knuth, *Surreal Numbers* (1974) — gentle narrative introduction.
- H. Gonshor, *An Introduction to the Theory of Surreal Numbers* (1986).

---

## Honest math core (what is and isn't implemented)

Full surreal numbers form a proper class and are defined by transfinite
recursion. Implementing all of that is unnecessary for scheduling, so this
prototype models exactly the slice priorities need — and is explicit about the
boundary.

### What we model

A priority is the element

```
    p = a * omega  +  b  +  c * (1 / omega)
```

where `a`, `b`, `c` are **dyadic rationals** (`src/dyadic.rs`). This is a real,
honest sub-structure of the surreals: the lexicographically ordered group of
Hahn series supported on the omega-powers `{ omega^1, omega^0, omega^-1 }`.
Ordering "most significant order first" reproduces the surreal order exactly on
this subset:

```
    ... 1/omega < any positive dyadic < ... < omega < omega + 1 < 2*omega ...
```

- **Dyadics** (`Dyadic`): stored canonically as `num / 2^den_pow` with all
  common factors of two removed, so equal values compare equal. Cross-multiplied
  comparison and dyadic addition/negation are exact (no floating point in the
  ordering path). `to_f64` exists only for display.
- **Priorities** (`Priority`): the three dyadic coefficients above. Comparison
  is lexicographic on `(a, b, c)`; addition and negation are component-wise. The
  subgroup is closed under both, and the ordering is a genuine total order (the
  tests check antisymmetry across a mixed sample).
- A tagged builder enum `Term { Finite, Omega{scale}, InvOmega{scale} }` lets you
  assemble linear combinations such as `2*omega + 3 + 1/omega` via
  `Priority::from_terms(&[...])`.

### What we deliberately leave out

- Surreal **multiplication** (only the additive group is implemented — enough to
  order and combine priorities).
- Higher powers of omega (`omega^2`, `sqrt(omega)`, `omega/2`-style exponents)
  and general transfinite birthdays.
- The raw `{ L | R }` set machinery. We use the equivalent
  coefficient/Hahn-series representation, which is faithful for this subset.

Arithmetic uses `i128` numerators; extreme coefficients could overflow. That is
fine for a prototype and well outside any realistic priority range.

---

## Project layout

```
surreal-priority/
├── Cargo.toml
├── README.md
└── src/
    ├── lib.rs         # module wiring, #![forbid(unsafe_code)]
    ├── dyadic.rs      # dyadic rationals n / 2^k (the coefficient ring)
    ├── surreal.rs     # Priority = a*omega + b + c/omega, ordering + arithmetic
    ├── scheduler.rs   # deterministic, OS-free scheduler simulation
    └── main.rs        # demo: ordering table + scheduler run
```

No third-party dependencies. No `unsafe` (`#![forbid(unsafe_code)]`).

---

## How to run

Requires a Rust toolchain (`cargo`). Developed and verified with Rust 1.94.

```bash
cd surreal-priority

# Run the unit tests (surreal ordering + scheduler behaviour): 16 tests.
cargo test

# Run the demo (ordering table + scheduler simulation).
cargo run
```

### Sample output (`cargo run`)

```text
== Surreal priority ordering ==
ascending priorities:
  1/omega    = 1/w
  1/2        = 1/2
  1          = 1
  3          = 3
  omega + 1  = 1w + 1
  2*omega    = 2w
checks:
  1/omega < 1      : true
  1      < omega   : true
  omega  < 2*omega : true
  omega  > 1000000 : true

== Scheduler simulation ==
tasks (priority, work, quantum):
  render[omega]    prio=1w work=4 quantum=1
  ui[3]            prio=3 work=3 quantum=1
  sync[1]          prio=1 work=2 quantum=1
  gc[1/omega]      prio=1/w work=2 quantum=1

schedule:
  tick  task              prio      ran  remaining
     0  render[omega]     1w          1          3
     1  render[omega]     1w          1          2
     2  render[omega]     1w          1          1
     3  render[omega]     1w          1          0
     4  ui[3]             3           1          2
     5  ui[3]             3           1          1
     6  ui[3]             3           1          0
     7  sync[1]           1           1          1
     8  sync[1]           1           1          0
     9  gc[1/omega]       1/w         1          1
    10  gc[1/omega]       1/w         1          0

observations:
  - render[omega] runs ticks 0..3 back-to-back: an infinite
    priority starves every finite task until it is done.
  - gc[1/omega] runs last: an infinitesimal priority only gets
    the CPU once nothing else is runnable.
```

Note the display convention: `w` is printed for `omega`, so `1w` means `omega`,
`2w` means `2*omega`, and `1/w` means `1/omega`.

### Sample output (`cargo test`)

```text
running 16 tests
test dyadic::tests::addition_and_subtraction ... ok
test dyadic::tests::normalization_removes_factors_of_two ... ok
test dyadic::tests::ordering ... ok
test scheduler::tests::all_work_completes ... ok
test scheduler::tests::inv_omega_task_runs_last ... ok
test scheduler::tests::omega_task_starves_finite_tasks_until_done ... ok
test scheduler::tests::run_terminates_at_cap ... ok
test surreal::tests::addition_is_componentwise_and_commutative ... ok
test surreal::tests::canonical_ordering_of_omega_one_and_inv_omega ... ok
test surreal::tests::equality_ignores_construction_order ... ok
test surreal::tests::infinite_dominates_all_finites ... ok
test surreal::tests::infinitesimal_below_every_positive_finite ... ok
test surreal::tests::linear_combinations_order_lexicographically ... ok
test surreal::tests::negation_cancels ... ok
test surreal::tests::total_order_is_antisymmetric ... ok
test surreal::tests::two_omega_beats_omega ... ok

test result: ok. 16 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out
```

---

## How the scheduler uses the ordering

`Scheduler::step` picks the runnable task with the greatest surreal priority
(ties broken deterministically by original task order), runs it for one quantum,
and records the decision immutably in a schedule log. Because `omega` dominates
all finite priorities and `1/omega` is dominated by all positive finite
priorities, the surreal ordering directly produces strict-priority scheduling
with an infinite "must run first" band and an infinitesimal "idle only" band —
without any special-case code in the scheduler itself.
