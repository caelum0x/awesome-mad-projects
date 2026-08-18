"""Optional matplotlib PNG export of a solved domain field and a clash.

DEFERRED behind the ``commons.core.optional`` matplotlib guard: with no
matplotlib installed :func:`save_field_png` raises a clear
:class:`OptionalDependencyError` instead of failing at import time, so this
module stays importable with the standard library alone and always renders
headless on the Agg backend.

The picture is a 1x2 panel: the solved refined-domain field, and the crude-vs-
refined clash's merged field (the contested interior overwritten by the winner)
-- the same fields the ASCII renderer draws, exported as
``domain_expansion_field.png``.

This is an adapter: it imports ``core`` but is never imported by ``core``.
"""

from __future__ import annotations

from typing import Any, List

from commons.core.optional import try_import

from domain_expansion.core import scenarios
from domain_expansion.core.clash import clash
from domain_expansion.core.domain import Grid, solve_domain


class OptionalDependencyError(RuntimeError):
    """Raised when an optional viz backend (matplotlib) is unavailable.

    The ASCII renderers in :mod:`domain_expansion.adapters.render` never raise
    this; only the deferred PNG export does, and only when the caller explicitly
    requests it without the dependency.
    """


_PNG_HELP = (
    "PNG export requires matplotlib, which is not installed. Install the optional "
    "'viz' extra (pip install -e '.[viz]'), or use the ASCII renderer "
    "(domain_expansion.adapters.render.field_heatmap), which needs no dependencies."
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


def _to_imshow(field: Grid) -> List[List[float]]:
    """Return ``field`` (``[i=x][j=y]``) as row-major ``rows[y][x]`` with y up.

    ``imshow`` draws row 0 at the top by default, so we reverse the y order to put
    the largest ``y`` on top, matching the ASCII / numeric views.
    """
    nx = len(field)
    ny = len(field[0])
    return [[field[i][j] for i in range(nx)] for j in range(ny - 1, -1, -1)]


def save_field_png(path: str) -> str:
    """Render the refined field and the clash merged field to ``path`` (matplotlib).

    matplotlib is imported lazily; raises :class:`OptionalDependencyError` when it
    is absent. Returns ``path`` on success.
    """
    refined = scenarios.make_refined_domain()
    crude = scenarios.make_crude_domain()
    refined_result = solve_domain(refined)
    clash_result = clash(crude, refined)

    pyplot = _load_pyplot()
    figure, axes = pyplot.subplots(1, 2, figsize=(11, 5))

    im0 = axes[0].imshow(
        _to_imshow(refined_result.field), cmap="inferno", origin="upper"
    )
    axes[0].set_title(
        f"Refined Domain field\nrigidity={refined_result.rigidity:.2f}, "
        f"residual_L2={refined_result.residual_l2:.1e}"
    )
    axes[0].set_xlabel("x")
    axes[0].set_ylabel("y")
    figure.colorbar(im0, ax=axes[0], fraction=0.046, pad=0.04)

    im1 = axes[1].imshow(
        _to_imshow(clash_result.merged_field), cmap="inferno", origin="upper"
    )
    axes[1].set_title(
        f"Clash merged field\nwinner: {clash_result.winner} overwrites interior"
    )
    axes[1].set_xlabel("x")
    axes[1].set_ylabel("y")
    figure.colorbar(im1, ax=axes[1], fraction=0.046, pad=0.04)

    figure.suptitle("Domain Expansion :: coupled constraint solver")
    figure.tight_layout()
    figure.savefig(path, dpi=120)
    pyplot.close(figure)
    return path
