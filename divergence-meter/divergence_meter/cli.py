"""Command-line interface for the Divergence Meter.

Subcommands:
    measure <path-or-->     Compute and display the divergence for a source.
    field   [path-or--]     Classify the current line into an attractor field.
    save    <name> [src]    Save the current worldline under a name.
    jump    <name> [src]    Recall a saved worldline and show the delta to now.
    lines                   List all saved worldlines.

A "source" is a directory, a file, "-" for stdin, or literal text/JSON. When a
source is omitted for field/save/jump it defaults to the current directory ".".
"""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .attractor import classify
from .divergence import DivergenceReading, compute_divergence
from .nixie import render_reading
from .steiner import (
    DEFAULT_STORE_PATH,
    SteinerError,
    divergence_delta,
    get_line,
    list_lines,
    save_line,
)
from .worldstate import WorldStateError, snapshot_from_source

DEFAULT_SOURCE = "."


def _read(source: str) -> DivergenceReading:
    """Snapshot a source and compute its divergence reading."""
    snapshot = snapshot_from_source(source)
    return compute_divergence(snapshot)


def _print_reading(reading: DivergenceReading, *, show_field: bool = True) -> None:
    print(render_reading(reading.display))
    print(f"      origin   : {reading.origin}")
    print(f"      sha256   : {reading.digest[:16]}...")
    if reading.is_steins_gate():
        print("      *** EL PSY CONGROO -- you are on the Steins;Gate worldline ***")
    if show_field:
        print(f"      {classify(reading.value).describe()}")


def cmd_measure(args: argparse.Namespace) -> int:
    reading = _read(args.source)
    _print_reading(reading)
    return 0


def cmd_field(args: argparse.Namespace) -> int:
    reading = _read(args.source)
    result = classify(reading.value)
    print(f"Divergence : {reading.display}")
    print(result.describe())
    return 0


def cmd_save(args: argparse.Namespace) -> int:
    reading = _read(args.source)
    record = save_line(args.name, reading, store_path=args.store)
    print(f"Saved worldline '{record.name}' @ {record.display}")
    print(f"  origin: {record.origin}")
    print(f"  store : {args.store}")
    return 0


def cmd_jump(args: argparse.Namespace) -> int:
    saved = get_line(args.name, store_path=args.store)
    current = _read(args.source)
    delta = divergence_delta(saved.value, current.value)
    direction = "Beta-ward (+)" if delta > 0 else "Alpha-ward (-)" if delta < 0 else "no shift"
    print(render_reading(current.display))
    print(f"      Reading Steiner engaged. Jump target: '{saved.name}'")
    print(f"      saved line   : {saved.display}  ({saved.origin})")
    print(f"      current line : {current.display}  ({current.origin})")
    print(f"      divergence Δ : {delta:+.6f}  [{direction}]")
    return 0


def cmd_lines(args: argparse.Namespace) -> int:
    records = list_lines(store_path=args.store)
    if not records:
        print("No worldlines saved yet.")
        return 0
    print(f"Saved worldlines ({len(records)}):")
    for rec in records:
        print(f"  {rec.display}  {rec.name:<16} {rec.origin}  @ {rec.saved_at}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="divergence_meter",
        description="Steins;Gate Divergence Meter -- compute worldline divergence.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument(
        "--store",
        default=DEFAULT_STORE_PATH,
        help=f"Path to the Reading Steiner JSON store (default: {DEFAULT_STORE_PATH}).",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    p_measure = sub.add_parser("measure", help="Compute and display divergence.")
    p_measure.add_argument("source", help="Directory, file, '-' for stdin, or literal text.")
    p_measure.set_defaults(func=cmd_measure)

    p_field = sub.add_parser("field", help="Classify into an attractor field.")
    p_field.add_argument("source", nargs="?", default=DEFAULT_SOURCE)
    p_field.set_defaults(func=cmd_field)

    p_save = sub.add_parser("save", help="Save the current worldline under a name.")
    p_save.add_argument("name", help="Name to store the worldline under.")
    p_save.add_argument("source", nargs="?", default=DEFAULT_SOURCE)
    p_save.set_defaults(func=cmd_save)

    p_jump = sub.add_parser("jump", help="Recall a saved worldline and show the delta.")
    p_jump.add_argument("name", help="Name of the saved worldline to jump to.")
    p_jump.add_argument("source", nargs="?", default=DEFAULT_SOURCE)
    p_jump.set_defaults(func=cmd_jump)

    p_lines = sub.add_parser("lines", help="List all saved worldlines.")
    p_lines.set_defaults(func=cmd_lines)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except (WorldStateError, SteinerError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except (ValueError, TypeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
