"""Command-line front end for the four Infinity lenses.

``argparse`` subcommands, each a thin wrapper over :mod:`gojo_infinity.core`
(and, for the ``--ascii`` option, :mod:`gojo_infinity.adapters.viz`):

    zeno        Lens 1  Geometric series / Zeno      -> FRAGILE
    measure     Lens 2  Lebesgue measure             -> FRAGILE
    riemannian  Lens 3  Riemannian conformal metric  -> FORMIDABLE
    topology    Lens 4  World-Cutting Slash          -> FALLS
    all         run all four and print the conclusion table

Each subcommand prints a stable, greppable headline line
``LENS k -- ... verdict: <VERDICT>`` followed by the essay's numeric evidence,
so the output is easy to assert in tests. Pass ``--ascii`` to append the
deterministic ASCII chart for that lens, or ``--png OUTDIR`` to additionally
render the matplotlib PNG chart(s) into ``OUTDIR`` (optional 'viz' extra).

Run:  python -m gojo_infinity.adapters.cli all --png /tmp/gojo
"""

from __future__ import annotations

import argparse
import os
from fractions import Fraction
from typing import Dict, List, Optional, Sequence, Tuple

from gojo_infinity.core import (
    ConformalMetric,
    calibrate,
    component_count,
    conclusion_table,
    conformal_factor,
    connected_components,
    continuity_at,
    format_table,
    geodesic_length,
    geodesic_to_barrier,
    lebesgue_measure_of_Z,
    make_severed_factor,
    max_christoffel_difference,
    partial_sum,
    per_decade_increment,
    residual,
    severed_geodesic_length,
    subdivision_set,
    total_arrival_time,
    total_cover_length,
    zeno_series_sum,
)
from gojo_infinity.adapters import animate, animate_3d, animate_lenses, viz

_ZENO_MAX_N = 8


def _rule(title: str) -> List[str]:
    """A boxed section header as a list of output lines."""
    bar = "=" * 70
    return [bar, title, bar]


# ---------------------------------------------------------------------------
# Lens 1 -- Zeno
# ---------------------------------------------------------------------------

def render_zeno(*, ascii_art: bool = False) -> str:
    """Return the Lens 1 report text (geometric series / Zeno)."""
    lines = _rule("LENS 1 -- GEOMETRIC SERIES (Zeno)   verdict: FRAGILE")
    lines.append("Partial sums S_n = 1/2 + 1/4 + ... + 1/2^n = 1 - (1/2)^n:")
    lines.append(f"{'n':>3} | {'S_n (exact)':>14} | {'S_n (decimal)':>14} | {'residual':>14}")
    lines.append("-" * 56)
    for n in range(1, _ZENO_MAX_N + 1):
        s = partial_sum(n)
        r = residual(n)
        lines.append(f"{n:>3} | {str(s):>14} | {float(s):>14.8f} | {str(r):>14}")
    total = zeno_series_sum()
    arrival = total_arrival_time(speed=Fraction(1, 2))
    lines.append("")
    lines.append(f"Geometric sum a/(1-r) with a=1/2, r=1/2 = {total}  (exactly 1).")
    lines.append(f"Total arrival time at speed 1/2 = {arrival}  ->  FINITE.")
    lines.append("Residual (1/2)^n > 0 for every finite n, yet the series -> 1:")
    lines.append("the attacker ARRIVES. Infinity is FRAGILE.")
    if ascii_art:
        lines.append("")
        lines.append(viz.render_zeno_convergence(12))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Lens 2 -- Lebesgue measure
# ---------------------------------------------------------------------------

def render_measure(*, ascii_art: bool = False) -> str:
    """Return the Lens 2 report text (Lebesgue measure of the barrier Z)."""
    lines = _rule("LENS 2 -- LEBESGUE MEASURE   verdict: FRAGILE")
    zset = subdivision_set(4)
    lines.append(
        "Subdivision set Z = { z_n = 1 - 1/2^n } = {"
        + ", ".join(str(z) for z in zset)
        + ", ...}  (countably infinite)"
    )
    eps = Fraction(1, 10)
    lines.append(f"Cover z_n by I_n of length eps/2^n (here eps = {eps}):")
    lines.append(f"{'terms':>5} | {'total cover length (exact)':>26} | {'decimal':>10}")
    lines.append("-" * 50)
    for terms in (1, 2, 4, 8, 16):
        tot = total_cover_length(eps, terms)
        lines.append(f"{terms:>5} | {str(tot):>26} | {float(tot):>10.6f}")
    lines.append("")
    lines.append(f"As terms -> infinity the total -> eps = {eps} = {float(eps)}.")
    lines.append(f"As eps -> 0 the infimum -> 0, so  m(Z) = {lebesgue_measure_of_Z()}.")
    lines.append("The barrier is countably many points of TOTAL LENGTH ZERO: FRAGILE.")
    if ascii_art:
        lines.append("")
        lines.append(viz.render_cover_convergence(eps, 12))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Lens 3 -- Riemannian geometry
# ---------------------------------------------------------------------------

def render_riemannian(*, ascii_art: bool = False) -> str:
    """Return the Lens 3 report text (conformal metric blow-up / geodesic)."""
    lines = _rule("LENS 3 -- RIEMANNIAN GEOMETRY   verdict: FORMIDABLE")
    cal = calibrate()
    lines.append("Conformal metric ds = Omega(x) dx, g = Omega(x)^2, Gojo at x = 1.0")
    lines.append(
        f"Calibrated: sigma = {cal.sigma:.4f}, lambda = {cal.lam:.6f} "
        "(lambda DERIVED by bisection on g(0.8) = 4.1)"
    )
    lines.append(f"{'label':>7} | {'x':>4} | {'g = Omega^2':>12} | {'felt ds':>9}")
    lines.append("-" * 42)
    lines.append(f"{'A far':>7} | {0.1:>4.1f} | {cal.g_far:>12.4f} | {cal.ds_far:>9.4f}")
    lines.append(f"{'B near':>7} | {0.8:>4.1f} | {cal.g_near:>12.4f} | {cal.ds_near:>9.4f}")
    lines.append("")
    barrier = geodesic_to_barrier(0.5)
    lines.append(
        f"Felt geodesic length from x0 = 0.5 to the barrier = {barrier}  "
        "(math.inf: an IMPROPER integral that DIVERGES)."
    )
    lines.append(
        f"Each decade of approach adds ~ lambda*ln(10) = {per_decade_increment(cal.lam):.4f}: "
        "L is unbounded."
    )
    lines.append("Every attack must cross infinite felt distance. Infinity is FORMIDABLE.")
    if ascii_art:
        lines.append("")
        lines.append(viz.render_omega_blowup())
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Lens 3 (2-D) -- Riemannian manifold geodesics (enhancement)
# ---------------------------------------------------------------------------

def render_manifold(*, ascii_art: bool = False) -> str:
    """Return the Lens 3 (2-D) report: a real manifold geodesic solver.

    Prints the Christoffel cross-check, the conserved affine invariant, the
    radial parity with the 1-D lens, the felt-length divergence table, and a
    grazing-geodesic deflection angle. ``ascii_art`` is accepted for CLI
    uniformity but this lens has no ASCII chart.
    """
    del ascii_art  # no ASCII chart for the 2-D manifold; kept for CLI symmetry
    metric = ConformalMetric()
    lines = _rule("LENS 3 (2-D) -- RIEMANNIAN MANIFOLD GEODESICS   verdict: FORMIDABLE")
    lines.append("Metric g_ij = Omega(x)^2 delta_ij on R^2, Gojo at the origin (0, 0).")
    lines.append("Conformal geodesic: x'' = |x'|^2 grad(phi) - 2 (grad(phi).x') x', phi=ln Omega.")

    pts = [(0.5, 0.3), (1.0, -0.4), (2.0, 0.1), (-0.7, 0.9)]
    worst = max_christoffel_difference(metric, pts)
    lines.append("")
    lines.append(
        f"(1) Christoffel cross-check: max |closed-form - general| = {worst:.2e} "
        "(the conformal formula is correct)."
    )

    graze = metric.integrate_geodesic((-3.0, 0.5), (1.0, 0.0), dtau=1e-3, max_steps=6000)
    lines.append(
        f"(2) Affine invariant Omega^2|v|^2 conserved: relative drift = "
        f"{graze.energy_drift:.2e} over {graze.steps} RK4 steps."
    )

    d0 = 0.5
    radial = metric.integrate_geodesic(
        (d0, 0.0), (-1.0, 0.0), dtau=1e-3, target_radius=0.05, max_steps=500_000
    )
    ref = geodesic_length(1.0 - d0, 1.0 - radial.final_radius)
    lines.append(
        f"(3) Radial parity with the 1-D lens: felt length = {radial.arc_length:.6f} "
        f"vs 1-D integral = {ref:.6f} (|diff| = {abs(radial.arc_length - ref):.2e}); "
        f"tangential drift = {max(abs(p[1]) for p in radial.points):.1e}."
    )

    lines.append("(4) Felt length to reach within delta of Gojo (start radius 0.9):")
    lines.append(f"{'delta':>10} | {'felt length':>12}")
    lines.append("-" * 26)
    for delta, length in metric.felt_length_divergence(
        [1e-1, 1e-2, 1e-3, 1e-4, 1e-6], start_radius=0.9
    ):
        lines.append(f"{delta:>10.0e} | {length:>12.6f}")
    lines.append(
        f"    -> unbounded as delta -> 0 (per decade ~ lam*ln 10 = "
        f"{per_decade_increment():.4f}). FORMIDABLE."
    )

    lines.append(
        f"(5) Deflection: a grazing ray (impact 0.5) bends toward Gojo by "
        f"{graze.deflection_angle:.4f} rad (final v_y = {graze.final_velocity[1]:.4f} < 0)."
    )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Lens 4 -- Topology
# ---------------------------------------------------------------------------

def render_topology(*, ascii_art: bool = False) -> str:
    """Return the Lens 4 report text (World-Cutting Slash / disconnection)."""
    lines = _rule("LENS 4 -- TOPOLOGY   verdict: FALLS")
    x0, x1, cut = 0.1, 0.9, 0.5
    intact_report = continuity_at(conformal_factor, cut)
    severed = make_severed_factor(cut, jump=1.0)
    severed_report = continuity_at(severed, cut)
    lines.append(
        f"Attacker at x0 = {x0}, Gojo beyond x1 = {x1}. World-Cutting Slash at c = {cut}."
    )
    lines.append("(a) Continuity of Omega across the domain:")
    lines.append(
        f"    intact  metric @ c={cut}: continuous = {intact_report.continuous} "
        f"({intact_report.detail})"
    )
    lines.append(
        f"    severed metric @ c={cut}: continuous = {severed_report.continuous} "
        f"({severed_report.detail})"
    )
    length = severed_geodesic_length(x0, x1, cut)
    lines.append("(b) Geodesic integral across the cut:")
    lines.append(f"    felt length = {length}  (None: UNDEFINED, not inf, not finite)")
    comps = connected_components(x0, x1, cut)
    lines.append("(c) Connectivity of the domain [x0, x1] \\ {c}:")
    lines.append(
        f"    components = {comps}  ->  count = {component_count(x0, x1, cut)} "
        "(DISCONNECTED into 2 pieces)"
    )
    lines.append("")
    lines.append("The cut crosses NO distance; it tears continuity. Infinity FALLS.")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# All lenses + conclusion table
# ---------------------------------------------------------------------------

def render_conclusion() -> str:
    """Return the four-verdict conclusion table plus the honest cursed-energy caveat."""
    lines = _rule("CONCLUSION -- four lenses, four verdicts")
    lines.append(format_table())
    lines.append("")
    lines.append("Honest caveat: applying real analysis to a fictional universe has")
    lines.append("limits. 'Cursed energy' and authorial intent do not obey the axioms")
    lines.append("of real analysis; these four models illuminate the idea of Infinity,")
    lines.append("they do not govern it.")
    return "\n".join(lines)


def render_all(*, ascii_art: bool = False) -> str:
    """Return every lens report followed by the conclusion table."""
    blocks = [
        render_zeno(ascii_art=ascii_art),
        render_measure(ascii_art=ascii_art),
        render_riemannian(ascii_art=ascii_art),
        render_manifold(),
        render_topology(ascii_art=ascii_art),
        render_conclusion(),
    ]
    return "\n\n".join(blocks)


# ---------------------------------------------------------------------------
# argparse wiring
# ---------------------------------------------------------------------------

_RENDERERS = {
    "zeno": render_zeno,
    "measure": render_measure,
    "riemannian": render_riemannian,
    "manifold": render_manifold,
    "topology": render_topology,
}

# Each lens with a chart maps to (png-writer, output filename). matplotlib is
# reached lazily inside these writers, so importing this module stays dependency
# free; requesting --png without matplotlib raises viz.OptionalDependencyError.
_PNG_EXPORTERS: Dict[str, Tuple] = {
    "zeno": (viz.save_series_convergence_png, "lens1_zeno_convergence.png"),
    "measure": (viz.save_covering_png, "lens2_cover_convergence.png"),
    "riemannian": (viz.save_metric_blowup_png, "lens3_metric_blowup.png"),
}

# The 2-D manifold lens has TWO charts of its own (kept out of ``all`` so the
# ``all`` export stays exactly the three essay lens charts).
_MANIFOLD_PNG_EXPORTERS: List[Tuple] = [
    (viz.save_geodesic_bundle_png, "lens3_geodesic_bundle.png"),
    (viz.save_length_divergence_png, "lens3_length_divergence.png"),
]

# The animated GIFs (geodesic approach + Zeno never-arrives). matplotlib AND
# Pillow are reached lazily inside these writers; requesting ``animate`` without
# them raises viz.OptionalDependencyError (deferred).
_GIF_EXPORTERS: List[Tuple] = [
    (animate.save_geodesic_approach_gif, "gojo_geodesic_approach.gif"),
    (animate.save_never_arrives_gif, "gojo_never_arrives.gif"),
]


def export_gifs(outdir: str) -> List[str]:
    """Render the two animated GIFs into ``outdir``; return the written paths.

    The directory is created if missing. Raises
    :class:`viz.OptionalDependencyError` (deferred) when matplotlib or Pillow is
    unavailable.
    """
    os.makedirs(outdir, exist_ok=True)
    written: List[str] = []
    for writer, filename in _GIF_EXPORTERS:
        written.append(writer(os.path.join(outdir, filename)))
    return written


def export_rotating_gif(outdir: str) -> str:
    """Render the rotating 3-D geodesic GIF into ``outdir``; return its path.

    Needs matplotlib AND Pillow (reached lazily); raises
    :class:`viz.OptionalDependencyError` (deferred) when either is absent.
    """
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "gojo_geodesic_3d_rotating.gif")
    return animate_3d.save_geodesic_3d_rotating_gif(path)


def export_four_lenses_gif(outdir: str) -> str:
    """Render the four-lens composite explainer GIF into ``outdir``; return its path.

    Needs matplotlib AND Pillow (reached lazily); raises
    :class:`viz.OptionalDependencyError` (deferred) when either is absent.
    """
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "gojo_four_lenses.gif")
    return animate_lenses.save_four_lenses_gif(path)


def export_four_lenses_mp4(outdir: str) -> str:
    """Render the four-lens composite explainer MP4 into ``outdir``; return its path.

    Needs matplotlib AND an ffmpeg binary on PATH (reached lazily); raises
    :class:`viz.OptionalDependencyError` (deferred) when either is absent.
    """
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "gojo_four_lenses.mp4")
    return animate_lenses.save_four_lenses_mp4(path)


def export_mp4s(outdir: str) -> List[str]:
    """Render the approach + rotating-3-D MP4s into ``outdir``; return the paths.

    Needs matplotlib AND an ffmpeg binary on PATH (reached lazily); raises
    :class:`viz.OptionalDependencyError` (deferred) when either is absent.
    """
    os.makedirs(outdir, exist_ok=True)
    return [
        animate.save_geodesic_approach_mp4(
            os.path.join(outdir, "gojo_geodesic_approach.mp4")
        ),
        animate_3d.save_geodesic_3d_rotating_mp4(
            os.path.join(outdir, "gojo_geodesic_3d_rotating.mp4")
        ),
    ]


def render_animate(outdir: str, *, rotate: bool = False, mp4: bool = False,
                   lenses: bool = False) -> str:
    """Write the animations into ``outdir`` and return a short report string.

    Always writes the two baseline GIFs (geodesic approach + Zeno never-arrives).
    ``rotate`` additionally writes the rotating 3-D GIF; ``lenses`` additionally
    writes the four-lens composite explainer GIF; ``mp4`` additionally writes the
    approach, rotating-3-D and (if ``lenses``) four-lens MP4s (needs ffmpeg).
    Deferred: raises :class:`viz.OptionalDependencyError` when a required backend
    is absent.
    """
    written = export_gifs(outdir)
    if rotate:
        written.append(export_rotating_gif(outdir))
    if lenses:
        written.append(export_four_lenses_gif(outdir))
    lines = _rule("ANIMATIONS -- geodesic approach + Zeno never-arrives (FORMIDABLE)")
    lines.append("Rendered GIFs (matplotlib FuncAnimation + PillowWriter):")
    for path in written:
        lines.append(f"  {path}")
    if mp4:
        mp4s = export_mp4s(outdir)
        if lenses:
            mp4s.append(export_four_lenses_mp4(outdir))
        lines.append("")
        lines.append("Rendered MP4s (matplotlib FuncAnimation + FFMpegWriter):")
        for path in mp4s:
            lines.append(f"  {path}")
    lines.append("")
    lines.append("All show the attacker asymptotically approaching Gojo but never")
    lines.append("arriving: the felt (Riemannian) length climbs without bound.")
    return "\n".join(lines)


def export_pngs(command: str, outdir: str) -> List[str]:
    """Render the PNG(s) for ``command`` into ``outdir``; return written paths.

    ``all`` writes every essay lens chart; a single lens writes just its own
    (``manifold`` writes its two 2-D charts). The directory is created if
    missing. Raises :class:`viz.OptionalDependencyError` (deferred) when
    matplotlib is unavailable.
    """
    os.makedirs(outdir, exist_ok=True)
    written: List[str] = []
    if command == "manifold":
        for writer, filename in _MANIFOLD_PNG_EXPORTERS:
            written.append(writer(os.path.join(outdir, filename)))
        return written
    names = list(_PNG_EXPORTERS) if command == "all" else [command]
    for name in names:
        writer, filename = _PNG_EXPORTERS[name]
        written.append(writer(os.path.join(outdir, filename)))
    return written


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser with one subcommand per lens plus ``all``."""
    parser = argparse.ArgumentParser(
        prog="gojo-infinity",
        description="Gojo Satoru's 'Infinity' through four mathematical lenses.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    descriptions = {
        "zeno": "Lens 1: geometric series / Zeno (FRAGILE)",
        "measure": "Lens 2: Lebesgue measure (FRAGILE)",
        "riemannian": "Lens 3: Riemannian conformal metric (FORMIDABLE)",
        "manifold": "Lens 3 (2-D): Riemannian manifold geodesics (FORMIDABLE)",
        "topology": "Lens 4: World-Cutting Slash (FALLS)",
        "all": "run all four lenses and print the conclusion table",
        "animate": "render the approach GIFs (needs matplotlib + Pillow)",
    }
    # topology/animate have no ASCII chart; manifold has PNGs but no ASCII chart;
    # animate takes an OUTDIR positional instead of --ascii/--png.
    _no_ascii = {"topology", "manifold", "animate"}
    _no_png = {"topology", "animate"}
    for name, help_text in descriptions.items():
        p = sub.add_parser(name, help=help_text, description=help_text)
        if name == "animate":
            p.add_argument(
                "outdir",
                metavar="OUTDIR",
                help="directory to write the animated GIFs into "
                "(requires the optional 'viz' extra / matplotlib + Pillow)",
            )
            p.add_argument(
                "--rotate",
                action="store_true",
                help="also write the rotating 3-D geodesic GIF "
                "(gojo_geodesic_3d_rotating.gif)",
            )
            p.add_argument(
                "--lenses",
                action="store_true",
                help="also write the four-lens composite explainer GIF "
                "(gojo_four_lenses.gif); with --mp4 also its MP4",
            )
            p.add_argument(
                "--mp4",
                action="store_true",
                help="also write MP4s of the approach and rotating-3-D scenes "
                "(requires an ffmpeg binary on PATH)",
            )
            continue
        if name not in _no_ascii:
            p.add_argument(
                "--ascii",
                action="store_true",
                help="append the deterministic ASCII chart for this lens",
            )
        if name not in _no_png:
            p.add_argument(
                "--png",
                metavar="OUTDIR",
                default=None,
                help="also render the matplotlib PNG chart(s) into OUTDIR "
                "(requires the optional 'viz' extra / matplotlib)",
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
            rotate=bool(getattr(args, "rotate", False)),
            mp4=bool(getattr(args, "mp4", False)),
            lenses=bool(getattr(args, "lenses", False)),
        )
    ascii_art = bool(getattr(args, "ascii", False))
    if args.command == "all":
        text = render_all(ascii_art=ascii_art)
    else:
        text = _RENDERERS[args.command](ascii_art=ascii_art)
    png_dir = getattr(args, "png", None)
    if png_dir:
        written = export_pngs(args.command, png_dir)
        text += "\n\nPNG export -> " + ", ".join(written)
    return text


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry point: render the requested report and print it. Returns 0."""
    print(run(argv))
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised via run()/main()
    raise SystemExit(main())
