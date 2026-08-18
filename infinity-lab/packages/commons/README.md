# commons — the shared, standard-library-only foundation

> *One small, dependency-free toolkit every project in the monorepo stands on:
> exact arithmetic, real numerics, a deterministic RNG, immutable config, optional-
> dependency guarding, and ASCII renderers.*

`commons` is the internal shared package for the [`infinity-lab`](../../README.md)
monorepo. Every other package (`calabi_yau_latent`, `domain_expansion`,
`divergence_meter`, `padic_embeddings`, `madoka_entropy`, and the rest) depends on
it. Its `core/` is **pure Python standard library** — no numpy, no matplotlib, no
network — so the mathematics of every downstream package remains trivially testable,
portable, and offline. There is **no banner, no artifact figure, no CLI, and no
`accel/` layer** here; `commons` is a library, not a demo.

---

## TL;DR

- **`core/exact.py`** — exact rational arithmetic over `fractions.Fraction`:
  `to_fraction`, `half_power(n) = 1/2ⁿ`, exact geometric partial sums and limits.
- **`core/numerics.py`** — real numerical routines: composite midpoint / trapezoid /
  adaptive-Simpson integration, central-difference and complex-step differentiation,
  bracketed bisection, and sign-change scanning.
- **`core/rng.py`** — `DeterministicRNG`, a seeded wrapper over `random.Random`
  (Mersenne Twister) that **never touches the global `random` state** and returns new
  lists (no input mutation).
- **`core/config.py`** — `FrozenConfig`, an immutable dataclass base with
  copy-on-change `with_changes(...)` and `to_dict()`.
- **`core/optional.py`** — `try_import(name)` returns the module or `None` (never
  raises for a missing dep), plus `has_numpy()` / `has_matplotlib()`.
- **`adapters/ascii_art.py`** — deterministic, dependency-free text renderers:
  line plots, convergence plots, heatmaps, and sign maps.
- Enforced core purity: `core` imports only stdlib (+ other `core`), never adapters
  or scientific deps.

---

## The idea

The monorepo's hard invariant is that the **core of every package is standard-library
only**; numpy and matplotlib are optional, import-guarded, and never required to run,
test, or demo anything. `commons` makes that invariant practical by concentrating the
genuinely shared, foundational primitives in one place: exact and floating-point
numerics that downstream cores need, a reproducible RNG, an immutable config base, a
one-function optional-dependency guard, and a small set of ASCII renderers so every
package can visualise results without a plotting dependency.

Everything is small, pure, and heavily unit-tested, so a downstream package can build
its own honest mathematics on top without ever reaching for a third-party library.

---

## The mathematics

`commons` is where the reproducible numeric targets that downstream READMEs cite
actually come from. All results below are pinned by the test suite.

### Exact rational arithmetic (`core/exact.py`)

Everything runs in `fractions.Fraction`, so there is **no floating-point rounding**.

- `to_fraction(x)` — converts `int`, `Fraction`, decimal `str` (e.g. `"0.1" → 1/10`
  exactly), or `float` (to its exact IEEE-754 value) to a `Fraction`; rejects `bool`.
- `half_power(n) = Fraction(1, 1 << n)` — exact dyadic `1/2ⁿ` for `n ≥ 0`, via an
  integer bit-shift, so it stays exact for huge `n` (e.g. `half_power(1075)` has
  numerator `1` and denominator `2¹⁰⁷⁵`). This is the primitive behind
  `divergence_meter`'s `exact_value = Fraction(word, 2⁶³)`.
- `geometric_partial_sum(a, r, n) = Σ_{k=0}^{n−1} a·rᵏ` — closed form
  `a·(1 − rⁿ)/(1 − r)` (or `a·n` when `r = 1`). Test target:
  `geometric_partial_sum(1/2, 1/2, 4) == Fraction(15, 16)` (the Zeno sum
  `½ + ¼ + ⅛ + 1⁄16`).
- `geometric_series_limit(a, r) = a/(1 − r)` for `|r| < 1`; raises on divergence.
  Test target: `geometric_series_limit(1/2, 1/2) == Fraction(1)`.

### Real numerics (`core/numerics.py`)

Pure `math`/`cmath`, using `math.fsum` for stable accumulation.

| Routine | Method | Pinned accuracy |
|---|---|---|
| `midpoint_integral`, `trapezoid_integral` | composite rules, `O(1/n²)` | `∫₀¹ x² ≈ 1/3` to `< 1e-6` (`n=2000`) |
| `adaptive_integral` | adaptive Simpson, Richardson error `\|δ\|/15 ≤ tol` | `∫₀¹ x² → 1/3` and `∫₀^π sin → 2` to `< 1e-10` |
| `central_difference` (order 1/2) | `(f(x+h) − f(x−h))/2h`, `(f(x+h) − 2f(x) + f(x−h))/h²` | `f'` to `< 1e-7`, `f''` to `< 1e-6` |
| `complex_step_derivative` | `Im(f(x + i·h))/h`, no subtractive cancellation | derivative to `< 1e-12` (`h = 1e-20`) |
| `bisection` | bracketed bisection | root of `x²−2 → √2` to `< 1e-10` |
| `find_sign_changes` | scan `n` sub-intervals for sign flips | `sin` on `[−0.5, 7]` finds `≥ 3` roots, each `\|sin(r)\| < 1e-9` |

### Deterministic RNG (`core/rng.py`)

`DeterministicRNG(seed)` wraps a private `random.Random(seed)` (CPython's Mersenne
Twister — a stable, platform-independent algorithm for a given seed and call
pattern), so the same seed reproduces the same stream across machines. It **never
reads or writes the global `random` module**, so concurrent components cannot perturb
each other. Methods: `random()`, `uniform(low, high)`, `randint(low, high)`,
`choice(seq)`, `sample(seq, k)` and `shuffled(seq)` (both return **new** lists,
inputs untouched), and `reset()` (returns a fresh generator that replays from the
start). `bool` seeds are rejected. `make_rng(seed)` is the convenience constructor.

### Immutable config (`core/config.py`)

`FrozenConfig` is a `@dataclass(frozen=True)` base. Assignment raises
`FrozenInstanceError`; updates go through `with_changes(**changes)` (a thin wrapper
over `dataclasses.replace` that returns a **new** instance and rejects unknown
fields) and `to_dict()`. The free function `immutable_replace(instance, **changes)`
does the same for any frozen dataclass. Frozen dataclasses also get value-equality
and hashing for free.

### Optional-dependency guarding (`core/optional.py`)

`try_import(name)` calls `importlib.import_module(name)` lazily and returns the module
or `None` — it catches **any** import-time exception and maps it to `None`, so a
missing or broken optional dependency never breaks a pure-core import. (Non-string
names raise `TypeError`; empty strings raise `ValueError`.) `has_numpy()` and
`has_matplotlib()` are boolean probes over it. This is how downstream `accel/` and
`viz.py` layers reach numpy/matplotlib **only at call time**, keeping the core pure.

---

## How it works

### Module map

```
src/commons/
  core/               PURE: standard library only (+ other core modules)
    exact.py            to_fraction, half_power, geometric_partial_sum / _limit
    numerics.py         midpoint/trapezoid/adaptive integrals, central_difference,
                        complex_step_derivative, bisection, find_sign_changes
    rng.py              DeterministicRNG, make_rng  (wraps random.Random)
    config.py           FrozenConfig, immutable_replace
    optional.py         try_import, has_numpy, has_matplotlib
  adapters/           presentation (import core; core never imports them)
    ascii_art.py        render_line_plot, render_convergence, render_heatmap,
                        render_sign_map
  demo.py             stdlib-only showcase of every core + adapter feature
```

### ASCII renderers (`adapters/ascii_art.py`)

All four return byte-for-byte deterministic `str`, no file I/O, stdlib only:

- `render_line_plot(ys, *, height=12, title=...)` — a 1-D series as a `height`-row
  ASCII chart, each sample marked `*`.
- `render_convergence(ys, target, ...)` — a line plot plus a legend showing the
  target and the final `|error|`.
- `render_heatmap(values, *, row_labels=None, width=None, title=...)` — a row-major
  2-D field (row 0 at the bottom), a 10-level shade ramp `" .:-=+*#%@"`, and a scale
  legend. This backs the ASCII heatmaps in `domain_expansion` and `padic_embeddings`.
- `render_sign_map(field, xs, ys, ...)` — `+`/`−` for field sign and `O` for zeros or
  cells adjacent to a sign change, tracing a zero curve.

### The core-purity rule

`core/*` imports only the standard library and other core modules — never an adapter,
never numpy/matplotlib. Enforced by `tests/test_core_purity.py`, which statically
scans every `core/*.py` and flags any line starting with `import commons.adapters`,
`from commons.adapters`, `import numpy`, or `import matplotlib`. (Downstream packages
extend this rule to their own `core/` via their `test_*_core_purity.py`.)

---

## Install & run

No install and no network are required. `commons` is wired onto the pytest
`pythonpath` by the repo's `pyproject.toml`, and its `demo.py` puts its own `src/` on
`sys.path`, so it runs with no `PYTHONPATH` needed:

```bash
# The stdlib-only showcase (exact sums, integration, derivatives, RNG, ASCII art)
python3 packages/commons/demo.py

# Tests (all pure stdlib — nothing to install, nothing skips)
python3 -m pytest packages/commons -q
```

Using it from another package:

```python
from commons.core.rng import make_rng
from commons.core.exact import to_fraction, half_power
from commons.core.config import FrozenConfig
from commons.core.optional import try_import
from commons.adapters.ascii_art import render_convergence

rng = make_rng(2026)
print(rng.sample(list(range(10)), 4))          # reproducible, global RNG untouched
print(half_power(63))                          # Fraction(1, 9223372036854775808)
print(render_convergence([0.5, 0.75, 0.875, 0.9375], target=1.0, height=6))
```

`demo.py` prints seven sections: exact Zeno partial sums driven into
`render_convergence` (with the exact limit `= 1`), `∫₀¹ x²` via all three integrators
(exact `1/3`), `sin` derivatives via central-difference and complex-step vs
`cos(0.7)`, a `√2` root via bisection, a `sin(x)cos(y)` heatmap, a `y − sin(x)` sign
map with a traced zero curve, and a deterministic `make_rng(2026).sample(...)` draw.

---

## Testing

Every core module and the ASCII adapters are unit-tested; the suite is pure stdlib,
so **nothing skips**. It pins, among others:

- **exact** — `half_power(0/1/10) = 1, 1/2, 1/1024`; `half_power(1075)` has
  denominator `1 << 1075`; `to_fraction("0.1") = 1/10`, `to_fraction(0.5) = 1/2`;
  `geometric_partial_sum(1/2, 1/2, 4) = 15/16`;
  `geometric_series_limit(1/2, 1/2) = 1`; divergent/negative inputs raise.
- **numerics** — the integration/differentiation/root-finding accuracies in the
  table above; bad bounds, orders, tolerances, and un-bracketed roots raise.
- **rng** — same seed → identical sequences; different seeds differ; `uniform`/
  `randint` bounds; `sample`/`shuffled` are permutations that leave the input
  unchanged; `reset()` replays; empty `choice` raises; `bool` seed rejected.
- **config** — frozen (mutation raises `FrozenInstanceError`); `with_changes` returns
  a new object and rejects unknown fields; `to_dict`; value-equality and hashing;
  `immutable_replace` on any frozen dataclass, rejecting non-dataclasses.
- **optional** — `try_import("math")` works; `try_import` of a missing module is
  `None`; non-string/empty names raise; `has_numpy`/`has_matplotlib` are booleans.
- **ascii_art** — deterministic output; correct legends (`target=+1.000000`,
  `scale:`); ragged/empty grids and mismatched labels raise; the sign map contains
  `+`, `−`, `O`, and a `zero curve` label.
- **core purity** — `tests/test_core_purity.py` statically forbids adapter and
  numpy/matplotlib imports in `core/`.

---

## Limitations & honest caveats

- `DeterministicRNG` reproducibility rests on CPython's Mersenne Twister being stable
  for a given seed and identical call pattern; it is not a cryptographic RNG.
- `to_fraction` gives exact decimals **only** for `str` input; a `float` argument is
  converted to its exact IEEE-754 machine value (so `to_fraction(0.1)` is the true
  binary value, not `1/10`). Use decimal strings when you want exact decimals.
- The core-purity test is a lightweight line-prefix scan, not an AST parse: it catches
  top-level `import numpy` / `import matplotlib` / adapter imports, which is exactly
  the invariant it guards, but it does not analyse imports hidden inside functions.
- `numerics` is a compact, general-purpose toolkit (integration, differentiation,
  root finding) — not a full numerical-analysis library; it deliberately has no
  linear-algebra, statistics, or vector helpers.

---

## References

- Python standard library: `fractions.Fraction`, `random.Random` (Mersenne Twister),
  `dataclasses`, `importlib`.
- M. Matsumoto & T. Nishimura, *Mersenne Twister: a 623-dimensionally
  equidistributed uniform pseudorandom number generator*, ACM TOMACS 8 (1998).
- Adaptive Simpson quadrature and Richardson extrapolation: any standard numerical-
  analysis text (e.g. Burden & Faires, *Numerical Analysis*).
- W. Squire & G. Trapp, *Using complex variables to estimate derivatives of real
  functions*, SIAM Review 40 (1998) — the complex-step derivative.
- Monorepo overview and the core-purity rule: [`infinity-lab/README.md`](../../README.md).
