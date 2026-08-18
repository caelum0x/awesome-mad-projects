#!/usr/bin/env python3
"""Build a self-contained static showcase gallery for infinity-lab.

Standard-library only (no third-party deps). Run it directly with any
Python 3.9+ interpreter:

    python3 gallery/build_gallery.py

It DYNAMICALLY scans ``artifacts/`` at run time, so re-running after adding
new PNG/GIF/MP4 files picks them up automatically -- anything unrecognised is
still embedded under an "Other artifacts" section so nothing is ever dropped.

The output ``gallery/index.html`` is fully self-contained: inline CSS, no
external CDNs, relative ``../artifacts/NAME`` paths. It opens offline with zero
network dependencies.

Attribution: the mathematical framing showcased here is *after* Achmad Roykhan
Sabiq, "Mathematics Behind Jujutsu Kaisen: Gojo Satoru's Infinity", Oxford
University Mathematics Essay Competition 2026. This gallery is an original
summary/companion -- it does not reproduce the essay's prose. See
``docs/essay-source.md`` for the section-by-section companion and the PDF URL.
"""

from __future__ import annotations

import html
import os
from typing import Dict, List, NamedTuple, Optional, Tuple

# ---------------------------------------------------------------------------
# Paths (repo-relative, robust to the caller's working directory)
# ---------------------------------------------------------------------------

_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.dirname(_HERE)
_ARTIFACTS_DIR = os.path.join(_REPO_ROOT, "artifacts")
_OUTPUT_HTML = os.path.join(_HERE, "index.html")

# Media extensions we know how to embed, mapped to a coarse kind.
_IMAGE_EXTS = {".png", ".gif", ".jpg", ".jpeg", ".webp", ".svg"}
_VIDEO_EXTS = {".mp4", ".webm", ".ogv", ".mov"}

_ESSAY_PDF_URL = (
    "https://tomrocksmaths.com/wp-content/uploads/2026/06/"
    "achmad-roykhan-sabiq_essay_competition_2026-achmad-roykhan-sabiq.pdf"
)


class Figure(NamedTuple):
    """One embeddable artifact plus its human-facing metadata."""

    filename: str
    title: str
    caption: str  # HTML-safe already (contains intentional inline markup)


class Group(NamedTuple):
    """A titled group of figures within a section."""

    heading: str
    blurb: str
    filenames: Tuple[str, ...]


class Section(NamedTuple):
    """A top-level section of the gallery."""

    section_id: str
    title: str
    subtitle: str
    groups: Tuple[Group, ...]


# ---------------------------------------------------------------------------
# Per-artifact metadata. Captions are ORIGINAL (not copied from the essay),
# explaining what each figure shows plus the relevant formula / verdict.
# ---------------------------------------------------------------------------

_METADATA: Dict[str, Tuple[str, str]] = {
    # -- gojo_infinity ------------------------------------------------------
    "gojo_metric_blowup.png": (
        "Lens 3 &mdash; conformal metric blow-up",
        "The one-dimensional conformal factor <code>&Omega;(x)</code> and the "
        "induced metric <code>g = &Omega;(x)&sup2;</code> plotted as the "
        "attacker&rsquo;s coordinate approaches Gojo at <code>x = 1</code>. Far "
        "away <code>g &asymp; 1</code>, so a physical step feels like itself; "
        "near Gojo the same step is stretched without bound. "
        "<em>ds&sup2; = &Sigma; g<sub>ij</sub> dx<sub>i</sub> dx<sub>j</sub></em>, "
        "with <code>&Omega;(x) = 1 + &lambda;&middot;exp(&minus;(x<sub>g</sub>&minus;x)&sup2;/&sigma;&sup2;)/(x<sub>g</sub>&minus;x)</code>. "
        "<strong>Verdict: FORMIDABLE.</strong>",
    ),
    "gojo_series_convergence.png": (
        "Lens 1 &mdash; geometric series converges",
        "The Zeno partial sums <code>S<sub>n</sub> = 1 &minus; (1/2)<sup>n</sup></code> "
        "climbing toward the dashed line <code>S = 1</code>, with the residual "
        "<code>(1/2)<sup>n</sup> &gt; 0</code> shrinking but never reaching zero. "
        "The full geometric sum <code>a/(1&minus;r)</code> with "
        "<code>a = r = 1/2</code> equals exactly 1, and the arrival time is finite: "
        "the attacker <em>arrives</em>. <strong>Verdict: FRAGILE.</strong>",
    ),
    "gojo_cover_convergence.png": (
        "Lens 2 &mdash; Lebesgue covering",
        "The measure-theoretic covering of the barrier "
        "<code>Z = {1 &minus; 1/2<sup>n</sup>}</code>: each point "
        "<code>z<sub>n</sub></code> is boxed by an interval of length "
        "<code>&epsilon;/2<sup>n</sup></code>, so the total cover length "
        "telescopes to exactly <code>&epsilon;</code>. Since <code>&epsilon;</code> "
        "is arbitrary, the infimum is 0 and <code>m(Z) = 0</code>: countably many "
        "points of total length zero. <strong>Verdict: FRAGILE (null set).</strong>",
    ),
    "gojo_geodesic_bundle.png": (
        "Lens 3 (2-D) &mdash; geodesic bundle",
        "A bundle of true geodesics on the 2-D conformally-flat manifold "
        "<code>g<sub>ij</sub> = &Omega;&sup2; &delta;<sub>ij</sub></code> (Gojo at "
        "the origin), integrated with an RK4 solver. Each ray bends inward as it "
        "nears Gojo, the metric&rsquo;s light-bending analogue, yet the felt path "
        "length keeps growing. <strong>Verdict: FORMIDABLE.</strong>",
    ),
    "gojo_length_divergence.png": (
        "Lens 3 (2-D) &mdash; felt length diverges",
        "The felt (Riemannian) length required to reach within <code>&delta;</code> "
        "of Gojo, plotted against <code>&delta; &rarr; 0</code>. Each decade of "
        "approach adds roughly <code>&lambda;&middot;ln 10</code>, so the improper "
        "integral <code>L = &int; &Omega; dx</code> diverges: no finite felt "
        "distance reaches the barrier. <strong>Verdict: FORMIDABLE.</strong>",
    ),
    "gojo_geodesic_3d.png": (
        "Lens 3 (3-D) &mdash; geodesics in R&sup3;",
        "The same conformal construction lifted to three dimensions "
        "(<code>ConformalMetricND</code>): a bundle of geodesics travelling in "
        "<code>+x</code> and bending toward Gojo at the origin. One code path "
        "serves 1-D, 2-D and 3-D; here it verifies planarity, affine-energy "
        "conservation and radial parity with the 1-D lens. "
        "<strong>Verdict: FORMIDABLE.</strong>",
    ),
    "gojo_geodesic_approach.gif": (
        "Lens 3 &mdash; approach animation (GIF)",
        "An animated geodesic bending around Gojo and slowing as its accumulated "
        "felt length climbs &mdash; it approaches forever but never arrives. The "
        "Euclidean gap shrinks while <code>&int; &Omega; dx</code> grows without "
        "bound. <strong>Verdict: FORMIDABLE.</strong>",
    ),
    "gojo_geodesic_approach.mp4": (
        "Lens 3 &mdash; approach animation (MP4)",
        "The same approaching-geodesic scene re-encoded to MP4 via ffmpeg: the "
        "ray asymptotically nears Gojo as its felt Riemannian length diverges. "
        "<strong>Verdict: FORMIDABLE.</strong>",
    ),
    "gojo_never_arrives.gif": (
        "Lens 1/3 &mdash; the attacker never arrives (GIF)",
        "The Zeno steps <code>x<sub>n</sub> = 1 &minus; (1/2)<sup>n</sup></code> "
        "marching toward Gojo. The residual <code>(1/2)<sup>n</sup> &gt; 0</code> "
        "stays strictly positive at every finite step while the felt length "
        "diverges &mdash; the tension between the FRAGILE (series) and FORMIDABLE "
        "(metric) readings made visible.",
    ),
    "gojo_geodesic_3d_rotating.gif": (
        "Lens 3 (3-D) &mdash; rotating geodesics (GIF)",
        "A few geodesics bending around Gojo in <code>R&sup3;</code> while the "
        "camera orbits the scene (azimuth advances and elevation sweeps each "
        "frame). The 3-D generalisation of the metric&rsquo;s inward light-bending. "
        "<strong>Verdict: FORMIDABLE.</strong>",
    ),
    "gojo_geodesic_3d_rotating.mp4": (
        "Lens 3 (3-D) &mdash; rotating geodesics (MP4)",
        "The rotating 3-D geodesic bundle re-encoded to MP4 via ffmpeg &mdash; an "
        "orbiting view of rays curving toward Gojo at the origin. "
        "<strong>Verdict: FORMIDABLE.</strong>",
    ),
    # -- mobius_rickness ----------------------------------------------------
    "mobius_strip_curve.png": (
        "Central Finite Curve &mdash; strip + zero set",
        "The M&ouml;bius strip (a ruled surface, hence strictly negative Gaussian "
        "curvature <code>K &lt; 0</code> on its interior) with the traced Central "
        "Finite Curve <code>R<sup>&minus;1</sup>(0)</code> overlaid. Because "
        "<code>K</code> never vanishes, the weighted field "
        "<code>K<sub>Rick</sub> = K&middot;R</code> is zero exactly where "
        "<code>R = 0</code>, so this red locus separates &lsquo;Rick-positive&rsquo; "
        "from &lsquo;Rick-negative&rsquo; universes on the band. "
        "<strong>Reading 1: the zero set R<sup>&minus;1</sup>(0).</strong>",
    ),
    "mobius_krick_heatmap.png": (
        "Central Finite Curve &mdash; K&middot;R heatmap",
        "A heatmap of the weighted field "
        "<code>K<sub>Rick</sub>(u,v) = K(u,v)&middot;R(u,v)</code> in "
        "<code>(u,v)</code> parameter space with the zero contour drawn on top. "
        "Since <code>K &lt; 0</code> strictly (worst "
        "<code>K = &minus;0.055927</code>), the sign changes of "
        "<code>K<sub>Rick</sub></code> come entirely from <code>R</code>, and the "
        "contour is the Central Finite Curve.",
    ),
    "mobius_ridge.png": (
        "Central Finite Curve &mdash; SCMS ridge",
        "The M&ouml;bius surface with the SCMS / Eberly height-ridge of maximal "
        "Rickness overlaid &mdash; the second, independent formalization of the "
        "Central Finite Curve. Where reading 1 solves "
        "<code>R<sup>&minus;1</sup>(0)</code> exactly, this ridge follows the crest "
        "of the field as a principal-curvature ridge. "
        "<strong>Reading 2: the SCMS ridge.</strong>",
    ),
    "mobius_rotating.gif": (
        "Central Finite Curve &mdash; rotating strip (GIF)",
        "An orbiting camera over the semi-transparent M&ouml;bius strip, overlaying "
        "<em>both</em> Central Finite Curve readings at once: the exact zero set "
        "<code>R<sup>&minus;1</sup>(0)</code> (red) and the SCMS ridge (orange). "
        "The two readings track the same feature from different mathematics.",
    ),
    "mobius_rotating.mp4": (
        "Central Finite Curve &mdash; rotating strip (MP4)",
        "The rotating M&ouml;bius scene re-encoded to MP4 via ffmpeg, showing the "
        "zero set <code>R<sup>&minus;1</sup>(0)</code> and the SCMS ridge together "
        "under an orbiting view.",
    ),
    # -- central_finite_curve (engine) --------------------------------------
    "central_finite_curve_projection.png": (
        "Rickness engine &mdash; ridge projection",
        "A flattened projection of the <code>central_finite_curve</code> engine: "
        "the Rickness ridge &mdash; the crest of near-maximal Rickness &mdash; "
        "traced across a simulated multiverse and projected to the plane. The "
        "highlighted band marks where the field sits within a near-maximal "
        "tolerance of its ridge, the engine&rsquo;s notion of &lsquo;the one arc "
        "of realities where a Rick exists.&rsquo;",
    ),
    "central_finite_curve_walk.gif": (
        "Rickness engine &mdash; ridge walk (GIF)",
        "An animated walk stepping along the Central Finite Curve as the engine "
        "follows the Rickness ridge / near-maximal band across the simulated "
        "multiverse, one reality at a time. The path stays pinned to the crest of "
        "the field rather than crossing it.",
    ),
    "central_finite_curve_walk.mp4": (
        "Rickness engine &mdash; ridge walk (MP4)",
        "The same ridge-walk re-encoded to MP4 via ffmpeg: the engine advances "
        "along the near-maximal Rickness band of the simulated multiverse, "
        "tracing the Central Finite Curve step by step.",
    ),
}

# ---------------------------------------------------------------------------
# Section layout. Filenames are grouped sensibly; anything present in
# artifacts/ but not listed here falls through to an "Other artifacts" group.
# ---------------------------------------------------------------------------

_GOJO_GROUPS: Tuple[Group, ...] = (
    Group(
        "Lens 1 &mdash; Geometric series (Zeno)",
        "Verdict FRAGILE: the halving series converges and the attacker arrives.",
        ("gojo_series_convergence.png", "gojo_never_arrives.gif"),
    ),
    Group(
        "Lens 2 &mdash; Lebesgue measure",
        "Verdict FRAGILE: the barrier is a countable null set, m(Z) = 0.",
        ("gojo_cover_convergence.png",),
    ),
    Group(
        "Lens 3 &mdash; Riemannian conformal metric",
        "Verdict FORMIDABLE: the felt geodesic length to the barrier diverges.",
        (
            "gojo_metric_blowup.png",
            "gojo_geodesic_bundle.png",
            "gojo_length_divergence.png",
            "gojo_geodesic_3d.png",
        ),
    ),
    Group(
        "Lens 3 &mdash; Approach & rotating animations",
        "The approach never completes; the rotating views show the 3-D bending.",
        (
            "gojo_geodesic_approach.gif",
            "gojo_geodesic_approach.mp4",
            "gojo_geodesic_3d_rotating.gif",
            "gojo_geodesic_3d_rotating.mp4",
        ),
    ),
)

_MOBIUS_GROUPS: Tuple[Group, ...] = (
    Group(
        "Strip & curve",
        "The ruled M&ouml;bius strip and the traced zero set R<sup>&minus;1</sup>(0).",
        ("mobius_strip_curve.png",),
    ),
    Group(
        "K&middot;R heatmap",
        "The weighted field K<sub>Rick</sub> = K&middot;R with its zero contour.",
        ("mobius_krick_heatmap.png",),
    ),
    Group(
        "SCMS ridge",
        "The second Central Finite Curve reading: the SCMS / Eberly ridge.",
        ("mobius_ridge.png",),
    ),
    Group(
        "Rotating animations",
        "An orbiting view carrying both Central Finite Curve readings together.",
        ("mobius_rotating.gif", "mobius_rotating.mp4"),
    ),
)


# ---------------------------------------------------------------------------
# Scanning & classification
# ---------------------------------------------------------------------------

def scan_artifacts(artifacts_dir: str = _ARTIFACTS_DIR) -> List[str]:
    """Return a sorted list of embeddable artifact filenames in ``artifacts_dir``.

    Only files with a known image/video extension are returned; hidden files
    and unknown extensions are ignored so we never embed a broken reference.
    """
    if not os.path.isdir(artifacts_dir):
        return []
    names: List[str] = []
    for entry in os.listdir(artifacts_dir):
        if entry.startswith("."):
            continue
        full = os.path.join(artifacts_dir, entry)
        if not os.path.isfile(full):
            continue
        ext = os.path.splitext(entry)[1].lower()
        if ext in _IMAGE_EXTS or ext in _VIDEO_EXTS:
            names.append(entry)
    return sorted(names)


def _default_title(filename: str) -> str:
    """A readable fallback title derived from the filename."""
    stem = os.path.splitext(filename)[0]
    return stem.replace("_", " ").replace("-", " ").strip().title()


def _figure_for(filename: str) -> Figure:
    """Build a :class:`Figure` (title + caption) for ``filename``."""
    title, caption = _METADATA.get(
        filename,
        (
            _default_title(filename),
            "Auto-discovered artifact embedded so nothing is dropped. Add an "
            "entry to <code>build_gallery.py</code> for a curated caption.",
        ),
    )
    return Figure(filename=filename, title=title, caption=caption)


def _kind(filename: str) -> str:
    """Return ``"image"`` or ``"video"`` for a known extension, else ``"other"``."""
    ext = os.path.splitext(filename)[1].lower()
    if ext in _IMAGE_EXTS:
        return "image"
    if ext in _VIDEO_EXTS:
        return "video"
    return "other"


# ---------------------------------------------------------------------------
# HTML rendering
# ---------------------------------------------------------------------------

_CSS = """
:root {
  --bg: #0f1117;
  --panel: #171a23;
  --panel-2: #1e2230;
  --ink: #e8eaf0;
  --muted: #9aa3b2;
  --accent: #7cc4ff;
  --accent-2: #ffc16b;
  --line: #2a2f3d;
}
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body {
  background: var(--bg);
  color: var(--ink);
  font: 16px/1.6 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
}
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
code {
  background: var(--panel-2);
  border: 1px solid var(--line);
  border-radius: 4px;
  padding: 0 4px;
  font-family: "SF Mono", ui-monospace, Menlo, Consolas, monospace;
  font-size: 0.9em;
}
.wrap { max-width: 1100px; margin: 0 auto; padding: 32px 20px 64px; }
header.masthead {
  border-bottom: 1px solid var(--line);
  padding-bottom: 20px;
  margin-bottom: 8px;
}
header.masthead h1 { margin: 0 0 6px; font-size: 30px; letter-spacing: -0.02em; }
header.masthead p.lede { margin: 0 0 14px; color: var(--muted); max-width: 720px; }
nav.links a {
  display: inline-block;
  margin: 0 14px 6px 0;
  padding: 6px 12px;
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 999px;
  font-size: 14px;
}
section.gallery { margin-top: 40px; }
section.gallery > h2 {
  font-size: 24px;
  margin: 0 0 4px;
  padding-bottom: 8px;
  border-bottom: 2px solid var(--accent);
  display: inline-block;
}
section.gallery > p.section-sub { color: var(--muted); margin: 8px 0 24px; }
.group { margin: 28px 0; }
.group > h3 { font-size: 18px; margin: 0 0 2px; color: var(--accent-2); }
.group > p.group-blurb { color: var(--muted); margin: 0 0 16px; font-size: 14px; }
.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
}
figure.card {
  margin: 0;
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 12px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}
figure.card .media {
  background: #0b0d12;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 10px;
}
figure.card img, figure.card video {
  max-width: 100%;
  height: auto;
  border-radius: 6px;
  display: block;
}
figure.card figcaption { padding: 14px 16px 18px; }
figure.card figcaption h4 { margin: 0 0 6px; font-size: 16px; }
figure.card figcaption p { margin: 0; color: var(--muted); font-size: 14px; }
figure.card .fname {
  display: block;
  margin-top: 10px;
  font-family: "SF Mono", ui-monospace, Menlo, Consolas, monospace;
  font-size: 12px;
  color: #6f7889;
}
table.verdicts {
  width: 100%;
  border-collapse: collapse;
  margin: 8px 0 4px;
  font-size: 14px;
}
table.verdicts th, table.verdicts td {
  border: 1px solid var(--line);
  padding: 8px 10px;
  text-align: left;
  vertical-align: top;
}
table.verdicts th { background: var(--panel-2); }
.verdict-fragile { color: #ff9d9d; font-weight: 600; }
.verdict-formidable { color: #9dffb4; font-weight: 600; }
.verdict-falls { color: var(--accent-2); font-weight: 600; }
.callout {
  background: var(--panel);
  border: 1px solid var(--line);
  border-left: 3px solid var(--accent-2);
  border-radius: 8px;
  padding: 14px 18px;
  margin: 20px 0;
}
.callout h3 { margin: 0 0 8px; font-size: 16px; }
.callout ul { margin: 0; padding-left: 20px; color: var(--muted); }
.readings { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; }
.reading {
  background: var(--panel-2);
  border: 1px solid var(--line);
  border-radius: 8px;
  padding: 14px 16px;
}
.reading h4 { margin: 0 0 6px; font-size: 15px; color: var(--accent); }
.reading p { margin: 0; color: var(--muted); font-size: 14px; }
footer.foot {
  margin-top: 56px;
  padding-top: 20px;
  border-top: 1px solid var(--line);
  color: var(--muted);
  font-size: 13px;
}
footer.foot a { color: var(--accent); }
"""


def _render_figure(fig: Figure) -> str:
    """Render one figure card. PNG/GIF via <img>, MP4 via <video>."""
    src = "../artifacts/" + fig.filename
    kind = _kind(fig.filename)
    safe_src = html.escape(src, quote=True)
    safe_title = fig.title  # curated titles contain intentional entities
    safe_alt = html.escape(fig.title, quote=True)
    safe_fname = html.escape(fig.filename)
    if kind == "video":
        media = (
            f'<video src="{safe_src}" controls loop muted playsinline '
            f'preload="metadata" aria-label="{safe_alt}">'
            f"Your browser cannot play <code>{safe_fname}</code>.</video>"
        )
    else:
        media = f'<img src="{safe_src}" alt="{safe_alt}" loading="lazy">'
    return (
        '<figure class="card">'
        f'<div class="media">{media}</div>'
        "<figcaption>"
        f"<h4>{safe_title}</h4>"
        f"<p>{fig.caption}</p>"
        f'<span class="fname">{safe_fname}</span>'
        "</figcaption></figure>"
    )


def _render_group(group: Group, present: set, used: set) -> Optional[str]:
    """Render a group, skipping figures whose file is absent. ``None`` if empty."""
    cards: List[str] = []
    for filename in group.filenames:
        if filename in present:
            used.add(filename)
            cards.append(_render_figure(_figure_for(filename)))
    if not cards:
        return None
    return (
        '<div class="group">'
        f"<h3>{group.heading}</h3>"
        f'<p class="group-blurb">{group.blurb}</p>'
        f'<div class="grid">{"".join(cards)}</div>'
        "</div>"
    )


def _render_section(section: Section, present: set, used: set) -> str:
    """Render a whole section from its groups."""
    body = []
    for group in section.groups:
        rendered = _render_group(group, present, used)
        if rendered:
            body.append(rendered)
    return (
        f'<section class="gallery" id="{section.section_id}">'
        f"<h2>{section.title}</h2>"
        f'<p class="section-sub">{section.subtitle}</p>'
        f'{"".join(body)}'
        "</section>"
    )


# Any artifact whose filename starts with this prefix is grouped under the
# "Central Finite Curve (engine)" section instead of falling into
# "Other artifacts". The files are produced by the central_finite_curve package
# and may not exist yet at edit time -- the rule is applied dynamically at scan
# time, so a later regeneration places them here automatically.
_CFC_ENGINE_PREFIX = "central_finite_curve_"


def _render_cfc_engine_section(present: set, used: set) -> str:
    """Render the 'Central Finite Curve (engine)' section.

    Dynamically collects every not-yet-placed artifact whose filename starts
    with ``central_finite_curve_`` (the engine's ``*_projection.png`` and
    ``*_walk.gif`` / ``*_walk.mp4`` outputs), so newly regenerated engine
    artifacts land here rather than in 'Other artifacts'. Returns ``""`` when
    no such file is present yet.
    """
    matched = sorted(
        f for f in present if f not in used and f.startswith(_CFC_ENGINE_PREFIX)
    )
    if not matched:
        return ""
    cards = []
    for filename in matched:
        used.add(filename)
        cards.append(_render_figure(_figure_for(filename)))
    return (
        '<section class="gallery" id="cfc-engine">'
        "<h2>Central Finite Curve (engine)</h2>"
        '<p class="section-sub">The <code>central_finite_curve</code> engine&rsquo;s '
        "Rickness ridge / near-maximal band traced over a simulated multiverse.</p>"
        f'<div class="group"><div class="grid">{"".join(cards)}</div></div>'
        "</section>"
    )


def _render_other(present: set, used: set) -> str:
    """Render an 'Other artifacts' section for anything not already placed."""
    leftovers = sorted(f for f in present if f not in used)
    if not leftovers:
        return ""
    cards = "".join(_render_figure(_figure_for(f)) for f in leftovers)
    return (
        '<section class="gallery" id="other">'
        "<h2>Other artifacts</h2>"
        '<p class="section-sub">Auto-discovered files that are not part of a '
        "known group &mdash; embedded so nothing is dropped.</p>"
        f'<div class="group"><div class="grid">{cards}</div></div>'
        "</section>"
    )


_VERDICT_TABLE = """
<table class="verdicts">
  <thead>
    <tr><th>Lens</th><th>Model</th><th>Verdict</th><th>Why</th></tr>
  </thead>
  <tbody>
    <tr>
      <td>1</td><td>Geometric series / Zeno</td>
      <td class="verdict-fragile">Fragile</td>
      <td><code>S<sub>n</sub> = 1 &minus; (1/2)<sup>n</sup> &rarr; 1</code> exactly; arrival time is finite. The attacker arrives.</td>
    </tr>
    <tr>
      <td>2</td><td>Lebesgue measure</td>
      <td class="verdict-fragile">Fragile</td>
      <td>The cover of <code>Z = {1 &minus; 1/2<sup>n</sup>}</code> telescopes to <code>&epsilon;</code>; infimum <code>&rarr; 0</code>, so <code>m(Z) = 0</code> (null set).</td>
    </tr>
    <tr>
      <td>3</td><td>Riemannian conformal geometry</td>
      <td class="verdict-formidable">Formidable</td>
      <td>The felt geodesic <code>&int; &Omega; dx</code> to the barrier is an improper integral that <em>diverges</em> (<code>= &infin;</code>).</td>
    </tr>
    <tr>
      <td>4</td><td>Topology / World-Cutting Slash</td>
      <td class="verdict-falls">Falls</td>
      <td>Severing the continuity of <code>&Omega;</code> at a point leaves the metric undefined; the domain splits into exactly 2 components.</td>
    </tr>
  </tbody>
</table>
"""

_CFC_READINGS = """
<div class="readings">
  <div class="reading">
    <h4>Reading 1 &mdash; the zero set R<sup>&minus;1</sup>(0)</h4>
    <p>Because the M&ouml;bius strip is ruled, <code>K &lt; 0</code> strictly, so
    <code>K<sub>Rick</sub> = K&middot;R = 0 &hArr; R = 0</code>. Solving
    <code>R(u,v) = 0</code> gives the Central Finite Curve exactly as a 1-D locus
    &mdash; the red curve in the strip and heatmap figures.</p>
  </div>
  <div class="reading">
    <h4>Reading 2 &mdash; the SCMS / Eberly ridge</h4>
    <p>An independent formalization follows the crest of the Rickness field as a
    principal-curvature (height) ridge via Subspace-Constrained Mean Shift. It
    traces the same feature from different mathematics &mdash; the orange ridge in
    the ridge and rotating figures.</p>
  </div>
</div>
"""

_CAVEATS = """
<div class="callout">
  <h3>Honest caveats</h3>
  <ul>
    <li>The M&ouml;bius strip is a <strong>ruled surface</strong>, so its Gaussian
    curvature is strictly negative (<code>K &lt; 0</code>) on the interior &mdash;
    the weighting by <code>K</code> is what makes <code>K<sub>Rick</sub></code>
    share its zero set with <code>R</code>, nothing more.</li>
    <li>Gojo&rsquo;s Infinity is only <em>fragile at true infinity</em>: every
    <em>finite</em> Zeno residual <code>(1/2)<sup>n</sup> &gt; 0</code> is strictly
    positive, and the FORMIDABLE reading depends on an <em>improper</em> integral
    that only diverges in the limit.</li>
    <li>Applying real analysis to a fictional universe has limits: &lsquo;cursed
    energy&rsquo; and authorial intent are <strong>not governed by real
    analysis</strong>. These models illuminate the idea of Infinity &mdash; they do
    not govern it.</li>
  </ul>
</div>
"""


def _render_attribution() -> str:
    """The essay attribution block (summary/attribution only, no verbatim text)."""
    return (
        '<div class="callout" id="attribution">'
        "<h3>Attribution</h3>"
        "<ul>"
        "<li>The mathematical framing showcased here is <em>after</em> Achmad "
        "Roykhan Sabiq, &ldquo;Mathematics Behind Jujutsu Kaisen: Gojo Satoru&rsquo;s "
        "Infinity&rdquo;, Oxford University Mathematics Essay Competition 2026. "
        f'Original PDF: <a href="{html.escape(_ESSAY_PDF_URL, quote=True)}">'
        "tomrocksmaths.com</a>.</li>"
        "<li>This gallery is an original summary/companion &mdash; captions are "
        "written in our own words and do <strong>not</strong> reproduce the "
        "essay&rsquo;s prose. See "
        '<a href="../docs/essay-source.md">docs/essay-source.md</a> for the '
        "section-by-section companion and source mapping.</li>"
        "<li>Jujutsu Kaisen and its characters are &copy; Gege Akutami / Shueisha; "
        "Rick &amp; Morty is &copy; its respective rights holders.</li>"
        "</ul></div>"
    )


def build_html(artifacts_dir: str = _ARTIFACTS_DIR) -> Tuple[str, int]:
    """Build the full HTML document. Return ``(html_text, num_embedded)``."""
    present = set(scan_artifacts(artifacts_dir))
    used: set = set()

    gojo = Section(
        "gojo",
        "Gojo&rsquo;s Infinity",
        "Four independent mathematical lenses interrogate the same barrier and "
        "reach four different verdicts &mdash; the disagreement is the point.",
        _GOJO_GROUPS,
    )
    mobius = Section(
        "mobius",
        "M&ouml;bius-Rickness &mdash; the Central Finite Curve",
        "The Rick &amp; Morty &lsquo;Central Finite Curve&rsquo; realised as a real "
        "zero set <code>R<sup>&minus;1</sup>(0)</code> on a M&ouml;bius strip of "
        "strictly negative Gaussian curvature.",
        _MOBIUS_GROUPS,
    )

    sections_html = [
        _render_section(gojo, present, used),
        _VERDICT_TABLE_WRAPPER(),
        _CAVEATS_ANCHOR_FOR_GOJO(),
        _render_section(mobius, present, used),
        _CFC_SECTION(),
        _render_cfc_engine_section(present, used),
        _render_other(present, used),
    ]

    body = "".join(s for s in sections_html if s)
    num_embedded = len(used) + len(sorted(f for f in present if f not in used))

    doc = (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        "<title>infinity-lab &mdash; showcase gallery</title>\n"
        f"<style>{_CSS}</style>\n"
        "</head>\n<body>\n"
        '<div class="wrap">\n'
        + _render_masthead()
        + body
        + _render_attribution()
        + _render_footer(num_embedded)
        + "\n</div>\n</body>\n</html>\n"
    )
    return doc, num_embedded


def _render_masthead() -> str:
    """The page header with links back to each README and the essay companion."""
    return (
        '<header class="masthead">'
        "<h1>infinity-lab &mdash; showcase gallery</h1>"
        '<p class="lede">Rendered figures and animations from two mathematics '
        "projects: Gojo Satoru&rsquo;s <em>Infinity</em> through four lenses, and "
        "the <em>Central Finite Curve</em> as a real zero set on a M&ouml;bius "
        "strip. Everything below is self-contained and opens offline.</p>"
        '<nav class="links">'
        '<a href="../README.md">Monorepo README</a>'
        '<a href="../packages/gojo_infinity/README.md">gojo_infinity README</a>'
        '<a href="../packages/mobius_rickness/README.md">mobius_rickness README</a>'
        '<a href="../docs/essay-source.md">Essay companion</a>'
        '<a href="#attribution">Attribution</a>'
        "</nav></header>"
    )


def _VERDICT_TABLE_WRAPPER() -> str:
    """The four-lens verdict table wrapped in its own titled block."""
    return (
        '<section class="gallery" id="verdicts">'
        "<h2>The four-lens verdict</h2>"
        '<p class="section-sub">Fragile / Fragile / Formidable / Falls &mdash; the '
        "same barrier judged by four different mathematics.</p>"
        f"{_VERDICT_TABLE}"
        "</section>"
    )


def _CAVEATS_ANCHOR_FOR_GOJO() -> str:
    """The caveats callout (shared by both projects)."""
    return _CAVEATS


def _CFC_SECTION() -> str:
    """The two Central Finite Curve readings block."""
    return (
        '<section class="gallery" id="cfc-readings">'
        "<h2>Two Central Finite Curve readings</h2>"
        '<p class="section-sub">The same feature located two independent ways.</p>'
        f"{_CFC_READINGS}"
        "</section>"
    )


def _render_footer(num_embedded: int) -> str:
    """The page footer."""
    return (
        '<footer class="foot">'
        f"<p>{num_embedded} artifact(s) embedded &mdash; generated by "
        "<code>gallery/build_gallery.py</code> (standard library only, no external "
        "network dependencies). Re-run it to pick up newly added artifacts.</p>"
        "</footer>"
    )


def main() -> int:
    """Generate ``gallery/index.html`` and report the embedded artifact count."""
    doc, num_embedded = build_html()
    with open(_OUTPUT_HTML, "w", encoding="utf-8") as fh:
        fh.write(doc)
    rel = os.path.relpath(_OUTPUT_HTML, os.getcwd())
    print(f"Wrote {rel}")
    print(f"Embedded {num_embedded} artifact(s) from {_ARTIFACTS_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
