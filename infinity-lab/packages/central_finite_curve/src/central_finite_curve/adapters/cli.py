"""Command-line front end for the Central Finite Curve engine.

``argparse`` subcommands, each a thin wrapper over the pure
:mod:`central_finite_curve.core` pipeline (and, for ``--png`` / ``animate``, the
lazily-guarded viz/animation adapters):

    generate   seed the multiverse and report the Rickness landscape
    curve      extract the near-maximal band (the Central Finite Curve)
    walk       fire the portal gun and report the acceptance ratio
    project    project curve + walk to 2-D and print the ASCII scatter
    all        run the whole pipeline end to end (the canonical report)
    animate    render the walk GIF (and, with --mp4, an MP4) into OUTDIR

Each subcommand prints a stable, greppable headline plus numeric evidence, so the
output is easy to assert in tests. Size/seed flags (``--universes``/``--seed``/…)
let callers run a small, fast pipeline; they default to the canonical config.
``project``/``all`` accept ``--png OUTDIR`` to also export the projection PNG.

Run:  python -m central_finite_curve.adapters.cli all --png /tmp/cfc
"""

from __future__ import annotations

import argparse
import os
from typing import List, Optional, Sequence

from central_finite_curve.adapters import (
    animate,
    animate_3d,
    animate_panels,
    render,
    viz,
)
from central_finite_curve.core.config import DEFAULT, CurveConfig
from central_finite_curve.core.pipeline import PipelineResult, run

# Canonical artifact filenames (shared with scripts/regenerate_artifacts.sh).
_PROJECTION_PNG = "central_finite_curve_projection.png"
_WALK_GIF = "central_finite_curve_walk.gif"
_WALK_MP4 = "central_finite_curve_walk.mp4"
_PANELS_GIF = "central_finite_curve_four_panels.gif"
_PANELS_MP4 = "central_finite_curve_four_panels.mp4"
_ROTATING_GIF = "central_finite_curve_rotating_3d.gif"
_ROTATING_MP4 = "central_finite_curve_rotating_3d.mp4"


def _rule(title: str) -> List[str]:
    """A boxed section header as a list of output lines."""
    bar = "=" * 70
    return [bar, title, bar]


def _fmt(x: float) -> str:
    return f"{x:.4f}"


def config_from_args(args: argparse.Namespace) -> CurveConfig:
    """Build a :class:`CurveConfig` from optional size/seed flags (canonical default).

    Any flag left unset falls back to :data:`central_finite_curve.core.config.DEFAULT`,
    so a bare subcommand reproduces the canonical run.
    """
    return CurveConfig(
        dim=getattr(args, "dim", None) or DEFAULT.dim,
        n_universes=getattr(args, "universes", None) or DEFAULT.n_universes,
        near_manifold_fraction=(
            getattr(args, "near_fraction", None)
            if getattr(args, "near_fraction", None) is not None
            else DEFAULT.near_manifold_fraction
        ),
        eps_absolute=(
            getattr(args, "eps", None)
            if getattr(args, "eps", None) is not None
            else DEFAULT.eps_absolute
        ),
        walk_steps=(
            getattr(args, "walk_steps", None)
            if getattr(args, "walk_steps", None) is not None
            else DEFAULT.walk_steps
        ),
        seed=getattr(args, "seed", None) or DEFAULT.seed,
    )


def _header_lines(config: CurveConfig) -> List[str]:
    lines = _rule("CENTRAL FINITE CURVE ENGINE")
    lines.append(f"dimensions           : {config.dim}")
    lines.append(f"universes generated  : {config.n_universes}")
    lines.append(f"seed                 : {config.seed}")
    return lines


def _landscape_lines(result: PipelineResult) -> List[str]:
    curve = result.curve
    lines = ["-- Rickness landscape ------------------------------------------"]
    lines.append(f"max Rickness         : {_fmt(curve.max_score)}")
    lines.append(f"epsilon band width   : {_fmt(curve.epsilon)}")
    lines.append(f"band lower bound     : {_fmt(curve.band_low)}")
    return lines


def _curve_lines(result: PipelineResult) -> List[str]:
    curve = result.curve
    lines = ["-- Central Finite Curve ----------------------------------------"]
    lines.append(f"curve size (universes): {curve.size}")
    lines.append(f"fraction of multiverse: {curve.fraction * 100:.3f}%")
    if curve.members:
        best = curve.members[0]
        lines.append(
            "best universe coords : ["
            + ", ".join(_fmt(c) for c in best.coords)
            + "]"
        )
    return lines


def _walk_lines(result: PipelineResult) -> List[str]:
    walk = result.walk
    lines = ["-- Portal gun (constrained MCMC walk) --------------------------"]
    lines.append(f"walk steps           : {walk.steps}")
    lines.append(f"acceptance rate      : {walk.acceptance_rate * 100:.1f}%")
    lines.append(f"trajectory length    : {len(walk.points)} points")
    if walk.scores:
        lines.append(
            f"score range on walk  : {_fmt(min(walk.scores))} .. {_fmt(max(walk.scores))}"
        )
    return lines


def _projection_lines(result: PipelineResult) -> List[str]:
    lines = ["-- ASCII projection (top-2 principal components) ---------------"]
    lines.append(
        render.ascii_scatter(
            result.proj_curve, result.proj_walk, config=result.config
        )
    )
    return lines


def render_generate(config: CurveConfig) -> str:
    """``generate`` report: header + the Rickness landscape."""
    result = run(config, project=False)
    return "\n".join(_header_lines(config) + [""] + _landscape_lines(result))


def render_curve(config: CurveConfig) -> str:
    """``curve`` report: header + landscape + the extracted band's size/shape."""
    result = run(config, project=False)
    lines = _header_lines(config) + [""] + _landscape_lines(result)
    lines += [""] + _curve_lines(result)
    return "\n".join(lines)


def render_walk(config: CurveConfig) -> str:
    """``walk`` report: header + curve + the portal-gun acceptance ratio."""
    result = run(config, project=False)
    lines = _header_lines(config) + [""] + _curve_lines(result)
    lines += [""] + _walk_lines(result)
    return "\n".join(lines)


def render_project(config: CurveConfig) -> str:
    """``project`` report: header + curve + walk + the ASCII scatter."""
    result = run(config, project=True)
    lines = _header_lines(config) + [""] + _curve_lines(result)
    lines += [""] + _walk_lines(result)
    lines += [""] + _projection_lines(result)
    return "\n".join(lines)


def render_all(config: CurveConfig) -> str:
    """``all`` report: the whole pipeline end to end (the canonical report)."""
    result = run(config, project=True)
    lines = _header_lines(config)
    lines += [""] + _landscape_lines(result)
    lines += [""] + _curve_lines(result)
    lines += [""] + _walk_lines(result)
    lines += [""] + _projection_lines(result)
    return "\n".join(lines)


def render_animate(
    config: CurveConfig,
    outdir: str,
    *,
    mp4: bool = False,
    panels: bool = False,
    rotate: bool = False,
) -> str:
    """Write the animation(s) into ``outdir`` and return a report string.

    Always writes the walk GIF (needs matplotlib + Pillow). ``mp4`` additionally
    writes the MP4 of every animation requested (needs an ffmpeg binary on PATH).
    ``panels`` additionally writes the four-panel composite explainer (a 2x2 GIF: the
    Rickness-scored multiverse, the near-maximal band, the portal-gun walk, and the
    Rickness histogram). ``rotate`` additionally writes the rotating 3-D projection (an
    orbiting-camera GIF of the multiverse with the band highlighted and the walk
    overlaid). DEFERRED: the animation adapters raise
    :class:`~central_finite_curve.adapters.viz.OptionalDependencyError` when a required
    backend is unavailable.
    """
    os.makedirs(outdir, exist_ok=True)
    gif_path = animate.save_walk_gif(os.path.join(outdir, _WALK_GIF), config=config)
    lines = _rule("ANIMATE -- portal gun walking along the Central Finite Curve")
    lines.append("Rendered GIF (matplotlib FuncAnimation + PillowWriter):")
    lines.append(f"  {gif_path}")
    if mp4:
        mp4_path = animate.save_walk_mp4(os.path.join(outdir, _WALK_MP4), config=config)
        lines.append("")
        lines.append("Rendered MP4 (matplotlib FuncAnimation + FFMpegWriter):")
        lines.append(f"  {mp4_path}")
    if panels:
        panels_gif = animate_panels.save_cfc_four_panels_gif(
            os.path.join(outdir, _PANELS_GIF), config=config
        )
        lines.append("")
        lines.append(
            "Rendered four-panel explainer GIF (2x2: Rickness-scored multiverse, "
            "near-maximal band, portal-gun walk, Rickness histogram):"
        )
        lines.append(f"  {panels_gif}")
        if mp4:
            panels_mp4 = animate_panels.save_cfc_four_panels_mp4(
                os.path.join(outdir, _PANELS_MP4), config=config
            )
            lines.append("")
            lines.append("Rendered four-panel explainer MP4 (FFMpegWriter):")
            lines.append(f"  {panels_mp4}")
    if rotate:
        rotate_gif = animate_3d.save_cfc_rotating_gif(
            os.path.join(outdir, _ROTATING_GIF), config=config
        )
        lines.append("")
        lines.append(
            "Rendered rotating 3-D GIF (orbiting camera over the multiverse with the "
            "near-maximal band + portal-gun walk):"
        )
        lines.append(f"  {rotate_gif}")
        if mp4:
            rotate_mp4 = animate_3d.save_cfc_rotating_mp4(
                os.path.join(outdir, _ROTATING_MP4), config=config
            )
            lines.append("")
            lines.append("Rendered rotating 3-D MP4 (FFMpegWriter):")
            lines.append(f"  {rotate_mp4}")
    return "\n".join(lines)


def _write_png(config: CurveConfig, outdir: str) -> str:
    """Render the projection PNG into ``outdir`` and return a summary line block.

    DEFERRED: :func:`central_finite_curve.adapters.viz.save_projection_png` raises
    :class:`~central_finite_curve.adapters.viz.OptionalDependencyError` when
    matplotlib is unavailable.
    """
    os.makedirs(outdir, exist_ok=True)
    target = os.path.join(outdir, _PROJECTION_PNG)
    viz.save_projection_png(target, config=config)
    return "\nPNG export written (matplotlib, headless Agg backend):\n  " + target


_RENDERERS = {
    "generate": render_generate,
    "curve": render_curve,
    "walk": render_walk,
    "project": render_project,
    "all": render_all,
}

# Subcommands that expose the --png OUTDIR option.
_PNG_COMMANDS = {"project", "all"}


def _add_size_flags(parser: argparse.ArgumentParser) -> None:
    """Attach the optional size/seed flags shared by the pipeline subcommands."""
    parser.add_argument("--dim", type=int, default=None, help="multiverse dimension (>= 8)")
    parser.add_argument(
        "--universes", type=int, default=None, help="number of universes to generate"
    )
    parser.add_argument("--seed", type=int, default=None, help="master reproducibility seed")
    parser.add_argument(
        "--walk-steps", dest="walk_steps", type=int, default=None,
        help="portal-gun MCMC step count",
    )
    parser.add_argument(
        "--eps", type=float, default=None, help="absolute Rickness band half-width"
    )
    parser.add_argument(
        "--near-fraction", dest="near_fraction", type=float, default=None,
        help="fraction of universes seeded near the manifold",
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser with one subcommand per pipeline stage plus ``all``."""
    parser = argparse.ArgumentParser(
        prog="central-finite-curve",
        description="The Central Finite Curve: a near-maximal Rickness ridge and a "
        "portal-gun walk along it.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    descriptions = {
        "generate": "seed the multiverse and report the Rickness landscape",
        "curve": "extract the near-maximal band (the Central Finite Curve)",
        "walk": "fire the portal gun and report the acceptance ratio",
        "project": "project curve + walk to 2-D and print the ASCII scatter",
        "all": "run the whole pipeline end to end (canonical report)",
        "animate": "render the walk GIF/MP4 into OUTDIR (needs matplotlib + Pillow)",
    }
    for name, help_text in descriptions.items():
        p = sub.add_parser(name, help=help_text, description=help_text)
        if name == "animate":
            _add_size_flags(p)
            p.add_argument(
                "outdir",
                metavar="OUTDIR",
                help="directory to write the walk animation into (requires "
                "matplotlib + Pillow for the GIF, ffmpeg for the MP4)",
            )
            p.add_argument(
                "--mp4",
                action="store_true",
                help="also write the MP4 of every requested animation (requires an "
                "ffmpeg binary on PATH)",
            )
            p.add_argument(
                "--panels",
                action="store_true",
                help="also write the four-panel composite explainer GIF "
                "(central_finite_curve_four_panels.gif; with --mp4 also the .mp4)",
            )
            p.add_argument(
                "--rotate",
                action="store_true",
                help="also write the rotating 3-D projection GIF "
                "(central_finite_curve_rotating_3d.gif; with --mp4 also the .mp4)",
            )
            continue
        _add_size_flags(p)
        if name in _PNG_COMMANDS:
            p.add_argument(
                "--png",
                metavar="OUTDIR",
                default=None,
                help="also render the projection PNG into OUTDIR (requires the "
                "optional 'viz' extra / matplotlib)",
            )
    return parser


def run_cli(argv: Optional[Sequence[str]] = None) -> str:
    """Resolve ``argv`` to the rendered report text (no printing).

    Kept side-effect free (apart from requested file exports) so tests can assert on
    the returned string.
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    config = config_from_args(args)
    if args.command == "animate":
        return render_animate(
            config,
            args.outdir,
            mp4=bool(getattr(args, "mp4", False)),
            panels=bool(getattr(args, "panels", False)),
            rotate=bool(getattr(args, "rotate", False)),
        )
    text = _RENDERERS[args.command](config)
    png_dir = getattr(args, "png", None)
    if png_dir:
        text += _write_png(config, png_dir)
    return text


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry point: render the requested report and print it. Returns 0."""
    print(run_cli(argv))
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised via run_cli()/main()
    raise SystemExit(main())
