"""Domain clash: two competing constraint systems overlapping on a region.

Two domains expand onto the same grid. Each wants its own field to hold in the
contested region. We solve both, compare their refinement (rigidity vs
residual), and the more refined / more stable domain wins: its constraints are
imposed on the contested region and the loser's field there is overwritten.

This mirrors JJK: when two Domain Expansions collide, the more refined domain
(the one whose constraints form the more stable, better-posed system) overwrites
the weaker one inside the overlap.
"""

from __future__ import annotations

from dataclasses import dataclass

from domain import Domain, SolveResult, solve_domain


@dataclass
class ClashResult:
    winner: str
    loser: str
    winner_result: SolveResult
    loser_result: SolveResult
    reason: str
    merged_field: list  # loser grid with contested region overwritten by winner


def _overwrite_region(base: list, winner: list, region: list) -> list:
    """Return a new grid: base with `region` cells replaced by winner values."""
    out = [row[:] for row in base]
    for (i, j) in region:
        out[i][j] = winner[i][j]
    return out


def contested_region(nx: int, ny: int, margin: int = 1) -> list:
    """The shared interior cells both domains fight over (whole interior here)."""
    return [
        (i, j)
        for i in range(margin, nx - margin)
        for j in range(margin, ny - margin)
    ]


def clash(a: Domain, b: Domain) -> ClashResult:
    """Stage a clash between domains a and b and decide the winner."""
    ra = solve_domain(a)
    rb = solve_domain(b)

    # Higher refinement wins. Ties broken by lower residual, then higher rigidity.
    a_wins = (ra.refinement, -ra.residual_l2, ra.rigidity) >= (
        rb.refinement,
        -rb.residual_l2,
        rb.rigidity,
    )

    if a_wins:
        winner, loser = a, b
        wr, lr = ra, rb
    else:
        winner, loser = b, a
        wr, lr = rb, ra

    region = contested_region(loser.nx, loser.ny)

    # The winner re-solves while forcing its constraints over the region that
    # the loser had claimed (loser's field pre-loaded, then overwritten).
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
