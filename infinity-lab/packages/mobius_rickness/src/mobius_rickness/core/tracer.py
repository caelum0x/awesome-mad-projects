"""Real tracing of the Central Finite Curve = the zero set ``R^{-1}(0)``.

Because ``K < 0`` everywhere on the Mobius interior, ``K_Rick = K * R`` vanishes
exactly where the sign-changing Rickness ``R`` vanishes, so tracing the Central
Finite Curve means tracing ``R^{-1}(0)``. Two complementary, cross-checking paths
are provided, both stdlib + :mod:`commons.core` only:

  * SCAN-LINE BISECTION (:func:`trace_columns`) -- for each ``u`` column, scan
    ``v`` for sign changes of ``R`` and refine every crossing with
    :func:`commons.core.numerics.bisection` to ``tol = 1e-9``, then lift to 3D.
  * MARCHING SQUARES (:func:`march_zero_segments`) -- 16-case contour extraction
    over the ``(u, v)`` grid with each edge crossing refined by bisection, then
    :func:`stitch_segments` links segments into ordered polylines, seam-stitching
    across the Mobius v-flip ``r(2*pi, v) = r(0, -v)`` so the curve closes across
    the ``u = 0 / 2*pi`` seam.

Every traced point satisfies ``|R| < 1e-6`` and ``|K_Rick| < 1e-6`` (verified by
:func:`verify_curve`). The torus zero circles ``theta = pi/2, 3*pi/2`` are located
by the same bisection machinery (:func:`trace_torus_zero_circles`).
"""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Callable, Dict, List, NamedTuple, Optional, Tuple

from commons.core.numerics import bisection, find_sign_changes

from mobius_rickness.core.field import k_rick
from mobius_rickness.core.geometry import TWO_PI, mobius_seam_wrap
from mobius_rickness.core.mobius import surface as mobius_surface
from mobius_rickness.core.rickness import V_MAX, V_MIN, rickness
from mobius_rickness.core.torus import gaussian_curvature_closed

Point2 = Tuple[float, float]

# Default root-finding tolerance shared by scan-line and marching-squares paths.
DEFAULT_TOL = 1e-9


class CurvePoint(NamedTuple):
    """A traced point on the Central Finite Curve, lifted to 3D."""

    u: float
    v: float
    x: float
    y: float
    z: float
    residual: float  # |R(u, v)| at the root (should be ~0)


class ColumnResult(NamedTuple):
    """Outcome of scanning a single ``u``-column for roots of ``R(u, .)``."""

    u: float
    roots: List[CurvePoint]
    has_root: bool


class Segment(NamedTuple):
    """A marching-squares contour segment between two refined ``(u, v)`` points."""

    p0: Point2
    p1: Point2


# ---------------------------------------------------------------------------
# Lifting
# ---------------------------------------------------------------------------

def lift(u: float, v: float) -> CurvePoint:
    """Lift a parameter-space root ``(u, v)`` to a 3D :class:`CurvePoint`."""
    x, y, z = mobius_surface(u, v)
    return CurvePoint(u=u, v=v, x=x, y=y, z=z, residual=abs(rickness(u, v)))


# ---------------------------------------------------------------------------
# Scan-line bisection path
# ---------------------------------------------------------------------------

def find_roots_in_v(
    u: float, n_samples: int = 200, tol: float = DEFAULT_TOL
) -> List[float]:
    """Return all ``v``-roots of ``R(u, .)`` in ``[V_MIN, V_MAX]`` via sign changes.

    Uses :func:`commons.core.numerics.find_sign_changes` to bracket each crossing
    and :func:`commons.core.numerics.bisection` to refine it.
    """
    if n_samples < 2:
        raise ValueError("n_samples must be >= 2")

    def f(v: float) -> float:
        return rickness(u, v)

    brackets = find_sign_changes(f, V_MIN, V_MAX, n_samples - 1)
    return [bisection(f, lo, hi, tol=tol) for lo, hi in brackets]


def trace_columns(
    n_u: int = 120, n_v_samples: int = 200, tol: float = DEFAULT_TOL
) -> List[ColumnResult]:
    """Trace ``R^{-1}(0)`` column-by-column across the ``u``-domain.

    Returns one :class:`ColumnResult` per sampled ``u`` (ordered), each holding the
    lifted 3D root points in that column (possibly empty).
    """
    if n_u < 2:
        raise ValueError("n_u must be >= 2")
    step = TWO_PI / (n_u - 1)
    results: List[ColumnResult] = []
    for i in range(n_u):
        u = i * step
        roots_v = find_roots_in_v(u, n_samples=n_v_samples, tol=tol)
        points = [lift(u, v) for v in roots_v]
        results.append(ColumnResult(u=u, roots=points, has_root=bool(points)))
    return results


def flatten_columns(results: List[ColumnResult]) -> List[CurvePoint]:
    """Collect all traced points from per-column results into one ordered list."""
    return [p for col in results for p in col.roots]


# ---------------------------------------------------------------------------
# Marching-squares path
# ---------------------------------------------------------------------------

def _linspace(a: float, b: float, n: int) -> List[float]:
    if n <= 1:
        return [a]
    step = (b - a) / (n - 1)
    return [a + i * step for i in range(n)]


def _refine_edge(a: Point2, b: Point2, tol: float) -> Point2:
    """Refine the ``R = 0`` crossing on the segment ``a -> b`` (opposite signs)."""
    au, av = a
    bu, bv = b

    def g(t: float) -> float:
        return rickness(au + t * (bu - au), av + t * (bv - av))

    t = bisection(g, 0.0, 1.0, tol=tol)
    return (au + t * (bu - au), av + t * (bv - av))


# Marching-squares case table: corner bit k set when R(corner_k) >= 0, corners
# ordered c0=(i,j), c1=(i+1,j), c2=(i+1,j+1), c3=(i,j+1); edges 0=bottom,
# 1=right, 2=top, 3=left. Each entry lists the edge pairs to connect.
_CASE_EDGES: Dict[int, List[Tuple[int, int]]] = {
    0: [],
    1: [(3, 0)],
    2: [(0, 1)],
    3: [(3, 1)],
    4: [(1, 2)],
    6: [(0, 2)],
    7: [(3, 2)],
    8: [(2, 3)],
    9: [(2, 0)],
    11: [(2, 1)],
    12: [(1, 3)],
    13: [(1, 0)],
    14: [(0, 3)],
    15: [],
    # 5 and 10 are the ambiguous saddle cases, resolved at runtime.
}


def march_zero_segments(
    field: Callable[[float, float], float] = rickness,
    n_u: int = 60,
    n_v: int = 25,
    u_min: float = 0.0,
    u_max: float = TWO_PI,
    v_min: float = V_MIN,
    v_max: float = V_MAX,
    tol: float = DEFAULT_TOL,
) -> List[Segment]:
    """Extract ``field = 0`` contour segments over the ``(u, v)`` grid.

    Classic 16-case marching squares; ambiguous saddle cells (5, 10) use the
    bilinear asymptotic decider. Every edge crossing is refined by bisection to
    ``tol`` so each emitted vertex satisfies ``|field| < tol``.
    """
    us = _linspace(u_min, u_max, n_u)
    vs = _linspace(v_min, v_max, n_v)
    grid = [[field(u, v) for u in us] for v in vs]  # grid[j][i]

    segments: List[Segment] = []
    for j in range(n_v - 1):
        for i in range(n_u - 1):
            f00 = grid[j][i]        # c0 (u_i,   v_j)
            f10 = grid[j][i + 1]    # c1 (u_i+1, v_j)
            f11 = grid[j + 1][i + 1]  # c2 (u_i+1, v_j+1)
            f01 = grid[j + 1][i]    # c3 (u_i,   v_j+1)

            case = (
                (1 if f00 >= 0.0 else 0)
                | (2 if f10 >= 0.0 else 0)
                | (4 if f11 >= 0.0 else 0)
                | (8 if f01 >= 0.0 else 0)
            )
            if case in (0, 15):
                continue

            c0 = (us[i], vs[j])
            c1 = (us[i + 1], vs[j])
            c2 = (us[i + 1], vs[j + 1])
            c3 = (us[i], vs[j + 1])
            edge_ends = {0: (c0, c1), 1: (c1, c2), 2: (c2, c3), 3: (c3, c0)}

            def crossing(edge_id: int) -> Point2:
                a, b = edge_ends[edge_id]
                return _refine_edge(a, b, tol)

            if case in (5, 10):
                pairs = _resolve_saddle(case, f00, f10, f11, f01)
            else:
                pairs = _CASE_EDGES[case]

            for e_a, e_b in pairs:
                segments.append(Segment(p0=crossing(e_a), p1=crossing(e_b)))
    return segments


def _resolve_saddle(
    case: int, f00: float, f10: float, f11: float, f01: float
) -> List[Tuple[int, int]]:
    """Resolve ambiguous marching-squares saddles (cases 5, 10)."""
    denom = f00 + f11 - f10 - f01
    # Bilinear saddle value; fall back to arithmetic mean if denom ~ 0.
    if denom == 0.0:
        center = 0.25 * (f00 + f10 + f11 + f01)
    else:
        center = (f00 * f11 - f10 * f01) / denom
    positive_corner_sign = f00 >= 0.0 if case == 5 else f10 >= 0.0
    center_matches_positive = (center >= 0.0) == positive_corner_sign
    if case == 5:
        # Positive corners c0, c2. If the centre matches them, the positive
        # region is connected through the middle -> isolate the negatives.
        if center_matches_positive:
            return [(0, 1), (2, 3)]
        return [(3, 0), (1, 2)]
    # case == 10: positive corners c1, c3.
    if center_matches_positive:
        return [(3, 0), (1, 2)]
    return [(0, 1), (2, 3)]


def _seam_key(pt: Point2, snap: float) -> Tuple[int, int]:
    """Hash a point after Mobius seam canonicalization ``r(2*pi, v) = r(0, -v)``."""
    cu, cv = mobius_seam_wrap(pt[0], pt[1])
    return (round(cu / snap), round(cv / snap))


def stitch_segments(
    segments: List[Segment], snap: Optional[float] = None
) -> List[List[Point2]]:
    """Link contour segments into ordered polylines, seam-stitched across the flip.

    Endpoints are hashed after :func:`mobius_seam_wrap`, so a crossing on the
    ``u = 2*pi`` boundary at ``v`` fuses with its partner on ``u = 0`` at ``-v`` and
    the traced curve closes across the seam.
    """
    n = len(segments)
    if n == 0:
        return []
    if snap is None:
        snap = 1e-6

    k0 = [_seam_key(s.p0, snap) for s in segments]
    k1 = [_seam_key(s.p1, snap) for s in segments]
    incident: Dict[Tuple[int, int], List[int]] = defaultdict(list)
    for idx in range(n):
        incident[k0[idx]].append(idx)
        incident[k1[idx]].append(idx)

    used = [False] * n

    def next_unused(key: Tuple[int, int]) -> Optional[int]:
        for idx in incident[key]:
            if not used[idx]:
                return idx
        return None

    polylines: List[List[Point2]] = []
    # Walk arcs (low-degree endpoints) first, then any remaining loops.
    start_order = sorted(incident.keys(), key=lambda key: len(incident[key]))
    for start_key in start_order:
        while next_unused(start_key) is not None:
            poly: List[Point2] = []
            key_cur = start_key
            first = True
            while True:
                idx = next_unused(key_cur)
                if idx is None:
                    break
                used[idx] = True
                if k0[idx] == key_cur:
                    p_from, p_to, key_next = segments[idx].p0, segments[idx].p1, k1[idx]
                else:
                    p_from, p_to, key_next = segments[idx].p1, segments[idx].p0, k0[idx]
                if first:
                    poly.append(p_from)
                    first = False
                poly.append(p_to)
                key_cur = key_next
                if key_cur == start_key:  # closed loop
                    break
            if len(poly) >= 2:
                polylines.append(poly)
    return polylines


def segment_points(segments: List[Segment], snap: float = 1e-6) -> List[CurvePoint]:
    """Deduplicate segment endpoints (seam-aware) and lift them to 3D."""
    seen: Dict[Tuple[int, int], CurvePoint] = {}
    for seg in segments:
        for pt in (seg.p0, seg.p1):
            key = _seam_key(pt, snap)
            if key not in seen:
                seen[key] = lift(pt[0], pt[1])
    return list(seen.values())


def march_mobius_curve(
    n_u: int = 60, n_v: int = 25, tol: float = DEFAULT_TOL
) -> Tuple[List[Segment], List[List[Point2]], List[CurvePoint]]:
    """Full marching-squares pipeline: segments, seam-stitched polylines, 3D points."""
    segments = march_zero_segments(rickness, n_u=n_u, n_v=n_v, tol=tol)
    snap = min(TWO_PI / (n_u - 1), (V_MAX - V_MIN) / (n_v - 1)) / 4.0
    polylines = stitch_segments(segments, snap=snap)
    points = segment_points(segments, snap=snap)
    return segments, polylines, points


# ---------------------------------------------------------------------------
# Verification
# ---------------------------------------------------------------------------

def verify_curve(
    points: List[CurvePoint], r_tol: float = 1e-6, k_rick_tol: float = 1e-6
) -> None:
    """Assert every traced point is a genuine zero of ``R`` (hence of ``K_Rick``).

    Raises :class:`AssertionError` if any point violates ``|R| < r_tol`` or
    ``|K_Rick| < k_rick_tol``.
    """
    for p in points:
        assert p.residual < r_tol, f"|R| too large at u={p.u}, v={p.v}: {p.residual}"
        kr = abs(k_rick(p.u, p.v))
        assert kr < k_rick_tol, f"|K_Rick| too large at u={p.u}, v={p.v}: {kr}"


# ---------------------------------------------------------------------------
# Torus zero circles
# ---------------------------------------------------------------------------

def trace_torus_zero_circles(
    n_theta: int = 400, tol: float = DEFAULT_TOL
) -> List[float]:
    """Locate ``theta`` where the torus closed-form ``K`` changes sign (K = 0 circles).

    Returns the refined ``theta`` values in ``[0, 2*pi)``; analytically ``pi/2`` and
    ``3*pi/2``.
    """
    if n_theta < 2:
        raise ValueError("n_theta must be >= 2")

    def f(theta: float) -> float:
        return gaussian_curvature_closed(theta)

    brackets = find_sign_changes(f, 0.0, TWO_PI, n_theta)
    return [bisection(f, lo, hi, tol=tol) for lo, hi in brackets]
