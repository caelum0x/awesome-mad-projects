"""Animated SCMS ridge convergence in the ``(u, v)`` domain (DEFERRED behind matplotlib + PIL).

Where :mod:`mobius_rickness.adapters.animate_3d` orbits a camera over the *finished*
curves, this module animates the ridge extractor's PROCESS: a cloud of scattered
seed points migrating, one Subspace-Constrained-Mean-Shift step per frame, until it
settles onto the SCMS / Eberly crest of maximal Rickness. Each frame draws the seed
scatter at iteration ``k`` over a faint 2-D Rickness backdrop ``R(u, v)`` (with the
zero curve ``R^{-1}(0)`` as a black reference contour and the converged ridge as a
faint orange reference), and the frame title reports the iteration index and the mean
ridge-condition residual ``mean_i |g_i . e_minor_i|`` shrinking toward ``0``.

    * :func:`save_ridge_convergence_gif` -- ``FuncAnimation`` + ``PillowWriter``
      (needs matplotlib AND Pillow).
    * :func:`save_ridge_convergence_mp4` -- the SAME scene through
      :class:`matplotlib.animation.FFMpegWriter` (needs matplotlib AND ffmpeg).

Both share one :func:`_build_convergence_animation` builder. Like its siblings this
is an adapter: it may import ``core`` and the numpy-backed ``ridge`` subpackage, but
``core`` never imports it, and matplotlib/Pillow/ffmpeg and numpy are reached ONLY
lazily. Absent a dependency the renderers raise
:class:`~mobius_rickness.adapters.viz.OptionalDependencyError` rather than failing at
import time, so this module stays importable with the standard library alone.
"""

from __future__ import annotations

from typing import Any, List, Tuple

from commons.core.optional import try_import

from mobius_rickness.adapters.animate_3d import (
    _DEFAULT_BITRATE,
    _ffmpeg_writer,
    ffmpeg_is_available,
)
from mobius_rickness.adapters.viz import OptionalDependencyError
from mobius_rickness.core import (
    U_MAX,
    U_MIN,
    V_MAX,
    V_MIN,
    evaluate_grid,
    rickness,
)

_GIF_HELP = (
    "SCMS convergence GIF export requires matplotlib AND Pillow, at least one of "
    "which is not installed. Install the optional 'viz' extra plus Pillow "
    "(pip install matplotlib pillow), or use the deterministic ASCII / numeric "
    "renderers, which need no dependencies."
)

_MP4_HELP = (
    "SCMS convergence MP4 export requires matplotlib AND an ffmpeg binary on PATH "
    "(matplotlib's FFMpegWriter shells out to it). Install ffmpeg (e.g. "
    "'brew install ffmpeg' or your distro's package), or export the animation as a "
    "GIF instead (save_ridge_convergence_gif), which needs only Pillow."
)

# Default seed cloud and backdrop resolution (kept modest so each frame is quick).
_SEED_N_U = 22
_SEED_N_V = 5
_BACKDROP_N_U = 121
_BACKDROP_N_V = 41

# SCMS iteration controls for the animation (a looser tolerance than the crisp
# ridge-trace default keeps the frame count bounded while still reaching ~0).
_ANIM_TOL = 1e-8
_ANIM_MAX_ITER = 60


def _load_backends_2d() -> Tuple[Any, Any]:
    """Return ``(pyplot, animation)`` on the headless Agg backend, or raise.

    matplotlib, matplotlib.pyplot, matplotlib.animation AND Pillow are reached
    lazily via :func:`commons.core.optional.try_import` (no mplot3d -- this is a 2-D
    scene). Raises :class:`OptionalDependencyError` when any is absent; never
    silently degrades. The Agg backend keeps rendering headless and deterministic.
    """
    matplotlib = try_import("matplotlib")
    if matplotlib is None:
        raise OptionalDependencyError(_GIF_HELP)
    matplotlib.use("Agg")  # headless, deterministic, no display needed
    pyplot = try_import("matplotlib.pyplot")
    animation = try_import("matplotlib.animation")
    pil = try_import("PIL")  # PillowWriter needs Pillow to encode the GIF frames
    if pyplot is None or animation is None or pil is None:
        raise OptionalDependencyError(_GIF_HELP)
    return pyplot, animation


def _require_numpy() -> Any:
    """Return numpy for the backdrop meshes, or raise a clear deferred error."""
    numpy = try_import("numpy")
    if numpy is None:  # pragma: no cover - matplotlib depends on numpy in practice
        raise OptionalDependencyError(
            "the SCMS convergence animation requires numpy, which is not installed."
        )
    return numpy


def _build_convergence_animation(
    *,
    seed_n_u: int,
    seed_n_v: int,
    backdrop_n_u: int,
    backdrop_n_v: int,
    tol: float,
    max_iter: int,
    hold: int,
) -> Tuple[Any, Any, Any, Any]:
    """Build the SCMS-convergence :class:`FuncAnimation` (shared by GIF/MP4 savers).

    Runs the seam-aware SCMS cloud history over the Mobius Rickness field, lays out
    a 2-D ``(u, v)`` scene (faint ``R`` backdrop, the ``R^{-1}(0)`` zero contour and
    the converged ridge as references, plus the migrating seed scatter) and wires a
    per-frame ``update`` that advances the scatter to snapshot ``k`` and writes the
    iteration index and mean residual into the title. Returns
    ``(pyplot, animation, figure, anim)`` so the caller picks the writer. Raises
    :class:`ValueError` for bad arguments and :class:`OptionalDependencyError` when
    matplotlib/Pillow/numpy are absent.
    """
    if hold < 0:
        raise ValueError("hold must be >= 0")

    numpy = _require_numpy()
    # Local import: keeps the module importable with the stdlib alone (numpy-gated).
    from mobius_rickness.core.geometry import mobius_seam_wrap
    from mobius_rickness.ridge import mobius_seeds, scms_ridge_history

    seeds = mobius_seeds(n_u=seed_n_u, n_v=seed_n_v)
    history = scms_ridge_history(
        rickness,
        seeds,
        wrap=mobius_seam_wrap,
        tol=tol,
        max_iter=max_iter,
        v_bounds=(V_MIN, V_MAX),
    )
    snapshots = history.snapshots
    residuals = history.residuals
    # Final crest points (kept exactly as scms_ridge would): a faint reference.
    kept = [p for p in history.points if p.converged and p.minor_eigval < 0.0]

    pyplot, animation = _load_backends_2d()

    grid = evaluate_grid(n_u=backdrop_n_u, n_v=backdrop_n_v)
    mesh_u, mesh_v = numpy.meshgrid(numpy.asarray(grid.us), numpy.asarray(grid.vs))
    r_field = numpy.asarray(grid.R)

    figure, axes = pyplot.subplots(figsize=(8, 4))
    axes.pcolormesh(
        mesh_u, mesh_v, r_field, cmap="RdBu", shading="auto", alpha=0.45
    )
    contour = axes.contour(mesh_u, mesh_v, r_field, levels=[0.0], colors="black")
    axes.clabel(contour, inline=True, fontsize=7, fmt="R=0")
    if kept:
        axes.scatter(
            [p.u for p in kept],
            [p.v for p in kept],
            s=14,
            color="darkorange",
            alpha=0.35,
            marker="x",
            label="converged SCMS ridge",
        )
    (scat,) = axes.plot(
        [], [], linestyle="none", marker="o", markersize=5,
        color="tab:green", label="migrating seeds",
    )
    axes.set_xlim(U_MIN, U_MAX)
    axes.set_ylim(V_MIN, V_MAX)
    axes.set_xlabel("u")
    axes.set_ylabel("v")
    axes.legend(loc="upper right", fontsize=8)

    # Repeat the settled final frame a few times so the GIF visibly "lands".
    n_snap = len(snapshots)
    frame_order: List[int] = list(range(n_snap)) + [n_snap - 1] * hold

    def update(frame: int) -> Tuple[Any, ...]:
        k = frame_order[frame]
        snap = snapshots[k]
        scat.set_data(snap[:, 0], snap[:, 1])
        axes.set_title(
            f"SCMS ridge convergence -- iteration {k}/{n_snap - 1}   "
            f"mean |grad . e_minor| = {residuals[k]:.2e}"
        )
        return (scat,)

    anim = animation.FuncAnimation(
        figure, update, frames=len(frame_order), blit=False
    )
    return pyplot, animation, figure, anim


def save_ridge_convergence_gif(
    path: str,
    *,
    seed_n_u: int = _SEED_N_U,
    seed_n_v: int = _SEED_N_V,
    backdrop_n_u: int = _BACKDROP_N_U,
    backdrop_n_v: int = _BACKDROP_N_V,
    tol: float = _ANIM_TOL,
    max_iter: int = _ANIM_MAX_ITER,
    hold: int = 8,
    fps: int = 10,
) -> str:
    """Animate the SCMS seed cloud settling onto the Rickness ridge to a GIF at ``path``.

    A scatter of Mobius-domain seeds migrates one SCMS step per frame over a faint
    ``R(u, v)`` backdrop (with the ``R^{-1}(0)`` zero curve and the converged ridge
    as references); the frame title shows the iteration index and the mean ridge
    residual shrinking toward ``0``. Rendered with ``FuncAnimation`` + ``PillowWriter``;
    matplotlib and Pillow are imported lazily, so this raises
    :class:`OptionalDependencyError` when either is absent. Returns ``path``.
    """
    if fps < 1:
        raise ValueError("fps must be >= 1")
    pyplot, animation, figure, anim = _build_convergence_animation(
        seed_n_u=seed_n_u, seed_n_v=seed_n_v,
        backdrop_n_u=backdrop_n_u, backdrop_n_v=backdrop_n_v,
        tol=tol, max_iter=max_iter, hold=hold,
    )
    anim.save(path, writer=animation.PillowWriter(fps=fps))
    pyplot.close(figure)
    return path


def save_ridge_convergence_mp4(
    path: str,
    *,
    seed_n_u: int = _SEED_N_U,
    seed_n_v: int = _SEED_N_V,
    backdrop_n_u: int = _BACKDROP_N_U,
    backdrop_n_v: int = _BACKDROP_N_V,
    tol: float = _ANIM_TOL,
    max_iter: int = _ANIM_MAX_ITER,
    hold: int = 8,
    fps: int = 10,
    bitrate: int = _DEFAULT_BITRATE,
) -> str:
    """Encode the SCMS ridge-convergence scene as an MP4 at ``path`` (ffmpeg).

    Reuses the exact :func:`save_ridge_convergence_gif` scene but writes it with
    :class:`matplotlib.animation.FFMpegWriter`. matplotlib is imported lazily and
    ffmpeg availability is checked at call time (via
    :func:`mobius_rickness.adapters.animate_3d.ffmpeg_is_available`); raises
    :class:`OptionalDependencyError` when matplotlib or an ffmpeg binary is absent.
    Returns ``path``.
    """
    if fps < 1:
        raise ValueError("fps must be >= 1")
    if not ffmpeg_is_available():  # fail fast, before building the scene
        raise OptionalDependencyError(_MP4_HELP)
    pyplot, animation, figure, anim = _build_convergence_animation(
        seed_n_u=seed_n_u, seed_n_v=seed_n_v,
        backdrop_n_u=backdrop_n_u, backdrop_n_v=backdrop_n_v,
        tol=tol, max_iter=max_iter, hold=hold,
    )
    writer = _ffmpeg_writer(animation, fps=fps, bitrate=bitrate)
    anim.save(path, writer=writer)
    pyplot.close(figure)
    return path
