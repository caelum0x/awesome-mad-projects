"""Capability detection and safe optional imports (stdlib only).

The core of every package must run with the standard library alone. Heavy,
optional scientific dependencies (numpy, matplotlib) are *never* hard-imported
at module top level. Instead call :func:`try_import` to obtain the module or
``None`` and branch on the result, or use the boolean capability probes
:func:`has_numpy` / :func:`has_matplotlib`.

Error behaviour:
    * :func:`try_import` never raises for a missing module; any ``ImportError``
      (or broader import-time failure) is swallowed and ``None`` is returned.
    * A non-string ``name`` raises :class:`TypeError` (a programming error, not
      a missing-dependency condition).
"""

from __future__ import annotations

import importlib
from types import ModuleType
from typing import Optional


def try_import(name: str) -> Optional[ModuleType]:
    """Import ``name`` and return the module, or ``None`` if it is unavailable.

    Never raises for a genuinely missing/broken dependency: ``ImportError`` and
    any other exception raised *during import* are caught and mapped to
    ``None``. A non-string ``name`` still raises :class:`TypeError`.
    """
    if not isinstance(name, str):
        raise TypeError(f"module name must be str, got {type(name).__name__}")
    if not name:
        raise ValueError("module name must be non-empty")
    try:
        return importlib.import_module(name)
    except Exception:  # noqa: BLE001 - any import-time failure means "unavailable"
        return None


def has_numpy() -> bool:
    """Return ``True`` iff ``numpy`` can be imported in this environment."""
    return try_import("numpy") is not None


def has_matplotlib() -> bool:
    """Return ``True`` iff ``matplotlib`` can be imported in this environment."""
    return try_import("matplotlib") is not None
