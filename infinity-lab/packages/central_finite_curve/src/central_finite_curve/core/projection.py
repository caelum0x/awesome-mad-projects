"""Project the high-dimensional curve down to 2-D (or 3-D) for viewing.

We use the top principal components (directions of greatest variance) of the
supplied points. This is a pure-stdlib power-iteration eigensolver with deflation:
form the covariance, extract the dominant eigenvector by power iteration, deflate,
and repeat for each successive component. Both the initial vector and the iteration
are fixed, so the projection is fully deterministic (no RNG). A numpy fast-path
lives separately in :mod:`central_finite_curve.accel.numpy_backend` and is never
imported here, so the core stays dependency free.

Two entry points share one deterministic eigensolver:

* :func:`project_2d` -- the classic top-2 view (unchanged, back-compatible), and
* :func:`project_3d` -- a top-3 view for the rotating 3-D animation.

Because the deflation sequence is identical, the first two components of
:func:`project_3d` match :func:`project_2d` exactly, so the 2-D and 3-D renderings
share a consistent frame.

Purity: imports only the standard library.
"""

from __future__ import annotations

import math
from typing import List, Sequence, Tuple

Vector = Sequence[float]
Matrix = List[List[float]]

# Power-iteration steps: plenty for a well-separated leading spectrum.
_POWER_ITERS = 200


def _mean_vector(points: Sequence[Vector]) -> List[float]:
    dim = len(points[0])
    means = [0.0] * dim
    for p in points:
        for j in range(dim):
            means[j] += p[j]
    n = len(points)
    return [m / n for m in means]


def _covariance(points: Sequence[Vector], means: Sequence[float]) -> Matrix:
    dim = len(means)
    cov: Matrix = [[0.0] * dim for _ in range(dim)]
    for p in points:
        d = [p[j] - means[j] for j in range(dim)]
        for i in range(dim):
            di = d[i]
            row = cov[i]
            for j in range(dim):
                row[j] += di * d[j]
    n = len(points)
    for i in range(dim):
        for j in range(dim):
            cov[i][j] /= n
    return cov


def _matvec(mat: Matrix, vec: Vector) -> List[float]:
    return [
        sum(mat[i][j] * vec[j] for j in range(len(vec))) for i in range(len(mat))
    ]


def _normalize(vec: Vector) -> List[float]:
    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0.0:
        return list(vec)
    return [v / norm for v in vec]


def _power_iteration(mat: Matrix, iters: int = _POWER_ITERS) -> Tuple[List[float], float]:
    """Dominant eigenvector/value via power iteration (deterministic start)."""
    dim = len(mat)
    v = _normalize([1.0 + 0.01 * i for i in range(dim)])
    for _ in range(iters):
        v = _normalize(_matvec(mat, v))
    w = _matvec(mat, v)
    val = sum(v[i] * w[i] for i in range(dim))
    return v, val


def _deflate(mat: Matrix, vec: Vector, val: float) -> Matrix:
    dim = len(mat)
    return [
        [mat[i][j] - val * vec[i] * vec[j] for j in range(dim)] for i in range(dim)
    ]


def _top_axes(points: Sequence[Vector], n_components: int) -> Tuple[List[float], List[List[float]]]:
    """Return ``(means, axes)`` -- the centroid and top-``n_components`` principal axes.

    Deterministic power iteration with sequential deflation: the ``k``-th axis is the
    dominant eigenvector of the covariance after the first ``k`` axes have been
    deflated away. Because the deflation order is fixed, the first ``m`` axes of a
    ``k``-component call (``k >= m``) are identical to an ``m``-component call, so the
    2-D and 3-D projections share a consistent frame. Raises :class:`ValueError` for
    ``n_components < 1``.
    """
    if n_components < 1:
        raise ValueError("n_components must be >= 1")
    means = _mean_vector(points)
    mat = _covariance(points, means)
    axes: List[List[float]] = []
    for _ in range(n_components):
        vec, val = _power_iteration(mat)
        axes.append(vec)
        mat = _deflate(mat, vec, val)
    return means, axes


def top2_axes(points: Sequence[Vector]) -> Tuple[List[float], List[float], List[float]]:
    """Return ``(means, pc1, pc2)`` -- the centroid and top-2 principal axes."""
    means, axes = _top_axes(points, 2)
    return means, axes[0], axes[1]


def top3_axes(
    points: Sequence[Vector],
) -> Tuple[List[float], List[float], List[float], List[float]]:
    """Return ``(means, pc1, pc2, pc3)`` -- the centroid and top-3 principal axes.

    The first two axes match :func:`top2_axes` exactly (shared deflation sequence).
    """
    means, axes = _top_axes(points, 3)
    return means, axes[0], axes[1], axes[2]


def _project_onto(
    points: Sequence[Vector], means: Sequence[float], axes: Sequence[Sequence[float]]
) -> List[Tuple[float, ...]]:
    """Project each centred point onto every axis; returns one tuple per point."""
    dim = len(means)
    out: List[Tuple[float, ...]] = []
    for p in points:
        d = [p[j] - means[j] for j in range(dim)]
        out.append(tuple(sum(d[j] * ax[j] for j in range(dim)) for ax in axes))
    return out


def project_2d(points: Sequence[Vector]) -> List[Tuple[float, float]]:
    """Return 2-D coordinates of each point along the top-2 principal axes.

    Deterministic: calling it twice with the same points yields identical output.
    Returns ``[]`` for an empty input.
    """
    if not points:
        return []
    means, axes = _top_axes(points, 2)
    return [(c[0], c[1]) for c in _project_onto(points, means, axes)]


def project_3d(points: Sequence[Vector]) -> List[Tuple[float, float, float]]:
    """Return 3-D coordinates of each point along the top-3 principal axes.

    Deterministic (no RNG) and consistent with :func:`project_2d`: the first two
    coordinates of each triple equal the corresponding :func:`project_2d` pair, so a
    3-D view and the 2-D view share one frame. Returns ``[]`` for an empty input.
    """
    if not points:
        return []
    means, axes = _top_axes(points, 3)
    return [(c[0], c[1], c[2]) for c in _project_onto(points, means, axes)]
