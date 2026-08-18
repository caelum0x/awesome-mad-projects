"""commons.adapters -- presentation / IO layers over the pure core.

Adapters may depend on :mod:`commons.core`, but core never depends on adapters
(one-directional coupling keeps the numerical core pure and testable).
"""

from __future__ import annotations

from commons.adapters.ascii_art import (
    render_convergence,
    render_heatmap,
    render_line_plot,
    render_sign_map,
)

__all__ = [
    "render_line_plot",
    "render_convergence",
    "render_heatmap",
    "render_sign_map",
]
