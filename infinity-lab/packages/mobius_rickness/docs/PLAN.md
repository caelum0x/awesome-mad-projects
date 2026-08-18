# mobius-rickness — Build Plan

_Phased plan synthesized from the architecture. Each phase lists deliverables and acceptance criteria tied to the resolved math targets._


## Phase 1: M1 - Package scaffold, src-layout migration, vectors, and shared infrastructure

**Goal.** Convert the flat prototype (geometry.py, mobius.py, torus.py, rickness.py, field.py, curve.py, ascii_heatmap.py, demo.py, test_central_finite_curve.py) into installable src-layout package mobius_rickness, extracting immutable vector primitives and standing up the adapter shells and the purity guard.


**Deliverables**
- pyproject.toml (scripts mobius-rickness=mobius_rickness.cli:main, optional viz=[numpy,matplotlib], dev=[pytest,pytest-cov,hypothesis])
- __init__.py, _optional.py (HAS_NUMPY/HAS_MPL, get_numpy, Agg before pyplot)
- config.py (frozen Config: domain bounds, n_u/n_v, Rickness weights, seed, three independent tolerances grid-h/root-eps/continuation-ds), rng.py (Prng + spawn + sample_domain), io.py (JSON load/save with boundary validation)
- core/vectors.py (Vec3 alias, sub/scale/dot/cross/norm returning fresh tuples)
- conftest.py, tests/test_core_purity.py, ARCHITECTURE.md

**Acceptance.** pip install -e . succeeds and `import mobius_rickness` works with neither numpy nor matplotlib installed (verified on Python 3.11+); test_core_purity asserts 'numpy' not in sys.modules after `import mobius_rickness.core`; every vector op returns a new tuple (immutability, no in-place mutation).


## Phase 2: M2 - Three cross-validating curvature paths: analytic oracle, numeric FD, complex-step, seam domain

**Goal.** Supply the closed-form analytic oracle the prototype lacks (its single biggest correctness upgrade), refactor the central-difference path, add the cancellation-free complex-step path, and encode the non-orientable Mobius seam and one-sided boundary stencils. Honest caveat: the strip is ruled so K<0 on the whole interior.


**Deliverables**
- core/analytic.py (E=(1+v cos(u/2))^2+v^2/4, first_form=(E,0,1), M=-1/(2 sqrt E), K=-1/(4E^2), triple_product=-0.5, require_embedded w<1, guard E>0)
- core/numeric.py (central-diff partials, fundamental_forms, gaussian_curvature, split optimal steps first ~(3eps)^(1/3) and second ~(48eps)^(1/4)~1e-4)
- core/complexstep.py (r_u_cs/r_v_cs via cmath h=1e-200, first_form_cs; documented analyticity precondition)
- core/domain.py (wrap seam u'=u-2pi*k with v flipped if k odd, one_sided_v 3-point stencils, validate |v|<w<1, bounds constants)
- tests: test_analytic, test_numeric, test_complexstep, test_domain

**Acceptance.** K(u,0)==-0.25 (analytic ==, numeric isclose to 4 places); F==0 and G==1 to ~1e-12, N==0 to ~1e-9, M==-1/(2 sqrt E), triple_product==-0.5; min|K| on the strip at |v|=0.5 ~ -0.0467 (verified: -0.04675); FD-vs-analytic |K_fd-K_analytic|<1e-6 over seeded random (u,v) with pinned seed AND sample count, plus a U-shaped error-vs-h curve; complex-step matches central diff to 10 digits; seam identity r(2pi,v)==r(0,-v) and wrap flips v; require_embedded raises for w>=1. Caveat encoded: K<0 asserted across the whole interior grid.


## Phase 3: M3 - Surfaces and fields: mobius, torus, rickness, weighted curvature, zeno, numerics

**Goal.** Wire the parametrizations to their curvature accessors, add the sign-changing Rickness field whose zero set is the Central Finite Curve, form the weighted curvature KR, and add the exact Gojo-Infinity Fraction link.


**Deliverables**
- core/mobius.py (surface, gaussian_curvature analytic default, gaussian_curvature_fd, fundamental_forms, bounds)
- core/torus.py (surface, gaussian_curvature_closed K=cos th/(r0(R0+r0 cos th)), sign_pattern, zero_circles=(pi/2,3pi/2), require_ring raises for R0<=r0)
- core/rickness.py (rickness=cos u+0.4 v cos(u/2)+0.2 sin u, rickness_naive kept as doc, column_coeffs A/B, column_root v*=-A/B, k_rick)
- core/weighted.py (KR=K*R, evaluate_grid, assert_mobius_K_negative, field_range) absorbing field.py
- core/numerics.py (kahan_sum, fsum, isclose_exact, normalize with constant-field guard, linspace); core/zeno.py (geometric_sum, partial_sum, residual via Fraction, guard |r|<1)
- tests: test_mobius, test_torus, test_rickness, test_weighted, test_numerics, test_zeno

**Acceptance.** torus numeric vs closed-form <1e-5 with K==0 exactly at theta=pi/2,3pi/2 and correct +/-/0 sign pattern; require_ring raises for R0<=r0 (not the prototype's silent 0.0); rickness sign-changes across the domain and column_root v*=-A/B agrees with bisection; KR==0 iff R==0 and KR<0 where R>0 (caveat: because K<0 everywhere, the curve is Zero(R), documented explicitly); kahan_sum==math.fsum on [1e16,1,-1e16]; zeno.geometric_sum(1/2,1/2)==1 EXACTLY (Fraction ==) and residual r^n>0.


## Phase 4: M4 - Curve-tracing pipeline: bisection, marching-squares, stitch, continuation, lift

**Goal.** Turn R into an explicit, verified curve: reuse scan-line bisection, add marching-squares topology with saddle disambiguation, segment stitching, seam-aware predictor-corrector continuation, and 3D lifting. Honest caveats: seam v-flip must be applied in the tracer, saddle cases 5/10 need the asymptotic decider, and singular points ||grad R||->0 must be guarded.


**Deliverables**
- trace/bisection.py (bisect, find_roots_in_v, scan_columns; Bolzano bracket, ValueError on non-bracket)
- trace/marching_squares.py (Segment, march with 16-case table, edge crossing t=F_A/(F_A-F_B), asymptotic decider for cases 5/10)
- trace/stitch.py (stitch via grid-hash snap ~h/4 into ordered polylines/components, seeds one per component)
- trace/continuation.py (grad, newton_correct, trace_component with tangent T=(R_v,-R_u)/||grad||, Euler predictor, minimal-norm Newton corrector, seam wrap+v-flip each step, adaptive ds, closed-loop termination, singular-point guard, max_steps cap)
- trace/lift.py (lift via mobius.surface, Kahan-summed arc_length); trace/pipeline.py (trace_mobius_curve hybrid, trace_torus_zero_circles, verify_curve)
- tests: test_bisection, test_marching_squares, test_stitch, test_continuation, test_lift, test_pipeline

**Acceptance.** bisect finds sqrt(2) and raises ValueError on a non-bracket; marching-squares component count matches the analytic zero set and scan-line bisection (cross-check); stitch orders a closed loop vs an open arc correctly; every continuation point |R|<1e-8, closed loops return within ds, and seam continuity holds across u=0/2pi (no spurious high-curvature seam); lifted points match surface to 1e-9 with arc_length>0; verify_curve asserts |R|<1e-6 and |k_rick|<1e-6 at every point; continuation is bounded by max_steps and the singular-point guard (no hang).


## Phase 5: M5 - Optional ridge, viz (ASCII+PNG), CLI, IO, end-to-end reproduction

**Goal.** Add the honestly-labelled Eberly/SCMS ridge as an optional-advanced alternative, the always-on ASCII and guarded PNG renderers, the argparse CLI, JSON IO, and one reproduction test pinning every research constant.


**Deliverables**
- ridge.py (hessian, jacobi_eigsym pure-stdlib 2x2/3x3, scms_step, trace_ridge; labelled as ridge/crest NOT literal argmax)
- viz/ascii.py (render heatmap + render_sign_map with O-overlay zero curve, constant-field guard, column downsampling, ~2:1 aspect) and viz/png.py (guarded, returns None without matplotlib, Agg before pyplot)
- cli.py (subcommands curvature/forms/trace/render/series/torus/verify, main(argv)->int, exit 0/2/1, ValueError caught at boundary)
- io.py round-trip wired; tests: test_ridge, test_viz_ascii, test_cli, test_io, test_reproduction; README quickstart

**Acceptance.** SCMS converges onto the known ridge of a Gaussian bump (ridge clearly documented as crest, not argmax); viz golden strings stable with constant-field guard; main([...]) returns exit 0 for valid commands, 2 for usage errors, 1 for domain ValueError (|v|>=w, |r|>=1) printed as one line; io JSON round-trips and rejects bad input fail-fast; `verify` subcommand runs the full invariant battery (K<0, seam identity, reproduced constants) and exits nonzero on failure; test_reproduction pins K(u,0)=-0.25, F=0/G=1/N=0, M=-1/(2 sqrt E), triple=-0.5, FD-vs-analytic <1e-6, zeno==1, seam identity in one place; coverage gate >=80%.


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

