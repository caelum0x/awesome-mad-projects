"""Command-line front end for the Domain Expansion constraint solver.

``argparse`` subcommands, each a thin wrapper over the pure
:mod:`domain_expansion.core` engine (and, for ``--png``, the lazily-guarded viz
adapter):

    refined   solve the clean Laplace domain, cross-check relax vs direct
    crude     solve the leaky, noisy domain for comparison
    clash     stage crude vs refined; the more refined domain overwrites
    void      Unlimited Void: an interior pin that dominates on rigidity
    all       the whole demo end to end (the canonical report)

Each subcommand prints a stable, greppable headline plus numeric evidence, so the
output is easy to assert in tests. ``clash``/``all`` accept ``--png OUTDIR`` to
also export the field PNG (requires matplotlib).

Run:  python -m domain_expansion.adapters.cli all --png artifacts
"""

from __future__ import annotations

import argparse
import os
from typing import List, Optional, Sequence

from domain_expansion.adapters import render, viz
from domain_expansion.core import scenarios
from domain_expansion.core.clash import clash
from domain_expansion.core.domain import (
    Domain,
    direct_solve_domain,
    max_grid_diff,
    solve_domain,
)

# Canonical artifact filename (shared with the viz adapter).
_FIELD_PNG = "domain_expansion_field.png"


def _rule(title: str) -> List[str]:
    """A boxed section header as a list of output lines."""
    bar = "=" * 64
    return [bar, title, bar]


def _solve_block(domain: Domain, *, with_field: bool = True) -> List[str]:
    """Solve ``domain`` and return report lines (optionally with the field grid)."""
    result = solve_domain(domain)
    lines: List[str] = []
    if with_field:
        lines.append(
            render.format_field(result.field, f"\n{domain.name} field (steady state):")
        )
        lines.append("")
    lines.append(render.format_solve_report(domain.name, result))
    return lines


def render_refined() -> str:
    """``refined`` report: solve + a relax-vs-direct cross-check."""
    domain = scenarios.make_refined_domain()
    result = solve_domain(domain)
    direct = direct_solve_domain(domain)
    lines = _rule("DOMAIN EXPANSION :: refined domain")
    lines.append(
        render.format_field(result.field, f"\n{domain.name} field (Laplace steady state):")
    )
    lines.append("")
    lines.append(render.format_solve_report(domain.name, result))
    lines.append(
        f"  direct-solve check: max|relax - direct| = "
        f"{max_grid_diff(result.field, direct):.3e}"
    )
    return "\n".join(lines)


def render_crude() -> str:
    """``crude`` report: solve the leaky, noisy domain."""
    domain = scenarios.make_crude_domain()
    lines = _rule("DOMAIN EXPANSION :: crude domain")
    lines += _solve_block(domain)
    return "\n".join(lines)


def render_clash() -> str:
    """``clash`` report: crude vs refined, with the merged field."""
    crude = scenarios.make_crude_domain()
    refined = scenarios.make_refined_domain()
    result = clash(crude, refined)
    lines = _rule("CLASH: Crude Domain  vs  Refined Domain")
    lines.append(render.format_clash_report(result))
    return "\n".join(lines)


def render_void() -> str:
    """``void`` report: Unlimited Void dominates a clash on raw rigidity."""
    void = scenarios.make_void_domain()
    crude = scenarios.make_crude_domain()
    lines = _rule("UNLIMITED VOID :: infinite-information-density constraint")
    lines += _solve_block(void, with_field=False)
    result = clash(crude, void)
    lines.append("")
    lines.append(f"Void vs Crude winner: {result.winner}")
    lines.append(f"WHY : {result.reason}")
    return "\n".join(lines)


def render_all() -> str:
    """``all`` report: the whole demo end to end (the canonical report)."""
    blocks = [
        render_refined(),
        render_crude(),
        render_clash(),
        render_void(),
    ]
    footer = "\n".join(
        _rule("Summary")
        + [
            "The domain with the more stable, better-posed constraint system",
            "(lower residual, higher rigidity) overwrites the weaker one.",
        ]
    )
    return "\n\n".join(blocks + [footer])


def _write_png(outdir: str) -> str:
    """Render the field PNG into ``outdir`` and return a summary line block.

    DEFERRED: :func:`domain_expansion.adapters.viz.save_field_png` raises
    :class:`~domain_expansion.adapters.viz.OptionalDependencyError` when
    matplotlib is unavailable.
    """
    os.makedirs(outdir, exist_ok=True)
    target = os.path.join(outdir, _FIELD_PNG)
    viz.save_field_png(target)
    return "\nPNG export written (matplotlib, headless Agg backend):\n  " + target


_RENDERERS = {
    "refined": render_refined,
    "crude": render_crude,
    "clash": render_clash,
    "void": render_void,
    "all": render_all,
}

# Subcommands that expose the --png OUTDIR option.
_PNG_COMMANDS = {"clash", "all"}


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser with one subcommand per demo stage plus ``all``."""
    parser = argparse.ArgumentParser(
        prog="domain-expansion",
        description="Domain Expansion as a coupled constraint solver: a discretized "
        "Laplace boundary-value problem whose 'power' is its rigidity.",
    )
    sub = parser.add_subparsers(dest="command", required=True)
    descriptions = {
        "refined": "solve the clean Laplace domain (relax vs direct cross-check)",
        "crude": "solve the leaky, noisy domain for comparison",
        "clash": "stage crude vs refined; the more refined domain overwrites",
        "void": "Unlimited Void: an interior pin that dominates on rigidity",
        "all": "run the whole demo end to end (canonical report)",
    }
    for name, help_text in descriptions.items():
        p = sub.add_parser(name, help=help_text, description=help_text)
        if name in _PNG_COMMANDS:
            p.add_argument(
                "--png",
                metavar="OUTDIR",
                default=None,
                help="also render the field PNG into OUTDIR (requires the optional "
                "'viz' extra / matplotlib)",
            )
    return parser


def run_cli(argv: Optional[Sequence[str]] = None) -> str:
    """Resolve ``argv`` to the rendered report text (no printing).

    Kept side-effect free apart from the requested PNG export, so tests can assert
    on the returned string.
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    text = _RENDERERS[args.command]()
    png_dir = getattr(args, "png", None)
    if png_dir:
        text += _write_png(png_dir)
    return text


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry point: render the requested report and print it. Returns 0."""
    print(run_cli(argv))
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised via run_cli()/main()
    raise SystemExit(main())
