![Death Note](./banner.png)

# Death Note — a SAFE, sandboxed process reaper

> Write a name in the notebook and the named thing dies — except the only things
> this notebook can ever touch are the harmless throwaway processes it spawned
> itself. A playful, deliberately over-theatrical homage to the *Death Note*
> manga/anime, implemented as a tiny dependency-free Rust CLI.

---

## TL;DR

- **What it is:** a single-binary Rust CLI (`deathnote`) that spawns harmless
  `sleep` processes, lets you "write their name into the note," and then reaps
  them on a timer with a chosen "cause of death."
- **What it really is under the hood:** a small **userspace process supervisor /
  killer** that operates *only* on an opt-in sandbox of processes it launched
  itself, re-verifying ownership before it sends a single signal.
- **Zero dependencies:** standard library only, plus the ordinary Unix
  utilities (`sleep`, `ps`, `kill`, `id`) that ship with macOS and Linux.
- **Try it in one line:** `DEATHNOTE_DELAY=3 cargo run -- demo`.

---

## ⚠️ SAFETY — read this first

This is a **sandbox toy**, not a system process killer. The safety model is
**enforced in code** (`src/safety.rs`), not merely documented:

- **Userspace only.** Everything happens with ordinary user-level tools. There
  are **no kernel modules, no eBPF, no ptrace, and nothing privileged**. Signals
  are delivered with the standard `kill(1)` command; liveness is probed with
  `kill -0`, which sends **no** signal.
- **Opt-in sandbox of self-spawned processes ONLY.** The only processes this
  tool can ever signal are the `sleep` processes *it itself* launched via
  `spawn`. Each spawn is recorded in a session registry together with its PID, a
  process **start-time signature**, and an ownership token.
- **NO arbitrary PIDs.** You never write a raw PID. The Death Note is written
  with a **name** — a label you assigned to one of *its own* sandbox processes.
  Names are validated as labels (`[A-Za-z0-9_-]`), and a bare number is rejected
  outright with a loud *"names are LABELS, not PIDs"* error.
- **It cannot touch a process it did not create.** Before any signal, every reap
  passes a single gate (`verify_owned`) that requires the target to be
  (1) present in our registry, (2) still alive, (3) owned by *our* uid,
  (4) still shaped like our sandbox `sleep`, and (5) carrying the **same start
  signature** recorded at spawn time. The start-signature check defeats **PID
  reuse**: if the OS recycled the PID into a different program, verification
  fails and **no signal is sent**.
- **It refuses to run as root** (uid 0). Every sub-command aborts immediately if
  invoked with root privileges.
- **Fail-closed by design.** If any check fails, the entry is *voided* and the
  target is left alone. There is no code path that can signal something this tool
  did not spawn — demonstrated in the *Safety refusal* section below, where an
  entry pointed at `launchd` (PID 1) is refused and PID 1 is left untouched.

---

## The idea

In the *Death Note* story, a shinigami's notebook has a simple, terrifying rule:
**a human whose name is written in it will die.** Write only the name and the
victim dies of a heart attack after **40 seconds**; write a specific *cause of
death* within a short window afterward and that cause is applied instead. The
notebook has strict rules — a name must match a real person, a misspelling has no
effect, and the same person cannot be killed twice.

This project turns that fiction into a harmless developer toy. The "notebook" is
a CLI. The "victims" are throwaway `sleep` processes you asked it to create. The
canonical "40 seconds" is scaled down to a few seconds so a demo finishes fast.
None of the mythology is real — but the *rules* are faithfully reproduced, and
the theatrics sit on top of ordinary, auditable process management.

---

## The honest core — what really happens

Strip away the costume and this is a **process supervisor with a timer**:

1. `spawn <name>` starts a real `sleep` process and records it in a small
   tab-separated session file, capturing its PID, start-time signature, and an
   `argv[0]` ownership marker.
2. `write <name>` looks the name up in that registry. A valid, still-alive entry
   is marked **CONDEMNED** with a deadline of `now + delay` and a chosen cause.
3. The reaper (`reap` / `watch` / the `demo` loop) periodically checks for
   condemned entries whose deadline has passed, re-verifies ownership, and then
   sends the mapped POSIX signal via `kill(1)`.

### What is real vs. simulated vs. theatrical

| Element | Category | Reality |
|---|---|---|
| "Dies after 40 seconds" | Theatrical → real timer | A real deadline of `now + DEATHNOTE_DELAY` seconds (default **4**, not 40). |
| "Heart attack" (default cause) | Theatrical label | A real **SIGTERM** delivered by `kill -s TERM`. |
| "Accident" | Theatrical label | A real **SIGKILL** (`kill -s KILL`). |
| "Coma" | Theatrical label | A real **SIGSTOP** (`kill -s STOP`) — pauses, not kills; finished during `cleanup`. |
| "OOM / starvation" | **Simulated** | A **SIGKILL** clearly labelled `SIMULATED` — it never actually exhausts memory. |
| "The notebook knows the victim's face/name" | Real check | Ownership verification: uid + start-signature + registry membership + command match. |
| "A misspelled name has no effect; permanently void after repeats" | Real state machine | Misspelling counter capped at `MAX_MISSPELLINGS = 3`. |
| "A name cannot be killed twice" | Real state machine | Second `write` of a condemned/reaped name returns VOID. |
| The shinigami, the death god, the moral peril | Pure fiction | Nothing here can harm anything but your own `sleep` processes. |

---

## How it works

### Module / crate map

Binary crate (`[[bin]] name = "deathnote"`, `src/main.rs`). No library target.
**No external dependencies** — standard library only.

| File | Responsibility |
|---|---|
| `src/main.rs` | CLI dispatch for `spawn / write / cause / list / watch / reap / cleanup / ledger / demo / rules / help`; `--help` and rules text. |
| `src/safety.rs` | **Safety core.** `ensure_not_root()` and `verify_owned()` — the single gate every reap must pass. Defines the `SANDBOX_TOKEN` marker. |
| `src/proccheck.rs` | Read-only, non-destructive process inspection: existence (`kill -0`), liveness/zombie state, owner uid, start signature, command line (all via `ps`). |
| `src/signals.rs` | Maps a "cause of death" string to a POSIX signal (`Cause`) and sends it via `kill -s`. |
| `src/registry.rs` | Session persistence: the `Session`, `Proc`, and `State` types; TSV load/save (write-then-rename); the human-readable ledger. |
| `src/ops.rs` | High-level operations shared by the CLI and demo: `validate_name`, `spawn`, `write`, `set_cause`, `tick`, `has_pending`, `cleanup`. |
| `src/config.rs` | Env-driven, scaled-down timing config; `MAX_MISSPELLINGS`. |
| `src/clock.rs` | Epoch-second time helper. |
| `src/demo.rs` | Scripted end-to-end demonstration. |

### Key types & algorithms

- **State machine (`registry::State`).** Each owned process moves through
  `Alive → Condemned → Reaped`, with `Void` as the fail-closed sink for entries
  that fail verification or break a rule. `write` only condemns an `Alive`
  process; anything else is void.
- **Timers & scheduling.** Deadlines are plain epoch seconds
  (`clock::now() + cfg.delay`). The reaper (`ops::tick`) is a poll loop: `watch`
  and the demo call it every ~400 ms until `has_pending` is false or a safety
  deadline elapses. There is no background thread or async runtime — it is a
  cooperative, invocation-driven loop, so state survives across separate CLI
  runs via the on-disk registry.
- **Signals (`signals::resolve` → `signals::send`).** Cause strings normalize to
  one of SIGTERM / SIGKILL / SIGSTOP. `STOP` is marked non-lethal (`lethal:
  false`) so the tool knows a "coma" victim is merely paused and must be finished
  during `cleanup`.
- **PID-reuse guard.** `proccheck::start_signature` reads `ps -o lstart=` (the
  process start timestamp) at spawn time and again at reap time. A mismatch means
  the PID was recycled into a different program, and the reap is refused.
- **Name validation.** `ops::validate_name` enforces a 1–64 char label of
  `[A-Za-z0-9_-]` and explicitly rejects all-digit input to block a PID smuggled
  in through the name field.
- **Persistence format.** A tiny line-based TSV (`PROC` / `MISS` rows) written to
  `DEATHNOTE_HOME`, saved atomically-ish via write-to-`.tmp`-then-`rename`, plus
  a `ledger.log` audit trail.

### A note on `unsafe`

The crate contains **zero `unsafe` code** — all OS interaction goes through
`std::process::Command` invoking ordinary shell utilities, so no `libc` FFI or
`unsafe` blocks are needed. Note, however, that the compiler-enforced
`#![forbid(unsafe_code)]` attribute is **not currently applied** in the source;
the "no unsafe" guarantee is upheld by construction and by the doc comments in
`main.rs`/`safety.rs`, not by a lint. Adding `#![forbid(unsafe_code)]` to
`main.rs` would make the guarantee compiler-checked.

---

## Install & run

### Requirements

- **Rust + Cargo** (developed and verified with `rustc`/`cargo` **1.94.0**,
  edition 2021).
- A **Unix** system with the standard `sleep`, `ps`, `kill`, and `id` utilities
  (macOS or Linux).
- **No network access and no external crates** — fully self-contained and
  offline-runnable.

### Build

```bash
cargo build --manifest-path death-note/Cargo.toml
```

```text
   Compiling deathnote v0.1.0 (/Users/you/.../death-note)
    Finished `dev` profile [unoptimized + debuginfo] target(s) in 0.31s
```

### The scripted demo (recommended first run)

```bash
cd death-note
DEATHNOTE_DELAY=3 cargo run --quiet -- demo
```

```text
┌────────────────────────────────────────────────────────────┐
│  DEATH NOTE — SAFE SANDBOX PROCESS REAPER                   │
│  Reaps ONLY the harmless `sleep` processes it spawned.      │
│  Never targets arbitrary PIDs. Never runs as root.         │
└────────────────────────────────────────────────────────────┘

== Spawning owned sandbox processes (harmless `sleep`) ==
  spawned 'Alpha' -> pid 70296 (owned, tracked)
  spawned 'Bravo' -> pid 70314 (owned, tracked)
  spawned 'Charlie' -> pid 70332 (owned, tracked)

== Writing Death Note entries ==
  'Alpha (valid, default heart attack)' -> CONDEMNED pid=70296 cause='heart_attack'
  'Bravo (valid, cause=accident/SIGKILL)' -> CONDEMNED pid=70314 cause='accident'
  'Nobody (misspelling, unregistered)' -> NO EFFECT (misspelling #1)
  'Nobody (misspelling, unregistered)' -> NO EFFECT (misspelling #2)
  'Nobody (misspelling, unregistered)' -> NO EFFECT (permanently void after 3 misspellings)
  'Nobody (misspelling, unregistered)' -> NO EFFECT (permanently void after 3 misspellings)
  'Alpha again (duplicate)' -> VOID (a name cannot be killed twice)
  (Charlie deliberately left un-noted — it should survive)

== Watching the reaper (valid entries die on schedule) ==
  REAPED 'Alpha' (pid 70296) via heart attack (SIGTERM)
  REAPED 'Bravo' (pid 70314) via accident (SIGKILL)

== Final state ==
  Alpha    pid=70296   state=Reaped     alive=false
  Bravo    pid=70314   state=Reaped     alive=false
  Charlie  pid=70332   state=Alive      alive=true

== Cleanup (only our own verified processes) ==
  cleanup: terminated owned 'Charlie'

All owned sandbox processes accounted for. Nothing stray left behind.

== Ledger ==
[1787085741] SPAWN name='Alpha' pid=70296 (harmless owned sleep)
[1787085741] SPAWN name='Bravo' pid=70314 (harmless owned sleep)
[1787085741] SPAWN name='Charlie' pid=70332 (harmless owned sleep)
[1787085741] WRITE name='Alpha' pid=70296 cause='heart_attack' -> CONDEMNED (dies in 3s)
[1787085741] WRITE name='Bravo' pid=70314 cause='accident' -> CONDEMNED (dies in 3s)
[1787085741] WRITE name='Nobody' -> NO EFFECT (misspelling 1/3)
[1787085741] WRITE name='Nobody' -> NO EFFECT (misspelling 2/3)
[1787085741] WRITE name='Nobody' -> NO EFFECT (misspelling 3/3)
[1787085741] WRITE name='Nobody' -> VOID (permanently misspelled)
[1787085741] WRITE name='Alpha' -> VOID (already used; cannot kill twice)
[1787085744] REAPED 'Alpha' (pid 70296) via heart attack (SIGTERM)
[1787085744] REAPED 'Bravo' (pid 70314) via accident (SIGKILL)
```

### Interactive use (state persists across invocations)

State is kept on disk in `DEATHNOTE_HOME`, so each command is a separate run:

```bash
export DEATHNOTE_DELAY=2            # scale the "40 seconds" down
deathnote spawn Light              # spawn an owned sandbox 'sleep', labelled "Light"
deathnote spawn L
deathnote write Light --cause coma # SIGSTOP after the delay
deathnote write L                  # default heart attack (SIGTERM)
deathnote write Light              # duplicate -> VOID (can't kill twice)
deathnote write Ryuk               # unregistered -> NO EFFECT (misspelling)
deathnote list
deathnote watch                    # reaper enforces the schedule
deathnote cleanup                  # finish any survivors (only our own)
```

Captured output of that session:

```text
$ deathnote spawn Light
spawned owned sandbox process 'Light' pid=71120 (harmless sleep, lives 300s if un-noted)

$ deathnote spawn L
spawned owned sandbox process 'L' pid=71157 (harmless sleep, lives 300s if un-noted)

$ deathnote write Light --cause coma
'Light' (pid 71120) CONDEMNED — cause 'coma', dies in ~2s. Run `watch`.

$ deathnote write L
'L' (pid 71157) CONDEMNED — cause 'heart_attack', dies in ~2s. Run `watch`.

$ deathnote write Light   (duplicate)
'Light' is VOID — a name cannot be killed twice.

$ deathnote write Ryuk    (unregistered)
'Ryuk' has NO EFFECT — not one of our processes (misspelling #1).

$ deathnote list
NAME       PID      STATE      ALIVE    cause
Light      71120    Condemned  true     coma
L          71157    Condemned  true     heart_attack

$ deathnote watch
REAPED 'Light' (pid 71120) via coma (SIGSTOP — paused, not dead; cleaned up later) [still paused]
REAPED 'L' (pid 71157) via heart attack (SIGTERM)
watch: nothing left pending.

$ deathnote cleanup
cleanup: finished paused 'Light'
cleanup: done (only our own verified processes were touched).
```

> Note the "coma" (SIGSTOP) victim shows `alive=true` after being reaped — it is
> *paused*, not dead. `cleanup` sends SIGCONT then SIGKILL to finish it.

### Commands

| Command | Purpose |
|---|---|
| `spawn <name>` | Spawn a harmless OWNED sandbox `sleep`, labelled `name`. |
| `write <name> [--cause C]` | Write a name into the note; valid names die after the delay. |
| `cause <name> <C>` | Amend the cause of a condemned name within the window. |
| `list` / `ls` | Show owned processes and their state. |
| `watch` | Run the reaper loop until nothing is pending. |
| `reap` / `tick` | Run one reaper tick. |
| `cleanup` / `reset` | Terminate any surviving OWNED processes (verified). |
| `ledger` | Print the session ledger. |
| `demo` | Run the full scripted demonstration. |
| `rules` | Print the enforced Death Note rules. |
| `help` / `-h` / `--help` | Print usage. |

### Causes of death

| Cause (aliases) | Signal | Lethal? |
|---|---|---|
| `heart_attack` / `heartattack` / `heart` / *(empty/unknown)* | SIGTERM | yes (default) |
| `accident` / `sigkill` / `kill` | SIGKILL | yes |
| `coma` / `sigstop` / `stop` / `sleep` | SIGSTOP | no (paused; finished at cleanup) |
| `oom` / `starvation` | SIGKILL | yes — **simulated**, no real memory pressure |

### Environment knobs

| Variable | Default | Meaning |
|---|---|---|
| `DEATHNOTE_DELAY` | `4` | Seconds from writing a name to death (canon: 40). |
| `DEATHNOTE_WINDOW` | = `DEATHNOTE_DELAY` | Seconds a specific cause may still be amended. |
| `DEATHNOTE_LIFE` | `300` | Seconds a spawned `sleep` lives if never noted. |
| `DEATHNOTE_HOME` | `./.deathnote_session` | Session registry + ledger directory. |

---

## Testing

**There is no automated `#[test]` suite yet.** `cargo test` compiles the crate
and reports zero tests:

```bash
cargo test --manifest-path death-note/Cargo.toml
```

```text
   Compiling deathnote v0.1.0 (/Users/you/.../death-note)
    Finished `test` profile [unoptimized + debuginfo] target(s) in 0.31s
     Running unittests src/main.rs (.../deathnote-94f1c578330cbcb3)

running 0 tests

test result: ok. 0 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out; finished in 0.00s
```

In place of a unit-test suite, the `demo` sub-command is a **scripted
end-to-end self-check** that exercises and visibly confirms every rule in one
run:

- a valid name is condemned and reaped on schedule (SIGTERM / SIGKILL);
- an unregistered name has no effect and becomes **permanently void** after 3
  misspellings;
- a duplicate write of an already-condemned name is **void** ("can't kill twice");
- an un-noted process (`Charlie`) **survives** the reaper and is only removed by
  the final `cleanup`, proving the tool reaps *only* what was validly written;
- `cleanup` leaves nothing stray behind.

The fail-closed safety gate can be reproduced manually (see below). A proper
`#[cfg(test)]` suite covering `validate_name`, the `State` transitions in
`ops::write`, `signals::resolve`, and the registry TSV round-trip is the obvious
next step.

### Safety refusal (reproduced manually)

Point an entry at PID 1 (`launchd`, owned by root) by hand-writing a registry row
and run the reaper — it **refuses** and sends no signal:

```text
$ deathnote reap    (entry points at PID 1 / launchd, owned by root)
REFUSED to reap 'Victim' (pid 1): pid 1 is owned by uid 0, not us (501) — REFUSING — entry voided

--- confirm launchd pid 1 still running, untouched ---
/sbin/launchd
```

And a raw PID passed as a name is rejected outright:

```text
$ deathnote write 12345
error: names are LABELS, not PIDs. This tool never targets a raw PID (safety).
```

---

## Limitations & honest caveats

- **Prototype scope.** This is an educational sandbox toy, not a workload
  manager. Do not use it to supervise real services.
- **No automated tests.** As above, correctness currently rests on the scripted
  `demo` and manual checks rather than a `cargo test` suite.
- **`#![forbid(unsafe_code)]` is not applied.** The code uses no `unsafe`, but
  that is by construction, not compiler-enforced (see the *unsafe* note above).
- **Shell-utility dependency.** Ownership checks and signalling shell out to
  `ps`, `kill`, and `id`. Output parsing (e.g. `ps -o lstart=`) is Unix-specific
  and will not work on Windows; exotic `ps` variants could in principle differ.
- **Best-effort ownership marker.** The `argv[0]` token is set via
  `sh -c 'exec -a ...'`; if a shell lacks `exec -a`, the child runs a plain
  `sleep` and the command check falls back to matching `sleep`. Registry
  membership, uid, and the start-signature guard still hold.
- **Coarse timing.** Deadlines are whole seconds and the reaper polls every
  ~400 ms; it is not a precise real-time scheduler.
- **Registry is user-writable plaintext.** Anyone who can edit
  `DEATHNOTE_HOME/session.tsv` can point an entry anywhere — but the runtime
  `verify_owned` gate still refuses to signal anything you don't own (as the
  PID-1 example shows), so tampering degrades to a refusal, not a foot-gun.
- **Not concurrency-safe.** Two `deathnote` processes sharing one
  `DEATHNOTE_HOME` could race on the TSV; the save is atomic-ish (write + rename)
  but there is no locking.

---

## References / attribution

- **Concept:** *Death Note* by Tsugumi Ohba and Takeshi Obata (Shueisha). This
  project is an unaffiliated, non-commercial homage that reproduces the
  notebook's *rules* as a software metaphor. No copyrighted artwork or text is
  bundled beyond the local `banner.png`.
- **Implementation:** Rust standard library only, plus the POSIX utilities
  `sleep`, `ps`, `kill`, and `id`. No third-party crates (`Cargo.lock` lists only
  `deathnote` itself).
- **License:** MIT. Educational sandbox prototype — not intended to manage real
  workloads.
