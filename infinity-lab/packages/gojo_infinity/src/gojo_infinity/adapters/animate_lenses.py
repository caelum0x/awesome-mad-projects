"""Four-lens composite explainer animation (DEFERRED behind matplotlib + PIL/ffmpeg).

A single composite animation that tells the whole essay's arc: ALL FOUR lenses of
Gojo's Infinity animating together on a 2x2 grid of subplots with a shared frame
timeline and a suptitle. Each panel animates its lens and shows its verdict:

    * Panel 1 -- Geometric series (Zeno) -> FRAGILE: the partial sums
      ``S_n = 1 - (1/2)^n`` fill toward the dashed limit at ``1`` as ``n`` grows.
    * Panel 2 -- Lebesgue measure -> FRAGILE: the covering intervals ``I_n`` around
      the points ``z_n = 1 - 1/2^n`` shrink as ``eps`` decreases, total length
      label ``= eps -> 0`` (illustrating ``m(Z) = 0``).
    * Panel 3 -- Riemannian geometry -> FORMIDABLE: the conformal factor
      ``Omega(x)`` with a marker approaching Gojo (``x -> 1``) frame by frame and a
      readout of the felt geodesic length climbing toward ``+infinity``.
    * Panel 4 -- Topology -> FALLS: ``Omega(x)`` shown continuous, then a cut
      appears at ``c`` that severs continuity, splitting the domain into two
      connected components ("continuity destroyed").

It ends on a HOLD frame showing the full verdict table
``Fragile / Fragile / Formidable / Falls``.

Every number is pulled from the REAL pure core (never fabricated):
:func:`gojo_infinity.core.partial_sum` (Lens 1),
:func:`gojo_infinity.core.subdivision_point` / ``cover_interval_length`` /
``outer_measure_upper_bound`` (Lens 2), :func:`gojo_infinity.core.conformal_factor`
/ ``geodesic_length`` (Lens 3) and :func:`gojo_infinity.core.component_count` /
``severed`` continuity (Lens 4). The numeric sequences are assembled by the pure
:func:`four_lens_frame_data` (stdlib + core only), so they are testable without any
scientific dependency.

Like its siblings this is an adapter: it may import ``core`` but ``core`` never
imports it, and matplotlib/Pillow/ffmpeg are reached ONLY lazily (through the
shared helpers in :mod:`gojo_infinity.adapters.animate`). Absent a dependency the
renderers raise :class:`OptionalDependencyError` rather than failing at import
time, so this module stays importable with the standard library alone.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Any, List, Tuple

from gojo_infinity.adapters.animate import (
    _DEFAULT_BITRATE,
    _MP4_HELP,
    _ffmpeg_writer,
    _load_backends,
    ffmpeg_is_available,
)
from gojo_infinity.adapters.viz import OptionalDependencyError
from gojo_infinity.core import (
    X_GOJO,
    component_count,
    conformal_factor,
    geodesic_length,
    outer_measure_upper_bound,
    partial_sum,
    residual,
    subdivision_point,
    verdict_labels,
)
from gojo_infinity.core.measure import cover_interval_length

# ---------------------------------------------------------------------------
# Scene constants (shared by the pure data builder and the renderer)
# ---------------------------------------------------------------------------

_MEASURE_POINTS: int = 5           # how many z_n points to cover in Panel 2
_MEASURE_EPS0: Fraction = Fraction(1, 4)  # starting cover budget eps
_RIEM_X0: float = 0.5              # attacker start for Lens 3 felt length
_RIEM_BASE_GAP: float = 0.4        # first (x_gojo - x) gap for the marker
_RIEM_SHRINK: float = 0.5          # gap halves each frame -> x -> x_gojo
_RIEM_Y_CAP: float = 8.0           # Omega y-axis cap (curve clipped for display)
_TOPO_X0: float = 0.1              # Panel 4 domain [x0, x1]
_TOPO_X1: float = 0.9
_TOPO_CUT: float = 0.5             # the World-Cutting Slash point c
_TOPO_JUMP: float = 1.5            # visual tear height added on the right of c
_TOPO_Y_CAP: float = 6.0
_CURVE_SAMPLES: int = 120


@dataclass(frozen=True)
class FourLensData:
    """Immutable numeric sequences for every panel, sourced from the pure core.

    All lists have length ``active`` along the frame axis (except the static
    curves and per-point ``measure_points``). Assembled by
    :func:`four_lens_frame_data`; consumed by the renderer. Kept dependency free
    (stdlib + ``gojo_infinity.core`` only) so it is testable without matplotlib.
    """

    active: int
    # Panel 1 -- Zeno
    zeno_n: List[int]
    zeno_S: List[float]
    zeno_residual: List[float]
    # Panel 2 -- measure
    measure_points: List[float]
    measure_eps: List[float]
    measure_widths: List[List[float]]
    measure_total: List[float]
    # Panel 3 -- Riemannian
    riem_x0: float
    riem_curve_x: List[float]
    riem_curve_omega: List[float]
    riem_x_marks: List[float]
    riem_felt: List[float]
    # Panel 4 -- topology
    topo_x0: float
    topo_x1: float
    topo_cut: float
    topo_jump: float
    topo_cut_frame: int
    topo_curve_x: List[float]
    topo_curve_omega: List[float]
    topo_components: List[int]


def _linspace(lo: float, hi: float, count: int) -> List[float]:
    """A small stdlib ``linspace`` (``count`` points from ``lo`` to ``hi`` inclusive)."""
    if count < 2:
        return [lo]
    step = (hi - lo) / (count - 1)
    return [lo + i * step for i in range(count)]


def four_lens_frame_data(active: int) -> FourLensData:
    """Build every panel's numeric sequences from the REAL pure core.

    ``active`` is the number of animated (non-hold) frames. Raises
    :class:`ValueError` for ``active < 1``. This function imports nothing beyond
    the standard library and :mod:`gojo_infinity.core`, so it is exercised in a
    dependency-free test that asserts the panels source genuine core values.
    """
    if active < 1:
        raise ValueError("active must be >= 1")

    # Panel 1 -- Zeno partial sums S_n = 1 - (1/2)^n (exact core -> float).
    zeno_n = list(range(1, active + 1))
    zeno_S = [float(partial_sum(n)) for n in zeno_n]
    zeno_residual = [float(residual(n)) for n in zeno_n]

    # Panel 2 -- covering the null set Z with a shrinking budget eps.
    measure_points = [float(subdivision_point(n)) for n in range(1, _MEASURE_POINTS + 1)]
    measure_eps: List[float] = []
    measure_widths: List[List[float]] = []
    measure_total: List[float] = []
    for p in range(active):
        eps = _MEASURE_EPS0 * Fraction(1, 2) ** p
        widths = [
            float(cover_interval_length(n, eps)) for n in range(1, _MEASURE_POINTS + 1)
        ]
        measure_eps.append(float(eps))
        measure_widths.append(widths)
        measure_total.append(float(outer_measure_upper_bound(eps)))

    # Panel 3 -- Omega(x) curve + a marker whose felt length climbs toward +inf.
    riem_curve_x = _linspace(0.0, 0.9, _CURVE_SAMPLES)
    riem_curve_omega = [conformal_factor(x) for x in riem_curve_x]
    riem_x_marks: List[float] = []
    riem_felt: List[float] = []
    for p in range(active):
        gap = _RIEM_BASE_GAP * (_RIEM_SHRINK ** p)
        x_mark = X_GOJO - gap
        riem_x_marks.append(x_mark)
        riem_felt.append(geodesic_length(_RIEM_X0, x_mark))

    # Panel 4 -- intact Omega, then a cut severs it at c halfway through.
    topo_curve_x = _linspace(_TOPO_X0, _TOPO_X1, _CURVE_SAMPLES)
    topo_curve_omega = [conformal_factor(x) for x in topo_curve_x]
    topo_cut_frame = max(1, active // 2)
    topo_components = [
        component_count(_TOPO_X0, _TOPO_X1, None if p < topo_cut_frame else _TOPO_CUT)
        for p in range(active)
    ]

    return FourLensData(
        active=active,
        zeno_n=zeno_n,
        zeno_S=zeno_S,
        zeno_residual=zeno_residual,
        measure_points=measure_points,
        measure_eps=measure_eps,
        measure_widths=measure_widths,
        measure_total=measure_total,
        riem_x0=_RIEM_X0,
        riem_curve_x=riem_curve_x,
        riem_curve_omega=riem_curve_omega,
        riem_x_marks=riem_x_marks,
        riem_felt=riem_felt,
        topo_x0=_TOPO_X0,
        topo_x1=_TOPO_X1,
        topo_cut=_TOPO_CUT,
        topo_jump=_TOPO_JUMP,
        topo_cut_frame=topo_cut_frame,
        topo_curve_x=topo_curve_x,
        topo_curve_omega=topo_curve_omega,
        topo_components=topo_components,
    )


# ---------------------------------------------------------------------------
# Per-panel drawing (each clears its axis and redraws for the given frame index)
# ---------------------------------------------------------------------------

def _draw_zeno(ax: Any, data: FourLensData, p: int) -> None:
    """Panel 1: partial sums S_n filling toward the dashed limit at 1."""
    ax.clear()
    ns = data.zeno_n[: p + 1]
    ss = data.zeno_S[: p + 1]
    ax.bar(ns, ss, color="tab:blue", width=0.8)
    ax.axhline(1.0, linestyle="--", color="grey")
    ax.set_xlim(0.5, data.active + 0.5)
    ax.set_ylim(0.0, 1.1)
    ax.set_title("1) Geometric series (Zeno) -> FRAGILE", fontsize=9)
    ax.set_xlabel("n", fontsize=8)
    ax.set_ylabel("S_n = 1 - (1/2)^n", fontsize=8)
    ax.text(
        0.03, 0.92,
        f"n = {data.zeno_n[p]}\nS_n = {data.zeno_S[p]:.6f}\nresidual = {data.zeno_residual[p]:.2e}",
        transform=ax.transAxes, va="top", ha="left", fontsize=7,
    )


def _draw_measure(ax: Any, data: FourLensData, p: int) -> None:
    """Panel 2: covering intervals shrinking as eps decreases (m(Z) = 0)."""
    ax.clear()
    widths = data.measure_widths[p]
    for x_center, w in zip(data.measure_points, widths):
        half = w / 2.0
        ax.plot([x_center - half, x_center + half], [0.0, 0.0],
                color="tab:orange", linewidth=6, solid_capstyle="butt")
        ax.plot([x_center], [0.0], marker="|", color="black", markersize=8)
    ax.set_xlim(0.4, 1.02)
    ax.set_ylim(-1.0, 1.0)
    ax.set_yticks([])
    ax.axvline(X_GOJO, linestyle="--", color="grey")
    ax.set_title("2) Lebesgue measure -> FRAGILE", fontsize=9)
    ax.set_xlabel("z_n = 1 - 1/2^n  (covered by I_n)", fontsize=8)
    ax.text(
        0.03, 0.92,
        f"eps = {data.measure_eps[p]:.3e}\ntotal length = {data.measure_total[p]:.3e}\nm(Z) -> 0",
        transform=ax.transAxes, va="top", ha="left", fontsize=7,
    )


def _draw_riemannian(ax: Any, data: FourLensData, p: int) -> None:
    """Panel 3: Omega(x) with a marker approaching Gojo, felt length climbing."""
    ax.clear()
    ax.plot(data.riem_curve_x, data.riem_curve_omega, color="tab:green", linewidth=1.5)
    x_mark = data.riem_x_marks[p]
    ax.axvline(x_mark, color="tab:red", linewidth=1.5)
    ax.axvline(X_GOJO, linestyle="--", color="grey")
    ax.plot([X_GOJO], [0.2], marker="*", markersize=12, color="black")
    ax.set_xlim(0.0, 1.02)
    ax.set_ylim(0.0, _RIEM_Y_CAP)
    ax.set_title("3) Riemannian geometry -> FORMIDABLE", fontsize=9)
    ax.set_xlabel("x  (Gojo at x = 1)", fontsize=8)
    ax.set_ylabel("Omega(x)", fontsize=8)
    ax.text(
        0.03, 0.92,
        f"x = {x_mark:.6f}\nfelt length = {data.riem_felt[p]:.3f}\n-> +infinity",
        transform=ax.transAxes, va="top", ha="left", fontsize=7,
    )


def _draw_topology(ax: Any, data: FourLensData, p: int) -> None:
    """Panel 4: continuous Omega, then a cut at c severs it into two components."""
    ax.clear()
    severed = data.topo_components[p] > 1
    xs, om = data.topo_curve_x, data.topo_curve_omega
    if not severed:
        ax.plot(xs, om, color="tab:purple", linewidth=1.5)
        detail = "continuous (1 component)"
    else:
        left_x = [x for x in xs if x < data.topo_cut]
        left_y = [conformal_factor(x) for x in left_x]
        right_x = [x for x in xs if x > data.topo_cut]
        right_y = [conformal_factor(x) + data.topo_jump for x in right_x]
        ax.plot(left_x, left_y, color="tab:purple", linewidth=1.5)
        ax.plot(right_x, right_y, color="tab:purple", linewidth=1.5)
        ax.axvline(data.topo_cut, color="tab:red", linestyle=":", linewidth=2)
        ax.text(data.topo_cut, _TOPO_Y_CAP * 0.9, "cut c", color="tab:red",
                ha="center", fontsize=7)
        detail = "continuity destroyed (2 components)"
    ax.set_xlim(data.topo_x0, data.topo_x1)
    ax.set_ylim(0.0, _TOPO_Y_CAP)
    ax.set_title("4) Topology -> FALLS", fontsize=9)
    ax.set_xlabel("x", fontsize=8)
    ax.set_ylabel("Omega(x)", fontsize=8)
    ax.text(
        0.03, 0.92,
        f"components = {data.topo_components[p]}\n{detail}",
        transform=ax.transAxes, va="top", ha="left", fontsize=7,
    )


def _verdict_banner_text() -> str:
    """The final hold-frame verdict row, e.g. 'Fragile | Fragile | Formidable | Falls'."""
    return "VERDICTS:  " + "  |  ".join(verdict_labels())


# ---------------------------------------------------------------------------
# The composite 2x2 animation shared by the GIF/MP4 savers
# ---------------------------------------------------------------------------

def _build_four_lens_animation(*, frames: int, hold: int) -> Tuple[Any, Any, Any, Any]:
    """Build the 2x2 four-lens :class:`FuncAnimation` (shared by the savers).

    ``frames`` is the TOTAL number of frames; the last ``min(hold, frames - 1)``
    are HOLD frames that freeze every panel at its final state and reveal the
    verdict table banner. Every numeric value comes from
    :func:`four_lens_frame_data` (the real pure core). Returns
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
    data = four_lens_frame_data(active)

    pyplot, animation = _load_backends()
    figure, axes = pyplot.subplots(2, 2, figsize=(10.0, 7.0))
    figure.suptitle(
        "Gojo's Infinity through four mathematical lenses", fontsize=13, y=0.98
    )
    banner = figure.text(0.5, 0.005, "", ha="center", va="bottom",
                         fontsize=11, color="firebrick", fontweight="bold")
    ax_zeno, ax_measure = axes[0][0], axes[0][1]
    ax_riem, ax_topo = axes[1][0], axes[1][1]

    def update(frame: int) -> Tuple[Any, ...]:
        p = min(frame, active - 1)
        _draw_zeno(ax_zeno, data, p)
        _draw_measure(ax_measure, data, p)
        _draw_riemannian(ax_riem, data, p)
        _draw_topology(ax_topo, data, p)
        banner.set_text(_verdict_banner_text() if frame >= active else "")
        return (ax_zeno, ax_measure, ax_riem, ax_topo, banner)

    figure.tight_layout(rect=(0.0, 0.04, 1.0, 0.96))
    anim = animation.FuncAnimation(figure, update, frames=frames, blit=False)
    return pyplot, animation, figure, anim


def save_four_lenses_gif(
    path: str,
    *,
    frames: int = 44,
    hold: int = 8,
    fps: int = 8,
) -> str:
    """Render the four-lens composite explainer as a GIF at ``path``.

    All four lenses animate together on a 2x2 grid over a shared timeline and end
    on a HOLD frame showing the verdict table. Rendered with matplotlib
    ``FuncAnimation`` + ``PillowWriter``; matplotlib and Pillow are imported
    lazily, so this raises :class:`OptionalDependencyError` when either is absent.
    Returns ``path``.
    """
    if fps < 1:
        raise ValueError("fps must be >= 1")
    pyplot, animation, figure, anim = _build_four_lens_animation(frames=frames, hold=hold)
    anim.save(path, writer=animation.PillowWriter(fps=fps))
    pyplot.close(figure)
    return path


def save_four_lenses_mp4(
    path: str,
    *,
    frames: int = 44,
    hold: int = 8,
    fps: int = 8,
    bitrate: int = _DEFAULT_BITRATE,
) -> str:
    """Encode the four-lens composite explainer as an MP4 at ``path`` (ffmpeg).

    Reuses the exact :func:`save_four_lenses_gif` scene but writes it with
    :class:`matplotlib.animation.FFMpegWriter`. matplotlib is imported lazily and
    ffmpeg availability is checked at call time; raises
    :class:`OptionalDependencyError` when matplotlib or an ffmpeg binary is
    absent. Returns ``path``.
    """
    if fps < 1:
        raise ValueError("fps must be >= 1")
    if not ffmpeg_is_available():  # fail fast, before building the scene
        raise OptionalDependencyError(_MP4_HELP)
    pyplot, animation, figure, anim = _build_four_lens_animation(frames=frames, hold=hold)
    writer = _ffmpeg_writer(animation, fps=fps, bitrate=bitrate)
    anim.save(path, writer=writer)
    pyplot.close(figure)
    return path
