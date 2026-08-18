"""Four-panel composite explainer of the Central Finite Curve (DEFERRED behind matplotlib + PIL/ffmpeg).

A single composite animation that tells the whole Central Finite Curve story on a
shared frame timeline: a 2x2 grid of subplots with a suptitle, ending on a HOLD
frame that reveals a summary banner. Every number is pulled from the REAL pure core
(never fabricated).

    * Panel 1 -- "Multiverse, Rickness-scored". The top-2 principal-component (PCA)
      projection (:mod:`central_finite_curve.core.projection`) of the WHOLE
      multiverse point cloud (:mod:`central_finite_curve.core.multiverse`), each
      universe coloured by its core Rickness score.
    * Panel 2 -- "Central Finite Curve = near-maximal band". The same projection with
      the epsilon-band subset (:mod:`central_finite_curve.core.curve`) highlighted
      against the rest, plus a readout of the curve size and its share of ``N``.
    * Panel 3 -- "Portal gun walks the curve". The Metropolis walk
      (:mod:`central_finite_curve.core.portal_gun`) animated step by step (frame ``k``
      reveals walk step ``k``), sliding ALONG the band without ever falling off it,
      with the acceptance ratio in the panel title.
    * Panel 4 -- "Rickness distribution". A histogram of Rickness across the
      multiverse with the epsilon band shaded as the near-max tail -- showing the
      curve is exactly the top band of the score distribution.

Panels 1, 2 and 4 are static; Panel 3 animates the walk over the shared timeline.
The last ``hold`` frames freeze everything and reveal the summary banner.

The whole numeric scene is assembled by the pure :func:`four_panel_frame_data`
(stdlib + ``central_finite_curve.core`` only, projection injectable), so it is
testable without any scientific dependency and provably sources the genuine core
values (band size == ``core.curve``'s, acceptance == ``core.portal_gun``'s).

Like its siblings this is an adapter: it may import ``core`` but ``core`` never
imports it, and matplotlib/Pillow/ffmpeg (and, for speed, numpy) are reached ONLY
lazily. Absent a dependency the renderers raise
:class:`~central_finite_curve.adapters.viz.OptionalDependencyError` rather than
failing at import time, so this module stays importable with the standard library
alone.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, List, Sequence, Tuple

from central_finite_curve.adapters.animate import (
    _DEFAULT_BITRATE,
    _MP4_HELP,
    ffmpeg_is_available,
)
from central_finite_curve.adapters.viz import (
    OptionalDependencyError,
    project_prefer_numpy,
)
from central_finite_curve.core import curve as curve_mod
from central_finite_curve.core import multiverse as multiverse_mod
from central_finite_curve.core import portal_gun as portal_gun_mod
from central_finite_curve.core import projection as projection_mod
from central_finite_curve.core.config import DEFAULT, CurveConfig
from central_finite_curve.core.pipeline import _GEN_TAG, _WALK_TAG
from central_finite_curve.core.sampling import child_rng

Point2D = Tuple[float, float]
Projector = Callable[[Sequence[Sequence[float]]], List[Point2D]]

_GIF_HELP = (
    "Four-panel explainer GIF export requires matplotlib AND Pillow, at least one of "
    "which is not installed. Install the optional 'viz' extra plus Pillow "
    "(pip install matplotlib pillow), or use the deterministic ASCII renderer, which "
    "needs no dependencies."
)

# The hold-frame summary banner (a third reading of the Central Finite Curve).
_BANNER = (
    "Central Finite Curve = the near-maximal Rickness band -- a third reading, "
    "cf. mobius_rickness's zero-set R^-1(0) and SCMS ridge."
)


@dataclass(frozen=True)
class FourPanelData:
    """Immutable numeric scene for every panel, sourced from the pure core.

    Assembled by :func:`four_panel_frame_data` (stdlib + ``central_finite_curve.core``
    only, with an injectable projector), so it is exercised in a dependency-free test
    that asserts the panels source genuine core values.
    """

    active: int
    # Panels 1 & 2 -- the projected multiverse cloud, coloured by Rickness.
    uni_x: List[float]
    uni_y: List[float]
    uni_scores: List[float]
    in_band: List[bool]
    # Panel 3 -- the projected portal-gun walk (same frame as the cloud).
    walk_x: List[float]
    walk_y: List[float]
    walk_scores: List[float]
    walk_reveal: List[int]
    # Shared scalar readouts (all straight from the core).
    curve_size: int
    total: int
    fraction: float
    max_score: float
    band_low: float
    epsilon: float
    acceptance_rate: float
    walk_steps: int


def _reveal_counts(count: int, active: int) -> List[int]:
    """Per-frame count of revealed items: ``1..count`` spread over ``active`` frames."""
    if count <= 0:
        return [0] * active
    if active <= 1:
        return [count]
    return [max(1, min(count, round((p + 1) * count / active))) for p in range(active)]


def four_panel_frame_data(
    active: int,
    *,
    config: CurveConfig = DEFAULT,
    projector: Projector | None = None,
) -> FourPanelData:
    """Build every panel's numeric scene from the REAL pure core.

    ``active`` is the number of animated (non-hold) frames. Runs the genuine core
    pipeline -- :func:`multiverse.generate` -> :func:`curve.extract` ->
    :func:`portal_gun.travel` -- with the same seeded streams the rest of the package
    uses (:data:`pipeline._GEN_TAG` / :data:`pipeline._WALK_TAG`), then projects the
    combined ``multiverse + walk`` cloud to 2-D so both share one frame.

    ``projector`` defaults to the pure-stdlib :func:`core.projection.project_2d`; the
    renderer passes the numpy-preferring fast path for speed. Raises
    :class:`ValueError` for ``active < 1``.
    """
    if active < 1:
        raise ValueError("active must be >= 1")
    project = projector or projection_mod.project_2d

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
    scores = [u.score for u in universes]
    in_band = [s >= band_low for s in scores]

    return FourPanelData(
        active=active,
        uni_x=[p[0] for p in proj_uni],
        uni_y=[p[1] for p in proj_uni],
        uni_scores=scores,
        in_band=in_band,
        walk_x=[p[0] for p in proj_walk],
        walk_y=[p[1] for p in proj_walk],
        walk_scores=list(the_walk.scores),
        walk_reveal=_reveal_counts(len(proj_walk), active),
        curve_size=the_curve.size,
        total=the_curve.total,
        fraction=the_curve.fraction,
        max_score=the_curve.max_score,
        band_low=band_low,
        epsilon=the_curve.epsilon,
        acceptance_rate=the_walk.acceptance_rate,
        walk_steps=the_walk.steps,
    )


# ---------------------------------------------------------------------------
# Lazy backend loading (matplotlib / Pillow reached only here)
# ---------------------------------------------------------------------------

def _load_backends() -> Tuple[Any, Any]:
    """Return ``(pyplot, animation)`` on the headless Agg backend, or raise.

    matplotlib, matplotlib.pyplot, matplotlib.animation AND Pillow are reached lazily
    via :func:`commons.core.optional.try_import`. Raises
    :class:`OptionalDependencyError` when any is absent; never silently degrades. The
    Agg backend keeps rendering headless and deterministic.
    """
    from commons.core.optional import try_import

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


# ---------------------------------------------------------------------------
# Per-panel drawing (Panels 1/2/4 are static; Panel 3 owns the animated artists)
# ---------------------------------------------------------------------------

def _draw_multiverse(ax: Any, data: FourPanelData) -> None:
    """Panel 1: the projected multiverse cloud coloured by core Rickness."""
    sc = ax.scatter(
        data.uni_x, data.uni_y, c=data.uni_scores, cmap="viridis", s=4, alpha=0.6
    )
    ax.set_title("1) Multiverse, Rickness-scored", fontsize=9)
    ax.set_xlabel("PC1", fontsize=8)
    ax.set_ylabel("PC2", fontsize=8)
    ax.figure.colorbar(sc, ax=ax, fraction=0.046, pad=0.04, label="Rickness")


def _draw_band(ax: Any, data: FourPanelData) -> None:
    """Panel 2: same projection with the near-maximal band highlighted vs the rest."""
    rest_x = [x for x, hot in zip(data.uni_x, data.in_band) if not hot]
    rest_y = [y for y, hot in zip(data.uni_y, data.in_band) if not hot]
    band_x = [x for x, hot in zip(data.uni_x, data.in_band) if hot]
    band_y = [y for y, hot in zip(data.uni_y, data.in_band) if hot]
    ax.scatter(rest_x, rest_y, s=4, c="#bbbbbb", alpha=0.35, label="rest of multiverse")
    ax.scatter(band_x, band_y, s=6, c="#cc3366", alpha=0.85, label="Central Finite Curve")
    ax.set_title("2) Central Finite Curve = near-maximal band", fontsize=9)
    ax.set_xlabel("PC1", fontsize=8)
    ax.set_ylabel("PC2", fontsize=8)
    ax.legend(loc="upper right", fontsize=6)
    ax.text(
        0.03, 0.96,
        f"curve size = {data.curve_size}\n"
        f"= {data.fraction * 100:.2f}% of N = {data.total}\n"
        f"band: Rickness >= {data.band_low:.3f}",
        transform=ax.transAxes, va="top", ha="left", fontsize=6.5,
    )


def _draw_histogram(ax: Any, data: FourPanelData) -> None:
    """Panel 4: Rickness histogram with the epsilon band shaded as the near-max tail."""
    ax.hist(data.uni_scores, bins=48, color="#4477aa", alpha=0.8)
    ax.axvline(data.band_low, color="#cc3366", linestyle="--", linewidth=1.5)
    ax.axvspan(data.band_low, data.max_score, color="#cc3366", alpha=0.2)
    ax.set_title("4) Rickness distribution", fontsize=9)
    ax.set_xlabel("Rickness", fontsize=8)
    ax.set_ylabel("count", fontsize=8)
    ax.text(
        0.03, 0.96,
        f"near-max tail (width eps = {data.epsilon:.2f})\n"
        f"max = {data.max_score:.3f}\n"
        f"tail = the curve ({data.curve_size} universes)",
        transform=ax.transAxes, va="top", ha="left", fontsize=6.5,
    )


# ---------------------------------------------------------------------------
# The composite 2x2 animation shared by the GIF/MP4 savers
# ---------------------------------------------------------------------------

def _build_four_panel_animation(
    *, config: CurveConfig, frames: int, hold: int
) -> Tuple[Any, Any, Any, Any]:
    """Build the 2x2 four-panel :class:`FuncAnimation` (shared by the savers).

    ``frames`` is the TOTAL number of frames; the last ``min(hold, frames - 1)`` are
    HOLD frames that freeze every panel and reveal the summary banner. All numeric
    values come from :func:`four_panel_frame_data` (the real pure core), projected via
    the numpy-preferring fast path for speed. Panels 1/2/4 are drawn once (static);
    Panel 3's walk trail + head + title animate over the shared timeline. Returns
    ``(pyplot, animation, figure, anim)`` so the caller picks the writer. Raises
    :class:`ValueError` for ``frames < 1`` / ``hold < 0`` and
    :class:`OptionalDependencyError` when matplotlib/Pillow are absent.
    """
    if frames < 1:
        raise ValueError("frames must be >= 1")
    if hold < 0:
        raise ValueError("hold must be >= 0")

    hold_frames = min(hold, frames - 1) if frames > 1 else 0
    active = frames - hold_frames
    data = four_panel_frame_data(active, config=config, projector=project_prefer_numpy)
    if not data.walk_x:
        raise ValueError("the walk produced no points to animate")

    pyplot, animation = _load_backends()
    figure, axes = pyplot.subplots(2, 2, figsize=(11.0, 8.0))
    figure.suptitle(
        "The Central Finite Curve: a near-maximal Rickness band walked by a portal gun",
        fontsize=12, y=0.99,
    )
    banner = figure.text(
        0.5, 0.005, "", ha="center", va="bottom",
        fontsize=9, color="firebrick", fontweight="bold", wrap=True,
    )
    ax_multi, ax_band = axes[0][0], axes[0][1]
    ax_walk, ax_hist = axes[1][0], axes[1][1]

    # Static panels: draw once so animating stays cheap even for a large multiverse.
    _draw_multiverse(ax_multi, data)
    _draw_band(ax_band, data)
    _draw_histogram(ax_hist, data)

    # Panel 3 backdrop: the faint band, over which the walk is drawn in.
    band_x = [x for x, hot in zip(data.uni_x, data.in_band) if hot]
    band_y = [y for y, hot in zip(data.uni_y, data.in_band) if hot]
    ax_walk.scatter(band_x, band_y, s=5, c="#22aa88", alpha=0.25, label="curve")
    all_x = data.uni_x + data.walk_x
    all_y = data.uni_y + data.walk_y
    pad_x = 0.05 * (max(all_x) - min(all_x) or 1.0)
    pad_y = 0.05 * (max(all_y) - min(all_y) or 1.0)
    ax_walk.set_xlim(min(all_x) - pad_x, max(all_x) + pad_x)
    ax_walk.set_ylim(min(all_y) - pad_y, max(all_y) + pad_y)
    ax_walk.set_xlabel("PC1", fontsize=8)
    ax_walk.set_ylabel("PC2", fontsize=8)
    (trail,) = ax_walk.plot([], [], linewidth=1.0, color="#cc3366", alpha=0.8)
    (head,) = ax_walk.plot([], [], marker="o", color="#cc3366")
    readout = ax_walk.text(
        0.03, 0.96, "", transform=ax_walk.transAxes, va="top", ha="left", fontsize=6.5
    )

    def update(frame: int) -> Tuple[Any, ...]:
        p = min(frame, active - 1)
        n = data.walk_reveal[p]
        k = max(0, n - 1)
        trail.set_data(data.walk_x[:n], data.walk_y[:n])
        head.set_data([data.walk_x[k]], [data.walk_y[k]])
        ax_walk.set_title(
            f"3) Portal gun walks the curve -- accept {data.acceptance_rate * 100:.1f}%",
            fontsize=9,
        )
        readout.set_text(
            f"step {k}/{data.walk_steps}\nRickness = {data.walk_scores[k]:.4f}"
        )
        banner.set_text(_BANNER if frame >= active else "")
        return (trail, head, readout, banner)

    figure.tight_layout(rect=(0.0, 0.05, 1.0, 0.96))
    anim = animation.FuncAnimation(figure, update, frames=frames, blit=False)
    return pyplot, animation, figure, anim


def save_cfc_four_panels_gif(
    path: str,
    *,
    config: CurveConfig = DEFAULT,
    frames: int = 44,
    hold: int = 8,
    fps: int = 8,
) -> str:
    """Render the four-panel composite explainer as a GIF at ``path``.

    All four panels sit on a 2x2 grid over a shared timeline (Panel 3 animates the
    walk) and end on a HOLD frame showing the summary banner. Rendered with
    matplotlib ``FuncAnimation`` + ``PillowWriter``; matplotlib and Pillow are
    imported lazily, so this raises :class:`OptionalDependencyError` when either is
    absent. Returns ``path``.
    """
    if fps < 1:
        raise ValueError("fps must be >= 1")
    pyplot, animation, figure, anim = _build_four_panel_animation(
        config=config, frames=frames, hold=hold
    )
    anim.save(path, writer=animation.PillowWriter(fps=fps))
    pyplot.close(figure)
    return path


def save_cfc_four_panels_mp4(
    path: str,
    *,
    config: CurveConfig = DEFAULT,
    frames: int = 44,
    hold: int = 8,
    fps: int = 8,
    bitrate: int = _DEFAULT_BITRATE,
) -> str:
    """Encode the four-panel composite explainer as an MP4 at ``path`` (ffmpeg).

    Reuses the exact :func:`save_cfc_four_panels_gif` scene but writes it with
    :class:`matplotlib.animation.FFMpegWriter`. matplotlib is imported lazily and
    ffmpeg availability is checked at call time; raises
    :class:`OptionalDependencyError` when matplotlib or an ffmpeg binary is absent.
    Returns ``path``.
    """
    if fps < 1:
        raise ValueError("fps must be >= 1")
    if not ffmpeg_is_available():  # fail fast, before building the scene
        raise OptionalDependencyError(_MP4_HELP)
    pyplot, animation, figure, anim = _build_four_panel_animation(
        config=config, frames=frames, hold=hold
    )
    writer = animation.FFMpegWriter(fps=fps, bitrate=bitrate)
    anim.save(path, writer=writer)
    pyplot.close(figure)
    return path
