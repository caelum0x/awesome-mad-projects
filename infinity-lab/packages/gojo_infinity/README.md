# gojo_infinity

Gojo Satoru's **"Infinity"** (Jujutsu Kaisen) examined through four independent
mathematical lenses, after Achmad Roykhan Sabiq's Oxford Maths essay (2026) and
the RIKEN *"Jujutsu Kaisen: Abyss of Math"* course. Each lens asks the same
question -- *can an attacker ever reach Gojo?* -- and reaches its own verdict.

| Lens | Model | Verdict |
|------|-------|---------|
| 1 | Geometric series / Zeno's paradox | **Fragile** |
| 2 | Lebesgue measure | **Fragile** |
| 3 | Riemannian conformal geometry | **Formidable** |
| 4 | Topology / World-Cutting Slash | **Falls** |

The point of the exercise: *the answer depends entirely on the mathematics you
choose to model "Infinity" with.* Three of the four models say the barrier can
be crossed or is negligible; only the Riemannian reading makes it truly
impassable, and a topological cut removes the metric altogether.

## Package layout

```
src/gojo_infinity/
  core/            # PURE math -- stdlib + commons.core ONLY (never adapters)
    zeno.py        # Lens 1: partial sums, residuals, arrival time
    measure.py     # Lens 2: covering length, m(Z) = 0
    riemannian.py  # Lens 3: conformal metric, divergent geodesic (1-D)
    riemannian_manifold.py     # Lens 3 (2-D): real manifold geodesic solver
    riemannian_manifold_nd.py  # Lens 3 (n-D): dimension-agnostic solver (1/2/3-D)
    topology.py    # Lens 4: continuity, severed metric, connectivity
    verdicts.py    # frozen Verdict dataclass + conclusion table
  accel/           # OPTIONAL numpy fast paths (lazy try_import; outside core)
    numpy_backend.py     # vectorised omega/metric/geodesic/cover/zeno mirrors
    manifold_backend.py  # vectorised batch geodesic integrator (2-D + n-D)
  adapters/        # may import core; core NEVER imports these
    viz.py         # deterministic ASCII charts (+ DEFERRED matplotlib PNG, 3-D)
    animate.py     # DEFERRED matplotlib+Pillow GIFs + ffmpeg MP4 of the approach
    animate_3d.py  # DEFERRED rotating 3-D geodesic animation (GIF + ffmpeg MP4)
    animate_lenses.py # DEFERRED four-lens 2x2 composite explainer (GIF + ffmpeg MP4)
    cli.py         # argparse: zeno/measure/riemannian/manifold/topology/all/animate
  demo.py          # end-to-end narrated report (headline + lenses + gallery)
tests/             # pytest suite (pure core tests + optional accel/PNG/GIF tests)
```

**Core purity** is a hard invariant and is enforced by
`tests/test_gojo_core_purity.py`: modules under `core/` import only the standard
library plus `commons.core`. No core module imports an adapter (`cli`/`viz`/`io`),
and nothing imports `numpy`/`matplotlib` at module top level. matplotlib is
reached only lazily inside `adapters/viz.save_convergence_png` via
`commons.core.optional.try_import` and is **deferred** -- absent it, the function
raises a clear `OptionalDependencyError` instead of failing to import.

## The resolved mathematics, per lens

### Lens 1 -- Geometric series (Zeno) -> Fragile
The attacker halves the remaining gap forever. Partial sums are computed
**exactly** with `fractions.Fraction`:

```
S_n = 1/2 + 1/4 + ... + 1/2^n = 1 - (1/2)^n
S_1..S_8 = 1/2, 3/4, 7/8, 15/16, 31/32, 63/64, 127/128, 255/256
         = 0.5, 0.75, 0.875, 0.9375, 0.96875, 0.984375, 0.9921875, 0.99609375
```

The residual `(1/2)^n` is **strictly positive for every finite n** (verified up
to and beyond `half_power(1075)`, where an IEEE-754 double would underflow to
`0.0` -- Fraction does not). Yet the geometric sum `a/(1-r)` with `a = r = 1/2`
equals **exactly `1`**, and the total arrival time at speed `1/2` is the finite
value `2`. The attacker arrives: Infinity is **Fragile**.

### Lens 2 -- Lebesgue measure -> Fragile
The subdivision points `Z = { z_n = 1 - 1/2^n } = {1/2, 3/4, 7/8, ...}` form a
countably infinite set. Cover `z_n` by an interval of width `eps/2^n`; the total
length telescopes:

```
sum_{n>=1} eps/2^n = eps * sum_{n>=1} 1/2^n = eps * 1 = eps   (exact, Fraction)
```

So the full cover has length **exactly `eps`** (`outer_measure_upper_bound(eps)
== eps`), and the finite-term partials rise toward it with tail `eps/2^terms -> 0`.
Since `eps > 0` is arbitrary, the infimum -- hence `m(Z)` -- is **`0`**. The
barrier is a null set of total length zero: **Fragile**.

### Lens 3 -- Riemannian conformal geometry -> Formidable
Space near Gojo carries a conformal metric `ds = Omega(x) dx`, `g11 = Omega(x)^2`,
with the RIKEN Gaussian (RBF) kernel:

```
K(x, y) = exp(-|x - y|^2 / sigma^2)
Omega(x) = 1 + lambda * K(x, x_gojo) / (x_gojo - x),   x_gojo = 1
```

`lambda` is **derived, not hardcoded**: `calibrate()` fits it by bisection
(`commons.core.bisection`) so `g(0.8) = 4.1`, giving `sigma = 0.35`,
`lambda ~= 0.284118`. The far target is then verified: `g(0.1) ~= 1.0008 ~ 1.0`
with felt step `ds ~= 0.10`; near the pole `g(0.8) = 4.1000` with `ds ~= 0.20`.

The felt geodesic to the barrier is an **improper integral that diverges**:
`geodesic_to_barrier(x0)` returns the literal `math.inf` (never a large finite
approximation), because the integrand `~ lambda/(x_gojo - x)` has antiderivative
`-lambda*ln(x_gojo - x) -> +inf`. Each decade of approach adds
`lambda*ln(10) ~= 0.6542`. A `naive_geodesic_to_barrier` finite midpoint sum is
kept ONLY as a labelled "float fails here" demo. Every strike crosses infinite
felt distance: **Formidable**.

### Lens 3 (2-D) -- Riemannian manifold geodesics -> Formidable (enhancement)
An **enhancement beyond the essay's 1-D treatment** (`core/riemannian_manifold.py`):
a genuine two-dimensional, conformally flat Riemannian manifold around Gojo, with
a real geodesic solver. Gojo sits at the **origin** of `R^2`; for the radial
distance `d = |x - g|` the conformal factor is the 2-D radial version of the same
RIKEN kernel, `sigma` and `lambda`:

```
Omega(x) = 1 + lambda * exp(-d^2/sigma^2) / d
g_ij(x)  = Omega(x)^2 * delta_ij          (2x2, symmetric, positive-definite)
```

With `phi = ln(Omega)`, a conformal metric `g_ij = e^{2 phi} delta_ij` has the
closed-form Christoffel symbols `Gamma^k_ij = d^k_i d_j phi + d^k_j d_i phi -
delta_ij d^k phi`, so the geodesic equation collapses to

```
x'' = |x'|^2 grad(phi) - 2 (grad(phi) . x') x'
```

integrated by fixed-step **RK4** (`integrate_geodesic`). `grad(phi)` is analytic.
The results, all machine-checked in `tests/test_riemannian_manifold.py`:

- **Christoffel cross-check.** `christoffel_conformal` (closed form) matches
  `christoffel_general` (the standard `1/2 g^{kl}(d_i g_jl + d_j g_il - d_l g_ij)`
  from finite differences of the metric) to **max diff ~ 2.6e-10** across sampled
  points -- the closed form is correct.
- **Affine invariant.** The metric energy `Omega(x)^2 |v|^2` is conserved along an
  integrated geodesic to a **relative drift ~ 2.7e-15** (a strong ODE check).
- **Flat-region sanity.** Far from Gojo (`Omega ~ 1`) a geodesic is straight:
  turning angle `< 1e-6`, direction preserved.
- **Parity with the 1-D lens.** A purely radial approach reproduces the existing
  1-D `geodesic_length` **exactly** (felt length `0.918122` vs `0.918122`,
  `|diff| ~ 3.6e-13`) and stays radial with **zero tangential drift** -- because
  the 1-D `gap = x_g - x` equals the radial distance, the two models coincide on
  rays.
- **Divergence (FORMIDABLE).** The felt length to reach within `delta` of Gojo is
  monotone and unbounded (`felt_length_to_reach`), climbing by `lambda*ln 10 ~
  0.6542` per decade:

  ```
   delta    felt length
  1e-01      1.085273
  1e-02      1.818231
  1e-03      2.481322
  1e-04      3.136427
  1e-06      4.444938
  ```

- **Deflection (light-bending analog).** A grazing ray (impact parameter `0.5`)
  **bends toward Gojo** by `-0.8176 rad` (final `v_y < 0`) -- higher `Omega` near
  the barrier acts like a denser optical medium.

An optional numpy **batch integrator** (`accel/manifold_backend.py`) advances many
geodesics at once and is parity-tested against the pure solver; `adapters/viz.py`
renders the geodesic bundle and the length-divergence curve as PNGs.

### Lens 3 (3-D) -- n-D geodesics + the planarity symmetry -> Formidable

The conformal geodesic mathematics is **dimension-agnostic**: for
`g_ij = Omega(x)^2 delta_ij` with `phi = ln Omega`, the Christoffel symbols and
the geodesic right-hand side are the SAME closed forms in every dimension:

```
Gamma^k_ij = d^k_i d_j phi + d^k_j d_i phi - delta_ij d^k phi
x'' = |x'|^2 grad(phi) - 2 (grad(phi) . x') x'
```

`core/riemannian_manifold_nd.py` (`ConformalMetricND`) generalises the solver to
operate on `n`-vectors (plain tuples of length `n`), so the **same code serves
1-D, 2-D and 3-D** — the dimension is inferred from `len(gojo)` (default: the
origin of `R^3`). There is exactly **one** copy of the geodesic RHS
(`conformal_acceleration`): the legacy 2-D `ConformalMetric.geodesic_rhs`
delegates to it, so 2-D behaviour is unchanged and backward compatible. Gojo
re-uses the SAME `sigma ~ 0.35`, `lambda ~ 0.284` and `Omega(x) = 1 +
lambda*exp(-d^2/sigma^2)/d` as the 1-D/2-D lenses. All machine-checked in
`tests/test_riemannian_manifold_3d.py`:

- **Christoffel cross-check (3-D).** `christoffel_conformal` matches
  `christoffel_general` (finite differences of `g_ij`) to **max diff ~ 1.4e-10**.
- **Affine invariant (3-D).** `Omega(x)^2 |v|^2` is conserved along a 3-D geodesic
  to a **relative drift ~ 5.3e-15**.
- **Radial parity.** A purely radial 3-D approach reproduces the 1-D lens felt
  length **exactly** (`0.918122` vs `0.918122`, `|diff| ~ 3.6e-13`) and stays on
  the axis with zero off-axis drift.
- **Planarity (the key 3-D symmetry).** A 3-D geodesic stays inside the 2-plane
  spanned by its initial position, initial velocity and Gojo — because both
  `grad(phi)` (radial) and `x'` lie in that plane, so it is invariant. The
  out-of-plane component (position dotted with the plane's unit normal) stays
  **< 1.1e-14** along the whole trajectory (`orbital_plane_normal` /
  `max_out_of_plane_drift`).
- **Deflection (3-D light-bending).** A grazing 3-D ray bends TOWARD Gojo by a
  turning angle of **~ 0.128 rad**, its final velocity tilting inward.
- **Divergence.** The radial felt length to within `delta` of Gojo is monotone and
  unbounded in 3-D too (same `lambda*ln 10` per-decade tail). Formidable.

The n-D numpy **batch integrator** `accel.manifold_backend.integrate_geodesics_batch_nd`
advances many 3-D (or any-`D`) geodesics at once and is parity-tested against the
pure n-D solver (`tests/test_manifold_accel_parity_3d.py`).
`adapters/viz.save_geodesic_3d_png` renders a bundle of 3-D geodesics bending
around Gojo (`mpl_toolkits.mplot3d`) to `artifacts/gojo_geodesic_3d.png`.

### Lens 4 -- Topology / World-Cutting Slash -> Falls
The intact metric factor is continuous across the domain (oscillation -> 0). The
**severed** factor is undefined at the cut `c = 0.5`, so `continuity_at` reports
`continuous = False` -- the continuity check FAILS after the cut. The geodesic
integral across the cut is therefore `None` (`severed_geodesic_length` --
**undefined**, distinct from both `math.inf` and any finite length). And the
domain `[x0, x1] \ {c}` splits into **exactly 2 connected components**
`[(0.1, 0.5), (0.5, 0.9)]`. The cut crosses no distance; it tears continuity.
Infinity **Falls**.

## Running

Everything runs **offline** -- no network, no `pip install`. Imports resolve via
the repo's `[tool.pytest.ini_options] pythonpath` (pytest) or an explicit
`PYTHONPATH` (scripts). Requires Python 3.11+ and the standard library only.

Run the full package test suite from the repo root
(`/Users/arhansubasi/mad-man-projects/infinity-lab`):

```bash
python -m pytest packages/gojo_infinity
```

Run the narrated demo end-to-end:

```bash
PYTHONPATH=packages/commons/src:packages/gojo_infinity/src \
  python -m gojo_infinity.demo
```

Run individual lenses via the CLI adapter (`zeno`, `measure`, `riemannian`,
`topology`, `all`; add `--ascii` for charts):

```bash
PYTHONPATH=packages/commons/src:packages/gojo_infinity/src \
  python -m gojo_infinity.adapters.cli all --ascii
```

## Optional acceleration & visualization

The core is stdlib-only. Two **optional** capabilities live *outside* `core/` and
reach `numpy` / `matplotlib` lazily via `commons.core.optional.try_import` — never
a top-level import, so `core/` purity is untouched:

- **`gojo_infinity.accel.numpy_backend`** — vectorised numpy fast paths that
  mirror the exact stdlib core (`omega_values`, `metric_g11_values`,
  `felt_ds_values`, `geodesic_partial_length` / `_midpoint`, `cover_interval_lengths`,
  `zeno_partial_sums`, `zeno_residuals`). Parity is asserted against the core:
  the dyadic cover/Zeno mirrors are **bit-identical**, and the exp/quadrature
  paths agree to **0–2 ULP**.
- **`gojo_infinity.accel.manifold_backend`** — a vectorised **batch 2-D geodesic
  integrator** (`integrate_geodesics_batch`) that advances many initial
  conditions at once with the same RK4 scheme; parity-tested against the pure
  `ConformalMetric.integrate_geodesic` to a few ULP.
- **matplotlib PNG exports** in `adapters/viz.py` — `save_metric_blowup_png`
  (Lens 3), `save_series_convergence_png` (Lens 1), `save_covering_png` (Lens 2),
  plus the 2-D `save_geodesic_bundle_png` (geodesics bending around Gojo),
  `save_length_divergence_png` (felt length vs `delta`), and the 3-D
  `save_geodesic_3d_png` (a bundle of geodesics bending around Gojo in `R^3`, via
  `mpl_toolkits.mplot3d`), all headless (`Agg`). Without matplotlib each raises
  `OptionalDependencyError`.
- **animated GIF exports** in `adapters/animate.py` (matplotlib
  `FuncAnimation` + `PillowWriter`, so they need **matplotlib AND Pillow**) —
  `save_geodesic_approach_gif` (a geodesic travelling and bending around Gojo,
  visibly slowing as its on-frame felt length climbs) and
  `save_never_arrives_gif` (an attacker's Zeno steps `x_n = 1 - (1/2)^n`
  asymptotically approaching Gojo at `x = 1`, residual `(1/2)^n > 0` forever while
  the felt length diverges). Absent either dependency each raises
  `OptionalDependencyError`.
- **rotating 3-D GIF** in `adapters/animate_3d.py` —
  `save_geodesic_3d_rotating_gif` renders a few conformal geodesics bending around
  Gojo in `R^3` (via `ConformalMetricND`, `mpl_toolkits.mplot3d`) while the
  **camera orbits** the scene: the azimuth advances a few degrees each frame and
  the elevation sweeps gently (`ax.view_init` per frame), so the viewer flies
  around the geodesics as they progress. Needs **matplotlib AND Pillow**; absent
  either it raises `OptionalDependencyError`.
- **four-lens composite explainer** in `adapters/animate_lenses.py` —
  `save_four_lenses_gif` / `save_four_lenses_mp4` render ONE animation that tells
  the essay's whole arc: all **four lenses** animate together on a 2x2 grid of
  subplots over a shared frame timeline (built by one
  `_build_four_lens_animation`), under a suptitle, and end on a **hold frame**
  showing the verdict table `Fragile / Fragile / Formidable / Falls`. Each panel
  draws its lens from the REAL pure core:
  - **Panel 1 — Geometric series (Zeno) → FRAGILE:** the partial sums
    `S_n = 1 - (1/2)^n` (from `core.partial_sum`) fill toward the dashed limit at
    `1` as the frame index advances `n`.
  - **Panel 2 — Lebesgue measure → FRAGILE:** the covering intervals `I_n` around
    the points `z_n = 1 - 1/2^n` (`core.subdivision_point`,
    `core.measure.cover_interval_length`) shrink as the budget `eps` decreases
    across frames, total-length label `= eps → 0`, illustrating `m(Z) = 0`.
  - **Panel 3 — Riemannian geometry → FORMIDABLE:** the conformal factor
    `Omega(x)` (`core.conformal_factor`) with a marker approaching Gojo (`x → 1`)
    frame by frame and a readout of the felt geodesic length
    (`core.geodesic_length`) climbing toward `+∞`.
  - **Panel 4 — Topology → FALLS:** `Omega(x)` shown continuous, then across
    frames a cut appears at `c` that severs continuity, splitting the domain into
    two connected components (`core.component_count` 1 → 2, "continuity
    destroyed").

  The numeric sequences are assembled by the pure `four_lens_frame_data`
  (stdlib + `core` only), so the panels are testable without any scientific
  dependency. Needs **matplotlib AND Pillow** (GIF) / **matplotlib AND ffmpeg**
  (MP4); absent a backend each raises `OptionalDependencyError`.
- **MP4 exports** via `matplotlib.animation.FFMpegWriter`, which shells out to an
  **ffmpeg** binary on `PATH` — `save_geodesic_approach_mp4` (the 2-D approach
  scene) and `save_geodesic_3d_rotating_mp4` (the rotating 3-D scene). They reuse
  the exact same `FuncAnimation` setups as the GIF savers (only the writer and
  extension differ), run at `fps = 20` with a reasonable bitrate, and detect
  ffmpeg at call time (`animate.ffmpeg_is_available()`, which probes
  `shutil.which("ffmpeg")` **and** matplotlib's registered writer). Absent
  matplotlib or ffmpeg each raises `OptionalDependencyError` (never a hard
  import-time requirement).

Both are absent from the stdlib-only interpreter's requirements: their tests
`pytest.importorskip("numpy")` / `importorskip("matplotlib")` and simply **skip**.

### Create the venv and run the optional tests

```bash
# From the repo root
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install numpy matplotlib pytest

# Optional accel + PNG tests RUN on the venv interpreter
.venv/bin/python -m pytest packages/gojo_infinity -q

# On the stdlib-only system interpreter they SKIP (core stays green)
python3 -m pytest packages/gojo_infinity -q
```

### Generate the PNGs

```bash
# Via the CLI adapter (writes one PNG per lens into OUTDIR)
PYTHONPATH=packages/commons/src:packages/gojo_infinity/src \
  .venv/bin/python -m gojo_infinity.adapters.cli all --png artifacts

# Or directly (repo-root sample deliverables)
PYTHONPATH=packages/commons/src:packages/gojo_infinity/src \
  .venv/bin/python -c '
from gojo_infinity.adapters.viz import save_metric_blowup_png, save_series_convergence_png
save_metric_blowup_png("artifacts/gojo_metric_blowup.png")
save_series_convergence_png("artifacts/gojo_series_convergence.png")'
```

The 2-D manifold charts are written by the `manifold` subcommand:

```bash
PYTHONPATH=packages/commons/src:packages/gojo_infinity/src \
  .venv/bin/python -m gojo_infinity.adapters.cli manifold --png artifacts
```

### Generate the 3-D PNG, the animated GIFs and the MP4s (via the venv)

The GIF animations need **matplotlib AND Pillow** (both in the `viz` extra plus
`pillow`); the MP4 exports additionally need an **ffmpeg** binary on `PATH`. All
render headless on the `Agg` backend. The `animate` subcommand writes the two
baseline GIFs into `OUTDIR` by default, `--rotate` adds the rotating 3-D GIF,
`--lenses` adds the four-lens composite explainer GIF, and `--mp4` adds the
approach, rotating-3-D and (with `--lenses`) four-lens MP4s:

```bash
# The two baseline approach GIFs into artifacts/
PYTHONPATH=packages/commons/src:packages/gojo_infinity/src \
  .venv/bin/python -m gojo_infinity.adapters.cli animate artifacts

# Also the rotating 3-D GIF, the four-lens explainer and every MP4
# (MP4s need ffmpeg on PATH)
PYTHONPATH=packages/commons/src:packages/gojo_infinity/src \
  .venv/bin/python -m gojo_infinity.adapters.cli animate artifacts --rotate --lenses --mp4

# Just the four-lens composite explainer (GIF + MP4), directly
PYTHONPATH=packages/commons/src:packages/gojo_infinity/src \
  .venv/bin/python -c '
from gojo_infinity.adapters.animate_lenses import (
    save_four_lenses_gif, save_four_lenses_mp4,
)
save_four_lenses_gif("artifacts/gojo_four_lenses.gif", frames=44, hold=8, fps=8)
save_four_lenses_mp4("artifacts/gojo_four_lenses.mp4", frames=44, hold=8, fps=8)'

# The 3-D bundle PNG and the animations directly (repo-root deliverables)
PYTHONPATH=packages/commons/src:packages/gojo_infinity/src \
  .venv/bin/python -c '
from gojo_infinity.adapters.viz import save_geodesic_3d_png
from gojo_infinity.adapters.animate import (
    save_geodesic_approach_gif, save_never_arrives_gif, save_geodesic_approach_mp4,
)
from gojo_infinity.adapters.animate_3d import (
    save_geodesic_3d_rotating_gif, save_geodesic_3d_rotating_mp4,
)
save_geodesic_3d_png("artifacts/gojo_geodesic_3d.png")
save_geodesic_approach_gif("artifacts/gojo_geodesic_approach.gif", frames=90, fps=20)
save_never_arrives_gif("artifacts/gojo_never_arrives.gif", max_n=26, fps=6)
save_geodesic_3d_rotating_gif("artifacts/gojo_geodesic_3d_rotating.gif", frames=72, fps=20)
save_geodesic_approach_mp4("artifacts/gojo_geodesic_approach.mp4", frames=90, fps=20)
save_geodesic_3d_rotating_mp4("artifacts/gojo_geodesic_3d_rotating.mp4", frames=72, fps=20)'
```

Sample outputs are committed at the repo root under
[`artifacts/`](../../artifacts/) (`gojo_metric_blowup.png`,
`gojo_series_convergence.png`, `gojo_geodesic_bundle.png`,
`gojo_length_divergence.png`, `gojo_geodesic_3d.png`,
`gojo_geodesic_approach.gif`, `gojo_never_arrives.gif`,
`gojo_geodesic_3d_rotating.gif`, `gojo_geodesic_approach.mp4`,
`gojo_geodesic_3d_rotating.mp4`, `gojo_four_lenses.gif`,
`gojo_four_lenses.mp4`).

## Sample output (verbatim headline + conclusion)

```
MATHEMATICS BEHIND JUJUTSU KAISEN: GOJO SATORU'S INFINITY

Four lenses, after Achmad Roykhan Sabiq (Oxford Maths Essay 2026).
```

Key evidence emitted at runtime: `S_8 = 255/256 = 0.99609375`; geometric sum
`= 1` exactly; arrival time `= 2`; `m(Z) = 0` with full cover length `= eps`;
calibrated `lambda = 0.284118`, `g(0.8) = 4.1000`; `geodesic_to_barrier = inf`;
severed felt length `= None`; domain `-> 2 components`.

```
CONCLUSION -- four lenses, four verdicts
Lens                     Verdict     Reason
-------------------------------------------
Geometric series (Zeno)  Fragile     attacker arrives; crossed series and arrival-time series both -> finite
Lebesgue measure         Fragile     m(Z) = 0; the barrier is a null set of total length zero
Riemannian geometry      Formidable  felt geodesic length to the barrier diverges to +infinity
Topology                 Falls       severing continuity disconnects the domain; the metric is undefined

Honest caveat: applying real analysis to a fictional universe has
limits. 'Cursed energy' and authorial intent do not obey the axioms
of real analysis; these four models illuminate the idea of Infinity,
they do not govern it.
```

## Design guarantees

- **Exactness where it matters**: Lens 1 and 2 use `fractions.Fraction`; no
  floating-point rounding in the headline numbers.
- **Honest infinities**: divergence returns `math.inf`; an undefined quantity
  returns `None`. Neither is faked with a large finite number.
- **Derived, not hardcoded**: the Riemannian `lambda` comes from bisection on the
  essay's Figure-8 targets.
- **Immutability**: verdicts and calibration results are `frozen` dataclasses; no
  shared mutable state.
- **Optional deps deferred**: numpy/matplotlib are never imported at module load;
  the PNG exporter guards on `try_import` and raises `OptionalDependencyError`
  when matplotlib is absent.
