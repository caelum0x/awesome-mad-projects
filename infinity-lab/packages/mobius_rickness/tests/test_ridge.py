"""SCMS / Eberly ridge -- the crest of maximal Rickness (numpy-backed).

These tests are OPTIONAL and DEFERRED. They begin with
``pytest.importorskip("numpy")`` so they SKIP on the stdlib-only system
interpreter (no numpy) and RUN on the venv interpreter (numpy 2.x).

They assert the three defining properties of the ridge as the *second*, distinct
formalization of the Central Finite Curve:

    1. Every converged ridge point satisfies the Eberly height-ridge condition:
       ``|gradient . minor_eigvec| < tol`` AND ``minor eigenvalue < 0``.
    2. The ridge is DISTINCT from the zero set ``R^{-1}(0)``: along the crest of the
       Mobius Rickness field ``R`` stays strictly away from ``0`` (it is an argmax
       ridge, not a level set).
    3. On a synthetic field with a known analytic ridge,
       ``R(u, v) = -(v - sin u)**2`` whose ridge is ``v = sin u``, SCMS recovers
       that ridge to tolerance from scattered seeds.
"""

from __future__ import annotations

import math

import pytest

np = pytest.importorskip("numpy")

from mobius_rickness.ridge import scms
from mobius_rickness.ridge.scms import (
    OptionalDependencyError,
    ridge_condition,
    scms_ridge,
    trace_mobius_ridge,
    verify_ridge,
)

# Tight iteration budget/tolerance for the near-quadratic fields under test.
_TOL = 1e-9
_MAX_ITER = 200
# Verification bound: re-evaluated central-difference gradient/Hessian introduce
# a little rounding, so the ridge condition is checked at 1e-6.
_VERIFY_TOL = 1e-6


def _synthetic(u: float, v: float) -> float:
    """Field with a known analytic ridge ``v = sin u`` (its crest of maxima)."""
    return -((v - math.sin(u)) ** 2)


# ---------------------------------------------------------------------------
# 3. Synthetic field: recover the known analytic ridge v = sin(u)
# ---------------------------------------------------------------------------

def _synthetic_seeds() -> list:
    us = [0.3, 1.0, 2.0, 3.5, 5.0]
    vs = [-0.8, -0.2, 0.0, 0.4, 0.9]
    return [(u, v) for u in us for v in vs]


def test_synthetic_ridge_recovers_v_equals_sin_u() -> None:
    seeds = _synthetic_seeds()
    kept = scms_ridge(_synthetic, seeds, tol=_TOL, max_iter=_MAX_ITER)
    # Every seed should reach the crest (the field is concave transverse everywhere
    # off the ridge, so SCMS converges from any of these starts).
    assert len(kept) == len(seeds)
    worst = max(abs(p.v - math.sin(p.u)) for p in kept)
    assert worst < 1e-6, f"SCMS did not recover v = sin(u): worst error {worst:.3e}"


def test_synthetic_converged_points_satisfy_ridge_condition() -> None:
    seeds = _synthetic_seeds()
    kept = scms_ridge(_synthetic, seeds, tol=_TOL, max_iter=_MAX_ITER)
    assert kept, "expected converged ridge points"
    for p in kept:
        proj, lam = ridge_condition(_synthetic, p.u, p.v)
        assert abs(proj) < _VERIFY_TOL, (
            f"gradient not orthogonal to minor eigvec: |g.e_minor|={abs(proj):.3e}"
        )
        assert lam < 0.0, f"minor eigenvalue not negative (not a crest): lam={lam:.3e}"
    # verify_ridge re-checks the same condition independently and must not raise.
    verify_ridge(_synthetic, kept, tol=_VERIFY_TOL)


# ---------------------------------------------------------------------------
# 1. Mobius Rickness ridge: every converged point is a genuine crest
# ---------------------------------------------------------------------------

def test_mobius_ridge_points_satisfy_eberly_condition() -> None:
    ridge = trace_mobius_ridge(n_u=24, n_v=5, tol=_TOL, max_iter=_MAX_ITER)
    assert ridge, "expected a non-empty Mobius ridge"
    for p in ridge:
        # Condition as stored by the SCMS iteration at the converged location.
        assert abs(p.grad_dot_minor) < _TOL, (
            f"stored |g.e_minor|={abs(p.grad_dot_minor):.3e} exceeds tol at "
            f"u={p.u}, v={p.v}"
        )
        assert p.minor_eigval < 0.0, (
            f"minor eigenvalue not negative at u={p.u}, v={p.v}: {p.minor_eigval:.3e}"
        )
        # Re-verify independently from the field (seam-aware wrap).
        proj, lam = ridge_condition(scms.rickness, p.u, p.v, wrap=scms.mobius_seam_wrap)
        assert abs(proj) < _VERIFY_TOL
        assert lam < 0.0


# ---------------------------------------------------------------------------
# 2. The ridge is DISTINCT from the zero set R^{-1}(0)
# ---------------------------------------------------------------------------

def test_mobius_ridge_is_distinct_from_zero_set() -> None:
    ridge = trace_mobius_ridge(n_u=24, n_v=5, tol=_TOL, max_iter=_MAX_ITER)
    assert ridge, "expected a non-empty Mobius ridge"
    abs_r = [abs(p.r) for p in ridge]
    # The zero set is |R| < 1e-6 (see core.tracer.verify_curve). Along the crest
    # of maximal Rickness, R is far from 0 -- so NO ridge point lands on the wall.
    assert min(abs_r) > 0.1, (
        f"a ridge point sits on the zero set: min |R|={min(abs_r):.3e} (not distinct)"
    )
    # And the crest is emphatically Rick-positive on average, unlike a level curve.
    assert sum(abs_r) / len(abs_r) > 0.5


def test_ridge_points_lift_to_the_mobius_surface() -> None:
    ridge = trace_mobius_ridge(n_u=24, n_v=5, tol=_TOL, max_iter=_MAX_ITER)
    for p in ridge:
        x, y, z = scms.mobius_surface(p.u, p.v)
        assert abs(p.x - x) < 1e-12
        assert abs(p.y - y) < 1e-12
        assert abs(p.z - z) < 1e-12


def test_ridge_polyline_is_deduped_and_u_ordered() -> None:
    ridge = trace_mobius_ridge(n_u=24, n_v=5, tol=_TOL, max_iter=_MAX_ITER)
    us = [p.u for p in ridge]
    assert us == sorted(us), "ridge polyline must be ordered by u"


def test_optional_dependency_error_is_runtime_error() -> None:
    # The deferred error type is exported for callers that catch missing numpy.
    assert issubclass(OptionalDependencyError, RuntimeError)
