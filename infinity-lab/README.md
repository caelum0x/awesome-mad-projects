# infinity-lab

> **Start here:** open the combined, shareable **[landing page](index.html)** —
> a single self-contained page (opens offline, no network) featuring the two
> explainer animations, the project cards, headline stills, honest caveats, and
> links into the full gallery and the essay companion.

A Python 3.11+ monorepo for independent mathematics projects that share one
internal `commons` package. Everything in the **core** of every package is
**standard-library only**; `numpy` / `matplotlib` are optional, import-guarded,
and not required to run, test, or demo anything here.

- **[`gojo_infinity`](packages/gojo_infinity/README.md)** — Gojo Satoru's
  "Infinity" (Jujutsu Kaisen) examined through four independent mathematical
  lenses, each reaching its own verdict.
- **[`mobius_rickness`](packages/mobius_rickness/README.md)** — the *Rick &
  Morty* "Central Finite Curve" realised as a real zero set `R^{-1}(0)` on a
  Möbius strip of strictly negative Gaussian curvature.
- **[`central_finite_curve`](packages/central_finite_curve/README.md)** — an
  engine that walks the Rickness ridge (the near-maximal band) across a
  simulated multiverse, tracing "the one arc of realities where a Rick exists"
  as a computed path.

Both are built on the shared **[`commons`](packages/commons/)** package
(numerics, exact arithmetic, deterministic RNG, config, optional-dep guarding,
ASCII renderers).

## Architecture: shared commons + src-layout

Each package is an isolated unit under `packages/`, using the **src layout**
(`src/<pkg>/`) so import roots are unambiguous and tests never accidentally pick
up an un-packaged module. The three `src/` roots are wired onto `sys.path` by a
single pytest setting — **no editable install, no network**:

```
infinity-lab/
├── pyproject.toml                 # metadata + [tool.pytest.ini_options] pythonpath wiring
├── README.md                      # this file (monorepo front page)
├── tests/                         # repo-level cross-package import wiring tests
└── packages/
    ├── commons/                   # shared internal package
    │   ├── src/commons/
    │   │   ├── core/              # PURE stdlib: numerics, exact, rng, config, optional
    │   │   └── adapters/          # text/ASCII renderers over the core
    │   ├── tests/
    │   └── demo.py
    ├── gojo_infinity/
    │   ├── src/gojo_infinity/
    │   │   ├── core/              # zeno, measure, riemannian, topology, verdicts
    │   │   ├── accel/             # OPTIONAL numpy fast paths (lazy try_import)
    │   │   └── adapters/          # cli, viz (ASCII; matplotlib deferred)
    │   ├── tests/
    │   ├── demo.py
    │   └── README.md
    └── mobius_rickness/
        ├── src/mobius_rickness/
        │   ├── core/              # geometry, mobius, rickness, field, tracer, torus
        │   ├── accel/             # OPTIONAL numpy curvature/field fast paths (lazy)
        │   ├── ridge/             # OPTIONAL numpy SCMS/Eberly ridge (lazy)
        │   └── adapters/          # cli, viz (ASCII; matplotlib deferred)
        ├── tests/
        ├── demo.py
        └── README.md
```

The `pythonpath` wiring (`pyproject.toml`):

```toml
[tool.pytest.ini_options]
pythonpath = [
    "packages/commons/src",
    "packages/gojo_infinity/src",
    "packages/mobius_rickness/src",
]
```

## The core-purity rule (hard invariant)

Modules under any package's `core/` import **only the standard library plus
`commons.core`** — never an adapter (`cli` / `viz` / `io`), and never `numpy` /
`matplotlib` at module top level. Adapters may import core; **core never imports
adapters** (one-way dependency). This keeps the mathematics free of I/O,
rendering, and optional heavy dependencies, and makes it trivially testable and
portable.

The invariant is enforced by real tests, not convention:

- `packages/commons/tests/test_core_purity.py`
- `packages/gojo_infinity/tests/test_gojo_core_purity.py`
- `packages/mobius_rickness/tests/test_mr_core_purity.py`

Optional acceleration is reached lazily via
`commons.core.optional.try_import`; when a dependency is absent the guarded
function raises a clear `OptionalDependencyError` instead of failing to import.

## Running the tests (no install, no network)

From the repo root (`infinity-lab/`):

```bash
python -m pytest                        # entire monorepo (commons + both packages)
python -m pytest packages/commons        # one package at a time
python -m pytest packages/gojo_infinity
python -m pytest packages/mobius_rickness
```

Imports resolve purely via the `pythonpath` setting above — no `pip install -e`
and no network access are required. Requires Python 3.11+ and the standard
library only.

## Running the demos (zero network)

The demos import across the `commons` boundary, so set `PYTHONPATH` to the
relevant `src/` roots (pytest does this automatically; standalone scripts need
it explicitly):

```bash
# gojo_infinity — four lenses, four verdicts
PYTHONPATH=packages/commons/src:packages/gojo_infinity/src \
  python -m gojo_infinity.demo

# mobius_rickness — Central Finite Curve as a real zero set
PYTHONPATH=packages/commons/src:packages/mobius_rickness/src \
  python -m mobius_rickness.demo

# commons — shared numerics / ASCII showcase (no PYTHONPATH needed)
python packages/commons/demo.py
```

Each package also exposes an `argparse` CLI adapter
(`python -m gojo_infinity.adapters.cli all --ascii`,
`python -m mobius_rickness.adapters.cli all`).

## Results

### gojo_infinity — four lenses, four verdicts

Each lens asks *can an attacker ever reach Gojo?* and answers with different
mathematics. Three of four models say the barrier is crossable or negligible;
only the Riemannian reading makes it impassable, and a topological cut removes
the metric entirely.

| Lens | Model | Verdict | Why |
|------|-------|---------|-----|
| 1 | Geometric series / Zeno | **Fragile** | `S_n = 1 - (1/2)^n → 1` exactly; arrival time `= 2` (finite). The attacker arrives. |
| 2 | Lebesgue measure | **Fragile** | Cover of `Z = {1 - 1/2^n}` telescopes to length exactly `eps`; infimum `→ 0`, so `m(Z) = 0` (null set). |
| 3 | Riemannian conformal geometry | **Formidable** | Felt geodesic `∫ Ω dx` to the barrier is an improper integral that **diverges** — `geodesic_to_barrier(x0) = math.inf`. |
| 4 | Topology / World-Cutting Slash | **Falls** | Severed metric is undefined at the cut `c = 0.5`; domain `[0.1,0.9]\{0.5}` splits into exactly **2** components. |

Headline evidence emitted at runtime (Lens-1/2 numbers are exact
`fractions.Fraction`): `S_8 = 255/256 = 0.99609375`; geometric sum `= 1`
exactly; arrival time `= 2`; full cover length `= eps`, `m(Z) = 0`; calibrated
`sigma = 0.35`, `lambda ≈ 0.284118` (derived by bisection) with `g(0.8) = 4.1`;
`geodesic_to_barrier = inf` (honest `math.inf`, not a large float); severed felt
length `= None` (undefined, not infinite); `→ 2 components`.

### mobius_rickness — the Central Finite Curve as a real zero set

The Möbius strip is a **ruled** surface, so its Gaussian curvature is
**strictly negative** on the interior (`K = -1/(4 E²) < 0`). Multiplying a
sign-changing scalar field `R(u,v)` by a nowhere-vanishing `K` leaves its zero
set unchanged:

```
K_Rick(u, v) = K(u, v) · R(u, v) = 0   ⇔   R(u, v) = 0
```

so the weighted field vanishes **exactly** on the curve `R^{-1}(0)` — a genuine
1-D locus, the Central Finite Curve, separating "Rick-positive" from
"Rick-negative" universes on the band. `K < 0` strictly (worst/max
`K = -0.055927`); three independent curvature paths (analytic, finite-difference,
complex-step) agree to `max |analytic − numeric| = 6.85e-09`.

A couple of traced zero points (all verified `|R| < 1e-6` **and**
`|K_Rick| < 1e-6`):

```
         u          v          x          y          z        |R|
------------------------------------------------------------------
    1.6368    -0.4888    -0.0439    +0.6645    -0.3568    5.9e-11
    4.9104    +0.0020    +0.1964    -0.9790    +0.0013    5.8e-11
```

The torus is the non-ruled counterpoint: its curvature
`K(θ) = cos θ / (r0 (R0 + r0 cos θ))` changes sign on its own, so its zero set
needs **no** weighting — the two `K = 0` circles are located exactly at
`θ = π/2` and `θ = 3π/2` (traced `1.570796, 4.712389`), with positive curvature
on the outer half and negative on the inner half.

## Optional extras (numpy acceleration & matplotlib visualization)

The pure stdlib `core/` is always the source of truth. Two **optional** layers
live strictly *outside* `core/` and reach their heavy dependency only lazily via
`commons.core.optional.try_import` (never a top-level import):

- **numpy fast paths** — vectorised mirrors of the core numerics under each
  package's `accel/` subpackage (`gojo_infinity.accel`, `mobius_rickness.accel`),
  plus the SCMS / Eberly height-ridge under `mobius_rickness.ridge` (the second
  Central Finite Curve formalization — see that package's README). They are
  verified for **bit-level / ULP-level parity** against the exact stdlib core.
- **matplotlib PNG exports** — headless (`Agg`) renderers under each package's
  `adapters/viz.py`, one per lens / field.

Neither is required to run, test, or demo the core. Without the dependency the
guarded function raises a clear `OptionalDependencyError` instead of failing at
import time, and the corresponding tests **skip** — so nothing is stubbed or
faked.

### Enabling the optional layers (venv)

```bash
# From the repo root, create a venv and install numpy + matplotlib + pytest
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install numpy matplotlib pytest

# Run the WHOLE suite on the venv interpreter: optional tests now RUN
.venv/bin/python -m pytest -q          # numpy/matplotlib parity + PNG tests execute

# The stdlib-only system interpreter still passes; optional tests SKIP
python3 -m pytest -q                   # accel/ridge/PNG modules are skipped
```

### Sample artifacts

Committed sample PNGs (rendered via the venv `adapters/viz.py` exporters — these
are deliverables, not test output) live in [`artifacts/`](artifacts/):

| File | Package | Picture |
|------|---------|---------|
| `gojo_metric_blowup.png` | gojo_infinity | Lens 3 `Omega(x)` metric blow-up toward `x_gojo` |
| `gojo_series_convergence.png` | gojo_infinity | Lens 1 Zeno `S_n -> 1` with residual |
| `mobius_strip_curve.png` | mobius_rickness | Möbius surface + traced Central Finite Curve `R^{-1}(0)` |
| `mobius_krick_heatmap.png` | mobius_rickness | `K_Rick(u,v) = K*R` heatmap + zero contour |
| `mobius_ridge.png` | mobius_rickness | Möbius surface + SCMS / Eberly ridge of maximal Rickness |

Regenerate them from the repo root with:

```bash
PYTHONPATH=packages/commons/src:packages/gojo_infinity/src:packages/mobius_rickness/src \
  .venv/bin/python -c '
from gojo_infinity.adapters.viz import save_metric_blowup_png, save_series_convergence_png
from mobius_rickness.adapters.viz import save_strip_3d_png, save_krick_heatmap_png, save_ridge_png
save_metric_blowup_png("artifacts/gojo_metric_blowup.png")
save_series_convergence_png("artifacts/gojo_series_convergence.png")
save_strip_3d_png("artifacts/mobius_strip_curve.png")
save_krick_heatmap_png("artifacts/mobius_krick_heatmap.png")
save_ridge_png("artifacts/mobius_ridge.png")'
```

The `gojo_infinity` and `mobius_rickness` CLI adapters also accept `--png OUTDIR`
to write these images directly.

## Gallery

A self-contained static showcase gallery presents both projects side by side
with every rendered figure and animation, each captioned with what it shows and
the relevant formula / verdict (plus the four-lens verdict table, the two
Central Finite Curve readings, the honest caveats, and attribution to the source
essay).

Open it directly in any browser — no server, no build step, no network:

```bash
open gallery/index.html          # macOS
# or: xdg-open gallery/index.html (Linux) / just double-click the file
```

The page is fully self-contained (inline CSS, no external CDNs) and embeds
artifacts via relative `../artifacts/NAME` paths, so it works offline. PNG/GIF
are embedded as `<img>`, MP4 as `<video controls loop muted>`.

Rebuild it any time with the **standard library only** (no dependencies) — it
dynamically re-scans `artifacts/`, so newly added artifacts appear automatically
and anything unrecognised still lands in an "Other artifacts" section:

```bash
python3 gallery/build_gallery.py     # writes gallery/index.html
```

## Scripts

Two glue scripts live in [`scripts/`](scripts/) (both executable, both robust to
being called from any directory — they resolve the repo root from their own
location):

- **`scripts/regenerate_artifacts.sh`** — regenerates every artifact into
  `artifacts/` using the repo venv (numpy + matplotlib + Pillow, ffmpeg on
  PATH), then rebuilds the gallery. It renders the PNGs via the `viz` exporters,
  the GIFs/MP4s via the `gojo animate --rotate --mp4` and `mobius animate --mp4`
  CLI subcommands, and echoes every file it writes. Idempotent: each run
  overwrites the same filenames in place.

  ```bash
  ./scripts/regenerate_artifacts.sh
  ```

- **`scripts/verify.sh`** — runs **both** test suites and prints a one-line
  summary for each, exiting non-zero if either fails:

  ```bash
  ./scripts/verify.sh
  # SUMMARY [offline core (python3)]: 296 passed, 11 skipped ... (exit 0)
  # SUMMARY [full suite (.venv)]:     379 passed ...           (exit 0)
  ```

## Test totals

Stdlib-only system interpreter — `python3 -m pytest -q` → **214 passed, 5
skipped**, offline, zero install (the 5 optional numpy/matplotlib modules skip):

| Suite | Core tests |
|-------|-------|
| `tests/` (repo-level import wiring) | 3 |
| `packages/commons/tests/` | 68 |
| `packages/gojo_infinity/tests/` | 73 |
| `packages/mobius_rickness/tests/` | 70 |
| **Total (core)** | **214** |

Venv interpreter (numpy + matplotlib installed) —
`.venv/bin/python -m pytest -q` → **263 passed** (the same 214 core tests plus
the optional numpy parity, SCMS ridge, and matplotlib PNG tests, which now run).
