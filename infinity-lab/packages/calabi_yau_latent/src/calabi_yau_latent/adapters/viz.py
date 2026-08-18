"""Optional matplotlib PNG export of the compact-torus wrap-around scatter.

DEFERRED behind the ``commons.core.optional`` matplotlib guard: with no
matplotlib installed :func:`save_torus_png` raises a clear
:class:`OptionalDependencyError` instead of failing at import time, so this module
stays importable with the standard library alone and always renders headless on
the Agg backend.

The picture is the compact 2-torus factor ``(theta1, theta2)`` coloured by
cluster -- the same structure the ASCII renderer draws -- exported as
``calabi_yau_latent_torus.png``.

This is an adapter: it imports ``core`` but is never imported by ``core``.
"""

from __future__ import annotations

from typing import Any, List, Sequence, Tuple

from commons.core.optional import try_import

from calabi_yau_latent.core.config import DEFAULT, CYConfig
from calabi_yau_latent.core.clustering import cluster
from calabi_yau_latent.core.data import generate, make_space
from calabi_yau_latent.core.distance import toroidal_angular_distance

Point2D = Tuple[float, float]


class OptionalDependencyError(RuntimeError):
    """Raised when the optional viz backend (matplotlib) is unavailable.

    The ASCII renderers in :mod:`calabi_yau_latent.adapters.ascii_viz` never raise
    this; only the deferred PNG export does, and only when the caller explicitly
    requests it without the dependency installed.
    """


_PNG_HELP = (
    "PNG export requires matplotlib, which is not installed. Install the optional "
    "'viz' extra (pip install -e '.[viz]'), or use the ASCII renderer "
    "(calabi_yau_latent.adapters.ascii_viz.torus_grid), which needs no "
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
        raise OptionalDependencyError(
            "matplotlib is present but pyplot is unavailable"
        )
    return pyplot


def _torus_dataset(
    config: CYConfig,
) -> Tuple[List[Point2D], List[int]]:
    """Return ``(torus_xy, wrap_aware_labels)`` for the compact-factor scatter."""
    space = make_space(config)
    points, _truth, torus_xy = generate(space, config)
    labels = cluster(points, toroidal_angular_distance, config.cluster_threshold)
    return list(torus_xy), labels


def save_torus_png(path: str, *, config: CYConfig = DEFAULT) -> str:
    """Render the compact 2-torus factor (coloured by cluster) to ``path``.

    Scatters ``(theta1, theta2)`` over ``[0, 2*pi)^2`` and colours each point by
    its wrap-aware cluster label. matplotlib is imported lazily; raises
    :class:`OptionalDependencyError` when it is absent. Returns ``path`` on success.
    """
    torus_xy, labels = _torus_dataset(config)
    pyplot = _load_pyplot()
    figure, axes = pyplot.subplots(figsize=(6, 6))
    xs = [p[0] for p in torus_xy]
    ys = [p[1] for p in torus_xy]
    axes.scatter(xs, ys, c=labels, cmap="tab10", s=32, edgecolors="black", lw=0.3)
    two_pi = 2.0 * 3.141592653589793
    axes.set_xlim(0.0, two_pi)
    axes.set_ylim(0.0, two_pi)
    axes.set_xlabel("theta1 (compact circle 1; 0 and 2*pi identified)")
    axes.set_ylabel("theta2 (compact circle 2; 0 and 2*pi identified)")
    axes.set_title(
        "Compact torus factor T^2 (wrap-aware clusters) -- TOY, not a CY manifold"
    )
    figure.tight_layout()
    figure.savefig(path, dpi=120)
    pyplot.close(figure)
    return path
