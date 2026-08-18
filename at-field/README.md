![AT Field](./banner.png)

# AT Field — process isolation as an ego boundary

> A pure-userspace **simulation** of process isolation, reimagined as the *Neon Genesis Evangelion* **Absolute Terror Field** (A.T. Field): the ego boundary that keeps one mind — here, one "process" — distinct and inviolable from another.

---

## TL;DR

- A **library + demo binary** written in Rust with **zero external dependencies** (std only — confirmed by `Cargo.lock`).
- Models entities as in-memory actors, each guarded by an **AT Field** with a numeric `strength`.
- A message (`Signal`) crosses the boundary only if its `impact` clears the field's `strength`; otherwise it is **reflected** or **absorbed** — a real, testable three-way predicate.
- Sustained assault **corrodes** a field via a documented, **monotone** attenuation law; rest **regenerates** it. Sub-threshold blows can eventually break a field.
- A separate **Dirac Sea** message plane is **capability-gated** on both ends and ignores field strength entirely — a privileged side channel.
- **Nothing touches the real OS.** No processes, memory pages, threads, or OS signals. Compiled with `#![forbid(unsafe_code)]`.

```bash
cargo build
cargo run     # run the demo scenes
cargo test    # run the 9 integration tests
```

---

## The idea

In *Neon Genesis Evangelion*, the **A.T. Field** ("Absolute Terror Field") is the barrier a being projects to assert *"I am me, and you are not me."* It is at once a shield and a wound: it protects the self but also isolates it. Two AT Fields pressed against each other resist; a strong enough will can *neutralize* another's field and cross into it.

That is a strikingly good metaphor for **process isolation**. Every process has an address space and a permission boundary that other processes cannot touch unless a boundary is crossed through a sanctioned channel (IPC, a syscall, a shared page). This project takes the metaphor literally and turns it into a runnable systems model.

| Evangelion                        | Systems analogue                                        |
| --------------------------------- | ------------------------------------------------------- |
| An entity / Angel / Eva unit      | An isolated in-memory actor ("process")                 |
| The AT Field                      | The isolation boundary / permission wall                |
| Field strength                    | How hard the boundary is to cross *right now*           |
| A signal's *impact*               | The "force" of an incoming message / access attempt     |
| Penetrating the field             | A message crossing the boundary into the inbox          |
| Reflecting / absorbing            | A rejected access attempt (bounced vs. soaked)          |
| Field corrosion under assault     | A boundary weakening under a sustained barrage          |
| Field regeneration at rest        | The boundary healing when left alone                    |
| The Dirac Sea                     | A capability-gated side channel / hidden namespace      |

---

## The honest core

This is a real, runnable model. Here is exactly what is real, what is simulated, and what is theatrical.

### The mathematics (real)

**1. The penetration rule.** A `Signal` carries an `impact`; a target has a field `strength`. The classifier (`signal::classify`) is a total, deterministic predicate:

```
impact >= strength            -> Penetrated   (crosses into the inbox)
strength/2 <= impact < strength -> Reflected  (rattles the wall, bounces off)
impact < strength/2           -> Absorbed     (too weak; soaked into the wall)
```

**2. Corrosion under sustained assault — a monotone phase-space law.** Every attack, whether or not it penetrates, corrodes the target's field. The field tracks an `assault_streak` (consecutive attacks absorbed without rest). The strength lost to a single blow is:

```
attenuation(impact, streak) = corrosion_base
                            * (impact / max_strength)
                            * (1 + streak * streak_escalation)
```

with defaults `corrosion_base = 6`, `max_strength = 100`, `regen_per_tick = 4`, `streak_escalation = 0.35`.

This function is **monotonically non-decreasing in both arguments**: a harder blow corrodes more, and each successive blow in an unbroken barrage corrodes *more than the last* (a fatigue term). It is exactly zero when `impact == 0`. The field's state lives in the phase space `(strength, streak)`: barrage drives a monotone descent of `strength` as `streak` climbs, and a quiet tick resets `streak` to 0 so the field can recover. This is precisely why an attacker can break a field with repeated **sub-threshold** blows — see the captured run (a break after 5 hits).

**3. Regeneration at rest.** A quiet tick (`World::rest`) resets `streak` to 0 and regenerates every field by `regen_per_tick`, capped at `max_strength`.

**4. The Dirac Sea (capability gate).** A **separate message plane**, named after the physicist's Dirac sea (the hidden reservoir "beneath" the vacuum). It is a distinct namespace (`dirac_inbox`) reachable only when **both** sender and receiver hold the Dirac capability flag; otherwise the signal is `DIRAC-BLOCKED`. It **ignores AT Fields entirely** — access is gated purely by capability, not by field strength — modeling a privileged side channel that bypasses the normal permission wall.

### Topological framing (the field as a membrane)

Picture each field strength `s` as the **height of a closed membrane** enclosing an entity's ego. A signal is a particle launched at it with kinetic term `impact`. Penetration is the particle clearing barrier height `s`; reflection and absorption are the two sub-barrier regimes (elastic bounce vs. dissipation). Two clashing fields are two membranes pressed boundary-to-boundary — the lower wall yields first. Corrosion deforms the membrane downward, the deformation per blow growing with the `streak` coordinate. The Dirac Sea is a disjoint sheet with no membrane, joined to the normal sheet only through the capability gate.

### What is real vs. simulated vs. theatrical

| Aspect | Status | Detail |
| ------ | ------ | ------ |
| Penetration / reflection / absorption predicate | **Real** | Pure function `classify(impact, strength)`, boundary-tested. |
| Monotone corrosion law | **Real** | `AtField::attenuation`; monotonicity proven by test. |
| Regeneration with a hard cap | **Real** | `AtField::regenerate`, clamped to `max_strength`. |
| Capability-gated Dirac plane | **Real** | `DiracSea::check` requires the flag on both ends. |
| Immutable event log | **Real** | Every routing decision is recorded as an `Event` with before/after field values. |
| "Process", "isolation", "ego boundary" | **Simulated** | Entities are plain in-memory structs; signals are values pushed into `Vec` inboxes. |
| Angels, Eva units, "the sea remembers" | **Theatrical** | Flavor naming and demo copy over the systems model. |
| Real OS processes / memory / threads / signals | **Absent** | Nothing here creates, inspects, kills, or signals anything in the operating system. |

> **Safety:** compiled crate-wide with `#![forbid(unsafe_code)]` (in both `src/lib.rs` and `src/main.rs`). No `unsafe`, no FFI, no OS calls beyond `println!`.

---

## How it works

### Module map

| File | Role |
| ---- | ---- |
| `src/lib.rs` | Crate root, module wiring, safety statement, `#![forbid(unsafe_code)]`, public re-exports. |
| `src/field.rs` | `AtField` (strength, corrosion, regen) and `FieldDynamics` (tunable constants). The monotone `attenuation` law lives here. |
| `src/signal.rs` | `Signal`, `Plane` (`Normal`/`DiracSea`), `Outcome`, and the `classify` penetration predicate. |
| `src/entity.rs` | `Entity` — a named ego: a field, a normal inbox, a Dirac inbox, and a `dirac_capable` flag. |
| `src/dirac_sea.rs` | `DiracSea` capability gate + `DiracAccess` result enum. |
| `src/event.rs` | `Event` / `EventKind` — immutable log records with a `Display` impl for the log format. |
| `src/world.rs` | `World` — orchestration: spawns entities, routes signals (`send`), handles `rest`, keeps the event log. |
| `src/main.rs` | The demo: four scenes exercising every mechanism. |
| `tests/at_field.rs` | 9 integration tests. |

Binary target: `at-field` (`src/main.rs`). Library target: `at_field` (`src/lib.rs`).

### Key types & algorithms

- **`World::send(signal)`** advances the tick, looks up the target, then dispatches by plane. On the normal plane it classifies the outcome against the *current* field, then calls `absorb_attack` (which corrodes and advances the streak) — so even a reflected/absorbed hit still wears the wall down. A penetrating signal is pushed to the target's `inbox`.
- **`World::rest()`** is a quiet tick for the whole world: every field regenerates and its streak cools; only fields that actually recovered are logged.
- **`AtField::absorb_attack(impact)`** applies `attenuation`, clamps `strength` to `>= 0`, and increments `assault_streak` (saturating).
- **`DiracSea::check(sender_capable, target_capable)`** returns `Granted` only when both flags are set, else identifies which end lacked the capability.
- **Immutability:** the builder `Entity::dirac_capable()` returns a new value; the event log is append-only and never rewritten.

---

## Install & run

Requires a stable Rust toolchain with `cargo` (developed against `rustc 1.94.0`).

```bash
cargo build    # just build the library + demo binary
cargo run      # run the four demo scenes
cargo test     # run the 9 integration tests
```

### Captured demo output

Verbatim output of `cargo run`. Log line format:

```
t<tick> [<plane>] <sender> --impact <n>--> <target> (field <before> -> <after>, streak <k>) <OUTCOME> "<payload>"
```

```text
AT Field :: process isolation as an ego boundary (simulation)
Entities: Unit-01(60) Unit-00(45) Sachiel(90) Kaworu(70,dirac) Lilith(30,dirac)

=== Scene 1: ordinary signals meet ordinary fields ===
  t 1 [Normal] Unit-01 --impact  50.0--> Unit-00 (field  45.0 ->  42.0, streak 1) PENETRATED    "sync clock"
  t 2 [Normal] Unit-00 --impact  40.0--> Unit-01 (field  60.0 ->  57.6, streak 1) reflected     "ping"
  t 3 [Normal] Unit-00 --impact  15.0--> Sachiel (field  90.0 ->  89.1, streak 1) absorbed      "who are you?"

=== Scene 2: Sachiel barrages Unit-00 — field corrosion and a break ===
  >> Unit-00's AT Field has been breached after 5 blows!
  t 4 [Normal] Sachiel --impact  30.0--> Unit-00 (field  42.0 ->  39.6, streak 2) reflected     "barrage #1"
  t 5 [Normal] Sachiel --impact  30.0--> Unit-00 (field  39.6 ->  36.5, streak 3) reflected     "barrage #2"
  t 6 [Normal] Sachiel --impact  30.0--> Unit-00 (field  36.5 ->  32.8, streak 4) reflected     "barrage #3"
  t 7 [Normal] Sachiel --impact  30.0--> Unit-00 (field  32.8 ->  28.5, streak 5) reflected     "barrage #4"
  t 8 [Normal] Sachiel --impact  30.0--> Unit-00 (field  28.5 ->  23.6, streak 6) PENETRATED    "barrage #5"

=== Scene 3: quiet ticks — Unit-00's field regenerates ===
  t 9 [rest ] Unit-01 regenerates (+ 4.0) (field  57.6 ->  61.6)
  t 9 [rest ] Unit-00 regenerates (+ 4.0) (field  23.6 ->  27.6)
  t 9 [rest ] Sachiel regenerates (+ 4.0) (field  89.1 ->  93.1)
  t 9 [rest ] Kaworu regenerates (+ 4.0) (field  70.0 ->  74.0)
  t 9 [rest ] Lilith regenerates (+ 4.0) (field  30.0 ->  34.0)
  t10 [rest ] Unit-01 regenerates (+ 4.0) (field  61.6 ->  65.6)
  t10 [rest ] Unit-00 regenerates (+ 4.0) (field  27.6 ->  31.6)
  t10 [rest ] Sachiel regenerates (+ 4.0) (field  93.1 ->  97.1)
  t10 [rest ] Kaworu regenerates (+ 4.0) (field  74.0 ->  78.0)
  t10 [rest ] Lilith regenerates (+ 4.0) (field  34.0 ->  38.0)
  t11 [rest ] Unit-01 regenerates (+ 4.0) (field  65.6 ->  69.6)
  t11 [rest ] Unit-00 regenerates (+ 4.0) (field  31.6 ->  35.5)
  t11 [rest ] Sachiel regenerates (+ 2.9) (field  97.1 -> 100.0)
  t11 [rest ] Kaworu regenerates (+ 4.0) (field  78.0 ->  82.0)
  t11 [rest ] Lilith regenerates (+ 4.0) (field  38.0 ->  42.0)
  t12 [rest ] Unit-01 regenerates (+ 4.0) (field  69.6 ->  73.6)
  t12 [rest ] Unit-00 regenerates (+ 4.0) (field  35.5 ->  39.5)
  t12 [rest ] Kaworu regenerates (+ 4.0) (field  82.0 ->  86.0)
  t12 [rest ] Lilith regenerates (+ 4.0) (field  42.0 ->  46.0)

=== Scene 4: the Dirac Sea plane (capability-gated, ignores fields) ===
  t13 [DiracSea] Kaworu --impact   1.0--> Lilith (field  46.0 ->  46.0, streak 0) PENETRATED    "the sea remembers"
  t14 [DiracSea] Unit-01 --impact 999.0--> Kaworu (field  86.0 ->  86.0, streak 0) DIRAC-BLOCKED "let me in"
  t15 [DiracSea] Kaworu --impact   5.0--> Unit-01 (field  73.6 ->  73.6, streak 0) DIRAC-BLOCKED "come below"

=== Final state ===
  Unit-01  field  73.6  normal-inbox 0  dirac-inbox 0
  Unit-00  field  39.5  normal-inbox 2  dirac-inbox 0
  Sachiel  field 100.0  normal-inbox 0  dirac-inbox 0
  Kaworu   field  86.0  normal-inbox 0  dirac-inbox 0
  Lilith   field  46.0  normal-inbox 0  dirac-inbox 1

Total events logged: 30
```

### Reading the log

- **Scene 1** shows all three normal outcomes: a **penetration** (50 ≥ 45), a **reflection** (40 rattles the 60-field), and an **absorption** (15 vs. 90).
- **Scene 2** is the corrosion story: five identical 30-impact blows, none clearing the *initial* field of 45, but the escalating streak term corrodes Unit-00's field `42.0 → 39.6 → 36.5 → 32.8 → 28.5 → 23.6` until blow #5 lands (`30 ≥ 28.5`) and **breaks through**. One entity breaks another's boundary through accumulated fatigue alone.
- **Scene 3** shows every field healing at rest (Sachiel clamps at the `max_strength` ceiling of 100).
- **Scene 4** shows the Dirac plane: Kaworu→Lilith succeeds (both capable) with no effect on the field, while a 999-impact blow from the non-capable Unit-01 is `DIRAC-BLOCKED` — raw power is irrelevant; only the capability flag matters.

---

## Testing

`cargo test` runs **9 integration tests** (`tests/at_field.rs`), all passing:

| Test | What it verifies |
| ---- | ---------------- |
| `strong_signal_penetrates_and_lands_in_inbox` | `impact >= strength` penetrates and the message lands in the inbox. |
| `medium_signal_reflects_and_delivers_nothing` | A sub-threshold-but-strong hit reflects; inbox stays empty. |
| `weak_signal_is_absorbed` | A very weak hit is absorbed; inbox stays empty. |
| `classify_boundaries` | Exact predicate boundaries: `60/60`→Penetrated, `59.9/60`→Reflected, `30/60`→Reflected, `29.9/60`→Absorbed. |
| `sustained_barrage_corrodes_and_eventually_breaks_a_field` | Repeated sub-threshold blows eventually break the field; at least one message gets through. |
| `attenuation_is_monotone_in_streak_and_impact` | Attenuation is monotone in impact (and zero at `impact=0`) and non-decreasing as the streak grows. |
| `field_regenerates_but_never_exceeds_max` | Regeneration recovers strength, resets the streak, and never exceeds `max_strength` even after 1000 ticks. |
| `dirac_plane_requires_capability_on_both_ends` | Dirac transmission needs the flag on both sender and receiver; missing either end → `DiracBlocked`. |
| `dirac_plane_ignores_field_strength` | A tiny-impact Dirac signal still lands in the Dirac inbox with the field untouched; nothing hits the normal inbox. |

Observed result:

```text
running 9 tests
test result: ok. 9 passed; 0 failed; 0 ignored; 0 measured; 0 filtered out
```

---

## Limitations & honest caveats

- **It is a metaphor, not a kernel.** No real isolation, no memory protection, no scheduler. The "boundary" is an `f64` comparison, not an MMU.
- **The dynamics are hand-tuned, not derived.** The attenuation law is a *chosen* monotone function with pleasant properties (fatigue, non-negativity), not a physical model. The physics/Evangelion references are inspiration, not simulation of either.
- **Single-threaded, deterministic, turn-based.** `World::send` advances one tick per call; there is no concurrency and no randomness.
- **`send` to an unknown target** is reported (and returns) as `Reflected` with zero effect — a convenience, not a hard error.
- **`spawn` panics on duplicate names.** This is treated as a programming error in the demo, not a runtime input path.
- Meant to illustrate isolation-boundary *concepts* clearly; not a security control.

---

## References / attribution

- **Concept:** the Absolute Terror Field (A.T. Field), *Neon Genesis Evangelion* (Hideaki Anno / Gainax). Naming and flavor are homage; no copyrighted assets are bundled (the banner is an original illustration).
- **Physics nod:** the *Dirac sea* — the negative-energy reservoir underlying the relativistic vacuum — used here only as a name for a hidden, capability-gated plane.
- **Real-world analogues:** process isolation, permission boundaries, capability-based access control, and privileged side channels.
- **Dependencies:** none — Rust standard library only (`Cargo.lock` lists a single package). Crate-wide `#![forbid(unsafe_code)]`.
- **License:** MIT.
