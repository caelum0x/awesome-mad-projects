"""domain_expansion.core -- the pure constraint-solver engine (stdlib only).

Every module here imports ONLY the standard library (plus its sibling core
modules); nothing imports an adapter (render / cli / viz) or hard-imports
numpy/matplotlib, so the core stays deterministic and dependency free. Optional
numpy fast-paths live in :mod:`domain_expansion.accel`; ASCII / matplotlib
rendering lives in :mod:`domain_expansion.adapters`.

Concept: a Domain Expansion is a closed region enforcing many simultaneous
constraints (a discretized Laplace boundary-value problem). Its 'power' is the
stability / well-posedness of that constraint system.

  * :mod:`~domain_expansion.core.linalg`    -- Gaussian elimination + power iteration.
  * :mod:`~domain_expansion.core.domain`     -- the Domain model + both solvers + metrics.
  * :mod:`~domain_expansion.core.clash`      -- two-domain clash and region overwrite.
  * :mod:`~domain_expansion.core.scenarios`  -- the canonical refined/crude/void domains.
"""

from __future__ import annotations

from domain_expansion.core.clash import (
    ClashResult,
    clash,
    contested_region,
)
from domain_expansion.core.domain import (
    Cell,
    Domain,
    Grid,
    SolveResult,
    direct_solve_domain,
    max_grid_diff,
    rigidity,
    solve_domain,
)
from domain_expansion.core.scenarios import (
    make_crude_domain,
    make_refined_domain,
    make_void_domain,
)

__all__ = [
    # domain
    "Cell",
    "Grid",
    "Domain",
    "SolveResult",
    "solve_domain",
    "direct_solve_domain",
    "max_grid_diff",
    "rigidity",
    # clash
    "ClashResult",
    "clash",
    "contested_region",
    # scenarios
    "make_refined_domain",
    "make_crude_domain",
    "make_void_domain",
]
