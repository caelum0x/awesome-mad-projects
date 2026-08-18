# Divergence Meter

A **Steins;Gate**-inspired command-line tool that computes a real "worldline
divergence" number from a snapshot of *world state*, classifies it into an
**attractor field**, renders it on a **nixie-tube ASCII display**, and lets you
save and recall named worldlines via **Reading Steiner**.

> *"The Divergence Meter reads 1.048596. This is the Steins;Gate worldline.
>  El Psy Congroo."*

## Concept & reference

In the anime *Steins;Gate*, the **Divergence Meter** is a nixie-tube device that
displays the current worldline's divergence from the original timeline. Worldlines
cluster into **attractor fields** — convergent groups of timelines that resist small
changes. The two major fields are **Alpha** (divergence `< 1.0`) and **Beta**
(divergence `>= 1.0`). The value `1.048596` marks the **Steins;Gate** worldline,
the goal the protagonist strives to reach.

This project is a faithful *systems* homage, not a replica: it reproduces the
**format and behaviour** of the meter while deriving the number honestly from real
data. Reference: Steins;Gate (2011), 5pb./Nitroplus; the "1.048596" line and the
Alpha/Beta attractor-field concept.

## The honest math / systems core

A divergence number is derived deterministically from a *snapshot* of world state.
No randomness, no clocks: the same input always yields the same worldline.

**1. Snapshot** (`worldstate.py`) — canonical bytes from one of:
   - a **directory** → a sorted `relative/path\tsize` listing (order-independent),
   - a **file** → its raw contents,
   - **`-`** → data read from standard input,
   - **JSON text** → normalised canonical JSON (sorted keys, so key order is irrelevant),
   - **plain text** → the text itself,
   - a **list of numbers** (via the API `snapshot_from_numbers`).

   Reads are capped at 8 MiB to avoid memory exhaustion.

**2. Divergence** (`divergence.py`):

```
digest   = SHA-256(payload)                # 256 bits, cryptographic avalanche
word     = first 8 bytes of digest         # a 64-bit big-endian integer
fraction = word / 2**64                     # a real number in [0, 1)
value    = fraction * 2.0                    # a real number in [0, 2)
display  = round(value, 6)                   # show-style e.g. 1.048596
```

Using SHA-256 (from the standard library) makes the result **deterministic across
machines** — unlike Python's salted built-in `hash()` — and **well-distributed**:
a one-byte change to the input scatters the number unpredictably across the whole
range. The canonical `1.048596` line generally cannot be produced from arbitrary
data — that is the point; reaching Steins;Gate is meant to be hard.

**3. Attractor fields** (`attractor.py`) — the `[0, 2)` range is partitioned into
contiguous named half-open bins:

| Field       | Range          | Cluster |
|-------------|----------------|---------|
| Alpha-Low   | `[0.0, 0.5)`   | Alpha   |
| Alpha       | `[0.5, 1.0)`   | Alpha   |
| Beta        | `[1.0, 1.5)`   | Beta    |
| Beta-High   | `[1.5, 2.0)`   | Beta    |

Classification reports the containing field, the coarse Alpha/Beta cluster, the
**nearest field boundary**, and the **distance** to it (how close the line is to
slipping into a neighbouring cluster). Values within `5e-7` of `1.048596` are
flagged as the **Steins;Gate** worldline.

**4. Reading Steiner** (`steiner.py`) — a JSON-backed store maps `name → record`.
Saving builds a **new** dict and writes it **atomically** (temp file + `os.replace`),
never mutating the loaded data in place. `jump` recalls a saved line and reports the
signed **divergence delta** between it and the current line.

**5. Nixie rendering** (`nixie.py`) — each digit is drawn with a 3×5 seven-segment
glyph, framed in an ASCII border to evoke the tube display. Pure ASCII; works in any
terminal.

### Design

Small, focused, standard-library-only modules (no third-party dependencies):

```
divergence_meter/
  __init__.py      package exports
  __main__.py      enables `python -m divergence_meter`
  worldstate.py    snapshot gathering (immutable Snapshot dataclass)
  divergence.py    SHA-256 -> divergence value + formatting
  attractor.py     attractor-field classification
  steiner.py       Reading Steiner JSON store + delta
  nixie.py         nixie-tube ASCII renderer
  cli.py           argparse CLI wiring
tests/
  test_divergence_meter.py   17 unittest cases
```

Snapshots, readings, classifications, and records are all **frozen dataclasses**,
so no shared state is mutated.

## Requirements

- **Python 3.9+** (developed and verified on Python 3.14). Standard library only.

## Run instructions

Run everything from the project root (`divergence-meter/`):

```bash
# Measure a literal string
python3 -m divergence_meter measure "El Psy Congroo"

# Measure a file, a directory, or standard input
python3 -m divergence_meter measure ./README.md
python3 -m divergence_meter measure .
printf 'Kurisu Makise' | python3 -m divergence_meter measure -

# JSON is normalised: key order does not change the worldline
python3 -m divergence_meter measure '{"a":1,"b":2}'

# Classify the current line into an attractor field (source defaults to ".")
python3 -m divergence_meter field "El Psy Congroo"

# Reading Steiner: save, list, and jump between worldlines
python3 -m divergence_meter save alpha "worldline alpha"
python3 -m divergence_meter save beta  "worldline beta"
python3 -m divergence_meter lines
python3 -m divergence_meter jump alpha "worldline beta"

# Version / help
python3 -m divergence_meter --version
python3 -m divergence_meter --help
```

The Reading Steiner store defaults to `worldlines_store.json` in the project
directory. Override it with `--store /path/to/store.json`.

### Run the tests

```bash
python3 -m unittest discover -s tests -v
# or, if pytest is installed:
pytest tests
```

## Sample output

`measure`:

```
$ python3 -m divergence_meter measure "El Psy Congroo"
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

`field`:

```
$ python3 -m divergence_meter field "El Psy Congroo"
Divergence : 1.062031
Field: Beta (cluster Beta) | nearest boundary 1.000000 (distance 0.062031)
```

`save` / `lines` / `jump`:

```
$ python3 -m divergence_meter save alpha "worldline alpha"
Saved worldline 'alpha' @ 0.120241
  origin: text:literal
  store : .../divergence-meter/worldlines_store.json

$ python3 -m divergence_meter lines
Saved worldlines (2):
  0.120241  alpha            text:literal  @ 2026-08-18T12:55:52+00:00
  0.124228  beta             text:literal  @ 2026-08-18T12:55:52+00:00

$ python3 -m divergence_meter jump alpha "worldline beta"
+---------------------------------+
|  _           _       _   _   _  |
| | |       |   | | |   |   | | | |
| | |       |  _| |_|  _|  _| |_| |
| | |       | |     | |   |   | | |
| |_|  .    | |_    | |_  |_  |_| |
+---------------------------------+
      DIVERGENCE: 0.124228
      Reading Steiner engaged. Jump target: 'alpha'
      saved line   : 0.120241  (text:literal)
      current line : 0.124228  (text:literal)
      divergence Δ : +0.003987  [Beta-ward (+)]
```

Test run:

```
$ python3 -m unittest discover -s tests -v
...
Ran 17 tests in 0.001s

OK
```

## Notes & limitations

- Values are deterministic and reproducible across machines (SHA-256, not `hash()`).
- The tool never signals processes, loads modules, or touches files outside its
  own directory; the store lives in the project folder by default.
- Hitting exactly `1.048596` from arbitrary input is astronomically unlikely by
  design — that is the whole premise of the show.
