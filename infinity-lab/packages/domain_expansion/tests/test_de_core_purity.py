"""Guard: domain_expansion.core must stay pure (stdlib + commons.core only).

Statically scans every module under ``domain_expansion/core`` and asserts none of
them import an adapter layer (render / cli / viz) or hard-import a scientific
optional dependency (numpy / matplotlib). It also asserts, dynamically in a FRESH
subprocess, that importing the core does not pull numpy into ``sys.modules``.
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys

import domain_expansion.core as core_pkg

_CORE_DIR = pathlib.Path(core_pkg.__file__).parent
_FORBIDDEN_SUBSTRINGS = (
    "import numpy",
    "import matplotlib",
    "from commons.adapters",
    "import commons.adapters",
    "domain_expansion.adapters",
    "domain_expansion.accel",
)

_EXPECTED = {
    "linalg.py",
    "domain.py",
    "clash.py",
    "scenarios.py",
}


def _core_files() -> list[pathlib.Path]:
    return sorted(p for p in _CORE_DIR.glob("*.py"))


def test_expected_core_modules_present() -> None:
    names = {p.name for p in _core_files()}
    assert _EXPECTED <= names


def test_core_imports_only_stdlib_and_commons_core() -> None:
    offenders: list[str] = []
    for path in _core_files():
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            for bad in _FORBIDDEN_SUBSTRINGS:
                if bad in stripped and stripped.startswith(("import", "from")):
                    offenders.append(f"{path.name}: {stripped}")
    assert offenders == [], f"core purity violated: {offenders}"


def test_importing_core_does_not_load_numpy() -> None:
    # Verified in a FRESH subprocess so the check is robust even when another test
    # in this session (e.g. the numpy accel parity tests) has already pulled numpy
    # into *this* process's sys.modules.
    script = (
        "import sys; import domain_expansion.core;"
        " sys.exit(1 if ('numpy' in sys.modules or 'matplotlib' in sys.modules)"
        " else 0)"
    )
    env = dict(os.environ, PYTHONPATH=os.pathsep.join(p for p in sys.path if p))
    result = subprocess.run(
        [sys.executable, "-c", script], env=env, capture_output=True, text=True
    )
    assert result.returncode == 0, (
        "importing domain_expansion.core pulled numpy/matplotlib into sys.modules; "
        f"stderr={result.stderr!r}"
    )
