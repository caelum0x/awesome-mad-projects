# divergence_meter

A **Steins;Gate**-inspired package for the `infinity-lab` monorepo. It computes a
real "worldline divergence" number from a snapshot of *world state*, classifies it
into an **attractor field**, renders it on a **nixie-tube ASCII display**, and lets
you save and recall named worldlines via **Reading Steiner**.

> *"The Divergence Meter reads 1.048596. This is the Steins;Gate worldline.
>  El Psy Congroo."*

This is the monorepo port of the standalone `divergence-meter` prototype. It keeps
the honest systems core, adopts the shared `commons` package, and follows the
`src`-layout / core-purity conventions used across `infinity-lab`.

## Concept & reference

In the anime *Steins;Gate*, the **Divergence Meter** is a nixie-tube device that
displays the current worldline's divergence from the original timeline. Worldlines
cluster into **attractor fields** — convergent groups that resist small changes.
The two major fields are **Alpha** (divergence `< 1.0`) and **Beta**
(divergence `>= 1.0`). The value `1.048596` marks the **Steins;Gate** worldline.
Reference: Steins;Gate (2011), 5pb./Nitroplus.

This is a *systems* homage, not a replica: it reproduces the **format and
behaviour** of the meter while deriving the number honestly from real data.

## The honest hash -> worldline mapping

A divergence number is derived deterministically from a *snapshot* of world state.
No randomness, no clocks: the same input always yields the same worldline.

**1. Snapshot** (`core/worldstate.py`) — canonical bytes from one of:
   - a **directory** → a sorted `relative/path\tsize` listing (order-independent),
   - a **file** → its raw contents,
   - **`-`** → data read from standard input,
   - **JSON text** → normalised canonical JSON (sorted keys, so key order is irrelevant),
   - **plain text** → the text itself,
   - a **list of numbers** (via the API `snapshot_from_numbers`).

   Reads are capped at 8 MiB to avoid memory exhaustion.

**2. Divergence** (`core/divergence.py`):

```
digest   = SHA-256(payload)                 # 256 bits, cryptographic avalanche
word     = first 8 bytes of digest          # a 64-bit big-endian integer
fraction = word / 2**64                      # a real number in [0, 1)
value    = fraction * 2.0                     # a real number in [0, 2)
display  = round(value, 6)                    # show-style e.g. 1.048596
```

Using SHA-256 (from the standard library) makes the result **deterministic across
machines** — unlike Python's salted built-in `hash()` — and **well-distributed**: a
one-byte change scatters the number unpredictably across the whole range. The
EXACT value `word / 2**63` is exposed losslessly as a `fractions.Fraction` via
`DivergenceReading.exact_value`, computed with `commons.core.exact`
(`to_fraction`/`half_power`) so no floating-point rounding creeps in. Hitting
exactly `1.048596` from arbitrary input is astronomically unlikely by design —
that is the whole premise of the show.

**3. Attractor fields** (`core/attractor.py`) — the `[0, 2)` range is partitioned
into contiguous named half-open bins:

| Field       | Range          | Cluster |
|-------------|----------------|---------|
| Alpha-Low   | `[0.0, 0.5)`   | Alpha   |
| Alpha       | `[0.5, 1.0)`   | Alpha   |
| Beta        | `[1.0, 1.5)`   | Beta    |
| Beta-High   | `[1.5, 2.0)`   | Beta    |

Classification reports the containing field, the coarse Alpha/Beta cluster, the
**nearest field boundary**, and the **distance** to it. Values within `5e-7` of
`1.048596` are flagged as the **Steins;Gate** worldline.

**4. Reading Steiner** (`core/steiner.py`) — a JSON-backed store maps
`name → record`. Saving builds a **new** dict and writes it **atomically** (temp
file + `os.replace`), never mutating loaded data in place. `jump` recalls a saved
line and reports the signed **divergence delta** to the current line.

**5. Seeded ensembles** (`core/ensemble.py`) — `simulate_worldlines(count, seed)`
draws reproducible tokens from a seeded `commons.core.rng.DeterministicRNG`
(the process-global RNG is never touched) and hashes each into a worldline, so you
can visualise how worldlines scatter across `[0, 2)` and populate the fields.

**6. Nixie rendering** (`adapters/nixie.py`) — each digit is drawn with a 3×5
seven-segment glyph, framed in an ASCII border. Pure ASCII; works in any terminal.
The ASCII worldline **timeline** and field **histogram** (`adapters/timeline.py`)
delegate to `commons.adapters.ascii_art`.

## Layout & purity

```
src/divergence_meter/
  __init__.py         package exports
  demo.py             runnable end-to-end demo
  core/               PURE: stdlib + commons.core only
    worldstate.py     snapshot gathering (immutable Snapshot dataclass)
    divergence.py     SHA-256 -> divergence value + exact Fraction
    attractor.py      attractor-field classification
    steiner.py        Reading Steiner JSON store + delta
    ensemble.py       seeded worldline ensembles (commons.core.rng)
  adapters/           presentation / optional I/O
    nixie.py          nixie-tube ASCII renderer
    timeline.py       ASCII timeline + histogram (commons.adapters.ascii_art)
    cli.py            argparse CLI (measure/field/save/jump/lines)
    viz.py            OPTIONAL matplotlib PNG (lazy via commons.core.optional)
tests/                test_dm_*.py
```

`core/*` imports **only** the standard library and `commons.core` (enforced by
`tests/test_dm_core_purity.py`). numpy/matplotlib are never hard-imported; the PNG
exporter reaches matplotlib lazily through `commons.core.optional.try_import` and
raises a clear `OptionalDependencyError` when it is absent. All snapshots,
readings, classifications, and records are **frozen dataclasses** — no shared state
is mutated.

## Run instructions

Imports resolve via the repo's pytest `pythonpath` (no install). To run the CLI or
demo directly, put the two `src` dirs on `PYTHONPATH`:

```bash
export PYTHONPATH=packages/commons/src:packages/divergence_meter/src

# Measure a literal string, a file, a directory, or stdin
python -m divergence_meter.adapters.cli measure "El Psy Congroo"
python -m divergence_meter.adapters.cli measure ./README.md
printf 'Kurisu Makise' | python -m divergence_meter.adapters.cli measure -

# JSON is normalised: key order does not change the worldline
python -m divergence_meter.adapters.cli measure '{"a":1,"b":2}'

# Classify into an attractor field (source defaults to ".")
python -m divergence_meter.adapters.cli field "El Psy Congroo"

# Reading Steiner: save, list, and jump between worldlines
python -m divergence_meter.adapters.cli save alpha "worldline alpha"
python -m divergence_meter.adapters.cli save beta  "worldline beta"
python -m divergence_meter.adapters.cli lines
python -m divergence_meter.adapters.cli jump alpha "worldline beta"

# The end-to-end demo (measure + ASCII timeline + field histogram)
python -m divergence_meter.demo
```

The Reading Steiner store defaults to `worldlines_store.json` in the package
directory; override it with `--store /path/to/store.json`.

### Optional PNG timeline

With the `viz` extra installed (`numpy`, `matplotlib`), export a worldline
divergence timeline with the Alpha/Beta bands shaded and the Steins;Gate line
marked:

```python
from divergence_meter.adapters import viz
viz.save_worldlines_png()  # -> infinity-lab/artifacts/divergence_meter_worldlines.png
```

Without matplotlib the call raises `viz.OptionalDependencyError`; use the ASCII
`adapters.timeline.render_worldline_timeline` instead (no dependencies).

### Tests

```bash
# System interpreter (no numpy/matplotlib): optional PNG test SKIPS
python3 -m pytest packages/divergence_meter -q

# venv interpreter (numpy/matplotlib present): optional PNG test RUNS
.venv/bin/python -m pytest packages/divergence_meter -q
```

## Sample output

`measure "El Psy Congroo"`:

```
+---------------------------------+
|          _   _   _   _   _      |
|   |     | | |     | | |   |   | |
|   |     | | |_   _| | |  _|   | |
|   |     | | | | |   | |   |   | |
|   |  .  |_| |_| |_  |_| ._|   | |
+---------------------------------+
      DIVERGENCE: 1.062031
      origin   : text:literal
      sha256   : 87f0a5ba6b8d774c...
      Field: Beta (cluster Beta) | nearest boundary 1.000000 (distance 0.062031)
```

`field "El Psy Congroo"`:

```
Divergence : 1.062031
Field: Beta (cluster Beta) | nearest boundary 1.000000 (distance 0.062031)
```

`save` / `lines` / `jump`:

```
$ ... save alpha "worldline alpha"
Saved worldline 'alpha' @ 0.120241
  origin: text:literal
  store : .../packages/divergence_meter/worldlines_store.json

$ ... jump alpha "worldline beta"
      Reading Steiner engaged. Jump target: 'alpha'
      saved line   : 0.120241  (text:literal)
      current line : 0.124228  (text:literal)
      divergence delta : +0.003987  [Beta-ward (+)]
```

## Notes & limitations

- Values are deterministic and reproducible across machines (SHA-256, not `hash()`).
- The tool never signals processes or touches files outside its own directory; the
  store lives in the package folder by default.
- Reaching exactly `1.048596` from arbitrary input is astronomically unlikely by
  design — that is the whole premise of the show.
