"""Four-panel composite explainer of the Central Finite Curve (DEFERRED behind matplotlib + PIL/ffmpeg).

A single composite animation that tells the whole Mobius-Rickness / Central Finite
Curve story on a shared frame timeline: a 2x2 grid of subplots with a suptitle,
each panel animating its own point and ending on a HOLD frame with a summary banner.

    * Panel 1 -- "Mobius strip: ruled => K < 0". A heatmap / sign-map of the
      Gaussian curvature ``K(u, v)`` with a scan line sweeping ``u`` across frames.
      ``K`` is strictly negative on the whole interior; a per-frame readout confirms
      the three curvature paths (analytic / finite-difference / complex-step) agree
      (the max path-difference ``max|analytic - numeric|``).
    * Panel 2 -- "Central Finite Curve = R^{-1}(0)". Over a faint sign-map of the
      sign-changing Rickness ``R(u, v)`` the traced zero-set curve is DRAWN IN
      point-by-point across frames (revealed up to frame ``k``): the boundary
      between the Rick-positive and Rick-negative regions.
    * Panel 3 -- "Second reading: SCMS ridge (crest of max Rickness)". The SCMS
      seed cloud converges onto the Eberly ridge (frame ``k`` = SCMS iteration
      ``k``), with the mean ridge residual ``mean_i |grad . e_minor|`` shrinking
      toward ``0`` in the panel title. Reuses :func:`scms_ridge_history`.
    * Panel 4 -- "Torus: non-ruled => K changes sign". The closed-form
      ``K(theta) = cos(theta) / (r0 (R0 + r0 cos theta))`` curve with a scan line
      sweeping ``theta``, marking the sign pattern (``+`` outer / ``-`` inner) and
      the ``K = 0`` circles at ``theta = pi/2, 3*pi/2``.

It ends on a HOLD frame that reveals the summary banner contrasting the two
readings (zero-set vs ridge) and the ruled/non-ruled dichotomy.

Every number is pulled from the REAL pure core (never fabricated): the Gaussian
curvature and its three cross-validating paths
(:func:`mobius_rickness.core.gaussian_curvature` / ``gaussian_curvature_numeric`` /
``gaussian_curvature_complex_step``), the Rickness field and weighted curvature
(:func:`mobius_rickness.core.rickness` / ``evaluate_grid``), the traced zero set
(:func:`mobius_rickness.core.trace_columns` / ``flatten_columns``), the torus
closed form and its zero circles
(:func:`mobius_rickness.core.gaussian_curvature_closed` / ``zero_circles``), and the
SCMS ridge history (:func:`mobius_rickness.ridge.scms_ridge_history`). Panels 1, 2
and 4 are assembled by the pure :func:`four_panel_frame_data` (stdlib + core only),
so they are testable without any scientific dependency.

Like its siblings this is an adapter: it may import ``core`` and the numpy-backed
``ridge`` subpackage, but ``core`` never imports it, and matplotlib/Pillow/ffmpeg
and numpy are reached ONLY lazily. Absent a dependency the renderers raise
:class:`~mobius_rickness.adapters.viz.OptionalDependencyError` rather than failing
at import time, so this module stays importable with the standard library alone.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
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
    assert_mobius_K_negative,
    evaluate_grid,
    flatten_columns,
    gaussian_curvature,
    gaussian_curvature_closed,
    gaussian_curvature_complex_step,
    gaussian_curvature_numeric,
    linspace,
    trace_columns,
    zero_circles,
)

TWO_PI = 2.0 * math.pi

_GIF_HELP = (
    "Four-panel explainer GIF export requires matplotlib AND Pillow AND numpy, at "
    "least one of which is not installed. Install the optional 'viz' extra plus "
    "Pillow and numpy (pip install matplotlib pillow numpy), or use the "
    "deterministic ASCII / numeric renderers, which need no dependencies."
)

_MP4_HELP = (
    "Four-panel explainer MP4 export requires matplotlib AND numpy AND an ffmpeg "
    "binary on PATH (matplotlib's FFMpegWriter shells out to it). Install ffmpeg "
    "(e.g. 'brew install ffmpeg' or your distro's package), or export the animation "
    "as a GIF instead (save_four_panels_gif), which needs only Pillow + numpy."
)

# ---------------------------------------------------------------------------
# Scene constants (shared by the pure data builder and the renderer)
# ---------------------------------------------------------------------------

_V_PROBE: float = 0.25          # Panel 1 v-slice for the three-path K readout
_CURVE_SAMPLES: int = 240       # dense samples for the Panel 1 / Panel 4 line plots
_GRID_N_U: int = 61             # background heatmap resolution (Panels 1/2/3)
_GRID_N_V: int = 21
_TRACE_N_U: int = 96            # Panel 2 zero-set trace density (u-columns)
_TRACE_N_V_SAMPLES: int = 160
_SEED_N_U: int = 20             # Panel 3 SCMS seed cloud
_SEED_N_V: int = 4
_SCMS_TOL: float = 1e-8
_SCMS_MAX_ITER: int = 60


@dataclass(frozen=True)
class FourPanelData:
    """Immutable numeric sequences for Panels 1, 2 and 4, sourced from the pure core.

    Assembled by :func:`four_panel_frame_data` (stdlib + ``mobius_rickness.core``
    only), so it is exercised in a dependency-free test that asserts the panels
    source genuine core values. Panel 3's SCMS history is numpy-backed and is
    fetched separately inside the renderer.
    """

    active: int
    # Panel 1 -- Mobius K scan (three agreeing curvature paths at the scan line)
    p1_v_probe: float
    p1_scan_u: List[float]
    p1_k_analytic: List[float]
    p1_k_fd: List[float]
    p1_k_cs: List[float]
    p1_max_delta: List[float]
    p1_k_worst: float
    # Panel 2 -- zero-set R^{-1}(0) revealed point-by-point
    p2_curve_u: List[float]
    p2_curve_v: List[float]
    p2_reveal: List[int]
    # Panel 4 -- torus K(theta) scan
    p4_theta: List[float]
    p4_k: List[float]
    p4_scan_theta: List[float]
    p4_scan_k: List[float]
    p4_zero_circles: Tuple[float, float]


def four_panel_frame_data(
    active: int,
    *,
    v_probe: float = _V_PROBE,
    curve_samples: int = _CURVE_SAMPLES,
    trace_n_u: int = _TRACE_N_U,
    trace_n_v_samples: int = _TRACE_N_V_SAMPLES,
) -> FourPanelData:
    """Build Panels 1/2/4 numeric sequences from the REAL pure core.

    ``active`` is the number of animated (non-hold) frames. Raises
    :class:`ValueError` for ``active < 1``. Imports nothing beyond the standard
    library and :mod:`mobius_rickness.core`, so it is testable without numpy /
    matplotlib.
    """
    if active < 1:
        raise ValueError("active must be >= 1")
    if curve_samples < 2:
        raise ValueError("curve_samples must be >= 2")

    # Panel 1 -- scan u across the strip; at each frame read the three curvature
    # paths at (u, v_probe) and their max mutual difference (they agree).
    p1_scan_u = linspace(U_MIN, U_MAX, active)
    p1_k_analytic: List[float] = []
    p1_k_fd: List[float] = []
    p1_k_cs: List[float] = []
    p1_max_delta: List[float] = []
    for u in p1_scan_u:
        k_a = gaussian_curvature(u, v_probe)
        k_fd = gaussian_curvature_numeric(u, v_probe)
        k_cs = gaussian_curvature_complex_step(u, v_probe)
        p1_k_analytic.append(k_a)
        p1_k_fd.append(k_fd)
        p1_k_cs.append(k_cs)
        p1_max_delta.append(max(abs(k_a - k_fd), abs(k_a - k_cs)))
    # The strict-negativity certificate: worst (max, i.e. closest to 0) interior K.
    p1_k_worst = assert_mobius_K_negative()

    # Panel 2 -- trace the zero set R^{-1}(0) and reveal it point-by-point.
    columns = trace_columns(n_u=trace_n_u, n_v_samples=trace_n_v_samples)
    points = flatten_columns(columns)
    p2_curve_u = [p.u for p in points]
    p2_curve_v = [p.v for p in points]
    n_pts = len(points)
    p2_reveal = [
        max(1, min(n_pts, round((p + 1) * n_pts / active))) if n_pts else 0
        for p in range(active)
    ]

    # Panel 4 -- torus closed-form K(theta) curve + a scan line sweeping theta.
    p4_theta = linspace(0.0, TWO_PI, curve_samples)
    p4_k = [gaussian_curvature_closed(t) for t in p4_theta]
    p4_scan_theta = linspace(0.0, TWO_PI, active)
    p4_scan_k = [gaussian_curvature_closed(t) for t in p4_scan_theta]

    return FourPanelData(
        active=active,
        p1_v_probe=v_probe,
        p1_scan_u=p1_scan_u,
        p1_k_analytic=p1_k_analytic,
        p1_k_fd=p1_k_fd,
        p1_k_cs=p1_k_cs,
        p1_max_delta=p1_max_delta,
        p1_k_worst=p1_k_worst,
        p2_curve_u=p2_curve_u,
        p2_curve_v=p2_curve_v,
        p2_reveal=p2_reveal,
        p4_theta=p4_theta,
        p4_k=p4_k,
        p4_scan_theta=p4_scan_theta,
        p4_scan_k=p4_scan_k,
        p4_zero_circles=zero_circles(),
    )


_BANNER = (
    "Central Finite Curve: two readings (zero-set R^-1(0) vs SCMS ridge); "
    "Mobius is ruled so K<0 everywhere => the curve is R's zero-set; "
    "the torus is non-ruled so K itself changes sign."
)


# ---------------------------------------------------------------------------
# Lazy backend loading (matplotlib / Pillow / numpy reached only here)
# ---------------------------------------------------------------------------

def _load_backends_2d() -> Tuple[Any, Any]:
    """Return ``(pyplot, animation)`` on the headless Agg backend, or raise.

    matplotlib, matplotlib.pyplot, matplotlib.animation AND Pillow are reached
    lazily via :func:`commons.core.optional.try_import` (a 2-D scene, no mplot3d).
    Raises :class:`OptionalDependencyError` when any is absent; never silently
    degrades. The Agg backend keeps rendering headless and deterministic.
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
    """Return numpy for the backdrop meshes / SCMS history, or raise clearly."""
    numpy = try_import("numpy")
    if numpy is None:  # pragma: no cover - matplotlib depends on numpy in practice
        raise OptionalDependencyError(
            "the four-panel explainer requires numpy, which is not installed."
        )
    return numpy


# ---------------------------------------------------------------------------
# Per-panel drawing (each clears its axis and redraws for the given frame index)
# ---------------------------------------------------------------------------

def _draw_mobius_k(ax: Any, np: Any, mesh_u: Any, mesh_v: Any, k_field: Any,
                   data: FourPanelData, p: int) -> None:
    """Panel 1: Mobius K heatmap (K < 0 everywhere) + a scan line sweeping u."""
    ax.clear()
    ax.pcolormesh(mesh_u, mesh_v, k_field, cmap="viridis", shading="auto")
    scan_u = data.p1_scan_u[p]
    ax.axvline(scan_u, color="white", linewidth=1.5)
    ax.axhline(data.p1_v_probe, color="white", linestyle=":", linewidth=0.8)
    ax.set_xlim(U_MIN, U_MAX)
    ax.set_title("1) Mobius strip: ruled => K < 0", fontsize=9)
    ax.set_xlabel("u", fontsize=8)
    ax.set_ylabel("v", fontsize=8)
    ax.text(
        0.03, 0.94,
        f"K < 0 strictly (max K = {data.p1_k_worst:+.4f})\n"
        f"u = {scan_u:.3f}, v = {data.p1_v_probe:.2f}\n"
        f"analytic={data.p1_k_analytic[p]:+.5f}\n"
        f"fd={data.p1_k_fd[p]:+.5f}  cs={data.p1_k_cs[p]:+.5f}\n"
        f"max|analytic - numeric| = {data.p1_max_delta[p]:.1e}",
        transform=ax.transAxes, va="top", ha="left", fontsize=6.5, color="white",
    )


def _draw_zero_set(ax: Any, np: Any, mesh_u: Any, mesh_v: Any, r_field: Any,
                   data: FourPanelData, p: int) -> None:
    """Panel 2: faint R sign-map with the traced zero set drawn in point-by-point."""
    ax.clear()
    ax.pcolormesh(mesh_u, mesh_v, r_field, cmap="RdBu", shading="auto", alpha=0.5)
    n = data.p2_reveal[p]
    if n > 0:
        ax.plot(
            data.p2_curve_u[:n], data.p2_curve_v[:n],
            linestyle="none", marker="o", markersize=2.5, color="black",
            label="R^-1(0) (drawn in)",
        )
        ax.legend(loc="upper right", fontsize=6)
    ax.set_xlim(U_MIN, U_MAX)
    ax.set_title("2) Central Finite Curve = R^-1(0)", fontsize=9)
    ax.set_xlabel("u", fontsize=8)
    ax.set_ylabel("v", fontsize=8)
    total = len(data.p2_curve_u)
    ax.text(
        0.03, 0.94,
        f"boundary: Rick+ | Rick-\ntraced {n}/{total} zero points",
        transform=ax.transAxes, va="top", ha="left", fontsize=6.5,
    )


def _draw_scms(ax: Any, np: Any, mesh_u: Any, mesh_v: Any, r_field: Any,
               snapshots: List[Any], residuals: List[float], kept_uv: Any,
               k: int) -> None:
    """Panel 3: SCMS seed cloud migrating onto the ridge (frame k = iteration k)."""
    ax.clear()
    ax.pcolormesh(mesh_u, mesh_v, r_field, cmap="RdBu", shading="auto", alpha=0.35)
    if kept_uv is not None and len(kept_uv):
        ax.scatter(kept_uv[:, 0], kept_uv[:, 1], s=12, color="darkorange",
                   alpha=0.35, marker="x", label="converged ridge")
    snap = snapshots[k]
    ax.scatter(snap[:, 0], snap[:, 1], s=14, color="tab:green",
               marker="o", label="migrating seeds")
    ax.legend(loc="upper right", fontsize=6)
    ax.set_xlim(U_MIN, U_MAX)
    ax.set_title(
        f"3) SCMS ridge: iter {k}/{len(snapshots) - 1}  "
        f"mean|grad.e_minor|={residuals[k]:.2e}",
        fontsize=8,
    )
    ax.set_xlabel("u", fontsize=8)
    ax.set_ylabel("v", fontsize=8)


def _draw_torus_k(ax: Any, data: FourPanelData, p: int) -> None:
    """Panel 4: torus K(theta) curve + a scan line sweeping theta; K=0 circles marked."""
    ax.clear()
    ax.plot(data.p4_theta, data.p4_k, color="tab:purple", linewidth=1.5)
    ax.axhline(0.0, color="grey", linewidth=0.8)
    scan_theta = data.p4_scan_theta[p]
    ax.axvline(scan_theta, color="tab:red", linewidth=1.5)
    for z in data.p4_zero_circles:
        ax.axvline(z, color="black", linestyle=":", linewidth=1.0)
    ax.set_xlim(0.0, TWO_PI)
    ax.set_title("4) Torus: non-ruled => K changes sign", fontsize=9)
    ax.set_xlabel("theta", fontsize=8)
    ax.set_ylabel("K(theta)", fontsize=8)
    sign = "+" if data.p4_scan_k[p] > 0 else ("-" if data.p4_scan_k[p] < 0 else "0")
    ax.text(
        0.03, 0.94,
        f"+ outer / - inner half\nK=0 at pi/2, 3pi/2\n"
        f"theta = {scan_theta:.3f}, K = {data.p4_scan_k[p]:+.4f} ({sign})",
        transform=ax.transAxes, va="top", ha="left", fontsize=6.5,
    )


# ---------------------------------------------------------------------------
# The composite 2x2 animation shared by the GIF/MP4 savers
# ---------------------------------------------------------------------------

def _build_four_panel_animation(
    *,
    frames: int,
    hold: int,
    grid_n_u: int,
    grid_n_v: int,
    trace_n_u: int,
    trace_n_v_samples: int,
    seed_n_u: int,
    seed_n_v: int,
    scms_tol: float,
    scms_max_iter: int,
    curve_samples: int,
) -> Tuple[Any, Any, Any, Any]:
    """Build the 2x2 four-panel :class:`FuncAnimation` (shared by the savers).

    ``frames`` is the TOTAL number of frames; the last ``min(hold, frames - 1)`` are
    HOLD frames that freeze every panel at its final state and reveal the summary
    banner. Panels 1/2/4 come from the pure :func:`four_panel_frame_data`; Panel 3
    from the numpy-backed :func:`scms_ridge_history`. Returns
    ``(pyplot, animation, figure, anim)`` so the caller picks the writer. Raises
    :class:`ValueError` for bad arguments and :class:`OptionalDependencyError` when
    matplotlib/Pillow/numpy are absent.
    """
    if frames < 1:
        raise ValueError("frames must be >= 1")
    if hold < 0:
        raise ValueError("hold must be >= 0")

    hold_frames = min(hold, frames - 1) if frames > 1 else 0
    active = frames - hold_frames

    np = _require_numpy()
    data = four_panel_frame_data(
        active, curve_samples=curve_samples,
        trace_n_u=trace_n_u, trace_n_v_samples=trace_n_v_samples,
    )

    # Local imports: keep the module importable with the stdlib alone (numpy-gated).
    from mobius_rickness.core.geometry import mobius_seam_wrap
    from mobius_rickness.core.rickness import rickness
    from mobius_rickness.core.mobius import V_MAX, V_MIN
    from mobius_rickness.ridge import mobius_seeds, scms_ridge_history

    # Shared (u, v) background meshes for Panels 1/2/3 from the pure core grid.
    grid = evaluate_grid(n_u=grid_n_u, n_v=grid_n_v)
    mesh_u, mesh_v = np.meshgrid(np.asarray(grid.us), np.asarray(grid.vs))
    k_field = np.asarray(grid.K)
    r_field = np.asarray(grid.R)

    # Panel 3: the SCMS ridge convergence history (numpy-backed, real core field).
    seeds = mobius_seeds(n_u=seed_n_u, n_v=seed_n_v)
    history = scms_ridge_history(
        rickness, seeds, wrap=mobius_seam_wrap,
        tol=scms_tol, max_iter=scms_max_iter, v_bounds=(V_MIN, V_MAX),
    )
    snapshots = history.snapshots
    residuals = history.residuals
    n_snap = len(snapshots)
    kept = [p for p in history.points if p.converged and p.minor_eigval < 0.0]
    kept_uv = np.array([[p.u, p.v] for p in kept], dtype=float) if kept else None

    pyplot, animation = _load_backends_2d()
    figure, axes = pyplot.subplots(2, 2, figsize=(11.0, 7.5))
    figure.suptitle(
        "The Central Finite Curve: Mobius (ruled, K<0) vs Torus (K changes sign)",
        fontsize=12, y=0.99,
    )
    banner = figure.text(0.5, 0.005, "", ha="center", va="bottom",
                         fontsize=9, color="firebrick", fontweight="bold", wrap=True)
    ax_k, ax_zero = axes[0][0], axes[0][1]
    ax_scms, ax_torus = axes[1][0], axes[1][1]

    def update(frame: int) -> Tuple[Any, ...]:
        p = min(frame, active - 1)
        # Panel 3 iteration index maps the shared timeline onto the SCMS history.
        if active > 1:
            k = min(round(p * (n_snap - 1) / (active - 1)), n_snap - 1)
        else:
            k = n_snap - 1
        _draw_mobius_k(ax_k, np, mesh_u, mesh_v, k_field, data, p)
        _draw_zero_set(ax_zero, np, mesh_u, mesh_v, r_field, data, p)
        _draw_scms(ax_scms, np, mesh_u, mesh_v, r_field, snapshots, residuals,
                   kept_uv, k)
        _draw_torus_k(ax_torus, data, p)
        banner.set_text(_BANNER if frame >= active else "")
        return (ax_k, ax_zero, ax_scms, ax_torus, banner)

    figure.tight_layout(rect=(0.0, 0.05, 1.0, 0.96))
    anim = animation.FuncAnimation(figure, update, frames=frames, blit=False)
    return pyplot, animation, figure, anim


def save_four_panels_gif(
    path: str,
    *,
    frames: int = 44,
    hold: int = 8,
    fps: int = 8,
    grid_n_u: int = _GRID_N_U,
    grid_n_v: int = _GRID_N_V,
    trace_n_u: int = _TRACE_N_U,
    trace_n_v_samples: int = _TRACE_N_V_SAMPLES,
    seed_n_u: int = _SEED_N_U,
    seed_n_v: int = _SEED_N_V,
    scms_tol: float = _SCMS_TOL,
    scms_max_iter: int = _SCMS_MAX_ITER,
    curve_samples: int = _CURVE_SAMPLES,
) -> str:
    """Render the four-panel composite explainer as a GIF at ``path``.

    All four panels animate together on a 2x2 grid over a shared timeline and end on
    a HOLD frame showing the summary banner. Rendered with ``FuncAnimation`` +
    ``PillowWriter``; matplotlib, Pillow and numpy are imported lazily, so this
    raises :class:`OptionalDependencyError` when any is absent. Returns ``path``.
    """
    if fps < 1:
        raise ValueError("fps must be >= 1")
    pyplot, animation, figure, anim = _build_four_panel_animation(
        frames=frames, hold=hold,
        grid_n_u=grid_n_u, grid_n_v=grid_n_v,
        trace_n_u=trace_n_u, trace_n_v_samples=trace_n_v_samples,
        seed_n_u=seed_n_u, seed_n_v=seed_n_v,
        scms_tol=scms_tol, scms_max_iter=scms_max_iter,
        curve_samples=curve_samples,
    )
    anim.save(path, writer=animation.PillowWriter(fps=fps))
    pyplot.close(figure)
    return path


def save_four_panels_mp4(
    path: str,
    *,
    frames: int = 44,
    hold: int = 8,
    fps: int = 8,
    bitrate: int = _DEFAULT_BITRATE,
    grid_n_u: int = _GRID_N_U,
    grid_n_v: int = _GRID_N_V,
    trace_n_u: int = _TRACE_N_U,
    trace_n_v_samples: int = _TRACE_N_V_SAMPLES,
    seed_n_u: int = _SEED_N_U,
    seed_n_v: int = _SEED_N_V,
    scms_tol: float = _SCMS_TOL,
    scms_max_iter: int = _SCMS_MAX_ITER,
    curve_samples: int = _CURVE_SAMPLES,
) -> str:
    """Encode the four-panel composite explainer as an MP4 at ``path`` (ffmpeg).

    Reuses the exact :func:`save_four_panels_gif` scene but writes it with
    :class:`matplotlib.animation.FFMpegWriter`. matplotlib/numpy are imported lazily
    and ffmpeg availability is checked at call time (via
    :func:`mobius_rickness.adapters.animate_3d.ffmpeg_is_available`); raises
    :class:`OptionalDependencyError` when matplotlib, numpy or an ffmpeg binary is
    absent. Returns ``path``.
    """
    if fps < 1:
        raise ValueError("fps must be >= 1")
    if not ffmpeg_is_available():  # fail fast, before building the scene
        raise OptionalDependencyError(_MP4_HELP)
    pyplot, animation, figure, anim = _build_four_panel_animation(
        frames=frames, hold=hold,
        grid_n_u=grid_n_u, grid_n_v=grid_n_v,
        trace_n_u=trace_n_u, trace_n_v_samples=trace_n_v_samples,
        seed_n_u=seed_n_u, seed_n_v=seed_n_v,
        scms_tol=scms_tol, scms_max_iter=scms_max_iter,
        curve_samples=curve_samples,
    )
    writer = _ffmpeg_writer(animation, fps=fps, bitrate=bitrate)
    anim.save(path, writer=writer)
    pyplot.close(figure)
    return path
