"""A 'Domain' = a closed region enforcing many simultaneous constraints.

We model a domain as a discretized boundary-value problem: the Laplace equation
on a rectangular grid,

    d2u/dx2 + d2u/dy2 = 0     inside the domain,
    u = g                     on the boundary (the fixed "sure-hit" condition).

Discretized with the 5-point stencil, every interior cell must equal the average
of its four neighbours. That is a big set of simultaneous linear constraints; the
unique field satisfying all of them at once is the domain's "manifestation".

JJK flavor:
  * The fixed boundary values are the guaranteed-hit condition (the technique the
    domain forces onto everything inside).
  * Solving the field = expanding the domain until every point obeys the rule.
  * The 'refinement' of a domain = how stable / well-posed that solution is. A
    crude domain (noisy, weakly coupled) has low rigidity; a refined domain locks
    in cleanly.

Two independent solvers are provided: Gauss-Seidel relaxation (:func:`solve_domain`)
and a direct Gaussian elimination (:func:`direct_solve_domain`). They agree to
tolerance, which is how we know relaxation reached the true field.

Pure module: standard library only (plus :mod:`domain_expansion.core.linalg`).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

from domain_expansion.core import linalg

Grid = List[List[float]]
Cell = Tuple[int, int]

_MIN_COUPLING = 1e-9
_RIGIDITY_STENCIL = 4
_VOID_RIGIDITY_SCALE = 1e-3


@dataclass
class Domain:
    """A closed rectangular region with fixed boundary constraints.

    ``coupling == 1.0`` and ``noise == 0.0`` is a clean Laplace domain (refined).
    ``coupling < 1`` with ``noise > 0`` models a crude domain whose interior
    constraints are weakly / inconsistently enforced (the technique leaks).
    ``void_cells`` pins interior cells with an enormous weight (Unlimited Void).
    """

    name: str
    nx: int
    ny: int
    # Boundary value function g(i, j) evaluated on border cells.
    boundary: Callable[[int, int], float]
    coupling: float = 1.0
    noise: float = 0.0
    void_cells: Dict[Cell, float] = field(default_factory=dict)
    void_weight: float = 1e6

    def __post_init__(self) -> None:
        if self.nx < 3 or self.ny < 3:
            raise ValueError("a domain needs at least a 3x3 grid (an interior cell)")

    def is_boundary(self, i: int, j: int) -> bool:
        """Return ``True`` iff ``(i, j)`` lies on the grid border."""
        return i == 0 or j == 0 or i == self.nx - 1 or j == self.ny - 1

    def initial_field(self) -> Grid:
        """Return a fresh grid seeded with boundary values, interior at 0."""
        u: Grid = [[0.0 for _ in range(self.ny)] for _ in range(self.nx)]
        for i in range(self.nx):
            for j in range(self.ny):
                if self.is_boundary(i, j):
                    u[i][j] = self.boundary(i, j)
        return u


@dataclass(frozen=True)
class SolveResult:
    """The solved field plus its constraint-quality metrics."""

    field: Grid
    iterations: int
    residual_l2: float
    residual_inf: float
    rigidity: float
    converged: bool

    @property
    def refinement(self) -> float:
        """A single scalar: high rigidity and low residual => refined.

        ``refinement = rigidity / (1 + residual_l2)``. Larger is better-posed.
        """
        return self.rigidity / (1.0 + self.residual_l2)


def _residual(domain: Domain, u: Grid) -> Tuple[float, float]:
    """Return ``(L2, Linf)`` norms of how badly ``u`` violates the constraints.

    For each interior cell the constraint is
    ``coupling * (4 u_ij - sum(neighbours)) - noise == 0``. Void cells add a
    heavily weighted violation.
    """
    res: List[float] = []
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
    field_override: Optional[Grid] = None,
) -> SolveResult:
    """Gauss-Seidel relaxation to find the field satisfying all constraints.

    ``field_override`` lets a clash pre-load the contested region with another
    domain's values before this domain reasserts its own constraints. This
    domain's boundary (its guaranteed condition) is always re-imposed. Raises
    :class:`ValueError` for ``max_iters < 1`` or ``tol <= 0``.
    """
    if max_iters < 1:
        raise ValueError("max_iters must be >= 1")
    if tol <= 0.0:
        raise ValueError("tol must be positive")

    u: Grid = [row[:] for row in (field_override or domain.initial_field())]

    # Re-impose this domain's own boundary even if an override changed it.
    for i in range(domain.nx):
        for j in range(domain.ny):
            if domain.is_boundary(i, j):
                u[i][j] = domain.boundary(i, j)

    converged = False
    it = 0
    coupling = max(domain.coupling, _MIN_COUPLING)
    for it in range(1, max_iters + 1):
        delta = 0.0
        for i in range(1, domain.nx - 1):
            for j in range(1, domain.ny - 1):
                if (i, j) in domain.void_cells:
                    new_val = domain.void_cells[(i, j)]
                else:
                    neigh = u[i - 1][j] + u[i + 1][j] + u[i][j - 1] + u[i][j + 1]
                    # Gauss-Seidel update for coupling*(4u - neigh) = noise.
                    new_val = (neigh + domain.noise / coupling) / 4.0
                delta = max(delta, abs(new_val - u[i][j]))
                u[i][j] = new_val
        if delta < tol:
            converged = True
            break

    res_l2, res_inf = _residual(domain, u)
    return SolveResult(
        field=u,
        iterations=it,
        residual_l2=res_l2,
        residual_inf=res_inf,
        rigidity=rigidity(domain),
        converged=converged,
    )


def direct_solve_domain(domain: Domain) -> Grid:
    """Assemble the interior linear system and solve it directly (Gaussian).

    This is the direct-solve counterpart to :func:`solve_domain` and is used to
    cross-check that relaxation converged to the true solution. Ignores void
    cells for the plain Laplace cross-check.
    """
    interior = [
        (i, j)
        for i in range(1, domain.nx - 1)
        for j in range(1, domain.ny - 1)
    ]
    index = {cell: k for k, cell in enumerate(interior)}
    n = len(interior)
    matrix: linalg.Matrix = [[0.0] * n for _ in range(n)]
    b = linalg.zeros(n)

    for (i, j), k in index.items():
        matrix[k][k] = 4.0 * domain.coupling
        b[k] = domain.noise
        for (ni, nj) in ((i - 1, j), (i + 1, j), (i, j - 1), (i, j + 1)):
            if (ni, nj) in index:
                matrix[k][index[(ni, nj)]] = -1.0 * domain.coupling
            else:  # neighbour is a fixed boundary -> moves to the right-hand side
                b[k] += domain.coupling * domain.boundary(ni, nj)

    x = linalg.gaussian_solve(matrix, b)

    u = domain.initial_field()
    for (i, j), k in index.items():
        u[i][j] = x[k]
    return u


def max_grid_diff(a: Grid, b: Grid) -> float:
    """Return the max absolute per-cell difference between two equal-shape grids."""
    if len(a) != len(b) or (a and len(a[0]) != len(b[0])):
        raise ValueError("grids must have matching shape")
    return max(
        (abs(a[i][j] - b[i][j]) for i in range(len(a)) for j in range(len(a[0]))),
        default=0.0,
    )


def rigidity(domain: Domain) -> float:
    """Rigidity / well-posedness proxy for the interior constraint operator.

    We build a small representative interior Laplacian and estimate its spectral
    radius via power iteration. A strongly coupled, void-reinforced domain has a
    larger operator norm, so it dominates a clash. Interior noise penalizes the
    effective rigidity. Cheap and pure-python.

    Honest caveat: this is a *proxy* -- the operator norm of a representative
    stencil, not the true condition number of the full assembled matrix. It is
    chosen because it is monotone in the qualities we care about (coupling
    strength, void reinforcement, low noise).
    """
    m = _RIGIDITY_STENCIL
    matrix: linalg.Matrix = [[0.0] * m for _ in range(m)]
    for k in range(m):
        matrix[k][k] = 4.0 * domain.coupling
        if k > 0:
            matrix[k][k - 1] = -1.0 * domain.coupling
        if k < m - 1:
            matrix[k][k + 1] = -1.0 * domain.coupling
    base = linalg.spectral_radius_estimate(matrix)
    void_bonus = domain.void_weight * _VOID_RIGIDITY_SCALE if domain.void_cells else 0.0
    noise_penalty = 1.0 + abs(domain.noise)
    return (base + void_bonus) / noise_penalty
