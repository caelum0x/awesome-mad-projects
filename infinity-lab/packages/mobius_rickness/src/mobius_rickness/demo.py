"""Runnable demo: the Central Finite Curve as a REAL zero set.

Reproduces the original curvature sample table (naive positive Rickness, for
continuity), then traces and prints the real Central Finite Curve points
``(u, v, x, y, z)`` on the Mobius strip, and finally shows the torus Gaussian
curvature sign pattern whose two zero circles ``theta = pi/2, 3*pi/2`` form a
genuine, geometry-driven zero set.

The narrative rendering lives in :mod:`mobius_rickness.adapters.cli` so the demo,
the CLI, and the tests all share exactly one source of truth. This module adds
the top headline and the ASCII gallery.

Everything runs on the standard library (numpy / matplotlib are optional and
deferred). Run:  python -m mobius_rickness.demo
"""

from __future__ import annotations

from mobius_rickness.adapters import cli, viz

_HEADLINE = "MOBIUS-RICKNESS: THE CENTRAL FINITE CURVE AS A REAL ZERO SET"
_SUBTITLE = (
    "K<0 on the ruled Mobius strip, so K_Rick = K*R vanishes exactly where "
    "R vanishes."
)


def render_demo() -> str:
    """Return the full demo text: headline, three reports, ASCII gallery."""
    blocks = [
        _HEADLINE,
        _SUBTITLE,
        "",
        cli.render_curvature(),
        cli.render_trace(),
        cli.render_torus(),
        "ASCII GALLERY -- Rickness sign map (Central Finite Curve) + K_Rick heatmap:",
        viz.render_rickness_sign_map(),
        viz.render_k_rick_heatmap(),
    ]
    return "\n\n".join(blocks)


def main() -> int:
    """Print the demo. Returns process exit code 0."""
    print(render_demo())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
