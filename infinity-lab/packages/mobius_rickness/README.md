# mobius_rickness

**The Central Finite Curve as a real zero set.**

A pure, stdlib-only differential-geometry package that turns a *Rick & Morty*
conceit into honest mathematics: the "Central Finite Curve" (the one arc of
realities where a Rick exists) is realised as the exact zero set `R^{-1}(0)` of a
sign-changing scalar field layered on the Gaussian curvature of a Möbius strip.

Because the Möbius strip is a **ruled** surface, its Gaussian curvature `K` is
**strictly negative** on the interior. Multiplying by a nowhere-vanishing `K`
leaves the zero set of the weighting `R` unchanged, so the weighted field

```
K_Rick(u, v) = K(u, v) * R(u, v) = 0   <=>   R(u, v) = 0
```

vanishes *exactly* on the curve `R^{-1}(0)`. That curve is the Central Finite
Curve — a genuine 1-D locus separating the "Rick-positive" from the
"Rick-negative" universes on the band.

The torus is the non-ruled counterpoint: its curvature changes sign on its own,
so its zero set (`theta = pi/2, 3pi/2`) needs no weighting at all — pure geometry.

---

## Two formalizations of the Central Finite Curve

"The one curve on which a Rick exists" admits **two mathematically distinct
readings**, and this package ships both:

1. **The zero-set wall — `R^{-1}(0)`** (pure `core/`, always available). The
   Central Finite Curve is the **boundary** where the sign-changing Rickness
   field vanishes: `K_Rick(u,v) = K(u,v)·R(u,v) = 0 ⇔ R(u,v) = 0`. It separates
   the "Rick-positive" from the "Rick-negative" universes — the frontier of the
   set of realities with a Rick. Traced exactly by `core/tracer.py`
   (scan-line bisection + marching squares); every point has `|R| < 1e-6`.

2. **The SCMS / Eberly height-ridge — the crest of maximal Rickness**
   (`mobius_rickness.ridge`, optional numpy). Here the Central Finite Curve is
   read as the **1-D ridge** where Rickness is locally *maximal transverse to the
   curve* — the "spine" of the most-Rick realities, not their boundary. It is
   defined by the Subspace-Constrained Mean-Shift / Eberly condition on the field
   `R`: at a ridge point the gradient is orthogonal to the minor Hessian
   eigenvector and that eigenvalue is negative (`|g·e_minor| < tol` **and**
   `λ_minor < 0`). Computed via `numpy.linalg.eigh` with a Newton transverse
   projection `t = -(g·e_minor)/λ_minor`.

The two are **genuinely different curves**: the ridge sits emphatically *off* the
zero wall (traced ridge points have `|R| ∈ [0.60, 1.15]`, mean `|R| > 0.5`, while
the zero set has `|R| < 1e-6`). The `mobius_ridge.png` artifact overlays the SCMS
ridge; `mobius_strip_curve.png` overlays the `R^{-1}(0)` wall — so the contrast is
visible side by side.

---

## Layout & purity

```
src/mobius_rickness/
├── core/            # pure: stdlib + commons.core ONLY (no adapters, no numpy/matplotlib)
│   ├── geometry.py  # fundamental forms E,F,G,L,M,N + 3 curvature paths + Möbius seam wrap
│   ├── mobius.py    # Möbius parametrization; K = -1/(4 E**2) < 0 strictly
│   ├── rickness.py  # sign-changing Rickness field R(u,v) (+ legacy naive weighting)
│   ├── field.py     # K_Rick = K*R grid + strict-negativity certificate
│   ├── tracer.py    # real zero-set tracing (scan-line bisection + marching squares)
│   └── torus.py     # ring torus; closed-form K sign-changing, zero at pi/2 & 3pi/2
├── accel/           # OPTIONAL numpy fast paths (lazy try_import; outside core)
│   └── numpy_backend.py  # vectorised curvature / rickness / K_Rick / surface meshes
├── ridge/           # OPTIONAL numpy SCMS/Eberly ridge (lazy; the 2nd CFC formalization)
│   └── scms.py      # gradient/Hessian, eigen-split, height-ridge trace + convergence history
└── adapters/        # import core, NEVER the reverse
    ├── viz.py            # ASCII sign map, K_Rick heatmap, curvature table (matplotlib deferred)
    ├── animate_3d.py     # rotating 3-D GIF/MP4 of the strip + both CFC readings (deferred)
    ├── animate_scms.py   # 2-D GIF/MP4 of the SCMS seed cloud converging onto the ridge (deferred)
    └── cli.py            # argparse subcommands: curvature / trace / torus / all / animate
```

**Core purity invariant** (enforced by `tests/test_mr_core_purity.py`): every
module under `core/` imports only the standard library and `commons.core`. No core
module imports an adapter, and nothing anywhere imports `numpy`/`matplotlib` at
module top level — the optional 3D PNG path is deferred behind
`commons.core.optional.try_import` and raises `OptionalDependencyError` when
matplotlib is absent, never a hard import.

---

## The resolved math, per module

### `geometry.py` — the surface-agnostic engine
Computes the first/second fundamental forms of any smooth `r(u, v) -> (x, y, z)`
and `K = (L*N - M**2) / (E*G - F**2)` via **three independent, cross-validating
paths**:

- **(a) analytic oracle** — closed form `K = -1/(4 E**2)` with
  `E = (1 + v cos(u/2))**2 + v**2/4`.
- **(b) central finite differences** — built on `commons.core.numerics.central_difference`.
- **(c) complex-step** — cancellation-free first derivatives via
  `commons.core.numerics.complex_step_derivative`.

The Möbius **seam v-flip** `r(2pi, v) = r(0, -v)` is load-bearing: any periodic
stencil sampling a neighbour outside `[0, 2pi]` wraps `u` modulo `2pi` *and* flips
`v` for an odd number of wraps (`mobius_seam_wrap`). Ordinary surfaces (the torus)
use `identity_wrap`.

### `mobius.py` — strictly negative curvature
Parametrization `r(u,v) = ((1 + v cos(u/2)) cos u, (1 + v cos(u/2)) sin u, v sin(u/2))`,
`u in [0, 2pi]`, `v in [-0.5, 0.5]`. The strip is ruled (`r_vv = 0`) and
`M = -1/(2 sqrt(E))` never vanishes, so `K = -1/(4 E**2) < 0` strictly on the
interior. The three curvature paths agree to `< 1e-8`.

### `rickness.py` — the sign-changing field
```
R(u, v) = cos(u) + 0.4 v cos(u/2) + 0.2 sin(u)
```
Respects the seam constraint `R(0, -v) = R(2pi, v)`, so its zero set is a
*continuous* curve on the band. For fixed `u` the field is affine in `v`
(`R = A(u) + B(u) v`), giving an exact per-column root `v* = -A/B` that never
depends on grid resolution. The legacy `rickness_naive` (with a `+1.5` constant,
always `> 0`) is retained to document why the earlier design had **no** genuine
zero.

### `field.py` — the weighted field & certificate
Provides the sampled `K_Rick = K * R` grid and the strict-negativity certificate
for `K`. Since `K < 0` everywhere, the `K_Rick` grid **straddles zero** iff `R`
does, and the zero set is exactly `R^{-1}(0)`.

### `tracer.py` — real zero-set tracing
Two complementary, cross-checking paths (stdlib + `commons.core` only):
- **scan-line bisection** — per `u`-column sign scan + `bisection` refine to `1e-9`.
- **marching squares** — 16-case contour extraction, each edge crossing refined by
  bisection, segments stitched into ordered polylines across the Möbius seam.

Every traced point satisfies `|R| < 1e-6` and `|K_Rick| < 1e-6` (`verify_curve`).
The torus zero circles are located by the same bisection machinery.

### `torus.py` — the geometry-driven counterpoint
Ring torus `K(theta) = cos(theta) / (r0 (R0 + r0 cos theta))`: positive outer
half, negative inner half, **zero exactly at `theta = pi/2` and `3pi/2`**. Numeric
`K` (via the shared central-difference engine) matches the closed form, and
`require_ring` fails fast on `R0 <= r0` (self-intersecting, singular `K`).

---

## Running it (offline, zero install, zero network)

Imports resolve via the repo's `[tool.pytest.ini_options] pythonpath` — no
editable install needed. From the repo root `infinity-lab/`:

```bash
# Full package test suite
python3 -m pytest packages/mobius_rickness

# Demo (headline math + reproduced table + traced curve + torus + ASCII gallery)
PYTHONPATH=packages/commons/src:packages/mobius_rickness/src \
  python3 -m mobius_rickness.demo

# CLI subcommands: curvature | trace | torus | all  (--ascii on curvature/trace/all)
PYTHONPATH=packages/commons/src:packages/mobius_rickness/src \
  python3 -m mobius_rickness.adapters.cli all
```

Requires Python 3.11+. `numpy`/`matplotlib` are optional (only for the deferred 3D
PNG export, the numpy fast paths, and the SCMS ridge) and are **not** needed for
anything above.

---

## Optional acceleration & visualization

The core is stdlib-only. Three **optional** capabilities live *outside* `core/`
and reach `numpy` / `matplotlib` lazily via `commons.core.optional.try_import` —
never a top-level import, so `core/` purity is untouched:

- **`mobius_rickness.accel.numpy_backend`** — vectorised numpy fast paths mirroring
  the exact core: `curvature_fd_mesh` (seam-aware central-difference `K`),
  `curvature_analytic_mesh`, `rickness_mesh`, `k_rick_mesh` (`= K·R`), and
  `mobius_surface_mesh` (3D point cloud). Parity against the core is **bit-exact**
  (analytic `K`, `R`, `K_Rick`, surface: max abs diff `0.0`; the FD mixed partial
  replicates the core's *nested* central-difference grouping to stay bit-exact).
- **`mobius_rickness.ridge.scms`** — the SCMS / Eberly ridge (the **second** CFC
  formalization above), via `numpy.linalg.eigh`. Entry point
  `trace_mobius_ridge()`; on the stdlib-only interpreter it imports fine but
  raises `OptionalDependencyError` when called (numpy reached only inside functions).
- **matplotlib PNG exports** in `adapters/viz.py` — `save_strip_3d_png`
  (surface + `R^{-1}(0)` wall), `save_krick_heatmap_png` (`K_Rick` field + zero
  contour), `save_ridge_png` (surface + SCMS ridge), all headless (`Agg`).

All are absent from the stdlib-only interpreter's requirements: their tests
`pytest.importorskip("numpy")` / `importorskip("matplotlib")` and simply **skip**.

### Create the venv and run the optional tests

```bash
# From the repo root
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install numpy matplotlib pytest

# Optional accel + ridge + PNG tests RUN on the venv interpreter
.venv/bin/python -m pytest packages/mobius_rickness -q

# On the stdlib-only system interpreter they SKIP (the 70 core tests stay green)
python3 -m pytest packages/mobius_rickness -q
```

### Generate the PNGs

```bash
# Via the CLI adapter (writes the three PNGs into OUTDIR)
PYTHONPATH=packages/commons/src:packages/mobius_rickness/src \
  .venv/bin/python -m mobius_rickness.adapters.cli all --png artifacts

# Or directly (repo-root sample deliverables)
PYTHONPATH=packages/commons/src:packages/mobius_rickness/src \
  .venv/bin/python -c '
from mobius_rickness.adapters.viz import save_strip_3d_png, save_krick_heatmap_png, save_ridge_png
save_strip_3d_png("artifacts/mobius_strip_curve.png")
save_krick_heatmap_png("artifacts/mobius_krick_heatmap.png")
save_ridge_png("artifacts/mobius_ridge.png")'
```

Sample outputs are committed at the repo root under
[`artifacts/`](../../artifacts/) (`mobius_strip_curve.png`,
`mobius_krick_heatmap.png`, `mobius_ridge.png`).

### Animations — rotating 3-D GIF + MP4

`adapters/animate_3d.py` renders the Möbius strip as a **rotating 3-D animation**
that puts **both Central Finite Curve readings on one orbiting scene**: the
semi-transparent strip surface carries the traced zero-set wall `R^{-1}(0)` (red)
**and** the SCMS ridge of maximal Rickness (orange), while an orbiting camera
advances its azimuth per frame and sweeps its elevation (`ax.view_init`), so the
contrast between the two curves is visible from every angle.

- `save_mobius_rotating_gif(path)` — `FuncAnimation` + `PillowWriter` (needs
  matplotlib **and** Pillow).
- `save_mobius_rotating_mp4(path)` — the **same** scene through `FFMpegWriter`
  (needs matplotlib **and** an `ffmpeg` binary on `PATH`). Both share one
  `_build_rotating_animation` builder.

Both are **deferred**: with matplotlib/Pillow absent the GIF saver raises
`OptionalDependencyError` rather than importing at module top level. The MP4 saver
detects ffmpeg at call time (`shutil.which("ffmpeg")` **and** matplotlib's
registered `ffmpeg` writer) and fails fast with `OptionalDependencyError` when it
is missing — ffmpeg is never a hard requirement. The ridge overlay itself
**degrades gracefully**: when numpy (or the ridge subpackage) is unavailable the
strip and the `R^{-1}(0)` zero curve still render and the ridge is simply omitted.

**ffmpeg note:** matplotlib's `FFMpegWriter` shells out to an `ffmpeg` binary on
`PATH` (e.g. `brew install ffmpeg`). Without it, use the GIF (Pillow only).

Regenerate the sample artifacts (rotating GIF + MP4) into the repo-root
`artifacts/`:

```bash
# Via the CLI: writes mobius_rotating.gif, and with --mp4 also mobius_rotating.mp4
PYTHONPATH=packages/commons/src:packages/mobius_rickness/src \
  .venv/bin/python -m mobius_rickness.adapters.cli animate artifacts --mp4

# Or directly
PYTHONPATH=packages/commons/src:packages/mobius_rickness/src \
  .venv/bin/python -c '
from mobius_rickness.adapters.animate_3d import save_mobius_rotating_gif, save_mobius_rotating_mp4
save_mobius_rotating_gif("artifacts/mobius_rotating.gif")
save_mobius_rotating_mp4("artifacts/mobius_rotating.mp4")'
```

Sample outputs are committed at the repo root under
[`artifacts/`](../../artifacts/) (`mobius_rotating.gif` — GIF89a; and
`mobius_rotating.mp4` — ISO-BMFF `ftyp`, decodes cleanly under
`ffmpeg -v error -i mobius_rotating.mp4 -f null -`).

### Animations — SCMS ridge convergence (the extractor's *process*)

Where the rotating scene orbits the *finished* curves, `adapters/animate_scms.py`
animates **how the SCMS / Eberly ridge is found**: a cloud of scattered seed points
migrates, **one Subspace-Constrained-Mean-Shift step per frame**, until it settles
onto the crest of maximal Rickness. Each frame is a 2-D `(u, v)` scene — a faint
`R(u, v)` backdrop with the zero curve `R^{-1}(0)` as a black reference contour and
the converged ridge as faint orange `×` marks — and the **frame title reports the
iteration index and the mean ridge-condition residual** `mean_i |∇R·e_minor|`
shrinking toward `0`.

The migration/residual data comes from two history variants added to
`ridge/scms.py` (both numpy-backed, additive, sharing the exact single-SCMS-step
logic of `scms_point`/`scms_ridge`):

- `scms_ridge_history(field, seeds, …) -> RidgeConvergence` — advances **all** seeds
  together and records, per iteration, the whole-cloud `(n_seeds, 2)` snapshot, the
  mean residual, and the final per-seed `RidgePoint` (a seed frozen once it reaches
  the ridge, so its final position matches the independent `scms_ridge`).
- `scms_point_history(field, u0, v0, …) -> list[(u, v)]` — the full `(u, v)`
  trajectory a single seed walks onto the ridge.

Over the Möbius Rickness field the mean residual falls from **≈3.3e-1 to ≈3.0e-9**
across 29 iterations (110 seeds), e.g.
`3.32e-01 → 2.16e-01 → 1.22e-01 → … → 9.85e-07 → 4.47e-08 → 3.00e-09` (it trends
monotonically down; the seed cloud can overshoot slightly before Newton's quadratic
tail collapses the residual to ~0). On a near-quadratic field it is monotone
throughout.

- `save_ridge_convergence_gif(path)` — `FuncAnimation` + `PillowWriter` (needs
  matplotlib **and** Pillow).
- `save_ridge_convergence_mp4(path)` — the **same** scene through `FFMpegWriter`
  (needs matplotlib **and** an `ffmpeg` binary on `PATH`). Both share one
  `_build_convergence_animation` builder, and the MP4 saver fails fast with
  `OptionalDependencyError` (via `shutil.which` + matplotlib's registered writer)
  when ffmpeg is absent — never a hard requirement.

Regenerate the sample artifacts into the repo-root `artifacts/`:

```bash
# Via the CLI: `--scms` adds mobius_ridge_convergence.gif; with --mp4 also the .mp4
PYTHONPATH=packages/commons/src:packages/mobius_rickness/src \
  .venv/bin/python -m mobius_rickness.adapters.cli animate artifacts --scms --mp4

# Or directly
PYTHONPATH=packages/commons/src:packages/mobius_rickness/src \
  .venv/bin/python -c '
from mobius_rickness.adapters.animate_scms import save_ridge_convergence_gif, save_ridge_convergence_mp4
save_ridge_convergence_gif("artifacts/mobius_ridge_convergence.gif")
save_ridge_convergence_mp4("artifacts/mobius_ridge_convergence.mp4")'
```

Sample outputs are committed under [`artifacts/`](../../artifacts/)
(`mobius_ridge_convergence.gif` — GIF89a; and `mobius_ridge_convergence.mp4` —
ISO-BMFF `ftyp`, decodes cleanly under
`ffmpeg -v error -i mobius_ridge_convergence.mp4 -f null -`).

---

### Animations — four-panel explainer (the whole story on one timeline)

`adapters/animate_panels.py` renders **one composite 2×2 animation** that tells the
entire Mobius-Rickness / Central Finite Curve story on a shared frame timeline (a
suptitle over four panels), ending on a **HOLD frame** that reveals a summary
banner. Every number is pulled from the **real pure core** — nothing is fabricated.

- **Panel 1 — “Mobius strip: ruled ⇒ K < 0”.** A heatmap of the Gaussian curvature
  `K(u, v)` (from `evaluate_grid`) with a **scan line sweeping `u`**. `K` is strictly
  negative on the whole interior (`assert_mobius_K_negative`); a per-frame readout
  confirms the three curvature paths agree — `analytic` (`gaussian_curvature`), `fd`
  (`gaussian_curvature_numeric`), `cs` (`gaussian_curvature_complex_step`) — via
  `max|analytic − numeric|`.
- **Panel 2 — “Central Finite Curve = R⁻¹(0)”.** Over a faint sign-map of the
  sign-changing Rickness `R(u, v)`, the traced zero set (`trace_columns` →
  `flatten_columns`) is **drawn in point-by-point** across frames: the boundary
  between the Rick-positive and Rick-negative regions.
- **Panel 3 — “Second reading: SCMS ridge (crest of max Rickness)”.** The SCMS seed
  cloud converges onto the Eberly ridge (frame `k` = SCMS iteration `k`, from
  `ridge/scms.py`’s `scms_ridge_history`), with the mean residual
  `mean_i |∇R·e_minor|` shrinking toward `0` in the panel title.
- **Panel 4 — “Torus: non-ruled ⇒ K changes sign”.** The closed-form
  `K(θ) = cos θ / (r0 (R0 + r0 cos θ))` curve (`gaussian_curvature_closed`) with a
  scan line sweeping `θ`, marking the sign pattern (`+` outer / `−` inner) and the
  `K = 0` circles at `θ = π/2, 3π/2` (`zero_circles`).

- `save_four_panels_gif(path)` — `FuncAnimation` + `PillowWriter` (needs matplotlib
  **and** Pillow **and** numpy).
- `save_four_panels_mp4(path)` — the **same** scene through `FFMpegWriter` (needs
  matplotlib **and** numpy **and** an `ffmpeg` binary on `PATH`). Both share one
  `_build_four_panel_animation` builder; Panels 1/2/4 are assembled by the pure
  `four_panel_frame_data` (stdlib + core only), and the MP4 saver fails fast with
  `OptionalDependencyError` when ffmpeg is absent.

Regenerate the sample artifacts into the repo-root `artifacts/`:

```bash
# Via the CLI: `--panels` adds mobius_four_panels.gif; with --mp4 also the .mp4
PYTHONPATH=packages/commons/src:packages/mobius_rickness/src \
  .venv/bin/python -m mobius_rickness.adapters.cli animate artifacts --panels --mp4

# Or directly
PYTHONPATH=packages/commons/src:packages/mobius_rickness/src \
  .venv/bin/python -c '
from mobius_rickness.adapters.animate_panels import save_four_panels_gif, save_four_panels_mp4
save_four_panels_gif("artifacts/mobius_four_panels.gif")
save_four_panels_mp4("artifacts/mobius_four_panels.mp4")'
```

Sample outputs are committed under [`artifacts/`](../../artifacts/)
(`mobius_four_panels.gif` — GIF89a; and `mobius_four_panels.mp4` — ISO-BMFF `ftyp`,
decodes cleanly under `ffmpeg -v error -i mobius_four_panels.mp4 -f null -`).

---

## Verified headline targets

- `K < 0` strictly on the Möbius interior (worst/max `K = -0.055927`).
- Three curvature paths agree: `max |analytic - numeric| = 6.85e-09`.
- `R` changes sign — the sampled grid straddles 0 — so `K_Rick` grid straddles 0.
- Every traced curve point: `|R| < 1e-6` **and** `|K_Rick| < 1e-6`
  (11 zero points, all `|R| < 1.6e-10`).
- Torus numeric `K` matches the closed form and `K = 0` exactly at
  `theta = pi/2` & `3pi/2` (traced `1.570796, 4.712389`).

### Real sample output (demo headline)

```
MOBIUS-RICKNESS: THE CENTRAL FINITE CURVE AS A REAL ZERO SET

K<0 on the ruled Mobius strip, so K_Rick = K*R vanishes exactly where R vanishes.

======================================================================
CURVATURE -- Mobius strip: K < 0 strictly (ruled surface)
======================================================================
r(u,v) = ((1 + v cos(u/2)) cos u, (1 + v cos(u/2)) sin u, v sin(u/2))
K < 0 strictly on the interior (worst / max K = -0.055927).
Three curvature paths at (u,v)=(pi/3, 0.25): analytic=-0.111778891  fd=-0.111778898  cs=-0.111778891
max |analytic - numeric| = 6.85e-09  (paths agree).
```

Traced Central Finite Curve (`R^{-1}(0)`), real points:

```
         u          v          x          y          z        |R|
------------------------------------------------------------------
    1.6368    -0.4888    -0.0439    +0.6645    -0.3568    5.9e-11
    1.6896    -0.3015    -0.0948    +0.7942    -0.2255    1.5e-10
    ...
    5.0688    +0.4915    +0.2081    -0.5589    +0.2805    1.6e-11
```

Torus zero set (geometry-driven, no weighting):

```
       theta       K_closed      K_numeric   sign
--------------------------------------------------
  pi/2 (top)       0.000000       0.000000      0
 3pi/2 (bot)      -0.000000       0.000000      0
Traced K=0 circles at theta = 1.570796, 4.712389  (pi/2, 3pi/2)
```

The demo also prints the reproduced naive-Rickness curvature table and an ASCII
gallery (Rickness sign map with the traced zero curve overlaid as `O`, plus the
shaded `K_Rick` heatmap).

---

## Tests

Stdlib-only system interpreter: `python3 -m pytest packages/mobius_rickness -q`
→ **70 passed, 5 skipped** (the optional numpy accel, SCMS ridge, matplotlib PNG,
rotating-animation, and SCMS-convergence-animation modules skip); full monorepo
`python3 -m pytest -q` → **296 passed, 12 skipped**. All offline, no network, no
install.

Venv interpreter (numpy + matplotlib + ffmpeg): `.venv/bin/python -m pytest
packages/mobius_rickness -q` → **109 passed** (accel + ridge + PNG + rotating
GIF/MP4 + SCMS ridge-convergence GIF/MP4 tests run); full monorepo
`.venv/bin/python -m pytest -q` → **389 passed**.
