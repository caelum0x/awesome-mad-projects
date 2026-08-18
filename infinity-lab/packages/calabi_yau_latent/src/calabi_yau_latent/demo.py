"""Runnable demo: naive vs topology-aware view of a compactified latent space.

Reproduces the canonical narrated report -- the seam problem, naive-vs-wrap-aware
clustering, the ASCII 2-torus, and the holonomy-flavoured parallel-transport
cartoon -- sharing exactly one source of truth with the CLI and the tests
(:mod:`calabi_yau_latent.adapters.cli`).

This is a TOY. It is NOT a Calabi-Yau manifold. See README.md.

Run:  python -m calabi_yau_latent.demo
"""

from __future__ import annotations

from calabi_yau_latent.adapters import cli
from calabi_yau_latent.core.config import DEFAULT, CYConfig

_HEADLINE = (
    "COMPACTIFIED LATENT SPACE -- structure hidden in small, periodic dimensions"
)
_SUBTITLE = (
    "A flat R^k x T^m product space: an HONEST TOY analogy for Calabi-Yau "
    "compactification, not a Ricci-flat CY manifold."
)


def render_demo(config: CYConfig = DEFAULT) -> str:
    """Return the full demo text: headline, subtitle, and the canonical report."""
    blocks = [_HEADLINE, _SUBTITLE, "", cli.render_all(config)]
    return "\n".join(blocks)


def main() -> int:
    """Print the demo. Returns process exit code 0."""
    print(render_demo())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
