"""Rotating 3-D animation of the Mobius strip with BOTH Central Finite Curve readings.

A companion to :mod:`mobius_rickness.adapters.viz` that renders the Mobius strip as
a *rotating* three-dimensional scene: the semi-transparent strip surface carries two
distinct overlaid curves while the CAMERA orbits (the azimuth advances every frame and
the elevation sweeps gently via ``ax.view_init``), so the viewer flies around the scene:

    * the traced **Central Finite Curve** ``R^{-1}(0)`` -- the sign-changing wall of the
      Rickness field, from :mod:`mobius_rickness.core.tracer` (one colour); and
    * the **SCMS / Eberly ridge** of maximal Rickness -- the complementary crest, from
      :mod:`mobius_rickness.ridge.trace_mobius_ridge` (a distinct colour).

Two savers share ONE builder (:func:`_build_rotating_animation`):

    * :func:`save_mobius_rotating_gif` -- ``FuncAnimation`` + ``PillowWriter`` (needs
      matplotlib AND Pillow).
    * :func:`save_mobius_rotating_mp4` -- the SAME scene through
      :class:`matplotlib.animation.FFMpegWriter` (needs matplotlib AND ffmpeg).

Like its siblings this is an adapter: it may import ``core`` (and the numpy-backed
``ridge`` subpackage) but ``core`` never imports it, and matplotlib/Pillow/ffmpeg and
numpy are reached ONLY lazily (through :func:`commons.core.optional.try_import` and the
shared helpers in :mod:`mobius_rickness.adapters.viz`). Absent a dependency the
renderers raise :class:`OptionalDependencyError` rather than failing at import time, so
this module stays importable with the standard library alone.

The ridge overlay degrades gracefully: when numpy (or the ridge subpackage) is
unavailable the strip surface and the ``R^{-1}(0)`` zero curve still render and the
ridge is simply omitted -- the animation never fails just because numpy is absent.
"""

from __future__ import annotations

import math
import shutil
from typing import Any, List, Sequence, Tuple

from commons.core.optional import try_import

from mobius_rickness.adapters.viz import (
    OptionalDependencyError,
    _surface_grids,
    _traced_cfc_points,
    _try_trace_ridge,
)

_GIF_HELP = (
    "Rotating GIF export requires matplotlib AND Pillow, at least one of which is "
    "not installed. Install the optional 'viz' extra plus Pillow "
    "(pip install matplotlib pillow), or use the deterministic ASCII / numeric "
    "renderers, which need no dependencies."
)

_MP4_HELP = (
    "Rotating MP4 export requires matplotlib AND an ffmpeg binary on PATH "
    "(matplotlib's FFMpegWriter shells out to it). Install ffmpeg (e.g. "
    "'brew install ffmpeg' or your distro's package), or export the animation as a "
    "GIF instead (save_mobius_rotating_gif), which needs only Pillow."
)

# A reasonable default video bitrate (kbit/s) for the short, schematic scene.
_DEFAULT_BITRATE = 1800

# Default surface sampling for the animated strip (a touch coarser than the PNG
# exports so each frame renders quickly).
_ANIM_N_U = 90
_ANIM_N_V = 19

# Default trace densities for the two overlaid curves.
_CFC_N_U = 120
_CFC_N_V_SAMPLES = 200
_RIDGE_N_U = 24
_RIDGE_N_V = 5


def _load_backends() -> Tuple[Any, Any]:
    """Return ``(pyplot, animation)`` on the headless Agg backend, or raise.

    matplotlib, matplotlib.pyplot, matplotlib.animation, mplot3d AND Pillow are all
    reached lazily via :func:`commons.core.optional.try_import`. If any is absent this
    raises :class:`OptionalDependencyError` (deferred behaviour); it never silently
    degrades. The Agg backend keeps rendering headless and deterministic.
    """
    matplotlib = try_import("matplotlib")
    if matplotlib is None:
        raise OptionalDependencyError(_GIF_HELP)
    matplotlib.use("Agg")  # headless, deterministic, no display needed
    pyplot = try_import("matplotlib.pyplot")
    animation = try_import("matplotlib.animation")
    pil = try_import("PIL")  # PillowWriter needs Pillow to encode the GIF frames
    mplot3d = try_import("mpl_toolkits.mplot3d")  # registers the 3-D projection
    if pyplot is None or animation is None or pil is None or mplot3d is None:
        raise OptionalDependencyError(_GIF_HELP)
    return pyplot, animation


def _load_animation_backend() -> Any:
    """Return ``matplotlib.animation`` on the headless Agg backend, or raise.

    Like :func:`_load_backends` but WITHOUT the Pillow requirement -- the MP4 exporter
    does not encode through Pillow. Raises :class:`OptionalDependencyError` when
    matplotlib itself is absent.
    """
    matplotlib = try_import("matplotlib")
    if matplotlib is None:
        raise OptionalDependencyError(_MP4_HELP)
    matplotlib.use("Agg")  # headless, deterministic, no display needed
    animation = try_import("matplotlib.animation")
    if animation is None:  # pragma: no cover - matplotlib without animation is degenerate
        raise OptionalDependencyError(_MP4_HELP)
    return animation


def ffmpeg_is_available() -> bool:
    """Return ``True`` iff an ffmpeg MP4 writer can actually be used.

    Both an ffmpeg binary on ``PATH`` (probed with :func:`shutil.which`, so it is
    trivially monkeypatchable in tests) AND matplotlib's registered ``ffmpeg`` writer
    must be present. Never raises: it is a pure capability probe.
    """
    if shutil.which("ffmpeg") is None:
        return False
    animation = try_import("matplotlib.animation")
    if animation is None:
        return False
    return bool(animation.writers.is_available("ffmpeg"))


def _ffmpeg_writer(animation: Any, *, fps: int, bitrate: int) -> Any:
    """Return a configured :class:`matplotlib.animation.FFMpegWriter`, or raise.

    Raises :class:`OptionalDependencyError` (deferred behaviour) when ffmpeg is
    unavailable, and :class:`ValueError` for a non-positive ``fps``.
    """
    if fps < 1:
        raise ValueError("fps must be >= 1")
    if not ffmpeg_is_available():
        raise OptionalDependencyError(_MP4_HELP)
    return animation.FFMpegWriter(fps=fps, bitrate=bitrate)


def _plot_curve(axes: Any, points: Sequence, *, color: str, label: str, **kwargs: Any) -> None:
    """Overlay a lifted 3-D curve (objects with ``.x/.y/.z``) as a line on ``axes``."""
    if not points:
        return
    axes.plot(
        [p.x for p in points],
        [p.y for p in points],
        [p.z for p in points],
        color=color,
        label=label,
        **kwargs,
    )


def _build_rotating_animation(
    *,
    n_u_surface: int,
    n_v_surface: int,
    cfc_n_u: int,
    cfc_n_v_samples: int,
    ridge_n_u: int,
    ridge_n_v: int,
    frames: int,
    azim_per_frame: float,
    elev_base: float,
    elev_amplitude: float,
    elev_cycles: float,
) -> Tuple[Any, Any, Any, Any]:
    """Build the rotating 3-D :class:`FuncAnimation` (shared by the GIF/MP4 savers).

    Lays out an ``mpl_toolkits.mplot3d`` scene: the semi-transparent Mobius strip
    surface, the traced ``R^{-1}(0)`` zero curve and (when numpy is available) the SCMS
    ridge, then wires a per-frame ``update`` that advances the camera (``ax.view_init``)
    so the whole scene orbits. Returns ``(pyplot, animation, figure, anim)`` so the
    caller picks the writer. Raises :class:`ValueError` for ``frames < 1`` and
    :class:`OptionalDependencyError` when matplotlib/Pillow are absent.
    """
    if frames < 1:
        raise ValueError("frames must be >= 1")

    grid_x, grid_y, grid_z = _surface_grids(n_u_surface, n_v_surface)
    cfc_points = _traced_cfc_points(n_u=cfc_n_u, n_v_samples=cfc_n_v_samples)
    # Degrades gracefully: [] when numpy / the ridge subpackage is unavailable.
    ridge_points = _try_trace_ridge(ridge_n_u, ridge_n_v)

    pyplot, animation = _load_backends()
    figure = pyplot.figure(figsize=(7, 6))
    axes = figure.add_subplot(111, projection="3d")
    axes.plot_surface(grid_x, grid_y, grid_z, alpha=0.3, color="gray", linewidth=0)
    _plot_curve(
        axes, cfc_points,
        color="red", label="Central Finite Curve R^-1(0)", linewidth=2.0,
    )
    _plot_curve(
        axes, ridge_points,
        color="darkorange", label="SCMS ridge (max Rickness)",
        linewidth=2.0, marker="o", markersize=3,
    )
    if cfc_points or ridge_points:
        axes.legend(loc="upper right", fontsize=8)
    axes.set_title("Mobius strip -- orbiting camera over both Central Finite Curves")
    axes.set_xlabel("x")
    axes.set_ylabel("y")
    axes.set_zlabel("z")
    readout = axes.text2D(
        0.02, 0.95, "", transform=axes.transAxes, va="top", ha="left", fontsize=9
    )

    def update(frame: int) -> Tuple[Any, ...]:
        azim = azim_per_frame * frame
        elev = elev_base + elev_amplitude * math.sin(
            2.0 * math.pi * elev_cycles * frame / frames
        )
        axes.view_init(elev=elev, azim=azim)
        readout.set_text(f"camera: azim = {azim % 360:.0f} deg, elev = {elev:.0f} deg")
        return (readout,)

    anim = animation.FuncAnimation(figure, update, frames=frames, blit=False)
    return pyplot, animation, figure, anim


def save_mobius_rotating_gif(
    path: str,
    *,
    n_u_surface: int = _ANIM_N_U,
    n_v_surface: int = _ANIM_N_V,
    cfc_n_u: int = _CFC_N_U,
    cfc_n_v_samples: int = _CFC_N_V_SAMPLES,
    ridge_n_u: int = _RIDGE_N_U,
    ridge_n_v: int = _RIDGE_N_V,
    frames: int = 72,
    fps: int = 20,
    azim_per_frame: float = 5.0,
    elev_base: float = 24.0,
    elev_amplitude: float = 12.0,
    elev_cycles: float = 1.0,
) -> str:
    """Animate the Mobius strip with both CFC readings under an orbiting camera to a GIF.

    The semi-transparent strip carries the traced ``R^{-1}(0)`` zero curve (red) and the
    SCMS ridge of maximal Rickness (orange) while the camera azimuth advances
    ``azim_per_frame`` degrees each frame and the elevation sweeps ``+/- elev_amplitude``
    degrees about ``elev_base``. Rendered with ``mpl_toolkits.mplot3d`` + ``PillowWriter``;
    matplotlib and Pillow are imported lazily, so this raises
    :class:`OptionalDependencyError` when either is absent. When numpy is unavailable the
    ridge is omitted and the strip + zero curve still render. Returns ``path``.
    """
    if fps < 1:
        raise ValueError("fps must be >= 1")
    pyplot, animation, figure, anim = _build_rotating_animation(
        n_u_surface=n_u_surface, n_v_surface=n_v_surface,
        cfc_n_u=cfc_n_u, cfc_n_v_samples=cfc_n_v_samples,
        ridge_n_u=ridge_n_u, ridge_n_v=ridge_n_v,
        frames=frames, azim_per_frame=azim_per_frame, elev_base=elev_base,
        elev_amplitude=elev_amplitude, elev_cycles=elev_cycles,
    )
    anim.save(path, writer=animation.PillowWriter(fps=fps))
    pyplot.close(figure)
    return path


def save_mobius_rotating_mp4(
    path: str,
    *,
    n_u_surface: int = _ANIM_N_U,
    n_v_surface: int = _ANIM_N_V,
    cfc_n_u: int = _CFC_N_U,
    cfc_n_v_samples: int = _CFC_N_V_SAMPLES,
    ridge_n_u: int = _RIDGE_N_U,
    ridge_n_v: int = _RIDGE_N_V,
    frames: int = 72,
    fps: int = 20,
    bitrate: int = _DEFAULT_BITRATE,
    azim_per_frame: float = 5.0,
    elev_base: float = 24.0,
    elev_amplitude: float = 12.0,
    elev_cycles: float = 1.0,
) -> str:
    """Encode the rotating Mobius scene as an MP4 at ``path`` (ffmpeg).

    Reuses the exact :func:`save_mobius_rotating_gif` scene but writes it with
    :class:`matplotlib.animation.FFMpegWriter`. matplotlib is imported lazily and ffmpeg
    availability is checked at call time; raises :class:`OptionalDependencyError` when
    matplotlib or an ffmpeg binary is absent. Returns ``path``.
    """
    if fps < 1:
        raise ValueError("fps must be >= 1")
    if not ffmpeg_is_available():  # fail fast, before building the scene
        raise OptionalDependencyError(_MP4_HELP)
    pyplot, animation, figure, anim = _build_rotating_animation(
        n_u_surface=n_u_surface, n_v_surface=n_v_surface,
        cfc_n_u=cfc_n_u, cfc_n_v_samples=cfc_n_v_samples,
        ridge_n_u=ridge_n_u, ridge_n_v=ridge_n_v,
        frames=frames, azim_per_frame=azim_per_frame, elev_base=elev_base,
        elev_amplitude=elev_amplitude, elev_cycles=elev_cycles,
    )
    writer = _ffmpeg_writer(animation, fps=fps, bitrate=bitrate)
    anim.save(path, writer=writer)
    pyplot.close(figure)
    return path
