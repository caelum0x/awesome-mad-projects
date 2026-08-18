"""The four-lens conclusion table.

Sabiq's essay reads Gojo Satoru's "Infinity" through four mathematical lenses,
each reaching an independent verdict on whether the barrier holds:

    Lens 1  Geometric series / Zeno      -> FRAGILE
    Lens 2  Lebesgue measure             -> FRAGILE
    Lens 3  Riemannian conformal metric  -> FORMIDABLE
    Lens 4  Topology / World-Cutting Slash -> FALLS

This module owns the immutable :class:`Verdict` value object and the canonical
verdict for each lens. The lens modules import :class:`Verdict` (and their own
constant) from here; this module never imports the lens modules, so the
dependency arrow is one-directional and there is no import cycle.

Pure stdlib only.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class Verdict:
    """A single lens verdict for the conclusion table.

    Immutable: assemble a new instance rather than mutating an existing one.
    """

    lens: str
    verdict: str
    reason: str


# ---------------------------------------------------------------------------
# Canonical per-lens verdicts (the essay's conclusions)
# ---------------------------------------------------------------------------

ZENO_VERDICT: Verdict = Verdict(
    lens="Geometric series (Zeno)",
    verdict="Fragile",
    reason="attacker arrives; crossed series and arrival-time series both -> finite",
)

MEASURE_VERDICT: Verdict = Verdict(
    lens="Lebesgue measure",
    verdict="Fragile",
    reason="m(Z) = 0; the barrier is a null set of total length zero",
)

RIEMANNIAN_VERDICT: Verdict = Verdict(
    lens="Riemannian geometry",
    verdict="Formidable",
    reason="felt geodesic length to the barrier diverges to +infinity",
)

TOPOLOGY_VERDICT: Verdict = Verdict(
    lens="Topology",
    verdict="Falls",
    reason="severing continuity disconnects the domain; the metric is undefined",
)


def conclusion_table() -> List[Verdict]:
    """Return the four lens verdicts in essay order (immutable tuple -> list)."""
    return [
        ZENO_VERDICT,
        MEASURE_VERDICT,
        RIEMANNIAN_VERDICT,
        TOPOLOGY_VERDICT,
    ]


def verdict_labels() -> List[str]:
    """Just the four verdict labels: ``['Fragile', 'Fragile', 'Formidable', 'Falls']``."""
    return [v.verdict for v in conclusion_table()]


def format_table() -> str:
    """Render the conclusion table as a fixed-width ASCII block (deterministic)."""
    rows = conclusion_table()
    lens_w = max(len("Lens"), *(len(v.lens) for v in rows))
    verdict_w = max(len("Verdict"), *(len(v.verdict) for v in rows))
    header = f"{'Lens':<{lens_w}}  {'Verdict':<{verdict_w}}  Reason"
    sep = "-" * len(header)
    lines = [header, sep]
    for v in rows:
        lines.append(f"{v.lens:<{lens_w}}  {v.verdict:<{verdict_w}}  {v.reason}")
    return "\n".join(lines)
