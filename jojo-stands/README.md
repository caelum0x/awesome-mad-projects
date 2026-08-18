# JoJo Stand System

A tick-based **simulation** of an OS-style scheduler whose in-memory "processes"
can be granted **Stand abilities** from *JoJo's Bizarre Adventure*. Each Stand is
implemented as a real operation on the **simulated** process table — not on your
computer.

```
 The World      time stop          — freeze every other sim process for N ticks
 Killer Queen   touch to detonate  — prime a target; next signal removes it
 King Crimson   erase time         — roll the whole sim table back X ticks
 Sticky Fingers zip                — move a process (and its queue) to a new lane
```

## Concept

Every "process" is a plain Rust struct (`SimProcess`) — a PID, a name, a lane /
namespace, a work queue, a frozen counter, a work-done counter, and an optional
bound Stand — living inside a `Scheduler`'s `HashMap`. The engine advances in
discrete **ticks**. On each tick every alive, non-frozen process completes one
queued task. After each tick the engine snapshots the entire table into a bounded
history ring so that King Crimson can "erase time".

Abilities map to concrete table operations:

| Stand | Sim operation |
|-------|---------------|
| The World / Star Platinum | Set `frozen_ticks = N` on every *other* process; the caster keeps advancing while they stall. |
| Killer Queen | Set `primed = true` on a target; the next `send_signal` to a primed process does `HashMap::remove` (detonation). |
| King Crimson | Restore the snapshot taken X ticks ago and reset the tick counter. |
| Sticky Fingers | Change a process's `lane` field; its `VecDeque` work queue travels with it. |

A tiny `Command` enum provides a decoupled command interface (`Spawn`,
`AssignStand`, `Tick`, `TheWorld`, `KillerQueenMark`, `Signal`,
`KingCrimsonErase`, `StickyFingersZip`) so the demo — or any future REPL — drives
the engine without touching its internals.

## SAFETY

**This program is a pure, in-memory simulation. It cannot harm your system.**

- It does **not** touch real OS processes. There are no real threads, no real
  PIDs, no `fork`/`exec`, and no OS-level scheduling.
- "Signals" are just `&str` labels routed through the simulation. Nothing is ever
  sent to the kernel or to any real process.
- "Terminate" / "detonate" means removing a struct from an in-memory `HashMap`.
  The worst possible outcome is that a simulated value is dropped.
- It targets **only** its own simulated process table. It never references,
  inspects, signals, kills, or stops any process it did not create inside the
  sim.
- No kernel modules, no privilege escalation, no network, no filesystem writes.
- `#![forbid(unsafe_code)]` is set crate-wide; there is zero `unsafe`.
- Zero external dependencies — std-only Rust.

The "processes" scheduled here are fictional actors named after JoJo characters.
The only thing being stopped, detonated, rewound, or zipped is data structures
that this program itself allocated.

## Project layout

```
jojo-stands/
├── Cargo.toml
├── src/
│   ├── lib.rs         # crate root, safety notes, re-exports (#![forbid(unsafe_code)])
│   ├── process.rs     # SimProcess, ProcState, Task
│   ├── stand.rs       # Stand enum + flavour
│   ├── scheduler.rs   # tick engine, snapshots, Stand ability implementations
│   ├── command.rs     # Command enum + apply()
│   └── main.rs        # demo runner
└── tests/
    └── simulation.rs  # 9 integration tests
```

## Run it

```bash
cd jojo-stands
cargo run          # run the narrated demo
cargo test         # run the 9 integration tests
cargo build        # just compile
cargo clippy       # lint (clean)
```

Requires a standard Rust toolchain (built and tested with cargo 1.94).

## Sample output (tick-by-tick log)

Running `cargo run` produces the trace below. Watch:
- **Phase 2** — after The World, only `jotaro`'s `work_done` grows while the
  others show `FROZEN (no advance)`.
- **Phase 3** — a signal detonates the primed `giorno`, removing it from the
  table.
- **Phase 5** — King Crimson rolls back 2 ticks: `jotaro`'s `work_done` drops
  `5 -> 4`, the tick counter returns to `t4`, and — because the snapshot was
  taken at the t4 tick boundary before the detonation — `giorno` is even
  restored.
- **Phase 6** — Sticky Fingers zips `jotaro` (and its remaining queue) from lane
  `main` to `isolated`.

```
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
  Phase 4: run 2 ticks (giorno is gone)
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

## Tests

`cargo test` runs 9 integration tests covering normal scheduling, time-stop
freezing (caster keeps running), Killer Queen priming + detonation, harmless
unprimed signals, King Crimson rollback and out-of-window errors, Sticky Fingers
lane moves, wrong-Stand rejection, and the command interface.

## License

MIT — a fan-made programming exercise. JoJo's Bizarre Adventure and its Stands
are trademarks of their respective owners.
