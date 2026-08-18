"""Optional matplotlib PNG export of the global-entropy timeline.

DEFERRED behind the ``commons.core.optional`` matplotlib guard: with no
matplotlib installed :func:`save_entropy_png` raises a clear
:class:`OptionalDependencyError` instead of failing at import time, so this
module stays importable with the standard library alone and always renders
headless on the Agg backend.

The picture is the global entropy rising over the run, with each witch
transformation marked as a vertical line + point, exported (by default) as
``madoka_entropy_entropy.png``.

This is an adapter: it imports ``core`` but is never imported by ``core``.
"""

from __future__ import annotations

from typing import Any, List

from commons.core.optional import try_import

from madoka_entropy.core.config import DEFAULT, SimConfig
from madoka_entropy.core.simulation import run_simulation


class OptionalDependencyError(RuntimeError):
    """Raised when the optional viz backend (matplotlib) is unavailable.

    The ASCII renderers in :mod:`madoka_entropy.adapters.plot` never raise this;
    only the deferred PNG export does, and only when the caller explicitly
    requests it without the dependency.
    """


_PNG_HELP = (
    "PNG export requires matplotlib, which is not installed. Install the "
    "optional 'viz' extra (pip install -e '.[viz]'), or use the ASCII renderer "
    "(madoka_entropy.adapters.plot.global_entropy_chart), which needs no "
    "dependencies."
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


def save_entropy_png(path: str, *, config: SimConfig = DEFAULT) -> str:
    """Render the global-entropy timeline (with witch marks) to ``path``.

    Plots global entropy vs step as a rising line, overlays each witch
    transformation as a vertical marker, and annotates the total-entropy
    invariant. matplotlib is imported lazily; raises
    :class:`OptionalDependencyError` when it is absent. Returns ``path``.
    """
    result = run_simulation(config)
    records = result.records
    steps = [r.step for r in records]
    global_series = [r.global_entropy for r in records]
    total_series = [r.total_entropy for r in records]
    witch_events: List[int] = [r.step for r in records if r.witches_this_step]

    pyplot = _load_pyplot()
    figure, axes = pyplot.subplots(figsize=(9, 5))
    if steps:
        axes.plot(
            steps, global_series, color="#8844cc", lw=1.6,
            label="global entropy (karmic reservoir)",
        )
        axes.plot(
            steps, total_series, color="#22aa88", lw=1.0, ls="--",
            label="total entropy (2nd-law monotone)",
        )
    first = True
    for w in witch_events:
        axes.axvline(
            w, color="#cc3366", lw=0.9, alpha=0.6,
            label="witch transformation" if first else None,
        )
        idx = steps.index(w)
        axes.scatter([w], [global_series[idx]], color="#cc3366", s=28, zorder=5)
        first = False
    axes.set_title(
        "Madoka Magica -- global entropy rising with karma "
        f"(seed {config.seed}, {config.steps} steps, "
        f"{len(witch_events)} witch events)"
    )
    axes.set_xlabel("simulation step")
    axes.set_ylabel("entropy (dimensionless)")
    axes.legend(loc="upper left")
    figure.tight_layout()
    figure.savefig(path, dpi=120)
    pyplot.close(figure)
    return path
