"""Projection: stdlib power-iteration PCA returns deterministic 2-D coordinates.

Asserts:

* :func:`project_2d` returns one 2-tuple per input point,
* it is deterministic (no RNG): calling it twice yields identical output,
* the principal axes are unit-norm and orthogonal (``top2_axes``),
* the projection captures variance (a clearly anisotropic cloud spreads more along
  PC1 than PC2), and
* an empty input yields an empty projection.
"""

from __future__ import annotations

import math

from central_finite_curve.core import projection as P
from central_finite_curve.core.config import CurveConfig
from central_finite_curve.core.sampling import child_rng, uniform_vector


def _cloud(n: int, dim: int):
    rng = child_rng(7, 1)
    # Anisotropic: dim 0 stretched, others compressed, so PC1 is unambiguous.
    pts = []
    for _ in range(n):
        v = uniform_vector(rng, dim, 1.0)
        v[0] *= 10.0
        pts.append(v)
    return pts


def test_project_2d_returns_pairs() -> None:
    pts = _cloud(200, 8)
    proj = P.project_2d(pts)
    assert len(proj) == len(pts)
    assert all(len(p) == 2 for p in proj)


def test_project_2d_deterministic() -> None:
    pts = _cloud(150, 8)
    assert P.project_2d(pts) == P.project_2d(pts)


def test_axes_orthonormal() -> None:
    _means, v1, v2 = P.top2_axes(_cloud(200, 8))
    assert math.isclose(math.sqrt(sum(x * x for x in v1)), 1.0, rel_tol=1e-9)
    assert math.isclose(math.sqrt(sum(x * x for x in v2)), 1.0, rel_tol=1e-9)
    dot = sum(a * b for a, b in zip(v1, v2))
    assert abs(dot) < 1e-6


def test_projection_captures_dominant_variance() -> None:
    proj = P.project_2d(_cloud(400, 8))
    var_pc1 = sum(a * a for a, _ in proj) / len(proj)
    var_pc2 = sum(b * b for _, b in proj) / len(proj)
    assert var_pc1 > var_pc2


def test_empty_projection() -> None:
    assert P.project_2d([]) == []


# ---------------------------------------------------------------------------
# project_3d: top-3 view, deterministic, and consistent with the 2-D projection
# ---------------------------------------------------------------------------

def test_project_3d_returns_triples() -> None:
    pts = _cloud(200, 8)
    proj = P.project_3d(pts)
    assert len(proj) == len(pts)
    assert all(len(p) == 3 for p in proj)


def test_project_3d_deterministic() -> None:
    pts = _cloud(150, 8)
    assert P.project_3d(pts) == P.project_3d(pts)


def test_project_3d_first_two_match_2d() -> None:
    # The 3-D projection reuses the 2-D deflation sequence, so its first two
    # components are bit-for-bit the existing 2-D projection (shared frame).
    pts = _cloud(200, 8)
    p2 = P.project_2d(pts)
    p3 = P.project_3d(pts)
    for (a2, b2), (a3, b3, _c3) in zip(p2, p3):
        assert math.isclose(a2, a3, rel_tol=0.0, abs_tol=1e-12)
        assert math.isclose(b2, b3, rel_tol=0.0, abs_tol=1e-12)


def test_project_3d_variance_ordering() -> None:
    proj = P.project_3d(_cloud(400, 8))
    n = len(proj)
    var_pc1 = sum(p[0] * p[0] for p in proj) / n
    var_pc2 = sum(p[1] * p[1] for p in proj) / n
    var_pc3 = sum(p[2] * p[2] for p in proj) / n
    assert var_pc1 >= var_pc2 >= var_pc3


def test_top3_axes_orthonormal() -> None:
    _means, v1, v2, v3 = P.top3_axes(_cloud(200, 8))
    for v in (v1, v2, v3):
        assert math.isclose(math.sqrt(sum(x * x for x in v)), 1.0, rel_tol=1e-9)
    for a, b in ((v1, v2), (v1, v3), (v2, v3)):
        assert abs(sum(x * y for x, y in zip(a, b))) < 1e-6


def test_project_3d_empty() -> None:
    assert P.project_3d([]) == []
