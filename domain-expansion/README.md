# Domain Expansion as a Coupled Constraint Solver

A small, self-contained Python prototype that models a *Jujutsu Kaisen*
**Domain Expansion** as a mathematical object: a closed region that enforces
many simultaneous constraints on everything inside it, and whose "power" is
literally the **stability and well-posedness** of that constraint system.

Pure standard library. `numpy` is used if present, otherwise an import-guarded
pure-python linear-algebra fallback (Gaussian elimination + power iteration)
takes over. The systems are tiny (a 7x7 grid), so pure python is fine.

---

## The concept (JJK → math)

In JJK a Domain Expansion manifests an innate technique as a *closed space* and
forces a **guaranteed-hit condition** on everyone trapped inside. We model that
directly:

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

Each domain is a discretized **Laplace equation** on the grid:

```
  ∂²u/∂x² + ∂²u/∂y² = 0     inside the domain
  u = g                      on the boundary  (the sure-hit condition)
```

Discretized with the 5-point stencil, every interior cell must equal the
average of its four neighbours:

```
  coupling · (4·u[i,j] − u[i−1,j] − u[i+1,j] − u[i,j−1] − u[i,j+1]) = noise
```

That is a large set of **simultaneous linear constraints**. The unique field
that satisfies all of them at once is the domain's manifestation.

- `coupling = 1.0`, `noise = 0` → a clean Laplace domain (**refined**).
- `coupling < 1`, `noise > 0` → constraints are weakly / inconsistently
  enforced; the technique "leaks" (**crude**).

---

## The honest math

**Solvers.** Two independent solvers are implemented:

1. **Gauss–Seidel relaxation** (`solve_domain`) — iterates the averaging update
   in place until the max cell change drops below `1e-8`. This is the domain
   "expanding" until it reaches a fixed point.
2. **Direct Gaussian elimination** (`direct_solve_domain` + `linalg.gaussian_solve`)
   — assembles the interior linear system `A x = b` (boundary terms moved to the
   right-hand side) and solves it exactly with partial pivoting.

The demo cross-checks them: `max|relax − direct| ≈ 2.8e-08`, confirming the
relaxation converges to the true solution.

**Refinement metric.** For a solved field we compute the **constraint residual**
`r` (how badly each constraint is violated) and report:

- `residual_L2 = ‖r‖₂` — total constraint violation. A properly-posed domain
  drives this to ~`1e-8` (machine-ish, given the tolerance).
- `residual_Linf = ‖r‖∞` — the single worst-violated constraint.
- `rigidity` — a conditioning proxy: the spectral radius (via power iteration)
  of the interior operator, scaled by `coupling`, boosted by any Unlimited-Void
  reinforcement, and penalized by interior noise. Higher = harder / more rigid.
- **refinement score** = `rigidity / (1 + residual_L2)`. Larger is better-posed.

This is honest about what it is: `rigidity` is a *proxy* (operator norm of a
representative interior stencil, not the true condition number of the full
matrix), chosen because it is cheap, pure-python, and monotone in the qualities
we care about (coupling strength, void reinforcement, low noise).

**Domain clash.** Two domains expand onto the same grid and both claim the
interior. We solve both, compare refinement scores, and the **more refined**
domain wins. The winner then re-solves with the loser's field pre-loaded and
**overwrites** the contested interior region with its own solution — while the
loser keeps its own boundary edges, so you can literally see the takeover.

Tie-break order: refinement score, then lower residual, then higher rigidity.

**Unlimited Void.** A void cell is a constraint `void_weight · (u[i,j] − target)`
with `void_weight = 1e6`. It forces a discontinuity against the smooth Laplace
field, so its *residual is large* — but its **rigidity is astronomically
higher** (≈1004 vs ≈0.23 for a crude domain), so it still dominates a clash.
That is the point: infinite information density overpowers a weak technique on
sheer rigidity, even though it is not a "smooth" solution.

### Residual / refinement comparison (from the sample run)

| Domain | converged | residual L2 | rigidity | refinement | clash outcome |
|---|---|---|---|---|---|
| Refined Domain | 74 iters | `5.23e-08` | `4.618` | **4.6180** | beats Crude |
| Crude Domain | 78 iters | `2.15e-08` | `0.231` | 0.2309 | loses |
| Unlimited Void | 50 iters | `2.21e+03` | `1004.6` | 0.4537 | beats Crude |

Note the crude domain actually reaches a *small* residual too (Gauss–Seidel
converges on its own weak system), but its **rigidity** is ~20x lower, so the
refined domain is far more refined and wins the overlap. The Void wins on raw
rigidity despite a huge residual.

---

## Run it

```bash
cd domain-expansion
python3 main.py
```

No dependencies required. If `numpy` happens to be installed it is used; the
header line reports which backend is active.

---

## Files

| File | Role |
|---|---|
| `linalg.py` | numpy guard + pure-python Gaussian elimination, norms, power iteration |
| `domain.py` | `Domain` model, Gauss–Seidel + direct solvers, residual & rigidity metrics |
| `clash.py` | Two-domain clash, winner decision, region overwrite |
| `main.py` | Demo: solve a domain, stage a clash, show Unlimited Void |

---

## Sample output

```
================================================================
DOMAIN EXPANSION :: coupled constraint solver
numpy backend: no (pure-python fallback)
================================================================

Refined Domain field (Laplace steady state):
  100.0   20.0   20.0   20.0   20.0   20.0    0.0
  100.0   56.9   38.2   28.1   20.8   13.1    0.0
  100.0   69.3   47.9   33.3   22.1   11.7    0.0
  100.0   72.3   50.8   35.0   22.7   11.5    0.0
  100.0   69.3   47.9   33.3   22.1   11.7    0.0
  100.0   56.9   38.2   28.1   20.8   13.1    0.0
  100.0   20.0   20.0   20.0   20.0   20.0    0.0

[Refined Domain]
  converged        : True in 74 iters
  residual  (L2)   : 5.231327e-08
  residual  (Linf) : 1.861986e-08
  rigidity  proxy  : 4.618034
  refinement score : 4.618034
  direct-solve check: max|relax - direct| = 2.793e-08

[Crude Domain]
  converged        : True in 78 iters
  residual  (L2)   : 2.153567e-08
  residual  (Linf) : 7.665193e-09
  rigidity  proxy  : 0.230902
  refinement score : 0.230902
----------------------------------------------------------------
CLASH: Crude Domain  vs  Refined Domain
----------------------------------------------------------------
WINNER : Refined Domain
LOSER  : Crude Domain
WHY    : Refined Domain is more refined: refinement=4.6180 ... vs Crude Domain refinement=0.2309 ...

Contested region overwritten by Refined Domain:
   60.0   50.0   50.0   50.0   50.0   50.0   40.0
   60.0   56.9   38.2   28.1   20.8   13.1   40.0
   60.0   69.3   47.9   33.3   22.1   11.7   40.0
   60.0   72.3   50.8   35.0   22.7   11.5   40.0
   60.0   69.3   47.9   33.3   22.1   11.7   40.0
   60.0   56.9   38.2   28.1   20.8   13.1   40.0
   60.0   50.0   50.0   50.0   50.0   50.0   40.0
----------------------------------------------------------------
UNLIMITED VOID: infinite-information-density constraint
----------------------------------------------------------------
[Unlimited Void]
  converged        : True in 50 iters
  residual  (L2)   : 2.213391e+03
  residual  (Linf) : 2.213391e+03
  rigidity  proxy  : 1004.618034
  refinement score : 0.453677

Void vs Crude winner: Unlimited Void
================================================================
```

The loser keeps its own boundary (60 / 50 / 40 edges) but its entire interior
is overwritten by the winner's field — the refined domain has imposed its
constraints on the contested region.
