"""Rotating 3-D projection of the Central Finite Curve (DEFERRED behind matplotlib + PIL/ffmpeg).

A companion to :mod:`central_finite_curve.adapters.animate` that renders the
multiverse in THREE dimensions under an orbiting camera. The scene is the top-3
principal-component projection (:func:`central_finite_curve.core.projection.project_3d`)
of the multiverse point cloud:

    * the whole multiverse scattered faintly (context), with
    * the near-maximal **Central Finite Curve** band highlighted
      (:mod:`central_finite_curve.core.curve`), and
    * the **portal-gun walk** (:mod:`central_finite_curve.core.portal_gun`) overlaid
      as a trajectory line,

while the CAMERA ORBITS -- the azimuth advances every frame and the elevation sweeps
gently via ``ax.view_init`` -- so the viewer flies around the ridge. Because the
first two of the three principal components match the 2-D projection exactly, this
3-D view is the same frame the flat renderers use, lifted into depth.

Two savers share ONE builder (:func:`_build_rotating_animation`):

    * :func:`save_cfc_rotating_gif` -- ``FuncAnimation`` + ``PillowWriter`` (needs
      matplotlib AND Pillow).
    * :func:`save_cfc_rotating_mp4` -- the SAME scene through
      :class:`matplotlib.animation.FFMpegWriter` (needs matplotlib AND ffmpeg).

Like its siblings this is an adapter: it may import ``core`` but ``core`` never
imports it, and matplotlib/Pillow/ffmpeg (and, for speed, numpy) are reached ONLY
lazily. Absent a dependency the renderers raise
:class:`~central_finite_curve.adapters.viz.OptionalDependencyError` rather than
failing at import time, so this module stays importable with the standard library
alone.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Callable, List, Sequence, Tuple

from central_finite_curve.adapters.animate import (
    _DEFAULT_BITRATE,
    _MP4_HELP,
    ffmpeg_is_available,
)
from central_finite_curve.adapters.viz import (
    OptionalDependencyError,
    project_prefer_numpy_3d,
)
from central_finite_curve.core import curve as curve_mod
from central_finite_curve.core import multiverse as multiverse_mod
from central_finite_curve.core import portal_gun as portal_gun_mod
from central_finite_curve.core import projection as projection_mod
from central_finite_curve.core.config import DEFAULT, CurveConfig
from central_finite_curve.core.pipeline import _GEN_TAG, _WALK_TAG
from central_finite_curve.core.sampling import child_rng

Point3D = Tuple[float, float, float]
Projector3D = Callable[[Sequence[Sequence[float]]], List[Point3D]]

_GIF_HELP = (
    "Rotating 3-D GIF export requires matplotlib AND Pillow, at least one of which is "
    "not installed. Install the optional 'viz' extra plus Pillow "
    "(pip install matplotlib pillow), or use the deterministic ASCII renderer, which "
    "needs no dependencies."
)

# Cap the faint background scatter so the orbiting 3-D scene stays cheap to render
# for a large multiverse; the band and the walk are always drawn in full.
_DEFAULT_MAX_BACKGROUND = 4000


@dataclass(frozen=True)
class RotatingSceneData:
    """Immutable 3-D scene sourced from the pure core (projection injectable).

    Assembled by :func:`rotating_scene_data` (stdlib + ``central_finite_curve.core``
    only when the default projector is used), so it is testable without matplotlib.
    """

    # Faint background: the (optionally sub-sampled) multiverse cloud.
    bg_x: List[float]
    bg_y: List[float]
    bg_z: List[float]
    # The highlighted near-maximal band.
    band_x: List[float]
    band_y: List[float]
    band_z: List[float]
    # The portal-gun walk trajectory.
    walk_x: List[float]
    walk_y: List[float]
    walk_z: List[float]
    curve_size: int
    total: int
    fraction: float
    acceptance_rate: float


def _stride_indices(count: int, cap: int) -> List[int]:
    """Return up to ``cap`` evenly strided indices into ``range(count)``."""
    if count <= cap:
        return list(range(count))
    step = count / cap
    return [min(count - 1, int(i * step)) for i in range(cap)]


def rotating_scene_data(
    *,
    config: CurveConfig = DEFAULT,
    max_background: int = _DEFAULT_MAX_BACKGROUND,
    projector: Projector3D | None = None,
) -> RotatingSceneData:
    """Build the 3-D scene from the REAL pure core.

    Runs the genuine pipeline -- :func:`multiverse.generate` -> :func:`curve.extract`
    -> :func:`portal_gun.travel` -- with the same seeded streams the rest of the
    package uses, then projects the combined ``multiverse + walk`` cloud to 3-D so
    everything shares one frame. ``projector`` defaults to the pure-stdlib
    :func:`core.projection.project_3d`; the renderer passes the numpy-preferring fast
    path. The faint background is strided down to at most ``max_background`` points;
    the band and walk are kept in full. Raises :class:`ValueError` for
    ``max_background < 1``.
    """
    if max_background < 1:
        raise ValueError("max_background must be >= 1")
    project = projector or projection_mod.project_3d

    gen_rng = child_rng(config.seed, _GEN_TAG)
    walk_rng = child_rng(config.seed, _WALK_TAG)
    universes = multiverse_mod.generate(gen_rng, config)
    the_curve = curve_mod.extract(universes, config)
    the_walk = portal_gun_mod.travel(the_curve, walk_rng, config)

    uni_coords = [list(u.coords) for u in universes]
    walk_coords = [list(p) for p in the_walk.points]
    proj_all = project(uni_coords + walk_coords)
    n_uni = len(uni_coords)
    proj_uni = proj_all[:n_uni]
    proj_walk = proj_all[n_uni:]

    band_low = the_curve.band_low
    in_band = [u.score >= band_low for u in universes]

    bg_idx = _stride_indices(n_uni, max_background)
    band_x, band_y, band_z = [], [], []
    for i, hot in enumerate(in_band):
        if hot:
            px, py, pz = proj_uni[i]
            band_x.append(px)
            band_y.append(py)
            band_z.append(pz)

    return RotatingSceneData(
        bg_x=[proj_uni[i][0] for i in bg_idx],
        bg_y=[proj_uni[i][1] for i in bg_idx],
        bg_z=[proj_uni[i][2] for i in bg_idx],
        band_x=band_x, band_y=band_y, band_z=band_z,
        walk_x=[p[0] for p in proj_walk],
        walk_y=[p[1] for p in proj_walk],
        walk_z=[p[2] for p in proj_walk],
        curve_size=the_curve.size,
        total=the_curve.total,
        fraction=the_curve.fraction,
        acceptance_rate=the_walk.acceptance_rate,
    )


def _load_backends() -> Tuple[Any, Any]:
    """Return ``(pyplot, animation)`` on headless Agg (needs Pillow + mplot3d), or raise."""
    from commons.core.optional import try_import

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


def _build_rotating_animation(
    *,
    config: CurveConfig,
    max_background: int,
    frames: int,
    azim_per_frame: float,
    elev_base: float,
    elev_amplitude: float,
    elev_cycles: float,
) -> Tuple[Any, Any, Any, Any]:
    """Build the rotating 3-D :class:`FuncAnimation` (shared by the GIF/MP4 savers).

    Lays out an ``mpl_toolkits.mplot3d`` scene: the faint multiverse scatter, the
    highlighted near-maximal band and the portal-gun walk line, then wires a per-frame
    ``update`` that advances the camera (``ax.view_init``) so the whole scene orbits.
    Every coordinate comes from :func:`rotating_scene_data` (the real pure core),
    projected via the numpy-preferring fast path. Returns
    ``(pyplot, animation, figure, anim)`` so the caller picks the writer. Raises
    :class:`ValueError` for ``frames < 1`` and :class:`OptionalDependencyError` when
    matplotlib/Pillow are absent.
    """
    if frames < 1:
        raise ValueError("frames must be >= 1")

    data = rotating_scene_data(
        config=config, max_background=max_background, projector=project_prefer_numpy_3d
    )

    pyplot, animation = _load_backends()
    figure = pyplot.figure(figsize=(8, 7))
    axes = figure.add_subplot(111, projection="3d")
    axes.scatter(
        data.bg_x, data.bg_y, data.bg_z, s=3, c="#bbbbbb", alpha=0.15,
        label="multiverse",
    )
    if data.band_x:
        axes.scatter(
            data.band_x, data.band_y, data.band_z, s=8, c="#cc3366", alpha=0.7,
            label="Central Finite Curve",
        )
    if data.walk_x:
        axes.plot(
            data.walk_x, data.walk_y, data.walk_z,
            color="#2244cc", linewidth=1.0, alpha=0.85, label="portal-gun walk",
        )
    axes.legend(loc="upper right", fontsize=8)
    axes.set_title(
        "Central Finite Curve in 3-D -- orbiting the near-maximal Rickness band\n"
        f"{data.curve_size} universes ({data.fraction * 100:.1f}% of N), "
        f"accept {data.acceptance_rate * 100:.1f}%",
        fontsize=10,
    )
    axes.set_xlabel("PC1")
    axes.set_ylabel("PC2")
    axes.set_zlabel("PC3")
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


def save_cfc_rotating_gif(
    path: str,
    *,
    config: CurveConfig = DEFAULT,
    max_background: int = _DEFAULT_MAX_BACKGROUND,
    frames: int = 72,
    fps: int = 20,
    azim_per_frame: float = 5.0,
    elev_base: float = 22.0,
    elev_amplitude: float = 12.0,
    elev_cycles: float = 1.0,
) -> str:
    """Animate the 3-D Central Finite Curve under an orbiting camera to a GIF.

    The faint multiverse scatter carries the highlighted near-maximal band and the
    portal-gun walk while the camera azimuth advances ``azim_per_frame`` degrees each
    frame and the elevation sweeps ``+/- elev_amplitude`` degrees about ``elev_base``.
    Rendered with ``mpl_toolkits.mplot3d`` + ``PillowWriter``; matplotlib and Pillow
    are imported lazily, so this raises :class:`OptionalDependencyError` when either is
    absent. Returns ``path``.
    """
    if fps < 1:
        raise ValueError("fps must be >= 1")
    pyplot, animation, figure, anim = _build_rotating_animation(
        config=config, max_background=max_background, frames=frames,
        azim_per_frame=azim_per_frame, elev_base=elev_base,
        elev_amplitude=elev_amplitude, elev_cycles=elev_cycles,
    )
    anim.save(path, writer=animation.PillowWriter(fps=fps))
    pyplot.close(figure)
    return path


def save_cfc_rotating_mp4(
    path: str,
    *,
    config: CurveConfig = DEFAULT,
    max_background: int = _DEFAULT_MAX_BACKGROUND,
    frames: int = 72,
    fps: int = 20,
    bitrate: int = _DEFAULT_BITRATE,
    azim_per_frame: float = 5.0,
    elev_base: float = 22.0,
    elev_amplitude: float = 12.0,
    elev_cycles: float = 1.0,
) -> str:
    """Encode the rotating 3-D scene as an MP4 at ``path`` (ffmpeg).

    Reuses the exact :func:`save_cfc_rotating_gif` scene but writes it with
    :class:`matplotlib.animation.FFMpegWriter`. matplotlib is imported lazily and
    ffmpeg availability is checked at call time; raises
    :class:`OptionalDependencyError` when matplotlib or an ffmpeg binary is absent.
    Returns ``path``.
    """
    if fps < 1:
        raise ValueError("fps must be >= 1")
    if not ffmpeg_is_available():  # fail fast, before building the scene
        raise OptionalDependencyError(_MP4_HELP)
    pyplot, animation, figure, anim = _build_rotating_animation(
        config=config, max_background=max_background, frames=frames,
        azim_per_frame=azim_per_frame, elev_base=elev_base,
        elev_amplitude=elev_amplitude, elev_cycles=elev_cycles,
    )
    writer = animation.FFMpegWriter(fps=fps, bitrate=bitrate)
    anim.save(path, writer=writer)
    pyplot.close(figure)
    return path
