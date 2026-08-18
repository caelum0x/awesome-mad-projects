"""Command-line interface for the Divergence Meter.

Subcommands:
    measure <path-or-->     Compute and display the divergence for a source.
    field   [path-or--]     Classify the current line into an attractor field.
    save    <name> [src]    Save the current worldline under a name.
    jump    <name> [src]    Recall a saved worldline and show the delta to now.
    lines                   List all saved worldlines.

A "source" is a directory, a file, ``"-"`` for stdin, or literal text/JSON. When
a source is omitted for ``field``/``save``/``jump`` it defaults to the current
directory ``"."``.

This is an adapter: it wraps the pure :mod:`divergence_meter.core` engine plus the
ASCII nixie renderer and is never imported by ``core``. It is kept largely
side-effect free (apart from the Reading Steiner store writes) so tests can assert
on the returned strings via :func:`run_cli`.
"""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional, Sequence

from divergence_meter.adapters.nixie import render_reading
from divergence_meter.core.attractor import classify
from divergence_meter.core.divergence import DivergenceReading, compute_divergence
from divergence_meter.core.steiner import (
    DEFAULT_STORE_PATH,
    SteinerError,
    divergence_delta,
    get_line,
    list_lines,
    save_line,
)
from divergence_meter.core.worldstate import WorldStateError, snapshot_from_source

DEFAULT_SOURCE = "."


def _read(source: str) -> DivergenceReading:
    """Snapshot a source and compute its divergence reading."""
    snapshot = snapshot_from_source(source)
    return compute_divergence(snapshot)


def _reading_lines(reading: DivergenceReading, *, show_field: bool = True) -> List[str]:
    lines = [render_reading(reading.display)]
    lines.append(f"      origin   : {reading.origin}")
    lines.append(f"      sha256   : {reading.digest[:16]}...")
    if reading.is_steins_gate():
        lines.append(
            "      *** EL PSY CONGROO -- you are on the Steins;Gate worldline ***"
        )
    if show_field:
        lines.append(f"      {classify(reading.value).describe()}")
    return lines


def render_measure(source: str) -> str:
    """``measure`` report: the nixie display plus origin, hash, and field."""
    return "\n".join(_reading_lines(_read(source)))


def render_field(source: str) -> str:
    """``field`` report: the divergence value and its attractor classification."""
    reading = _read(source)
    result = classify(reading.value)
    return "\n".join([f"Divergence : {reading.display}", result.describe()])


def render_save(name: str, source: str, *, store_path: str) -> str:
    """``save`` report: confirm the stored worldline name, value, and origin."""
    reading = _read(source)
    record = save_line(name, reading, store_path=store_path)
    return "\n".join(
        [
            f"Saved worldline '{record.name}' @ {record.display}",
            f"  origin: {record.origin}",
            f"  store : {store_path}",
        ]
    )


def render_jump(name: str, source: str, *, store_path: str) -> str:
    """``jump`` report: the current nixie display plus the delta to a saved line."""
    saved = get_line(name, store_path=store_path)
    current = _read(source)
    delta = divergence_delta(saved.value, current.value)
    direction = (
        "Beta-ward (+)" if delta > 0 else "Alpha-ward (-)" if delta < 0 else "no shift"
    )
    return "\n".join(
        [
            render_reading(current.display),
            f"      Reading Steiner engaged. Jump target: '{saved.name}'",
            f"      saved line   : {saved.display}  ({saved.origin})",
            f"      current line : {current.display}  ({current.origin})",
            f"      divergence delta : {delta:+.6f}  [{direction}]",
        ]
    )


def render_lines(*, store_path: str) -> str:
    """``lines`` report: every saved worldline, sorted by name."""
    records = list_lines(store_path=store_path)
    if not records:
        return "No worldlines saved yet."
    out = [f"Saved worldlines ({len(records)}):"]
    for rec in records:
        out.append(f"  {rec.display}  {rec.name:<16} {rec.origin}  @ {rec.saved_at}")
    return "\n".join(out)


def build_parser() -> argparse.ArgumentParser:
    """Build the argparse parser with the five Divergence Meter subcommands."""
    parser = argparse.ArgumentParser(
        prog="divergence-meter",
        description="Steins;Gate Divergence Meter -- compute worldline divergence.",
    )
    parser.add_argument(
        "--store",
        default=DEFAULT_STORE_PATH,
        help=f"Path to the Reading Steiner JSON store (default: {DEFAULT_STORE_PATH}).",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    p_measure = sub.add_parser("measure", help="Compute and display divergence.")
    p_measure.add_argument("source", help="Directory, file, '-' for stdin, or text.")

    p_field = sub.add_parser("field", help="Classify into an attractor field.")
    p_field.add_argument("source", nargs="?", default=DEFAULT_SOURCE)

    p_save = sub.add_parser("save", help="Save the current worldline under a name.")
    p_save.add_argument("name", help="Name to store the worldline under.")
    p_save.add_argument("source", nargs="?", default=DEFAULT_SOURCE)

    p_jump = sub.add_parser("jump", help="Recall a saved worldline and show the delta.")
    p_jump.add_argument("name", help="Name of the saved worldline to jump to.")
    p_jump.add_argument("source", nargs="?", default=DEFAULT_SOURCE)

    sub.add_parser("lines", help="List all saved worldlines.")

    return parser


def run_cli(argv: Optional[Sequence[str]] = None) -> str:
    """Resolve ``argv`` to the rendered report text (no printing).

    Raises the underlying :class:`WorldStateError` / :class:`SteinerError` /
    :class:`ValueError` so callers (and :func:`main`) decide how to report them.
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    store = args.store
    if args.command == "measure":
        return render_measure(args.source)
    if args.command == "field":
        return render_field(args.source)
    if args.command == "save":
        return render_save(args.name, args.source, store_path=store)
    if args.command == "jump":
        return render_jump(args.name, args.source, store_path=store)
    if args.command == "lines":
        return render_lines(store_path=store)
    raise ValueError(f"Unknown command: {args.command!r}")  # pragma: no cover


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry point: render the requested report and print it.

    Returns 0 on success, 1 for world-state/store errors, 2 for value/type
    errors -- mirroring the standalone prototype's exit codes.
    """
    try:
        print(run_cli(argv))
        return 0
    except (WorldStateError, SteinerError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except (ValueError, TypeError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":  # pragma: no cover - exercised via run_cli()/main()
    raise SystemExit(main())
