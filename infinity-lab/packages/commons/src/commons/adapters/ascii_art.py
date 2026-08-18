"""Text-based visualisation renderers (stdlib only, deterministic).

Every function returns a plain ``str`` suitable for logs, terminals, or test
assertions -- no third-party plotting library and no file I/O. Given the same
inputs the output is byte-for-byte identical, so renders are safe to pin in
tests.

Renderers:
    * :func:`render_line_plot` / :func:`render_convergence` -- a single 1-D
      series as a vertical-axis line chart.
    * :func:`render_heatmap` -- a 2-D scalar field as a shaded grid with a
      value legend.
    * :func:`render_sign_map` -- a +/- region map that traces the zero curve
      (sign-change boundary) of a field over a scatter grid.

This is an *adapter*: it imports only the standard library, never ``core``
numerics, so it stays a pure presentation layer.
"""

from __future__ import annotations

from typing import Callable, List, Optional, Sequence

# Shading ramp from lowest (space) to highest ('@') value.
_RAMP = " .:-=+*#%@"

_POS_CHAR = "+"
_NEG_CHAR = "-"
_ZERO_CHAR = "O"
_POINT_CHAR = "*"
_BLANK_CHAR = " "


def _column_indices(n_cols: int, width: Optional[int]) -> List[int]:
    """Return the column indices to sample, optionally downsampled to ``width``."""
    if width is None or width >= n_cols:
        return list(range(n_cols))
    if width < 1:
        raise ValueError("width must be >= 1")
    if width == 1:
        return [0]
    return [round(c * (n_cols - 1) / (width - 1)) for c in range(width)]


def render_line_plot(
    ys: Sequence[float],
    *,
    height: int = 12,
    title: str = "line plot",
) -> str:
    """Render a 1-D series ``ys`` as an ASCII line chart with a value axis.

    The vertical axis spans ``[min(ys), max(ys)]`` over ``height`` rows; each
    sample maps to one column marked with ``'*'``. Returns a non-empty
    deterministic string. Raises :class:`ValueError` for empty ``ys`` or
    ``height < 1``.
    """
    if len(ys) == 0:
        raise ValueError("ys must be non-empty")
    if height < 1:
        raise ValueError("height must be >= 1")

    lo = min(ys)
    hi = max(ys)
    span = (hi - lo) if hi > lo else 1.0

    # Row 0 is the top (highest value); map each y to a row bucket.
    def row_of(y: float) -> int:
        frac = (y - lo) / span
        r = int(round((1.0 - frac) * (height - 1)))
        return max(0, min(height - 1, r))

    rows = [row_of(y) for y in ys]
    lines: List[str] = [title]
    for r in range(height):
        # Value label for this row (top row = hi, bottom row = lo).
        val = hi - (r / (height - 1)) * span if height > 1 else hi
        cells = [
            _POINT_CHAR if rows[c] == r else _BLANK_CHAR for c in range(len(ys))
        ]
        lines.append(f"{val:+10.4f} |" + "".join(cells))
    axis = " " * 11 + "+" + "-" * len(ys)
    footer = " " * 12 + f"n=0 .. n={len(ys) - 1}"
    return "\n".join(lines + [axis, footer])


def render_convergence(
    ys: Sequence[float],
    target: float,
    *,
    height: int = 12,
    title: str = "convergence",
) -> str:
    """Render a convergence trace of ``ys`` toward ``target``.

    Delegates to :func:`render_line_plot` and appends a legend line reporting
    the final absolute error ``|ys[-1] - target|``. Raises :class:`ValueError`
    for empty ``ys``.
    """
    if len(ys) == 0:
        raise ValueError("ys must be non-empty")
    plot = render_line_plot(ys, height=height, title=title)
    final_err = abs(ys[-1] - target)
    legend = f"legend: target={target:+.6f}   final |error|={final_err:.3e}"
    return plot + "\n\n" + legend


def render_heatmap(
    values: List[List[float]],
    *,
    row_labels: Optional[Sequence[float]] = None,
    width: Optional[int] = None,
    title: str = "heatmap",
) -> str:
    """Render a 2-D scalar field ``values`` as a shaded ASCII grid + legend.

    ``values`` is row-major (``values[row][col]``); row 0 is printed at the
    *bottom* so the vertical axis increases upward. Cell shade is chosen from a
    10-level ramp scaled to ``[min, max]``. ``row_labels`` (one per row) annotate
    the left margin; ``width`` optionally downsamples wide grids. Returns a
    non-empty deterministic string. Raises :class:`ValueError` for an empty or
    ragged grid, or mismatched ``row_labels``.
    """
    if len(values) == 0 or len(values[0]) == 0:
        raise ValueError("values must be a non-empty 2-D grid")
    n_cols = len(values[0])
    if any(len(row) != n_cols for row in values):
        raise ValueError("all rows must have equal length")
    n_rows = len(values)
    if row_labels is not None and len(row_labels) != n_rows:
        raise ValueError("row_labels length must match number of rows")

    flat = [x for row in values for x in row]
    lo, hi = min(flat), max(flat)
    span = (hi - lo) if hi > lo else 1.0
    col_idx = _column_indices(n_cols, width)

    lines: List[str] = [title]
    for r in range(n_rows - 1, -1, -1):
        chars = []
        for i in col_idx:
            frac = (values[r][i] - lo) / span
            k = int(frac * (len(_RAMP) - 1))
            k = max(0, min(len(_RAMP) - 1, k))
            chars.append(_RAMP[k])
        label = f"{row_labels[r]:+.3f}" if row_labels is not None else f"r{r:>3d}"
        lines.append(f"{label:>8} |" + "".join(chars))

    axis = " " * 9 + "+" + "-" * len(col_idx)
    legend = (
        f"scale: '{_RAMP[0]}'={lo:+.4f}  ...  '{_RAMP[-1]}'={hi:+.4f}"
    )
    return "\n".join(lines + [axis, "", legend])


def render_sign_map(
    field: Callable[[float, float], float],
    xs: Sequence[float],
    ys: Sequence[float],
    *,
    width: Optional[int] = None,
    title: str = "sign map",
) -> str:
    """Render the sign of ``field(x, y)`` over a grid and trace its zero curve.

    ``'+'`` marks ``field > 0``, ``'-'`` marks ``field < 0``, and ``'O'`` marks
    any cell that is zero or adjacent (4-neighbour) to a sign change -- i.e. the
    traced zero curve overlaid on the scatter grid. Rows correspond to ``ys``
    (printed with ``ys[-1]`` on top), columns to ``xs``. Returns a non-empty
    deterministic string. Raises :class:`ValueError` for empty ``xs``/``ys``.
    """
    if len(xs) == 0 or len(ys) == 0:
        raise ValueError("xs and ys must be non-empty")
    col_idx = _column_indices(len(xs), width)

    signs: List[List[int]] = []
    for y in ys:
        row: List[int] = []
        for i in col_idx:
            val = field(xs[i], y)
            row.append(1 if val > 0.0 else (-1 if val < 0.0 else 0))
        signs.append(row)

    n_rows = len(ys)
    n_scols = len(col_idx)

    def on_curve(r: int, c: int) -> bool:
        s = signs[r][c]
        if s == 0:
            return True
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < n_rows and 0 <= nc < n_scols:
                neighbour = signs[nr][nc]
                if neighbour == -s or neighbour == 0:
                    return True
        return False

    lines: List[str] = [title]
    for r in range(n_rows - 1, -1, -1):
        chars = []
        for c in range(n_scols):
            if on_curve(r, c):
                chars.append(_ZERO_CHAR)
            elif signs[r][c] > 0:
                chars.append(_POS_CHAR)
            else:
                chars.append(_NEG_CHAR)
        lines.append(f"{ys[r]:+.3f} |" + "".join(chars))

    axis = " " * 7 + "+" + "-" * n_scols
    legend = (
        f"legend: '{_POS_CHAR}'=field>0   '{_NEG_CHAR}'=field<0   "
        f"'{_ZERO_CHAR}'=zero curve (field=0)"
    )
    return "\n".join(lines + [axis, "", legend])
