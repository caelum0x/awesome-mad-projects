"""Lens 4 -- Topology / the World-Cutting Slash. Verdict: FALLS.

Infinity's Riemannian defence (Lens 3) works only while the conformal factor
``Omega(x)`` is CONTINUOUS across the whole space between attacker and Gojo: the
felt distance is an integral of ``Omega``, and an integral needs a connected,
continuous path.

The essay's decisive move is the "World-Cutting Slash". It crosses NO distance;
instead it introduces a cut at a point ``c in (x0, x1)`` that SEVERS the
continuity of ``Omega`` there -- ``Omega`` becomes undefined at ``c`` and
two-valued around it. Three things follow:

    (a) the continuity check FAILS at ``c`` (a jump appears; ``Omega(c)`` undefined);
    (b) the geodesic integral across the cut is UNDEFINED -- represented as
        ``None``, kept strictly type-distinct from the ``math.inf`` of Lens 3 and
        from any finite length;
    (c) the domain ``[x0, x1] \\ {c}`` is DISCONNECTED into exactly two components,
        so no single continuous stretched space remains to traverse.

Infinity is not out-run -- the space that carries it is torn. The barrier ceases
to exist. Infinity FALLS.

Continuity is tested numerically via the oscillation definition: for a
continuous ``f``, ``|f(x+h) - f(x-h)| -> 0`` as ``h -> 0``; at a jump it stays
bounded below by the jump size.

Pure core: stdlib + ``commons.core`` only.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple

from gojo_infinity.core.riemannian import X_GOJO, conformal_factor
from gojo_infinity.core.verdicts import TOPOLOGY_VERDICT, Verdict

# A metric factor is a function ``x -> Omega(x)`` that may raise if x is undefined.
MetricFactor = Callable[[float], float]


class Continuity(enum.Enum):
    """Classification of a point under the oscillation test."""

    CONTINUOUS = "continuous"
    JUMP = "jump"
    UNDEFINED = "undefined"


# ---------------------------------------------------------------------------
# Continuity check (oscillation definition)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ContinuityReport:
    """Result of a numeric continuity check at a point."""

    point: float
    classification: Continuity
    continuous: bool
    oscillation: Optional[float]  # None if the factor is undefined at/near the point
    detail: str


def _safe_eval(factor: MetricFactor, x: float) -> Optional[float]:
    """Evaluate ``factor(x)``; return ``None`` if it is undefined there."""
    try:
        return factor(x)
    except (ValueError, ZeroDivisionError):
        return None


def continuity_at(factor: MetricFactor, x: float, *,
                  hs: Tuple[float, ...] = (1e-2, 1e-3, 1e-4, 1e-5),
                  tol: float = 1e-3) -> ContinuityReport:
    """Classify continuity of ``factor`` at ``x`` via shrinking oscillations.

    * ``UNDEFINED``: ``factor(x)`` (or a neighbour) raises -> not continuous.
    * ``CONTINUOUS``: the oscillation ``|f(x+h) - f(x-h)|`` falls below ``tol``.
    * ``JUMP``: the oscillation stays ``>= tol`` as ``h`` shrinks (a jump).

    ``continuous`` is ``True`` only for the ``CONTINUOUS`` case.
    """
    if _safe_eval(factor, x) is None:
        return ContinuityReport(x, Continuity.UNDEFINED, False, None,
                                "Omega(x) undefined at the point (the cut)")

    smallest: Optional[float] = None
    for h in hs:
        left = _safe_eval(factor, x - h)
        right = _safe_eval(factor, x + h)
        if left is None or right is None:
            return ContinuityReport(x, Continuity.UNDEFINED, False, None,
                                    "Omega undefined next to the point (the cut)")
        osc = abs(right - left)
        smallest = osc if smallest is None else min(smallest, osc)

    continuous = smallest is not None and smallest < tol
    if continuous:
        return ContinuityReport(x, Continuity.CONTINUOUS, True, smallest,
                                "oscillation -> 0 (continuous)")
    return ContinuityReport(x, Continuity.JUMP, False, smallest,
                            "oscillation stays positive (jump discontinuity)")


def is_continuous_on(factor: MetricFactor, points: List[float], *,
                     tol: float = 1e-3) -> bool:
    """True iff ``factor`` passes the continuity check at every listed point."""
    return all(continuity_at(factor, p, tol=tol).continuous for p in points)


# ---------------------------------------------------------------------------
# The World-Cutting Slash: a severed conformal factor
# ---------------------------------------------------------------------------

def severed_conformal_factor(x: float, c: float, *, jump: float = 1.0,
                             x_gojo: float = X_GOJO) -> float:
    """Conformal factor torn at ``c``: undefined at ``c``, two-valued around it.

    Away from ``c`` it equals the intact
    :func:`gojo_infinity.core.riemannian.conformal_factor`, but a constant
    ``jump`` is added on the right side so the left and right limits at ``c``
    differ (the tear). Exactly at ``c`` it is UNDEFINED (raises). Requires
    ``jump > 0``.
    """
    if jump <= 0:
        raise ValueError("jump must be positive to sever continuity")
    if x == c:
        raise ValueError("Omega is undefined at the cut point c (two-valued)")
    base = conformal_factor(x, x_gojo=x_gojo)
    return base + (jump if x > c else 0.0)


def make_severed_factor(c: float, *, jump: float = 1.0,
                        x_gojo: float = X_GOJO) -> MetricFactor:
    """Return a one-argument severed factor ``x -> Omega_cut(x)``."""
    def factor(x: float) -> float:
        return severed_conformal_factor(x, c, jump=jump, x_gojo=x_gojo)
    return factor


# ---------------------------------------------------------------------------
# Geodesic across a cut is undefined (None) -- type-distinct from inf and finite
# ---------------------------------------------------------------------------

def geodesic_is_defined(x0: float, x1: float, cut: Optional[float]) -> bool:
    """False iff a cut lies on the path ``[x0, x1]`` (the integral is undefined)."""
    if x1 < x0:
        raise ValueError("require x0 <= x1")
    return not (cut is not None and x0 <= cut <= x1)


def severed_geodesic_length(x0: float, x1: float, cut: float) -> None:
    """Felt length across a severed metric: ``None`` -- UNDEFINED.

    Any path from ``x0`` to ``x1 >= cut`` must cross the undefined point ``cut``,
    so the geodesic integral cannot be evaluated. Returning ``None`` keeps the
    "undefined" outcome strictly type-distinct from Lens 3's ``math.inf``
    (divergent-but-defined) and from any finite length. Raises if no cut lies on
    the path (use :func:`gojo_infinity.core.riemannian.geodesic_length` instead).
    """
    if geodesic_is_defined(x0, x1, cut):
        raise ValueError("no cut on this path; use riemannian.geodesic_length")
    return None


def cut_crosses_distance(cut: float) -> float:
    """The slash itself crosses NO distance: it is a single point, measure ``0``.

    Returns ``0.0`` -- the cut is applied "for free" (it does not require
    traversing any felt length), which is exactly why it defeats the Riemannian
    defence that only ever charged for *distance*.
    """
    return 0.0


# ---------------------------------------------------------------------------
# The domain is disconnected by the cut
# ---------------------------------------------------------------------------

def connected_components(x0: float, x1: float,
                         cut: Optional[float]) -> List[Tuple[float, float]]:
    """Connected components of ``[x0, x1] \\ {cut}`` (immutable list of intervals).

    Removing an interior point splits the interval into two pieces
    ``[x0, cut)`` and ``(cut, x1]``; with no interior cut the interval stays a
    single connected component. Returns a fresh list (no shared mutable state).
    """
    if x1 < x0:
        raise ValueError("require x0 <= x1")
    if cut is None or not (x0 < cut < x1):
        return [(x0, x1)]
    return [(x0, cut), (cut, x1)]


def component_count(x0: float, x1: float, cut: Optional[float]) -> int:
    """Number of connected components of ``[x0, x1] \\ {cut}`` (1 intact, 2 after cut)."""
    return len(connected_components(x0, x1, cut))


def is_connected(x0: float, x1: float, cut: Optional[float]) -> bool:
    """True iff ``[x0, x1] \\ {cut}`` is a single connected component."""
    return component_count(x0, x1, cut) == 1


def same_component(x0: float, x1: float, cut: Optional[float],
                   p: float, q: float) -> bool:
    """True iff points ``p`` and ``q`` lie in the same component of ``[x0, x1] \\ {cut}``.

    After a cut at ``c``, a point left of ``c`` and a point right of ``c`` are in
    different components -- there is no continuous path between them.
    """
    for comp in connected_components(x0, x1, cut):
        lo, hi = comp
        if lo <= p <= hi and lo <= q <= hi:
            return True
    return False


# ---------------------------------------------------------------------------
# Verdict
# ---------------------------------------------------------------------------

def verdict() -> Verdict:
    """Topology verdict: FALLS -- severing continuity destroys the metric."""
    return TOPOLOGY_VERDICT
