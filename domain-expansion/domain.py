"""A 'Domain' = a closed region enforcing many simultaneous constraints.

We model a domain as a discretized boundary-value problem: the Laplace
equation on a rectangular grid,

        d2u/dx2 + d2u/dy2 = 0     inside the domain,
        u = g                     on the boundary (the fixed "sure-hit" condition).

Discretized on a grid, every interior cell must equal the average of its four
neighbours. That is a big set of simultaneous linear constraints. The unique
field that satisfies all of them at once is the domain's "manifestation".

JJK flavor:
  - The fixed boundary values are the guaranteed-hit condition (the technique
    that the domain forces onto everything inside).
  - Solving the field = expanding the domain until every point obeys the rule.
  - The 'refinement' of a domain = how stable / well-posed that solution is.
    A crude domain (noisy, weakly coupled) has a large residual and low
    rigidity; a refined domain locks in cleanly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Optional

import linalg


@dataclass
class Domain:
    """A closed rectangular region with fixed boundary constraints."""

    name: str
    nx: int
    ny: int
    # Boundary value function g(i, j) evaluated on border cells.
    boundary: Callable[[int, int], float]
    # Interior coupling weight. 1.0 == pure Laplace. Values < 1 model a
    # "crude" domain whose interior constraints are weakly / inconsistently
    # enforced (the technique leaks).
    coupling: float = 1.0
    # Per-cell interior source/noise term. A crude domain has non-zero noise:
    # its constraints do not perfectly cancel, raising the residual.
    noise: float = 0.0
    # Optional "Unlimited Void" cells: (i, j) -> forced value with huge weight.
    void_cells: dict = field(default_factory=dict)
    void_weight: float = 1e6

    def is_boundary(self, i: int, j: int) -> bool:
        return i == 0 or j == 0 or i == self.nx - 1 or j == self.ny - 1

    def initial_field(self) -> list:
        """Grid seeded with boundary values, interior at 0."""
        u = [[0.0 for _ in range(self.ny)] for _ in range(self.nx)]
        for i in range(self.nx):
            for j in range(self.ny):
                if self.is_boundary(i, j):
                    u[i][j] = self.boundary(i, j)
        return u


@dataclass
class SolveResult:
    field: list           # solved grid
    iterations: int
    residual_l2: float    # L2 norm of the constraint residual
    residual_inf: float   # max single-constraint violation
    rigidity: float       # conditioning / rigidity proxy (higher = more refined)
    converged: bool

    @property
    def refinement(self) -> float:
        """A single scalar: high rigidity and low residual => refined.

        Refinement score = rigidity / (1 + residual_l2). Larger is better.
        """
        return self.rigidity / (1.0 + self.residual_l2)


def _residual(domain: Domain, u: list) -> tuple:
    """Compute how badly the field violates the domain's constraints.

    For each interior cell the constraint is
        coupling * (4 u_ij - sum(neighbours)) - noise == 0.
    Void cells add a heavily weighted violation.
    Returns (l2_norm, inf_norm).
    """
    res = []
    for i in range(1, domain.nx - 1):
        for j in range(1, domain.ny - 1):
            neigh = u[i - 1][j] + u[i + 1][j] + u[i][j - 1] + u[i][j + 1]
            r = domain.coupling * (4.0 * u[i][j] - neigh) - domain.noise
            res.append(r)
    for (i, j), target in domain.void_cells.items():
        res.append(domain.void_weight * (u[i][j] - target))
    return linalg.norm2(res), linalg.norm_inf(res)


def solve_domain(
    domain: Domain,
    max_iters: int = 5000,
    tol: float = 1e-8,
    field_override: Optional[list] = None,
) -> SolveResult:
    """Gauss-Seidel relaxation to find the field satisfying all constraints.

    field_override lets a clash pre-load the contested region with another
    domain's values before this domain tries to reassert its constraints.
    """
    u = [row[:] for row in (field_override or domain.initial_field())]

    # Re-impose this domain's own boundary (its guaranteed condition) even if
    # an override tried to change it.
    for i in range(domain.nx):
        for j in range(domain.ny):
            if domain.is_boundary(i, j):
                u[i][j] = domain.boundary(i, j)

    converged = False
    it = 0
    for it in range(1, max_iters + 1):
        delta = 0.0
        for i in range(1, domain.nx - 1):
            for j in range(1, domain.ny - 1):
                if (i, j) in domain.void_cells:
                    new_val = domain.void_cells[(i, j)]
                else:
                    neigh = u[i - 1][j] + u[i + 1][j] + u[i][j - 1] + u[i][j + 1]
                    # Gauss-Seidel update for coupling*(4u - neigh) = noise.
                    new_val = (neigh + domain.noise / max(domain.coupling, 1e-9)) / 4.0
                delta = max(delta, abs(new_val - u[i][j]))
                u[i][j] = new_val
        if delta < tol:
            converged = True
            break

    res_l2, res_inf = _residual(domain, u)
    rigidity = _rigidity(domain)
    return SolveResult(
        field=u,
        iterations=it,
        residual_l2=res_l2,
        residual_inf=res_inf,
        rigidity=rigidity,
        converged=converged,
    )


def direct_solve_domain(domain: Domain) -> list:
    """Assemble the interior linear system and solve it directly (Gaussian).

    This is the 'direct solve' counterpart to the Gauss-Seidel relaxation and
    is used to cross-check that relaxation converged to the true solution.
    Ignores void cells / noise for the plain Laplace cross-check.
    """
    interior = [
        (i, j)
        for i in range(1, domain.nx - 1)
        for j in range(1, domain.ny - 1)
    ]
    index = {cell: k for k, cell in enumerate(interior)}
    n = len(interior)
    A = [[0.0] * n for _ in range(n)]
    b = linalg.zeros(n)

    for (i, j), k in index.items():
        A[k][k] = 4.0 * domain.coupling
        b[k] = domain.noise
        for (ni, nj) in ((i - 1, j), (i + 1, j), (i, j - 1), (i, j + 1)):
            if (ni, nj) in index:
                A[k][index[(ni, nj)]] = -1.0 * domain.coupling
            else:  # neighbour is a fixed boundary -> moves to right-hand side
                b[k] += domain.coupling * domain.boundary(ni, nj)

    x = linalg.gaussian_solve(A, b)

    u = domain.initial_field()
    for (i, j), k in index.items():
        u[i][j] = x[k]
    return u


def max_grid_diff(a: list, b: list) -> float:
    """Max absolute per-cell difference between two grids."""
    return max(
        abs(a[i][j] - b[i][j])
        for i in range(len(a))
        for j in range(len(a[0]))
    )


def _rigidity(domain: Domain) -> float:
    """Rigidity / well-posedness proxy for the interior constraint operator.

    We build the small interior Laplacian for a reduced grid and estimate its
    spectral radius via power iteration. A strongly coupled, void-reinforced
    domain has a larger operator norm => it is 'harder' and dominates a clash.
    Kept cheap and pure-python.
    """
    # Use a coarse representative interior operator (independent of grid size)
    # scaled by the domain's coupling, plus a bonus for void reinforcement.
    m = 4
    A = [[0.0] * m for _ in range(m)]
    for k in range(m):
        A[k][k] = 4.0 * domain.coupling
        if k > 0:
            A[k][k - 1] = -1.0 * domain.coupling
        if k < m - 1:
            A[k][k + 1] = -1.0 * domain.coupling
    base = linalg.spectral_radius_estimate(A)
    void_bonus = domain.void_weight * 1e-3 if domain.void_cells else 0.0
    # Penalize interior noise: leaky constraints reduce effective rigidity.
    noise_penalty = 1.0 + abs(domain.noise)
    return (base + void_bonus) / noise_penalty
