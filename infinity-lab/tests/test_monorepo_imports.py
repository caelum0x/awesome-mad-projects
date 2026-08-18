"""Repo-level wiring test: all three packages import with zero install.

Confirms the ``pythonpath`` pytest setting exposes ``commons``, ``gojo_infinity``
and ``mobius_rickness`` from the repo root without an editable install.
"""

from __future__ import annotations


def test_import_commons_public_api() -> None:
    import commons

    assert callable(commons.adaptive_integral)
    assert callable(commons.bisection)
    assert callable(commons.render_heatmap)
    assert commons.__version__


def test_import_gojo_infinity_marker() -> None:
    import gojo_infinity

    assert hasattr(gojo_infinity, "__version__")


def test_import_mobius_rickness_marker() -> None:
    import mobius_rickness

    assert hasattr(mobius_rickness, "__version__")
