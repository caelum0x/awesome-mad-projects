"""Command-line front end for the compactified-latent-space TOY.

``argparse`` subcommands, each a thin wrapper over the pure
:mod:`calabi_yau_latent.core` engine (and, for ``--png``, the lazily-guarded viz
adapter):

    seam       show why the naive number line tears a seam-straddling cluster
    cluster    connected-components clustering: naive (over-segments) vs wrap-aware
    holonomy   the toy parallel-transport cartoon (ANALOGY, not real CY)
    torus      print the ASCII 2-torus of wrap-aware cluster labels
    all        run the whole narrated demo end to end (canonical report)

Each subcommand prints a stable, greppable headline plus numeric evidence, so the
output is easy to assert in tests. ``torus`` / ``all`` accept ``--png OUTDIR`` to
also export the compact-torus PNG.

Run:  python -m calabi_yau_latent.adapters.cli all --png /tmp/cy
"""

from __future__ import annotations

import argparse
import os
from typing import List, Optional, Sequence

from calabi_yau_latent.adapters import ascii_viz, viz
from calabi_yau_latent.core.clustering import (
    cluster,
    nearest_neighbor,
    num_clusters,
    purity,
)
from calabi_yau_latent.core.config import DEFAULT, CYConfig
from calabi_yau_latent.core.data import generate, make_space
from calabi_yau_latent.core.distance import (
    naive_angular_distance,
    toroidal_angular_distance,
)
from calabi_yau_latent.core.holonomy import (
    holonomy_angle,
    loop_trace,
    transport_around_loop,
)

# Canonical artifact filename (shared with the repo-level artifacts dir).
_TORUS_PNG = "calabi_yau_latent_torus.png"

_CAVEAT = (
    "TOY analogy only: a flat R^k x T^m product space, NOT a Ricci-flat "
    "Calabi-Yau manifold. See README.md."
)


def _rule(title: str) -> List[str]:
    bar = "=" * 68
    return [bar, title, bar]


def config_from_args(args: argparse.Namespace) -> CYConfig:
    """Build a :class:`CYConfig` from optional size/seed flags (canonical default).

    Any flag left unset falls back to
    :data:`calabi_yau_latent.core.config.DEFAULT`, so a bare subcommand reproduces
    the canonical run.
    """
    per_cluster = getattr(args, "per_cluster", None)
    seed = getattr(args, "seed", None)
    threshold = getattr(args, "threshold", None)
    return CYConfig(
        per_cluster=per_cluster if per_cluster is not None else DEFAULT.per_cluster,
        seed=seed if seed is not None else DEFAULT.seed,
        cluster_threshold=(
            threshold if threshold is not None else DEFAULT.cluster_threshold
        ),
    )


def _nn_accuracy(points, truth, dist) -> float:
    """Fraction of points whose nearest neighbour shares the true cluster."""
    correct = 0
    for i, p in enumerate(points):
        j = nearest_neighbor(p, points, dist)
        if j >= 0 and truth[j] == truth[i]:
            correct += 1
    return correct / len(points) if points else 0.0


def _header_lines(config: CYConfig, n: int, n_truth: int) -> List[str]:
    lines = _rule("COMPACTIFIED LATENT SPACE (TOY CY-style compactification)")
    lines.append(f"extended dims k      : {config.k}")
    lines.append(f"compact circles m    : {config.m}   radii = {config.radii}")
    lines.append(f"points               : {n}")
    lines.append(f"ground-truth clusters: {n_truth}")
    lines.append(f"seed                 : {config.seed}")
    return lines


def render_seam(config: CYConfig) -> str:
    """The seam problem: a cluster straddling ``theta1 = 0 / 2*pi``."""
    space = make_space(config)
    points, truth, _ = generate(space, config)
    lines = _header_lines(config, len(points), num_clusters(truth))
    lines += _rule("1) The seam problem: cluster 0 straddles theta1 = 0 / 2*pi")
    seam_angles = [p.angles[0] for p, t in zip(points, truth) if t == 0]
    lines.append(ascii_viz.wrap_number_line(seam_angles, width=config.grid_w))

    idxs = [i for i, t in enumerate(truth) if t == 0]
    lo = min(idxs, key=lambda i: points[i].angles[0])
    hi = max(idxs, key=lambda i: points[i].angles[0])
    p_lo, p_hi = points[lo], points[hi]
    d_naive = naive_angular_distance(p_lo, p_hi)
    d_wrap = toroidal_angular_distance(p_lo, p_hi)
    ratio = d_naive / d_wrap if d_wrap > 0 else float("inf")
    lines.append(f"naive angular distance     : {d_naive:6.3f}  (looks FAR)")
    lines.append(f"wrap-aware angular distance: {d_wrap:6.3f}  (correctly CLOSE)")
    lines.append(f"naive / wrap ratio         : {ratio:6.1f}x overestimate")
    return "\n".join(lines)


def render_cluster(config: CYConfig) -> str:
    """Connected-components clustering: naive over-segments vs wrap-aware recovers."""
    space = make_space(config)
    points, truth, _ = generate(space, config)
    lines = _rule("2) Connected-components clustering (target = 3 clusters)")
    thr = config.cluster_threshold
    lab_naive = cluster(points, naive_angular_distance, thr)
    lab_wrap = cluster(points, toroidal_angular_distance, thr)
    acc_naive = _nn_accuracy(points, truth, naive_angular_distance)
    acc_wrap = _nn_accuracy(points, truth, toroidal_angular_distance)
    lines.append(f"threshold            : {thr}")
    lines.append(
        f"naive      : #clusters = {num_clusters(lab_naive):2d}   "
        f"purity = {purity(lab_naive, truth):.2f}   NN-acc = {acc_naive:.0%}"
    )
    lines.append(
        f"wrap-aware : #clusters = {num_clusters(lab_wrap):2d}   "
        f"purity = {purity(lab_wrap, truth):.2f}   NN-acc = {acc_wrap:.0%}"
    )
    lines.append(
        "(Naive over-segments seam-straddling clusters; wrap-aware recovers "
        "the true count.)"
    )
    return "\n".join(lines)


def render_holonomy(config: CYConfig) -> str:
    """The holonomy-flavoured parallel-transport cartoon (ANALOGY, not real CY)."""
    lines = _rule("4) Holonomy-flavoured parallel transport (ANALOGY, not real CY)")
    curvature = config.curvature
    final_v, holo = transport_around_loop((1.0, 0.0), curvature=curvature)
    lines.append(
        f"transport (1,0) once around a compact loop, curvature = {curvature}"
    )
    lines.append(f"net holonomy angle (measured)    : {holo:.4f} rad")
    lines.append(
        f"net holonomy angle (closed form) : {holonomy_angle(curvature):.4f} rad"
    )
    lines.append(f"final vector = ({final_v[0]:+.4f}, {final_v[1]:+.4f})")
    lines.append(
        "Real Calabi-Yau spaces are prized for SPECIAL (SU(n)) holonomy -- deep "
        "geometry we do NOT reproduce here."
    )
    lines.append(
        ascii_viz.render_holonomy(
            loop_trace((1.0, 0.0), curvature=curvature, samples=8)
        )
    )
    return "\n".join(lines)


def render_torus(config: CYConfig) -> str:
    """The ASCII compact 2-torus coloured by wrap-aware cluster labels."""
    space = make_space(config)
    points, _truth, torus_xy = generate(space, config)
    lab_wrap = cluster(points, toroidal_angular_distance, config.cluster_threshold)
    lines = _rule("3) The compact 2-torus (wrap-aware cluster labels)")
    lines.append(
        ascii_viz.torus_grid(
            torus_xy, lab_wrap, width=config.grid_w, height=config.grid_h
        )
    )
    return "\n".join(lines)


def render_all(config: CYConfig) -> str:
    """The full narrated report: every section + the honest caveat.

    ``render_seam`` already emits the run header, so it leads the report.
    """
    blocks = [
        render_seam(config),
        render_cluster(config),
        render_torus(config),
        render_holonomy(config),
        "\n".join(_rule("Summary") + [_CAVEAT]),
    ]
    return "\n\n".join(blocks)


_RENDERERS = {
    "seam": render_seam,
    "cluster": render_cluster,
    "holonomy": render_holonomy,
    "torus": render_torus,
    "all": render_all,
}

# Subcommands that expose the --png OUTDIR option.
_PNG_COMMANDS = {"torus", "all"}


def _write_png(config: CYConfig, outdir: str) -> str:
    """Export the compact-torus PNG into ``outdir`` (creates it if missing)."""
    os.makedirs(outdir, exist_ok=True)
    target = os.path.join(outdir, _TORUS_PNG)
    viz.save_torus_png(target, config=config)
    return "\nPNG export written (matplotlib, headless Agg backend):\n  " + target


def _add_size_flags(parser: argparse.ArgumentParser) -> None:
    """Attach the optional size/seed flags shared by every subcommand."""
    parser.add_argument(
        "--per-cluster", dest="per_cluster", type=int, default=None,
        help="points generated per ground-truth cluster",
    )
    parser.add_argument(
        "--seed", type=int, default=None, help="reproducibility seed"
    )
    parser.add_argument(
        "--threshold", type=float, default=None,
        help="connected-components distance threshold",
    )


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser: one subcommand per section plus ``all``."""
    parser = argparse.ArgumentParser(
        prog="calabi-yau-latent",
        description="A compactified latent space over R^k x T^m: why periodic, "
        "compact latent dimensions hide structure from a naive Euclidean view. "
        "TOY analogy, not a real Calabi-Yau manifold.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    descriptions = {
        "seam": "show why the naive number line tears a seam-straddling cluster",
        "cluster": "connected-components clustering: naive vs wrap-aware",
        "holonomy": "toy parallel-transport cartoon (ANALOGY, not real CY)",
        "torus": "print the ASCII 2-torus of wrap-aware cluster labels",
        "all": "run the whole narrated demo end to end (canonical report)",
    }
    for name, help_text in descriptions.items():
        p = sub.add_parser(name, help=help_text, description=help_text)
        _add_size_flags(p)
        if name in _PNG_COMMANDS:
            p.add_argument(
                "--png", metavar="OUTDIR", default=None,
                help="also render the compact-torus PNG into OUTDIR (requires the "
                "optional 'viz' extra / matplotlib)",
            )
    return parser


def run_cli(argv: Optional[Sequence[str]] = None) -> str:
    """Resolve ``argv`` to the rendered report text (no printing).

    Kept side-effect free apart from requested file exports, so tests can assert
    on the returned string.
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    config = config_from_args(args)
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
