"""ASCII visualization of the compact torus factor and the wrap-around effect.

matplotlib is optional. If present, `save_png` can render a scatter, but the
default path is pure-ASCII so the demo always produces visible output.
"""
from __future__ import annotations

import math
from typing import List, Sequence, Tuple

try:  # optional
    import matplotlib  # noqa: F401
    HAVE_MPL = True
except Exception:
    HAVE_MPL = False

TWO_PI = 2.0 * math.pi


def torus_grid(
    points: Sequence[Tuple[float, float]],
    labels: Sequence[int],
    width: int = 48,
    height: int = 18,
) -> str:
    """Render (theta1, theta2) points on a 2D torus as an ASCII grid.

    Left/right edges are identified, top/bottom edges are identified (that IS
    the torus). Points near opposite edges are actually neighbors -- the grid
    makes the wrap-around visible.
    """
    grid = [[" " for _ in range(width)] for _ in range(height)]
    glyphs = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    for (t1, t2), lab in zip(points, labels):
        col = int((t1 % TWO_PI) / TWO_PI * width) % width
        row = int((t2 % TWO_PI) / TWO_PI * height) % height
        grid[row][col] = glyphs[lab % len(glyphs)]

    top = "  +" + "-" * width + "+   theta1 -> (right edge wraps to left)"
    lines: List[str] = [top]
    for r in range(height):
        lines.append("  |" + "".join(grid[r]) + "|")
    bot = "  +" + "-" * width + "+"
    lines.append(bot)
    lines.append("  theta2 | (bottom edge wraps to top). Same digit = same cluster.")
    return "\n".join(lines)


def wrap_number_line(
    angles: Sequence[float], width: int = 48
) -> str:
    """Show angles on a naive [0, 2*pi) number line where wrap-around is hidden.

    Demonstrates why the naive view splits a cluster that straddles 0 / 2*pi.
    """
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


def render_holonomy(trace) -> str:
    """Textual depiction of a vector rotating as it is transported round a loop."""
    lines = ["  theta      vector (x, y)      arrow"]
    for theta, (x, y) in trace:
        ang = math.atan2(y, x)
        arrows = "→↗↑↖←↙↓↘"  # coarse 8-direction indicator (E,NE,N,NW,W,SW,S,SE)
        idx = int(((ang % TWO_PI) / TWO_PI) * 8) % 8
        lines.append(
            f"  {theta:5.2f}   ({x:+.3f}, {y:+.3f})     {arrows[idx]}"
        )
    return "\n".join(lines)


def save_png(points, labels, path: str) -> bool:  # pragma: no cover
    """Optionally save a matplotlib scatter. Returns True if written."""
    if not HAVE_MPL:
        return False
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    plt.figure(figsize=(5, 5))
    plt.scatter(xs, ys, c=labels, cmap="tab10", s=30)
    plt.xlabel("theta1")
    plt.ylabel("theta2")
    plt.title("Compact torus factor (colored by cluster)")
    plt.savefig(path, dpi=100, bbox_inches="tight")
    plt.close()
    return True
