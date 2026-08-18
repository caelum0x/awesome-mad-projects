"""Animated GIFs of the approach to Gojo (DEFERRED behind matplotlib + PIL).

Two headless animations, written with :class:`matplotlib.animation.FuncAnimation`
and a :class:`matplotlib.animation.PillowWriter` (which needs Pillow):

    * :func:`save_geodesic_approach_gif` -- one or a few conformal geodesics
      travelling and bending around Gojo, with an on-frame readout of the
      accumulated *felt* (Riemannian) length climbing as the ray nears Gojo.
      Because the affine invariant ``Omega^2 |v|^2`` is conserved, the coordinate
      speed ``|v| ~ 1/Omega`` collapses near the barrier: the ray visibly SLOWS
      and never arrives while its felt length runs away.
    * :func:`save_never_arrives_gif` -- an attacker taking Zeno steps
      ``x_n = 1 - (1/2)^n`` toward Gojo at ``x = 1``: the residual ``(1/2)^n``
      halves forever (never reaching ``0``) while the *felt* geodesic length
      ``integral Omega dx`` from the start to ``x_n`` climbs without bound.

Both are adapters: they may import ``core`` but ``core`` never imports them, and
matplotlib/PIL are reached ONLY lazily through
:func:`commons.core.optional.try_import`. Absent either dependency, each renderer
raises :class:`OptionalDependencyError` instead of failing at import time, so this
module stays importable with the standard library alone.
"""

from __future__ import annotations

import math
import shutil
from typing import Any, List, Tuple

from commons.core.optional import try_import

from gojo_infinity.adapters.viz import OptionalDependencyError
from gojo_infinity.core import (
    ConformalMetric,
    X_GOJO,
    conformal_factor,
    geodesic_length,
    partial_sum,
    residual,
)

Vec2 = Tuple[float, float]

_GIF_HELP = (
    "GIF export requires matplotlib AND Pillow, at least one of which is not "
    "installed. Install the optional 'viz' extra plus Pillow "
    "(pip install matplotlib pillow), or use the deterministic ASCII / numeric "
    "renderers, which need no dependencies."
)

_MP4_HELP = (
    "MP4 export requires matplotlib AND an ffmpeg binary on PATH (matplotlib's "
    "FFMpegWriter shells out to it). Install ffmpeg (e.g. 'brew install ffmpeg' "
    "or your distro's package), or export the animation as a GIF instead "
    "(save_geodesic_approach_gif / save_geodesic_3d_rotating_gif), which needs "
    "only Pillow."
)

# A reasonable default video bitrate (kbit/s) for the short, schematic scenes.
_DEFAULT_BITRATE = 1800


def _load_backends() -> Tuple[Any, Any]:
    """Return ``(pyplot, animation)`` on the headless Agg backend, or raise.

    matplotlib, matplotlib.pyplot, matplotlib.animation AND Pillow are all reached
    lazily via :func:`commons.core.optional.try_import`. If any is absent this
    raises :class:`OptionalDependencyError` (deferred behaviour); it never
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


def _load_animation_backend() -> Any:
    """Return ``matplotlib.animation`` on the headless Agg backend, or raise.

    Like :func:`_load_backends` but WITHOUT the Pillow requirement -- the MP4
    exporters do not encode through Pillow. Raises
    :class:`OptionalDependencyError` when matplotlib itself is absent.
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
    trivially monkeypatchable in tests) AND matplotlib's registered ``ffmpeg``
    writer must be present. Never raises: it is a pure capability probe.
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


# ---------------------------------------------------------------------------
# Shared trajectory helper -- points + cumulative felt (Riemannian) length
# ---------------------------------------------------------------------------

def _geodesic_with_felt_length(
    metric: ConformalMetric,
    p0: Vec2,
    v0: Vec2,
    *,
    dtau: float,
    max_steps: int,
    target_radius: float,
) -> Tuple[List[Vec2], List[float]]:
    """Integrate a geodesic and return ``(points, cumulative_felt_length)``.

    The cumulative felt length is the Riemannian length of the polyline: for each
    segment, ``0.5 * (Omega(a) + Omega(b)) * |b - a|`` (the trapezoid rule on
    ``Omega`` along the path), matching the integrator's own arc length.
    """
    res = metric.integrate_geodesic(
        p0, v0, dtau=dtau, max_steps=max_steps,
        target_radius=target_radius, min_radius=1e-4,
    )
    points = list(res.points)
    cumulative = [0.0]
    for a, b in zip(points, points[1:]):
        seg = math.hypot(b[0] - a[0], b[1] - a[1])
        felt = 0.5 * (metric.omega(a) + metric.omega(b)) * seg
        cumulative.append(cumulative[-1] + felt)
    return points, cumulative


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


# ---------------------------------------------------------------------------
# (a) The felt-length approach animation
# ---------------------------------------------------------------------------

def _build_approach_animation(
    *,
    p0: Vec2,
    v0: Vec2,
    frames: int,
    dtau: float,
    max_steps: int,
    target_radius: float,
) -> Tuple[Any, Any, Any, Any]:
    """Build the 2-D approach :class:`FuncAnimation` (shared by the GIF/MP4 savers).

    Integrates the grazing conformal geodesic, lays out the figure and wires the
    per-frame ``update`` closure, returning ``(pyplot, animation, figure, anim)``.
    The caller chooses the writer (Pillow for GIF, ffmpeg for MP4). Raises
    :class:`ValueError` for ``frames < 1`` and :class:`OptionalDependencyError`
    when matplotlib/Pillow are absent.
    """
    if frames < 1:
        raise ValueError("frames must be >= 1")
    metric = ConformalMetric()  # Gojo at the origin of R^2
    points, felt = _geodesic_with_felt_length(
        metric, p0, v0, dtau=dtau, max_steps=max_steps, target_radius=target_radius
    )
    idx = _sample_indices(len(points), frames)
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]

    pyplot, animation = _load_backends()
    figure, axes = pyplot.subplots()
    pad = 0.3
    axes.set_xlim(min(xs) - pad, max(xs) + pad)
    axes.set_ylim(min(ys) - pad, max(ys) + pad)
    axes.set_aspect("equal", adjustable="box")
    axes.plot([0.0], [0.0], marker="*", markersize=16, color="black")
    axes.set_title("Geodesic approach to Gojo -- felt length diverges")
    axes.set_xlabel("x")
    axes.set_ylabel("y")
    (trail,) = axes.plot([], [], linewidth=1.5, color="tab:blue")
    (head,) = axes.plot([], [], marker="o", color="tab:red")
    readout = axes.text(
        0.02, 0.97, "", transform=axes.transAxes, va="top", ha="left", fontsize=9
    )

    def update(frame: int) -> Tuple[Any, Any, Any]:
        k = idx[frame]
        trail.set_data(xs[: k + 1], ys[: k + 1])
        head.set_data([xs[k]], [ys[k]])
        r = math.hypot(xs[k], ys[k])
        readout.set_text(f"felt length = {felt[k]:.3f}\nradius to Gojo = {r:.4f}")
        return trail, head, readout

    anim = animation.FuncAnimation(figure, update, frames=len(idx), blit=False)
    return pyplot, animation, figure, anim


def save_geodesic_approach_gif(
    path: str,
    *,
    p0: Vec2 = (-1.6, 0.28),
    v0: Vec2 = (1.0, 0.0),
    frames: int = 60,
    fps: int = 20,
    dtau: float = 1e-3,
    max_steps: int = 200_000,
    target_radius: float = 0.03,
) -> str:
    """Animate a geodesic bending around Gojo, felt length climbing, to ``path``.

    A grazing conformal geodesic (2-D) starts at ``p0`` heading ``v0``; it bends
    toward Gojo (the origin) and slows as ``Omega`` erupts, its accumulated felt
    length shown on each frame. matplotlib + Pillow are imported lazily; raises
    :class:`OptionalDependencyError` when either is absent. Returns ``path``.
    """
    if fps < 1:
        raise ValueError("fps must be >= 1")
    pyplot, animation, figure, anim = _build_approach_animation(
        p0=p0, v0=v0, frames=frames, dtau=dtau,
        max_steps=max_steps, target_radius=target_radius,
    )
    anim.save(path, writer=animation.PillowWriter(fps=fps))
    pyplot.close(figure)
    return path


def save_geodesic_approach_mp4(
    path: str,
    *,
    p0: Vec2 = (-1.6, 0.28),
    v0: Vec2 = (1.0, 0.0),
    frames: int = 60,
    fps: int = 20,
    bitrate: int = _DEFAULT_BITRATE,
    dtau: float = 1e-3,
    max_steps: int = 200_000,
    target_radius: float = 0.03,
) -> str:
    """Encode the 2-D geodesic-approach animation as an MP4 at ``path`` (ffmpeg).

    Reuses the exact :func:`save_geodesic_approach_gif` scene but writes it with
    :class:`matplotlib.animation.FFMpegWriter`. matplotlib is imported lazily and
    ffmpeg availability is checked at call time; raises
    :class:`OptionalDependencyError` when matplotlib or an ffmpeg binary is
    absent. Returns ``path``.
    """
    if fps < 1:
        raise ValueError("fps must be >= 1")
    if not ffmpeg_is_available():  # fail fast, before building the scene
        raise OptionalDependencyError(_MP4_HELP)
    pyplot, animation, figure, anim = _build_approach_animation(
        p0=p0, v0=v0, frames=frames, dtau=dtau,
        max_steps=max_steps, target_radius=target_radius,
    )
    writer = _ffmpeg_writer(animation, fps=fps, bitrate=bitrate)
    anim.save(path, writer=writer)
    pyplot.close(figure)
    return path


# ---------------------------------------------------------------------------
# (b) The Zeno "never arrives" animation
# ---------------------------------------------------------------------------

def save_never_arrives_gif(
    path: str,
    *,
    start: float = 0.0,
    max_n: int = 24,
    fps: int = 6,
) -> str:
    """Animate an attacker's Zeno steps toward Gojo (never arriving) to ``path``.

    Step ``n`` sits at ``x_n = 1 - (1/2)^n`` on the way to Gojo at ``x = 1``. The
    residual ``(1/2)^n`` halves forever (never ``0``), while the felt geodesic
    length ``integral_{start}^{x_n} Omega dx`` climbs without bound -- shown on
    each frame. matplotlib + Pillow are imported lazily; raises
    :class:`OptionalDependencyError` when either is absent. Returns ``path``.
    """
    if max_n < 1:
        raise ValueError("max_n must be >= 1")
    if fps < 1:
        raise ValueError("fps must be >= 1")
    if not (0.0 <= start < X_GOJO):
        raise ValueError("require 0 <= start < x_gojo")

    ns = list(range(1, max_n + 1))
    positions = [float(partial_sum(n)) for n in ns]      # x_n = 1 - (1/2)^n
    residuals = [float(residual(n)) for n in ns]         # (1/2)^n > 0 forever
    felt = [geodesic_length(start, x) for x in positions]  # climbs toward +inf

    pyplot, animation = _load_backends()
    figure, axes = pyplot.subplots()
    axes.set_xlim(start - 0.05, X_GOJO + 0.05)
    axes.set_ylim(-0.4, 0.4)
    axes.axvline(X_GOJO, linestyle="--", color="grey")
    axes.plot([X_GOJO], [0.0], marker="*", markersize=16, color="black")
    axes.text(X_GOJO, 0.12, "Gojo", ha="center", fontsize=9)
    axes.set_yticks([])
    axes.set_title("Zeno steps toward Gojo -- residual > 0, felt length -> inf")
    axes.set_xlabel("x (attacker position; barrier at x_g = 1)")
    (attacker,) = axes.plot([], [], marker="o", markersize=10, color="tab:red")
    (track,) = axes.plot([], [], linewidth=1.0, color="tab:blue")
    readout = axes.text(
        0.02, 0.97, "", transform=axes.transAxes, va="top", ha="left", fontsize=9
    )

    def update(frame: int) -> Tuple[Any, Any, Any]:
        x = positions[frame]
        attacker.set_data([x], [0.0])
        track.set_data(positions[: frame + 1], [0.0] * (frame + 1))
        readout.set_text(
            f"n = {ns[frame]}\n"
            f"residual (1/2)^n = {residuals[frame]:.3e}\n"
            f"felt length = {felt[frame]:.3f}"
        )
        return attacker, track, readout

    anim = animation.FuncAnimation(figure, update, frames=len(ns), blit=False)
    anim.save(path, writer=animation.PillowWriter(fps=fps))
    pyplot.close(figure)
    return path
