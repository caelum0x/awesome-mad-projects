"""Runnable demo: the Madoka Magica entropy & karmic calculus, end to end.

Reproduces the canonical run -- seed the closed system, spend wishes, corrupt
soul gems into witches, harvest the karmic surplus, and verify the second-law
invariant -- sharing exactly one source of truth with the CLI and the tests
(:mod:`madoka_entropy.adapters.cli`).

Run:  python -m madoka_entropy.demo
"""

from __future__ import annotations

from madoka_entropy.adapters import cli
from madoka_entropy.core.config import DEFAULT, SimConfig

_HEADLINE = "MADOKA MAGICA -- buying local order by exporting a larger global cost"
_SUBTITLE = (
    "A seeded closed-system entropy ledger: every wish nets (k-1)x > 0, every "
    "witch injects a burst, and total entropy never decreases."
)


def render_demo(config: SimConfig = DEFAULT) -> str:
    """Return the full demo text: headline, subtitle, and the canonical report."""
    blocks = [_HEADLINE, _SUBTITLE, "", cli.render_report(config)]
    return "\n".join(blocks)


def main() -> int:
    """Print the demo. Returns process exit code 0."""
    print(render_demo())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
