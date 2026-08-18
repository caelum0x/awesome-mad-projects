"""CLI demo for the p-adic embedding space.

Examples
--------
Default demo (2-adic clustering of a list of integers):

    python3 demo.py

Choose a prime and supply your own integers:

    python3 demo.py --p 7 --ints 7 14 49 50 98 100 343

Embed short strings and query nearest neighbors:

    python3 demo.py --p 2 --strings cat cot cog dog log apple --query cat

Standard library only.
"""

from __future__ import annotations

import argparse
from typing import List, Sequence

import embedding
import padic


def _fmt(x: float) -> str:
    """Compact fixed-width formatting for distances in [0, 1]."""
    if x == 0.0:
        return "0".rjust(8)
    return f"{x:.5f}".rjust(8)


def print_distance_matrix(labels: Sequence[str], coords: Sequence[int],
                          p: int) -> None:
    matrix = embedding.distance_matrix(coords, p)
    width = max(8, max(len(s) for s in labels) + 1)
    header = " " * width + "".join(s.rjust(9) for s in labels)
    print(header)
    for i, row_label in enumerate(labels):
        cells = "".join(_fmt(matrix[i][j]) + " " for j in range(len(labels)))
        print(row_label.rjust(width) + " " + cells)


def print_valuation_table(labels: Sequence[str], coords: Sequence[int],
                          p: int) -> None:
    print(f"item{'':6} coord{'':8} v_{p}(coord)   |coord|_{p}")
    for label, c in zip(labels, coords):
        v = padic.valuation(c, p)
        a = padic.p_adic_abs(c, p)
        v_str = "inf" if v == float("inf") else str(int(v))
        print(f"{label:<10} {c:<12} {v_str:>8}      {a:.6f}")


def run(p: int, items: Sequence, is_strings: bool, query, levels: List[int],
        modulus: int) -> None:
    labels = [str(it) for it in items]
    coords = embedding.embed(items, modulus)

    print("=" * 64)
    print(f"p-adic Embedding Space   (prime p = {p})")
    print("=" * 64)

    kind = "strings (SHA-256 hashed into Z)" if is_strings else "integers"
    print(f"\nItems ({kind}):")
    for label, c in zip(labels, coords):
        print(f"  {label!r:<14} -> coordinate {c}")

    print("\n--- p-adic valuation / absolute value of each coordinate ---")
    print_valuation_table(labels, coords, p)

    print(f"\n--- Pairwise {p}-adic distance matrix  d_p(a,b) = |a-b|_p ---")
    print_distance_matrix(labels, coords, p)

    print("\n--- Ultrametric (strong triangle inequality) verification ---")
    ok, checked, failures = embedding.verify_ultrametric(coords, p)
    print(f"  d_p(a,c) <= max(d_p(a,b), d_p(b,c)) for ALL ordered triples?")
    print(f"  triples checked: {checked}")
    print(f"  violations found: {len(failures)}")
    print(f"  RESULT: {'HOLDS (this is a true ultrametric)' if ok else 'FAILED'}")
    if failures:
        for a, b, c in failures[:5]:
            print(f"    counterexample: a={a}, b={b}, c={c}")

    print("\n--- Hierarchical clusters induced by p-adic proximity ---")
    print("  (coordinates in the same group agree modulo p**level;")
    print("   each group is a ball of radius p**(-level) in Z_p)")
    for level in levels:
        radius = float(p) ** (-level)
        clusters = embedding.cluster_by_valuation(coords, p, level)
        print(f"\n  level {level}: balls of radius {radius:g} "
              f"(mod {p}**{level} = {p ** level})")
        for key in sorted(clusters):
            members = sorted(clusters[key])
            print(f"    residue {key:>6} : {members}")

    if query is not None:
        print(f"\n--- Nearest neighbors of {query!r} under the {p}-adic metric ---")
        neighbors = embedding.nearest_neighbors(query, items, p, k=3,
                                                modulus=modulus)
        if not neighbors:
            print("  (no other items to compare)")
        for it, d in neighbors:
            print(f"  {it!r:<14} distance {d:.6f}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="p-adic embedding space demo")
    parser.add_argument("--p", type=int, default=2, help="prime p (default 2)")
    parser.add_argument("--ints", type=int, nargs="+",
                        help="integer items to embed")
    parser.add_argument("--strings", type=str, nargs="+",
                        help="string items to embed (SHA-256 hashed into Z)")
    parser.add_argument("--query", type=str, default=None,
                        help="item for nearest-neighbor search")
    parser.add_argument("--levels", type=int, nargs="+", default=[1, 2, 3],
                        help="clustering levels to display (default 1 2 3)")
    parser.add_argument("--modulus", type=int, default=2 ** 20,
                        help="hash modulus for strings (default 2**20)")
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = build_parser().parse_args(argv)

    if not padic.is_prime(args.p):
        raise SystemExit(f"error: p={args.p} is not prime")

    if args.strings:
        items: List = list(args.strings)
        is_strings = True
        query = args.query
    elif args.ints:
        items = list(args.ints)
        is_strings = False
        query = int(args.query) if args.query is not None else None
    else:
        # Default showcase: integers chosen to reveal 2-adic tree structure.
        items = [1, 3, 5, 8, 16, 17, 24, 32, 48, 64]
        is_strings = False
        query = int(args.query) if args.query is not None else 16

    run(args.p, items, is_strings, query, args.levels, args.modulus)


if __name__ == "__main__":
    main()
