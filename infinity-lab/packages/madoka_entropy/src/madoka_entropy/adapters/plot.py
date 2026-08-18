"""Dependency-free ASCII plotting for the entropy timeline.

No third-party dependencies. Renders the global (or total) entropy curve as an
ASCII line chart and *marks the steps where a witch transformation occurred* --
the one feature the shared :mod:`commons.adapters.ascii_art` line renderer does
not provide. For the unmarked total-entropy view we defer to the shared
``commons`` renderer, keeping a single source of truth for plain series charts.

This is an adapter: it imports ``core`` and ``commons.adapters`` but is never
imported by ``core``.
"""

from __future__ import annotations

from typing import Iterable, List, Optional, Sequence, Set

from commons.adapters.ascii_art import render_line_plot

from madoka_entropy.core.simulation import StepRecord


def witch_steps(records: Sequence[StepRecord]) -> Set[int]:
    """Return the set of step indices on which any witch transformation fired."""
    return {r.step for r in records if r.witches_this_step}


def ascii_line_chart(
    values: Sequence[float],
    marks: Optional[Iterable[int]] = None,
    width: int = 60,
    height: int = 18,
    title: str = "",
) -> str:
    """Render ``values`` as an ASCII line chart with optional event marks.

    Args:
        values: sequence of floats (the series to plot).
        marks: optional collection of sample indices to flag (witch events).
        width: number of columns for the plot area (series resampled to fit).
        height: number of rows for the plot area.
        title: optional heading printed above the chart.

    Marked columns are drawn with ``'*'`` (vs ``'o'`` for ordinary samples) and
    flagged with ``'^'`` on the x-axis. Returns a multi-line string.
    """
    if width < 1 or height < 1:
        raise ValueError("width and height must be >= 1")
    mark_set = set(marks or ())
    if not values:
        return (title + "\n(no data)").strip()

    n = len(values)
    cols: List[float] = []
    col_is_mark: List[bool] = []
    for c in range(width):
        idx = int(round(c * (n - 1) / max(1, width - 1)))
        cols.append(values[idx])
        # A column is marked if any sample it represents was a mark.
        lo = int(round((c - 0.5) * (n - 1) / max(1, width - 1)))
        hi = int(round((c + 0.5) * (n - 1) / max(1, width - 1)))
        col_is_mark.append(any(m in mark_set for m in range(max(0, lo), hi + 1)))

    vmin = min(cols)
    vmax = max(cols)
    span = (vmax - vmin) or 1.0

    # Build grid: rows top (high) -> bottom (low).
    rows = [[" "] * width for _ in range(height)]
    for c, v in enumerate(cols):
        level = int(round((v - vmin) / span * (height - 1)))
        r = height - 1 - level
        rows[r][c] = "*" if col_is_mark[c] else "o"

    lines: List[str] = []
    if title:
        lines.append(title)
    for r, row in enumerate(rows):
        if r == 0:
            label = f"{vmax:8.1f} |"
        elif r == height - 1:
            label = f"{vmin:8.1f} |"
        else:
            label = " " * 8 + " |"
        lines.append(label + "".join(row))

    lines.append(" " * 8 + " +" + "-" * width)

    xmarks = ["^" if col_is_mark[c] else " " for c in range(width)]
    lines.append(" " * 10 + "".join(xmarks))
    lines.append(" " * 10 + f"step 0 .. {n - 1}   ('^' = witch transformation)")
    return "\n".join(lines)


def global_entropy_chart(
    records: Sequence[StepRecord],
    width: int = 60,
    height: int = 18,
    title: str = (
        "GLOBAL entropy (the universe's reservoir) -- climbs with karma:"
    ),
) -> str:
    """Marked ASCII chart of global entropy over time (witch events flagged)."""
    values = [r.global_entropy for r in records]
    return ascii_line_chart(
        values, marks=witch_steps(records), width=width, height=height, title=title
    )


def total_entropy_chart(
    records: Sequence[StepRecord],
    height: int = 12,
    title: str = "TOTAL entropy S_global + sum(S_local) -- 2nd-law monotone",
) -> str:
    """Unmarked total-entropy chart via the shared ``commons`` line renderer."""
    values = [r.total_entropy for r in records]
    if not values:
        return f"{title}\n(no data)"
    return render_line_plot(values, height=height, title=title)
