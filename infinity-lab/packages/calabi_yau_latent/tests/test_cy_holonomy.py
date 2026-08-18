"""Tests for the holonomy-flavoured transport cartoon (calabi_yau_latent.core.holonomy).

The measured net rotation after one loop must match the closed form
``(curvature * 2*pi) mod 2*pi``. Also checks the transported vector keeps unit
length (a pure rotation) and fail-fast validation. This is an ANALOGY only, not
real Calabi-Yau special holonomy. Stdlib-only -> RUNS on both interpreters.
"""

from __future__ import annotations

import math

import pytest

from calabi_yau_latent.core.holonomy import (
    holonomy_angle,
    loop_trace,
    transport_around_loop,
)


def test_measured_holonomy_matches_closed_form() -> None:
    _, measured = transport_around_loop((1.0, 0.0), curvature=0.15, steps=720)
    assert abs(measured - holonomy_angle(0.15)) < 1e-6


def test_holonomy_closed_form_value() -> None:
    assert holonomy_angle(0.15) == pytest.approx((0.15 * 2.0 * math.pi) % (2.0 * math.pi))


def test_transport_preserves_vector_length() -> None:
    final, _ = transport_around_loop((1.0, 0.0), curvature=0.15, steps=720)
    assert math.hypot(*final) == pytest.approx(1.0, abs=1e-9)


def test_zero_curvature_gives_trivial_holonomy() -> None:
    final, measured = transport_around_loop((1.0, 0.0), curvature=0.0, steps=360)
    assert measured == pytest.approx(0.0)
    assert final == pytest.approx((1.0, 0.0))


def test_loop_trace_length_and_start() -> None:
    trace = loop_trace((1.0, 0.0), curvature=0.15, samples=8)
    assert len(trace) == 8
    assert trace[0][0] == pytest.approx(0.0)
    assert trace[0][1] == pytest.approx((1.0, 0.0))


def test_invalid_step_and_sample_counts_raise() -> None:
    with pytest.raises(ValueError):
        transport_around_loop((1.0, 0.0), steps=0)
    with pytest.raises(ValueError):
        loop_trace((1.0, 0.0), samples=0)
