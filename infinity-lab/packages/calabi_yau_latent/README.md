# calabi_yau_latent — Compactified Latent Space over R^k × T^m (TOY)

A small, runnable model of a latent space where a few dimensions are **large /
extended** (`R^k`) and the rest are **compactified** — periodic, small-radius
circles forming a torus `T^m`. Structure planted in the compact, periodic axes is
easy to *miss* under a naive Euclidean view (it tears wrap-around clusters apart),
but reappears once the periodic topology is respected. It is an honest, simplified
stand-in for the string-theory idea of extra-dimension compactification, used here
as an **analogy** for latent-space structure.

This package lives in the `infinity-lab` monorepo and shares the internal
[`commons`](../commons) package: seeded RNG (`commons.core.rng`), immutable config
(`commons.core.config`), and optional-dependency detection
(`commons.core.optional`).

> ## Honest caveat (read this first)
>
> **This is a TOY. It is NOT a Calabi–Yau manifold.**
>
> A real Calabi–Yau manifold is a compact Kähler manifold with vanishing first
> Chern class and a **Ricci-flat metric with special SU(n) holonomy**. Actually
> computing such a metric is *research-grade* numerical geometry (there is no known
> closed form for a generic CY metric).
>
> What this package actually builds is a **flat product space**: `R^k × T^m` — a
> few ordinary "extended" real dimensions times a product of small circles (a
> torus `T^m`). The only genuine ingredients we borrow are:
> (1) **compactification** = small, periodic dimensions, and
> (2) **wrap-around topology** = distances that respect periodicity.
> The "holonomy" demo is a deliberately labelled cartoon, not CY geometry.
> **Nothing here reproduces a Ricci-flat metric or special holonomy.**

## The concept / analogy

In string theory, our familiar large spacetime dimensions are extended, while
extra dimensions are *compactified* — curled up so small that everyday observation
does not resolve them, yet their shape governs the observable physics. Calabi–Yau
manifolds are the favoured shape for those extra dimensions.

The latent-space analogy: imagine an autoencoder-style latent code where a few
axes carry "large" variation and other axes are **periodic and small-radius**.
Structure encoded in the compact, periodic axes is easy to overlook if you treat
the latent space as ordinary flat Euclidean space — because you ignore the
wrap-around topology. Respect the periodicity and the hidden structure reappears.

## What the package demonstrates

- **Compactified latent geometry** (`core/latent.py`): a point is
  `(extended ∈ R^k) × (angles ∈ T^m)`, where each angle lives on a small circle of
  radius `r_j` (mod `2π`). `encode` / `decode` map raw vectors in and out; decode
  embeds each circle as `(r·cosθ, r·sinθ)`, so the small radii make the compact
  part contribute little Euclidean magnitude — which is *why* a naive view
  overlooks it.
- **Topology-aware distance** (`core/distance.py`): Euclidean on `R^k`, but the
  **shortest arc** on each circle for the compact factors. Contrasted with a naive
  metric that compares raw angle values on the real line.
- **Hidden-structure recovery** (`core/data.py`, `core/clustering.py`): clusters
  are planted purely in the compact dimensions, with some **straddling the `0 / 2π`
  seam**. A naive metric tears those clusters apart (over-segments); the wrap-aware
  metric recovers the true clustering (connected components).
- **Holonomy-flavoured parallel transport** (`core/holonomy.py`): transport a
  vector once around a compact loop under a toy connection and measure the net
  rotation ("holonomy angle"). A nod to CY's special holonomy — **clearly labelled
  as analogy only.**
- **ASCII visualisation** (`adapters/ascii_viz.py`): renders the compact 2-torus
  (edges identified) and the naive number line, so the wrap-around is visible.
- **Optional PNG** (`adapters/viz.py`): a matplotlib scatter of the compact torus,
  coloured by cluster — lazily guarded, never a hard dependency.
- **Optional numpy fast-paths** (`accel/numpy_backend.py`): vectorised pairwise
  distance matrices that match the pure core to a few ULP (parity-tested).

## Layout (mirrors the monorepo `src`-layout)

```
packages/calabi_yau_latent/
  src/calabi_yau_latent/
    core/        latent, distance, data, clustering, holonomy, sampling, config
    accel/       numpy_backend  (optional numpy, lazily guarded)
    adapters/    ascii_viz, cli, viz  (viz = optional matplotlib)
    demo.py
  tests/         test_cy_*.py
  README.md
```

**Core purity**: everything under `core/` imports only the standard library and
`commons.core`. numpy lives only in `accel/`; matplotlib only in `adapters/viz.py`
— both reached lazily via `commons.core.optional.try_import`, so the core runs
anywhere with no third-party dependency (a test enforces this).

## Run it

From the monorepo root (`infinity-lab/`):

```bash
# The full narrated demo (stdlib only — runs anywhere)
PYTHONPATH="packages/commons/src:packages/calabi_yau_latent/src" \
  python3 -m calabi_yau_latent.demo

# Or drive individual sections via the CLI
PYTHONPATH="packages/commons/src:packages/calabi_yau_latent/src" \
  python3 -m calabi_yau_latent.adapters.cli all
#   subcommands: seam | cluster | holonomy | torus | all
#   torus/all also accept:  --png OUTDIR   (needs the optional 'viz' extra)

# Tests (optional numpy/matplotlib tests SKIP without them, RUN with the venv)
python3 -m pytest packages/calabi_yau_latent -q
```

`numpy` and `matplotlib` are **optional** and import-guarded; the core is pure
standard library. Install the optional extras with `pip install -e '.[viz]'` to
enable the numpy fast-paths and the PNG export.

## Sample output (seed = 7)

- **Seam pair**: two points in the *same* planted cluster but on opposite sides of
  the `0 / 2π` seam. Naive angular distance `≈ 6.14` (looks far); wrap-aware
  distance `≈ 0.59` (correctly close) — a **~10× overestimate** by the naive
  metric.
- **Clustering** (connected components, same threshold for both):
  - naive metric: **5 clusters** (over-segments the two seam-straddling clusters),
    purity `1.00`.
  - wrap-aware metric: **3 clusters** (the ground truth), purity `1.00`.
- **Holonomy**: transporting `(1, 0)` around the loop with toy curvature `0.15`
  yields a net rotation of `0.15 · 2π ≈ 0.9425 rad`, matching the closed form.

The compact 2-torus (wrap-aware cluster labels; opposite edges identified):

```
  +------------------------------------------------+   theta1 -> (right edge wraps to left)
  |                     11 11                      |
  |                     1  11                      |
  |                  1                             |
  |                        2                      0|
  |   0                    2 2                    0|
  |000                  22222                     0|
  | 0                                           0 0|
  |                      11 1                      |
  +------------------------------------------------+
  theta2 | (bottom edge wraps to top). Same digit = same cluster.
```

Notice cluster `0` appears at **both** the left and right edges, and cluster `1`
at both the top and bottom — those are single wrap-around clusters that the naive
number-line view splits apart.

An optional matplotlib rendering is exported to
`infinity-lab/artifacts/calabi_yau_latent_torus.png`.

## Honest limitations (recap)

- The compact factor is a **flat torus**, not a curved Calabi–Yau manifold.
- The "metric" is the obvious product metric, not a Ricci-flat one.
- The "holonomy" uses an ad-hoc connection chosen to give a visible, nonzero
  rotation; it does **not** model SU(n) special holonomy.
- The encode/decode is a fixed analytic map, not a trained autoencoder. It exists
  to make the `R^k × T^m` structure concrete, nothing more.

The value here is pedagogical: it makes tangible *why periodic / compact latent
dimensions can hide structure from a naive Euclidean view*, using compactification
as the guiding analogy.
