"""Runnable demo: the Central Finite Curve engine end to end.

Reproduces the canonical pipeline -- seed the multiverse, extract the near-maximal
Rickness ridge, fire the portal gun along it, and render the ASCII projection --
sharing exactly one source of truth with the CLI and the tests
(:mod:`central_finite_curve.adapters.cli`).

Run:  python -m central_finite_curve.demo
"""

from __future__ import annotations

from central_finite_curve.adapters import cli
from central_finite_curve.core.config import DEFAULT, CurveConfig

_HEADLINE = "THE CENTRAL FINITE CURVE -- every reality where a Rick is smartest"
_SUBTITLE = (
    "A near-maximal Rickness ridge over a high-dimensional multiverse, walked by a "
    "hard-constraint portal gun."
)


def render_demo(config: CurveConfig = DEFAULT) -> str:
    """Return the full demo text: headline, subtitle, and the canonical report."""
    blocks = [_HEADLINE, _SUBTITLE, "", cli.render_all(config)]
    return "\n".join(blocks)


def main() -> int:
    """Print the demo. Returns process exit code 0."""
    print(render_demo())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
