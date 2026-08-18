# padic_embeddings

An "embedding space" whose geometry is governed by the **p-adic metric** instead of
the usual Euclidean one. Items (integers or short strings) are mapped to integer
coordinates in `Z`, and closeness is measured by how divisible their difference is by
a fixed prime `p`. The result is an *ultrametric* space with a natural tree /
hierarchy structure.

This package is the monorepo port of a standalone prototype. The pure math lives under
`padic_embeddings.core` (standard library + `commons.core` only); text rendering and
an optional matplotlib PNG export live under `padic_embeddings.adapters`, with
matplotlib reached lazily through `commons.core.optional.try_import`.

---

## The concept

Ordinary machine-learning embeddings place items in `R^d` and use Euclidean (or
cosine) distance: two points are close when their coordinates are numerically near.
The p-adic world uses a completely different notion of "size":

> A number is **small** when it is **highly divisible by a prime `p`** — not when it
> is near zero on the number line.

Under this metric, `1_000_000` and `0` are *very close* for `p = 2` (their difference
is divisible by a high power of 2), while `1` and `2` are *far* apart. This produces a
hierarchical, tree-shaped geometry that is a natural fit for taxonomies, nested
categories, and prefix / factor-sharing data.

---

## The math (honest)

Fix a prime `p`.

### p-adic valuation `v_p`

For a nonzero integer `n`, `v_p(n)` is the largest integer `k` with `p^k | n`. By
convention `v_p(0) = +infinity`. For a rational `a/b`:

```
v_p(a/b) = v_p(a) - v_p(b)
```

Examples: `v_2(8) = 3` (`8 = 2^3`), `v_2(12) = 2`, `v_7(49) = 2`,
`v_2(3/4) = 0 - 2 = -2`.

### p-adic absolute value `|x|_p`

```
|x|_p = p^(-v_p(x))     and     |0|_p = 0
```

So `|8|_2 = 2^-3 = 0.125` and `|3|_2 = 2^0 = 1`. Highly divisible numbers have *small*
absolute value. This package computes `|x|_p` **exactly** as a
`fractions.Fraction` (it is always an exact power of `p`), so the ultrametric checks
never depend on a floating-point tolerance.

### p-adic distance `d_p`

```
d_p(a, b) = |a - b|_p
```

A genuine **metric**: non-negative, symmetric, and zero iff `a = b`.

### The ultrametric (strong triangle) inequality

The defining property, stronger than the ordinary triangle inequality:

```
d_p(a, c)  <=  max( d_p(a, b),  d_p(b, c) )
```

A space obeying this is an **ultrametric space**. Consequences:
- every triangle is isosceles with the two longest sides equal;
- "balls" are nested rather than overlapping, forming a tree;
- the residue class of an integer modulo `p^k` is *exactly* a ball of radius `p^(-k)`.
  Two integers agree mod `p^k` **iff** `d_p(a, b) <= p^(-k)`.

The package verifies this inequality **exhaustively on real data** (all ordered
triples, `O(n^3)`) — see the sample output below.

---

## Layout

```
padic_embeddings/
├── core/
│   ├── padic.py       # v_p, |x|_p (exact + float), d_p, exact ultrametric triple
│   └── embedding.py   # embed items -> Z, distance matrix, k-NN, exhaustive
│                      # ultrametric verifier, residue-class balls, seeded sample
└── adapters/
    ├── render.py      # ASCII matrix + heatmap (via commons) + clusters + report
    ├── cli.py         # argparse front end
    └── viz.py         # OPTIONAL matplotlib distance-matrix heatmap PNG (lazy)
```

The embedding layer maps **integers** to themselves (they already live in `Z`) and
**strings** to integers via SHA-256 reduced modulo `2^20` (deterministic across runs,
unlike Python's salted `hash()`). Clusters at "level `k`" group coordinates by residue
mod `p^k`; increasing `k` refines the clustering, revealing the nested tree of p-adic
balls.

---

## How to run

No install is needed — the repo's `pyproject.toml` wires each package's `src` onto
`pythonpath` for pytest, and the CLI can be run with `PYTHONPATH` set to the `commons`
and `padic_embeddings` src dirs.

```bash
# From the repo root, with commons + this package on the path:
export PYTHONPATH=packages/commons/src:packages/padic_embeddings/src

# Default showcase: 2-adic structure of a list of integers
python3 -m padic_embeddings.adapters.cli --p 2

# Pick a prime and supply your own integers
python3 -m padic_embeddings.adapters.cli --p 7 --ints 7 14 49 50 98 100 343 --query 49

# Embed short strings and query nearest neighbors
python3 -m padic_embeddings.adapters.cli --p 2 --strings cat cot cog dog apple --query cat

# The one-shot demo (headline + canonical report)
python3 -m padic_embeddings.demo

# OPTIONAL: also export the distance-matrix heatmap PNG (needs matplotlib)
python3 -m padic_embeddings.adapters.cli --p 2 --png artifacts
```

CLI flags: `--p` (prime, default 2), `--ints` / `--strings` (items), `--query`
(nearest-neighbor target), `--levels` (cluster levels, default `1 2 3`), `--modulus`
(hash modulus for strings, default `2^20`), `--png OUTDIR` (optional PNG export).

### Tests

```bash
# System interpreter (no numpy/matplotlib): optional PNG test SKIPS
python3 -m pytest packages/padic_embeddings -q

# venv with numpy + matplotlib: optional PNG test RUNS
.venv/bin/python -m pytest packages/padic_embeddings -q
```

---

## Sample output (real, copied from a run)

### `--p 2` — a real 2-adic distance matrix

```
pairwise 2-adic distance matrix  d_p(a,b) = |a-b|_p
                1        3        5        8       16       17       24       32       48       64
       1        0  0.50000  0.25000  1.00000  1.00000  0.06250  1.00000  1.00000  1.00000  1.00000
       3  0.50000        0  0.50000  1.00000  1.00000  0.50000  1.00000  1.00000  1.00000  1.00000
       5  0.25000  0.50000        0  1.00000  1.00000  0.25000  1.00000  1.00000  1.00000  1.00000
       8  1.00000  1.00000  1.00000        0  0.12500  1.00000  0.06250  0.12500  0.12500  0.12500
      16  1.00000  1.00000  1.00000  0.12500        0  1.00000  0.12500  0.06250  0.03125  0.06250
      17  0.06250  0.50000  0.25000  1.00000  1.00000        0  1.00000  1.00000  1.00000  1.00000
      24  1.00000  1.00000  1.00000  0.06250  0.12500  1.00000        0  0.12500  0.12500  0.12500
      32  1.00000  1.00000  1.00000  0.12500  0.06250  1.00000  0.12500        0  0.06250  0.03125
      48  1.00000  1.00000  1.00000  0.12500  0.03125  1.00000  0.12500  0.06250        0  0.06250
      64  1.00000  1.00000  1.00000  0.12500  0.06250  1.00000  0.12500  0.03125  0.06250        0
```

Note the tree behavior: `1` and `17` are very close (`0.0625`, since
`17 - 1 = 16 = 2^4`), while every odd number is at distance `1` from every even one.

### Verified ultrametric property (real)

```
ultrametric (strong triangle inequality) verification
  d_p(a,c) <= max(d_p(a,b), d_p(b,c)) for ALL ordered triples?
  triples checked : 720
  violations found: 0
  RESULT: HOLDS (this is a true ultrametric)
```

All `10 * 9 * 8 = 720` ordered triples of the sample satisfy the strong triangle
inequality, checked over exact `Fraction` distances — **zero** violations.

### Induced hierarchical clusters (real)

```
  level 1: balls of radius 0.5 (mod 2**1 = 2)
    residue      0 : [8, 16, 24, 32, 48, 64]
    residue      1 : [1, 3, 5, 17]

  level 2: balls of radius 0.25 (mod 2**2 = 4)
    residue      0 : [8, 16, 24, 32, 48, 64]
    residue      1 : [1, 5, 17]
    residue      3 : [3]

  level 3: balls of radius 0.125 (mod 2**3 = 8)
    residue      0 : [8, 16, 24, 32, 48, 64]
    residue      1 : [1, 17]
    residue      3 : [3]
    residue      5 : [5]
```

### Nearest neighbors (real)

```
nearest neighbors of '16' under the 2-adic metric
  48             distance 0.031250
  32             distance 0.062500
  64             distance 0.062500
```

`16` is closest to `48` because `48 - 16 = 32 = 2^5` is the most 2-divisible
difference — they share the most factors of 2.

### 7-adic example (real, `--p 7 --ints 7 14 49 50 98 100 343 --query 49`)

```
  level 1: balls of radius 0.142857 (mod 7**1 = 7)
    residue      0 : [7, 14, 49, 98, 343]
    residue      1 : [50]
    residue      2 : [100]

  level 2: balls of radius 0.0204082 (mod 7**2 = 49)
    residue      0 : [49, 98, 343]
    residue      7 : [7]
    residue     14 : [14]
    ...

nearest neighbors of '49' under the 7-adic metric
  98             distance 0.020408
  343            distance 0.020408
  7              distance 0.142857
```

Multiples of `7` collapse together, and among them `49`, `98`, `343` (all divisible by
`49 = 7^2`) form a tighter sub-cluster — the p-adic metric groups numbers by *shared
prime factors*, exactly as intended.

### Optional PNG artifact

With matplotlib installed, `--png OUTDIR` (or `viz.save_distance_matrix_png`) renders
the distance matrix as a labelled heatmap to
`artifacts/padic_embeddings_distance_matrix.png`. Without matplotlib the exporter
raises a clear `OptionalDependencyError` and the ASCII renderers are used instead.

---

## Honest limitations

- Coordinates are single integers in `Z`, not vectors; this is a faithful 1-D p-adic
  embedding, not a learned high-dimensional one.
- The string embedding is a deterministic hash, so semantic similarity of words is
  **not** captured — proximity reflects the hashed integers' divisibility, which is
  what the p-adic geometry acts on. The string mode exists to show the metric works on
  hashed items, not to model language meaning.
- The ultrametric check is exhaustive `O(n^3)`; fine for the small demo sizes, not
  intended for large corpora.
