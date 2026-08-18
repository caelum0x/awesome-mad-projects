"""Canonical demo domains -- one source of truth for CLI, demo, and tests.

Three archetypes, each a pure :class:`~domain_expansion.core.domain.Domain`:

  * :func:`make_refined_domain` -- a clean, strongly-coupled Laplace domain
    (hot left wall, cold right wall). Low residual, high rigidity.
  * :func:`make_crude_domain`   -- a leaky, weakly-coupled, noisy domain. Its
    constraints are unstable, so its rigidity is far lower.
  * :func:`make_void_domain`    -- Unlimited Void: a single interior cell pinned
    with an enormous weight (infinite information density) that dominates the
    operator's rigidity even though it fights the smooth Laplace field.

Pure module: standard library only (plus :mod:`domain_expansion.core.domain`).
"""

from __future__ import annotations

from domain_expansion.core.domain import Domain

_GRID = 7


def make_refined_domain() -> Domain:
    """A clean, strongly-coupled Laplace domain: hot left edge, cold right."""
    nx = ny = _GRID

    def g(i: int, j: int) -> float:
        if i == 0:
            return 100.0  # left wall hot (the guaranteed 'sure-hit' condition)
        if i == nx - 1:
            return 0.0  # right wall cold
        return 20.0  # top/bottom moderate

    return Domain(name="Refined Domain", nx=nx, ny=ny, boundary=g,
                  coupling=1.0, noise=0.0)


def make_crude_domain() -> Domain:
    """A leaky, weakly-coupled, noisy domain: unstable constraints."""
    nx = ny = _GRID

    def g(i: int, j: int) -> float:
        if i == 0:
            return 60.0
        if i == nx - 1:
            return 40.0
        return 50.0

    return Domain(name="Crude Domain", nx=nx, ny=ny, boundary=g,
                  coupling=0.45, noise=8.0)


def make_void_domain() -> Domain:
    """Unlimited Void: an interior cell pinned with enormous weight."""
    nx = ny = _GRID

    def g(i: int, j: int) -> float:
        return 10.0 if i in (0, nx - 1) else 30.0

    void = {(3, 3): 999.0}  # infinite information density at the center
    return Domain(name="Unlimited Void", nx=nx, ny=ny, boundary=g,
                  coupling=1.0, noise=0.0, void_cells=void, void_weight=1e6)
