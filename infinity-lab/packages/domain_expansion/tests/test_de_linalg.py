"""Unit tests for the pure linear-algebra core (domain_expansion.core.linalg)."""

from __future__ import annotations

import math

import pytest

from domain_expansion.core import linalg


def test_gaussian_solve_known_system() -> None:
    # 2x + y = 5 ; x - 3y = -1  -> x = 2, y = 1.
    matrix = [[2.0, 1.0], [1.0, -3.0]]
    b = [5.0, -1.0]
    x = linalg.gaussian_solve(matrix, b)
    assert x[0] == pytest.approx(2.0, abs=1e-12)
    assert x[1] == pytest.approx(1.0, abs=1e-12)


def test_gaussian_solve_needs_partial_pivot() -> None:
    # A zero leading pivot forces a row swap; the answer must still be exact.
    matrix = [[0.0, 2.0], [1.0, 1.0]]
    b = [4.0, 3.0]
    x = linalg.gaussian_solve(matrix, b)
    residual = [
        matrix[0][0] * x[0] + matrix[0][1] * x[1] - b[0],
        matrix[1][0] * x[0] + matrix[1][1] * x[1] - b[1],
    ]
    assert linalg.norm2(residual) < 1e-12


def test_gaussian_solve_is_non_destructive() -> None:
    matrix = [[3.0, 0.0], [0.0, 4.0]]
    b = [6.0, 8.0]
    linalg.gaussian_solve(matrix, b)
    assert matrix == [[3.0, 0.0], [0.0, 4.0]]
    assert b == [6.0, 8.0]


def test_gaussian_solve_singular_raises() -> None:
    with pytest.raises(ValueError):
        linalg.gaussian_solve([[1.0, 2.0], [2.0, 4.0]], [1.0, 2.0])


def test_norms() -> None:
    assert linalg.norm2([3.0, 4.0]) == pytest.approx(5.0)
    assert linalg.norm_inf([-7.0, 2.0, 5.0]) == pytest.approx(7.0)
    assert linalg.norm_inf([]) == 0.0


def test_spectral_radius_of_diagonal_matrix() -> None:
    # Dominant eigenvalue of diag(5, -2, 1) has magnitude 5.
    matrix = [[5.0, 0.0, 0.0], [0.0, -2.0, 0.0], [0.0, 0.0, 1.0]]
    est = linalg.spectral_radius_estimate(matrix, iters=500)
    assert est == pytest.approx(5.0, abs=1e-6)


def test_spectral_radius_symmetric_stencil() -> None:
    # 2x2 [[2,1],[1,2]] has eigenvalues 1 and 3 (dominant eigenvector [1,1]);
    # power iteration from the uniform start converges to 3.
    est = linalg.spectral_radius_estimate([[2.0, 1.0], [1.0, 2.0]], iters=500)
    assert est == pytest.approx(3.0, abs=1e-6)


def test_matvec_and_dot_shapes() -> None:
    assert linalg.matvec([[1.0, 2.0], [3.0, 4.0]], [1.0, 1.0]) == [3.0, 7.0]
    with pytest.raises(ValueError):
        linalg.dot([1.0], [1.0, 2.0])


def test_spectral_radius_zero_matrix() -> None:
    assert linalg.spectral_radius_estimate([[0.0, 0.0], [0.0, 0.0]]) == 0.0


def test_gaussian_solve_larger_random_consistency() -> None:
    # Diagonally dominant so it is well conditioned; check A x == b.
    matrix = [
        [10.0, 1.0, 2.0],
        [1.0, 12.0, 3.0],
        [2.0, 3.0, 15.0],
    ]
    b = [13.0, 16.0, 20.0]
    x = linalg.gaussian_solve(matrix, b)
    recon = linalg.matvec(matrix, x)
    assert math.isclose(recon[0], b[0], abs_tol=1e-10)
    assert linalg.norm2([recon[i] - b[i] for i in range(3)]) < 1e-10
