# Calabi–Yau-style Compactified Latent Space (TOY)

A small, runnable Python prototype of a latent space where some dimensions are
**large / extended** and others are **compactified** (periodic, small radius).
It is an honest, simplified stand-in for the string-theory idea of
extra-dimension compactification, used here as an **analogy** for latent-space
structure.

> ## Honest caveat (read this first)
>
> **This is a TOY. It is NOT a Calabi–Yau manifold.**
>
> A real Calabi–Yau manifold is a compact Kähler manifold with vanishing first
> Chern class and a Ricci-flat metric with **special SU(n) holonomy**.
> Actually computing such a metric is *research-grade* numerical geometry
> (there is no known closed form for a generic CY metric).
>
> What this project actually builds is a **flat product space**:
> `R^k  ×  T^m`  — a few ordinary "extended" real dimensions times a product of
> small circles (a torus `T^m`). The only genuine ingredients we borrow are:
> (1) **compactification** = small, periodic dimensions, and
> (2) **wrap-around topology** = distances that respect periodicity.
> The "holonomy" demo is a deliberately labeled cartoon, not CY geometry.
> Nothing here reproduces a Ricci-flat metric or special holonomy.

## The concept / analogy

In string theory, our familiar large spacetime dimensions are extended, while
extra dimensions are *compactified* — curled up so small that everyday
observation does not resolve them, yet their shape governs the observable
physics. Calabi–Yau manifolds are the favored shape for those extra dimensions.

The latent-space analogy: imagine an autoencoder-style latent code where a few
axes carry "large" variation and other axes are **periodic and small-radius**.
Structure encoded in the compact, periodic axes is easy to *miss* if you treat
the latent space as ordinary flat Euclidean space — because you ignore the
wrap-around topology. Respect the periodicity and the hidden structure reappears.

## What the prototype demonstrates

- **Compactified latent geometry** (`latent.py`): a point is
  `(extended ∈ R^k)  ×  (angles ∈ T^m)`, where each angle lives on a small
  circle of radius `r_j` (mod `2π`). `encode` / `decode` map raw vectors in and
  out; decode embeds each circle as `(r·cosθ, r·sinθ)`, so the small radii make
  the compact part contribute little Euclidean magnitude — which is *why* a
  naive view overlooks it.
- **Topology-aware distance** (`distance.py`): Euclidean on `R^k`, but the
  **shortest arc** on each circle for the compact factors. Contrasted with a
  naive metric that compares raw angle values on the real line.
- **Hidden structure recovery** (`data.py`, `clustering.py`, `demo.py`):
  clusters are planted purely in the compact dimensions, with some clusters
  **straddling the `0 / 2π` seam**. A naive metric tears those clusters apart
  (over-segments); the wrap-aware metric recovers the true clustering.
- **Holonomy-flavored parallel transport** (`holonomy.py`): transport a vector
  once around a compact loop under a toy connection and measure the net
  rotation ("holonomy angle"). A nod to CY's special holonomy — **clearly
  labeled as analogy only.**
- **ASCII visualization** (`ascii_viz.py`): renders the compact 2-torus (edges
  identified) and the naive number line, so the wrap-around is visible.
  `matplotlib` is optional (ASCII is the default and always works).

## Run it

```bash
cd calabi-yau-latent
python3 demo.py     # the full narrated demo
python3 tests.py    # lightweight self-tests (no pytest needed)
```

No third-party packages are required. `numpy` and `matplotlib` are **optional**
and import-guarded (see `latent.py` / `ascii_viz.py`); the core is pure standard
library so it runs anywhere.

## Example results (seed = 7)

- **Seam pair**: two points in the *same* planted cluster but on opposite sides
  of the `0 / 2π` seam. Naive angular distance `≈ 6.2` (looks far); wrap-aware
  distance `≈ 0.26` (correctly close) — a **~24× overestimate** by the naive
  metric.
- **Clustering** (connected-components, same threshold for both):
  - naive metric: **5 clusters** (over-segments the two seam-straddling
    clusters), purity `1.00`.
  - wrap-aware metric: **3 clusters** (the ground truth), purity `1.00`.
- **Holonomy**: transporting `(1,0)` around the loop with toy curvature `0.15`
  yields a net rotation of `0.15 · 2π ≈ 0.94 rad`, matching the closed form.

## Files

| File | Purpose |
|------|---------|
| `latent.py`   | `LatentPoint`, `CompactifiedLatentSpace`, encode/decode |
| `distance.py` | naive vs wrap-aware (toroidal) distances |
| `data.py`     | generate clusters planted in the compact factor |
| `clustering.py` | connected-components clustering + purity metric |
| `holonomy.py` | toy parallel transport around a compact loop |
| `ascii_viz.py` | ASCII torus / number-line rendering (matplotlib optional) |
| `demo.py`     | the runnable narrated demo |
| `tests.py`    | self-tests |

## Honest limitations (recap)

- The compact factor is a **flat torus**, not a curved Calabi–Yau manifold.
- The "metric" is the obvious product metric, not a Ricci-flat one.
- The "holonomy" uses an ad-hoc connection chosen to give a visible, nonzero
  rotation; it does **not** model SU(n) special holonomy.
- The "autoencoder" encode/decode is a fixed analytic map, not a trained
  network. It exists to make the `R^k × T^m` structure concrete, nothing more.

The value here is pedagogical: it makes tangible *why periodic/compact latent
dimensions can hide structure from a naive Euclidean view*, using
compactification as the guiding analogy.
