# AT Field — process isolation as an ego boundary

A small, self-contained Rust prototype that models **process isolation** as an
Evangelion-style **Absolute Terror Field** (AT Field): the psychological
boundary that keeps one mind — here, one "process" — distinct and inviolable
from another.

> **This is a pure userspace simulation.** It does not create, inspect, kill, or
> signal any real operating-system process. It does not read or write real
> memory, threads, or OS signals. "Entities" are plain in-memory structs and
> "signals" are values pushed into `Vec` inboxes. The crate is compiled with
> `#![forbid(unsafe_code)]`.

---

## Concept: the Absolute Terror Field

In *Neon Genesis Evangelion*, the AT Field is the barrier a being projects to
assert "I am me, and you are not me." It is simultaneously a shield and a wound:
it protects the self, but it also isolates it. Two AT Fields pressed against
each other resist; a strong enough will can *neutralize* another's field and
cross into it.

That is a startlingly good metaphor for **process isolation**: every process has
an address space that other processes cannot touch unless a boundary is crossed
through a sanctioned channel (IPC, a syscall, a shared page). This prototype
takes the metaphor literally and makes it a runnable systems model.

| Evangelion                     | Systems analogue                                   |
| ------------------------------ | -------------------------------------------------- |
| An entity / Angel / Eva unit   | An isolated in-memory actor ("process")            |
| The AT Field                   | The isolation boundary / permission wall           |
| Field strength                 | How hard the boundary is to cross right now        |
| A signal's *impact*            | The "force" of an incoming message / access attempt|
| Penetrating the field          | A message crossing the boundary into the inbox     |
| Reflecting / absorbing         | A rejected access attempt (bounced vs. soaked)     |
| Field corrosion under assault  | A boundary weakening under a sustained barrage      |
| Field regeneration at rest     | The boundary healing when left alone                |
| The Dirac Sea                  | A capability-gated side channel / hidden namespace |

---

## Honest systems core

The interesting, non-hand-wavy parts of the model:

### 1. Penetration rule (the boundary check)

A `Signal` carries an `impact`. When it meets a target's field of `strength`:

* `impact >= strength` → **Penetrated** — the message crosses and lands in the
  inbox.
* `strength/2 <= impact < strength` → **Reflected** — strong enough to rattle
  the membrane, not enough to cross; it bounces off.
* `impact < strength/2` → **Absorbed** — too weak to matter; soaked harmlessly
  into the membrane.

This is a real, testable predicate — not a coin flip. See
[`src/signal.rs`](src/signal.rs) (`classify`).

### 2. Corrosion under sustained assault (monotone phase-space attenuation)

Every attack — whether it penetrates or not — corrodes the target's field. The
field tracks an `assault_streak`: the number of consecutive attacks absorbed
without a chance to rest. The strength lost to a single blow is:

```text
attenuation(impact, streak) = corrosion_base
                            * (impact / max_strength)
                            * (1 + streak * streak_escalation)
```

with defaults `corrosion_base = 6`, `max_strength = 100`,
`streak_escalation = 0.35`.

This function is **monotonically non-decreasing in both arguments**: a harder
blow corrodes more, and each successive blow in an unbroken barrage corrodes
*more than the last* (fatigue / metal-fatigue analogue). It is exactly zero when
`impact == 0`. This is the "simple monotone phase-space law" the brief asks for:
the field's state lives in the phase space `(strength, streak)`, and the
attenuation term is the monotone flow that drives `strength` downward as
`streak` climbs. Implementation and proof-by-test are in
[`src/field.rs`](src/field.rs) and
[`tests/at_field.rs`](tests/at_field.rs) (`attenuation_is_monotone_in_streak_and_impact`).

This is precisely why an attacker can break a field with repeated *sub-threshold*
blows: 30-impact hits never clear Unit-00's initial field of 45, but the streak
term escalates the corrosion each hit until the field drops below 30 and the
next blow penetrates (see the log below — a break after 5 blows).

### 3. Regeneration at rest

A quiet tick (`World::rest`) resets the streak to 0 and regenerates every field
by `regen_per_tick` (default 4), capped at `max_strength`. Boundaries heal when
they are not under attack.

### 4. The Dirac Sea (capability-gated side namespace)

A **separate message plane** modeled after the physicist's Dirac sea — the
hidden reservoir "beneath" the ordinary vacuum. It is a distinct namespace from
the normal inbox and is **reachable only by entities holding the Dirac
capability flag**. A Dirac transmission requires the flag on *both* ends;
otherwise it is `DIRAC-BLOCKED`. Crucially, the Dirac plane **ignores AT Fields
entirely** — access is gated purely by capability, not by field strength. This
mirrors a privileged side channel that bypasses the normal permission wall. See
[`src/dirac_sea.rs`](src/dirac_sea.rs).

---

## Topological framing: the field as a membrane

Picture each entity's field strength `s` as the **height of a closed membrane**
enclosing its ego (a level set / potential barrier). A signal is a particle
launched at the membrane with kinetic term `impact`:

* **Penetration** is the particle clearing the barrier height `s` and crossing
  the membrane into the interior (the inbox). Below `s` it cannot cross.
* **Reflection vs. absorption** are the two sub-barrier regimes: enough energy
  to elastically bounce off the wall, or so little it is dissipated into the
  wall.
* **Two fields clashing** are two membranes pressed boundary-to-boundary; the
  lower wall is the one that yields first — competing boundaries in the same
  space.
* **Corrosion** deforms the membrane downward; the deformation per blow grows
  with the `streak` coordinate. The system's trajectory through the
  `(strength, streak)` **phase space** is a monotone descent under barrage and a
  monotone climb back toward `max_strength` at rest.
* The **Dirac Sea** is a disjoint sheet — a second cover of the message space —
  with no membrane at all, joined to the normal sheet only through the
  capability gate.

---

## Project layout

```
at-field/
├── Cargo.toml
├── README.md
├── src/
│   ├── lib.rs         # crate root, module wiring, safety statement
│   ├── field.rs       # AtField: strength, corrosion, regen, attenuation law
│   ├── signal.rs      # Signal, Plane, Outcome, penetration classifier
│   ├── entity.rs      # Entity: field + inboxes + Dirac capability flag
│   ├── dirac_sea.rs   # capability-gated side plane
│   ├── event.rs       # immutable event-log records + Display
│   ├── world.rs       # orchestration, routing, the event log
│   └── main.rs        # the demo scenes
└── tests/
    └── at_field.rs    # 9 integration tests
```

No external dependencies. Standard library only.

---

## Run it

```bash
cd at-field
cargo run          # run the demo scenes
cargo test         # run the 9 integration tests
cargo build        # just build
```

Requires a stable Rust toolchain with `cargo` (developed against Rust 1.94).

---

## Sample output (event log)

This is the actual output of `cargo run`. The log format is:

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

* **Scene 1** shows all three normal outcomes: a **penetration** (50 ≥ 45), a
  **reflection** (40 rattles the 60-field), and an **absorption** (15 vs. 90).
* **Scene 2** is the corrosion story: five identical 30-impact blows, none of
  which clears the *initial* field of 45, but the escalating streak term
  corrodes Unit-00's field `42.0 → 39.6 → 36.5 → 32.8 → 28.5 → 23.6` until blow
  #5 lands `30 ≥ 28.5` and **breaks through**. One entity breaks another's field
  after enough hits — exactly the required demo.
* **Scene 3** shows every field healing at rest (Sachiel clamps at the
  `max_strength` ceiling of 100).
* **Scene 4** shows the Dirac plane: Kaworu→Lilith succeeds (both capable) with
  no effect on the field, while a 999-impact blow from the non-capable Unit-01
  is `DIRAC-BLOCKED` — power is irrelevant, only the capability flag matters.

---

## Tests

`cargo test` runs 9 integration tests covering: penetration/reflection/
absorption, the classifier boundaries, barrage-to-break corrosion, monotonicity
of the attenuation law, regeneration with a max cap, and the Dirac plane's
capability gating and field-independence.

## License

MIT.
