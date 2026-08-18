"""Linear-algebra helpers.

numpy is used if available, otherwise a pure-python fallback is provided.
The systems here are small (grids of a few hundred unknowns at most for the
direct solve, and iterative relaxation for the field), so pure-python
Gaussian elimination is perfectly adequate.
"""

from __future__ import annotations

try:  # import-guarded numpy
    import numpy as _np

    HAVE_NUMPY = True
except Exception:  # pragma: no cover - exercised when numpy is absent
    _np = None
    HAVE_NUMPY = False


Vector = list  # list[float]
Matrix = list  # list[list[float]]


def zeros(n: int) -> Vector:
    return [0.0 for _ in range(n)]


def dot(a: Vector, b: Vector) -> float:
    return sum(x * y for x, y in zip(a, b))


def norm2(a: Vector) -> float:
    """Euclidean (L2) norm."""
    return sum(x * x for x in a) ** 0.5


def norm_inf(a: Vector) -> float:
    """Max-absolute (L-infinity) norm."""
    return max((abs(x) for x in a), default=0.0)


def matvec(A: Matrix, x: Vector) -> Vector:
    return [dot(row, x) for row in A]


def gaussian_solve(A: Matrix, b: Vector) -> Vector:
    """Solve A x = b via Gaussian elimination with partial pivoting.

    Pure python, non-destructive: copies inputs and returns a new vector.
    Raises ValueError if the matrix is singular.
    """
    n = len(A)
    # Build an augmented copy so we never mutate the caller's data.
    M = [list(A[i]) + [b[i]] for i in range(n)]

    for col in range(n):
        # Partial pivot: find the row with the largest magnitude in this column.
        pivot = max(range(col, n), key=lambda r: abs(M[r][col]))
        if abs(M[pivot][col]) < 1e-15:
            raise ValueError("Singular matrix: constraints are inconsistent/degenerate")
        if pivot != col:
            M[col], M[pivot] = M[pivot], M[col]

        pivot_val = M[col][col]
        for r in range(col + 1, n):
            factor = M[r][col] / pivot_val
            if factor == 0.0:
                continue
            for c in range(col, n + 1):
                M[r][c] -= factor * M[col][c]

    # Back substitution.
    x = zeros(n)
    for i in range(n - 1, -1, -1):
        s = M[i][n] - sum(M[i][c] * x[c] for c in range(i + 1, n))
        x[i] = s / M[i][i]
    return x


def spectral_radius_estimate(A: Matrix, iters: int = 200) -> float:
    """Estimate the largest-magnitude eigenvalue via power iteration.

    Used as a cheap conditioning / rigidity proxy. Pure python.
    """
    n = len(A)
    v = [1.0 / (n ** 0.5)] * n
    lam = 0.0
    for _ in range(iters):
        w = matvec(A, v)
        nrm = norm2(w)
        if nrm < 1e-18:
            return 0.0
        v = [x / nrm for x in w]
        lam = nrm
    return lam
