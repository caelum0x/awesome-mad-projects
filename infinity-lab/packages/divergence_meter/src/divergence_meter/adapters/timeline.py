"""ASCII worldline-timeline rendering (stdlib + commons.adapters only).

Delegates to :mod:`commons.adapters.ascii_art` -- the shared text renderer -- so
the Divergence Meter draws a worldline *timeline* (divergence value per
experiment) and an attractor-field *histogram* with the same deterministic,
byte-for-byte-stable machinery every other package in the monorepo uses.

This is an adapter: it imports ``core`` and ``commons.adapters`` but is never
imported by ``core``.
"""

from __future__ import annotations

from typing import Sequence

from commons.adapters.ascii_art import render_line_plot

from divergence_meter.core.attractor import FIELDS
from divergence_meter.core.divergence import STEINS_GATE_VALUE, DivergenceReading
from divergence_meter.core.ensemble import field_histogram


def render_worldline_timeline(
    readings: Sequence[DivergenceReading],
    *,
    height: int = 12,
) -> str:
    """Render a timeline of divergence values across an ensemble of readings.

    Uses :func:`commons.adapters.ascii_art.render_line_plot` for the value axis
    and appends the Steins;Gate reference line. Raises :class:`ValueError` for an
    empty ``readings`` sequence.
    """
    if len(readings) == 0:
        raise ValueError("readings must be non-empty")
    values = [r.value for r in readings]
    plot = render_line_plot(
        values, height=height, title="worldline divergence timeline"
    )
    legend = (
        f"legend: range [0, 2)   Steins;Gate line = {STEINS_GATE_VALUE:.6f}   "
        f"n={len(values)} experiments"
    )
    return plot + "\n\n" + legend


def render_field_histogram(readings: Sequence[DivergenceReading]) -> str:
    """Render a text bar chart of how an ensemble populates the attractor fields.

    Deterministic and dependency-free; the bar length is proportional to the
    field count. Raises :class:`ValueError` for an empty ``readings`` sequence.
    """
    if len(readings) == 0:
        raise ValueError("readings must be non-empty")
    counts = field_histogram(tuple(readings))
    total = len(readings)
    max_count = max(counts.values()) or 1
    lines = ["attractor-field population (Alpha < 1.0 <= Beta):"]
    for name, low, high in FIELDS:
        count = counts[name]
        bar = "#" * int(round(count / max_count * 40))
        pct = 100.0 * count / total
        lines.append(f"  {name:<10} [{low:.1f},{high:.1f}) {count:>5} {pct:5.1f}% {bar}")
    return "\n".join(lines)
