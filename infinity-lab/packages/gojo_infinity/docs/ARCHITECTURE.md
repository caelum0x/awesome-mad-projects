# gojo-infinity — Architecture

_Target architecture designed by the planning workflow from the resolved mathematics. A working prototype already exists; this is the fuller structure it evolves into. Every module has a real responsibility — no mock code._


## Overview

A stdlib-first, src-layout Python package that models Gojo Satoru's "Infinity" through the four mathematical lenses of Sabiq's essay, each reaching its own verdict: Lens 1 geometric series / Zeno (FRAGILE), Lens 2 Lebesgue measure (FRAGILE/negligible), Lens 3 Riemannian conformal geometry (FORMIDABLE), Lens 4 topology / World-Cutting Slash (FALLS). The existing prototype already has correct, well-documented flat modules (zeno.py, measure.py, riemannian.py, topology.py, demo.py, test_lenses.py) whose math is worth keeping verbatim. The target evolves that prototype into an importable package with a strict PURE-CORE / ADAPTER split (ports-and-adapters): every lens becomes one or more small pure-math modules under core/ using fractions.Fraction for exact rational targets and import-guarded numpy only inside adapters, never in core. New real capabilities the research demands but the prototype lacks are added as first-class modules: an epsilon-N convergence oracle, an arrival-TIME series evaluator (distance-converges vs time-converges distinction), an exact Lebesgue covering-length + N-for-error engine with disjointness certificate, a singularity-subtraction quadrature that returns the honest analytic -lambda*ln divergence (plus deliberately-wrong trapezoid/adaptive-Simpson variants kept to demonstrate their failure modes), an oscillation-based continuity classifier with Aitken one-sided limits, an interval-union connectedness engine, a seeded RNG + Monte-Carlo residual estimator, Kahan/fsum numeric helpers, an always-on ASCII visualization layer, optional matplotlib PNG, and an argparse subcommand CLI. Every module reproduces a pinned numeric target that the pytest suite asserts (Fraction == for exact rationals, math.isclose with explicit abs_tol for floats, k*sigma/sqrt(N) for Monte-Carlo).


## Directory layout

```
gojo-infinity/
├── pyproject.toml                # PEP 621 metadata; scripts=gojo-infinity=...cli:main; optional viz=[numpy,matplotlib]
├── README.md                     # quickstart, four-lens table, runnable example (evolve existing README)
├── ARCHITECTURE.md               # core/adapter dependency rule, reproducibility & optional-dep policy, module table
├── conftest.py                   # shared fixtures: seeded Prng, default Config, sample grids
├── src/
│   └── gojo_infinity/
│       ├── __init__.py           # __version__, __all__, thin re-exports of the four lens verdicts + key core fns
│       ├── _optional.py          # HAS_NUMPY / HAS_MPL capability flags via guarded imports; Agg backend before pyplot
│       ├── config.py             # frozen dataclass Config: X_GOJO, SIGMA, LAMBDA, SEED, grid sizes, calibration targets
│       ├── rng.py                # Prng wrapper over random.Random(seed) + deterministic spawn(tag)
│       ├── verdict.py            # frozen Verdict dataclass + LensVerdict enum (Fragile/Formidable/Falls); shared by all lenses
│       ├── core/
│       │   ├── __init__.py
│       │   ├── exact.py          # exact power-of-two & Fraction helpers: pow2(n)=1<<n, half_pow(n), validate_ratio
│       │   ├── series.py         # Lens 1: partial_sum, residual, geometric_sum, zeno_series_sum (from prototype zeno.py)
│       │   ├── residual_proof.py # Lens 1: strict-positivity certificate + inductive R_{n+1}=R_n/2 + float-failure witness
│       │   ├── convergence.py    # Lens 1: epsilon_N oracle (least N with (1/2)^N < eps), exact-Fraction confirmed
│       │   ├── arrival_time.py   # Lens 1: constant-speed time series T=1/v; Achilles catch-up T=d0/(1-r)
│       │   ├── measure.py        # Lens 2: subdivision_set Z, cover lengths, N_for_error, disjointness, m(Z)=0 (from measure.py)
│       │   ├── conformal.py      # Lens 3: gaussian_kernel, conformal_factor Omega, g11, felt_step (from riemannian.py)
│       │   ├── quadrature.py     # Lens 3: midpoint/trapezoid/adaptive-Simpson + singularity_subtraction integrators
│       │   ├── geodesic.py       # Lens 3: geodesic_length, divergence_by_decade, calibrate, geodesic_ball solver
│       │   ├── continuity.py     # Lens 4: oscillation_at classifier, one_sided_limits (Aitken), jump_ratio
│       │   ├── topology.py       # Lens 4: sever, connected_components, same_component, geodesic-across-cut undefined
│       │   ├── montecarlo.py     # optional MC estimate of residual/cover integrals using injected Prng
│       │   └── numerics.py       # kahan_sum, fsum wrapper, isclose_frac/float helpers, normalize, float-failure demos
│       ├── viz/
│       │   ├── __init__.py
│       │   ├── ascii.py          # always-on renderers: convergence bars, cover-length ramp, Omega/L profile, severed sign map
│       │   └── png.py            # matplotlib-guarded PNG for each lens; returns None when HAS_MPL is False
│       └── cli.py                # argparse subcommands: zeno, measure, riemannian, topology, demo, render; main(argv)->int
└── tests/
    ├── test_series.py
    ├── test_residual_proof.py
    ├── test_convergence.py
    ├── test_arrival_time.py
    ├── test_measure.py
    ├── test_conformal.py
    ├── test_quadrature.py
    ├── test_geodesic.py
    ├── test_continuity.py
    ├── test_topology.py
    ├── test_numerics.py
    ├── test_montecarlo.py
    ├── test_rng.py
    ├── test_viz_ascii.py
    ├── test_cli.py
    ├── test_reproduction.py      # pins all four lenses' headline numeric targets end to end
    └── test_core_purity.py       # asserts 'numpy' not in sys.modules after importing gojo_infinity.core
```


## Modules

| Path | Responsibility | Tests |
|---|---|---|
| `src/gojo_infinity/verdict.py` | Shared immutable verdict type for all four lenses, replacing the prototype's habit of importing Verdict from zeno.py (which coupled every lens to Lens 1). Single source of the conclusion-table row. | `tests/test_reproduction.py` |
| `src/gojo_infinity/config.py` | Central frozen configuration: Gojo position X_GOJO=1.0, calibration constants SIGMA=0.35 LAMBDA=0.277, RNG SEED, default grid/step sizes, and the essay Figure-8 calibration targets (g(0.1)~1.0, g(0.8)~4.1). No logic, no I/O. | `tests/test_reproduction.py` |
| `src/gojo_infinity/_optional.py` | Single point of optional-dependency detection so core never imports numpy/matplotlib at top level. Exposes booleans and lazily sets the Agg backend before pyplot import. | `tests/test_core_purity.py` |
| `src/gojo_infinity/rng.py` | Deterministic, reproducible PRNG adapter wrapping random.Random(seed) (MT19937) with independent deterministic sub-streams via spawn(tag). Injected everywhere; never module-level random.*. | `tests/test_rng.py` |
| `src/gojo_infinity/core/exact.py` | Exact integer/Fraction primitives shared by Lens 1 and Lens 2: builds powers of two with the exact shift 1<<n (NEVER float 2.0**n which overflows at n=1024, NEVER 0.5**n which underflows at n=1075), plus ratio validation. | `tests/test_series.py` |
| `src/gojo_infinity/core/series.py` | Lens 1 pure core (evolved from prototype zeno.py): exact partial sum S_n=1-(1/2)^n, residual R_n, and general geometric_sum a/(1-r). All exact via Fraction. | `tests/test_series.py` |
| `src/gojo_infinity/core/residual_proof.py` | Lens 1 machine-checkable strict-positivity certificate: R_n=(1/2)^n>0 for all finite n, via exact numerator==1 check and inductive R_{n+1}=R_n/2 loop; plus a documented float-failure witness proving 1-0.5**n==1.0 at n=60 and 0.5**1075==0.0. | `tests/test_residual_proof.py` |
| `src/gojo_infinity/core/convergence.py` | Lens 1 epsilon-N oracle: least N with residual (1/2)^N < eps, operationalising S_n->1. Integer doubling for a first guess, then exact Fraction comparison to kill math.log2 off-by-one. | `tests/test_convergence.py` |
| `src/gojo_infinity/core/arrival_time.py` | Lens 1 arrival-TIME evaluator: shows summed travel TIMES also converge (constant speed v: T=1/v; Achilles: T=d0/(1-r)), the distinction that distance-converges does not by itself imply time-converges. Keeps v an explicit Fraction so the v->0 time-dilation escape hatch is modelled, not silently assumed. | `tests/test_arrival_time.py` |
| `src/gojo_infinity/core/measure.py` | Lens 2 pure core (evolved from prototype measure.py, extended): subdivision set Z, exact cover-interval and total covering lengths, the constructive m(Z)=0 witness, plus NEW exact N_for_error truncation control and a disjointness certificate (eps<2/3). | `tests/test_measure.py` |
| `src/gojo_infinity/core/conformal.py` | Lens 3 metric core (from prototype riemannian.py): RIKEN Gaussian/RBF kernel, conformal factor Omega(x)=1+lam*K(x,x_g)/(x_g-x) with its simple pole at x_g, metric component g11=Omega^2, and felt step. Pure floats; raises for x>=x_g. | `tests/test_conformal.py` |
| `src/gojo_infinity/core/quadrature.py` | Lens 3 integrators as separable, testable pieces: composite midpoint (open, handles endpoint pole), trapezoid and adaptive Simpson kept explicitly to DEMONSTRATE failure near the pole, and the recommended singularity_subtraction that extracts the exact -lam*ln term and integrates only the bounded remainder. | `tests/test_quadrature.py` |
| `src/gojo_infinity/core/geodesic.py` | Lens 3 felt-length engine (evolved from riemannian.py): geodesic_length via chosen integrator, divergence_by_decade witness (lam*ln(10) per decade), a calibration solver that DERIVES sigma,lam from the essay targets instead of hardcoding, and a geodesic-ball solver proving every finite proper radius R has a solution strictly inside (a, x_g). | `tests/test_geodesic.py` |
| `src/gojo_infinity/core/continuity.py` | Lens 4 continuity analysis (evolved from prototype topology.continuity_at): oscillation-based point classifier CONTINUOUS/JUMP/POLE over shrinking symmetric windows, Aitken one-sided limit extrapolation (never evaluates Omega(c) itself), and a grid-refinement jump-ratio detector. | `tests/test_continuity.py` |
| `src/gojo_infinity/core/topology.py` | Lens 4 topological verdict (evolved from prototype topology.py): the World-Cutting-Slash severed factor, immutable domain sever(), connected-components / same_component via interval-union with open-endpoint semantics, and the fact that a geodesic across a cut is UNDEFINED (not infinite). | `tests/test_topology.py` |
| `src/gojo_infinity/core/numerics.py` | Pure numeric helpers so stdlib reductions stay accurate without numpy: Kahan compensated summation, math.fsum wrapper, exact/approx isclose helpers, min-max normalization for viz, and reusable float-failure demonstrators (underflow/cancellation thresholds). | `tests/test_numerics.py` |
| `src/gojo_infinity/core/montecarlo.py` | Optional reproducible Monte-Carlo cross-checks (injected Prng): estimate the covered fraction / cover-length integrals stochastically and confirm they land within k*sigma/sqrt(N) of the exact Fraction targets, demonstrating the exact core is right without trusting a single method. | `tests/test_montecarlo.py` |
| `src/gojo_infinity/viz/ascii.py` | Always-on, dependency-free ASCII visualization for every lens, golden-string testable: convergence bar chart of S_n->1 with residual, cover-length ramp toward eps, Omega(x)/cumulative-L profile whose right edge shoots off-scale at the barrier, and a severed sign map showing the two disconnected components after the slash. | `tests/test_viz_ascii.py` |
| `src/gojo_infinity/viz/png.py` | Optional matplotlib PNG renderers (one per lens) that return None when matplotlib is absent, so plotting is never a hard dependency. Agg backend set before pyplot via _optional. | `tests/test_viz_ascii.py` |
| `src/gojo_infinity/cli.py` | Thin argparse subcommand adapter (replaces prototype demo.py as an installed entry point): each subcommand parses argv, calls exactly one core function, formats output, and reports a lens verdict. main(argv=None)->int for testability; catches core ValueError at the boundary. | `tests/test_cli.py` |


### Module detail


#### `src/gojo_infinity/verdict.py`

Shared immutable verdict type for all four lenses, replacing the prototype's habit of importing Verdict from zeno.py (which coupled every lens to Lens 1). Single source of the conclusion-table row.


_Public API:_
- `@dataclass(frozen=True) Verdict(lens: str, verdict: str, reason: str)`
- `class LensVerdict(str, Enum): FRAGILE='Fragile'; FORMIDABLE='Formidable'; FALLS='Falls'`
- `format_table(verdicts: Sequence[Verdict]) -> str`

_Key algorithms:_
- Column-width computation for aligned ASCII conclusion table (ported from demo.print_conclusion)

_Depends on:_ `dataclasses`, `enum`, `typing`


#### `src/gojo_infinity/config.py`

Central frozen configuration: Gojo position X_GOJO=1.0, calibration constants SIGMA=0.35 LAMBDA=0.277, RNG SEED, default grid/step sizes, and the essay Figure-8 calibration targets (g(0.1)~1.0, g(0.8)~4.1). No logic, no I/O.


_Public API:_
- `@dataclass(frozen=True) Config(x_gojo=1.0, sigma=0.35, lam=0.277, seed=0, midpoint_steps=20000, calib_far=(0.1,1.0), calib_near=(0.8,4.1))`
- `DEFAULT: Config`

_Key algorithms:_
- none (pure data holder)

_Depends on:_ `dataclasses`


#### `src/gojo_infinity/_optional.py`

Single point of optional-dependency detection so core never imports numpy/matplotlib at top level. Exposes booleans and lazily sets the Agg backend before pyplot import.


_Public API:_
- `HAS_NUMPY: bool`
- `HAS_MPL: bool`
- `get_numpy() -> module | None`
- `get_pyplot() -> module | None  # calls matplotlib.use('Agg') first`

_Key algorithms:_
- try/except ImportError capability probing (catch ImportError specifically, never bare except)

_Depends on:_ `importlib`


#### `src/gojo_infinity/rng.py`

Deterministic, reproducible PRNG adapter wrapping random.Random(seed) (MT19937) with independent deterministic sub-streams via spawn(tag). Injected everywhere; never module-level random.*.


_Public API:_
- `class Prng: __init__(self, seed: int); random() -> float; uniform(a,b) -> float; spawn(self, tag: int) -> 'Prng'`
- `from_config(cfg: Config) -> Prng`

_Key algorithms:_
- MT19937 seeding; child seed = parent.randint(0,2**31-1) mixed with hash((seed,tag)) through a wide mixer to avoid XOR collisions

_Depends on:_ `random`, `config.py`


#### `src/gojo_infinity/core/exact.py`

Exact integer/Fraction primitives shared by Lens 1 and Lens 2: builds powers of two with the exact shift 1<<n (NEVER float 2.0**n which overflows at n=1024, NEVER 0.5**n which underflows at n=1075), plus ratio validation.


_Public API:_
- `pow2(n: int) -> int  # 1 << n`
- `half_pow(n: int) -> Fraction  # Fraction(1, 1<<n)`
- `one_minus_half_pow(n: int) -> Fraction  # Fraction((1<<n)-1, 1<<n)`
- `validate_ratio(r: Fraction) -> None  # 0<r<1 else ValueError`

_Key algorithms:_
- Exact big-int left shift for denominators; fail-fast ratio guard

_Depends on:_ `fractions`


#### `src/gojo_infinity/core/series.py`

Lens 1 pure core (evolved from prototype zeno.py): exact partial sum S_n=1-(1/2)^n, residual R_n, and general geometric_sum a/(1-r). All exact via Fraction.


_Public API:_
- `partial_sum(n: int, *, ratio=Fraction(1,2)) -> Fraction`
- `residual(n: int, *, ratio=Fraction(1,2)) -> Fraction`
- `partial_sum_table(max_n: int, *, ratio=Fraction(1,2)) -> list[Fraction]`
- `geometric_sum(a: Fraction, r: Fraction) -> Fraction`
- `zeno_series_sum() -> Fraction`
- `verdict() -> Verdict  # FRAGILE`

_Key algorithms:_
- Closed form S_n = 1 - ratio**n and a/(1-r); exact rational arithmetic; ValueError on |r|>=1 (divergence boundary)

_Depends on:_ `core/exact.py`, `verdict.py`, `fractions`


#### `src/gojo_infinity/core/residual_proof.py`

Lens 1 machine-checkable strict-positivity certificate: R_n=(1/2)^n>0 for all finite n, via exact numerator==1 check and inductive R_{n+1}=R_n/2 loop; plus a documented float-failure witness proving 1-0.5**n==1.0 at n=60 and 0.5**1075==0.0.


_Public API:_
- `is_strictly_positive(n: int) -> bool`
- `positivity_certificate(max_n: int) -> list[tuple[int, Fraction]]`
- `inductive_halving_chain(max_n: int) -> bool  # asserts R_next.numerator==1 and R_next<R_prev`
- `float_residual_fails_at(n: int) -> bool  # True where float path spuriously reads 0`

_Key algorithms:_
- Exact positive-rational certificate (numerator always 1); inductive halving invariant; deliberate float cancellation/underflow demonstration

_Depends on:_ `core/series.py`, `core/exact.py`, `fractions`


#### `src/gojo_infinity/core/convergence.py`

Lens 1 epsilon-N oracle: least N with residual (1/2)^N < eps, operationalising S_n->1. Integer doubling for a first guess, then exact Fraction comparison to kill math.log2 off-by-one.


_Public API:_
- `epsilon_N(eps: Fraction, *, ratio=Fraction(1,2)) -> int`
- `residual_below(N: int, eps: Fraction, *, ratio=Fraction(1,2)) -> bool`

_Key algorithms:_
- Double an int until (1<<N)*eps.numerator > eps.denominator; confirm/adjust with exact Fraction(1,1<<N) < eps; guard 0<ratio<1 (no finite witness at ratio>=1)

_Depends on:_ `core/series.py`, `core/exact.py`, `fractions`


#### `src/gojo_infinity/core/arrival_time.py`

Lens 1 arrival-TIME evaluator: shows summed travel TIMES also converge (constant speed v: T=1/v; Achilles: T=d0/(1-r)), the distinction that distance-converges does not by itself imply time-converges. Keeps v an explicit Fraction so the v->0 time-dilation escape hatch is modelled, not silently assumed.


_Public API:_
- `partial_time(n: int, v: Fraction) -> Fraction`
- `total_time_constant_speed(v: Fraction) -> Fraction  # Fraction(1,v)`
- `achilles_total(d0: Fraction, v_achilles: Fraction, v_tortoise: Fraction) -> Fraction`
- `time_residual(n: int, v: Fraction) -> Fraction`

_Key algorithms:_
- T_n = (1/v)*(1-(1/2)^n); Achilles catch-up d0/(1-r) with r=vt/va; assert v>0 (else the barrier is rescued / ZeroDivision) and r<1

_Depends on:_ `core/series.py`, `fractions`


#### `src/gojo_infinity/core/measure.py`

Lens 2 pure core (evolved from prototype measure.py, extended): subdivision set Z, exact cover-interval and total covering lengths, the constructive m(Z)=0 witness, plus NEW exact N_for_error truncation control and a disjointness certificate (eps<2/3).


_Public API:_
- `subdivision_point(n: int) -> Fraction`
- `subdivision_set(count: int) -> list[Fraction]`
- `cover_interval(n: int, eps: Fraction) -> tuple[Fraction,Fraction]`
- `cover_interval_length(n: int, eps: Fraction) -> Fraction`
- `total_cover_length(eps: Fraction, terms: int) -> Fraction`
- `tail(eps: Fraction, terms: int) -> Fraction`
- `N_for_error(eps: Fraction, target: Fraction) -> int`
- `intervals_disjoint(eps: Fraction) -> bool  # eps < Fraction(2,3)`
- `outer_measure_upper_bound(eps: Fraction) -> Fraction  # == eps`
- `lebesgue_measure_of_Z() -> Fraction  # 0`
- `verdict() -> Verdict  # FRAGILE`

_Key algorithms:_
- Finite geometric sum eps*(2^N-1)/2^N with exact self-check against the loop; exact tail eps/2^N; disjointness threshold 3*eps<2; inf over eps->0 gives m(Z)=0

_Depends on:_ `core/exact.py`, `verdict.py`, `fractions`


#### `src/gojo_infinity/core/conformal.py`

Lens 3 metric core (from prototype riemannian.py): RIKEN Gaussian/RBF kernel, conformal factor Omega(x)=1+lam*K(x,x_g)/(x_g-x) with its simple pole at x_g, metric component g11=Omega^2, and felt step. Pure floats; raises for x>=x_g.


_Public API:_
- `gaussian_kernel(x: float, y: float, sigma: float) -> float`
- `conformal_factor(x: float, *, x_gojo, sigma, lam) -> float`
- `metric_g11(x: float, **kw) -> float`
- `felt_step(x: float, dx: float, **kw) -> float`
- `near_pole_asymptote(x: float, *, lam, x_gojo) -> float  # lam/(x_g-x)`

_Key algorithms:_
- Omega = 1 + lam*exp(-(x_g-x)^2/sigma^2)/(x_g-x); fail-fast ValueError at gap<=0 (singularity); asymptote lam/(x_g-x) as x->x_g

_Depends on:_ `config.py`, `math`


#### `src/gojo_infinity/core/quadrature.py`

Lens 3 integrators as separable, testable pieces: composite midpoint (open, handles endpoint pole), trapezoid and adaptive Simpson kept explicitly to DEMONSTRATE failure near the pole, and the recommended singularity_subtraction that extracts the exact -lam*ln term and integrates only the bounded remainder.


_Public API:_
- `midpoint(f: Callable, a: float, b: float, steps: int) -> float`
- `trapezoid(f, a, b, steps) -> float`
- `adaptive_simpson(f, a, b, *, tol, max_depth) -> tuple[float,float,bool]  # (value,err,converged)`
- `singularity_subtracted_length(a: float, b: float, *, lam, sigma, x_gojo) -> float`

_Key algorithms:_
- Composite Newton-Cotes (open midpoint avoids endpoint node); adaptive Simpson with Richardson |S_whole-(S_l+S_r)|/15 and depth cap; singularity subtraction L=[-lam*ln(x_g-x)]_a^b + INT (Omega - lam/(x_g-x)) with Taylor guard r~-lam*(x_g-x)/sigma^2 for |x_g-x|<1e-8

_Depends on:_ `core/conformal.py`, `_optional.py`, `math`


#### `src/gojo_infinity/core/geodesic.py`

Lens 3 felt-length engine (evolved from riemannian.py): geodesic_length via chosen integrator, divergence_by_decade witness (lam*ln(10) per decade), a calibration solver that DERIVES sigma,lam from the essay targets instead of hardcoding, and a geodesic-ball solver proving every finite proper radius R has a solution strictly inside (a, x_g).


_Public API:_
- `geodesic_length(x0: float, cutoff: float, *, method='subtract', x_gojo, sigma, lam, steps) -> float`
- `divergence_by_decade(x0: float, deltas: list[float], **kw) -> list[tuple[float,float]]`
- `per_decade_increment(lam: float) -> float  # lam*ln 10`
- `calibrate(cfg: Config) -> tuple[float,float]  # (sigma,lam) via bisection on g(0.8) target`
- `geodesic_ball(x0: float, R: float, **kw) -> float  # x* with L(x0,x*)=R`
- `verdict() -> Verdict  # FORMIDABLE`

_Key algorithms:_
- Improper integral to x_g returns math.inf explicitly; monotone bisection root-find for both calibration (fit g(0.8)~4.1) and geodesic-ball (L monotone increasing, hi=x_g-eps); each decade adds lam*ln10

_Depends on:_ `core/conformal.py`, `core/quadrature.py`, `config.py`, `verdict.py`, `math`


#### `src/gojo_infinity/core/continuity.py`

Lens 4 continuity analysis (evolved from prototype topology.continuity_at): oscillation-based point classifier CONTINUOUS/JUMP/POLE over shrinking symmetric windows, Aitken one-sided limit extrapolation (never evaluates Omega(c) itself), and a grid-refinement jump-ratio detector.


_Public API:_
- `class PointClass(Enum): CONTINUOUS; JUMP; POLE`
- `oscillation_at(f: Callable, c: float, *, del0, rho, stages, samples) -> tuple[list[float], PointClass]`
- `one_sided_limits(f, c, *, h0, rho, stages) -> tuple[float|None,float|None,float|None]  # (L-,L+,J)`
- `jump_ratio(f, x0, x1, n) -> float  # ->1 jump, ->2^-p continuous`

_Key algorithms:_
- Sampled oscillation osc_k=max-min over (c-del,c+del) with geometric shrink; Aitken delta-squared with near-zero-denominator guard; forward-difference halving ratio |D(h/2)|/|D(h)|

_Depends on:_ `core/conformal.py`, `math`


#### `src/gojo_infinity/core/topology.py`

Lens 4 topological verdict (evolved from prototype topology.py): the World-Cutting-Slash severed factor, immutable domain sever(), connected-components / same_component via interval-union with open-endpoint semantics, and the fact that a geodesic across a cut is UNDEFINED (not infinite).


_Public API:_
- `severed_conformal_factor(x: float, c: float, *, jump, x_gojo) -> float`
- `make_severed_factor(c: float, *, jump, x_gojo) -> Callable`
- `sever(domain: tuple, c: Fraction) -> tuple  # returns NEW domain [lo,c) (c,hi]`
- `connected_components(x0, x1, cut) -> list[tuple]`
- `same_component(domain, p, q) -> bool`
- `geodesic_is_defined(x0, x1, cut) -> bool`
- `severed_geodesic_length(x0, x1, cut) -> None  # undefined`
- `verdict() -> Verdict  # FALLS`

_Key algorithms:_
- Immutable interval split on cut point (half-open [lo,c) and (c,hi], NOT adjacent); union/sweep connectivity where a half-open gap blocks adjacency; undefined (None) not +inf distinguishes severing from divergence

_Depends on:_ `core/conformal.py`, `core/continuity.py`, `verdict.py`, `fractions`


#### `src/gojo_infinity/core/numerics.py`

Pure numeric helpers so stdlib reductions stay accurate without numpy: Kahan compensated summation, math.fsum wrapper, exact/approx isclose helpers, min-max normalization for viz, and reusable float-failure demonstrators (underflow/cancellation thresholds).


_Public API:_
- `kahan_sum(xs: Iterable[float]) -> float`
- `stable_sum(xs) -> float  # math.fsum`
- `isclose_float(a,b,*,rel_tol=1e-9,abs_tol=0.0) -> bool`
- `normalize(v, lo, hi) -> float  # constant-field guard`
- `float_underflow_n() -> int  # 1075`
- `float_cancellation_n() -> int  # 60`

_Key algorithms:_
- Kahan invariant y=x-c; t=s+y; c=(t-s)-y; s=t (O(1)*u error); PEP 485 isclose with mandatory abs_tol near zero; normalize with vmax==vmin guard

_Depends on:_ `math`


#### `src/gojo_infinity/core/montecarlo.py`

Optional reproducible Monte-Carlo cross-checks (injected Prng): estimate the covered fraction / cover-length integrals stochastically and confirm they land within k*sigma/sqrt(N) of the exact Fraction targets, demonstrating the exact core is right without trusting a single method.


_Public API:_
- `estimate_covered_fraction(n: int, prng: Prng, samples: int) -> float`
- `estimate_cover_length(eps: Fraction, terms: int, prng: Prng, samples: int) -> float`
- `standard_error(sigma: float, samples: int) -> float`

_Key algorithms:_
- Uniform sampling with injected MT19937; standard error sigma/sqrt(N); sort any set before iterating to defeat PYTHONHASHSEED

_Depends on:_ `rng.py`, `core/series.py`, `core/measure.py`, `core/numerics.py`


#### `src/gojo_infinity/viz/ascii.py`

Always-on, dependency-free ASCII visualization for every lens, golden-string testable: convergence bar chart of S_n->1 with residual, cover-length ramp toward eps, Omega(x)/cumulative-L profile whose right edge shoots off-scale at the barrier, and a severed sign map showing the two disconnected components after the slash.


_Public API:_
- `render_convergence(rows: list[tuple[int,Fraction,Fraction]], width=60) -> str`
- `render_cover_length(eps: Fraction, max_terms: int) -> str`
- `render_omega_profile(xs, values, width=None) -> str`
- `render_severed_map(x0, x1, cut, width=60) -> str`

_Key algorithms:_
- Ramp ' .:-=+*#%@' indexing with normalize + len-1 clamp; off-scale sentinel for pole/inf; component shading for [x0,c) vs (c,x1]; ASCII-only for stable golden tests

_Depends on:_ `core/series.py`, `core/measure.py`, `core/conformal.py`, `core/numerics.py`


#### `src/gojo_infinity/viz/png.py`

Optional matplotlib PNG renderers (one per lens) that return None when matplotlib is absent, so plotting is never a hard dependency. Agg backend set before pyplot via _optional.


_Public API:_
- `save_convergence_png(rows, path) -> str | None`
- `save_measure_png(eps, terms, path) -> str | None`
- `save_geodesic_png(x0, deltas, path, **kw) -> str | None`
- `save_severed_png(x0, x1, cut, path) -> str | None`

_Key algorithms:_
- Guarded import; numeric result must match ASCII path within tolerance (cross-check test when HAS_MPL)

_Depends on:_ `_optional.py`, `core/series.py`, `core/measure.py`, `core/geodesic.py`


#### `src/gojo_infinity/cli.py`

Thin argparse subcommand adapter (replaces prototype demo.py as an installed entry point): each subcommand parses argv, calls exactly one core function, formats output, and reports a lens verdict. main(argv=None)->int for testability; catches core ValueError at the boundary.


_Public API:_
- `build_parser() -> argparse.ArgumentParser`
- `main(argv: list[str] | None = None) -> int`
- `subcommands: zeno, measure, riemannian, topology, demo, render (--png optional)`

_Key algorithms:_
- add_subparsers + set_defaults(func=handler) dispatch; exit codes 0 ok / 2 usage / 1 domain error; prints format_table(verdicts) for demo

_Depends on:_ `core/*`, `viz/ascii.py`, `viz/png.py`, `verdict.py`, `config.py`, `argparse`


## Data flow

Configuration & determinism enter first: config.Config (frozen) supplies X_GOJO/SIGMA/LAMBDA/SEED/targets; rng.Prng is constructed from the seed and injected wherever randomness is needed (montecarlo only) — never global random.*. The dependency arrow is strictly one-directional: core/ (pure, deterministic, stdlib-only, no top-level numpy) <- adapters (rng, viz, cli). Nothing in core imports an adapter.

Per lens: (1) Lens 1 — cli 'zeno' -> core.series.partial_sum/residual/geometric_sum (exact Fraction) -> core.residual_proof certificate -> core.convergence.epsilon_N -> core.arrival_time totals -> verdict.Verdict(FRAGILE). (2) Lens 2 — cli 'measure' -> core.measure.subdivision_set/total_cover_length/tail/N_for_error/intervals_disjoint -> outer_measure_upper_bound(eps)->eps -> m(Z)=0 -> Verdict(FRAGILE). (3) Lens 3 — cli 'riemannian' -> core.geodesic.calibrate(cfg) derives (sigma,lam) via bisection -> core.conformal.metric_g11/felt_step reproduce Figure-8 -> core.quadrature.singularity_subtracted_length feeds core.geodesic.divergence_by_decade (lam*ln10 per decade) and geodesic_length(x0,x_gojo)=inf -> geodesic_ball proves finite-R solutions -> Verdict(FORMIDABLE). (4) Lens 4 — cli 'topology' -> core.conformal intact factor -> core.continuity.oscillation_at classifies interior point CONTINUOUS -> topology.sever(domain,c) returns a NEW disconnected domain -> continuity.oscillation_at now returns JUMP, topology.same_component False, severed_geodesic_length None (undefined) -> Verdict(FALLS).

Presentation: each lens's numeric rows flow to viz.ascii (always) and optionally viz.png (only if HAS_MPL). montecarlo optionally re-derives Lens 1/2 numbers stochastically from the injected Prng and numerics.stable_sum, asserting agreement within k*sigma/sqrt(N). cli.main aggregates the four Verdicts and prints verdict.format_table. Exactness is preserved end-to-end by keeping Fraction inside core and converting to float only at the viz/cli edge (labelled lossy).


## Testing strategy

pytest with tests/ mirroring the package one-file-per-module, plus test_reproduction.py (headline targets end-to-end) and test_core_purity.py (imports gojo_infinity.core and asserts 'numpy' not in sys.modules, enforcing the core/adapter boundary). Enable executable docstrings via [tool.pytest.ini_options] addopts='--doctest-modules --cov=src/gojo_infinity --cov-report=term-missing', coverage gate 80% (pure core should approach 100%). Assertion discipline: exact == for Fraction/int targets, math.isclose with explicit abs_tol for floats, k*sigma/sqrt(N) for Monte-Carlo. Pinned targets carried over/added: Lens 1 partial_sum_table(8) == [1/2,3/4,7/8,15/16,31/32,63/64,127/128,255/256]; geometric_sum(1/2,1/2)==1 and zeno_series_sum()==1 exactly; residual(n)>0 for n in {0,1,2,10,60,1075,10000}; property test 0<residual(n+1)<residual(n) and residual(n)*2==residual(n-1); epsilon_N(Fraction(1,1000)) confirmed by exact Fraction(1,1<<N)<eps and Fraction(1,1<<(N-1))>=eps; arrival_time total_time_constant_speed(2)==Fraction(1,2), achilles_total(10,2,1)==20; regression witness float_residual_fails_at(1075) and 1-0.5**60==1.0. Lens 2 total_cover_length(1/10,terms)==(1/10)*(1-1/2^terms) with tail==(1/10)/2^terms, partial totals strictly increasing to eps, N_for_error correct, intervals_disjoint(Fraction(1,2)) True and intervals_disjoint(Fraction(9,10)) False, m(Z)==0; float-collapse witness 1-2**-54==1.0 and 1e-300/2.0**80==0.0. Lens 3 metric_g11(0.1)~1.0 (abs 2e-3), metric_g11(0.8)~4.0 (abs 0.15), geodesic_length to X_GOJO is math.inf, divergence_by_decade increments -> lam*ln10=0.6378 (high-res steps to beat pole error), singularity_subtracted matches high-n midpoint below the pole, geodesic_ball returns x* strictly inside (0,X_GOJO) for large R, calibrate() reproduces LAMBDA~0.277, quadrature failure tests assert trapezoid/adaptive-Simpson diverge from analytic -lam*ln as b->x_g. Lens 4 oscillation_at(intact,0.5)->CONTINUOUS, on synthetic Omega=1|2 jump -> JUMP with one_sided_limits J~1.0 and jump_ratio~1; after sever same_component(x0,x1) False, severed_geodesic_length None, connected_components -> two pieces; geodesic_is_defined False across cut. Property tests via Hypothesis (optional): kahan_sum == math.fsum on random lists incl [1e16,1,-1e16]; residual monotonicity; Omega>0 on the sampled domain. viz golden-string tests for each ASCII renderer; cli tested by main(['zeno']) etc. capturing stdout and asserting exit codes (0/2/1). rng test asserts byte-for-byte reproducibility from a fixed seed and independent spawn streams.


## Visualization strategy

ASCII is always available and is the default renderer (pure stdlib, golden-string testable); matplotlib PNG is an optional, import-guarded enhancement selected only when HAS_MPL. Four ASCII views, one per lens, reusing the reference project's ' .:-=+*#%@' ramp and normalize-with-constant-guard idiom: (1) Lens 1 render_convergence draws a horizontal bar per n showing S_n approaching a '1' rule with the residual (1/2)^n annotated, making 'strictly below 1 forever yet -> 1' visible. (2) Lens 2 render_cover_length ramps the partial cover total toward eps as terms grow, showing it never exceeds eps. (3) Lens 3 render_omega_profile plots Omega(x) or cumulative felt length L(x) across [0,x_gojo) with the right-hand column rendered as an off-scale sentinel to signal the divergent barrier. (4) Lens 4 render_severed_map shades the intact interval, then after sever shows two visually separated components with the cut column marked undefined — the 1-D analogue of the reference sign-map / zero-curve renderer. Every renderer converts Fraction->float only at the final formatting step and labels decimals as lossy. PNG counterparts (save_*_png) mirror each view, set the Agg backend before importing pyplot, return None when matplotlib is missing, and are cross-checked against the ASCII numeric data when the dependency is present.


## CLI design

Single ArgumentParser with add_subparsers(dest='command'); each subcommand set_defaults(func=handler); main(argv=None)->int is the installed entry point (pyproject [project.scripts] gojo-infinity = 'gojo_infinity.cli:main'), replacing the prototype demo.py while preserving its output. Subcommands: `zeno [--max-n N] [--eps P/Q]` prints the exact partial-sum/residual table, epsilon_N, arrival-time totals, verdict; `measure [--eps P/Q] [--terms K]` prints Z, cover lengths, tail, N_for_error, disjointness, m(Z)=0, verdict; `riemannian [--x0 F] [--calibrate] [--method subtract|midpoint]` prints Figure-8 g/felt steps, divergence-by-decade table, geodesic_ball demo, verdict; `topology [--x0 F --x1 F --cut C]` prints continuity classification intact vs severed, components, undefined geodesic, verdict; `demo` runs all four and prints verdict.format_table (the prototype's conclusion table); `render <lens> [--png PATH] [--width W]` emits the ASCII view and, if matplotlib present and --png given, also writes the PNG. Exit codes: 0 success, 2 argparse usage error, 1 domain error (core ValueError caught at the boundary and printed as a one-line message, never a traceback). argv is accepted as a parameter so CLI tests pass a list instead of touching sys.argv; handlers hold no math — parse -> call one core function -> format.


## Dependencies

- **Required:** Python 3.10+ standard library only: fractions, math, random, dataclasses, enum, typing, argparse, importlib, pytest (dev/test), pytest-cov (dev/test, 80% gate)
- **Optional:** numpy (import-guarded accelerator for the Lens 3 integral only; core must run without it), matplotlib (import-guarded PNG rendering with Agg backend; ASCII is the always-on fallback), hypothesis (dev/test only, property-based invariants)


## Risks

- Fraction denominator/bit-length growth: ratio**n and 2**n for very large n (e.g. n=10000, 1075) are exact but O(n)-bit; tests use those exact values deliberately — keep them but cap user-facing n in the CLI and document the cost. Never fall back to float for the certificate.
- Quadrature near the pole: midpoint/trapezoid/adaptive-Simpson under-estimate or recurse forever approaching x_gojo. Mitigation: singularity_subtraction is the default, geodesic_length to x_gojo returns math.inf explicitly, adaptive_simpson has a mandatory depth cap and requires b<=x_g-eps; the weak integrators are retained only as labelled failure demonstrations.
- Conflating 'undefined' (severed, None/NaN) with 'infinite' (divergent, +inf): the three verdict return-values (finite / +inf / None) must stay distinct or Lens 3 and Lens 4 collapse into each other. Enforced by type and by test.
- Float regression witnesses are platform-IEEE-754 dependent (n=60 cancellation, n=1075 underflow, n=54 point collapse): assert them as documentation of the failure mode, guarded so they never gate core correctness.
- Migration from flat prototype to src-layout: existing bare imports (import zeno, from riemannian import ...) break under package-relative imports; must convert to from ..core import series etc. and add pip install -e . — the single largest refactor step. test_lenses.py splits into the mirrored per-module test files.
- PYTHONHASHSEED nondeterminism if any RNG draw derives from set/dict iteration order: sort before iterating in montecarlo; pin seed AND sample count N in tests.
- Calibration solver could fail to converge or return a degenerate (sigma,lam); bracket must straddle the target and validate Omega>0, else fall back to config defaults with a clear error.


## No-mock guarantee

Every module computes a real, independently-verifiable quantity — there are no stubs or placeholder returns. verdict.py/config.py are real immutable data + a real table formatter (ported from demo.print_conclusion). exact.py does genuine big-int shift arithmetic. series.py/residual_proof.py/convergence.py/arrival_time.py each implement distinct exact-rational algorithms (closed-form sums, inductive positivity certificate, integer-doubling epsilon-N search, time-series totals) with different pinned targets. measure.py computes real geometric-series cover lengths, exact tails, disjointness thresholds and N_for_error. conformal.py evaluates the actual RIKEN-kernel conformal factor; quadrature.py implements four real integrators (midpoint, trapezoid, adaptive Simpson, singularity subtraction) — the deliberately-weak ones are real algorithms retained to exhibit true numerical failure, not fake code. geodesic.py does real bisection calibration and geodesic-ball root-finding and returns math.inf for the genuinely improper integral. continuity.py runs real sampled-oscillation classification and Aitken extrapolation; topology.py performs real immutable interval severing and interval-union connectivity. numerics.py implements real Kahan summation and PEP-485 isclose; montecarlo.py runs a real seeded MT19937 estimator cross-checked against the exact core. viz/ascii.py renders real normalized character maps (golden-tested); viz/png.py calls real matplotlib when present and honestly returns None when not. cli.py is a real argparse dispatcher wired to those functions. The prototype's four lens modules are reused verbatim where correct and only relocated/extended — no functionality is faked to fill the tree.

