# gojo-infinity — Build Plan

_Phased plan synthesized from the architecture. Each phase lists deliverables and acceptance criteria tied to the resolved math targets._


## Phase 1: G1 - Package scaffold, src-layout migration, and shared infrastructure

**Goal.** Convert the flat prototype (zeno.py, measure.py, riemannian.py, topology.py, demo.py, test_lenses.py) into an installable src-layout package gojo_infinity with the core/adapter boundary physically enforced, before any math is touched.


**Deliverables**
- pyproject.toml (PEP 621, scripts gojo-infinity=gojo_infinity.cli:main, optional viz=[numpy,matplotlib], dev=[pytest,pytest-cov,hypothesis])
- src/gojo_infinity/__init__.py (__version__, __all__, thin re-exports)
- _optional.py (HAS_NUMPY/HAS_MPL via try/except ImportError, get_pyplot sets matplotlib.use('Agg') before pyplot)
- config.py (frozen Config: X_GOJO=1.0, sigma=0.35, lam=0.277, seed=0, midpoint_steps=20000, calib targets (0.1,1.0)/(0.8,4.1))
- verdict.py (frozen Verdict, LensVerdict enum Fragile/Formidable/Falls, format_table ported from demo.print_conclusion)
- rng.py (Prng over random.Random(seed) with deterministic spawn(tag))
- conftest.py fixtures; tests/test_core_purity.py; ARCHITECTURE.md documenting the dependency rule
- pip install -e . working; bare-interpreter import verified

**Acceptance.** pip install -e . succeeds; `import gojo_infinity` works on an interpreter with no numpy/matplotlib; test_core_purity asserts 'numpy' not in sys.modules after `import gojo_infinity.core`; verdict.format_table reproduces the prototype conclusion-table layout; Verdict no longer imported from any lens module.


## Phase 2: G2 - Lens 1: exact series, positivity certificate, epsilon-N oracle, arrival time (verdict FRAGILE)

**Goal.** Port zeno.py into exact-Fraction core modules and add the research-demanded capabilities the prototype lacks: an epsilon-N convergence oracle, an arrival-TIME evaluator, and a machine-checkable strict-positivity certificate with float-failure witnesses.


**Deliverables**
- core/exact.py (pow2=1<<n, half_pow, one_minus_half_pow, validate_ratio; big-int shift never 2.0**n)
- core/series.py (partial_sum=1-(1/2)^n, residual, partial_sum_table, geometric_sum=a/(1-r), zeno_series_sum, ValueError on |r|>=1)
- core/residual_proof.py (is_strictly_positive, positivity_certificate, inductive_halving_chain, float_residual_fails_at)
- core/convergence.py (epsilon_N via integer doubling then exact Fraction confirm, residual_below)
- core/arrival_time.py (partial_time, total_time_constant_speed=1/v, achilles_total=d0/(1-r), guard v>0)
- tests: test_series, test_residual_proof, test_convergence, test_arrival_time

**Acceptance.** partial_sum_table(8)==[1/2,3/4,7/8,15/16,31/32,63/64,127/128,255/256] exactly (Fraction ==); geometric_sum(1/2,1/2)==1 and zeno_series_sum()==1 exactly; residual(n)>0 for n in {0,1,2,10,60,1075,10000} with residual(n)*2==residual(n-1); epsilon_N(1/1000) confirmed by Fraction(1,1<<N)<eps and Fraction(1,1<<(N-1))>=eps; total_time_constant_speed(2)==Fraction(1,2), achilles_total(10,2,1)==20; documented witnesses float_residual_fails_at(1075) and 1-0.5**60==1.0 assert as failure-mode docs, not correctness gates.


## Phase 3: G3 - Lens 2: exact Lebesgue covering engine (verdict FRAGILE)

**Goal.** Evolve measure.py into an exact covering-length core that constructively proves m(Z)=0, extended with N-for-error truncation control and a disjointness certificate.


**Deliverables**
- core/measure.py (subdivision_point/set, cover_interval[_length], total_cover_length=eps*(2^N-1)/2^N, tail=eps/2^N, N_for_error, intervals_disjoint eps<2/3, outer_measure_upper_bound==eps, lebesgue_measure_of_Z==0, verdict FRAGILE)
- tests/test_measure.py pinning the exact geometric-sum self-check against the loop

**Acceptance.** total_cover_length(1/10,terms)==(1/10)*(1-1/2^terms) with tail==(1/10)/2^terms (Fraction ==); partial totals strictly increasing and never exceeding eps; N_for_error correct; intervals_disjoint(1/2) True and intervals_disjoint(9/10) False; outer_measure_upper_bound(eps)==eps and inf over eps->0 gives m(Z)==0; float-collapse witnesses 1-2**-54==1.0 and 1e-300/2.0**80==0.0 assert as docs only.


## Phase 4: G4 - Lens 3: Riemannian conformal geometry, quadrature, geodesics, calibration (verdict FORMIDABLE)

**Goal.** Port riemannian.py into a metric core plus separable integrators, and add the honest singularity-subtraction quadrature, an inf-returning improper geodesic, a bisection calibration solver that DERIVES (sigma,lam), and a geodesic-ball solver. Weak integrators are retained only to demonstrate their failure near the pole.


**Deliverables**
- core/conformal.py (gaussian_kernel, conformal_factor Omega=1+lam*K/(x_g-x), metric_g11=Omega^2, felt_step, near_pole_asymptote=lam/(x_g-x); ValueError at gap<=0)
- core/quadrature.py (midpoint open, trapezoid, adaptive_simpson with mandatory depth cap and b<=x_g-eps, singularity_subtracted_length extracting -lam*ln term with Taylor guard for |x_g-x|<1e-8)
- core/geodesic.py (geodesic_length returns math.inf to x_gojo, divergence_by_decade, per_decade_increment=lam*ln10, calibrate via bisection, geodesic_ball root-find, verdict FORMIDABLE)
- tests: test_conformal, test_quadrature, test_geodesic

**Acceptance.** metric_g11(0.1) isclose 1.0 (abs 2e-3), metric_g11(0.8) isclose ~4.0 (abs 0.15); geodesic_length(x0,X_GOJO) is exactly math.inf (type-distinct from None and from finite); divergence_by_decade increments -> lam*ln10=0.6378 (verified numerically); singularity_subtracted matches high-n midpoint below the pole; calibrate() reproduces lam~0.277; geodesic_ball returns x* strictly inside (0,X_GOJO) for large R; FAILURE tests assert trapezoid/adaptive-Simpson diverge from the analytic -lam*ln as b->x_g (caveat: these are labelled demonstrations, not the default path).


## Phase 5: G5 - Lens 4: continuity classification and topological severing (verdict FALLS)

**Goal.** Evolve topology.py into an oscillation-based continuity classifier with Aitken one-sided limits and an immutable interval-severing/connectedness engine, keeping 'undefined' (None) strictly distinct from 'infinite' (+inf).


**Deliverables**
- core/continuity.py (PointClass enum, oscillation_at with geometric shrink, one_sided_limits via Aitken with near-zero-denominator guard, jump_ratio)
- core/topology.py (severed_conformal_factor, make_severed_factor, immutable sever(domain,c) -> half-open [lo,c)/(c,hi], connected_components, same_component, geodesic_is_defined, severed_geodesic_length returns None, verdict FALLS)
- tests: test_continuity, test_topology

**Acceptance.** oscillation_at(intact,0.5)->CONTINUOUS; on synthetic Omega=1|2 jump -> JUMP with one_sided_limits J~1.0 and jump_ratio~1; after sever same_component(x0,x1) False and connected_components yields two pieces; severed_geodesic_length is None (undefined), asserted type-distinct from the math.inf of G4; geodesic_is_defined False across the cut.


## Phase 6: G6 - Adapters: numerics, Monte-Carlo cross-check, viz (ASCII+PNG), CLI, end-to-end reproduction

**Goal.** Add the leaf adapters and the numeric helpers, then lock all four lenses' headline targets with one end-to-end reproduction test and enforce the 80% coverage gate.


**Deliverables**
- core/numerics.py (kahan_sum, stable_sum=math.fsum, isclose_float with mandatory abs_tol, normalize with constant-field guard, float_underflow_n=1075, float_cancellation_n=60)
- core/montecarlo.py (estimate_covered_fraction, estimate_cover_length, standard_error, injected Prng, sorted iteration to defeat PYTHONHASHSEED)
- viz/ascii.py (render_convergence, render_cover_length, render_omega_profile with off-scale pole sentinel, render_severed_map) and viz/png.py (guarded, returns None without matplotlib)
- cli.py (argparse subcommands zeno/measure/riemannian/topology/demo/render, main(argv)->int, exit codes 0/2/1)
- tests: test_numerics, test_montecarlo, test_rng, test_viz_ascii, test_cli, test_reproduction; README quickstart + four-lens table

**Acceptance.** kahan_sum==math.fsum on [1e16,1,-1e16]; Monte-Carlo estimates land within k*sigma/sqrt(N) of exact Fraction targets with pinned seed AND sample count; viz golden strings stable and ASCII-only; main(['zeno']) etc. return exit 0, usage errors 2, domain ValueError caught and printed as one line (exit 1); test_reproduction pins all four verdicts and headline numbers end-to-end; pytest --cov gate >=80% (pure core approaches 100%).


## Shared conventions

- Directory & layout: identical src-layout (src/<pkg>/), core/ subpackage for pure math, adapters at top level; tests/ mirror the package one-file-per-module plus a shared test_reproduction.py and test_core_purity.py; ARCHITECTURE.md documents the dependency rule in both repos.
- Dependency rule (enforced by test): core/ is pure, deterministic, stdlib-only and NEVER imports numpy, matplotlib, or any adapter; adapters (rng, io, viz, cli) depend on core, never the reverse; test_core_purity asserts 'numpy' not in sys.modules after importing <pkg>.core.
- Optional dependencies: a single _optional.py exposes HAS_NUMPY/HAS_MPL via try/except ImportError (never a bare except); matplotlib.use('Agg') is called before importing pyplot; every PNG renderer returns None (never raises) when matplotlib is absent; ASCII is the always-on guaranteed fallback.
- Exactness discipline: use fractions.Fraction and integer bit-shifts (1<<n) for rational targets, converting to float only at the viz/cli edge and labelling it lossy; never use 2.0**n or 0.5**n where an exact path exists. Both packages carry the geometric_sum(1/2,1/2)==1 exact target.
- Immutability: frozen dataclass Config as the single source of knobs, dataclasses.replace for copies, vector/verdict/domain operations return new objects and never mutate in place (per coding-style rule).
- Determinism: never call module-level random.*; inject a Prng wrapper over random.Random(seed) with deterministic spawn(tag); sort any set/dict before iterating to defeat PYTHONHASHSEED; pin BOTH seed and sample count N in Monte-Carlo/random tests.
- Assertion policy: exact == for Fraction/int targets; math.isclose with an explicit mandatory abs_tol for floats near zero; k*sigma/sqrt(N) for Monte-Carlo; FD/geometry float tolerances kept at ~1e-5..1e-6 (not 1e-12) to avoid flakiness from step-size coupling.
- Distinct result semantics: keep finite value / math.inf (divergent) / None (undefined) strictly type-distinct across modules — Gojo Lens 3 vs Lens 4 and Mobius singular vs improper cases must never collapse into one another; enforce by type and by test.
- CLI contract: single argparse ArgumentParser with add_subparsers and set_defaults(func=handler); main(argv=None)->int accepts an argv list for testability; exit codes 0 ok / 2 usage / 1 domain error; core ValueError caught at the boundary and printed as a one-line message, never a traceback; handlers hold no math (parse -> one core call -> format).
- Testing & tooling: pytest with addopts including --doctest-modules and --cov, coverage gate 80% (pure core approaches 100%); TDD RED->GREEN->REFACTOR; optional Hypothesis property tests for invariants (Gojo residual monotonicity / Omega>0; Mobius K<0 on the grid, kahan_sum==fsum).
- Migration method: both prototypes are flat with bare imports; do a single mechanical refactor pass converting to package-relative imports (from ..core import ...), add pip install -e ., split the monolithic test file into mirrored per-module tests, and lock the new boundary with test_core_purity immediately after.
- Honesty about caveats: retain deliberately-weak algorithms (Gojo trapezoid/adaptive-Simpson, rickness_naive, the Mobius ridge) only as clearly-labelled demonstrations or alternatives, never as the default correctness path, with docstrings stating why they fail or what they actually compute.


## Open questions

- Python floor: gojo-infinity states 3.10+ while mobius-rickness states 3.11+ (verified on 3.14). Should both be pinned to a single minimum (e.g. 3.11) for a uniform CI matrix, or kept independent?
- Fraction denominator/bit-length blow-up: both packages deliberately test huge exact n (Gojo n=1075/10000; Mobius zeno partial_sum). Confirm the CLI should cap user-facing n (and at what value) while tests keep the exact large-n cases, and whether a float fallback past a threshold is acceptable or forbidden.
- IEEE-754 float-failure witnesses (n=60 cancellation, n=1075/1024 underflow, n=54 collapse) are platform-dependent. Confirm they should be asserted as documentation guarded so they never gate core correctness, and whether any non-x86/ARM platform must be supported.
- Repository structure: should these ship as two independent repos/packages, or a single monorepo with a shared internal 'commons' package for the duplicated _optional/config/rng/numerics/viz skeleton? The two designs currently duplicate that infrastructure verbatim.
- numpy's exact role: in both specs numpy is an optional accelerator that must produce identical numbers to the pure path. Confirm whether numpy acceleration is in-scope for the first delivery at all, or deferred until the pure core is locked.
- Gojo calibration: calibrate() derives (sigma,lam) by bisection to fit g(0.8)~4.1. If the bracket fails to straddle the target or yields a degenerate (sigma,lam), should it hard-fail or fall back to Config defaults with a warning? The risk note lists both.
- Mobius ridge module: is the Eberly/SCMS ridge in scope for the initial deliverable (it is the most numerically delicate component and flagged optional-advanced), or should it be deferred behind the level-set 'wall' tracer?
- Coverage target for adapters: the 80% gate is global but pure core should approach 100%. Confirm whether viz/png and matplotlib-only branches (unreachable without the optional dep in CI) may be excluded from coverage or must be exercised in a viz-enabled CI job.

