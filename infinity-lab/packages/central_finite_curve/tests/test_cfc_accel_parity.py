"""Parity: the numpy fast-paths must equal the pure Rickness core value-for-value.

OPTIONAL and DEFERRED: begins with ``pytest.importorskip("numpy")`` so it SKIPS on
the stdlib-only system interpreter (no numpy) and RUNS on the venv (numpy present).

Each fast-path in :mod:`central_finite_curve.accel.numpy_backend` evaluates a
quantity over a whole batch of universes that the pure
:mod:`central_finite_curve.core.rickness` computes one at a time. We assert they
agree to ``atol = 1e-12`` (a few ULP through the shared ``exp``/``log``). The batch
is built once from the seeded generator and passed to both paths, so any difference
is a genuine numerical-path difference, not different sample points.
"""

from __future__ import annotations

import pytest

np = pytest.importorskip("numpy")

from central_finite_curve.accel import numpy_backend as accel
from central_finite_curve.core.rickness import complexity, entropy, penalty, rickness
from central_finite_curve.core.config import CurveConfig
from central_finite_curve.core.multiverse import generate
from central_finite_curve.core.sampling import child_rng

_CONFIG = CurveConfig(n_universes=500, walk_steps=0, seed=137)
_ATOL = 1e-12


def _coords():
    universes = generate(child_rng(_CONFIG.seed, 1), _CONFIG)
    return [list(u.coords) for u in universes]


def test_complexity_values_match_core() -> None:
    coords = _coords()
    fast = accel.complexity_values(coords)
    pure = np.array([complexity(c) for c in coords])
    assert np.allclose(fast, pure, atol=_ATOL, rtol=0.0)


def test_entropy_values_match_core() -> None:
    coords = _coords()
    fast = accel.entropy_values(coords)
    pure = np.array([entropy(c) for c in coords])
    assert np.allclose(fast, pure, atol=_ATOL, rtol=0.0)


def test_penalty_values_match_core() -> None:
    coords = _coords()
    fast = accel.penalty_values(coords, _CONFIG)
    pure = np.array([penalty(c, _CONFIG) for c in coords])
    assert np.allclose(fast, pure, atol=_ATOL, rtol=0.0)


def test_rickness_values_match_core() -> None:
    coords = _coords()
    fast = accel.rickness_values(coords, _CONFIG)
    pure = np.array([rickness(c, _CONFIG) for c in coords])
    max_abs = float(np.max(np.abs(fast - pure)))
    assert max_abs <= _ATOL, f"rickness parity broke: max abs diff {max_abs:.3e}"


def test_numpy_pca_variance_matches_stdlib() -> None:
    # Principal axes are sign-ambiguous between eigh and power-iteration, but the
    # projected variances (sign invariant) must agree.
    from central_finite_curve.core import projection as core_proj

    coords = _coords()
    fast = accel.project_2d_numpy(coords)
    pure = core_proj.project_2d(coords)
    for pair in (fast, pure):
        var1 = sum(a * a for a, _ in pair) / len(pair)
        var2 = sum(b * b for _, b in pair) / len(pair)
        assert var1 >= var2  # PC1 dominates in both paths
    fast_v1 = sum(a * a for a, _ in fast) / len(fast)
    pure_v1 = sum(a * a for a, _ in pure) / len(pure)
    assert fast_v1 == pytest.approx(pure_v1, rel=1e-6)


def test_numpy_pca_3d_variance_matches_stdlib() -> None:
    # The top-3 numpy projection must agree (sign-invariantly) with the pure core:
    # PC1 >= PC2 >= PC3 in both paths and PC1 variance matches.
    from central_finite_curve.core import projection as core_proj

    coords = _coords()
    fast = accel.project_3d_numpy(coords)
    pure = core_proj.project_3d(coords)
    for triples in (fast, pure):
        n = len(triples)
        v1 = sum(p[0] * p[0] for p in triples) / n
        v2 = sum(p[1] * p[1] for p in triples) / n
        v3 = sum(p[2] * p[2] for p in triples) / n
        assert v1 >= v2 >= v3
    fast_v1 = sum(p[0] * p[0] for p in fast) / len(fast)
    pure_v1 = sum(p[0] * p[0] for p in pure) / len(pure)
    assert fast_v1 == pytest.approx(pure_v1, rel=1e-6)


def test_optional_dependency_error_is_runtime_error() -> None:
    assert issubclass(accel.OptionalDependencyError, RuntimeError)
