"""Vectorised numpy fast-paths mirroring the pure float-valued Rickness core.

Each routine reproduces, over a whole batch of universes at once, a scalar
computation that :mod:`central_finite_curve.core.rickness` performs one universe at
a time. numpy is NEVER imported at module top level: every function calls
:func:`commons.core.optional.try_import` lazily and raises
:class:`OptionalDependencyError` when numpy is absent, so importing this module
with the standard library alone never fails.

Parity honesty
--------------
* :func:`complexity_values`, :func:`penalty_values` are polynomial / ``tanh`` in the
  coordinates; the pure core and numpy agree to within a few ULP.
* :func:`entropy_values` routes through ``exp``/``log``; libm (pure core) and numpy
  agree to within ~1 ULP per element, a few ULP after the reduction.
* :func:`rickness_values` is the weighted combination of the three, so it inherits
  the same few-ULP agreement. The parity test asserts ``allclose(atol=1e-12)``.

:func:`project_2d_numpy` mirrors :func:`central_finite_curve.core.projection.project_2d`
using ``numpy.linalg.eigh``; principal axes are sign-ambiguous, so callers that
compare against the pure path must align signs (the parity test compares variances,
which are sign invariant).
"""

from __future__ import annotations

from typing import Any, List, Sequence, Tuple

from commons.core.optional import try_import

from central_finite_curve.core.config import DEFAULT, CurveConfig


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
            "numpy is required for central_finite_curve.accel fast-paths but is not "
            "installed; install the 'viz' extra (pip install -e '.[viz]') or use the "
            "pure central_finite_curve.core functions instead"
        )
    return np


def _as_matrix(coords: Sequence[Sequence[float]]) -> Any:
    """Return ``coords`` as a float ``(n, dim)`` numpy array (raises on empty)."""
    np = _numpy()
    if len(coords) == 0:
        raise ValueError("coords must be non-empty")
    return np.asarray(coords, dtype=np.float64)


def complexity_values(coords: Sequence[Sequence[float]]) -> Any:
    """Vectorised ``complexity`` = ``tanh(std(x)/2)`` for each row of ``coords``."""
    np = _numpy()
    arr = _as_matrix(coords)
    std = np.std(arr, axis=1)  # population std, matching the pure core's /n variance
    return np.tanh(std / 2.0)


def entropy_values(coords: Sequence[Sequence[float]]) -> Any:
    """Vectorised normalised Shannon entropy of ``softmax(|x|)`` per row."""
    np = _numpy()
    arr = _as_matrix(coords)
    dim = arr.shape[1]
    mags = np.abs(arr)
    m = mags.max(axis=1, keepdims=True)
    exps = np.exp(mags - m)
    total = exps.sum(axis=1, keepdims=True)
    probs = exps / total
    # 0 * log 0 -> 0; clip only inside the log to avoid warnings.
    logs = np.where(probs > 0.0, np.log(probs), 0.0)
    h = -(probs * logs).sum(axis=1)
    return h / np.log(dim)


def penalty_values(
    coords: Sequence[Sequence[float]], config: CurveConfig = DEFAULT
) -> Any:
    """Vectorised constraint penalty (sum of squared residuals) per row."""
    np = _numpy()
    arr = _as_matrix(coords)
    r = config.ring_radius
    g0 = arr[:, 0] ** 2 + arr[:, 1] ** 2 - r * r
    g1 = arr[:, 2] - np.sin(np.pi * arr[:, 0])
    g2 = arr[:, 3] + arr[:, 4]
    g3 = arr[:, 5] * arr[:, 6] - 1.0
    return g0 * g0 + g1 * g1 + g2 * g2 + g3 * g3


def rickness_values(
    coords: Sequence[Sequence[float]], config: CurveConfig = DEFAULT
) -> Any:
    """Vectorised Rickness score per row, mirroring the scalar core.

    Equals ``w_complexity*complexity + w_entropy*entropy - w_penalty*penalty``
    elementwise, agreeing with the pure core to within a few ULP.
    """
    comp = complexity_values(coords)
    ent = entropy_values(coords)
    pen = penalty_values(coords, config)
    return (
        config.w_complexity * comp
        + config.w_entropy * ent
        - config.w_penalty * pen
    )


def _project_k_numpy(
    points: Sequence[Sequence[float]], k: int
) -> List[Tuple[float, ...]]:
    """Top-``k`` principal-component projection via ``numpy.linalg.eigh``.

    Shared engine for :func:`project_2d_numpy` / :func:`project_3d_numpy`. Principal
    axes are sign-ambiguous versus the pure core; the projected *variances* match.
    Returns ``[]`` for empty input. Raises :class:`ValueError` for ``k < 1``.
    """
    if k < 1:
        raise ValueError("k must be >= 1")
    if len(points) == 0:
        return []
    np = _numpy()
    arr = np.asarray(points, dtype=np.float64)
    means = arr.mean(axis=0)
    centered = arr - means
    cov = np.cov(centered, rowvar=False)
    vals, vecs = np.linalg.eigh(cov)
    order = np.argsort(vals)[::-1][:k]
    axes = vecs[:, order]
    coords = centered @ axes
    return [tuple(float(v) for v in row) for row in coords]


def project_2d_numpy(
    points: Sequence[Sequence[float]],
) -> List[Tuple[float, float]]:
    """Top-2 principal-component projection to 2-D via ``numpy.linalg.eigh``.

    Mirrors :func:`central_finite_curve.core.projection.project_2d`. Principal axes
    are sign-ambiguous between the two paths; the projected *variances* match. Returns
    ``[]`` for empty input.
    """
    return [(c[0], c[1]) for c in _project_k_numpy(points, 2)]


def project_3d_numpy(
    points: Sequence[Sequence[float]],
) -> List[Tuple[float, float, float]]:
    """Top-3 principal-component projection to 3-D via ``numpy.linalg.eigh``.

    Mirrors :func:`central_finite_curve.core.projection.project_3d`. Principal axes
    are sign-ambiguous between the two paths; the projected *variances* match. Returns
    ``[]`` for empty input.
    """
    return [(c[0], c[1], c[2]) for c in _project_k_numpy(points, 3)]
