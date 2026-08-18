"""Optional matplotlib PNG export of the p-adic distance matrix (heatmap).

DEFERRED behind the :func:`commons.core.optional.try_import` matplotlib guard: with
no matplotlib installed :func:`save_distance_matrix_png` raises a clear
:class:`OptionalDependencyError` instead of failing at import time, so this module
stays importable with the standard library alone and always renders headless on the
Agg backend.

The picture is the pairwise p-adic distance matrix drawn as a labelled heatmap --
the same structure the ASCII renderer prints -- exported as
``padic_embeddings_distance_matrix.png``.

This is an adapter: it imports ``core`` but is never imported by ``core``; matplotlib
is reached only lazily.
"""

from __future__ import annotations

from typing import Any, List, Optional, Sequence

from commons.core.optional import try_import

from padic_embeddings.core import embedding

# Canonical artifact filename (mirrors the repo's artifacts/ naming convention).
DISTANCE_MATRIX_PNG = "padic_embeddings_distance_matrix.png"


class OptionalDependencyError(RuntimeError):
    """Raised when the optional viz backend (matplotlib) is unavailable.

    The ASCII renderers in :mod:`padic_embeddings.adapters.render` never raise this;
    only the deferred PNG export does, and only when the caller explicitly requests
    it without the dependency.
    """


_PNG_HELP = (
    "PNG export requires matplotlib, which is not installed. Install the optional "
    "'viz' extra (pip install -e '.[viz]'), or use the ASCII renderer "
    "(padic_embeddings.adapters.render.distance_heatmap), which needs no "
    "dependencies."
)


def _load_pyplot() -> Any:
    """Return ``matplotlib.pyplot`` bound to the headless Agg backend, or raise."""
    matplotlib = try_import("matplotlib")
    if matplotlib is None:
        raise OptionalDependencyError(_PNG_HELP)
    matplotlib.use("Agg")  # headless, deterministic, no display needed
    pyplot = try_import("matplotlib.pyplot")
    if pyplot is None:  # pragma: no cover - matplotlib without pyplot is degenerate
        raise OptionalDependencyError("matplotlib is present but pyplot is unavailable")
    return pyplot


def save_distance_matrix_png(
    path: str,
    coords: Sequence[int],
    p: int,
    *,
    labels: Optional[Sequence[str]] = None,
) -> str:
    """Render the ``p``-adic distance matrix of ``coords`` to ``path`` as a heatmap.

    matplotlib is imported lazily; raises :class:`OptionalDependencyError` when it is
    absent. Cells are annotated with their distance and axes are labelled with the
    items (their string form by default). Returns ``path`` on success. Raises
    :class:`ValueError` for an empty ``coords`` or a ``labels`` length mismatch.
    """
    if not coords:
        raise ValueError("coords must be non-empty")
    if labels is None:
        labels = [str(c) for c in coords]
    if len(labels) != len(coords):
        raise ValueError("labels length must match coords length")

    matrix: List[List[float]] = embedding.distance_matrix(coords, p)
    pyplot = _load_pyplot()
    n = len(coords)
    figure, axes = pyplot.subplots(figsize=(1.1 * n + 2, 1.1 * n + 2))
    image = axes.imshow(matrix, cmap="viridis", vmin=0.0, vmax=1.0)
    axes.set_xticks(range(n))
    axes.set_yticks(range(n))
    axes.set_xticklabels(labels, rotation=45, ha="right")
    axes.set_yticklabels(labels)
    for i in range(n):
        for j in range(n):
            axes.text(
                j, i, f"{matrix[i][j]:.3f}",
                ha="center", va="center", color="white", fontsize=7,
            )
    axes.set_title(f"{p}-adic distance matrix  d_p(a,b) = |a-b|_p")
    figure.colorbar(image, ax=axes, label="p-adic distance")
    figure.tight_layout()
    figure.savefig(path, dpi=120)
    pyplot.close(figure)
    return path
