"""Animated GIF/MP4 of the portal gun walking along the Central Finite Curve.

DEFERRED behind the matplotlib + Pillow (GIF) / ffmpeg (MP4) guards, reached only
lazily through :func:`commons.core.optional.try_import`. Absent a backend each saver
raises :class:`~central_finite_curve.adapters.viz.OptionalDependencyError` instead of
failing at import time, so this module stays importable with the standard library
alone.

The scene: the curve is scattered faintly in the top-2 principal-component plane and
the portal-gun trajectory is drawn in growing as an animated trail + head, with an
on-frame readout of the step index and current Rickness -- the gun sliding ALONG the
ridge without ever falling off it.

This is an adapter: it may import ``core`` but ``core`` never imports it.
"""

from __future__ import annotations

import shutil
from typing import Any, List, Tuple

from commons.core.optional import try_import

from central_finite_curve.adapters.viz import (
    OptionalDependencyError,
    project_prefer_numpy,
)
from central_finite_curve.core.config import DEFAULT, CurveConfig
from central_finite_curve.core.pipeline import run

Point2D = Tuple[float, float]

_GIF_HELP = (
    "GIF export requires matplotlib AND Pillow, at least one of which is not "
    "installed. Install the optional 'viz' extra plus Pillow (pip install matplotlib "
    "pillow), or use the deterministic ASCII renderer, which needs no dependencies."
)

_MP4_HELP = (
    "MP4 export requires matplotlib AND an ffmpeg binary on PATH (matplotlib's "
    "FFMpegWriter shells out to it). Install ffmpeg (e.g. 'brew install ffmpeg'), or "
    "export the animation as a GIF instead (save_walk_gif), which needs only Pillow."
)

_DEFAULT_BITRATE = 1800


def _load_backends() -> Tuple[Any, Any]:
    """Return ``(pyplot, animation)`` on headless Agg (needs Pillow too), or raise."""
    matplotlib = try_import("matplotlib")
    if matplotlib is None:
        raise OptionalDependencyError(_GIF_HELP)
    matplotlib.use("Agg")  # headless, deterministic, no display needed
    pyplot = try_import("matplotlib.pyplot")
    animation = try_import("matplotlib.animation")
    pil = try_import("PIL")  # PillowWriter needs Pillow to encode GIF frames
    if pyplot is None or animation is None or pil is None:
        raise OptionalDependencyError(_GIF_HELP)
    return pyplot, animation


def ffmpeg_is_available() -> bool:
    """Return ``True`` iff an ffmpeg MP4 writer can actually be used.

    Requires both an ffmpeg binary on ``PATH`` (probed with :func:`shutil.which`, so
    it is trivially monkeypatchable in tests) AND matplotlib's registered ``ffmpeg``
    writer. Never raises: a pure capability probe.
    """
    if shutil.which("ffmpeg") is None:
        return False
    animation = try_import("matplotlib.animation")
    if animation is None:
        return False
    return bool(animation.writers.is_available("ffmpeg"))


def _sample_indices(count: int, frames: int) -> List[int]:
    """Return ``frames`` evenly spaced indices into a sequence of length ``count``."""
    if count < 1:
        raise ValueError("count must be >= 1")
    if frames < 1:
        raise ValueError("frames must be >= 1")
    if frames >= count:
        return list(range(count))
    last = count - 1
    return [round(i * last / (frames - 1)) for i in range(frames)]


def _build_walk_animation(config: CurveConfig, frames: int) -> Tuple[Any, Any, Any, Any]:
    """Build the walk :class:`FuncAnimation` shared by the GIF/MP4 savers.

    Runs the pipeline (no core projection), projects the combined curve+walk cloud to
    2-D via the numpy-preferring PCA, lays out the figure and wires the per-frame
    ``update`` closure. Raises :class:`ValueError` for ``frames < 1`` and
    :class:`OptionalDependencyError` when matplotlib/Pillow are absent.
    """
    if frames < 1:
        raise ValueError("frames must be >= 1")
    result = run(config, project=False)
    curve_coords = [list(u.coords) for u in result.curve.members]
    walk_coords = [list(p) for p in result.walk.points]
    proj_all = project_prefer_numpy(curve_coords + walk_coords)
    n_curve = len(curve_coords)
    proj_curve = proj_all[:n_curve]
    proj_walk = proj_all[n_curve:]
    if not proj_walk:
        raise ValueError("the walk produced no points to animate")
    scores = result.walk.scores

    pyplot, animation = _load_backends()
    figure, axes = pyplot.subplots(figsize=(8, 6))
    if proj_curve:
        cx = [p[0] for p in proj_curve]
        cy = [p[1] for p in proj_curve]
        axes.scatter(cx, cy, s=4, c="#22aa88", alpha=0.25, label="curve")
    all_pts = proj_curve + proj_walk
    xs = [p[0] for p in all_pts]
    ys = [p[1] for p in all_pts]
    pad = 0.05 * (max(xs) - min(xs) or 1.0)
    axes.set_xlim(min(xs) - pad, max(xs) + pad)
    axes.set_ylim(min(ys) - pad, max(ys) + pad)
    axes.set_title("Portal gun walking along the Central Finite Curve")
    axes.set_xlabel("PC1")
    axes.set_ylabel("PC2")

    wx = [p[0] for p in proj_walk]
    wy = [p[1] for p in proj_walk]
    idx = _sample_indices(len(proj_walk), frames)
    (trail,) = axes.plot([], [], linewidth=1.0, color="#cc3366", alpha=0.8)
    (head,) = axes.plot([], [], marker="o", color="#cc3366")
    readout = axes.text(
        0.02, 0.97, "", transform=axes.transAxes, va="top", ha="left", fontsize=9
    )

    def update(frame: int) -> Tuple[Any, Any, Any]:
        k = idx[frame]
        trail.set_data(wx[: k + 1], wy[: k + 1])
        head.set_data([wx[k]], [wy[k]])
        readout.set_text(f"step = {k}\nRickness = {scores[k]:.4f}")
        return trail, head, readout

    anim = animation.FuncAnimation(figure, update, frames=len(idx), blit=False)
    return pyplot, animation, figure, anim


def save_walk_gif(
    path: str,
    *,
    config: CurveConfig = DEFAULT,
    frames: int = 60,
    fps: int = 20,
) -> str:
    """Animate the portal gun sliding along the curve to ``path`` (GIF).

    matplotlib + Pillow are imported lazily; raises :class:`OptionalDependencyError`
    when either is absent. Returns ``path`` on success.
    """
    if fps < 1:
        raise ValueError("fps must be >= 1")
    pyplot, animation, figure, anim = _build_walk_animation(config, frames)
    anim.save(path, writer=animation.PillowWriter(fps=fps))
    pyplot.close(figure)
    return path


def save_walk_mp4(
    path: str,
    *,
    config: CurveConfig = DEFAULT,
    frames: int = 60,
    fps: int = 20,
    bitrate: int = _DEFAULT_BITRATE,
) -> str:
    """Encode the walk animation as an MP4 at ``path`` (ffmpeg).

    Reuses the exact :func:`save_walk_gif` scene but writes it with
    :class:`matplotlib.animation.FFMpegWriter`. matplotlib is imported lazily and
    ffmpeg availability is checked at call time; raises
    :class:`OptionalDependencyError` when matplotlib or an ffmpeg binary is absent.
    Returns ``path`` on success.
    """
    if fps < 1:
        raise ValueError("fps must be >= 1")
    if not ffmpeg_is_available():  # fail fast, before building the scene
        raise OptionalDependencyError(_MP4_HELP)
    pyplot, animation, figure, anim = _build_walk_animation(config, frames)
    writer = animation.FFMpegWriter(fps=fps, bitrate=bitrate)
    anim.save(path, writer=writer)
    pyplot.close(figure)
    return path
