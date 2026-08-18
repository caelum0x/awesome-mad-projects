"""Runnable demo: Domain Expansion as a coupled constraint solver.

Reproduces the canonical demo -- solve a refined domain (cross-checked against a
direct Gaussian solve), solve a crude one, stage a clash, and show Unlimited Void
-- sharing exactly one source of truth with the CLI and the tests
(:mod:`domain_expansion.adapters.cli`).

Run:  python -m domain_expansion.demo
"""

from __future__ import annotations

from domain_expansion.adapters import cli

_HEADLINE = "DOMAIN EXPANSION -- a closed region that enforces every constraint at once"
_SUBTITLE = (
    "A discretized Laplace boundary-value problem whose 'power' is the rigidity of "
    "its constraint system; the more refined domain overwrites the weaker one."
)


def render_demo() -> str:
    """Return the full demo text: headline, subtitle, and the canonical report."""
    blocks = [_HEADLINE, _SUBTITLE, "", cli.render_all()]
    return "\n".join(blocks)


def main() -> int:
    """Print the demo. Returns process exit code 0."""
    print(render_demo())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
