"""Tests for the compactified latent space (calabi_yau_latent.core.latent).

Covers angle normalisation (into [0, 2*pi) without mutating the caller's input),
encode/decode geometry, the decode embedding length k + 2m, the atan2 round-trip,
and fail-fast validation. Stdlib-only -> RUNS on both interpreters.
"""

from __future__ import annotations

import math

import pytest

from calabi_yau_latent.core.latent import (
    TWO_PI,
    CompactifiedLatentSpace,
    LatentPoint,
)


def test_angles_wrapped_into_unit_circle_range() -> None:
    p = LatentPoint(extended=(1.0,), angles=(TWO_PI + 0.5, -0.25))
    assert all(0.0 <= a < TWO_PI for a in p.angles)
    assert abs(p.angles[0] - 0.5) < 1e-9


def test_construction_does_not_mutate_caller_input() -> None:
    src = (TWO_PI + 0.5, -0.25)
    LatentPoint(extended=(1.0,), angles=src)
    assert src == (TWO_PI + 0.5, -0.25)  # untouched


def test_decode_embedding_length_is_k_plus_2m() -> None:
    space = CompactifiedLatentSpace(k=2, radii=(0.1, 0.2))
    pt = space.encode([0.3, -1.2, 5.9, 0.1])
    assert len(space.decode(pt)) == space.k + 2 * space.m


def test_decode_embeds_each_circle_as_r_cos_r_sin() -> None:
    space = CompactifiedLatentSpace(k=0, radii=(0.5,))
    pt = LatentPoint(extended=(), angles=(0.0,))
    emb = space.decode(pt)
    assert emb == pytest.approx((0.5, 0.0))


def test_angle_roundtrip_ok() -> None:
    space = CompactifiedLatentSpace(k=2, radii=(0.1, 0.2))
    pt = space.encode([0.3, -1.2, 5.9, 0.1])
    assert space.roundtrip_angles_ok(pt)


def test_encode_pads_missing_phases_with_zero() -> None:
    space = CompactifiedLatentSpace(k=1, radii=(0.1, 0.1))
    pt = space.encode([2.0, 1.0])  # only one phase supplied for two circles
    assert pt.angles[1] == pytest.approx(0.0)


def test_encode_rejects_too_short_raw() -> None:
    space = CompactifiedLatentSpace(k=3, radii=(0.1,))
    with pytest.raises(ValueError):
        space.encode([1.0, 2.0])


def test_space_rejects_nonpositive_radius() -> None:
    with pytest.raises(ValueError):
        CompactifiedLatentSpace(k=1, radii=(0.0,))


def test_latent_point_is_frozen() -> None:
    pt = LatentPoint(extended=(1.0,), angles=(0.1,))
    with pytest.raises(Exception):
        pt.extended = (2.0,)  # type: ignore[misc]


def test_m_property_counts_circles() -> None:
    assert CompactifiedLatentSpace(k=2, radii=(0.1, 0.2, 0.3)).m == 3
    assert abs(math.tau - TWO_PI) < 1e-12
