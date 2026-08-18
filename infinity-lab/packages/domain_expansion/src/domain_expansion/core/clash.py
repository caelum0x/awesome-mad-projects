"""Domain clash: two competing constraint systems overlapping on a region.

Two domains expand onto the same grid. Each wants its own field to hold in the
contested region. We solve both, compare their refinement (rigidity vs residual),
and the more refined / more stable domain wins: its constraints are imposed on
the contested region and the loser's field there is overwritten.

This mirrors JJK: when two Domain Expansions collide, the more refined domain
(the one whose constraints form the more stable, better-posed system) overwrites
the weaker one inside the overlap.

Pure module: standard library only (plus :mod:`domain_expansion.core.domain`).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from domain_expansion.core.domain import (
    Cell,
    Domain,
    Grid,
    SolveResult,
    solve_domain,
)


@dataclass(frozen=True)
class ClashResult:
    """The outcome of a two-domain clash."""

    winner: str
    loser: str
    winner_result: SolveResult
    loser_result: SolveResult
    reason: str
    merged_field: Grid  # loser grid with the contested region overwritten by winner


def _overwrite_region(base: Grid, winner: Grid, region: List[Cell]) -> Grid:
    """Return a new grid: ``base`` with ``region`` cells replaced by winner values."""
    out: Grid = [row[:] for row in base]
    for (i, j) in region:
        out[i][j] = winner[i][j]
    return out


def contested_region(nx: int, ny: int, margin: int = 1) -> List[Cell]:
    """Return the shared interior cells both domains fight over.

    With ``margin == 1`` this is the whole interior (everything but the border).
    Raises :class:`ValueError` for a non-positive ``margin``.
    """
    if margin < 1:
        raise ValueError("margin must be >= 1")
    return [
        (i, j)
        for i in range(margin, nx - margin)
        for j in range(margin, ny - margin)
    ]


def clash(a: Domain, b: Domain) -> ClashResult:
    """Stage a clash between domains ``a`` and ``b`` and decide the winner.

    Both grids must match in shape. Higher refinement wins; ties break by lower
    residual, then higher rigidity. The winner re-solves with the loser's field
    pre-loaded and overwrites the contested interior with its own solution, while
    the loser keeps its own boundary edges so the takeover is visible.
    """
    if a.nx != b.nx or a.ny != b.ny:
        raise ValueError("clashing domains must share the same grid shape")

    ra = solve_domain(a)
    rb = solve_domain(b)

    a_key = (ra.refinement, -ra.residual_l2, ra.rigidity)
    b_key = (rb.refinement, -rb.residual_l2, rb.rigidity)
    a_wins = a_key >= b_key

    if a_wins:
        winner, loser, wr, lr = a, b, ra, rb
    else:
        winner, loser, wr, lr = b, a, rb, ra

    region = contested_region(loser.nx, loser.ny)

    # The winner reasserts its constraints over the region the loser had claimed
    # (loser's field pre-loaded, then overwritten).
    reasserted = solve_domain(winner, field_override=lr.field)
    merged = _overwrite_region(lr.field, reasserted.field, region)

    reason = (
        f"{winner.name} is more refined: refinement={wr.refinement:.4f} "
        f"(rigidity={wr.rigidity:.3f}, residual_L2={wr.residual_l2:.3e}) vs "
        f"{loser.name} refinement={lr.refinement:.4f} "
        f"(rigidity={lr.rigidity:.3f}, residual_L2={lr.residual_l2:.3e})."
    )

    return ClashResult(
        winner=winner.name,
        loser=loser.name,
        winner_result=wr,
        loser_result=lr,
        reason=reason,
        merged_field=merged,
    )
