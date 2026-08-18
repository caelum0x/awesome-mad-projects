"""ASCII rendering of solved domain fields (stdlib only, deterministic).

Turns the pure :mod:`domain_expansion.core` results into plain ``str`` blocks
that are safe to print or pin in tests. Two views of a field:

  * :func:`format_field` -- a bespoke labelled fixed-width numeric grid (the
    "read the actual temperatures" table), which the generic commons renderers
    do not provide.
  * :func:`field_heatmap` -- a shaded heatmap that DELEGATES to
    :func:`commons.adapters.ascii_art.render_heatmap`, where a shaded grid with a
    value legend is the natural tool.

Alongside them: per-domain solve reports and a clash report.

This is an adapter: it imports ``core`` and ``commons.adapters`` but is never
imported by ``core``.
"""

from __future__ import annotations

from typing import List

from commons.adapters.ascii_art import render_heatmap

from domain_expansion.core.clash import ClashResult
from domain_expansion.core.domain import Grid, SolveResult


def _rows_top_first(field: Grid) -> List[List[float]]:
    """Return ``field`` (indexed ``[i=x][j=y]``) as row-major ``values[y][x]``.

    Row ``y == 0`` is placed first so a caller printing bottom-up (like
    :func:`commons.adapters.ascii_art.render_heatmap`) shows increasing ``y``
    upward, matching the numeric :func:`format_field` view.
    """
    if not field or not field[0]:
        raise ValueError("field must be a non-empty grid")
    nx = len(field)
    ny = len(field[0])
    return [[field[i][j] for i in range(nx)] for j in range(ny)]


def format_field(field: Grid, title: str) -> str:
    """Return the field as a labelled fixed-width numeric grid (y increases up)."""
    if not field or not field[0]:
        raise ValueError("field must be a non-empty grid")
    nx = len(field)
    ny = len(field[0])
    lines: List[str] = [title]
    for j in range(ny - 1, -1, -1):  # top row (largest y) first
        row = "  ".join(f"{field[i][j]:6.1f}" for i in range(nx))
        lines.append("  " + row)
    return "\n".join(lines)


def field_heatmap(field: Grid, *, title: str = "domain field heatmap") -> str:
    """Shaded heatmap of a solved field via the shared commons renderer."""
    values = _rows_top_first(field)
    return render_heatmap(values, width=len(field), title=title)


def format_solve_report(name: str, result: SolveResult) -> str:
    """Return a stable, greppable multi-line report of a :class:`SolveResult`."""
    return "\n".join(
        [
            f"[{name}]",
            f"  converged        : {result.converged} in {result.iterations} iters",
            f"  residual  (L2)   : {result.residual_l2:.6e}",
            f"  residual  (Linf) : {result.residual_inf:.6e}",
            f"  rigidity  proxy  : {result.rigidity:.6f}",
            f"  refinement score : {result.refinement:.6f}",
        ]
    )


def format_clash_report(result: ClashResult) -> str:
    """Return the clash verdict plus the merged field with the overwrite marked."""
    lines: List[str] = [
        f"WINNER : {result.winner}",
        f"LOSER  : {result.loser}",
        f"WHY    : {result.reason}",
        "",
        format_field(
            result.merged_field,
            f"Contested region overwritten by {result.winner}:",
        ),
    ]
    return "\n".join(lines)
