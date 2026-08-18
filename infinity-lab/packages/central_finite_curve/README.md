# central_finite_curve

A `src`-layout package in the **infinity-lab** monorepo. Inspired by the
**Central Finite Curve** from *Rick and Morty* -- the region of the multiverse
containing every reality in which a Rick is the smartest being: an
infinite-but-bounded set of universes carved out of the wider multiverse.

This package models that idea concretely and runs it end to end. The pure math
core is **standard-library only** (plus the shared internal `commons` package);
numpy is an optional fast-path and matplotlib/Pillow/ffmpeg drive only the
optional figures and animations.

---

## The concept

* The **multiverse** is a cloud of `N` points in a high-dimensional space `R^D`.
  Each point is one universe; its coordinates are its "physical constants".
* Each universe gets a deterministic **Rickness** score.
* The **Central Finite Curve** is the subset of universes whose Rickness is
  within a small `epsilon` of the observed maximum -- a thin ridge, *infinite in
  principle yet finitely varying*: you can slide along its free directions
  forever, but the constrained directions are pinned.
* A **portal gun** (a hard-constraint Metropolis random walk) travels *along*
  that ridge, only ever stepping to universes that stay inside the band.

---

## The honest math

Nothing is hidden behind hand-waving. The pipeline is four pure-core stages
(`core/`) plus presentation adapters (`adapters/`).

### 1. Rickness score (`core/rickness.py`)

`rickness(x)` is a weighted combination of two bounded "genius" proxies minus a
heavily-weighted "harmony penalty":

```
rickness(x) = w_complexity * complexity(x)
            + w_entropy    * entropy(x)
            - w_penalty    * penalty(x)
```

* `complexity(x) = tanh(std(x) / 2)` in `[0, 1)` -- rewards universes whose
  coordinates are spread out. Bounded, so it cannot run to infinity.
* `entropy(x)` = normalised Shannon entropy of `softmax(|x|)` in `[0, 1]` --
  rewards universes that spread their "mass" across many dimensions.
* `penalty(x)` = sum of squared residuals of algebraic constraints
  `g_k(x) = 0`. Their common zero-set is a **manifold** embedded in `R^D`.
  Because the penalty is heavily weighted, the near-maximal set is a thin tube
  hugging that manifold -- this is what makes the maximum a *ridge* (a whole
  sub-manifold) rather than an isolated point.

The constraints (with `D = 8`) pin ~4 of the 8 degrees of freedom:

| constraint | meaning                                             |
|-----------|------------------------------------------------------|
| `g0`      | dims (0, 1) lie on a circle of radius `ring_radius` (the "ring") |
| `g1`      | dim 2 tied to dim 0 via a sine wave                  |
| `g2`      | dims (3, 4) are mirror images (sum to 0)             |
| `g3`      | dims (5, 6) are a reciprocal pair (product = 1)      |

Dim 7 is completely free. So the ridge is roughly a **4-dimensional
sub-manifold living in 8-dimensional space**.

### 2. Generating the multiverse (`core/multiverse.py`)

A deterministic mixture: a small `near_manifold_fraction` of universes are
solved *onto* the manifold (with a tiny Gaussian jitter) so the near-maximal band
stays populated, and the rest are uniform-box junk. Every draw flows through
`commons.core.rng.DeterministicRNG` seeded from `config.seed` (Gaussian draws are
synthesised from the uniform stream via Box-Muller), so two runs with the same
config are byte-identical.

### 3. Filtering to the near-maximal band (`core/curve.py`)

The true supremum is unknown analytically, so we take the maximum *observed*
score as the practical peak and keep every universe within an absolute tolerance
of it:

```
band_low = max_score - eps_absolute
curve    = { u : rickness(u) >= band_low }
```

### 4. Sampling along it -- the portal gun (`core/portal_gun.py`)

A hard-constraint Metropolis walk: from the best universe, propose a Gaussian
step and **accept only if the new Rickness stays inside the band**, otherwise stay
put. The acceptance rule is the indicator of the band region, so the walk
explores the ridge (near-)uniformly instead of collapsing to a point. The
acceptance ratio is tracked; the trajectory is a genuine path *along the Central
Finite Curve*.

### 5. Projection & render (`core/projection.py`, `adapters/`)

The 8-D ridge is projected to 2-D via its **top-2 principal components**
(pure-stdlib power-iteration eigensolver with deflation; an optional numpy
`eigh` fast-path lives in `accel/`; a `project_3d` top-3 view feeds the rotating
3-D animation). `adapters/render.py` draws it as an ASCII density scatter with
the walk overlaid; `adapters/viz.py` and `adapters/animate*.py` add an optional
matplotlib PNG, the walk GIF/MP4, a four-panel explainer and a rotating 3-D
projection (see [Animations](#animations)).

---

## Reading of the Central Finite Curve -- and the contrast with `mobius_rickness`

This monorepo hosts **two honest but different readings** of the same *Rick and
Morty* idea, and they are worth contrasting:

* **This package (`central_finite_curve`) -- a near-maximal *band* (ridge as a
  super-level set).** The curve is `{ x : rickness(x) >= max - epsilon }`: the
  thin tube of universes that are *within epsilon of the most Rick*. It is a
  ridge because the constraint penalty is flat (zero) all along a sub-manifold
  while the bounded complexity/entropy vary only gently on it. The object is a
  **statistical super-level set** of a scalar field over a sampled point cloud;
  its thickness is a tunable `epsilon` and its shape is discovered empirically
  from the samples.

* **`mobius_rickness` -- an exact *zero set* (`R^{-1}(0)`) and an SCMS ridge.**
  There the Central Finite Curve is the honest **zero set** of a sign-changing
  Rickness field layered on the Gaussian curvature of a Mobius strip (traced by
  scan-line bisection + marching squares), plus a density-ridge reading via
  Subspace-Constrained Mean Shift. That curve is a genuine *codimension-1*
  contour `{ R = 0 }` on a smooth surface, exact up to a root-finding tolerance.

The contrast in one line: **`mobius_rickness` reads the curve as the level set
`R = 0` (a boundary where Rickness vanishes); `central_finite_curve` reads it as
the near-*maximal* band `R >= max - epsilon` (a ridge where Rickness peaks).**
Zero-set versus argmax-ridge -- two faithful ways to make "the only arc of
realities where a Rick exists" concrete.

---

## Layout

```
central_finite_curve/
  src/central_finite_curve/
    core/            # pure engine: stdlib + commons.core ONLY
      config.py      #   frozen CurveConfig (all tunables) + DEFAULT
      sampling.py    #   seeded draws on commons.core.rng (Box-Muller Gaussians)
      rickness.py    #   the Rickness score + the four ridge constraints
      multiverse.py  #   seeded generation of N high-dim universes
      curve.py       #   filter to the near-maximal epsilon band
      portal_gun.py  #   hard-constraint Metropolis walk along the band
      projection.py  #   stdlib power-iteration PCA to 2-D
      pipeline.py    #   end-to-end orchestrator (one source of truth)
    accel/
      numpy_backend.py  # OPTIONAL vectorised Rickness + numpy PCA (lazily guarded)
    adapters/
      render.py      # ASCII density scatter + walk overlay (stdlib)
      cli.py         # argparse subcommands + --png / animate
      viz.py         # OPTIONAL matplotlib projection PNG (lazy)
      animate.py     # OPTIONAL walk GIF / MP4 (lazy matplotlib + Pillow / ffmpeg)
      animate_panels.py # OPTIONAL four-panel composite explainer GIF / MP4 (lazy)
      animate_3d.py  # OPTIONAL rotating 3-D projection GIF / MP4 (lazy)
    demo.py          # runnable end-to-end demo
  tests/             # pytest (core tests always run; optional tests importorskip)
```

**Core purity** is enforced by a test: `core/*` imports only the standard library
and `commons.core` -- never numpy, matplotlib, or an adapter.

---

## Run

From the repo root, with the package on the path (the repo's `pyproject.toml`
already wires this for pytest):

```bash
export PYTHONPATH=packages/commons/src:packages/central_finite_curve/src

# Full pipeline, canonical report + ASCII projection:
python3 -m central_finite_curve.adapters.cli all

# Individual stages (all stdlib-only):
python3 -m central_finite_curve.adapters.cli generate
python3 -m central_finite_curve.adapters.cli curve
python3 -m central_finite_curve.adapters.cli walk
python3 -m central_finite_curve.adapters.cli project

# Small, fast run (handy for a quick look):
python3 -m central_finite_curve.adapters.cli all --universes 800 --walk-steps 300

# The runnable demo:
python3 -m central_finite_curve.demo
```

Optional figures/animations need the `viz` extra (numpy + matplotlib) and, for
MP4, ffmpeg on PATH:

```bash
# Projection PNG -> OUTDIR/central_finite_curve_projection.png
python3 -m central_finite_curve.adapters.cli all --png artifacts

# Walk GIF (+ MP4) -> OUTDIR/central_finite_curve_walk.gif (.mp4)
python3 -m central_finite_curve.adapters.cli animate artifacts --mp4
```

The repo-level `scripts/regenerate_artifacts.sh` regenerates every artifact via
the venv, using exactly these adapters.

---

## Animations

Three optional animations render the pipeline, all DEFERRED behind the `viz`
extra (matplotlib + Pillow for GIFs; an `ffmpeg` binary on PATH for MP4s) and
reached only lazily -- with no backend the savers raise a clear
`OptionalDependencyError` instead of failing at import. Every number is pulled
from the **real pure core** (`multiverse` -> `curve` -> `portal_gun` ->
`projection`), never fabricated.

### 1. Portal-gun walk (`adapters/animate.py`)

The classic 2-D scatter of the curve with the portal-gun trajectory drawn in as
a growing trail. Artifacts: `central_finite_curve_walk.gif` (`.mp4`).

### 2. Four-panel explainer (`adapters/animate_panels.py`)

A 2x2 composite on a shared frame timeline, ending on a HOLD-frame summary
banner. `save_cfc_four_panels_gif` / `_mp4` share one `_build` builder:

* **Panel 1 -- "Multiverse, Rickness-scored":** the top-2 PCA projection of the
  whole multiverse cloud, coloured by core Rickness.
* **Panel 2 -- "Central Finite Curve = near-maximal band":** the same projection
  with the epsilon-band subset highlighted vs the rest, plus a readout of the
  curve size and its share of `N`.
* **Panel 3 -- "Portal gun walks the curve":** the Metropolis walk animated step
  by step (frame `k` = step `k`), never leaving the band, with the acceptance
  ratio in the title.
* **Panel 4 -- "Rickness distribution":** a histogram of Rickness across the
  multiverse with the epsilon band shaded as the near-max tail (the curve = the
  top band).

Artifacts: `central_finite_curve_four_panels.gif` (`.mp4`).

### 3. Rotating 3-D projection (`adapters/animate_3d.py`)

A 3-D scatter (`mpl_toolkits.mplot3d`) of the multiverse (faint) with the
near-maximal band highlighted and the portal-gun walk overlaid, while the
**camera orbits** (azimuth per frame + a gentle elevation sweep via
`ax.view_init`). It uses `core.projection.project_3d` -- a pure-stdlib
power-iteration PCA to three components whose first two axes match the 2-D
projection exactly, so the flat and depth views share one frame.
`save_cfc_rotating_gif` / `_mp4` share one builder.

Artifacts: `central_finite_curve_rotating_3d.gif` (`.mp4`).

### Regenerating

```bash
# Walk + four-panel explainer + rotating 3-D (each GIF and, with --mp4, MP4):
python3 -m central_finite_curve.adapters.cli animate artifacts --panels --rotate --mp4
```

The repo-level `scripts/regenerate_artifacts.sh` runs exactly this (via the venv)
alongside the projection PNG.

---

## Sample output

With the default config (`D=8`, `N=20000`, `seed=137`, `eps_absolute=0.20`) the
curve is a thin ridge of ~1,385 universes (about 6.9% of the multiverse), and the
portal gun walks along it at ~22% acceptance -- sometimes stepping to a universe
*slightly more Rick* than any that was generated:

```
======================================================================
CENTRAL FINITE CURVE ENGINE
======================================================================
dimensions           : 8
universes generated  : 20000
seed                 : 137

-- Rickness landscape ------------------------------------------
max Rickness         : 1.5956
epsilon band width   : 0.2000
band lower bound     : 1.3956

-- Central Finite Curve ----------------------------------------
curve size (universes): 1385
fraction of multiverse: 6.925%
best universe coords : [1.5387, -1.2664, -1.0029, 1.9391, -1.9047, 1.9630, 0.5101, -2.6825]

-- Portal gun (constrained MCMC walk) --------------------------
walk steps           : 6000
acceptance rate      : 21.8%
trajectory length    : 6001 points
score range on walk  : 1.3957 .. 1.6376

-- ASCII projection (top-2 principal components) ---------------
+----------------------------------------------------------------------+
|                                      .                               |
|                                   .  .: .:..                         |
|                                ..::.. .:..--:-.                      |
|                             .    .::-:.- : -=:.:::.                  |
|                            .   . ...: .:.:- :--++=:- -...            |
|    @@@@@@@@@@@@        :  ..      . :. .: ..-: :--=%+-::..           |
|    @@@@@@@@@@@@@@. ..  .:. .  .   .  .    ..:::::-*-==*---:. ..      |
|    @@@    @@@    ..    . : ..:. ..  .   .:. .  :-==.-::==-:::::.     |
|  @@@@@@         ::.::--- :-:: ..: .        ....::=:..+=-::#=-:: .    |
|   @  @@@         ..:.:+:--.:=--:::::.:.. .      . :  :::..:::: : .   |
|@@@@@@@@@             ::==-+-+:-:::- .:   ...   .   : .: . ... :-::.: |
|  @@@                    -:= :===---:.::-. :   .  .   ..:::.:: .  ..:.|
|                         :::*-+=+%-::::::- .:.    .  . .  .     :     |
|                             :.::++=-=:--:- ::. :::.                  |
+----------------------------------------------------------------------+
legend:  ' ' empty   .:-=+*#% curve density   @ portal-gun walk
```

**Reading the picture:** the `.:-=+*#%` cloud is the curve's density in the top-2
principal-component plane (the ring/reciprocal constraints give it its shape), and
the `@` band is the portal-gun trajectory sliding *along* that ridge without ever
falling off it. Exact numbers vary with the seeded RNG algorithm but the shape --
a thin, near-maximal ridge walked by a constrained sampler -- is reproducible from
`(config, seed)` alone.

---

## Tuning

Everything lives on the frozen `CurveConfig` (`core/config.py`); functions thread
an explicit config, defaulting to `DEFAULT`:

* `dim`, `n_universes`, `seed` -- size and reproducibility.
* `eps_absolute` -- ridge thickness (smaller = thinner curve).
* `proposal_sigma`, `walk_steps` -- portal-gun step size and length. Smaller sigma
  raises acceptance but travels more slowly along the ridge.
* `w_complexity`, `w_entropy`, `w_penalty` -- reshape the Rickness landscape.
* `near_manifold_fraction`, `box`, `ring_radius`, `jitter_sigma` -- multiverse
  geometry.
