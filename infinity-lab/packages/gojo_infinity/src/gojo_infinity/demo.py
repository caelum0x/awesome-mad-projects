"""Runnable demo: the four lenses on Gojo Satoru's "Infinity".

Reproduces the numeric examples from Achmad Roykhan Sabiq's essay -- the Zeno
partial sums, the Lebesgue cover length, the calibrated conformal metric, and
the World-Cutting Slash -- then prints the full four-verdict conclusion table
followed by the essay's honest 'cursed-energy' caveat.

The narrative rendering lives in :mod:`gojo_infinity.adapters.cli` so the demo,
the CLI, and the tests all share exactly one source of truth. This module adds
the top headline and the ASCII galleries.

Run:  python -m gojo_infinity.demo
"""

from __future__ import annotations

from gojo_infinity.adapters import cli, viz

_HEADLINE = "MATHEMATICS BEHIND JUJUTSU KAISEN: GOJO SATORU'S INFINITY"
_SUBTITLE = "Four lenses, after Achmad Roykhan Sabiq (Oxford Maths Essay 2026)."


def render_demo() -> str:
    """Return the full demo text: headline, four lens reports, ASCII, conclusion."""
    blocks = [
        _HEADLINE,
        _SUBTITLE,
        "",
        cli.render_zeno(),
        cli.render_measure(),
        cli.render_riemannian(),
        cli.render_manifold(),
        cli.render_topology(),
        "ASCII GALLERY -- convergence of the three quantitative lenses:",
        viz.render_zeno_convergence(12),
        viz.render_omega_blowup(),
        viz.render_cover_convergence(),
        cli.render_conclusion(),
    ]
    return "\n\n".join(blocks)


def main() -> int:
    """Print the demo. Returns process exit code 0."""
    print(render_demo())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
