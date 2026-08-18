# mobius-rickness — Architecture

_Target architecture designed by the planning workflow from the resolved mathematics. A working prototype already exists; this is the fuller structure it evolves into. Every module has a real responsibility — no mock code._


## Overview

A stdlib-first Python package that computes the differential geometry of the Mobius strip and torus and traces the "Central Finite Curve" as an honest zero set, echoing Gojo's Infinity (convergent series) and Rick & Morty's Central Finite Curve. The target evolves the existing flat prototype (geometry.py, mobius.py, torus.py, rickness.py, field.py, curve.py, ascii_heatmap.py, demo.py, test_central_finite_curve.py) into an importable src-layout package `mobius_rickness` with a strict PURE-MATH core / thin-adapter split. The core is deterministic, stdlib-only (math, cmath, fractions), and carries three independent curvature paths that cross-validate: (1) an exact closed-form analytic oracle K=-1/(4E^2) with E=(1+v cos(u/2))^2+v^2/4 — MISSING from the prototype and the single biggest correctness upgrade; (2) the existing central-difference finite-difference path; (3) a cancellation-free complex-step first-derivative path. On top of that sits a full zero-set tracing pipeline (scan-line bisection — reused from curve.py — plus NEW marching-squares topology, segment stitching, and predictor-corrector continuation) that is Mobius-seam-aware via the gluing r(2pi,v)=r(0,-v). Adapters (config, rng, io, viz/ascii, viz/png, cli) depend on the core, never the reverse. numpy/matplotlib are import-guarded behind capability flags with pure-stdlib fallbacks so the package imports and every command runs on a bare interpreter (verified: Python 3.14, no numpy/matplotlib). A pytest suite pins the reproduced numeric targets from the research (K(u,0)=-1/4, F=0, G=1, N=0, M=-1/(2 sqrt E), triple product=-1/2, analytic-vs-FD max error <1e-6, seam identity, geometric_sum(1/2,1/2)==1 exact).


## Directory layout

```
mobius-rickness/
├── pyproject.toml                # PEP 621; scripts=mobius-rickness=...cli:main; [optional-dependencies] viz=[numpy,matplotlib], dev=[pytest,pytest-cov,hypothesis]
├── README.md                     # quickstart, one runnable example, install (pip install -e .[viz])
├── ARCHITECTURE.md               # core/adapter dependency rule, reproducibility contract, optional-dep policy, module table
├── conftest.py                   # shared fixtures: seeded Prng, sample Config, tolerance constants
├── src/
│   └── mobius_rickness/
│       ├── __init__.py           # __version__, __all__, thin re-export of core public API
│       ├── _optional.py          # HAS_NUMPY / HAS_MPL flags via guarded imports; matplotlib.use('Agg') before pyplot
│       ├── config.py             # frozen dataclass Config (domain bounds, grid sizes, weights, seed, tolerances)
│       ├── rng.py                # Prng wrapper over random.Random(seed) + deterministic spawn()
│       ├── io.py                 # load/save params & traced curves as JSON; schema-validate at boundary
│       ├── cli.py                # argparse subcommands: curvature | forms | trace | render | series | torus | verify
│       ├── core/
│       │   ├── __init__.py
│       │   ├── vectors.py        # Vec3 sub/scale/dot/cross/norm — immutable tuple helpers (extracted from geometry.py)
│       │   ├── analytic.py       # [NEW] closed-form E, first_form, second_form_M, K oracle, embedding guard
│       │   ├── numeric.py        # central-difference partials, fundamental_forms, K_fd (refactor of geometry.py)
│       │   ├── complexstep.py    # [NEW] cancellation-free r_u/r_v via cmath; E,F,G
│       │   ├── domain.py         # [NEW] Mobius seam wrap (2pi,v)~(0,-v); one-sided v-boundary stencils; input validation
│       │   ├── mobius.py         # surface + curvature (delegates analytic/numeric); bounds (refactor)
│       │   ├── torus.py          # torus surface + closed-form K(theta); sign_pattern; zero_circles (refactor)
│       │   ├── rickness.py       # sign-changing R(u,v)=A(u)+B(u)v, closed-form column root, k_rick (refactor)
│       │   ├── weighted.py       # [NEW] KR(u,v)=K*R; theory assertion Zero(KR)=Zero(R); grid evaluation (absorbs field.py)
│       │   ├── numerics.py       # [NEW] kahan_sum, fsum wrapper, isclose helpers, normalize, linspace
│       │   └── zeno.py           # [NEW] geometric_sum/partial_sum via fractions.Fraction (Gojo-Infinity exact target)
│       ├── trace/
│       │   ├── __init__.py
│       │   ├── bisection.py      # scan-line IVT bracketing + bisection (reuse of curve.py bisect/find_roots_in_v)
│       │   ├── marching_squares.py # [NEW] 16-case contour, linear edge crossing, asymptotic saddle decider
│       │   ├── stitch.py         # [NEW] hash-snap endpoints -> ordered polylines / connected components
│       │   ├── continuation.py   # [NEW] predictor-corrector pseudo-arclength tracer (seam-aware)
│       │   ├── lift.py           # [NEW] lift (u,v)->3D via mobius.surface; polyline arc length
│       │   └── pipeline.py       # [NEW] hybrid: marching-squares seeds -> stitch -> continuation, bisection fallback; verify_curve
│       ├── ridge.py              # [NEW, optional-advanced] Eberly height-ridge + SCMS (2x2/3x3 Jacobi eigensolver)
│       └── viz/
│           ├── __init__.py
│           ├── ascii.py          # always-on heatmap + sign-map renderer (refactor of ascii_heatmap.py)
│           └── png.py            # matplotlib-guarded PNG heatmap + 3D curve (refactor of ascii_heatmap.py)
└── tests/
    ├── test_vectors.py
    ├── test_analytic.py          # F=0,G=1,N=0,M=-1/(2 sqrt E),triple=-1/2,K(u,0)=-1/4,embedding guard
    ├── test_numeric.py           # FD vs analytic max err<1e-6; U-shaped error-vs-h curve
    ├── test_complexstep.py       # complex-step matches central diff to 10 digits
    ├── test_domain.py            # seam identity r(2pi,v)=r(0,-v); wrap flips v; one-sided stencils O(h^2)
    ├── test_mobius.py
    ├── test_torus.py             # numeric vs closed-form <1e-5; zeros at pi/2,3pi/2; sign pattern
    ├── test_rickness.py          # sign change; closed-form column root v*=-A/B vs bisection
    ├── test_weighted.py          # KR=0 iff R=0; KR<0 where R>0
    ├── test_numerics.py          # kahan_sum==math.fsum on [1e16,1,-1e16]
    ├── test_zeno.py              # geometric_sum(1/2,1/2)==1 exact (Fraction ==); residual r^n>0
    ├── test_bisection.py         # sqrt(2) root; ValueError on non-bracket
    ├── test_marching_squares.py  # component count vs analytic zero set; saddle resolution
    ├── test_stitch.py            # closed loop vs open arc ordering
    ├── test_continuation.py      # every traced |R|<1e-8; closed-loop return within ds; seam continuity
    ├── test_lift.py              # lifted points match surface to 1e-9; arc length > 0
    ├── test_pipeline.py          # marching-squares & scan-line agree on component count
    ├── test_ridge.py             # SCMS converges onto known ridge of a Gaussian bump
    ├── test_viz_ascii.py         # golden-string heatmap/sign-map; constant-field guard
    ├── test_cli.py               # main([...]) exit codes; stdout contains expected values
    ├── test_io.py                # round-trip JSON; boundary validation rejects bad input
    ├── test_core_purity.py       # import core -> assert 'numpy' not in sys.modules
    └── test_reproduction.py      # pins all analytic constants from the research in one place
```


## Modules

| Path | Responsibility | Tests |
|---|---|---|
| `src/mobius_rickness/core/vectors.py` | Immutable 3D vector primitives shared by every geometry path; each op RETURNS A NEW TUPLE and never mutates (coding-style immutability rule). Extracted from the prototype's geometry.py so vector math lives in one place. | `tests/test_vectors.py` |
| `src/mobius_rickness/core/analytic.py` | [NEW — critical] The closed-form ground-truth ORACLE for the Mobius strip. Implements the research's exact scalars so every numerical path can be validated to machine precision and the prototype's missing analytic layer is supplied. | `tests/test_analytic.py` |
| `src/mobius_rickness/core/numeric.py` | Surface-agnostic numeric Gaussian curvature via central finite differences of the first/second fundamental forms; the general-purpose path used to cross-check the oracle and to handle swapped non-analytic surfaces. Refactor of the prototype geometry.py. | `tests/test_numeric.py` |
| `src/mobius_rickness/core/complexstep.py` | [NEW] Cancellation-free first derivatives via the complex-step trick (cos/sin are entire), giving a rock-solid first fundamental form and normal direction, matched to central differences to 10 digits. | `tests/test_complexstep.py` |
| `src/mobius_rickness/core/domain.py` | [NEW] Encodes the non-orientable Mobius domain: the seam gluing r(2pi,v)=r(0,-v), the index/wrap map used by periodic stencils and tracers, one-sided 3-point v-boundary stencils, and fail-fast input validation (u real, |v|<w<1). | `tests/test_domain.py` |
| `src/mobius_rickness/core/mobius.py` | The Mobius strip itself: the standard ruled parametrization plus curvature accessors that delegate to the analytic oracle (default) or the numeric path (cross-check). Refactor of prototype mobius.py. | `tests/test_mobius.py` |
| `src/mobius_rickness/core/torus.py` | The torus as the non-ruled counterpoint with sign-changing curvature: exact closed form, numeric cross-check, sign pattern, and the geometry-driven zero circles theta=pi/2,3pi/2. Refactor of prototype torus.py. | `tests/test_torus.py` |
| `src/mobius_rickness/core/rickness.py` | The sign-changing Rickness field R(u,v) whose zero set IS the Central Finite Curve (because K<0 everywhere on the Mobius interior), plus its closed-form per-column root. Refactor of prototype rickness.py; keeps rickness_naive to document why the +1.5 version had no zero. | `tests/test_rickness.py` |
| `src/mobius_rickness/core/weighted.py` | [NEW] The weighted curvature KR=K*R and the grid evaluation of K,R,KR (absorbs prototype field.py). Encodes the theorem Zero(KR)=Zero(R) on the Mobius strip and Zero(KR) contains K^{-1}(0) on the torus, and the invariant K<0 on the interior. | `tests/test_weighted.py` |
| `src/mobius_rickness/core/numerics.py` | [NEW] Stdlib numeric utilities used across core and adapters when numpy is absent: accurate summation, approximate-equality helpers, normalization, and linspace (extracted from field.py). | `tests/test_numerics.py` |
| `src/mobius_rickness/core/zeno.py` | [NEW] The Gojo-Infinity link realized as an EXACT reproduced target: the convergent geometric series with fractions.Fraction, so tests assert equality with == rather than a tolerance. | `tests/test_zeno.py` |
| `src/mobius_rickness/trace/bisection.py` | 1D scan-line root finding: reduce R(u_i,.) to g(v), detect Bolzano sign changes, refine each bracket by bisection to ~1e-9. Reuse of prototype curve.py bisect/find_roots_in_v; also used as the robust fallback and seed source. | `tests/test_bisection.py` |
| `src/mobius_rickness/trace/marching_squares.py` | [NEW] Global contour topology of R=0 over a (u,v) grid: 16-case classification, linear edge crossings, asymptotic saddle disambiguation — discovers every component (including closed loops) the single-direction v-scan misses. | `tests/test_marching_squares.py` |
| `src/mobius_rickness/trace/stitch.py` | [NEW] Convert unordered marching-squares segments into ordered polylines, one per connected component, and emit exactly one seed per component for continuation. | `tests/test_stitch.py` |
| `src/mobius_rickness/trace/continuation.py` | [NEW] Predictor-corrector pseudo-arclength tracer producing an ordered, uniformly arc-length-sampled, high-accuracy polyline; seam-aware and adaptive; the rigorous 'real curve' path. | `tests/test_continuation.py` |
| `src/mobius_rickness/trace/lift.py` | [NEW] Lift traced parameter-space points to the physical 3D strip and measure lifted arc length. Isolated so tracing stays surface-agnostic. | `tests/test_lift.py` |
| `src/mobius_rickness/trace/pipeline.py` | [NEW] Hybrid orchestration = coverage + accuracy: marching-squares for seeds/topology -> stitch -> Newton-polish + continuation, with scan-line bisection as the robust fallback where continuation stalls; verifies every traced point. Also the torus zero-circle tracer. Absorbs prototype curve.py's higher-level entry points. | `tests/test_pipeline.py` |
| `src/mobius_rickness/ridge.py` | [NEW, optional-advanced] The Eberly height-ridge / SCMS realization of the Central Finite Curve as an intrinsic 1-D crest of the Rickness field, offered alongside the level-set 'wall'. Documented honestly as the ridge, not the literal argmax. | `tests/test_ridge.py` |
| `src/mobius_rickness/viz/ascii.py` | Always-on, dependency-free visualization: value heatmap and +/-/O sign map that draws the Central Finite Curve directly on the (u,v) domain. Refactor of prototype ascii_heatmap.py render/render_sign_map; golden-string testable. | `tests/test_viz_ascii.py` |
| `src/mobius_rickness/viz/png.py` | Optional matplotlib PNG output (2D K_Rick heatmap, 3D traced curve on the strip). Import-guarded — returns None when matplotlib is absent so the ASCII path is the guaranteed fallback. Refactor of prototype save_png/save_curve_png. | `tests/test_viz_ascii.py` |
| `src/mobius_rickness/_optional.py` | Single point of optional-dependency capability detection so adapters branch on booleans and the core never imports numpy/matplotlib at module top level. | `tests/test_core_purity.py` |
| `src/mobius_rickness/config.py` | Frozen dataclass carrying all knobs (domain bounds, grid sizes n_u/n_v, Rickness weights, seed, tolerances, step sizes) — pure data, no logic — keeping the three independent knobs (grid h, root eps, continuation ds) explicit and immutable. | `tests/test_cli.py` |
| `src/mobius_rickness/rng.py` | Reproducible seeded PRNG wrapper for Monte-Carlo cross-checks (e.g. FD-vs-analytic error over random (u,v)), with deterministic child sub-streams so nested sampling stays reproducible. | `tests/test_cli.py` |
| `src/mobius_rickness/io.py` | Boundary adapter: load/save surface params and traced curves as JSON with schema validation, so external data is validated fail-fast and never trusted. No math. | `tests/test_io.py` |
| `src/mobius_rickness/cli.py` | Thin argparse subcommand adapter: parse -> call exactly one core/trace function -> format. Holds no math and no persistent state; main(argv=None)->int for testability. Absorbs the prototype demo.py narrative as subcommands. | `tests/test_cli.py` |


### Module detail


#### `src/mobius_rickness/core/vectors.py`

Immutable 3D vector primitives shared by every geometry path; each op RETURNS A NEW TUPLE and never mutates (coding-style immutability rule). Extracted from the prototype's geometry.py so vector math lives in one place.


_Public API:_
- `Vec3 (type alias tuple[float,float,float])`
- `sub(a,b)->Vec3`
- `scale(a,s)->Vec3`
- `dot(a,b)->float`
- `cross(a,b)->Vec3`
- `norm(a)->float`

_Key algorithms:_
- Elementary Euclidean vector arithmetic returning fresh tuples

_Depends on:_ `math`


#### `src/mobius_rickness/core/analytic.py`

[NEW — critical] The closed-form ground-truth ORACLE for the Mobius strip. Implements the research's exact scalars so every numerical path can be validated to machine precision and the prototype's missing analytic layer is supplied.


_Public API:_
- `E(u,v)->float`
- `first_form(u,v)->(E,F,G)  # (E,0.0,1.0)`
- `M(u,v)->float  # -1/(2*sqrt(E))`
- `K(u,v)->float  # -1/(4*E**2)`
- `triple_product(u,v)->float  # r_uv.(r_u x r_v) == -0.5`
- `require_embedded(w)->None  # raise if w>=1`

_Key algorithms:_
- E=(1+v cos(u/2))^2 + v^2/4 by direct math.cos
- K=-1/(4 E^2), M=-1/(2 sqrt(E)), F=0, G=1, N=0 (analytic collapse)
- Defensive guard E>0; embedding validation w<1

_Depends on:_ `math`


#### `src/mobius_rickness/core/numeric.py`

Surface-agnostic numeric Gaussian curvature via central finite differences of the first/second fundamental forms; the general-purpose path used to cross-check the oracle and to handle swapped non-analytic surfaces. Refactor of the prototype geometry.py.


_Public API:_
- `partials(surf,a,b,h=1e-4)->dict[str,Vec3]`
- `fundamental_forms(surf,a,b)->(E,F,G,L,M,N)`
- `gaussian_curvature(surf,a,b)->float`
- `optimal_step_first()->float`
- `optimal_step_second()->float`

_Key algorithms:_
- Central stencils: r_u O(h^2), r_uu O(h^2), 4-point mixed r_uv
- n=(r_u x r_v)/sqrt(EG-F^2); L,M,N as dots with n; K=(LN-M^2)/(EG-F^2)
- Step selection: h~(3 eps)^(1/3) first deriv, h~(48 eps)^(1/4)~1e-4 second deriv

_Depends on:_ `math`, `core.vectors`


#### `src/mobius_rickness/core/complexstep.py`

[NEW] Cancellation-free first derivatives via the complex-step trick (cos/sin are entire), giving a rock-solid first fundamental form and normal direction, matched to central differences to 10 digits.


_Public API:_
- `r_u_cs(surf,u,v,h=1e-200)->Vec3`
- `r_v_cs(surf,u,v,h=1e-200)->Vec3`
- `first_form_cs(surf,u,v)->(E,F,G)`

_Key algorithms:_
- r_u = Im(surf(complex(u,h),v))/h componentwise via cmath, h=1e-200
- Analyticity precondition check (documented): fails silently for abs/max/branch cuts

_Depends on:_ `cmath`, `core.vectors`


#### `src/mobius_rickness/core/domain.py`

[NEW] Encodes the non-orientable Mobius domain: the seam gluing r(2pi,v)=r(0,-v), the index/wrap map used by periodic stencils and tracers, one-sided 3-point v-boundary stencils, and fail-fast input validation (u real, |v|<w<1).


_Public API:_
- `wrap(u,v)->(u,v)  # k=floor(u/2pi); v flipped if k odd`
- `one_sided_v(surf,u,v,side,h)->Vec3`
- `validate(u,v,w)->None`
- `U_MIN,U_MAX,V_MIN,V_MAX,HALF_WIDTH`

_Key algorithms:_
- Seam index map: u'=u-2pi*k, v'=v if k even else -v
- Forward/backward 3-point one-sided differences (O(h^2)) within one step of |v|=w
- Boundary validation raising ValueError on |v|>=w or w>=1

_Depends on:_ `math`, `core.vectors`


#### `src/mobius_rickness/core/mobius.py`

The Mobius strip itself: the standard ruled parametrization plus curvature accessors that delegate to the analytic oracle (default) or the numeric path (cross-check). Refactor of prototype mobius.py.


_Public API:_
- `surface(u,v)->Vec3`
- `gaussian_curvature(u,v)->float  # analytic default`
- `gaussian_curvature_fd(u,v)->float  # numeric`
- `fundamental_forms(u,v)->(E,F,G,L,M,N)`
- `U_MIN,U_MAX,V_MIN,V_MAX`

_Key algorithms:_
- r(u,v)=((1+v cos(u/2))cos u,(1+v cos(u/2))sin u,v sin(u/2))
- Delegation to analytic.K and numeric.gaussian_curvature(surface,...)

_Depends on:_ `math`, `core.analytic`, `core.numeric`, `core.vectors`


#### `src/mobius_rickness/core/torus.py`

The torus as the non-ruled counterpoint with sign-changing curvature: exact closed form, numeric cross-check, sign pattern, and the geometry-driven zero circles theta=pi/2,3pi/2. Refactor of prototype torus.py.


_Public API:_
- `surface(theta,phi,R0=2,r0=1)->Vec3`
- `gaussian_curvature_closed(theta,...)->float`
- `gaussian_curvature(theta,phi=0,...)->float`
- `sign_pattern(theta,...)->int`
- `zero_circles()->(pi/2,3pi/2)`
- `require_ring(R0,r0)->None`

_Key algorithms:_
- K(theta)=cos(theta)/(r0(R0+r0 cos theta))
- Ring-torus guard R0>r0 (raise instead of masking singularity)

_Depends on:_ `math`, `core.numeric`, `core.vectors`


#### `src/mobius_rickness/core/rickness.py`

The sign-changing Rickness field R(u,v) whose zero set IS the Central Finite Curve (because K<0 everywhere on the Mobius interior), plus its closed-form per-column root. Refactor of prototype rickness.py; keeps rickness_naive to document why the +1.5 version had no zero.


_Public API:_
- `rickness(u,v)->float  # cos u + 0.4 v cos(u/2) + 0.2 sin u`
- `rickness_naive(u,v)->float`
- `column_coeffs(u)->(A,B)`
- `column_root(u)->Optional[float]  # v*=-A/B if in [-w,w]`
- `k_rick(u,v)->float`

_Key algorithms:_
- Affine-in-v decomposition R=A(u)+B(u)v, A=cos u+0.2 sin u, B=0.4 cos(u/2)
- Exact column root v*=-A/B (removes grid-resolution miss risk)

_Depends on:_ `math`, `core.mobius`


#### `src/mobius_rickness/core/weighted.py`

[NEW] The weighted curvature KR=K*R and the grid evaluation of K,R,KR (absorbs prototype field.py). Encodes the theorem Zero(KR)=Zero(R) on the Mobius strip and Zero(KR) contains K^{-1}(0) on the torus, and the invariant K<0 on the interior.


_Public API:_
- `KR(u,v)->float`
- `evaluate_grid(n_u,n_v)->Grid`
- `assert_mobius_K_negative(...)->float`
- `field_range(grid)->(lo,hi)`

_Key algorithms:_
- KR=K*R; assertion KR==0 exactly where R==0
- Interior sampling excluding v=+/-w to certify strict K<0

_Depends on:_ `core.mobius`, `core.rickness`, `core.numerics`, `core.numerics`


#### `src/mobius_rickness/core/numerics.py`

[NEW] Stdlib numeric utilities used across core and adapters when numpy is absent: accurate summation, approximate-equality helpers, normalization, and linspace (extracted from field.py).


_Public API:_
- `kahan_sum(xs)->float`
- `fsum(xs)->float`
- `isclose_exact(a,b,rel,abs_)->bool`
- `normalize(vals,lo,hi)->list`
- `linspace(a,b,n)->list`

_Key algorithms:_
- Kahan compensated summation (O(1)*u error) with math.fsum wrapper
- math.isclose (PEP 485) helpers with mandatory abs_tol near zero
- Min-max normalization with constant-field guard (vmax==vmin -> midpoint)

_Depends on:_ `math`


#### `src/mobius_rickness/core/zeno.py`

[NEW] The Gojo-Infinity link realized as an EXACT reproduced target: the convergent geometric series with fractions.Fraction, so tests assert equality with == rather than a tolerance.


_Public API:_
- `geometric_sum(a,r)->Fraction  # a/(1-r)`
- `partial_sum(a,r,n)->Fraction  # a(1-r^n)/(1-r)`
- `residual(r,n)->Fraction  # r^n>0`

_Key algorithms:_
- Exact rational arithmetic; closed form a/(1-r); partial 1-r^n
- Domain guard |r|<1 (raise ValueError otherwise)

_Depends on:_ `fractions`


#### `src/mobius_rickness/trace/bisection.py`

1D scan-line root finding: reduce R(u_i,.) to g(v), detect Bolzano sign changes, refine each bracket by bisection to ~1e-9. Reuse of prototype curve.py bisect/find_roots_in_v; also used as the robust fallback and seed source.


_Public API:_
- `bisect(f,lo,hi,tol=1e-9)->float`
- `find_roots_in_v(u,n_samples,tol)->list[float]`
- `scan_columns(field,us,tol)->list[list[float]]`

_Key algorithms:_
- Bolzano bracket g(a)g(b)<0 then interval halving; n=ceil(log2((b-a)/eps))
- Explicit g(node)==0 catch; fail-fast ValueError on non-bracket

_Depends on:_ `math`, `core.rickness`, `core.numerics`


#### `src/mobius_rickness/trace/marching_squares.py`

[NEW] Global contour topology of R=0 over a (u,v) grid: 16-case classification, linear edge crossings, asymptotic saddle disambiguation — discovers every component (including closed loops) the single-direction v-scan misses.


_Public API:_
- `Segment (NamedTuple)`
- `march(field,us,vs)->list[Segment]`

_Key algorithms:_
- 4-bit corner sign case index + static edge table
- Edge crossing t=F_A/(F_A-F_B), P=A+t(B-A)
- Bilinear asymptotic decider alpha=(F00 F11-F10 F01)/(F00+F11-F10-F01) for cases 5/10

_Depends on:_ `core.numerics`


#### `src/mobius_rickness/trace/stitch.py`

[NEW] Convert unordered marching-squares segments into ordered polylines, one per connected component, and emit exactly one seed per component for continuation.


_Public API:_
- `stitch(segments,cell)->list[Polyline]`
- `seeds(components)->list[tuple[float,float]]`

_Key algorithms:_
- Grid-hash snap (~h/4) building endpoint->segment adjacency
- Walk from degree-1 vertex (arc) or unused vertex (loop) following unique unused incident segment
- Consistent saddle pairing at degree-4 vertices

_Depends on:_ `trace.marching_squares`


#### `src/mobius_rickness/trace/continuation.py`

[NEW] Predictor-corrector pseudo-arclength tracer producing an ordered, uniformly arc-length-sampled, high-accuracy polyline; seam-aware and adaptive; the rigorous 'real curve' path.


_Public API:_
- `grad(R,u,v,dh=1e-6)->(Ru,Rv)`
- `newton_correct(R,u,v,tol=1e-12)->(u,v,ok)`
- `trace_component(R,u0,v0,ds=0.02,wrap=domain.wrap)->list[tuple]`

_Key algorithms:_
- Tangent T=(R_v,-R_u)/||grad R||; Euler predictor x+ds*T
- Minimal-norm Newton corrector x -= R*grad R/||grad R||^2
- Seam wrap + v-flip each step; heading preservation with post-seam special case; adaptive ds; closed-loop termination ||x-x0||<ds
- Singular-point guard ||grad R||~0 -> stop/branch

_Depends on:_ `math`, `core.domain`, `core.numerics`


#### `src/mobius_rickness/trace/lift.py`

[NEW] Lift traced parameter-space points to the physical 3D strip and measure lifted arc length. Isolated so tracing stays surface-agnostic.


_Public API:_
- `lift(points)->list[CurvePoint]`
- `arc_length(curve_points)->float`

_Key algorithms:_
- r(u,v) evaluation via mobius.surface
- Discrete polyline length sum ||r_{k+1}-r_k|| (Kahan-summed)

_Depends on:_ `core.mobius`, `core.numerics`


#### `src/mobius_rickness/trace/pipeline.py`

[NEW] Hybrid orchestration = coverage + accuracy: marching-squares for seeds/topology -> stitch -> Newton-polish + continuation, with scan-line bisection as the robust fallback where continuation stalls; verifies every traced point. Also the torus zero-circle tracer. Absorbs prototype curve.py's higher-level entry points.


_Public API:_
- `trace_mobius_curve(config)->TracedCurve`
- `trace_torus_zero_circles(n_theta,tol)->list[float]`
- `verify_curve(points,r_tol,k_rick_tol)->None`

_Key algorithms:_
- Seed dedupe per component; continuation with bisection fallback
- Torus closed-form K sign-change scan + bisection
- Residual assertions |R|<1e-6 and |K_Rick|<1e-6

_Depends on:_ `trace.bisection`, `trace.marching_squares`, `trace.stitch`, `trace.continuation`, `trace.lift`, `core.rickness`, `core.torus`


#### `src/mobius_rickness/ridge.py`

[NEW, optional-advanced] The Eberly height-ridge / SCMS realization of the Central Finite Curve as an intrinsic 1-D crest of the Rickness field, offered alongside the level-set 'wall'. Documented honestly as the ridge, not the literal argmax.


_Public API:_
- `hessian(R,u,v,h)->list[list[float]]`
- `jacobi_eigsym(A)->(vals,vecs)`
- `scms_step(R,x)->tuple`
- `trace_ridge(R,seed)->list[tuple]`

_Key algorithms:_
- Central-difference gradient+Hessian on a lightly smoothed field
- Jacobi rotation symmetric 2x2/3x3 eigensolver (pure stdlib)
- SCMS update x += V V^T m(x) projecting onto transverse subspace

_Depends on:_ `math`, `core.numerics`


#### `src/mobius_rickness/viz/ascii.py`

Always-on, dependency-free visualization: value heatmap and +/-/O sign map that draws the Central Finite Curve directly on the (u,v) domain. Refactor of prototype ascii_heatmap.py render/render_sign_map; golden-string testable.


_Public API:_
- `render(values,us,vs,width=None)->str`
- `render_sign_map(field,us,vs,width=None)->str`

_Key algorithms:_
- Ramp indexing with min-max normalization and constant-field guard
- Neighbor sign-change detection for the zero-curve overlay
- Column downsampling for terminal width

_Depends on:_ `core.numerics`


#### `src/mobius_rickness/viz/png.py`

Optional matplotlib PNG output (2D K_Rick heatmap, 3D traced curve on the strip). Import-guarded — returns None when matplotlib is absent so the ASCII path is the guaranteed fallback. Refactor of prototype save_png/save_curve_png.


_Public API:_
- `save_heatmap(values,us,vs,path)->Optional[str]`
- `save_curve_png(curve_points,path)->Optional[str]`

_Key algorithms:_
- Agg backend selected before pyplot import
- imshow heatmap; 3D surface + scatter of traced curve

_Depends on:_ `_optional`, `core.mobius`


#### `src/mobius_rickness/_optional.py`

Single point of optional-dependency capability detection so adapters branch on booleans and the core never imports numpy/matplotlib at module top level.


_Public API:_
- `HAS_NUMPY:bool`
- `HAS_MPL:bool`
- `get_numpy()->module|None`

_Key algorithms:_
- try/except ImportError guards; matplotlib.use('Agg') before pyplot


#### `src/mobius_rickness/config.py`

Frozen dataclass carrying all knobs (domain bounds, grid sizes n_u/n_v, Rickness weights, seed, tolerances, step sizes) — pure data, no logic — keeping the three independent knobs (grid h, root eps, continuation ds) explicit and immutable.


_Public API:_
- `Config (frozen dataclass)`
- `DEFAULT: Config`

_Key algorithms:_
- Immutable configuration object; with_-style copy via dataclasses.replace

_Depends on:_ `dataclasses`


#### `src/mobius_rickness/rng.py`

Reproducible seeded PRNG wrapper for Monte-Carlo cross-checks (e.g. FD-vs-analytic error over random (u,v)), with deterministic child sub-streams so nested sampling stays reproducible.


_Public API:_
- `Prng(seed) `
- `Prng.uniform(a,b)`
- `Prng.spawn(tag)->Prng`
- `Prng.sample_domain(n)->list[tuple]`

_Key algorithms:_
- random.Random(MT19937) injection (never module-level random.*)
- Deterministic child seed = parent.randint XOR/hash(tag); sorted iteration to defeat PYTHONHASHSEED

_Depends on:_ `random`


#### `src/mobius_rickness/io.py`

Boundary adapter: load/save surface params and traced curves as JSON with schema validation, so external data is validated fail-fast and never trusted. No math.


_Public API:_
- `load_config(path)->Config`
- `save_curve(points,path)->None`
- `load_curve(path)->list[CurvePoint]`

_Key algorithms:_
- JSON (de)serialization; explicit field/type/range validation raising ValueError

_Depends on:_ `json`, `config`, `trace.lift`


#### `src/mobius_rickness/cli.py`

Thin argparse subcommand adapter: parse -> call exactly one core/trace function -> format. Holds no math and no persistent state; main(argv=None)->int for testability. Absorbs the prototype demo.py narrative as subcommands.


_Public API:_
- `build_parser()->ArgumentParser`
- `main(argv=None)->int`

_Key algorithms:_
- add_subparsers + set_defaults(func) dispatch; exit codes 0 ok / 2 usage / 1 domain error
- Catch core ValueError at boundary, print one-line message

_Depends on:_ `argparse`, `core.mobius`, `core.torus`, `core.weighted`, `core.zeno`, `trace.pipeline`, `viz.ascii`, `viz.png`, `config`


## Data flow

1) Config (immutable) supplies domain bounds, grid sizes, weights, seed, and the three independent tolerances (grid h, root eps, continuation ds). 2) core/mobius.surface and core/torus.surface define the geometry. 3) Curvature is produced by THREE independent core paths that converge: analytic.K (exact oracle) <- numeric.gaussian_curvature (central-difference FD, cross-check) <- complexstep.first_form_cs (cancellation-free first form). 4) core/rickness computes the sign-changing field R(u,v)=A(u)+B(u)v and its exact column root; core/weighted forms KR=K*R and evaluates the K/R/KR grid, asserting K<0 on the interior so Zero(KR)=Zero(R). 5) The trace/ pipeline turns R into an explicit curve: marching_squares.march finds topology+seeds over the grid -> stitch orders them into components -> continuation.trace_component (seam-aware via domain.wrap, Newton-corrected) produces a uniform high-accuracy polyline, with bisection.find_roots_in_v as the robust fallback and redundant seed source -> lift.lift maps each (u,v) to 3D and arc_length measures it; pipeline.verify_curve asserts |R|<1e-6 and |K_Rick|<1e-6 at every point. 6) Adapters consume core/trace outputs only: viz/ascii renders the always-on heatmap and sign-map; viz/png emits optional matplotlib images; io persists JSON; zeno provides the exact geometric-series target; cli wires argv to exactly one core/trace call. Dependency direction is strictly core -> (nothing external); adapters (rng, io, viz, cli) -> core; core never imports numpy/matplotlib or any adapter.


## Testing strategy

pytest (v9 available) with tests/ mirroring the package; TDD RED->GREEN->REFACTOR; 80%+ coverage via pytest-cov (pure core modules approach 100%). Enable executable formula docstrings with addopts=\"--doctest-modules\". A dedicated tests/test_reproduction.py pins every numeric target from the research in one place: analytic F==0 and G==1 to ~1e-12, N==0 to ~1e-9, M==-1/(2 sqrt E), triple product r_uv.(r_u x r_v)==-1/2, K(u,0)==-0.25 (analytic ==, numeric isclose to 4 places), min|K| on the strip at |v|=0.5 ~ -0.0467; FD-vs-analytic property test |K_fd-K_analytic|<1e-6 (~6e-8) over seeded random (u,v) with pinned seed AND sample count; a monotone/U-shaped error-vs-h curve test showing the truncation/round-off trade-off; complex-step matches central diff to 10 digits; seam identity r(2pi,v)==r(0,-v) and domain.wrap flips v across the seam (removing the u=0 discontinuity); torus numeric vs closed form <1e-5 with zeros exactly at pi/2,3pi/2 and correct +/-/0 sign pattern; rickness column root v*=-A/B agrees with bisection; weighted KR==0 iff R==0; kahan_sum==math.fsum on [1e16,1,-1e16]; zeno.geometric_sum(1/2,1/2)==1 EXACTLY via Fraction ==; every continuation point |R|<1e-8, closed-loop returns within ds, marching-squares and scan-line agree on component count; bisect raises ValueError on a non-bracket; a purity test asserting `import mobius_rickness.core` leaves 'numpy' out of sys.modules. Optional Hypothesis property tests for invariants (K<0 on the whole Mobius grid). viz/ascii tested by exact golden-string comparison; cli by calling main([...]) with an argv list and capturing stdout/exit code.


## Visualization strategy

Two-tier, always-degradable. Default (stdlib, guaranteed): viz/ascii.render draws a character-ramp heatmap of any scalar field (K, R, K_Rick) with min-max normalization and a constant-field guard, and viz/ascii.render_sign_map draws the +/- universes with an 'O' overlay marking the sign-change locus — i.e. the Central Finite Curve directly on the (u,v) domain — plus a legend and u/v axes; both are pure strings, so they are golden-string testable and terminal-friendly via column downsampling and a ~2:1 aspect correction. Optional enhancement (import-guarded): viz/png.save_heatmap renders a matplotlib magma heatmap and save_curve_png plots the traced curve as red scatter on a translucent 3D Mobius surface; both select the Agg backend before importing pyplot and return None (never raise) when matplotlib is absent. The CLI 'render' subcommand always prints ASCII and additionally writes PNGs only when HAS_MPL. Numeric fields feeding both renderers come exclusively from the pure core, so visualization is a leaf adapter with no feedback into the math.


## CLI design

Single ArgumentParser with add_subparsers(); each handler parses its own args, calls exactly one pure-core/trace function, formats, and returns an int exit code (0 ok, 2 usage per argparse default, 1 domain error). main(argv=None) accepts an argv list for testability. Subcommands: `curvature --u --v [--method analytic|fd|cs]` prints K (and optionally E,F,G,L,M,N); `forms --u --v` prints the fundamental-form table with the analytic collapse (F=0,G=1,N=0,M=-1/(2 sqrt E)); `trace [--surface mobius|torus] [--method hybrid|scan] [--n-u --n-v --ds]` traces the Central Finite Curve, prints sampled (u,v,x,y,z,|R|) points and verification status; `render [--field k|r|krick] [--width] [--png PATH]` prints the ASCII heatmap/sign-map and optionally writes a PNG when matplotlib is present; `series --a --r --n` prints the exact geometric partial sum and residual (Gojo-Infinity Fraction target); `torus [--R0 --r0]` prints the sign pattern and the K=0 circles; `verify` runs the full invariant battery (K<0, seam identity, reproduced constants) and exits nonzero on failure. Core ValueErrors (e.g. |v|>=w, |r|>=1) are caught at the boundary and printed as a clean one-line message, never a traceback.


## Dependencies

- **Required:** Python >=3.11 (stdlib only: math, cmath, fractions, random, argparse, json, dataclasses, typing) — no third-party runtime dependency; verified on Python 3.14 with neither numpy nor matplotlib installed
- **Optional:** numpy (compact array storage / accelerated grid eval — behind HAS_NUMPY, pure-Python + Kahan/fsum fallback), matplotlib (PNG heatmap and 3D curve — behind HAS_MPL with Agg backend, ASCII fallback always present), pytest, pytest-cov, hypothesis (dev/test only)


## Risks

- Prototype is FLAT with bare imports (import geometry, from mobius import ...); converting to src-layout + package-relative imports touches every module and every test import line — mechanical but broad; mitigate with a single refactor pass plus test_core_purity to lock the new boundary.
- Finite-difference step coupling: the prototype uses _H=1e-5 for both first and second derivatives; the research shows the second-derivative optimum is ~1e-4. Splitting into two steps changes numeric K values slightly, so FD tests must use tol ~1e-5..1e-6, not 1e-12, or they go flaky.
- Mobius seam v-flip is load-bearing and easy to omit: forgetting v->-v across u=0/2pi produces a spurious high-curvature seam and a C0-discontinuous traced curve. Covered by test_domain seam identity but must be applied in BOTH continuation and any periodic stencil.
- Complex-step silently corrupts if the surface ever gains abs/max/branch cuts (e.g. a swapped non-analytic surface); the path must document and, where cheap, assert analyticity, and never be the sole derivative source for L,M,N.
- Marching-squares saddle ambiguity (cases 5/10) and sub-cell features: inconsistent decider or too-coarse grid yields spurious/merged components; mitigate with the asymptotic decider and by cross-checking component count against scan-line bisection.
- Continuation branch-jump / singular-point stall where ||grad R||->0: adaptive ds, turning-angle cap, and Newton guard are required; without them closed-loop termination can hang or mis-close — bounded by max_steps and the singular-point guard.
- Ridge module (Eberly/SCMS) is the most numerically delicate (Hessian noise, eigenvector sign flips at umbilic points); keep it optional-advanced and clearly labeled as the ridge/crest, NOT the literal argmax, to avoid overclaiming.
- Non-ring torus (R0<=r0) makes K genuinely singular; the prototype's denom==0 -> 0.0 guard masks this. The target must raise for R0<=r0 instead of silently returning 0.
- Fraction denominator blow-up in zeno.partial_sum for large n; cap n or fall back to float past a threshold to avoid quadratic memory.


## No-mock guarantee

Every module carries a real algorithm and is exercised by real assertions — nothing is a stub. core/vectors: elementary but real, returns fresh immutable tuples. core/analytic: the exact closed-form oracle (E, K=-1/(4E^2), M, triple product) validated to machine precision — the opposite of a mock, it is the ground truth. core/numeric: genuine central-difference fundamental forms reconstructing K, cross-checked <1e-6 against the oracle. core/complexstep: real cmath complex-step derivatives matched to 10 digits. core/domain: the actual seam index map and one-sided stencils, proven by the r(2pi,v)=r(0,-v) test. core/mobius & core/torus: full parametrizations with delegated curvature. core/rickness: the real sign-changing field with an exact column root. core/weighted: real KR product and grid with the K<0 invariant. core/numerics: working Kahan summation matched to math.fsum. core/zeno: exact Fraction geometric series (geometric_sum(1/2,1/2)==1). trace/bisection: real IVT bracketing + halving to 1e-9. trace/marching_squares: real 16-case contouring with asymptotic saddle decider. trace/stitch: real endpoint-hash adjacency walk. trace/continuation: real predictor-corrector with Newton corrector and seam handling. trace/lift: real 3D lift and arc length. trace/pipeline: real hybrid orchestration with residual verification. ridge: real Jacobi eigensolver + SCMS. viz/ascii: real normalized renderer (golden-string tested); viz/png: real matplotlib output guarded by capability flags. config/rng/io/_optional/cli: real adapters (frozen config, injected MT19937, JSON validation, argparse dispatch) with no placeholder branches — the only 'fallbacks' are genuine stdlib implementations that produce the same numbers as the optional accelerated path.

