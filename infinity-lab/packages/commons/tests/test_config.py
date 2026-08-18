"""Tests for commons.core.config (immutable configuration)."""

from __future__ import annotations

import dataclasses

import pytest

from commons.core.config import FrozenConfig, immutable_replace


@dataclasses.dataclass(frozen=True)
class SampleConfig(FrozenConfig):
    n_u: int = 49
    n_v: int = 17
    label: str = "grid"


def test_defaults() -> None:
    cfg = SampleConfig()
    assert cfg.n_u == 49 and cfg.n_v == 17 and cfg.label == "grid"


def test_frozen_cannot_mutate() -> None:
    cfg = SampleConfig()
    with pytest.raises(dataclasses.FrozenInstanceError):
        cfg.n_u = 100  # type: ignore[misc]


def test_with_changes_returns_new_object() -> None:
    cfg = SampleConfig()
    finer = cfg.with_changes(n_u=97)
    assert finer.n_u == 97
    assert cfg.n_u == 49  # original untouched
    assert finer is not cfg


def test_with_changes_unknown_field_raises() -> None:
    with pytest.raises(TypeError):
        SampleConfig().with_changes(does_not_exist=1)


def test_to_dict() -> None:
    assert SampleConfig().to_dict() == {"n_u": 49, "n_v": 17, "label": "grid"}


def test_immutable_replace_free_function() -> None:
    cfg = SampleConfig()
    out = immutable_replace(cfg, n_v=33)
    assert out.n_v == 33
    assert cfg.n_v == 17


def test_immutable_replace_rejects_non_dataclass() -> None:
    with pytest.raises(TypeError):
        immutable_replace(object(), x=1)


def test_value_equality_and_hash() -> None:
    assert SampleConfig() == SampleConfig()
    assert hash(SampleConfig()) == hash(SampleConfig())
