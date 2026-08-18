"""Tests for commons.core.optional (capability detection / safe import)."""

from __future__ import annotations

import pytest

from commons.core import optional


def test_try_import_returns_module_for_stdlib() -> None:
    mod = optional.try_import("math")
    assert mod is not None
    assert mod.sqrt(4.0) == 2.0


def test_try_import_returns_none_for_missing() -> None:
    assert optional.try_import("definitely_not_a_real_module_xyz") is None


def test_try_import_rejects_non_string() -> None:
    with pytest.raises(TypeError):
        optional.try_import(123)  # type: ignore[arg-type]


def test_try_import_rejects_empty() -> None:
    with pytest.raises(ValueError):
        optional.try_import("")


def test_has_numpy_matches_try_import() -> None:
    assert optional.has_numpy() == (optional.try_import("numpy") is not None)


def test_has_matplotlib_matches_try_import() -> None:
    assert optional.has_matplotlib() == (
        optional.try_import("matplotlib") is not None
    )


def test_capabilities_are_bool() -> None:
    assert isinstance(optional.has_numpy(), bool)
    assert isinstance(optional.has_matplotlib(), bool)
