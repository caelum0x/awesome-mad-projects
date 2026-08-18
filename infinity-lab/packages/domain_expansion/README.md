# domain_expansion

**A *Jujutsu Kaisen* Domain Expansion, modelled as a coupled constraint solver.**

A Domain Expansion manifests an innate technique as a *closed space* and forces a
**guaranteed-hit condition** on everything trapped inside. We model that directly
as a discretized **Laplace boundary-value problem** on a grid: a large set of
simultaneous linear constraints whose unique solution is the domain's
manifestation. A domain's "power" is literally the **stability / well-posedness
(rigidity)** of that constraint system.

This is the monorepo port of the standalone `domain-expansion` prototype. The
pure math lives in `domain_expansion.core` (standard library only, sharing
`commons.core`); ASCII/PNG rendering lives in `domain_expansion.adapters`;
optional numpy fast-paths live in `domain_expansion.accel`. It mirrors the
`central_finite_curve` src-layout.

---

## Concept → math mapping

| JJK notion | Mathematical model |
|---|---|
| The closed domain | A rectangular grid region |
| The guaranteed "sure-hit" condition | Fixed **boundary values** (Dirichlet condition) |
| The technique filling the space | The **field** that satisfies every interior constraint at once |
| Expanding / manifesting the domain | **Solving** the boundary-value problem until every point obeys the rule |
| A refined vs. crude domain | A **well-posed, strongly-coupled** system vs. a leaky, noisy one |
| Two domains clashing | Two constraint systems overlapping on a shared region; the **more stable** one overwrites the other |
| Unlimited Void | A single interior cell pinned with **enormous weight** (infinite information density) that dominates the operator |

### The constraint system

Each domain is a discretized Laplace equation on the grid:

```
  d2u/dx2 + d2u/dy2 = 0     inside the domain
  u = g                      on the boundary  (the sure-hit condition)
```

Discretized with the 5-point stencil, every interior cell must equal the average
of its four neighbours:

```
  coupling * (4*u[i,j] - u[i-1,j] - u[i+1,j] - u[i,j-1] - u[i,j+1]) = noise
```

- `coupling = 1.0`, `noise = 0` -> a clean Laplace domain (**refined**).
- `coupling < 1`, `noise > 0`  -> constraints weakly / inconsistently enforced;
  the technique "leaks" (**crude**).

---

## The honest math

**Two independent solvers** (they agree, which is how we know relaxation reached
the true field):

1. **Gauss-Seidel relaxation** (`core.domain.solve_domain`) — iterates the
   averaging update in place until the max cell change drops below `tol`. This is
   the domain "expanding" until it reaches a fixed point.
2. **Direct Gaussian elimination** (`core.domain.direct_solve_domain` +
   `core.linalg.gaussian_solve`) — assembles the interior linear system `A x = b`
   (boundary terms moved to the right-hand side) and solves it exactly with
   partial pivoting. Pure python; an optional numpy path
   (`accel.numpy_backend.gaussian_solve_numpy`) mirrors it to a few ULP.

The demo cross-checks them: `max|relax - direct| ≈ 2.8e-08`.

**Refinement metric.** For a solved field we compute the constraint residual `r`
and report:

- `residual_L2 = ||r||_2` — total constraint violation (a well-posed domain drives
  this to ~`1e-8`, near the relaxation tolerance).
- `residual_Linf = ||r||_inf` — the single worst-violated constraint.
- `rigidity` — a conditioning proxy: the spectral radius (via power iteration,
  `core.linalg.spectral_radius_estimate`) of a representative interior operator,
  scaled by `coupling`, boosted by any Unlimited-Void reinforcement, and penalized
  by interior noise. Higher = harder / more rigid.
- **refinement score** = `rigidity / (1 + residual_L2)`. Larger is better-posed.

**On the rigidity proxy (honest treatment).** `rigidity` is a *proxy*, not the
true condition number of the full assembled matrix. It is the operator norm of a
small representative interior stencil (a 4×4 tridiagonal Laplacian scaled by
`coupling`), plus a void-reinforcement bonus, divided by a noise penalty. It was
chosen because it is **cheap, pure-python, and monotone** in the qualities we care
about (coupling strength, void reinforcement, low noise) — not because it equals
the spectral condition number. Two consequences worth stating plainly:

- The power-iteration estimate returns the *dominant* eigenvalue reachable from a
  uniform start vector; for a symmetric stencil whose dominant eigenvector is
  orthogonal to that start it would under-report. The representative stencil used
  here is chosen so the uniform start has a component along the dominant mode, so
  the estimate is meaningful for the comparisons we make.
- Because rigidity is stencil-based (not grid-solved), it is a *comparative* score
  for ranking domains in a clash, not an absolute physical quantity.

**Domain clash.** Two domains expand onto the same grid and both claim the
interior. We solve both, compare refinement scores, and the **more refined** domain
wins. The winner then re-solves with the loser's field pre-loaded and **overwrites**
the contested interior region with its own solution — while the loser keeps its own
boundary edges, so the takeover is visible. Tie-break order: refinement, then lower
residual, then higher rigidity.

**Unlimited Void.** A void cell is a constraint `void_weight * (u[i,j] - target)`
with `void_weight = 1e6`. It forces a discontinuity against the smooth Laplace
field, so its *residual is large* — but its **rigidity is astronomically higher**
(~1004 vs ~0.23 for a crude domain), so it still dominates a clash. That is the
point: infinite information density overpowers a weak technique on sheer rigidity,
even though it is not a "smooth" solution.

### Residual / refinement comparison (from the sample run)

| Domain | converged | residual L2 | rigidity | refinement | clash outcome |
|---|---|---|---|---|---|
| Refined Domain | 74 iters | `5.23e-08` | `4.618` | **4.6180** | beats Crude |
| Crude Domain | 78 iters | `2.15e-08` | `0.231` | 0.2309 | loses |
| Unlimited Void | 50 iters | `2.21e+03` | `1004.6` | 0.4537 | beats Crude |

The crude domain also reaches a small residual (Gauss-Seidel converges on its own
weak system), but its **rigidity is ~20x lower**, so the refined domain is far more
refined and wins the overlap. The Void wins on raw rigidity despite a huge residual.

---

## Layout

```
src/domain_expansion/
  core/                 # pure engine: stdlib + commons.core only
    linalg.py           # Gaussian elimination, norms, power iteration
    domain.py           # Domain model, Gauss-Seidel + direct solvers, metrics
    clash.py            # two-domain clash, winner decision, region overwrite
    scenarios.py        # the canonical refined / crude / void domains
  adapters/             # presentation / I/O (never imported by core)
    render.py           # ASCII field grid + heatmap (via commons.adapters.ascii_art)
    cli.py              # argparse front end
    viz.py              # OPTIONAL matplotlib PNG export (lazily guarded)
  accel/                # OPTIONAL numpy fast-paths (lazily guarded)
    numpy_backend.py    # numpy Gaussian solve + spectral radius, parity-tested
  demo.py               # runnable end-to-end demo
```

Core purity is enforced by `tests/test_de_core_purity.py`: no `core` module
imports an adapter or hard-imports numpy/matplotlib, verified statically and in a
fresh subprocess.

---

## Run it

No dependencies required for the ASCII path (numpy/matplotlib are optional):

```bash
# From the repo root (imports resolve via pyproject pytest pythonpath):
PYTHONPATH=packages/commons/src:packages/domain_expansion/src \
  python3 -m domain_expansion.demo

# Or the CLI, one subcommand per stage (refined | crude | clash | void | all):
PYTHONPATH=packages/commons/src:packages/domain_expansion/src \
  python3 -m domain_expansion.adapters.cli clash

# Optional PNG of the solved field + clash (needs the 'viz' extra / matplotlib):
PYTHONPATH=packages/commons/src:packages/domain_expansion/src \
  .venv/bin/python -m domain_expansion.adapters.cli all --png artifacts
#  -> artifacts/domain_expansion_field.png
```

Run the tests (optional numpy/matplotlib tests SKIP when those are absent, RUN on
the venv):

```bash
python3 -m pytest packages/domain_expansion -q
```

---

## Sample output (clash)

```
================================================================
CLASH: Crude Domain  vs  Refined Domain
================================================================
WINNER : Refined Domain
LOSER  : Crude Domain
WHY    : Refined Domain is more refined: refinement=4.6180 (rigidity=4.618,
         residual_L2=5.231e-08) vs Crude Domain refinement=0.2309 ...

Contested region overwritten by Refined Domain:
    60.0    50.0    50.0    50.0    50.0    50.0    40.0
    60.0    56.9    38.2    28.1    20.8    13.1    40.0
    60.0    69.3    47.9    33.3    22.1    11.7    40.0
    60.0    72.3    50.8    35.0    22.7    11.5    40.0
    60.0    69.3    47.9    33.3    22.1    11.7    40.0
    60.0    56.9    38.2    28.1    20.8    13.1    40.0
    60.0    50.0    50.0    50.0    50.0    50.0    40.0
```

The loser keeps its own boundary (60 / 50 / 40 edges) but its entire interior is
overwritten by the winner's field — the refined domain has imposed its constraints
on the contested region.

