"""Optional numpy fast-paths mirroring the pure linear-algebra core.

Each routine reproduces, with numpy, a computation that
:mod:`domain_expansion.core.linalg` performs in pure python. numpy is NEVER
imported at module top level: every function calls
:func:`commons.core.optional.try_import` lazily and raises
:class:`OptionalDependencyError` when numpy is absent, so importing this module
with the standard library alone never fails.

Parity honesty
--------------
* :func:`gaussian_solve_numpy` routes through ``numpy.linalg.solve`` (LAPACK LU);
  it agrees with the pure partial-pivot elimination to within a few ULP on the
  small, well-conditioned interior systems this package builds.
* :func:`spectral_radius_numpy` returns ``max(abs(eigvals))`` via
  ``numpy.linalg.eigvals``; the pure power-iteration estimate converges to the
  same dominant magnitude for the diagonally-dominant stencils used here. The
  parity test asserts agreement to a modest absolute tolerance.
"""

from __future__ import annotations

from typing import Any, List, Sequence

from commons.core.optional import try_import


class OptionalDependencyError(RuntimeError):
    """Raised when a numpy fast-path is requested but numpy is unavailable.

    The pure core never raises this; only these deferred accel routines do, and
    only when the caller invokes them without numpy installed.
    """


def _numpy() -> Any:
    """Return the numpy module, or raise :class:`OptionalDependencyError`.

    numpy is imported LAZILY via :func:`commons.core.optional.try_import`, so this
    module stays importable with the standard library alone.
    """
    np = try_import("numpy")
    if np is None:
        raise OptionalDependencyError(
            "numpy is required for domain_expansion.accel fast-paths but is not "
            "installed; install the 'viz' extra (pip install -e '.[viz]') or use the "
            "pure domain_expansion.core.linalg functions instead"
        )
    return np


def gaussian_solve_numpy(
    matrix: Sequence[Sequence[float]], b: Sequence[float]
) -> List[float]:
    """Solve ``A x = b`` via ``numpy.linalg.solve``; mirrors ``linalg.gaussian_solve``.

    Raises :class:`ValueError` for a non-square matrix or a mismatched right-hand
    side, matching the pure core's contract.
    """
    np = _numpy()
    a_arr = np.asarray(matrix, dtype=np.float64)
    if a_arr.ndim != 2 or a_arr.shape[0] != a_arr.shape[1]:
        raise ValueError("matrix must be square")
    b_arr = np.asarray(b, dtype=np.float64)
    if b_arr.shape[0] != a_arr.shape[0]:
        raise ValueError("b length must match matrix dimension")
    x = np.linalg.solve(a_arr, b_arr)
    return [float(v) for v in x]


def spectral_radius_numpy(matrix: Sequence[Sequence[float]]) -> float:
    """Return ``max(abs(eigvals(matrix)))``; mirrors ``linalg.spectral_radius_estimate``.

    Raises :class:`ValueError` for a non-square matrix.
    """
    np = _numpy()
    a_arr = np.asarray(matrix, dtype=np.float64)
    if a_arr.ndim != 2 or a_arr.shape[0] != a_arr.shape[1]:
        raise ValueError("matrix must be square")
    if a_arr.shape[0] == 0:
        return 0.0
    eigenvalues = np.linalg.eigvals(a_arr)
    return float(np.max(np.abs(eigenvalues)))
