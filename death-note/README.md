# Death Note — a SAFE, sandboxed process reaper

A tiny Rust prototype that re-imagines the *Death Note* as a `/dev/deathnote`-style
CLI. You "write a name" into the note, and after a delay the named target dies —
optionally of a specific cause.

The twist that keeps it harmless: **the only things this tool can ever kill are the
throwaway `sleep` processes it spawned itself.** You never write a PID. You write a
*name* — a label you assigned to one of *its own* sandbox processes.

---

## ⚠️ SAFETY — read this first

This is a **sandbox toy**, not a system process killer. The safety model is
enforced in code (`src/safety.rs`), not just documented:

- **It only ever reaps processes it spawned.** `spawn` launches harmless `sleep`
  processes, records their PID + a start-time "signature" + an ownership marker in
  a session registry. Nothing else is ever a valid target.
- **You never target a raw PID.** The Death Note is written with a *name*. Names
  are validated as labels (`[A-Za-z0-9_-]`); a bare number is rejected with a loud
  "names are LABELS, not PIDs" error.
- **Every reap re-verifies ownership** before a single signal is sent. The target
  must (1) be in our registry, (2) still be alive, (3) be owned by *our* uid,
  (4) still look like our sandbox `sleep`, and (5) have the **same start signature**
  we recorded at spawn time. The start-signature check defeats **PID reuse**: if the
  OS recycled the PID into some other program, verification fails and **no signal is
  sent**.
- **It refuses to run as root** (uid 0). Any command aborts immediately.
- **No privileges, no magic.** No `unsafe`, no kernel modules, no eBPF, no ptrace.
  Signals are delivered with the ordinary `kill(1)` command, restricted to PIDs that
  passed every check above. Liveness is probed with `kill -0` (which sends **no**
  signal).
- **By design there is no code path** that can signal a process this tool did not
  create. If verification fails, the entry is voided and the target is left alone.

If you point the registry at a process you don't own (e.g. `launchd`, PID 1), the
reaper **refuses** and voids the entry — verified in the test below.

---

## Death Note rules (faithfully enforced, scaled for a quick demo)

1. **Writing a name kills the target after a delay.** Canon is "40 seconds"; here it
   defaults to a few seconds (`DEATHNOTE_DELAY`, default `4`) so the demo finishes fast.
2. **Cause of death.** If a specific cause is written within a short window it is
   applied; otherwise the target dies of the default **heart attack** (SIGTERM).
   Causes map to signals:
   - `heart_attack` → SIGTERM (default)
   - `accident` / `sigkill` → SIGKILL
   - `coma` / `sigstop` → SIGSTOP (paused, then finished during cleanup)
   - `oom` → SIGKILL, **simulated** (it never actually exhausts memory — clearly labelled)
3. **A misspelled name has no effect.** A name that doesn't match a registered owned
   process does nothing; after a few attempts (`MAX_MISSPELLINGS = 3`) that name is
   **permanently void**.
4. **A name cannot be killed twice.** Once a name is condemned or reaped, re-entries
   are void.

---

## Requirements

- Rust + Cargo (built with 1.94).
- A Unix system with the standard `sleep`, `ps`, `kill`, `id` utilities (macOS/Linux).
- No network access and no external crates — fully self-contained.

## Build & run

```bash
cd death-note
cargo build

# The full scripted demonstration (recommended first run):
DEATHNOTE_DELAY=3 cargo run -- demo

# Print the enforced rules / help:
cargo run -- rules
cargo run -- help
```

### Interactive use (state persists across invocations)

```bash
export DEATHNOTE_DELAY=2            # scale the "40 seconds" down for the demo
cargo run -- spawn Light            # spawn an owned sandbox 'sleep', label it "Light"
cargo run -- spawn L
cargo run -- write Light --cause coma   # SIGSTOP after the delay
cargo run -- write L                    # default heart attack (SIGTERM)
cargo run -- write Light                # duplicate -> VOID (can't kill twice)
cargo run -- write Ryuk                 # unregistered -> NO EFFECT (misspelling)
cargo run -- list
cargo run -- watch                      # reaper enforces the schedule
cargo run -- cleanup                    # terminate any survivors (only our own)
```

### Environment knobs

| Variable           | Default              | Meaning                                        |
|--------------------|----------------------|------------------------------------------------|
| `DEATHNOTE_DELAY`  | `4`                  | Seconds from writing a name to death (canon 40)|
| `DEATHNOTE_WINDOW` | = `DEATHNOTE_DELAY`  | Seconds a specific cause may still be written  |
| `DEATHNOTE_LIFE`   | `300`                | Seconds a spawned `sleep` lives if un-noted    |
| `DEATHNOTE_HOME`   | `./.deathnote_session` | Session registry + ledger directory          |

---

## Sample output

```
$ DEATHNOTE_DELAY=3 cargo run -- demo

┌────────────────────────────────────────────────────────────┐
│  DEATH NOTE — SAFE SANDBOX PROCESS REAPER                   │
│  Reaps ONLY the harmless `sleep` processes it spawned.      │
│  Never targets arbitrary PIDs. Never runs as root.         │
└────────────────────────────────────────────────────────────┘

== Spawning owned sandbox processes (harmless `sleep`) ==
  spawned 'Alpha' -> pid 52337 (owned, tracked)
  spawned 'Bravo' -> pid 52355 (owned, tracked)
  spawned 'Charlie' -> pid 52375 (owned, tracked)

== Writing Death Note entries ==
  'Alpha (valid, default heart attack)' -> CONDEMNED pid=52337 cause='heart_attack'
  'Bravo (valid, cause=accident/SIGKILL)' -> CONDEMNED pid=52355 cause='accident'
  'Nobody (misspelling, unregistered)' -> NO EFFECT (misspelling #1)
  'Nobody (misspelling, unregistered)' -> NO EFFECT (misspelling #2)
  'Nobody (misspelling, unregistered)' -> NO EFFECT (permanently void after 3 misspellings)
  'Nobody (misspelling, unregistered)' -> NO EFFECT (permanently void after 3 misspellings)
  'Alpha again (duplicate)' -> VOID (a name cannot be killed twice)
  (Charlie deliberately left un-noted — it should survive)

== Watching the reaper (valid entries die on schedule) ==
  REAPED 'Alpha' (pid 52337) via heart attack (SIGTERM)
  REAPED 'Bravo' (pid 52355) via accident (SIGKILL)

== Final state ==
  Alpha    pid=52337   state=Reaped     alive=false
  Bravo    pid=52355   state=Reaped     alive=false
  Charlie  pid=52375   state=Alive      alive=true

== Cleanup (only our own verified processes) ==
  cleanup: terminated owned 'Charlie'

All owned sandbox processes accounted for. Nothing stray left behind.
```

### Safety refusal (verified)

Point an entry at PID 1 (`launchd`, owned by root) and the reaper refuses — no
signal is ever sent:

```
reaper tick against pid 1 (must REFUSE with uid reason, no signal):
REFUSED to reap 'Victim' (pid 1): pid 1 is owned by uid 0, not us (501) — REFUSING — entry voided

--- confirm launchd pid 1 still running (untouched) ---
/sbin/launchd
```

And a raw PID passed as a name is rejected outright:

```
$ cargo run -- write 12345
error: names are LABELS, not PIDs. This tool never targets a raw PID (safety).
```

---

## Project layout

```
death-note/
├── Cargo.toml
├── README.md
└── src/
    ├── main.rs        CLI dispatch (spawn/write/cause/list/watch/reap/cleanup/demo/rules)
    ├── safety.rs      SAFETY CORE — ensure_not_root + verify_owned (the reap gate)
    ├── proccheck.rs   Read-only process inspection (kill -0, ps) — never destructive
    ├── signals.rs     Cause -> POSIX signal mapping + kill sender
    ├── registry.rs    Session persistence (owned processes + misspelling counters + ledger)
    ├── ops.rs         High-level operations: spawn, write, set_cause, tick, cleanup
    ├── config.rs      Env-driven, scaled-down timings
    ├── clock.rs       Epoch-second helper
    └── demo.rs        Scripted end-to-end demonstration
```

## License

MIT. Educational sandbox prototype — not intended to manage real workloads.
