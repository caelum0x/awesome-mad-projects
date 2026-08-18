"""ASCII rendering of the 2-D projection (stdlib only, deterministic).

The primary renderer is :func:`ascii_scatter`: it draws the projected curve as a
density ramp and overlays the portal-gun walk as ``'@'`` in a shared frame -- the
bespoke picture the concept calls for (a density scatter with an overlaid path),
which the generic ``commons.adapters.ascii_art`` renderers do not provide directly.
:func:`density_heatmap` is offered alongside it and DOES delegate to
:func:`commons.adapters.ascii_art.render_heatmap` for a pure density view where a
labelled shaded grid is the more natural tool.

Given the same inputs the output is byte-for-byte identical, so renders are safe to
pin in tests. This is an adapter: it imports ``core`` config and
``commons.adapters`` but is never imported by ``core``.
"""

from __future__ import annotations

from typing import List, Optional, Sequence, Tuple

from commons.adapters.ascii_art import render_heatmap

from central_finite_curve.core.config import DEFAULT, CurveConfig

Point2D = Tuple[float, float]

# Density ramp: space (empty) .. '%' (dense); '@' overlays the walk.
_RAMP = " .:-=+*#%"
_WALK_CHAR = "@"


def _bounds(points: Sequence[Point2D]) -> Tuple[float, float, float, float]:
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return min(xs), max(xs), min(ys), max(ys)


def _counts_grid(
    curve_pts: Sequence[Point2D],
    walk_pts: Sequence[Point2D],
    width: int,
    height: int,
) -> Tuple[List[List[int]], List[List[bool]]]:
    """Bin curve points into a counts grid and mark walk cells (shared frame)."""
    all_pts = list(curve_pts) + list(walk_pts)
    xmin, xmax, ymin, ymax = _bounds(all_pts)
    dx = (xmax - xmin) or 1.0
    dy = (ymax - ymin) or 1.0

    def cell(pt: Point2D) -> Tuple[int, int]:
        cx = int((pt[0] - xmin) / dx * (width - 1))
        # Flip y so larger y renders higher on screen.
        cy = int((ymax - pt[1]) / dy * (height - 1))
        return cx, cy

    counts = [[0] * width for _ in range(height)]
    for p in curve_pts:
        cx, cy = cell(p)
        counts[cy][cx] += 1
    walk_mask = [[False] * width for _ in range(height)]
    for p in walk_pts:
        cx, cy = cell(p)
        walk_mask[cy][cx] = True
    return counts, walk_mask


def ascii_scatter(
    curve_pts: Sequence[Point2D],
    walk_pts: Optional[Sequence[Point2D]] = None,
    *,
    config: CurveConfig = DEFAULT,
    width: Optional[int] = None,
    height: Optional[int] = None,
) -> str:
    """Render the curve density with the walk overlaid as ``'@'`` in one frame.

    Curve cells shade by point count along ``_RAMP``; walk cells are drawn as
    ``'@'`` on top. A shared bounding box keeps both in the same frame. Returns
    ``"(empty curve)"`` when there is nothing to draw.
    """
    walk_pts = list(walk_pts or [])
    curve_pts = list(curve_pts)
    if not curve_pts and not walk_pts:
        return "(empty curve)"
    w = width if width is not None else config.grid_w
    h = height if height is not None else config.grid_h

    counts, walk_mask = _counts_grid(curve_pts, walk_pts, w, h)
    max_count = max((max(row) for row in counts), default=0) or 1

    lines: List[str] = []
    for y in range(h):
        row_chars: List[str] = []
        for x in range(w):
            if walk_mask[y][x]:
                row_chars.append(_WALK_CHAR)
                continue
            c = counts[y][x]
            if c == 0:
                row_chars.append(" ")
            else:
                idx = 1 + int((c / max_count) * (len(_RAMP) - 2))
                idx = min(idx, len(_RAMP) - 1)
                row_chars.append(_RAMP[idx])
        lines.append("".join(row_chars))

    border = "+" + "-" * w + "+"
    framed = [border] + ["|" + ln + "|" for ln in lines] + [border]
    legend = "legend:  ' ' empty   .:-=+*#% curve density   @ portal-gun walk"
    return "\n".join(framed) + "\n" + legend


def density_heatmap(
    curve_pts: Sequence[Point2D],
    *,
    config: CurveConfig = DEFAULT,
    width: Optional[int] = None,
    height: Optional[int] = None,
) -> str:
    """Pure density view of the curve via ``commons.adapters.ascii_art.render_heatmap``.

    Bins the projected curve points into a counts grid and hands it to the shared
    commons heatmap renderer (a labelled, shaded grid with a value legend). Returns
    ``"(empty curve)"`` when there is nothing to draw.
    """
    curve_pts = list(curve_pts)
    if not curve_pts:
        return "(empty curve)"
    w = width if width is not None else config.grid_w
    h = height if height is not None else config.grid_h
    counts, _ = _counts_grid(curve_pts, [], w, h)
    values = [[float(c) for c in row] for row in counts]
    return render_heatmap(values, width=w, title="curve density (top-2 PCA plane)")
