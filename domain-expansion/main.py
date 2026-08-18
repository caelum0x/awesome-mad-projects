"""Demo: Domain Expansion as a coupled constraint solver.

Run:  python3 main.py
"""

from __future__ import annotations

import linalg
from clash import clash
from domain import Domain, direct_solve_domain, max_grid_diff, solve_domain


def hline(char: str = "-", n: int = 64) -> None:
    print(char * n)


def render_field(u: list, title: str) -> None:
    print(title)
    for j in range(len(u[0]) - 1, -1, -1):  # print top row first
        row = "  ".join(f"{u[i][j]:5.1f}" for i in range(len(u)))
        print("  " + row)


def make_refined_domain() -> Domain:
    """A clean, strongly-coupled Laplace domain: hot left edge, cold right."""
    nx = ny = 7

    def g(i: int, j: int) -> float:
        if i == 0:
            return 100.0   # left wall hot  (the guaranteed 'sure-hit' condition)
        if i == nx - 1:
            return 0.0     # right wall cold
        return 20.0        # top/bottom moderate

    return Domain(name="Refined Domain", nx=nx, ny=ny, boundary=g,
                  coupling=1.0, noise=0.0)


def make_crude_domain() -> Domain:
    """A leaky, weakly-coupled, noisy domain: unstable constraints."""
    nx = ny = 7

    def g(i: int, j: int) -> float:
        if i == 0:
            return 60.0
        if i == nx - 1:
            return 40.0
        return 50.0

    return Domain(name="Crude Domain", nx=nx, ny=ny, boundary=g,
                  coupling=0.45, noise=8.0)


def make_void_domain() -> Domain:
    """Unlimited Void flavor: an interior cell pinned with enormous weight."""
    nx = ny = 7

    def g(i: int, j: int) -> float:
        return 10.0 if i in (0, nx - 1) else 30.0

    void = {(3, 3): 999.0}  # infinite information density at the center
    return Domain(name="Unlimited Void", nx=nx, ny=ny, boundary=g,
                  coupling=1.0, noise=0.0, void_cells=void, void_weight=1e6)


def report(name: str, res) -> None:
    print(f"[{name}]")
    print(f"  converged        : {res.converged} in {res.iterations} iters")
    print(f"  residual  (L2)   : {res.residual_l2:.6e}")
    print(f"  residual  (Linf) : {res.residual_inf:.6e}")
    print(f"  rigidity  proxy  : {res.rigidity:.6f}")
    print(f"  refinement score : {res.refinement:.6f}")


def main() -> None:
    hline("=")
    print("DOMAIN EXPANSION :: coupled constraint solver")
    print("numpy backend:", "yes" if linalg.HAVE_NUMPY else "no (pure-python fallback)")
    hline("=")

    # 1) Solve a single refined domain.
    refined = make_refined_domain()
    r_refined = solve_domain(refined)
    render_field(r_refined.field, "\nRefined Domain field (Laplace steady state):")
    print()
    report(refined.name, r_refined)

    # Cross-check relaxation against a direct (Gaussian) solve.
    u_direct = direct_solve_domain(refined)
    print(f"  direct-solve check: max|relax - direct| = "
          f"{max_grid_diff(r_refined.field, u_direct):.3e}")

    # 2) Solve a crude domain for comparison.
    crude = make_crude_domain()
    r_crude = solve_domain(crude)
    print()
    report(crude.name, r_crude)

    # 3) Clash: crude vs refined.
    hline()
    print("CLASH: Crude Domain  vs  Refined Domain")
    hline()
    result = clash(crude, refined)
    print(f"WINNER : {result.winner}")
    print(f"LOSER  : {result.loser}")
    print("WHY    :", result.reason)
    render_field(result.merged_field,
                 f"\nContested region overwritten by {result.winner}:")

    # 4) Unlimited Void dominates on raw rigidity.
    hline()
    print("UNLIMITED VOID: infinite-information-density constraint")
    hline()
    void = make_void_domain()
    r_void = solve_domain(void)
    report(void.name, r_void)
    void_clash = clash(crude, void)
    print()
    print(f"Void vs Crude winner: {void_clash.winner}")
    print("WHY :", void_clash.reason)

    hline("=")
    print("Summary: the domain with the more stable, better-posed constraint")
    print("system (lower residual, higher rigidity) overwrites the weaker one.")
    hline("=")


if __name__ == "__main__":
    main()
