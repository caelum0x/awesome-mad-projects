"""Attractor field classification for divergence values.

In Steins;Gate, worldlines cluster into "attractor fields" -- convergent
groups of timelines that resist small changes. We model the divergence range
[0, 2) as a set of contiguous named fields with fixed boundaries, classify a
value into its field, and report the distance to the nearest field boundary
(how close the current line is to slipping into a neighbouring cluster).
"""

from __future__ import annotations

from dataclasses import dataclass

from .divergence import STEINS_GATE_VALUE

# Half-open [low, high) bins spanning the full [0, 2) divergence range.
# The canonical split is Alpha < 1.0 and Beta >= 1.0; we subdivide each half
# for a little more texture ("...etc" in the spec).
FIELDS: tuple[tuple[str, float, float], ...] = (
    ("Alpha-Low", 0.0, 0.5),
    ("Alpha", 0.5, 1.0),
    ("Beta", 1.0, 1.5),
    ("Beta-High", 1.5, 2.0),
)

# Distance under which a value is considered "on the Steins;Gate worldline".
STEINS_GATE_TOLERANCE = 5e-7


@dataclass(frozen=True)
class FieldClassification:
    """Result of classifying a divergence value.

    Attributes:
        value: The divergence value classified.
        field: Name of the containing attractor field.
        cluster: The coarse cluster, "Alpha" (<1.0) or "Beta" (>=1.0).
        nearest_boundary: The boundary value closest to ``value``.
        distance_to_boundary: Absolute distance to ``nearest_boundary``.
        on_steins_gate: Whether the value sits on the Steins;Gate worldline.
    """

    value: float
    field: str
    cluster: str
    nearest_boundary: float
    distance_to_boundary: float
    on_steins_gate: bool

    def describe(self) -> str:
        """A one-line human-readable summary of the classification."""
        tag = " [STEINS;GATE]" if self.on_steins_gate else ""
        return (
            f"Field: {self.field} (cluster {self.cluster}){tag} | "
            f"nearest boundary {self.nearest_boundary:.6f} "
            f"(distance {self.distance_to_boundary:.6f})"
        )


def _boundaries() -> list[float]:
    """All unique field edge values, sorted ascending."""
    edges = {low for _, low, _ in FIELDS}
    edges.update(high for _, _, high in FIELDS)
    return sorted(edges)


def _field_for(value: float) -> str:
    """Return the name of the field containing ``value``."""
    for name, low, high in FIELDS:
        if low <= value < high:
            return name
    # Values at or above the top edge fall into the last field.
    if value >= FIELDS[-1][2]:
        return FIELDS[-1][0]
    return FIELDS[0][0]


def classify(value: float) -> FieldClassification:
    """Classify a divergence value into an attractor field.

    Args:
        value: A divergence value, expected in [0, 2) but clamped-tolerant.

    Raises:
        ValueError: If ``value`` is not a finite real number.
    """
    if value != value or value in (float("inf"), float("-inf")):
        raise ValueError(f"Divergence value must be finite, got {value!r}.")

    field = _field_for(value)
    cluster = "Alpha" if value < 1.0 else "Beta"

    boundaries = _boundaries()
    nearest = min(boundaries, key=lambda edge: abs(value - edge))
    distance = abs(value - nearest)

    on_sg = abs(value - STEINS_GATE_VALUE) <= STEINS_GATE_TOLERANCE

    return FieldClassification(
        value=value,
        field=field,
        cluster=cluster,
        nearest_boundary=nearest,
        distance_to_boundary=distance,
        on_steins_gate=on_sg,
    )
