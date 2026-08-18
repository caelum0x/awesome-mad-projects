"""domain_expansion -- a JJK Domain Expansion as a coupled constraint solver.

Inspired by *Jujutsu Kaisen*: a Domain Expansion is a closed space that enforces
a guaranteed-hit condition on everything inside it. We model that concretely as a
discretized Laplace boundary-value problem on a grid -- a large set of
simultaneous linear constraints whose unique solution is the domain's
manifestation. A domain's 'power' is the stability / well-posedness (rigidity) of
that constraint system: when two domains clash, the more refined one overwrites
the weaker one's interior, and an Unlimited Void pin dominates on raw rigidity.

The pure math lives under :mod:`domain_expansion.core` (stdlib only) and its
public API is re-exported here. Optional numpy fast-paths live in
:mod:`domain_expansion.accel`; ASCII / matplotlib rendering lives in
:mod:`domain_expansion.adapters` -- all lazily guarded.
"""

from __future__ import annotations

from domain_expansion import core
from domain_expansion.core import (
    ClashResult,
    Domain,
    SolveResult,
    clash,
    contested_region,
    direct_solve_domain,
    make_crude_domain,
    make_refined_domain,
    make_void_domain,
    max_grid_diff,
    rigidity,
    solve_domain,
)

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "core",
    # domain
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
