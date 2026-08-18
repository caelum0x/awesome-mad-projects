"""Tiny stdlib-only ASCII plotting for the entropy timeline.

No third-party dependencies. Renders the global (or total) entropy curve as a
row-per-sample chart and marks steps where a witch transformation occurred.
"""


def ascii_line_chart(
    values,
    marks=None,
    width: int = 60,
    height: int = 18,
    title: str = "",
) -> str:
    """Render ``values`` as an ASCII line chart.

    Args:
        values: sequence of floats (the series to plot).
        marks: optional set/collection of sample indices to flag on the x-axis
            (used to mark witch transformations).
        width: number of columns for the plot area (series is resampled to fit).
        height: number of rows for the plot area.
        title: optional heading printed above the chart.

    Returns a multi-line string.
    """
    marks = set(marks or ())
    if not values:
        return (title + "\n(no data)").strip()

    n = len(values)
    # Resample the series onto `width` columns (nearest-sample).
    cols = []
    col_is_mark = []
    for c in range(width):
        idx = int(round(c * (n - 1) / max(1, width - 1)))
        cols.append(values[idx])
        # A column is marked if any sample it represents was a mark.
        lo = int(round((c - 0.5) * (n - 1) / max(1, width - 1)))
        hi = int(round((c + 0.5) * (n - 1) / max(1, width - 1)))
        col_is_mark.append(any(m in marks for m in range(max(0, lo), hi + 1)))

    vmin = min(cols)
    vmax = max(cols)
    span = (vmax - vmin) or 1.0

    # Build grid: rows top (high) -> bottom (low).
    rows = [[" "] * width for _ in range(height)]
    for c, v in enumerate(cols):
        level = int(round((v - vmin) / span * (height - 1)))
        r = height - 1 - level
        rows[r][c] = "*" if col_is_mark[c] else "o"

    lines = []
    if title:
        lines.append(title)
    for r, row in enumerate(rows):
        # y-axis label at top, middle, bottom
        if r == 0:
            label = f"{vmax:8.1f} |"
        elif r == height - 1:
            label = f"{vmin:8.1f} |"
        else:
            label = " " * 8 + " |"
        lines.append(label + "".join(row))

    axis = " " * 8 + " +" + "-" * width
    lines.append(axis)

    # x-axis: mark columns with '^' where witches occurred.
    xmarks = [" "] * width
    for c in range(width):
        if col_is_mark[c]:
            xmarks[c] = "^"
    lines.append(" " * 10 + "".join(xmarks))
    lines.append(" " * 10 + f"step 0 .. {n - 1}   ('^' = witch transformation)")
    return "\n".join(lines)
