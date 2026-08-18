#!/usr/bin/env python3
"""Stitch one headline still per project into a single shareable poster.

Writes ``artifacts/poster.png``. Requires matplotlib — run it with the venv:

    .venv/bin/python gallery/build_poster.py

It composes existing PNG stills already in ``artifacts/`` (rendered by the
package viz adapters), so it never recomputes any math; it is pure presentation.
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
ARTIFACTS = os.path.join(ROOT, "artifacts")

# (panel title, candidate source stills in priority order)
PANELS: list[tuple[str, list[str]]] = [
    ("Gojo's Infinity — 3-D geodesics bending around Gojo",
     ["gojo_geodesic_3d.png", "gojo_metric_blowup.png", "gojo_geodesic_bundle.png"]),
    ("Mobius — Central Finite Curve  R^-1(0)",
     ["mobius_strip_curve.png", "mobius_krick_heatmap.png"]),
    ("Central Finite Curve — near-maximal Rickness band",
     ["central_finite_curve_projection.png"]),
    ("Mobius — SCMS ridge (crest of max Rickness)",
     ["mobius_ridge.png", "mobius_krick_heatmap.png"]),
]

TITLE = "infinity-lab   ·   anime  x  mathematics, in real code"


def _pick(candidates: list[str]) -> str | None:
    for name in candidates:
        path = os.path.join(ARTIFACTS, name)
        if os.path.exists(path):
            return path
    return None


def build_poster(out_path: str | None = None) -> str:
    """Render the poster and return its path. Raises RuntimeError if matplotlib
    is unavailable or no source stills exist."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.image as mpimg
        import matplotlib.pyplot as plt
    except Exception as exc:  # pragma: no cover - exercised only without mpl
        raise RuntimeError(f"matplotlib is required (use the venv): {exc}") from exc

    chosen = [(title, _pick(cands)) for title, cands in PANELS]
    chosen = [(title, path) for title, path in chosen if path]
    if not chosen:
        raise RuntimeError(f"no source stills found in {ARTIFACTS}")

    cols = 2
    rows = (len(chosen) + cols - 1) // cols
    fig, axes = plt.subplots(rows, cols, figsize=(cols * 5.3, rows * 4.1))
    flat = axes.ravel() if hasattr(axes, "ravel") else [axes]
    for ax, (title, path) in zip(flat, chosen):
        ax.imshow(mpimg.imread(path))
        ax.set_title(title, fontsize=11)
        ax.axis("off")
    for ax in flat[len(chosen):]:
        ax.axis("off")

    fig.suptitle(TITLE, fontsize=17, y=0.995)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    out_path = out_path or os.path.join(ARTIFACTS, "poster.png")
    fig.savefig(out_path, dpi=140)
    plt.close(fig)
    return out_path


def main() -> int:
    try:
        out = build_poster()
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"Wrote {out} ({os.path.getsize(out)} bytes) from {len(PANELS)} candidate panels")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
