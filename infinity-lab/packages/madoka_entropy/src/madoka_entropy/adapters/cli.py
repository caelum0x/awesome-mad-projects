"""Command-line front end for the Madoka entropy simulation.

``argparse`` with ``--seed`` / ``--steps`` flags, a thin wrapper over the pure
:mod:`madoka_entropy.core` simulation (and, for ``--png``, the lazily-guarded
viz adapter). The report prints:

    * a per-run summary of the karmic parameters,
    * an ASCII chart of GLOBAL entropy rising over time with witch marks,
    * an ASCII chart of TOTAL entropy (must be monotone non-decreasing),
    * the incubator energy harvest,
    * a verification of the second-law invariant (``dS_total >= 0`` per step).

``run_cli`` returns the rendered report string (side-effect free apart from the
optional PNG export) so tests can assert on it directly.

Run:  python -m madoka_entropy.adapters.cli --seed 42 --steps 120
"""

from __future__ import annotations

import argparse
import os
from typing import List, Optional, Sequence, Tuple

from madoka_entropy.adapters import plot, viz
from madoka_entropy.core.config import DEFAULT, SimConfig
from madoka_entropy.core.simulation import SimResult, StepRecord, run_simulation

_RULE = "=" * 68
_THIN = "-" * 68

_ENTROPY_PNG = "madoka_entropy_entropy.png"


def config_from_args(args: argparse.Namespace) -> SimConfig:
    """Build a :class:`SimConfig` from ``--seed`` / ``--steps`` (canonical default)."""
    seed = getattr(args, "seed", None)
    steps = getattr(args, "steps", None)
    return SimConfig(
        seed=DEFAULT.seed if seed is None else seed,
        steps=DEFAULT.steps if steps is None else steps,
    )


def _witch_events(records: Sequence[StepRecord]) -> List[Tuple[int, str]]:
    """Return ``(step, name)`` tuples for every witch transformation."""
    events: List[Tuple[int, str]] = []
    for rec in records:
        for name in rec.witches_this_step:
            events.append((rec.step, name))
    return events


def _header_lines(cfg: SimConfig) -> List[str]:
    return [
        _RULE,
        " MADOKA MAGICA  --  Entropy & Karmic Calculus",
        _RULE,
        f" seed={cfg.seed}  steps={cfg.steps}  girls={', '.join(cfg.girl_names)}",
        (
            f" karmic_multiplier={cfg.karmic_multiplier}  "
            f"(each wish: -x local, +{cfg.karmic_multiplier}x global => net >0)"
        ),
        (
            f" witch_threshold(purity)={cfg.witch_threshold}  "
            f"decay_per_order={cfg.decay_per_order}"
        ),
    ]


def _witch_lines(records: Sequence[StepRecord]) -> List[str]:
    events = _witch_events(records)
    lines = [_THIN]
    if events:
        lines.append(f" WITCH TRANSFORMATIONS ({len(events)}):")
        for step, name in events:
            lines.append(f"   step {step:>4}:  {name} -> witch (entropy singularity)")
    else:
        lines.append(" No witch transformations this run.")
    return lines


def _accounting_lines(records: Sequence[StepRecord]) -> List[str]:
    final = records[-1]
    return [
        _THIN,
        " FINAL ACCOUNTING",
        f"   global_entropy    : {final.global_entropy:12.3f}",
        f"   local_entropy     : {final.local_entropy:12.3f}",
        f"   TOTAL entropy     : {final.total_entropy:12.3f}",
        f"   incubator harvest : {final.harvested_energy:12.3f}  (negentropy)",
    ]


def _invariant_lines(result: SimResult) -> List[str]:
    records = result.records
    violations = [r for r in records if not r.invariant_ok]
    lines = [
        _RULE,
        " SECOND-LAW INVARIANT CHECK   (dS_total >= 0 every step)",
        _RULE,
        f"   steps checked        : {len(records)}",
        f"   min per-step dS_total: {result.min_d_total:+.6f}",
        f"   violations           : {len(violations)}",
    ]
    if result.invariant_holds:
        lines.append("   RESULT: PASS -- total entropy never decreased. 2nd law holds.")
    else:
        lines.append("   RESULT: FAIL -- invariant violated (see steps below):")
        for r in violations[:10]:
            lines.append(f"     step {r.step}: dS_total={r.d_total:+.6f}")
    lines.append(_RULE)
    return lines


def render_report(cfg: SimConfig = DEFAULT) -> str:
    """Return the full text report for a run described by ``cfg``."""
    result = run_simulation(cfg)
    records = result.records

    lines = _header_lines(cfg)
    lines.append("")
    if records:
        lines.append(plot.global_entropy_chart(records))
        lines.append("")
        lines.append(plot.total_entropy_chart(records))
        lines.append("")
        lines += _witch_lines(records)
        lines.append("")
        lines += _accounting_lines(records)
        lines.append("")
    else:
        lines.append(" (no steps requested)")
        lines.append("")
    lines += _invariant_lines(result)
    return "\n".join(lines)


def _write_png(cfg: SimConfig, outdir: str) -> str:
    """Render the entropy PNG into ``outdir`` and return a summary block.

    DEFERRED: :func:`madoka_entropy.adapters.viz.save_entropy_png` raises
    :class:`~madoka_entropy.adapters.viz.OptionalDependencyError` when
    matplotlib is unavailable.
    """
    os.makedirs(outdir, exist_ok=True)
    target = os.path.join(outdir, _ENTROPY_PNG)
    viz.save_entropy_png(target, config=cfg)
    return "\nPNG export written (matplotlib, headless Agg backend):\n  " + target


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser (``--seed`` / ``--steps`` / ``--png``)."""
    parser = argparse.ArgumentParser(
        prog="madoka-entropy",
        description=(
            "Madoka Magica entropy & karmic calculus: a seeded closed-system "
            "simulation whose total entropy is non-decreasing every step."
        ),
    )
    parser.add_argument(
        "--seed", type=int, default=None, help="RNG seed (reproducible)"
    )
    parser.add_argument(
        "--steps", type=int, default=None, help="number of simulation steps"
    )
    parser.add_argument(
        "--png",
        metavar="OUTDIR",
        default=None,
        help=(
            "also render the entropy PNG into OUTDIR (requires the optional "
            "'viz' extra / matplotlib)"
        ),
    )
    return parser


def run_cli(argv: Optional[Sequence[str]] = None) -> str:
    """Resolve ``argv`` to the rendered report text (no printing)."""
    parser = build_parser()
    args = parser.parse_args(argv)
    cfg = config_from_args(args)
    text = render_report(cfg)
    png_dir = getattr(args, "png", None)
    if png_dir:
        text += _write_png(cfg, png_dir)
    return text


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry point: render the requested report and print it. Returns 0."""
    print(run_cli(argv))
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised via run_cli()/main()
    raise SystemExit(main())
