"""Optional matplotlib PNG export of the Central Finite Curve projection.

DEFERRED behind the ``commons.core.optional`` matplotlib guard: with no matplotlib
installed :func:`save_projection_png` raises a clear :class:`OptionalDependencyError`
instead of failing at import time, so this module stays importable with the standard
library alone and always renders headless on the Agg backend.

The picture is the top-2 principal-component scatter of the curve with the
portal-gun walk overlaid -- the same 2-D frame the ASCII renderer draws, exported as
``central_finite_curve_projection.png``.

This is an adapter: it imports ``core`` (and, when available, the numpy accel PCA)
but is never imported by ``core``.
"""

from __future__ import annotations

from typing import Any, List, Sequence, Tuple

from commons.core.optional import try_import

from central_finite_curve.core import projection as projection_mod
from central_finite_curve.core.config import DEFAULT, CurveConfig
from central_finite_curve.core.pipeline import PipelineResult, run

Point2D = Tuple[float, float]


class OptionalDependencyError(RuntimeError):
    """Raised when an optional viz backend (matplotlib) is unavailable.

    The ASCII renderers in :mod:`central_finite_curve.adapters.render` never raise
    this; only the deferred PNG export does, and only when the caller explicitly
    requests it without the dependency.
    """


_PNG_HELP = (
    "PNG export requires matplotlib, which is not installed. Install the optional "
    "'viz' extra (pip install -e '.[viz]'), or use the ASCII renderer "
    "(central_finite_curve.adapters.render.ascii_scatter), which needs no "
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


def project_prefer_numpy(
    points: Sequence[Sequence[float]],
) -> List[Point2D]:
    """Project to 2-D using the numpy accel path when available, else pure stdlib.

    numpy is reached lazily; when it is absent (or the accel path is unavailable)
    this falls back to the deterministic pure-stdlib power-iteration PCA. Both fit
    the top-2 principal axes of ``points``.
    """
    if not points:
        return []
    np = try_import("numpy")
    if np is not None:
        from central_finite_curve.accel import numpy_backend as accel

        try:
            return accel.project_2d_numpy(points)
        except accel.OptionalDependencyError:  # pragma: no cover - numpy vanished mid-call
            pass
    return projection_mod.project_2d(points)


def project_prefer_numpy_3d(
    points: Sequence[Sequence[float]],
) -> List[Tuple[float, float, float]]:
    """Project to 3-D using the numpy accel path when available, else pure stdlib.

    numpy is reached lazily; when it is absent (or the accel path is unavailable)
    this falls back to the deterministic pure-stdlib power-iteration PCA
    (:func:`central_finite_curve.core.projection.project_3d`). Both fit the top-3
    principal axes of ``points``.
    """
    if not points:
        return []
    np = try_import("numpy")
    if np is not None:
        from central_finite_curve.accel import numpy_backend as accel

        try:
            return accel.project_3d_numpy(points)
        except accel.OptionalDependencyError:  # pragma: no cover - numpy vanished mid-call
            pass
    return projection_mod.project_3d(points)


def _projected_result(config: CurveConfig) -> PipelineResult:
    """Run the pipeline without core projection, then project via numpy if present.

    Keeps a single source of truth for the curve/walk while letting the PNG use the
    faster numpy PCA on the venv. The curve and walk share one frame (axes fit on the
    combined cloud).
    """
    result = run(config, project=False)
    if not result.curve.members:
        return result
    curve_coords = [list(u.coords) for u in result.curve.members]
    walk_coords = [list(p) for p in result.walk.points]
    proj_all = project_prefer_numpy(curve_coords + walk_coords)
    n_curve = len(curve_coords)
    return PipelineResult(
        config=result.config,
        curve=result.curve,
        walk=result.walk,
        proj_curve=proj_all[:n_curve],
        proj_walk=proj_all[n_curve:],
    )


def save_projection_png(path: str, *, config: CurveConfig = DEFAULT) -> str:
    """Render the 2-D projection scatter + walk overlay to ``path`` (matplotlib).

    Fits the top-2 principal axes on the combined curve+walk cloud, scatters the
    curve density, and overlays the portal-gun trajectory as a line. matplotlib is
    imported lazily; raises :class:`OptionalDependencyError` when it is absent.
    Returns ``path`` on success.
    """
    result = _projected_result(config)
    pyplot = _load_pyplot()
    figure, axes = pyplot.subplots(figsize=(8, 6))
    if result.proj_curve:
        cx = [p[0] for p in result.proj_curve]
        cy = [p[1] for p in result.proj_curve]
        axes.scatter(cx, cy, s=4, c="#22aa88", alpha=0.4, label="curve")
    if result.proj_walk:
        wx = [p[0] for p in result.proj_walk]
        wy = [p[1] for p in result.proj_walk]
        axes.plot(wx, wy, c="#cc3366", lw=0.7, alpha=0.8, label="portal-gun walk")
    axes.set_title(
        "Central Finite Curve (top-2 principal projection) -- "
        f"{result.curve.size} universes, accept {result.walk.acceptance_rate * 100:.1f}%"
    )
    axes.set_xlabel("PC1")
    axes.set_ylabel("PC2")
    axes.legend(loc="upper right")
    figure.tight_layout()
    figure.savefig(path, dpi=120)
    pyplot.close(figure)
    return path
