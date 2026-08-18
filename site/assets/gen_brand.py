#!/usr/bin/env python3
"""
Generate raster brand assets:
  - favicon-32.png (32x32)
  - apple-touch-icon.png (180x180)
  - og-card.png (1200x630 social share card)

Run: /Users/arhansubasi/mad-man-projects/infinity-lab/.venv/bin/python gen_brand.py
"""
import os, io
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.patches import Circle, Arc, FancyBboxPatch
from PIL import Image

OUT = os.path.dirname(os.path.abspath(__file__))

CREAM  = '#f6f2e9'
INK    = '#16150f'
INK2   = '#3d3b32'
MUTED  = '#6b6760'
ACCENT = '#d1341a'
RULE   = '#c8c3b5'


def lemniscate(ax, cx, cy, scale, stroke, alpha=0.9):
    """Draw a lemniscate of Bernoulli centred at (cx,cy)."""
    t = np.linspace(0, 2*np.pi, 600)
    denom = 1 + np.sin(t)**2
    lx = scale * np.cos(t) / denom + cx
    ly = scale * np.sin(t)*np.cos(t) / denom + cy
    ax.plot(lx, ly, color=INK, lw=stroke, alpha=alpha,
            solid_capstyle='round', solid_joinstyle='round')
    # Accent crossover dot
    ax.plot(cx, cy, 'o', color=ACCENT, markersize=stroke*1.4, alpha=0.95)


def make_favicon(size: int, out_path: str):
    dpi = 100
    sz_in = size / dpi
    fig, ax = plt.subplots(figsize=(sz_in, sz_in), dpi=dpi)
    fig.patch.set_facecolor(CREAM)
    ax.set_facecolor(CREAM)
    ax.set_xlim(0, size); ax.set_ylim(0, size)
    ax.set_aspect('equal'); ax.axis('off')
    # Rounded rect feel via background
    margin = size * 0.06
    cx, cy = size/2, size/2
    sc = size * 0.28
    stroke = size * 0.045
    lemniscate(ax, cx, cy, sc, stroke)
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0, dpi=dpi)
    plt.close(fig)
    buf.seek(0)
    img = Image.open(buf).convert('RGBA')
    img = img.resize((size, size), Image.LANCZOS)
    img.save(out_path, 'PNG', optimize=True)
    print(f'  ok  {out_path}  ({os.path.getsize(out_path)//1024}KB)')


def make_og_card(out_path: str):
    """1200x630 social share card — ink on cream."""
    W, H = 1200, 630
    dpi = 100
    fig, ax = plt.subplots(figsize=(W/dpi, H/dpi), dpi=dpi)
    fig.patch.set_facecolor(CREAM)
    ax.set_facecolor(CREAM)
    ax.set_xlim(0, W); ax.set_ylim(0, H)
    ax.axis('off')
    ax.set_aspect('equal')

    # ── Hairline border ──────────────────────────────────────────────────
    border = FancyBboxPatch((18, 18), W-36, H-36, boxstyle='square,pad=0',
                            linewidth=0.8, edgecolor=RULE, facecolor='none')
    ax.add_patch(border)

    # ── Left column: mathematical motif (Möbius + geodesics) ────────────
    mc_x, mc_y, mc_r = 310, H/2, 195
    # Geodesic curves converging to center
    n_geo = 22
    for i in range(n_geo):
        theta = i / n_geo * 2 * np.pi
        sx = mc_x + mc_r * np.cos(theta)
        sy = mc_y + mc_r * np.sin(theta)
        t = np.linspace(0, 1, 80)
        cx_b = sx*0.28 + mc_x*0.72
        cy_b = sy*0.28 + mc_y*0.72
        xs = (1-t)**2*sx + 2*(1-t)*t*cx_b + t**2*mc_x
        ys = (1-t)**2*sy + 2*(1-t)*t*cy_b + t**2*mc_y
        alpha = 0.12 + 0.18*abs(np.cos(theta))
        ax.plot(xs, ys, color=INK, lw=0.7, alpha=alpha,
                solid_capstyle='round')
    # Lemniscate
    t = np.linspace(0, 2*np.pi, 500)
    sc_lem = 95
    denom = 1 + np.sin(t)**2
    lx = sc_lem * np.cos(t) / denom + mc_x
    ly = sc_lem * np.sin(t)*np.cos(t) / denom + mc_y
    ax.plot(lx, ly, color=INK, lw=1.6, alpha=0.60, solid_capstyle='round')
    # Singularity
    ax.plot(mc_x, mc_y, 'o', color=ACCENT, markersize=7, alpha=0.90)
    # Vertical divider rule
    ax.plot([590, 590], [50, H-50], color=RULE, lw=0.8, alpha=0.8)

    # ── Right column: wordmark + tagline ────────────────────────────────
    # "awesome-" prefix (small, tracked)
    ax.text(630, H - 110, 'awesome-', fontsize=18, fontstyle='italic',
            color=MUTED, alpha=0.8,
            fontfamily='Georgia, serif')
    # "mad·projects" large display
    ax.text(630, H - 175, 'mad', fontsize=68, fontweight='bold',
            color=INK, fontfamily='Georgia, serif',
            verticalalignment='baseline')
    ax.text(775, H - 175, '·', fontsize=68, color=ACCENT,
            fontfamily='Georgia, serif', verticalalignment='baseline')
    ax.text(797, H - 175, 'projects', fontsize=42,
            color=INK2, fontfamily='ui-monospace, monospace',
            verticalalignment='baseline')

    # Thin rule under wordmark
    ax.plot([630, W - 60], [H - 195, H - 195], color=RULE, lw=0.8, alpha=0.8)

    # Tagline
    tagline = ('An awesome list of mad math × anime projects\n'
               'turned into real, tested code.')
    ax.text(630, H - 260, tagline, fontsize=19, color=INK2,
            fontfamily='Georgia, serif', linespacing=1.55,
            verticalalignment='top')

    # Stats row
    for i, (val, lbl) in enumerate([('22', 'projects'), ('4', 'languages'),
                                     ('3', 'clusters'), ('600+', 'tests')]):
        x = 630 + i*130
        ax.text(x, 200, val, fontsize=28, fontweight='bold', color=INK,
                fontfamily='Georgia, serif', ha='left')
        ax.text(x, 170, lbl, fontsize=11, color=MUTED,
                fontfamily='ui-monospace, monospace', ha='left')

    # Thin rule above stats
    ax.plot([630, W - 60], [230, 230], color=RULE, lw=0.5, alpha=0.7)

    # URL
    ax.text(W - 60, 50, 'mad-projects.com', fontsize=12, color=MUTED,
            fontfamily='ui-monospace, monospace', ha='right', alpha=0.7)

    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0, dpi=dpi)
    plt.close(fig)
    buf.seek(0)
    img = Image.open(buf).convert('RGB')
    # Crop/resize to exactly 1200×630
    img = img.resize((W, H), Image.LANCZOS)
    img.save(out_path, 'PNG', optimize=True, compress_level=7)
    size = os.path.getsize(out_path)
    if size > 290_000:
        img.save(out_path, 'PNG', optimize=True, compress_level=9)
    print(f'  ok  {out_path}  ({os.path.getsize(out_path)//1024}KB)')


if __name__ == '__main__':
    print('Generating brand assets...')
    make_favicon(32,  os.path.join(OUT, 'favicon-32.png'))
    make_favicon(180, os.path.join(OUT, 'apple-touch-icon.png'))
    make_og_card(os.path.join(OUT, 'og-card.png'))
    print('Done.')
