"""Pure-python linear-algebra helpers for the domain solver.

This module is deliberately dependency free: it imports only the standard
library, so it can live in the pure :mod:`domain_expansion.core` layer. The
systems solved here are tiny (a few hundred unknowns for the direct solve, and
iterative relaxation for the field), so pure-python Gaussian elimination and
power iteration are perfectly adequate.

Optional numpy fast-paths for these same routines live in
:mod:`domain_expansion.accel.numpy_backend` and are lazily guarded; the core
never imports them.
"""

from __future__ import annotations

from typing import List

Vector = List[float]
Matrix = List[List[float]]

_SINGULAR_EPS = 1e-15


def zeros(n: int) -> Vector:
    """Return a length-``n`` zero vector. Raises for ``n < 0``."""
    if n < 0:
        raise ValueError("n must be >= 0")
    return [0.0 for _ in range(n)]


def dot(a: Vector, b: Vector) -> float:
    """Euclidean inner product. Raises :class:`ValueError` on length mismatch."""
    if len(a) != len(b):
        raise ValueError("dot requires equal-length vectors")
    return sum(x * y for x, y in zip(a, b))


def norm2(a: Vector) -> float:
    """Euclidean (L2) norm of ``a``."""
    return sum(x * x for x in a) ** 0.5


def norm_inf(a: Vector) -> float:
    """Max-absolute (L-infinity) norm of ``a`` (0.0 for an empty vector)."""
    return max((abs(x) for x in a), default=0.0)


def matvec(matrix: Matrix, x: Vector) -> Vector:
    """Matrix-vector product ``matrix @ x`` (each row dotted with ``x``)."""
    return [dot(row, x) for row in matrix]


def gaussian_solve(matrix: Matrix, b: Vector) -> Vector:
    """Solve ``A x = b`` via Gaussian elimination with partial pivoting.

    Pure python and non-destructive: the inputs are copied and a fresh vector is
    returned. Raises :class:`ValueError` if the matrix is singular (the
    constraints are inconsistent or degenerate) or the shapes disagree.
    """
    n = len(matrix)
    if n == 0:
        return []
    if any(len(row) != n for row in matrix):
        raise ValueError("matrix must be square")
    if len(b) != n:
        raise ValueError("b length must match matrix dimension")

    # Build an augmented copy so we never mutate the caller's data.
    aug: Matrix = [list(matrix[i]) + [b[i]] for i in range(n)]

    for col in range(n):
        # Partial pivot: the row with the largest magnitude in this column.
        pivot = max(range(col, n), key=lambda r: abs(aug[r][col]))
        if abs(aug[pivot][col]) < _SINGULAR_EPS:
            raise ValueError(
                "singular matrix: constraints are inconsistent/degenerate"
            )
        if pivot != col:
            aug[col], aug[pivot] = aug[pivot], aug[col]

        pivot_val = aug[col][col]
        for r in range(col + 1, n):
            factor = aug[r][col] / pivot_val
            if factor == 0.0:
                continue
            for c in range(col, n + 1):
                aug[r][c] -= factor * aug[col][c]

    # Back substitution.
    x = zeros(n)
    for i in range(n - 1, -1, -1):
        s = aug[i][n] - sum(aug[i][c] * x[c] for c in range(i + 1, n))
        x[i] = s / aug[i][i]
    return x


def spectral_radius_estimate(matrix: Matrix, iters: int = 200) -> float:
    """Estimate the largest-magnitude eigenvalue of ``matrix`` via power iteration.

    Used as a cheap conditioning / rigidity proxy. Pure python. Returns 0.0 if
    the iterate collapses to the zero vector. Raises :class:`ValueError` for a
    non-square matrix or ``iters < 1``.
    """
    n = len(matrix)
    if n == 0:
        return 0.0
    if any(len(row) != n for row in matrix):
        raise ValueError("matrix must be square")
    if iters < 1:
        raise ValueError("iters must be >= 1")

    v: Vector = [1.0 / (n ** 0.5)] * n
    lam = 0.0
    for _ in range(iters):
        w = matvec(matrix, v)
        nrm = norm2(w)
        if nrm < 1e-18:
            return 0.0
        v = [x / nrm for x in w]
        lam = nrm
    return lam
