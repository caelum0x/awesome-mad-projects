"""Lens 4 (Topology / World-Cutting Slash) -- continuity, cut, disconnection."""

from __future__ import annotations

import math

from gojo_infinity.core import riemannian as rm
from gojo_infinity.core import topology as topo


def test_intact_factor_is_continuous_at_interior_point() -> None:
    report = topo.continuity_at(rm.conformal_factor, 0.5)
    assert report.classification is topo.Continuity.CONTINUOUS
    assert report.continuous is True


def test_continuity_check_fails_after_the_cut() -> None:
    c = 0.5
    severed = topo.make_severed_factor(c, jump=1.0)
    report = topo.continuity_at(severed, c)
    # At the cut Omega is undefined -> the continuity check FAILS.
    assert report.continuous is False
    assert report.classification is topo.Continuity.UNDEFINED


def test_synthetic_step_is_classified_as_a_jump() -> None:
    # A factor DEFINED at c but with different one-sided limits (Omega = 1 | 2)
    # is classified JUMP: the oscillation stays >= tol as h shrinks.
    c = 0.5

    def step(x: float) -> float:
        return 1.0 if x < c else 2.0

    report = topo.continuity_at(step, c)
    assert report.classification is topo.Continuity.JUMP
    assert report.continuous is False
    assert report.oscillation is not None and report.oscillation >= 1.0 - 1e-9


def test_domain_splits_into_exactly_two_components() -> None:
    x0, x1, c = 0.0, 1.0, 0.5
    assert topo.component_count(x0, x1, None) == 1
    assert topo.is_connected(x0, x1, None) is True
    comps = topo.connected_components(x0, x1, c)
    assert comps == [(0.0, 0.5), (0.5, 1.0)]
    assert topo.component_count(x0, x1, c) == 2
    assert topo.is_connected(x0, x1, c) is False


def test_points_across_the_cut_are_in_different_components() -> None:
    x0, x1, c = 0.0, 1.0, 0.5
    assert topo.same_component(x0, x1, c, 0.2, 0.4) is True
    assert topo.same_component(x0, x1, c, 0.2, 0.8) is False


def test_three_return_semantics_stay_type_distinct() -> None:
    # finite (Lens 3 below barrier), +inf (Lens 3 improper), None (Lens 4 cut)
    finite = rm.geodesic_length(0.0, 0.9)
    infinite = rm.geodesic_to_barrier(0.0)
    undefined = topo.severed_geodesic_length(0.0, 1.0, 0.5)

    assert isinstance(finite, float) and math.isfinite(finite)
    assert infinite == math.inf and math.isinf(infinite)
    assert undefined is None
    # they are mutually distinct
    assert finite != infinite
    assert undefined is not infinite
    assert undefined is not finite


def test_geodesic_is_undefined_across_cut() -> None:
    assert topo.geodesic_is_defined(0.0, 1.0, 0.5) is False
    assert topo.geodesic_is_defined(0.0, 0.4, 0.5) is True


def test_cut_crosses_no_distance() -> None:
    assert topo.cut_crosses_distance(0.5) == 0.0


def test_verdict_is_falls() -> None:
    assert topo.verdict().verdict == "Falls"
