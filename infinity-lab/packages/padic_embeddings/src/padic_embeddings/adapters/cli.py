"""Command-line front end for the p-adic embedding space.

``argparse`` over the pure :mod:`padic_embeddings.core` engine (and, for ``--png``,
the lazily-guarded viz adapter). Choose a prime ``p``, feed integers or strings, and
the report prints:

    * each item's integer coordinate,
    * a valuation / absolute-value table,
    * the pairwise p-adic distance matrix (labelled table + shaded heatmap),
    * the EXHAUSTIVE ultrametric (strong-triangle) verdict,
    * the residue-class clusters (the nested p-adic balls), and
    * optionally the nearest neighbours of a query item.

The report is assembled as a string by :func:`run_cli` (side-effect free apart from a
requested ``--png`` export) so tests can assert on it.

Run:  python -m padic_embeddings.adapters.cli --p 2 --ints 1 3 5 8 16 17 24 32 48 64
"""

from __future__ import annotations

import argparse
import os
from typing import List, Optional, Sequence

from padic_embeddings.core import embedding, padic
from padic_embeddings.adapters import render, viz

# Default showcase: integers chosen to reveal the 2-adic tree structure.
_DEFAULT_INTS = [1, 3, 5, 8, 16, 17, 24, 32, 48, 64]
_DEFAULT_QUERY = 16
_DEFAULT_LEVELS = [1, 2, 3]


def _rule(title: str) -> List[str]:
    """A boxed section header as a list of output lines."""
    bar = "=" * 64
    return [bar, title, bar]


def _resolve_items(
    args: argparse.Namespace,
) -> tuple[List[object], bool, Optional[object]]:
    """Resolve the items, whether they are strings, and the query from ``args``."""
    if args.strings:
        return list(args.strings), True, args.query
    if args.ints:
        query = int(args.query) if args.query is not None else None
        return list(args.ints), False, query
    query = int(args.query) if args.query is not None else _DEFAULT_QUERY
    return list(_DEFAULT_INTS), False, query


def render_report(
    p: int,
    items: Sequence[object],
    is_strings: bool,
    query: Optional[object],
    levels: Sequence[int],
    modulus: int,
) -> str:
    """Assemble the full text report for one embedding run."""
    if not padic.is_prime(p):
        raise ValueError(f"p must be prime, got {p}")
    labels = [str(it) for it in items]
    coords = embedding.embed(items, modulus)

    lines = _rule(f"p-adic Embedding Space   (prime p = {p})")
    kind = "strings (SHA-256 hashed into Z)" if is_strings else "integers"
    lines.append(f"\nItems ({kind}):")
    for label, c in zip(labels, coords):
        lines.append(f"  {label!r:<14} -> coordinate {c}")

    lines.append("\n--- valuation / absolute value of each coordinate ---")
    lines.append(render.format_valuation_table(labels, coords, p))

    lines.append("\n--- distance matrix ---")
    lines.append(render.format_distance_matrix(labels, coords, p))

    lines.append("\n--- distance heatmap ---")
    lines.append(render.distance_heatmap(coords, p))

    lines.append("\n--- ultrametric verification ---")
    lines.append(render.format_ultrametric_report(coords, p))

    lines.append("\n--- clusters ---")
    lines.append(render.format_clusters(coords, p, levels))

    if query is not None:
        neighbors = embedding.nearest_neighbors(query, items, p, k=3, modulus=modulus)
        lines.append("\n--- nearest neighbors ---")
        lines.append(render.format_nearest_neighbors(str(query), neighbors, p))

    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the p-adic embedding demo."""
    parser = argparse.ArgumentParser(
        prog="padic-embeddings",
        description="An embedding space governed by the p-adic (ultrametric) metric.",
    )
    parser.add_argument("--p", type=int, default=2, help="prime p (default 2)")
    parser.add_argument("--ints", type=int, nargs="+", help="integer items to embed")
    parser.add_argument(
        "--strings", type=str, nargs="+",
        help="string items to embed (SHA-256 hashed into Z)",
    )
    parser.add_argument(
        "--query", type=str, default=None, help="item for nearest-neighbor search"
    )
    parser.add_argument(
        "--levels", type=int, nargs="+", default=list(_DEFAULT_LEVELS),
        help="clustering levels to display (default 1 2 3)",
    )
    parser.add_argument(
        "--modulus", type=int, default=embedding.DEFAULT_MODULUS,
        help="hash modulus for strings (default 2**20)",
    )
    parser.add_argument(
        "--png", metavar="OUTDIR", default=None,
        help="also render the distance-matrix PNG into OUTDIR (requires the "
        "optional 'viz' extra / matplotlib)",
    )
    return parser


def _write_png(
    outdir: str, items: Sequence[object], p: int, modulus: int
) -> str:
    """Render the distance-matrix PNG into ``outdir`` and return a summary block.

    DEFERRED: :func:`padic_embeddings.adapters.viz.save_distance_matrix_png` raises
    :class:`~padic_embeddings.adapters.viz.OptionalDependencyError` when matplotlib is
    unavailable.
    """
    os.makedirs(outdir, exist_ok=True)
    target = os.path.join(outdir, viz.DISTANCE_MATRIX_PNG)
    labels = [str(it) for it in items]
    coords = embedding.embed(items, modulus)
    viz.save_distance_matrix_png(target, coords, p, labels=labels)
    return "\nPNG export written (matplotlib, headless Agg backend):\n  " + target


def run_cli(argv: Optional[Sequence[str]] = None) -> str:
    """Resolve ``argv`` to the rendered report text (no printing).

    Side-effect free apart from a requested ``--png`` export, so tests can assert on
    the returned string. Raises :class:`SystemExit` for a non-prime ``p``.
    """
    args = build_parser().parse_args(argv)
    if not padic.is_prime(args.p):
        raise SystemExit(f"error: p={args.p} is not prime")
    items, is_strings, query = _resolve_items(args)
    text = render_report(args.p, items, is_strings, query, args.levels, args.modulus)
    if args.png:
        text += _write_png(args.png, items, args.p, args.modulus)
    return text


def main(argv: Optional[Sequence[str]] = None) -> int:
    """CLI entry point: render the requested report and print it. Returns 0."""
    print(run_cli(argv))
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised via run_cli()/main()
    raise SystemExit(main())
