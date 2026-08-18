"""Guard: commons.core must not import adapters or optional scientific deps.

Statically scans the source of every module under ``commons/core`` and asserts
none of them import ``commons.adapters`` or hard-import ``numpy`` / ``matplotlib``
at module level. Optional deps may only be reached through
``commons.core.optional.try_import`` at call time.
"""

from __future__ import annotations

import pathlib

import commons.core as core_pkg

_CORE_DIR = pathlib.Path(core_pkg.__file__).parent
_FORBIDDEN_SUBSTRINGS = (
    "import commons.adapters",
    "from commons.adapters",
    "import numpy",
    "import matplotlib",
)


def _core_source_files() -> list[pathlib.Path]:
    return sorted(p for p in _CORE_DIR.glob("*.py"))


def test_core_files_present() -> None:
    names = {p.name for p in _core_source_files()}
    assert {
        "optional.py",
        "rng.py",
        "exact.py",
        "numerics.py",
        "config.py",
    } <= names


def test_core_does_not_import_adapters_or_sci_deps() -> None:
    offenders: list[str] = []
    for path in _core_source_files():
        text = path.read_text(encoding="utf-8")
        for line in text.splitlines():
            stripped = line.strip()
            for bad in _FORBIDDEN_SUBSTRINGS:
                if stripped.startswith(bad):
                    offenders.append(f"{path.name}: {stripped}")
    assert offenders == [], f"core purity violated: {offenders}"
