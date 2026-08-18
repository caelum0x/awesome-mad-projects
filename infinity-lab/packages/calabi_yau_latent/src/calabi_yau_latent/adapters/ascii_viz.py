"""ASCII visualisation of the compact torus factor and the wrap-around effect.

Pure stdlib text renderers (no plotting library, no file I/O): given the same
inputs the output is byte-for-byte identical, so renders are safe to pin in
tests. The optional matplotlib PNG export lives separately in
:mod:`calabi_yau_latent.adapters.viz`.

This is an *adapter*: it may import :mod:`calabi_yau_latent.core`, but the core
never imports it.
"""

from __future__ import annotations

import math
from typing import List, Sequence, Tuple

TWO_PI = 2.0 * math.pi

_GLYPHS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
# Coarse 8-direction indicator (E, NE, N, NW, W, SW, S, SE).
_ARROWS = "→↗↑↖←↙↓↘"


def torus_grid(
    points: Sequence[Tuple[float, float]],
    labels: Sequence[int],
    width: int = 48,
    height: int = 18,
) -> str:
    """Render ``(theta1, theta2)`` points on a 2-D torus as an ASCII grid.

    Left/right edges are identified and top/bottom edges are identified (that IS
    the torus). Points near opposite edges are actually neighbours -- the grid
    makes the wrap-around visible. Same digit = same cluster label. Raises
    :class:`ValueError` for non-positive ``width``/``height`` or mismatched lengths.
    """
    if width < 1 or height < 1:
        raise ValueError("width and height must be >= 1")
    if len(points) != len(labels):
        raise ValueError("points and labels must have equal length")
    grid = [[" " for _ in range(width)] for _ in range(height)]
    for (t1, t2), lab in zip(points, labels):
        col = int((t1 % TWO_PI) / TWO_PI * width) % width
        row = int((t2 % TWO_PI) / TWO_PI * height) % height
        grid[row][col] = _GLYPHS[lab % len(_GLYPHS)]

    top = "  +" + "-" * width + "+   theta1 -> (right edge wraps to left)"
    lines: List[str] = [top]
    for r in range(height):
        lines.append("  |" + "".join(grid[r]) + "|")
    lines.append("  +" + "-" * width + "+")
    lines.append(
        "  theta2 | (bottom edge wraps to top). Same digit = same cluster."
    )
    return "\n".join(lines)


def wrap_number_line(angles: Sequence[float], width: int = 48) -> str:
    """Show angles on a naive ``[0, 2*pi)`` number line where wrap-around is hidden.

    Demonstrates why the naive view splits a cluster that straddles ``0 / 2*pi``.
    Raises :class:`ValueError` for ``width < 6`` (needed for the axis labels).
    """
    if width < 6:
        raise ValueError("width must be >= 6")
    slots = [" "] * width
    for a in angles:
        idx = int((a % TWO_PI) / TWO_PI * width) % width
        slots[idx] = "*"
    line = "".join(slots)
    return (
        "  0" + " " * (width - 6) + "2*pi\n"
        "  [" + line + "]\n"
        "  ^ naive line: points at the two ends look FAR apart (but on the\n"
        "    circle they are adjacent)."
    )


def render_holonomy(trace: Sequence[Tuple[float, Tuple[float, float]]]) -> str:
    """Textual depiction of a vector rotating as it is transported round a loop."""
    lines = ["  theta      vector (x, y)      arrow"]
    for theta, (x, y) in trace:
        ang = math.atan2(y, x)
        idx = int(((ang % TWO_PI) / TWO_PI) * 8) % 8
        lines.append(
            f"  {theta:5.2f}   ({x:+.3f}, {y:+.3f})     {_ARROWS[idx]}"
        )
    return "\n".join(lines)
