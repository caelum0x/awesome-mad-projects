"""Optional matplotlib PNG export of a worldline divergence timeline.

DEFERRED behind the ``commons.core.optional`` matplotlib guard: with no
matplotlib installed :func:`save_worldlines_png` raises a clear
:class:`OptionalDependencyError` instead of failing at import time, so this
module stays importable with the standard library alone and always renders
headless on the Agg backend.

The picture is a seeded ensemble of worldlines (:func:`core.ensemble.
simulate_worldlines`) plotted as a divergence timeline over ``[0, 2)``, with the
Alpha/Beta attractor-field bands shaded and the Steins;Gate ``1.048596`` line
marked -- the same story the ASCII :mod:`~divergence_meter.adapters.timeline`
renderer tells, exported as ``divergence_meter_worldlines.png``.

This is an adapter: it imports ``core`` but is never imported by ``core``.
"""

from __future__ import annotations

import os
from typing import Any

from commons.core.optional import try_import

from divergence_meter.core.attractor import FIELDS
from divergence_meter.core.divergence import STEINS_GATE_VALUE
from divergence_meter.core.ensemble import simulate_worldlines

# infinity-lab/artifacts/divergence_meter_worldlines.png (repo-root artifacts dir).
_PACKAGE_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
_REPO_ROOT = os.path.dirname(os.path.dirname(_PACKAGE_ROOT))
ARTIFACT_NAME = "divergence_meter_worldlines.png"
DEFAULT_ARTIFACT_PATH = os.path.join(_REPO_ROOT, "artifacts", ARTIFACT_NAME)

# Alternating band shading for the Alpha/Beta attractor fields.
_BAND_COLORS = ("#12324a", "#1b4a63", "#4a2330", "#63313f")


class OptionalDependencyError(RuntimeError):
    """Raised when the optional viz backend (matplotlib) is unavailable.

    The ASCII renderers in :mod:`divergence_meter.adapters.timeline` and
    :mod:`~divergence_meter.adapters.nixie` never raise this; only the deferred
    PNG export does, and only when the caller explicitly requests it without the
    dependency.
    """


_PNG_HELP = (
    "PNG export requires matplotlib, which is not installed. Install the optional "
    "'viz' extra (pip install -e '.[viz]'), or use the ASCII renderer "
    "(divergence_meter.adapters.timeline.render_worldline_timeline), which needs "
    "no dependencies."
)


def _load_pyplot() -> Any:
    """Return ``matplotlib.pyplot`` bound to headless Agg, or raise (deferred)."""
    matplotlib = try_import("matplotlib")
    if matplotlib is None:
        raise OptionalDependencyError(_PNG_HELP)
    matplotlib.use("Agg")  # headless, deterministic, no display needed
    pyplot = try_import("matplotlib.pyplot")
    if pyplot is None:  # pragma: no cover - matplotlib without pyplot is degenerate
        raise OptionalDependencyError("matplotlib is present but pyplot is unavailable")
    return pyplot


def save_worldlines_png(
    path: str = DEFAULT_ARTIFACT_PATH,
    *,
    count: int = 240,
    seed: int = 42,
) -> str:
    """Render a seeded worldline divergence timeline to ``path`` (matplotlib).

    Simulates ``count`` reproducible worldlines, plots their divergence values in
    experiment order, shades the four attractor-field bands, and marks the
    Steins;Gate line. matplotlib is imported lazily; raises
    :class:`OptionalDependencyError` when it is absent. Returns ``path`` on
    success.
    """
    readings = simulate_worldlines(count, seed=seed)
    values = [r.value for r in readings]
    xs = list(range(len(values)))

    pyplot = _load_pyplot()
    figure, axes = pyplot.subplots(figsize=(9, 5))

    for index, (name, low, high) in enumerate(FIELDS):
        axes.axhspan(low, high, color=_BAND_COLORS[index % len(_BAND_COLORS)], alpha=0.5)
        axes.text(len(values) * 0.995, (low + high) / 2.0, name,
                  ha="right", va="center", fontsize=8, color="#dddddd")

    axes.axhline(1.0, color="#ffffff", lw=0.8, ls="--", alpha=0.6, label="Alpha/Beta split")
    axes.axhline(
        STEINS_GATE_VALUE, color="#ffb000", lw=1.4, label=f"Steins;Gate {STEINS_GATE_VALUE:.6f}"
    )
    axes.plot(xs, values, color="#ff6a00", lw=0.8, marker="o", ms=2.5, alpha=0.85,
              label="worldline divergence")

    axes.set_ylim(0.0, 2.0)
    axes.set_xlim(0, max(1, len(values) - 1))
    axes.set_title(
        f"Divergence Meter -- {len(values)} seeded worldlines (seed={seed})"
    )
    axes.set_xlabel("experiment index")
    axes.set_ylabel("divergence value [0, 2)")
    axes.legend(loc="upper right", fontsize=8)
    figure.tight_layout()

    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    figure.savefig(path, dpi=120)
    pyplot.close(figure)
    return path
