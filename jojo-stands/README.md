![JoJo Stands](./banner.png)

# JoJo Stand System

*A tick-based, pure in-memory simulation of an OS-style scheduler whose "processes" can be granted **Stand abilities** from* JoJo's Bizarre Adventure.

Every Stand is a real operation — but it operates on a **simulated** process table that lives entirely inside one `HashMap`, not on your computer.

---

## TL;DR

- A single-binary Rust program that models a toy cooperative scheduler.
- "Processes" are plain structs (`SimProcess`) in a `HashMap`; the engine advances in discrete **ticks**, completing one queued task per process per tick.
- Four *JoJo* Stands map to concrete, honest operations on that table: **The World** (freeze others), **Killer Queen** (prime + detonate), **King Crimson** (snapshot rollback), **Sticky Fingers** (move to another lane).
- **Zero external dependencies.** `std`-only. `#![forbid(unsafe_code)]` crate-wide.
- Ships with a narrated demo (`cargo run`) and 9 integration tests (`cargo test`).

---

## Safety (read this first)

**This program is a pure, in-memory simulation. It cannot touch, inspect, or harm anything on your system.**

The name talks about "processes," "signals," and "killing" — but every one of those is a data-structure operation. Concretely, based on the actual source:

- **No real processes or threads.** Nothing calls `fork`, `exec`, `spawn`, `std::thread`, or `std::process`. There is no concurrency at all — the whole simulation runs on one thread, synchronously. Grep the tree: the only occurrences of the word `spawn` are the scheduler's own `Scheduler::spawn`, which does `HashMap::insert` on an in-memory struct.
- **No OS PIDs.** A "PID" here is a `u64` counter (`next_pid`) that the scheduler hands out to its own structs. It never corresponds to a real operating-system process id, and the program never reads or targets any PID it did not itself mint.
- **No signals to the kernel.** `send_signal(pid, "SIGUSR1")` routes a `&str` label through the simulation. It is compared against a boolean flag on a simulated struct. Nothing is ever delivered to the OS.
- **"Terminate" / "detonate" == `HashMap::remove`.** The worst thing that can happen to a "process" is that its struct is dropped from the map. That is the entire blast radius.
- **Opt-in, self-contained sandbox.** The engine only ever mutates its own `processes` map, which it populated itself. It cannot reference, signal, freeze, kill, move, or even *see* anything outside that map — there is no code path that reaches out to the host.
- **No kernel modules, no privilege escalation, no `unsafe`.** `#![forbid(unsafe_code)]` is declared in `lib.rs`, so the compiler rejects any `unsafe` block anywhere in the crate.
- **No I/O beyond stdout.** No network, no filesystem writes, no environment reads. The demo's only side effect is `println!`.

The "processes" scheduled here are fictional actors named after *JoJo* characters. The only things being frozen, detonated, rewound, or zipped are structs this program allocated a few microseconds earlier.

---

## The idea

In *JoJo's Bizarre Adventure* (Part 3 onward), a **Stand** is a persona-bound spirit: a manifestation of a character's fighting will that stands beside them and acts on their behalf. Each Stand has one signature power — Star Platinum / The World stops time, Killer Queen turns anything it touches into a bomb, King Crimson erases a slice of time, Sticky Fingers opens zippers in space to move things around.

This project takes that "a named agent that carries out one specialized ability for its user" framing and maps it onto an OS-scheduler metaphor: each simulated process is a "user," and binding a Stand to it grants that process one special operation it can invoke against the shared process table.

---

## The honest core — what really happens

Strip away the flavour and this is a small **cooperative, tick-based scheduler simulator**:

1. A `Scheduler` owns a `HashMap<u64, SimProcess>` plus a stable scheduling `order: Vec<u64>`.
2. Each `SimProcess` holds a work queue (`VecDeque<Task>`), a `work_done` counter, a `frozen_ticks` counter, a `primed` flag, and an optional bound `Stand`.
3. Calling `tick()` walks the processes in order; each alive, non-frozen process pops and "completes" one task. Frozen processes decrement their freeze counter instead.
4. After every tick the engine clones the whole table into a bounded **snapshot ring buffer** (`history`), so a rollback is possible.
5. Stand abilities are ordinary methods on `Scheduler` that mutate that table.

### What is real vs. simulated vs. theatrical

| Layer | Example | Reality |
|-------|---------|---------|
| **Real** | The scheduling logic, tick loop, snapshot ring buffer, lane moves, error handling, tests | Genuine, working Rust data-structure code. The algorithms below actually run. |
| **Simulated** | "processes," "PIDs," "signals," "termination" | Modeled as in-memory structs / `u64`s / `&str`s / `HashMap::remove`. They resemble OS concepts but never leave the program. |
| **Theatrical** | "toki wo tomare!", "BOOM. Killer Queen detonates it.", character names, `.user()` / `.ability()` flavour strings | Pure narration for the log. Zero behavioral effect. |

So: the *scheduler* is real, the *operating-system framing* is a simulation, and the *JoJo dialogue* is set dressing.

Ability-to-operation mapping:

| Stand | Canonical user | Simulated operation |
|-------|----------------|---------------------|
| **The World** / Star Platinum | DIO / Jotaro | Set `frozen_ticks = N` on every *other* alive process; the caster keeps advancing while they stall for N ticks. |
| **Killer Queen** | Kira Yoshikage | Set `primed = true` on a target; the next `send_signal` to a primed process does `HashMap::remove` (detonation). An unprimed signal is a no-op. |
| **King Crimson** | Diavolo | Restore the snapshot taken `ticks_back` ticks ago and reset the tick counter; snapshots in the now-erased future are discarded. |
| **Sticky Fingers** | Bruno Bucciarati | Change a process's `lane` field; its `VecDeque` work queue travels with it. |

A small `Command` enum (`Spawn`, `AssignStand`, `Tick`, `TheWorld`, `KillerQueenMark`, `Signal`, `KingCrimsonErase`, `StickyFingersZip`) is a decoupled instruction layer so the demo — or any future REPL — drives the engine as plain data without touching its internals.

---

## How it works — module map, types, and algorithms

### Crate layout

The crate builds **both** a library (`jojo_stands`) and a binary (`jojo-stands`) from the same source tree.

| File | Role | Key items |
|------|------|-----------|
| `src/lib.rs` | Crate root: safety doc-comment, `#![forbid(unsafe_code)]`, module declarations and re-exports | re-exports `Command`, `ProcState`, `SimProcess`, `Task`, `Scheduler`, `Stand` |
| `src/process.rs` | The simulated process type and its lifecycle | `SimProcess`, `ProcState` (`Ready`/`Running`/`Idle`/`Frozen`/`Terminated`), `Task`, `SimProcess::step` |
| `src/stand.rs` | The Stand ability enum + flavour text | `Stand` (`TheWorld`/`KillerQueen`/`KingCrimson`/`StickyFingers`), `.user()`, `.ability()`, `Display` |
| `src/scheduler.rs` | The tick engine, snapshot history, and all Stand implementations | `Scheduler`, private `Snapshot`, `tick`, `snapshot`, `the_world`, `killer_queen_mark`, `send_signal`, `king_crimson_erase`, `sticky_fingers_zip`, `require_stand`, `table` |
| `src/command.rs` | Data-driven command interface over the engine | `Command` enum, `Command::apply`, `log_err` |
| `src/main.rs` | Narrated 6-phase demo runner | `main`, `banner`, `drain_log` |
| `tests/simulation.rs` | 9 integration tests exercising the public API | see [Testing](#testing) |

### Key types

- **`SimProcess`** — one simulated process: `pid: u64`, `name`, `lane`, `state: ProcState`, `queue: VecDeque<Task>`, `frozen_ticks: u32`, `work_done: u32`, `stand: Option<Stand>`, `primed: bool`. `step()` pops one task, bumps `work_done`, and updates `state` to `Running` or `Idle`.
- **`ProcState`** — an explicit lifecycle enum, matched exhaustively (state-machine pattern; no wildcard fall-through).
- **`Scheduler`** — owns the `processes` map, the `order` vector, the `history` ring, `max_history`, a monotonic `tick` counter, `next_pid`, and a human-readable `log: Vec<String>`.
- **`Snapshot`** (private) — an immutable `{ tick, processes: HashMap<..>, order }` copy of the whole table, taken at each tick boundary.
- **`Command`** — plain-data instruction; `apply` returns `Some(pid)` for `Spawn`, else `None`, and folds engine errors into the log instead of panicking.

### Algorithms worth calling out

- **Tick loop (`Scheduler::tick`)** — increments the tick, iterates a *clone* of `order` (so the map can be mutated mid-loop), skips terminated processes, decrements freeze counters for frozen ones, and calls `step()` on the rest. Then it takes a snapshot.
- **Snapshot ring buffer (`snapshot`)** — pushes a full clone onto `history` and pops from the front once it exceeds `max_history`. This bounds memory and defines King Crimson's reachable rollback window.
- **King Crimson rollback (`king_crimson_erase`)** — computes `target_tick = tick - ticks_back` with a checked subtraction (rejects erasing past `t0`), finds that snapshot by tick number (errors cleanly if it has aged out of the window), swaps the map/order/tick back, and trims any snapshots now in the "erased future." This is effectively a time-travel undo bounded by history depth.
- **Capability check (`require_stand`)** — every ability first verifies the caster exists *and* is wielding the matching Stand, returning a descriptive `Result::Err` otherwise. This is the guard that makes "wrong Stand" and "no such pid" safe, testable failures rather than panics.

**Immutability & safety notes:** the crate is `unsafe`-free by construction (`#![forbid(unsafe_code)]`), errors are surfaced as `Result<(), String>` and logged rather than `panic!`'d in the command layer, and rollback is implemented by restoring an immutable snapshot rather than mutating history in place.

---

## Install & run

Requires a standard Rust toolchain (built and tested with **cargo 1.94**). No other setup — there are no dependencies to fetch.

```bash
# From anywhere, using --manifest-path (or cd into the project first):
cargo build --manifest-path jojo-stands/Cargo.toml     # compile
cargo run   --manifest-path jojo-stands/Cargo.toml     # run the narrated demo
cargo test  --manifest-path jojo-stands/Cargo.toml     # run the 9 integration tests
```

> **CLI note:** the binary takes **no arguments and no subcommands** — `main.rs` runs one fixed, scripted 6-phase demo. Passing flags such as `-- --help` is accepted but ignored; you still get the demo. To script your own scenarios, use the library API (`Scheduler` + `Command`) as the tests do.

### `cargo build` (clean)

```text
   Compiling jojo-stands v0.1.0 (/Users/arhansubasi/mad-man-projects/jojo-stands)
    Finished `dev` profile [unoptimized + debuginfo] target(s) in 0.40s
```

### `cargo test`

```text
    Finished `test` profile [unoptimized + debuginfo] target(s) in 0.00s
     Running unittests src/lib.rs

running 0 tests
test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

     Running unittests src/main.rs

running 0 tests
test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

     Running tests/simulation.rs

running 9 tests
test command_interface_drives_engine ... ok
test killer_queen_detonates_on_signal ... ok
test king_crimson_outside_window_errors ... ok
test sticky_fingers_moves_process_and_queue ... ok
test normal_tick_advances_all_processes ... ok
test unprimed_signal_is_harmless ... ok
test king_crimson_rolls_back_state ... ok
test the_world_freezes_others_but_not_caster ... ok
test wrong_stand_is_rejected ... ok

test result: ok. 9 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s

   Doc-tests jojo_stands

running 0 tests
test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
```

### `cargo run` — the narrated demo

The demo builds a 4-process table (`jotaro`, `josuke`, `giorno`, `koichi`), binds one Stand to each, and walks through six phases. Things to watch:

- **Phase 2** — after The World, only `jotaro`'s `work_done` grows while the others show `FROZEN (no advance)`.
- **Phase 3** — a signal detonates the primed `giorno`, removing it from the table.
- **Phase 5** — King Crimson rolls back 2 ticks: `jotaro`'s `work_done` drops `5 -> 4`, the tick counter returns to `t4`, and — because the restored snapshot predates the detonation — `giorno` reappears.
- **Phase 6** — Sticky Fingers zips `jotaro` (and its remaining queued task) from lane `main` to `isolated`.

Captured verbatim:

```text
============================================================
  JoJo Stand System — in-memory process simulation
============================================================
Nothing here touches your OS. Every 'process' is a struct in a HashMap.
[t0] spawn  pid=1 "jotaro" in lane 'main'
[t0] spawn  pid=2 "josuke" in lane 'main'
[t0] spawn  pid=3 "giorno" in lane 'main'
[t0] spawn  pid=4 "koichi" in lane 'workers'
[t0] stand  pid=1 "jotaro" <= The World (time stop) — user: DIO / Jotaro
[t0] stand  pid=2 "josuke" <= Killer Queen (touch to detonate) — user: Kira Yoshikage
[t0] stand  pid=3 "giorno" <= King Crimson (erase time) — user: Diavolo
[t0] stand  pid=4 "koichi" <= Sticky Fingers (zip) — user: Bruno Bucciarati

Initial table:
  PID  STATE  FROZEN  LANE          WORK  QUEUE  STAND
  1    READY  0       main          0     5      The World
  2    READY  0       main          0     4      Killer Queen
  3    READY  0       main          0     4      King Crimson
  4    READY  0       workers       0     3      Sticky Fingers


============================================================
  Phase 1: run 2 normal ticks
============================================================
[t1] --- tick begins ---
[t1]   pid=1 "jotaro" ran task 'ora-1' (work_done=1)
[t1]   pid=2 "josuke" ran task 'heal-1' (work_done=1)
[t1]   pid=3 "giorno" ran task 'muda-1' (work_done=1)
[t1]   pid=4 "koichi" ran task 'echoes-1' (work_done=1)
[t2] --- tick begins ---
[t2]   pid=1 "jotaro" ran task 'ora-2' (work_done=2)
[t2]   pid=2 "josuke" ran task 'heal-2' (work_done=2)
[t2]   pid=3 "giorno" ran task 'muda-2' (work_done=2)
[t2]   pid=4 "koichi" ran task 'echoes-2' (work_done=2)

Table after t2:
  PID  STATE  FROZEN  LANE          WORK  QUEUE  STAND
  1    RUN    0       main          2     3      The World
  2    RUN    0       main          2     2      Killer Queen
  3    RUN    0       main          2     2      King Crimson
  4    RUN    0       workers       2     1      Sticky Fingers


============================================================
  Phase 2: jotaro casts THE WORLD (freeze others for 2 ticks)
============================================================
[t2] ABILITY "jotaro" (pid=1) casts THE WORLD — toki wo tomare! Freezing others for 2 tick(s).
[t3] --- tick begins ---
[t3]   pid=1 "jotaro" ran task 'ora-3' (work_done=3)
[t3]   pid=2 "josuke" FROZEN (no advance, 1 tick(s) left)
[t3]   pid=3 "giorno" FROZEN (no advance, 1 tick(s) left)
[t3]   pid=4 "koichi" FROZEN (no advance, 1 tick(s) left)
[t4] --- tick begins ---
[t4]   pid=1 "jotaro" ran task 'ora-4' (work_done=4)
[t4]   pid=2 "josuke" FROZEN (no advance, 0 tick(s) left)
[t4]   pid=3 "giorno" FROZEN (no advance, 0 tick(s) left)
[t4]   pid=4 "koichi" FROZEN (no advance, 0 tick(s) left)

Table after time-stop (note only jotaro's work_done grew):
  PID  STATE  FROZEN  LANE          WORK  QUEUE  STAND
  1    RUN    0       main          4     1      The World
  2    READY  0       main          2     2      Killer Queen
  3    READY  0       main          2     2      King Crimson
  4    READY  0       workers       2     1      Sticky Fingers


============================================================
  Phase 3: josuke's Killer Queen primes giorno, then a signal detonates it
============================================================
[t4] ABILITY Killer Queen (pid=2) touches pid=3 "giorno" — primed. Next signal detonates it.
[t4] SIGNAL 'SIGUSR1' -> pid=3 "giorno": BOOM. Killer Queen detonates it. Removed from sim table.

Table after detonation (giorno removed from sim table):
  PID  STATE  FROZEN  LANE          WORK  QUEUE  STAND
  1    RUN    0       main          4     1      The World
  2    READY  0       main          2     2      Killer Queen
  4    READY  0       workers       2     1      Sticky Fingers


============================================================
  Phase 4: run 2 ticks, then Giorno... wait, Giorno is gone — koichi is our survivor
============================================================
[t5] --- tick begins ---
[t5]   pid=1 "jotaro" ran task 'ora-5' (work_done=5)
[t5]   pid=2 "josuke" ran task 'heal-3' (work_done=3)
[t5]   pid=4 "koichi" ran task 'echoes-3' (work_done=3)
[t6] --- tick begins ---
[t6]   pid=1 "jotaro" idle (empty queue)
[t6]   pid=2 "josuke" ran task 'heal-4' (work_done=4)
[t6]   pid=4 "koichi" idle (empty queue)

Table BEFORE King Crimson (jotaro work_done=5, tick=t6):
  PID  STATE  FROZEN  LANE          WORK  QUEUE  STAND
  1    IDLE   0       main          5     0      The World
  2    IDLE   0       main          4     0      Killer Queen
  4    IDLE   0       workers       3     0      Sticky Fingers


============================================================
  Phase 5: KING CRIMSON — erase the last 2 ticks (rollback)
============================================================
[t6] stand  pid=1 "jotaro" <= King Crimson (erase time) — user: Diavolo
[t6] ABILITY King Crimson (pid=1) ERASES TIME: rolled back 2 tick(s) to t4. State restored.

Table AFTER King Crimson (jotaro work_done rolled 5 -> 4, tick=t4):
  PID  STATE  FROZEN  LANE          WORK  QUEUE  STAND
  1    RUN    0       main          4     1      The World
  2    READY  0       main          2     2      Killer Queen
  3    READY  0       main          2     2      King Crimson
  4    READY  0       workers       2     1      Sticky Fingers


============================================================
  Phase 6: koichi's Sticky Fingers ZIPS jotaro from 'main' to 'isolated'
============================================================
[t4] ABILITY Sticky Fingers (pid=4) ZIPS pid=1 "jotaro" (+1 queued tasks) from lane 'main' -> 'isolated'.

Final table:
  PID  STATE  FROZEN  LANE          WORK  QUEUE  STAND
  1    RUN    0       isolated      4     1      The World
  2    READY  0       main          2     2      Killer Queen
  3    READY  0       main          2     2      King Crimson
  4    READY  0       workers       2     1      Sticky Fingers


============================================================
  Simulation complete — no real processes were harmed
============================================================
```

### Driving it yourself (library API)

There is no interactive CLI, but the engine is a library. A minimal scenario:

```rust
use jojo_stands::{Command, Scheduler, Stand};

let mut sched = Scheduler::new(8); // remember up to 8 ticks of history

let dio = Command::Spawn {
    name: "dio".into(),
    lane: "main".into(),
    tasks: vec!["za-warudo".into(), "road-roller".into()],
}
.apply(&mut sched)
.unwrap();

Command::AssignStand { pid: dio, stand: Stand::TheWorld }.apply(&mut sched);
Command::TheWorld { caster: dio, ticks: 2 }.apply(&mut sched);
Command::Tick { n: 2 }.apply(&mut sched);

print!("{}", sched.table());
```

---

## Testing

`tests/simulation.rs` contains **9 integration tests** that exercise the public library API (all in-memory, no OS resources). They verify:

| Test | What it asserts |
|------|-----------------|
| `normal_tick_advances_all_processes` | Each tick advances every ready process by exactly one task; the tick counter increments. |
| `the_world_freezes_others_but_not_caster` | After The World, the caster advances every tick while victims stay at `work_done = 0`; once the freeze expires the victim advances again. |
| `killer_queen_detonates_on_signal` | A primed target is present before the signal and **absent** (removed) after it. |
| `unprimed_signal_is_harmless` | A signal to an unprimed process leaves it in the table untouched. |
| `king_crimson_rolls_back_state` | Rolling back N ticks restores both the tick counter and the exact `work_done` value from that checkpoint. |
| `king_crimson_outside_window_errors` | Asking to erase further back than `max_history` allows returns `Err`, not a panic or bad state. |
| `sticky_fingers_moves_process_and_queue` | The target's `lane` changes and its queue length is preserved (the queue travels with it). |
| `wrong_stand_is_rejected` | Invoking an ability the caster doesn't wield returns `Err` (the `require_stand` capability guard). |
| `command_interface_drives_engine` | `Command::Spawn`/`AssignStand`/`Tick` compose correctly and the bound Stand is recorded. |

There are currently no `#[cfg(test)]` unit tests, doc tests, or benchmarks — the 9 integration tests are the full suite, and all pass (see captured output above).

---

## Limitations & honest caveats

- **It is a simulation, full stop.** Despite the OS vocabulary, it never spawns, signals, schedules, or observes any real process or thread. Do not expect it to interact with your machine.
- **No interactive interface.** The binary runs one hard-coded scripted demo; there is no argument parsing, REPL, or config. Custom scenarios require using the library API in Rust.
- **Cooperative, single-threaded, one-task-per-tick.** There is no preemption, priority, time-slicing, fairness, or concurrency. Scheduling order is simply insertion order (`order: Vec<u64>`).
- **Bounded, coarse "time travel."** King Crimson can only reach ticks still in the `max_history` ring, and rollback granularity is one whole tick. Snapshots are full clones of the table (`HashMap` + `Vec`), which is simple but O(n) in memory per tick.
- **Errors are stringly-typed.** Abilities return `Result<(), String>`; there is no structured error enum. Good enough for a demo, not what you'd ship in a library that needs programmatic error handling.
- **PIDs are never reused.** `next_pid` only increments; terminated slots are not recycled.
- **`ProcState::Terminated` is essentially transient** — termination immediately removes the struct from the map, so the state variant exists mainly for clarity.

---

## References / attribution

- **Concept & Stand names:** *JoJo's Bizarre Adventure* by Hirohiko Araki. The World / Star Platinum, Killer Queen, King Crimson, and Sticky Fingers — and their users DIO/Jotaro, Kira Yoshikage, Diavolo, and Bruno Bucciarati — are the creations and trademarks of their respective rights holders. This project is an unaffiliated, fan-made programming exercise and uses only text references (no copyrighted artwork).
- **License:** MIT (see `Cargo.toml`).
- **Dependencies:** none — `std`-only Rust, Rust 2021 edition.
