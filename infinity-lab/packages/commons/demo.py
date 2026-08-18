"""Runnable demo of the commons public API (stdlib only, offline).

Run from the repo root::

    python packages/commons/demo.py

It exercises the exact arithmetic, numerics, RNG, and text renderers so the
shared building blocks can be eyeballed end to end without any install.
"""

from __future__ import annotations

import cmath
import math
import os
import sys

# Make `import commons` work when run directly (mirrors the pytest pythonpath).
_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "src")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

from fractions import Fraction  # noqa: E402

import commons  # noqa: E402


def main() -> None:
    print("=== commons demo (stdlib only) ===\n")

    # 1. Exact Zeno partial sums -> render convergence toward 1.
    partials = [
        float(commons.geometric_partial_sum(Fraction(1, 2), Fraction(1, 2), n))
        for n in range(1, 11)
    ]
    print(commons.render_convergence(partials, target=1.0, height=10,
                                     title="Zeno partial sums S_n -> 1"))
    print(f"\nExact limit a/(1-r) = "
          f"{commons.geometric_series_limit(Fraction(1, 2), Fraction(1, 2))}")
    print(f"half_power(1075) numerator = {commons.half_power(1075).numerator} "
          f"(strictly positive)\n")

    # 2. Integration: integral_0^1 x^2 dx = 1/3.
    for name, fn in (
        ("midpoint", commons.midpoint_integral),
        ("trapezoid", commons.trapezoid_integral),
    ):
        val = fn(lambda x: x * x, 0.0, 1.0, 4000)
        print(f"{name:>10} integral_0^1 x^2 dx = {val:.10f} (exact 1/3)")
    adap = commons.adaptive_integral(lambda x: x * x, 0.0, 1.0, 1e-12)
    print(f"{'adaptive':>10} integral_0^1 x^2 dx = {adap:.10f} (exact 1/3)\n")

    # 3. Derivatives of sin at x=0.7 (cos(0.7) analytic).
    x = 0.7
    cd = commons.central_difference(math.sin, x, 1e-6, 1)
    cs = commons.complex_step_derivative(cmath.sin, x, 1e-20)
    print(f"d/dx sin(0.7): central-diff={cd:.12f}  complex-step={cs:.12f}  "
          f"cos(0.7)={math.cos(x):.12f}\n")

    # 4. Root finding: sqrt(2).
    root = commons.bisection(lambda t: t * t - 2.0, 0.0, 2.0, 1e-12)
    print(f"bisection root of x^2-2 = {root:.12f} (sqrt2={math.sqrt(2.0):.12f})\n")

    # 5. Heatmap of f(x, y) = sin(x) * cos(y).
    xs = [i * (2 * math.pi) / 23 for i in range(24)]
    ys = [(-1.0 + i * (2.0 / 8)) for i in range(9)]
    grid = [[math.sin(xx) * math.cos(yy) for xx in xs] for yy in ys]
    print(commons.render_heatmap(grid, row_labels=ys, width=24,
                                 title="f(x,y)=sin(x)cos(y)"))
    print()

    # 6. Sign map + traced zero curve of f(x, y) = y - sin(x).
    print(commons.render_sign_map(lambda xx, yy: yy - math.sin(xx), xs, ys,
                                  width=24, title="zero curve of y - sin(x)"))

    # 7. Deterministic RNG sample.
    rng = commons.make_rng(2026)
    print(f"\nDeterministic sample(seed=2026) = "
          f"{rng.sample(list(range(10)), 4)}")


if __name__ == "__main__":
    main()
