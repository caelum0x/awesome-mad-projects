"""Command-line front end for the Mobius-Rickness curvature story.

``argparse`` subcommands, each a thin wrapper over :mod:`mobius_rickness.core`
(and, for the ``--ascii`` option, :mod:`mobius_rickness.adapters.viz`):

    curvature   Mobius Gaussian curvature K < 0 strictly + reproduced table
    trace       trace the Central Finite Curve R^{-1}(0) and list (u,v,x,y,z)
    torus       torus K sign pattern + the two geometry-driven zero circles
    all         run all three and print them in order
    animate     render a rotating 3-D GIF (and, with --mp4, an MP4) of the strip
                overlaying both Central Finite Curve readings under an orbiting camera

Each subcommand prints a stable, greppable headline line and the numeric
evidence, so the output is easy to assert in tests. Pass ``--ascii`` (curvature
and trace only) to append the deterministic ASCII pictures.

Run:  python -m mobius_rickness.adapters.cli all
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

from mobius_rickness.core import (
    R0_DEFAULT,
    R_MINOR_DEFAULT,
    assert_curvature_negative,
    flatten_columns,
    gaussian_curvature,
    gaussian_curvature_closed,
    gaussian_curvature_complex_step,
    gaussian_curvature_numeric,
    trace_columns,
    trace_torus_zero_circles,
    verify_curve,
    zero_circles,
)
from mobius_rickness.core import torus as torus_core

from mobius_rickness.adapters import animate_3d, animate_panels, animate_scms, viz

# theta samples for the torus sign-pattern table (label, radians).
_TORUS_SAMPLES: Tuple[Tuple[str, float], ...] = (
    ("0 (outer)", 0.0),
    ("pi/4", math.pi / 4.0),
    ("pi/2 (top)", math.pi / 2.0),
    ("3pi/4", 3.0 * math.pi / 4.0),
    ("pi (inner)", math.pi),
    ("5pi/4", 5.0 * math.pi / 4.0),
    ("3pi/2 (bot)", 3.0 * math.pi / 2.0),
    ("7pi/4", 7.0 * math.pi / 4.0),
)

# Below this magnitude the closed-form torus K is reported as an exact zero.
_ZERO_TOL = 1e-9


def _rule(title: str) -> List[str]:
    """A boxed section header as a list of output lines."""
    bar = "=" * 70
    return [bar, title, bar]


# ---------------------------------------------------------------------------
# curvature -- Mobius K < 0 strictly + reproduced table
# ---------------------------------------------------------------------------

def render_curvature(*, ascii_art: bool = False) -> str:
    """Return the ``curvature`` report: strict negativity, three paths, table."""
    lines = _rule("CURVATURE -- Mobius strip: K < 0 strictly (ruled surface)")
    lines.append(
        "r(u,v) = ((1 + v cos(u/2)) cos u, (1 + v cos(u/2)) sin u, v sin(u/2))"
    )
    worst = assert_curvature_negative()
    lines.append(
        f"K < 0 strictly on the interior (worst / max K = {worst:+.6f})."
    )
    u0, v0 = math.pi / 3.0, 0.25
    k_analytic = gaussian_curvature(u0, v0)
    k_fd = gaussian_curvature_numeric(u0, v0)
    k_cs = gaussian_curvature_complex_step(u0, v0)
    max_delta = max(abs(k_analytic - k_fd), abs(k_analytic - k_cs))
    lines.append(
        "Three curvature paths at (u,v)=(pi/3, 0.25): "
        f"analytic={k_analytic:.9f}  fd={k_fd:.9f}  cs={k_cs:.9f}"
    )
    lines.append(f"max |analytic - numeric| = {max_delta:.2e}  (paths agree).")
    lines.append("")
    lines.append(viz.render_curvature_table())
    if ascii_art:
        lines.append("")
        lines.append(viz.render_rickness_sign_map())
        lines.append("")
        lines.append(viz.render_k_rick_heatmap())
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# trace -- the Central Finite Curve R^{-1}(0)
# ---------------------------------------------------------------------------

def render_trace(*, ascii_art: bool = False) -> str:
    """Return the ``trace`` report: traced zero-curve points lifted to 3D."""
    lines = _rule("TRACE -- Central Finite Curve = R^-1(0)")
    lines.append(
        "K < 0 everywhere  =>  K_Rick = K*R = 0  <=>  R = 0."
    )
    lines.append(
        "Sign-changing R = cos u + 0.4 v cos(u/2) + 0.2 sin u  (zero set is a curve)."
    )
    results = trace_columns(n_u=120, n_v_samples=200)
    points = flatten_columns(results)
    verify_curve(points, r_tol=1e-6, k_rick_tol=1e-6)
    n_cols_with_root = sum(1 for c in results if c.has_root)
    lines.append(
        f"Traced {len(points)} zero points across {len(results)} u-columns "
        f"({n_cols_with_root} columns contain a root)."
    )
    lines.append("All traced points verified: |R| < 1e-6 and |K_Rick| < 1e-6.")
    lines.append("")
    lines.append(
        f"{'u':>10} {'v':>10} {'x':>10} {'y':>10} {'z':>10} {'|R|':>10}"
    )
    lines.append("-" * 66)
    step = max(1, len(points) // 14)
    for p in points[::step]:
        lines.append(
            f"{p.u:>10.4f} {p.v:>+10.4f} {p.x:>+10.4f} {p.y:>+10.4f} "
            f"{p.z:>+10.4f} {p.residual:>10.1e}"
        )
    if ascii_art:
        lines.append("")
        lines.append(viz.render_rickness_sign_map())
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# torus -- geometry-driven zero circles (K changes sign)
# ---------------------------------------------------------------------------

def render_torus(*, ascii_art: bool = False) -> str:
    """Return the ``torus`` report: K sign pattern + traced zero circles."""
    lines = _rule("TORUS -- geometry-driven zero set (K changes sign)")
    lines.append(
        f"Torus radii R0={R0_DEFAULT}, r0={R_MINOR_DEFAULT}.  "
        "K(theta) = cos(theta) / (r0 (R0 + r0 cos theta))."
    )
    lines.append("")
    lines.append(
        f"{'theta':>12} {'K_closed':>14} {'K_numeric':>14} {'sign':>6}"
    )
    lines.append("-" * 50)
    for label, theta in _TORUS_SAMPLES:
        k_closed = gaussian_curvature_closed(theta)
        k_numeric = torus_core.gaussian_curvature(theta, 0.0)
        if k_closed > _ZERO_TOL:
            sign = "+"
        elif k_closed < -_ZERO_TOL:
            sign = "-"
        else:
            sign = "0"
        lines.append(
            f"{label:>12} {k_closed:>14.6f} {k_numeric:>14.6f} {sign:>6}"
        )
    lines.append("-" * 50)
    lines.append(
        "Sign pattern: POSITIVE outer half, NEGATIVE inner half, "
        "ZERO on the top/bottom circles."
    )
    zeros = trace_torus_zero_circles(n_theta=400)
    exact = zero_circles()
    lines.append(
        "Traced K=0 circles at theta = "
        + ", ".join(f"{z:.6f}" for z in zeros)
    )
    lines.append(
        "Exact                 theta = "
        + ", ".join(f"{e:.6f}" for e in exact)
        + "  (pi/2, 3pi/2)"
    )
    lines.append(
        "These two circles ARE the torus's Central Finite Curve: a real, "
        "geometry-driven zero set."
    )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# all
# ---------------------------------------------------------------------------

def render_all(*, ascii_art: bool = False) -> str:
    """Return every report (curvature, trace, torus) in order."""
    blocks = [
        render_curvature(ascii_art=ascii_art),
        render_trace(ascii_art=ascii_art),
        render_torus(ascii_art=ascii_art),
    ]
    return "\n\n".join(blocks)


# ---------------------------------------------------------------------------
# animate -- rotating 3-D GIF/MP4 of the strip with both CFC readings
# ---------------------------------------------------------------------------

# Output file names for the rotating animation exports.
_ROTATING_GIF = "mobius_rotating.gif"
_ROTATING_MP4 = "mobius_rotating.mp4"

# Output file names for the SCMS ridge-convergence animation exports.
_SCMS_GIF = "mobius_ridge_convergence.gif"
_SCMS_MP4 = "mobius_ridge_convergence.mp4"

# Output file names for the four-panel composite explainer exports.
_PANELS_GIF = "mobius_four_panels.gif"
_PANELS_MP4 = "mobius_four_panels.mp4"


def render_animate(
    outdir: str, *, mp4: bool = False, scms: bool = False, panels: bool = False
) -> str:
    """Write the rotating animation(s) into ``outdir`` and return a report string.

    Always writes the rotating 3-D GIF (needs matplotlib + Pillow). ``mp4``
    additionally writes the MP4 (needs an ffmpeg binary on PATH). ``scms``
    additionally writes the SCMS ridge-convergence animation (a 2-D ``(u, v)`` GIF of
    the seed cloud migrating onto the ridge; with ``mp4`` also its MP4). ``panels``
    additionally writes the four-panel composite explainer (a 2x2 GIF telling the
    whole Central Finite Curve story; needs matplotlib + Pillow + numpy; with
    ``mp4`` also its MP4). DEFERRED:
    :mod:`mobius_rickness.adapters.animate_3d` /
    :mod:`mobius_rickness.adapters.animate_scms` raise
    :class:`~mobius_rickness.adapters.viz.OptionalDependencyError` when a required
    backend is unavailable, so this propagates a clear error rather than silently
    skipping.
    """
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    written: List[str] = [animate_3d.save_mobius_rotating_gif(str(out / _ROTATING_GIF))]
    lines = _rule(
        "ANIMATE -- rotating Mobius strip with both Central Finite Curves"
    )
    lines.append(
        "Orbiting camera over the semi-transparent strip; overlays R^-1(0) (red) "
        "and the SCMS ridge (orange)."
    )
    lines.append("")
    lines.append("Rendered GIF (matplotlib FuncAnimation + PillowWriter):")
    lines.append(f"  {written[0]}")
    if mp4:
        mp4_path = animate_3d.save_mobius_rotating_mp4(str(out / _ROTATING_MP4))
        written.append(mp4_path)
        lines.append("")
        lines.append("Rendered MP4 (matplotlib FuncAnimation + FFMpegWriter):")
        lines.append(f"  {mp4_path}")
    if scms:
        scms_gif = animate_scms.save_ridge_convergence_gif(str(out / _SCMS_GIF))
        written.append(scms_gif)
        lines.append("")
        lines.append(
            "Rendered SCMS ridge-convergence GIF (seed cloud settling onto the "
            "ridge; mean residual -> 0):"
        )
        lines.append(f"  {scms_gif}")
        if mp4:
            scms_mp4 = animate_scms.save_ridge_convergence_mp4(str(out / _SCMS_MP4))
            written.append(scms_mp4)
            lines.append("")
            lines.append("Rendered SCMS ridge-convergence MP4 (FFMpegWriter):")
            lines.append(f"  {scms_mp4}")
    if panels:
        panels_gif = animate_panels.save_four_panels_gif(str(out / _PANELS_GIF))
        written.append(panels_gif)
        lines.append("")
        lines.append(
            "Rendered four-panel explainer GIF (2x2 Central Finite Curve story: "
            "Mobius K<0 scan, zero-set R^-1(0) draw-in, SCMS ridge, torus K sign):"
        )
        lines.append(f"  {panels_gif}")
        if mp4:
            panels_mp4 = animate_panels.save_four_panels_mp4(str(out / _PANELS_MP4))
            written.append(panels_mp4)
            lines.append("")
            lines.append("Rendered four-panel explainer MP4 (FFMpegWriter):")
            lines.append(f"  {panels_mp4}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# argparse wiring
# ---------------------------------------------------------------------------

_RENDERERS = {
    "curvature": render_curvature,
    "trace": render_trace,
    "torus": render_torus,
}

# Subcommands that expose the --ascii option (torus has no ASCII chart of its own).
_ASCII_COMMANDS = {"curvature", "trace", "all"}

# Subcommands that expose the --png OUTDIR option (matplotlib PNG exports).
_PNG_COMMANDS = {"curvature", "trace", "all"}

# File names for the three matplotlib PNG exports written by --png.
_PNG_FILES = (
    ("mobius_strip_cfc.png", "save_strip_3d_png"),
    ("k_rick_heatmap.png", "save_krick_heatmap_png"),
    ("mobius_ridge.png", "save_ridge_png"),
)


def _write_pngs(outdir: str) -> str:
    """Render the three matplotlib PNGs into ``outdir`` and return a summary block.

    DEFERRED behaviour: :func:`mobius_rickness.adapters.viz` raises
    :class:`~mobius_rickness.adapters.viz.OptionalDependencyError` when matplotlib
    is unavailable, so this propagates a clear error rather than silently skipping.
    """
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    written: List[str] = []
    for filename, func_name in _PNG_FILES:
        target = str(out / filename)
        getattr(viz, func_name)(target)
        written.append(target)
    lines = ["", "PNG exports written (matplotlib, headless Agg backend):"]
    lines.extend(f"  {path}" for path in written)
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser with one subcommand per report plus ``all``."""
    parser = argparse.ArgumentParser(
        prog="mobius-rickness",
        description=(
            "Mobius/torus Gaussian curvature and the Central Finite Curve "
            "R^{-1}(0)."
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True)
    descriptions = {
        "curvature": "Mobius K < 0 strictly (three paths) + reproduced table",
        "trace": "trace the Central Finite Curve R^{-1}(0) and list (u,v,x,y,z)",
        "torus": "torus K sign pattern + the two geometry-driven zero circles",
        "all": "run curvature, trace and torus in order",
        "animate": "render a rotating 3-D GIF/MP4 of the strip with both CFC readings",
    }
    for name, help_text in descriptions.items():
        p = sub.add_parser(name, help=help_text, description=help_text)
        if name == "animate":
            p.add_argument(
                "outdir",
                metavar="OUTDIR",
                help="directory to write the rotating animation(s) into "
                "(requires matplotlib + Pillow for the GIF, ffmpeg for the MP4)",
            )
            p.add_argument(
                "--mp4",
                action="store_true",
                help="also write the rotating MP4 (mobius_rotating.mp4); "
                "requires an ffmpeg binary on PATH",
            )
            p.add_argument(
                "--scms",
                action="store_true",
                help="also write the SCMS ridge-convergence animation "
                "(mobius_ridge_convergence.gif; with --mp4 also the .mp4): a 2-D "
                "(u,v) scene of the seed cloud migrating onto the ridge as the mean "
                "residual shrinks to ~0",
            )
            p.add_argument(
                "--panels",
                action="store_true",
                help="also write the four-panel composite explainer "
                "(mobius_four_panels.gif; with --mp4 also the .mp4): a 2x2 scene "
                "telling the whole Central Finite Curve story (Mobius K<0 scan, "
                "zero-set R^-1(0) draw-in, SCMS ridge convergence, torus K sign) -- "
                "requires matplotlib + Pillow + numpy",
            )
            continue
        if name in _ASCII_COMMANDS:
            p.add_argument(
                "--ascii",
                action="store_true",
                help="append the deterministic ASCII picture(s) for this report",
            )
        if name in _PNG_COMMANDS:
            p.add_argument(
                "--png",
                metavar="OUTDIR",
                default=None,
                help=(
                    "render matplotlib PNGs (strip+CFC, K_Rick heatmap, SCMS ridge) "
                    "into OUTDIR; requires the optional matplotlib dependency"
                ),
            )
    return parser


def run(argv: Optional[Sequence[str]] = None) -> str:
    """Resolve ``argv`` to the rendered report text (no printing).

    Kept side-effect free so tests can assert on the returned string.
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "animate":
        return render_animate(
            args.outdir,
            mp4=bool(getattr(args, "mp4", False)),
            scms=bool(getattr(args, "scms", False)),
            panels=bool(getattr(args, "panels", False)),
        )
    ascii_art = bool(getattr(args, "ascii", False))
    if args.command == "all":
        text = render_all(ascii_art=ascii_art)
    else:
        text = _RENDERERS[args.command](ascii_art=ascii_art)
    png_dir = getattr(args, "png", None)
    if png_dir:
        text = text + "\n" + _write_pngs(png_dir)
    return text


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry point: render the requested report and print it. Returns 0."""
    print(run(argv))
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised via run()/main()
    raise SystemExit(main())
