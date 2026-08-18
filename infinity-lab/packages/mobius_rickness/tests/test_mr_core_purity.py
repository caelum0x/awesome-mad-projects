"""Guard: mobius_rickness.core must stay pure (stdlib + commons.core only).

Statically scans every module under ``mobius_rickness/core`` and asserts none of
them import adapters (``commons.adapters``) or hard-import numpy/matplotlib, and
that importing the core package does not pull numpy into ``sys.modules``.
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys

import mobius_rickness.core as core_pkg

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
        "geometry.py",
        "mobius.py",
        "torus.py",
        "rickness.py",
        "field.py",
        "tracer.py",
    } <= names


def test_core_does_not_import_adapters_or_sci_deps() -> None:
    offenders: list[str] = []
    for path in _core_source_files():
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            for bad in _FORBIDDEN_SUBSTRINGS:
                if stripped.startswith(bad):
                    offenders.append(f"{path.name}: {stripped}")
    assert offenders == [], f"core purity violated: {offenders}"


def test_importing_core_does_not_pull_numpy() -> None:
    # Core is stdlib + commons.core only; numpy must not be imported as a side
    # effect. Checked in a FRESH subprocess so the guarantee holds even when
    # another test in this session has already imported numpy into *this*
    # process's sys.modules (e.g. numpy-backed parity tests elsewhere).
    script = (
        "import sys; import mobius_rickness.core;"
        " sys.exit(1 if ('numpy' in sys.modules or 'matplotlib' in sys.modules)"
        " else 0)"
    )
    env = dict(os.environ, PYTHONPATH=os.pathsep.join(p for p in sys.path if p))
    result = subprocess.run(
        [sys.executable, "-c", script], env=env, capture_output=True, text=True
    )
    assert result.returncode == 0, (
        "importing mobius_rickness.core pulled numpy/matplotlib into sys.modules; "
        f"stderr={result.stderr!r}"
    )
