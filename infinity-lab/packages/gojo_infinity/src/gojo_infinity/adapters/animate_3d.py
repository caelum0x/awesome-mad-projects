"""Rotating 3-D geodesic-approach animation (DEFERRED behind matplotlib + PIL/ffmpeg).

A companion to :mod:`gojo_infinity.adapters.animate` that renders the Lens 3
geodesics as a *rotating* three-dimensional scene: a few conformal geodesics bend
around Gojo in ``R^3`` (via :class:`gojo_infinity.core.ConformalMetricND`, Gojo at
the origin) while the CAMERA orbits -- the azimuth advances every frame and the
elevation sweeps gently -- so the viewer flies around the scene as the geodesics
progress and slow near the barrier.

    * :func:`save_geodesic_3d_rotating_gif` -- ``FuncAnimation`` + ``PillowWriter``
      (needs matplotlib AND Pillow).
    * :func:`save_geodesic_3d_rotating_mp4` -- the SAME scene through
      :class:`matplotlib.animation.FFMpegWriter` (needs matplotlib AND ffmpeg).

Like its sibling this is an adapter: it may import ``core`` but ``core`` never
imports it, and matplotlib/Pillow/ffmpeg are reached ONLY lazily (through the
shared helpers in :mod:`gojo_infinity.adapters.animate`). Absent a dependency the
renderers raise :class:`OptionalDependencyError` rather than failing at import
time, so this module stays importable with the standard library alone.
"""

from __future__ import annotations

import math
from typing import Any, List, Sequence, Tuple

from gojo_infinity.adapters.animate import (
    _DEFAULT_BITRATE,
    _MP4_HELP,
    _ffmpeg_writer,
    _load_backends,
    _sample_indices,
    ffmpeg_is_available,
)
from gojo_infinity.adapters.viz import OptionalDependencyError
from gojo_infinity.core import ConformalMetricND

Vec3 = Tuple[float, float, float]
Offset = Tuple[float, float]
Trajectory = Tuple[List[float], List[float], List[float]]

# Transverse (y0, z0) launch offsets for the geodesic bundle; each ray starts at
# (x_start, y0, z0) heading in +x and bends toward Gojo at the origin.
_DEFAULT_OFFSETS: Tuple[Offset, ...] = (
    (0.5, 0.0), (0.0, 0.5), (0.5, 0.5), (-0.6, 0.3), (0.3, -0.6),
)


def _rotating_geodesics(
    metric: ConformalMetricND,
    offsets: Sequence[Offset],
    *,
    x_start: float,
    dtau: float,
    max_steps: int,
) -> List[Trajectory]:
    """Integrate one 3-D geodesic per offset and return their ``(xs, ys, zs)`` paths."""
    trajectories: List[Trajectory] = []
    for y0, z0 in offsets:
        res = metric.integrate_geodesic(
            (x_start, y0, z0), (1.0, 0.0, 0.0),
            dtau=dtau, max_steps=max_steps, min_radius=1e-3,
        )
        xs = [p[0] for p in res.points]
        ys = [p[1] for p in res.points]
        zs = [p[2] for p in res.points]
        trajectories.append((xs, ys, zs))
    return trajectories


def _build_rotating_3d_animation(
    *,
    offsets: Sequence[Offset],
    x_start: float,
    dtau: float,
    max_steps: int,
    frames: int,
    azim_per_frame: float,
    elev_base: float,
    elev_amplitude: float,
    elev_cycles: float,
) -> Tuple[Any, Any, Any, Any]:
    """Build the rotating 3-D :class:`FuncAnimation` (shared by the GIF/MP4 savers).

    Integrates the geodesic bundle, lays out an ``mpl_toolkits.mplot3d`` scene and
    wires a per-frame ``update`` that both grows the trails and advances the camera
    (``ax.view_init``). Returns ``(pyplot, animation, figure, anim)`` so the caller
    picks the writer. Raises :class:`ValueError` for ``frames < 1`` and
    :class:`OptionalDependencyError` when matplotlib/Pillow are absent.
    """
    if frames < 1:
        raise ValueError("frames must be >= 1")
    if len(offsets) < 1:
        raise ValueError("offsets must be non-empty")

    metric = ConformalMetricND()  # Gojo at the origin of R^3
    trajectories = _rotating_geodesics(
        metric, offsets, x_start=x_start, dtau=dtau, max_steps=max_steps
    )
    per_traj_idx = [_sample_indices(len(xs), frames) for xs, _, _ in trajectories]

    pyplot, animation = _load_backends()
    # Importing pyplot registers the 3-D projection; request it explicitly.
    figure = pyplot.figure()
    axes = figure.add_subplot(111, projection="3d")

    all_x = [v for xs, _, _ in trajectories for v in xs]
    all_y = [v for _, ys, _ in trajectories for v in ys]
    all_z = [v for _, _, zs in trajectories for v in zs]
    pad = 0.3
    axes.set_xlim(min(all_x) - pad, max(all_x) + pad)
    axes.set_ylim(min(all_y) - pad, max(all_y) + pad)
    axes.set_zlim(min(all_z) - pad, max(all_z) + pad)
    axes.scatter([0.0], [0.0], [0.0], marker="*", s=180, color="black", label="Gojo")
    axes.set_title("Lens 3 (3-D) -- orbiting geodesics bending around Gojo")
    axes.set_xlabel("x")
    axes.set_ylabel("y")
    axes.set_zlabel("z")

    lines: List[Any] = []
    heads: List[Any] = []
    for _ in trajectories:
        (line,) = axes.plot([], [], [], linewidth=1.4)
        (head,) = axes.plot([], [], [], marker="o", markersize=5, color="tab:red")
        lines.append(line)
        heads.append(head)
    readout = axes.text2D(
        0.02, 0.95, "", transform=axes.transAxes, va="top", ha="left", fontsize=9
    )

    def update(frame: int) -> Tuple[Any, ...]:
        for (xs, ys, zs), idx, line, head in zip(
            trajectories, per_traj_idx, lines, heads
        ):
            k = idx[frame]
            line.set_data(xs[: k + 1], ys[: k + 1])
            line.set_3d_properties(zs[: k + 1])
            head.set_data([xs[k]], [ys[k]])
            head.set_3d_properties([zs[k]])
        azim = azim_per_frame * frame
        elev = elev_base + elev_amplitude * math.sin(
            2.0 * math.pi * elev_cycles * frame / frames
        )
        axes.view_init(elev=elev, azim=azim)
        readout.set_text(f"camera: azim = {azim % 360:.0f} deg, elev = {elev:.0f} deg")
        return (*lines, *heads, readout)

    anim = animation.FuncAnimation(figure, update, frames=frames, blit=False)
    return pyplot, animation, figure, anim


def save_geodesic_3d_rotating_gif(
    path: str,
    *,
    offsets: Sequence[Offset] = _DEFAULT_OFFSETS,
    x_start: float = -3.0,
    dtau: float = 1e-3,
    max_steps: int = 6000,
    frames: int = 72,
    fps: int = 20,
    azim_per_frame: float = 5.0,
    elev_base: float = 22.0,
    elev_amplitude: float = 12.0,
    elev_cycles: float = 1.0,
) -> str:
    """Animate orbiting 3-D geodesics bending around Gojo to a GIF at ``path``.

    A few conformal geodesics travel toward Gojo (the origin of ``R^3``) while the
    camera azimuth advances ``azim_per_frame`` degrees each frame and the elevation
    sweeps ``+/- elev_amplitude`` degrees about ``elev_base`` -- the viewer orbits
    the scene as the rays progress. Rendered with ``mpl_toolkits.mplot3d`` +
    ``PillowWriter``; matplotlib and Pillow are imported lazily, so this raises
    :class:`OptionalDependencyError` when either is absent. Returns ``path``.
    """
    if fps < 1:
        raise ValueError("fps must be >= 1")
    pyplot, animation, figure, anim = _build_rotating_3d_animation(
        offsets=offsets, x_start=x_start, dtau=dtau, max_steps=max_steps,
        frames=frames, azim_per_frame=azim_per_frame, elev_base=elev_base,
        elev_amplitude=elev_amplitude, elev_cycles=elev_cycles,
    )
    anim.save(path, writer=animation.PillowWriter(fps=fps))
    pyplot.close(figure)
    return path


def save_geodesic_3d_rotating_mp4(
    path: str,
    *,
    offsets: Sequence[Offset] = _DEFAULT_OFFSETS,
    x_start: float = -3.0,
    dtau: float = 1e-3,
    max_steps: int = 6000,
    frames: int = 72,
    fps: int = 20,
    bitrate: int = _DEFAULT_BITRATE,
    azim_per_frame: float = 5.0,
    elev_base: float = 22.0,
    elev_amplitude: float = 12.0,
    elev_cycles: float = 1.0,
) -> str:
    """Encode the rotating 3-D geodesic scene as an MP4 at ``path`` (ffmpeg).

    Reuses the exact :func:`save_geodesic_3d_rotating_gif` scene but writes it with
    :class:`matplotlib.animation.FFMpegWriter`. matplotlib is imported lazily and
    ffmpeg availability is checked at call time; raises
    :class:`OptionalDependencyError` when matplotlib or an ffmpeg binary is absent.
    Returns ``path``.
    """
    if fps < 1:
        raise ValueError("fps must be >= 1")
    if not ffmpeg_is_available():  # fail fast, before building the scene
        raise OptionalDependencyError(_MP4_HELP)
    pyplot, animation, figure, anim = _build_rotating_3d_animation(
        offsets=offsets, x_start=x_start, dtau=dtau, max_steps=max_steps,
        frames=frames, azim_per_frame=azim_per_frame, elev_base=elev_base,
        elev_amplitude=elev_amplitude, elev_cycles=elev_cycles,
    )
    writer = _ffmpeg_writer(animation, fps=fps, bitrate=bitrate)
    anim.save(path, writer=writer)
    pyplot.close(figure)
    return path
