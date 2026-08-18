"""ASCII rendering of the p-adic embedding space (stdlib only, deterministic).

Turns the pure :mod:`padic_embeddings.core` results into plain ``str`` blocks that
are safe to print or pin in tests. Two views of the distance structure are offered:

  * :func:`format_distance_matrix` -- a bespoke labelled fixed-width table (the
    familiar "who is close to whom" matrix), which the generic commons renderers do
    not provide directly.
  * :func:`distance_heatmap` -- a pure shaded view that DELEGATES to
    :func:`commons.adapters.ascii_art.render_heatmap`, where a labelled shaded grid
    with a value legend is the natural tool.

Alongside them: valuation tables, residue-class clusters (the p-adic balls), the
exhaustive ultrametric verdict, and a nearest-neighbour list.

This is an adapter: it imports ``core`` and ``commons.adapters`` but is never
imported by ``core``.
"""

from __future__ import annotations

from typing import List, Sequence, Tuple

from commons.adapters.ascii_art import render_heatmap

from padic_embeddings.core import embedding, padic

Item = padic.Number


def _fmt_distance(x: float) -> str:
    """Compact fixed-width formatting for a distance in ``[0, 1]``."""
    if x == 0.0:
        return "0".rjust(8)
    return f"{x:.5f}".rjust(8)


def format_distance_matrix(
    labels: Sequence[str], coords: Sequence[int], p: int
) -> str:
    """Return the labelled pairwise ``p``-adic distance matrix as text."""
    matrix = embedding.distance_matrix(coords, p)
    width = max(8, max((len(s) for s in labels), default=0) + 1)
    lines: List[str] = [f"pairwise {p}-adic distance matrix  d_p(a,b) = |a-b|_p"]
    header = " " * width + "".join(s.rjust(9) for s in labels)
    lines.append(header)
    for i, row_label in enumerate(labels):
        cells = "".join(_fmt_distance(matrix[i][j]) + " " for j in range(len(labels)))
        lines.append(row_label.rjust(width) + " " + cells)
    return "\n".join(lines)


def distance_heatmap(coords: Sequence[int], p: int) -> str:
    """Shaded heatmap of the distance matrix via the shared commons renderer."""
    if not coords:
        return "(no coordinates)"
    matrix = embedding.distance_matrix(coords, p)
    return render_heatmap(matrix, width=len(coords), title=f"{p}-adic distance heatmap")


def format_valuation_table(
    labels: Sequence[str], coords: Sequence[int], p: int
) -> str:
    """Return a table of ``v_p(coord)`` and ``|coord|_p`` for each item."""
    lines: List[str] = [f"item        coord         v_{p}(coord)   |coord|_{p}"]
    for label, c in zip(labels, coords):
        v = padic.valuation(c, p)
        a = padic.p_adic_abs(c, p)
        v_str = "inf" if v == float("inf") else str(int(v))
        lines.append(f"{label:<10} {c:<12} {v_str:>8}      {a:.6f}")
    return "\n".join(lines)


def format_clusters(
    coords: Sequence[int], p: int, levels: Sequence[int]
) -> str:
    """Return the residue-class balls at each requested clustering level."""
    lines: List[str] = [
        "hierarchical clusters induced by p-adic proximity",
        "  (coordinates in a group agree modulo p**level;",
        "   each group is a ball of radius p**(-level) in Z_p)",
    ]
    for level in levels:
        radius = float(p) ** (-level)
        clusters = embedding.cluster_by_valuation(coords, p, level)
        lines.append(
            f"\n  level {level}: balls of radius {radius:g} "
            f"(mod {p}**{level} = {p ** level})"
        )
        for key in sorted(clusters):
            lines.append(f"    residue {key:>6} : {clusters[key]}")
    return "\n".join(lines)


def format_ultrametric_report(coords: Sequence[int], p: int) -> str:
    """Return the exhaustive strong-triangle-inequality verdict as text."""
    ok, checked, failures = embedding.verify_ultrametric(coords, p)
    lines: List[str] = [
        "ultrametric (strong triangle inequality) verification",
        "  d_p(a,c) <= max(d_p(a,b), d_p(b,c)) for ALL ordered triples?",
        f"  triples checked : {checked}",
        f"  violations found: {len(failures)}",
        f"  RESULT: {'HOLDS (this is a true ultrametric)' if ok else 'FAILED'}",
    ]
    for a, b, c in failures[:5]:
        lines.append(f"    counterexample: a={a}, b={b}, c={c}")
    return "\n".join(lines)


def format_nearest_neighbors(
    query: str, neighbors: Sequence[Tuple[object, float]], p: int
) -> str:
    """Return the nearest-neighbour list for ``query`` under the ``p``-adic metric."""
    lines: List[str] = [f"nearest neighbors of {query!r} under the {p}-adic metric"]
    if not neighbors:
        lines.append("  (no other items to compare)")
    for it, d in neighbors:
        lines.append(f"  {it!r:<14} distance {d:.6f}")
    return "\n".join(lines)
