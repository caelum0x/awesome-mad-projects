"""Runnable demo: the Divergence Meter end to end.

Measures a canonical worldline, renders it on the nixie display, classifies its
attractor field, then simulates a seeded ensemble and draws both the ASCII
worldline timeline (via :mod:`commons.adapters.ascii_art`) and the attractor-field
histogram -- one source of truth shared with the CLI, the tests, and the optional
PNG exporter.

Run:  python -m divergence_meter.demo
"""

from __future__ import annotations

from divergence_meter.adapters import cli, timeline
from divergence_meter.core.ensemble import simulate_worldlines

_HEADLINE = "THE DIVERGENCE METER -- El Psy Congroo"
_SUBTITLE = (
    "A deterministic worldline divergence from a SHA-256 snapshot of world state, "
    "classified into Alpha/Beta attractor fields and displayed on nixie tubes."
)
_CANONICAL_SOURCE = "El Psy Congroo"


def render_demo(*, count: int = 120, seed: int = 42) -> str:
    """Return the full demo text: headline, a measured worldline, and the ensemble.

    ``count`` seeded worldlines feed the ASCII timeline and field histogram; the
    result is fully reproducible for a given ``count``/``seed``.
    """
    readings = simulate_worldlines(count, seed=seed)
    blocks = [
        _HEADLINE,
        _SUBTITLE,
        "",
        "-- measure -----------------------------------------------------",
        cli.render_measure(_CANONICAL_SOURCE),
        "",
        timeline.render_worldline_timeline(readings),
        "",
        timeline.render_field_histogram(readings),
    ]
    return "\n".join(blocks)


def main() -> int:
    """Print the demo. Returns process exit code 0."""
    print(render_demo())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
