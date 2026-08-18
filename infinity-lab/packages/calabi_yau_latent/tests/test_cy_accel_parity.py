"""Parity: the numpy fast-paths must equal the pure metric core, value-for-value.

OPTIONAL and DEFERRED: begins with ``pytest.importorskip("numpy")`` so it SKIPS on
the stdlib-only system interpreter (no numpy) and RUNS on the venv (numpy present).

Each fast-path in :mod:`calabi_yau_latent.accel.numpy_backend` computes a whole
pairwise distance matrix that the pure :mod:`calabi_yau_latent.core.distance`
computes one pair at a time. We assert they agree to ``atol = 1e-12`` (a few ULP
through the shared ``mod``/fold). The batch is built once from the seeded
generator and passed to both paths, so any difference is a genuine numerical-path
difference, not different sample points.
"""

from __future__ import annotations

import pytest

np = pytest.importorskip("numpy")

from calabi_yau_latent.accel import numpy_backend as accel
from calabi_yau_latent.core.config import DEFAULT
from calabi_yau_latent.core.data import generate, make_space
from calabi_yau_latent.core.distance import (
    naive_angular_distance,
    toroidal_angular_distance,
    toroidal_distance,
)

_ATOL = 1e-12


def _batch():
    space = make_space(DEFAULT)
    points, _truth, _xy = generate(space, DEFAULT)
    extended = [list(p.extended) for p in points]
    angles = [list(p.angles) for p in points]
    return space, points, extended, angles


def _pure_matrix(points, metric):
    n = len(points)
    return np.array(
        [[metric(points[i], points[j]) for j in range(n)] for i in range(n)]
    )


def test_naive_angular_matrix_matches_core() -> None:
    _space, points, _ext, angles = _batch()
    fast = accel.naive_angular_distance_matrix(angles)
    pure = _pure_matrix(points, naive_angular_distance)
    assert np.allclose(fast, pure, atol=_ATOL, rtol=0.0)


def test_toroidal_angular_matrix_matches_core() -> None:
    _space, points, _ext, angles = _batch()
    fast = accel.toroidal_angular_distance_matrix(angles)
    pure = _pure_matrix(points, toroidal_angular_distance)
    assert np.allclose(fast, pure, atol=_ATOL, rtol=0.0)


def test_toroidal_full_matrix_matches_core() -> None:
    space, points, ext, angles = _batch()
    fast = accel.toroidal_distance_matrix(ext, angles, list(space.radii))
    pure = _pure_matrix(points, lambda p, q: toroidal_distance(space, p, q))
    assert np.allclose(fast, pure, atol=_ATOL, rtol=0.0)


def test_accel_raises_without_numpy_is_not_triggered_here() -> None:
    # numpy IS present in this test session; the matrix is a real ndarray.
    _space, _points, _ext, angles = _batch()
    out = accel.toroidal_angular_distance_matrix(angles)
    assert out.shape[0] == out.shape[1] == len(angles)
