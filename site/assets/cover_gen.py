#!/usr/bin/env python3
"""
Generate per-project cover images for awesome-mad-projects.
Ink-on-cream palette: mathematical plate series.
Run: /Users/arhansubasi/mad-man-projects/infinity-lab/.venv/bin/python cover_gen.py
Output: site/assets/covers/<slug>.png  (22 files, each < 300 KB)
"""
import hashlib, os, sys, io
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.patches import Arc, Circle, FancyBboxPatch, FancyArrowPatch
from matplotlib.collections import LineCollection
from PIL import Image

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'covers')
os.makedirs(OUTPUT_DIR, exist_ok=True)

FIG_W, FIG_H = 7.0, 4.5   # inches → 700 × 450 px at DPI=100
DPI = 100
MAX_BYTES = 290_000

# ── Ink-on-cream palette ──────────────────────────────────────────────────────
CREAM   = '#f6f2e9'
INK     = '#16150f'
INK_MID = '#3d3b32'
MUTED   = '#6b6760'
ACCENT  = '#d1341a'        # single vermilion accent
RULE    = '#c8c3b5'        # hairline rule colour
PALE    = '#ede9de'        # slightly darker cream for fills


def slug_rng(slug: str) -> np.random.Generator:
    seed = int(hashlib.md5(slug.encode()).hexdigest()[:8], 16) % (2 ** 31)
    return np.random.default_rng(seed)


def make_fig():
    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H), dpi=DPI)
    fig.patch.set_facecolor(CREAM)
    ax.set_facecolor(CREAM)
    ax.set_xlim(-1, 1)
    ax.set_ylim(-1, 1)
    ax.set_aspect('auto')
    ax.axis('off')
    # Thin frame
    for spine in ax.spines.values():
        spine.set_visible(False)
    # Draw hairline frame manually
    for (x0, y0, x1, y1) in [(-0.96,-0.93,-0.96,0.93),(-0.96,0.93,0.96,0.93),
                               (0.96,0.93,0.96,-0.93),(0.96,-0.93,-0.96,-0.93)]:
        ax.plot([x0,x1],[y0,y1], color=RULE, lw=0.5, transform=ax.transData)
    return fig, ax


def label(ax, text: str, color: str = INK_MID, y: float = -0.86):
    """Small monospace label at the bottom."""
    ax.text(0.94, y, text, ha='right', va='bottom', fontsize=7,
            fontfamily='monospace', color=color, transform=ax.transData,
            alpha=0.7)


def ink(ax, xs, ys, lw=1.2, alpha=0.85, color=INK, **kw):
    ax.plot(xs, ys, color=color, lw=lw, alpha=alpha,
            solid_capstyle='round', solid_joinstyle='round', **kw)


def save(fig, slug: str) -> str:
    path = os.path.join(OUTPUT_DIR, f'{slug}.png')
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.05, dpi=DPI)
    plt.close(fig)
    buf.seek(0)
    img = Image.open(buf).convert('RGB')
    img.save(path, 'PNG', optimize=True, compress_level=7)
    size = os.path.getsize(path)
    if size > MAX_BYTES:
        w, h = img.size
        factor = (MAX_BYTES / size) ** 0.5
        img = img.resize((int(w * factor), int(h * factor)), Image.LANCZOS)
        img.save(path, 'PNG', optimize=True, compress_level=9)
    return path


# ═══════════════════════════════════════════════════════════════════════════════
# Per-project cover functions — ink on cream, mathematical motifs
# ═══════════════════════════════════════════════════════════════════════════════

def cover_gojo_infinity(slug):
    """Geodesic curves converging to a central singularity. Lemniscate of Bernoulli."""
    fig, ax = make_fig()
    n = 18
    for i in range(n):
        theta = i / n * 2 * np.pi
        r = 0.80
        sx, sy = r * np.cos(theta), r * np.sin(theta)
        t = np.linspace(0, 1, 100)
        cx, cy = sx * 0.28, sy * 0.28
        xs = (1-t)**2*sx + 2*(1-t)*t*cx + t**2*0
        ys = (1-t)**2*sy + 2*(1-t)*t*cy + t**2*0
        alpha = 0.18 + 0.32 * abs(np.cos(theta))
        lw = 0.55 + 0.3 * abs(np.sin(theta + 0.5))
        ink(ax, xs, ys, lw=lw, alpha=alpha)
    # Lemniscate (∞) in accent
    t = np.linspace(0, 2*np.pi, 400)
    scale = 0.30
    lx = scale * np.cos(t) / (1 + np.sin(t)**2)
    ly = scale * np.sin(t)*np.cos(t) / (1 + np.sin(t)**2)
    ink(ax, lx, ly, lw=1.4, alpha=0.55, color=ACCENT)
    # Singularity point
    ax.plot(0, 0, 'o', color=INK, markersize=4, alpha=0.9)
    ax.text(0, 0.06, 'ds² → ∞', ha='center', fontsize=8, fontfamily='monospace',
            color=INK_MID, alpha=0.55)
    label(ax, 'gojo_infinity')
    return save(fig, slug)


def cover_mobius_rickness(slug):
    """Möbius strip cross-section lines — the ruled surface with K < 0."""
    fig, ax = make_fig()
    u = np.linspace(0, 2*np.pi, 500)
    v_vals = np.linspace(-0.30, 0.30, 9)
    for vi, v in enumerate(v_vals):
        x = (0.52 + v*np.cos(u/2))*np.cos(u)
        y = (0.52 + v*np.cos(u/2))*np.sin(u)*0.50
        z = v*np.sin(u/2)
        alpha = 0.20 + 0.55*(abs(v)/0.30)
        lw = 0.5 if abs(v) > 0.01 else 1.6
        col = ACCENT if abs(v) < 0.01 else INK
        ink(ax, x, y + z*0.28, lw=lw, alpha=alpha, color=col)
    ax.text(0, -0.06, 'K < 0', ha='center', fontsize=9, fontfamily='monospace',
            color=INK_MID, alpha=0.45)
    label(ax, 'mobius_rickness')
    return save(fig, slug)


def cover_central_finite_curve(slug):
    """Bounded arc of realities — infinite but contained."""
    fig, ax = make_fig()
    rng = slug_rng(slug)
    t = np.linspace(-np.pi*0.82, np.pi*0.82, 400)
    ax_x = np.sin(t)*0.80
    ax_y = np.cos(t)*0.32 - 0.08
    ink(ax, ax_x, ax_y, lw=1.4, alpha=0.75)
    # Reality dots
    n = 55
    t_pts = rng.uniform(-np.pi*0.78, np.pi*0.78, n)
    xs = np.sin(t_pts)*0.80 + rng.normal(0, 0.025, n)
    ys = np.cos(t_pts)*0.32 - 0.08 + rng.normal(0, 0.025, n)
    sizes = rng.uniform(4, 18, n)
    ax.scatter(xs, ys, s=sizes*0.8, color=INK, alpha=0.45, linewidths=0)
    # Accent endpoint caps
    for sign in [-1, 1]:
        tx = np.sin(sign*np.pi*0.82)*0.80
        ty = np.cos(sign*np.pi*0.82)*0.32 - 0.08
        ax.plot(tx, ty, 'o', color=ACCENT, markersize=5, alpha=0.85)
    ax.text(0, 0.38, '∀ Rick : smartest', ha='center', fontsize=7.5,
            fontfamily='monospace', color=MUTED, alpha=0.6)
    label(ax, 'central_finite_curve')
    return save(fig, slug)


def cover_calabi_yau_latent(slug):
    """Lattice grid with compactified circles at each node."""
    fig, ax = make_fig()
    rng = slug_rng(slug)
    cols = np.linspace(-0.80, 0.80, 7)
    rows = np.linspace(-0.62, 0.62, 5)
    for xi in cols:
        ink(ax, [xi, xi], [-0.65, 0.65], lw=0.3, alpha=0.18)
    for yi in rows:
        ink(ax, [-0.83, 0.83], [yi, yi], lw=0.3, alpha=0.18)
    theta = np.linspace(0, 2*np.pi, 60)
    for xi in cols:
        for yi in rows:
            r = 0.042 + rng.uniform(0, 0.012)
            ax.plot(xi + r*np.cos(theta), yi + r*np.sin(theta),
                    color=ACCENT, lw=0.7, alpha=0.55)
            ax.plot(xi + r*1.6*np.cos(theta), yi + r*1.6*np.sin(theta),
                    color=INK, lw=0.3, alpha=0.20)
    ax.text(0, -0.88, 'ℝⁿ × T^k', ha='center', fontsize=9, fontfamily='monospace',
            color=INK_MID, alpha=0.45)
    label(ax, 'calabi_yau_latent')
    return save(fig, slug)


def cover_domain_expansion(slug):
    """Concentric constraint rings expanding outward."""
    fig, ax = make_fig()
    theta = np.linspace(0, 2*np.pi, 300)
    radii = np.linspace(0.10, 0.85, 8)
    for i, r in enumerate(radii):
        alpha = 0.55 - i*0.04
        lw = 1.1 - i*0.07
        col = ACCENT if i == 0 else INK
        ax.plot(r*np.cos(theta), r*np.sin(theta), color=col, lw=lw, alpha=alpha)
    # Radial spokes
    for j in range(12):
        angle = j/12*2*np.pi
        ink(ax, [0, 0.85*np.cos(angle)], [0, 0.85*np.sin(angle)],
            lw=0.3, alpha=0.14)
    ax.plot(0, 0, 'o', color=ACCENT, markersize=4, alpha=0.9)
    ax.text(0, -0.94, '∂Ω = constraint boundary', ha='center', fontsize=7,
            fontfamily='monospace', color=MUTED, alpha=0.55)
    label(ax, 'domain_expansion')
    return save(fig, slug)


def cover_divergence_meter(slug):
    """Branching worldlines — Steins;Gate divergence tree."""
    fig, ax = make_fig()
    rng = slug_rng(slug)
    # Trunk
    ink(ax, [0, 0], [0.82, -0.15], lw=1.6, alpha=0.8)
    commit_y = np.linspace(0.70, -0.05, 7)
    ax.scatter(np.zeros(7), commit_y, s=14, color=INK, alpha=0.75, linewidths=0)
    # Branches
    for i, y in enumerate(commit_y):
        if i in [1, 3, 5]:
            sign = 1 if i == 1 else (-1 if i == 3 else 1)
            bx = sign*(0.28 + rng.uniform(0, 0.12))
            by = y - rng.uniform(0.12, 0.28)
            t = np.linspace(0, 1, 60)
            xs = t*bx
            ys = y + (by - y)*t - 0.06*np.sin(t*np.pi)
            col = ACCENT if sign > 0 else INK_MID
            ink(ax, xs, ys, lw=0.9, alpha=0.6, color=col)
            ax.scatter([bx], [by], s=10, color=col, alpha=0.7, linewidths=0)
    ax.text(0.38, 0.82, '0.337187', ha='center', fontsize=9.5,
            fontfamily='monospace', color=INK_MID, alpha=0.60)
    label(ax, 'divergence-meter')
    return save(fig, slug)


def cover_padic_embeddings(slug):
    """p-adic tree — ultrametric branching (base 3)."""
    fig, ax = make_fig()
    p = 3
    def draw_tree(x, y, dy, depth, max_depth):
        if depth > max_depth: return
        alpha = 0.80 - depth*0.15
        lw = 1.4 - depth*0.3
        col = ACCENT if depth == 0 else INK
        for i in range(p):
            nx = x + (i - (p-1)/2)*dy*0.95
            ny = y - dy
            ink(ax, [x, nx], [y, ny], lw=lw, alpha=alpha, color=col)
            if depth == max_depth:
                ax.plot(nx, ny, 'o', color=INK, markersize=3, alpha=0.6)
            draw_tree(nx, ny, dy/p, depth+1, max_depth)
    draw_tree(0, 0.80, 0.45, 0, 3)
    ax.text(0, -0.88, '|x−y|_p = p^{−v_p(x−y)}', ha='center', fontsize=7.5,
            fontfamily='monospace', color=MUTED, alpha=0.55)
    label(ax, 'padic-embeddings')
    return save(fig, slug)


def cover_madoka_entropy(slug):
    """Archimedean entropy spiral with particle traces."""
    fig, ax = make_fig()
    rng = slug_rng(slug)
    t = np.linspace(0, 5.5*np.pi, 700)
    r = t/(5.5*np.pi)*0.85
    xs = r*np.cos(t)
    ys = r*np.sin(t)*0.82
    # Colour gradient: ink at center → accent at edge
    from matplotlib.collections import LineCollection
    pts = np.array([xs, ys]).T.reshape(-1, 1, 2)
    segs = np.concatenate([pts[:-1], pts[1:]], axis=1)
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list('ink2acc', [INK, ACCENT])
    lc = LineCollection(segs, cmap=cmap, linewidth=1.1, alpha=0.75)
    lc.set_array(np.linspace(0, 1, len(segs)))
    ax.add_collection(lc)
    ax.plot(0, 0, 'o', color=ACCENT, markersize=4, alpha=0.85)
    ax.text(0, -0.92, 'ΔS ≥ 0', ha='center', fontsize=9, fontfamily='monospace',
            color=MUTED, alpha=0.55)
    label(ax, 'madoka-entropy')
    return save(fig, slug)


def cover_surreal_priority(slug):
    """Surreal number {L|R} tree with nested brace notation."""
    fig, ax = make_fig()
    def draw_surreal(x, y, level, span):
        if level > 3: return
        alpha = 0.9 - level*0.18
        lw = 1.5 - level*0.3
        labels = ['{|}', '{0|}', '{|0}', '{0|1}', '{-1|1}', '{1|2}']
        lbl = labels[min(level*2, 5)]
        col = ACCENT if level == 0 else INK
        ax.text(x, y, lbl, ha='center', va='center', fontsize=9-level*1.5,
                color=col, alpha=alpha, fontfamily='monospace')
        if level < 3:
            dx = span/2
            for sign in [-1, 1]:
                nx, ny = x + sign*dx, y - 0.36
                ink(ax, [x, nx], [y-0.08, ny+0.09], lw=lw*0.55, alpha=alpha*0.5)
                draw_surreal(nx, ny, level+1, span/2)
    draw_surreal(0, 0.78, 0, 0.82)
    label(ax, 'surreal-priority')
    return save(fig, slug)


def cover_statmech_scheduler(slug):
    """Phase space scatter — tasks as energy particles, MB curve."""
    fig, ax = make_fig()
    rng = slug_rng(slug)
    # Light grid
    for v in np.linspace(-0.80, 0.80, 9):
        ink(ax, [-0.83, 0.83], [v, v], lw=0.2, alpha=0.14)
        ink(ax, [v, v], [-0.83, 0.83], lw=0.2, alpha=0.14)
    n = 90
    px = rng.uniform(-0.82, 0.82, n)
    py = rng.uniform(-0.82, 0.82, n)
    energy = np.sqrt(px**2 + py**2)
    en = energy/energy.max()
    for i in range(n):
        col = ACCENT if en[i] > 0.7 else (INK_MID if en[i] > 0.35 else INK)
        ax.scatter(px[i], py[i], s=12, color=col, alpha=0.35+0.45*en[i], linewidths=0)
    # MB curve
    xe = np.linspace(0, 1.3, 80)
    ye_raw = xe**2*np.exp(-xe**2*2)
    ye = ye_raw/ye_raw.max()*0.55 - 0.83
    ink(ax, xe - 0.65, ye, lw=1.3, alpha=0.7, color=ACCENT)
    label(ax, 'statmech-scheduler')
    return save(fig, slug)


def cover_hairy_ball_router(slug):
    """Sphere S² with tangent vector field — the theorem in ink."""
    fig, ax = make_fig()
    rng = slug_rng(slug)
    theta = np.linspace(0, 2*np.pi, 200)
    R = 0.68
    ink(ax, R*np.cos(theta), R*np.sin(theta), lw=1.4, alpha=0.7)
    # Latitude lines
    for lat in np.linspace(-0.55, 0.55, 6):
        r_lat = np.sqrt(max(0, R**2 - lat**2))
        ax.plot(r_lat*np.cos(theta), lat + np.zeros_like(theta),
                color=INK, lw=0.3, alpha=0.18)
    # Meridian
    for lon in np.linspace(0, np.pi, 5):
        mx = R*np.sin(theta)*np.cos(lon)
        my = R*np.cos(theta)
        ink(ax, mx, my, lw=0.3, alpha=0.18)
    # Tangent arrows (vortex)
    n_arr = 28
    for i in range(n_arr):
        phi = rng.uniform(0, 2*np.pi)
        lat2 = rng.uniform(0.18, np.pi - 0.18)
        x = 0.60*np.sin(lat2)*np.cos(phi)
        y = 0.60*np.cos(lat2)
        vx = -np.sin(phi)*0.10
        vy = rng.uniform(-0.02, 0.02)
        ax.annotate('', xy=(x+vx, y+vy), xytext=(x, y),
                    arrowprops=dict(arrowstyle='->', color=ACCENT, lw=0.8, mutation_scale=7))
    label(ax, 'hairy-ball-router')
    return save(fig, slug)


def cover_banach_tarski(slug):
    """One sphere → two: free group F₂ decomposition."""
    fig, ax = make_fig()
    theta = np.linspace(0, 2*np.pi, 300)
    # Left sphere
    ink(ax, -0.38 + 0.36*np.cos(theta), 0.12 + 0.36*np.sin(theta), lw=1.3, alpha=0.7)
    ink(ax, -0.38 + 0.36*np.cos(theta), 0.12 + 0.36*np.sin(theta)*0.38,
        lw=0.5, alpha=0.25)  # equator ellipse
    # Right sphere
    ink(ax, 0.38 + 0.36*np.cos(theta), 0.12 + 0.36*np.sin(theta), lw=1.3, alpha=0.7)
    ink(ax, 0.38 + 0.36*np.cos(theta), 0.12 + 0.36*np.sin(theta)*0.38,
        lw=0.5, alpha=0.25)
    # Arrow
    ax.annotate('', xy=(0.12, 0.12), xytext=(-0.12, 0.12),
                arrowprops=dict(arrowstyle='->', color=ACCENT, lw=1.4,
                                connectionstyle='arc3,rad=0.3', mutation_scale=13))
    ax.text(0, 0.58, '≅', ha='center', fontsize=16, color=INK_MID, alpha=0.55)
    # Group elements
    for i, lbl in enumerate(['a', 'b', 'a⁻¹', 'b⁻¹']):
        ax.text(-0.62 + (i%2)*1.24, -0.45 + (i//2)*0.22, lbl, ha='center',
                fontsize=8.5, fontfamily='monospace', color=MUTED, alpha=0.50)
    label(ax, 'banach-tarski-dup')
    return save(fig, slug)


def cover_zeno_protocol(slug):
    """Zeno halving segments — dichotomy paradox."""
    fig, ax = make_fig()
    ink(ax, [-0.86, 0.86], [0.05, 0.05], lw=1.5, alpha=0.70)
    n_seg = 9
    x = -0.86
    end = 0.86
    for i in range(n_seg):
        mid = x + (end - x)/2
        ink(ax, [mid, mid], [-0.04, 0.14], lw=0.8, alpha=0.65,
            color=ACCENT if i == 0 else INK)
        frac = f'1/{2**(i+1)}'
        ax.text(mid, 0.20 + i*0.055, frac, ha='center', fontsize=max(4.5, 8.5-i),
                fontfamily='monospace', color=INK if i < 3 else MUTED,
                alpha=max(0.25, 0.85 - i*0.09))
        x = mid
    # Goal
    ax.plot(end, 0.05, 'o', color=ACCENT, markersize=5, alpha=0.85)
    ax.text(end, -0.14, 'goal', ha='center', fontsize=7.5,
            fontfamily='monospace', color=MUTED, alpha=0.65)
    ax.text(-0.86, -0.14, 'start', ha='center', fontsize=7.5,
            fontfamily='monospace', color=MUTED, alpha=0.65)
    label(ax, 'zeno-protocol')
    return save(fig, slug)


def cover_infinite_hotel(slug):
    """Hilbert corridor — perspective vanishing point."""
    fig, ax = make_fig()
    vp_x, vp_y = 0, 0.06
    n_lines = 12
    for i in range(n_lines):
        frac = i/(n_lines-1)
        x_near = -0.88 + frac*1.76
        ink(ax, [x_near, vp_x], [-0.82, vp_y], lw=0.55, alpha=0.35)
        ink(ax, [x_near, vp_x], [0.82, vp_y], lw=0.55, alpha=0.35)
    door_xs = [0.72, 0.54, 0.38, 0.24, 0.14, 0.07]
    door_hs = [0.60, 0.46, 0.34, 0.24, 0.17, 0.11]
    for dx, dh in zip(door_xs, door_hs):
        for side in [-1, 1]:
            x0 = side*dx - 0.07*side
            rect = FancyBboxPatch((x0 - 0.042, vp_y - dh/2), 0.084, dh,
                                  boxstyle='square,pad=0', linewidth=0.7,
                                  facecolor=PALE, edgecolor=INK, alpha=0.55)
            ax.add_patch(rect)
    ax.text(vp_x, vp_y, '∞', ha='center', va='center', fontsize=20,
            color=ACCENT, alpha=0.75)
    label(ax, 'infinite-hotel-scheduler')
    return save(fig, slug)


def cover_category_api(slug):
    """Commutative diagram — objects and morphisms."""
    fig, ax = make_fig()
    nodes = {'A': (-0.52, 0.45), 'B': (0.52, 0.45),
             'C': (0.52, -0.40), 'D': (-0.52, -0.40)}
    for lbl, (x, y) in nodes.items():
        c = Circle((x, y), 0.085, facecolor=PALE, edgecolor=INK, linewidth=1.2, alpha=0.85)
        ax.add_patch(c)
        ax.text(x, y, lbl, ha='center', va='center', fontsize=11,
                fontfamily='monospace', color=INK, fontweight='bold')
    morphisms = [('A','B','f',0.0,INK), ('B','C','g',0.0,INK),
                 ('A','D','h',0.0,INK), ('D','C','k',0.0,INK),
                 ('A','C','g∘f',-0.32,ACCENT)]
    for src, tgt, lbl, rad, col in morphisms:
        sx, sy = nodes[src]; tx, ty = nodes[tgt]
        ax.annotate('', xy=(tx, ty), xytext=(sx, sy),
                    arrowprops=dict(arrowstyle='->', color=col, lw=1.1,
                                   mutation_scale=11,
                                   connectionstyle=f'arc3,rad={rad}'))
        mx, my = (sx+tx)/2, (sy+ty)/2
        ax.text(mx+0.07*(1 if rad else -0.3), my, lbl, ha='center',
                fontsize=7.5, fontfamily='monospace', color=col, alpha=0.75)
    label(ax, 'category-api')
    return save(fig, slug)


def cover_reading_steiner_git(slug):
    """Branching worldlines — VCS with divergence number."""
    fig, ax = make_fig()
    rng = slug_rng(slug)
    ink(ax, [0, 0], [0.82, -0.72], lw=1.6, alpha=0.75)
    commit_y = np.linspace(0.68, -0.55, 8)
    ax.scatter(np.zeros(8), commit_y, s=14, color=INK, alpha=0.70, linewidths=0)
    for i, y in enumerate(commit_y):
        if i in [2, 4, 6]:
            sign = 1 if i == 2 else (-1 if i == 4 else 1)
            bx = sign*(0.30 + rng.uniform(0, 0.12))
            by = y - rng.uniform(0.10, 0.25)
            t = np.linspace(0, 1, 60)
            xs = t*bx
            ys = y + (by - y)*t - 0.05*np.sin(t*np.pi)
            col = ACCENT if sign > 0 else INK_MID
            ink(ax, xs, ys, lw=0.9, alpha=0.55, color=col)
            ax.scatter([bx], [by], s=10, color=col, alpha=0.65, linewidths=0)
    ax.text(0.42, 0.82, '0.337187', ha='center', fontsize=9.5,
            fontfamily='monospace', color=MUTED, alpha=0.60)
    label(ax, 'reading-steiner-git')
    return save(fig, slug)


def cover_death_note(slug):
    """Ruled notebook page — process entries in monospace."""
    fig, ax = make_fig()
    # Page
    page = FancyBboxPatch((-0.62, -0.82), 1.24, 1.64,
                          boxstyle='square,pad=0',
                          facecolor=PALE, edgecolor=INK, linewidth=1.0, alpha=0.9)
    ax.add_patch(page)
    # Rules
    for y in np.linspace(0.56, -0.66, 10):
        ink(ax, [-0.55, 0.55], [y, y], lw=0.4, alpha=0.20)
    # Accent left margin line
    ink(ax, [-0.42, -0.42], [-0.78, 0.62], lw=0.7, alpha=0.4, color=ACCENT)
    # Entries
    entries = ['Light Yagami', 'pid: 4096  SIGTERM', 'L Lawliet', 'pid: 1337  DENIED',
               'ryuk@deathnote:~$_', '', '# process table']
    for i, entry in enumerate(entries):
        y = 0.54 - i*0.175
        col = ACCENT if 'SIGTERM' in entry or 'DENIED' in entry else INK
        ax.text(-0.38, y, entry, ha='left', va='center', fontsize=7.0,
                fontfamily='monospace', color=col, alpha=0.75)
    label(ax, 'death-note')
    return save(fig, slug)


def cover_jojo_stands(slug):
    """Tick-based Gantt-like schedule grid — Stand abilities."""
    fig, ax = make_fig()
    rng = slug_rng(slug)
    stands = ['The World', 'Star Platinum', 'Crazy Diamond', 'Gold Experience', 'King Crimson']
    ticks = 14
    cell_h = 0.26
    cell_w = 0.86/ticks
    for row, stand in enumerate(stands):
        y = 0.62 - row*cell_h
        ax.text(-0.88, y, stand, ha='left', va='center', fontsize=6.2,
                fontfamily='monospace', color=MUTED, alpha=0.80)
        ink(ax, [-0.12, 0.76], [y, y], lw=0.2, alpha=0.18)
        for tick in range(ticks):
            active = rng.random() > (0.38 if 'World' in stand else 0.52)
            x = -0.12 + tick*cell_w + cell_w/2
            if active:
                rect = FancyBboxPatch((x - cell_w*0.42, y - cell_h*0.35),
                                      cell_w*0.84, cell_h*0.70,
                                      boxstyle='square,pad=0', linewidth=0.6,
                                      facecolor=PALE, edgecolor=INK, alpha=0.55)
                ax.add_patch(rect)
            else:
                ink(ax, [x, x], [y-0.04, y+0.04], lw=0.5, alpha=0.20)
    for tick in range(0, ticks, 3):
        x = -0.12 + tick*cell_w + cell_w/2
        ax.text(x, 0.74, str(tick+1), ha='center', fontsize=5,
                fontfamily='monospace', color=MUTED, alpha=0.45)
    label(ax, 'jojo-stands')
    return save(fig, slug)


def cover_unlimited_void(slug):
    """Container isolation rings — nested process space."""
    fig, ax = make_fig()
    theta = np.linspace(0, 2*np.pi, 300)
    radii_c = [0.85, 0.68, 0.52, 0.37, 0.22, 0.10]
    for i, r in enumerate(radii_c):
        alpha = 0.20 + i*0.12
        lw = 0.5 + i*0.18
        col = ACCENT if i == 5 else INK
        ax.plot(r*np.cos(theta), r*np.sin(theta), color=col, lw=lw, alpha=alpha)
    # Process dots
    n_p = 10
    for i in range(n_p):
        angle = i/n_p*2*np.pi
        r2 = 0.60
        ax.scatter([r2*np.cos(angle)], [r2*np.sin(angle)],
                   s=18, color=INK, alpha=0.45, linewidths=0)
    ax.plot(0, 0, 'o', color=ACCENT, markersize=4, alpha=0.9)
    ax.text(0, -0.92, '∅ — no information escapes', ha='center', fontsize=7,
            fontfamily='monospace', color=MUTED, alpha=0.50)
    label(ax, 'unlimited-void')
    return save(fig, slug)


def cover_at_field(slug):
    """Nested hexagons — AT Field barrier layers."""
    fig, ax = make_fig()
    def hexagon(cx, cy, r, col, alpha, lw=1.2, rot=0):
        angles = np.linspace(0, 2*np.pi, 7) + rot
        xs = cx + r*np.cos(angles)
        ys = cy + r*np.sin(angles)
        ax.plot(xs, ys, color=col, lw=lw, alpha=alpha)
    rots = [0, np.pi/6, 0, np.pi/6, 0, np.pi/6]
    radii_h = [0.84, 0.68, 0.53, 0.38, 0.24, 0.11]
    alphas = [0.18, 0.28, 0.40, 0.55, 0.70, 0.88]
    for r, al, rot in zip(radii_h, alphas, rots):
        col = ACCENT if r < 0.15 else INK
        hexagon(0, 0, r, col, al, lw=0.6+al*0.8, rot=rot)
    ax.plot(0, 0, 'o', color=INK, markersize=3, alpha=0.8)
    label(ax, 'at-field')
    return save(fig, slug)


def cover_equivalent_exchange(slug):
    """Balance scale — law of equivalent exchange."""
    fig, ax = make_fig()
    # Beam
    ink(ax, [-0.60, 0.60], [0.22, 0.22], lw=1.8, alpha=0.80)
    # Pivot
    ax.plot(0, 0.22, 'o', color=INK, markersize=5, alpha=0.8)
    # Stand + base
    ink(ax, [0, 0], [0.22, -0.50], lw=1.8, alpha=0.75)
    ink(ax, [-0.18, 0.18], [-0.50, -0.50], lw=1.8, alpha=0.75)
    # Pans
    ax.plot(-0.60, 0.22, 'o', color=INK, markersize=4, alpha=0.6)
    ax.plot( 0.60, 0.22, 'o', color=INK, markersize=4, alpha=0.6)
    arc_l = Arc((-0.60, 0.02), 0.34, 0.13, angle=0, theta1=180, theta2=360,
                color=INK, lw=1.1, alpha=0.65)
    arc_r = Arc(( 0.60, 0.02), 0.34, 0.13, angle=0, theta1=180, theta2=360,
                color=INK, lw=1.1, alpha=0.65)
    ax.add_patch(arc_l); ax.add_patch(arc_r)
    # Items
    for x in [-0.60, 0.60]:
        for i in range(3):
            a = i/3*2*np.pi
            ax.scatter([x + 0.06*np.cos(a)], [-0.02 + 0.03*np.sin(a)],
                       s=14, color=ACCENT, alpha=0.70, linewidths=0)
    ax.text(0, 0.52, '=', ha='center', fontsize=18, color=INK_MID, alpha=0.50)
    label(ax, 'equivalent-exchange-fs')
    return save(fig, slug)


def cover_vanguard_anticheat(slug):
    """Shield outline with horizontal scan sweep — safe userspace."""
    fig, ax = make_fig()
    # Shield body (approximate with arcs + lines)
    top_x = np.linspace(-0.48, 0.48, 60)
    top_y = np.full(60, 0.74)
    right_x = np.linspace(0.48, 0.0, 80)
    right_y = np.linspace(0.74, -0.76, 80)*(1 - (right_x/0.48)**2*0.08)
    left_x  = np.linspace(0.0, -0.48, 80)
    left_y  = np.linspace(-0.76, 0.74, 80)*(1 - (left_x/0.48)**2*0.08)
    shield_x = np.concatenate([top_x, right_x, left_x])
    shield_y = np.concatenate([top_y, right_y, left_y])
    ink(ax, shield_x, shield_y, lw=1.6, alpha=0.80)
    # Scan lines
    for y in np.linspace(0.58, -0.60, 11):
        x_half = 0.44*(1 - abs(y + 0.08)/0.86)
        ink(ax, [-x_half, x_half], [y, y], lw=0.35, alpha=0.22)
    # Checkmark in accent
    ck_x = [-0.15, 0.0, 0.22]; ck_y = [0.10, -0.06, 0.26]
    ink(ax, ck_x, ck_y, lw=2.5, alpha=0.85, color=ACCENT)
    label(ax, 'vanguard-anticheat')
    return save(fig, slug)


# ═══════════════════════════════════════════════════════════════════════════════

COVERS = [
    ('gojo_infinity',            cover_gojo_infinity),
    ('mobius_rickness',          cover_mobius_rickness),
    ('central_finite_curve',     cover_central_finite_curve),
    ('calabi_yau_latent',        cover_calabi_yau_latent),
    ('domain_expansion',         cover_domain_expansion),
    ('divergence-meter',         cover_divergence_meter),
    ('padic-embeddings',         cover_padic_embeddings),
    ('madoka-entropy',           cover_madoka_entropy),
    ('surreal-priority',         cover_surreal_priority),
    ('statmech-scheduler',       cover_statmech_scheduler),
    ('hairy-ball-router',        cover_hairy_ball_router),
    ('banach-tarski-dup',        cover_banach_tarski),
    ('zeno-protocol',            cover_zeno_protocol),
    ('infinite-hotel-scheduler', cover_infinite_hotel),
    ('category-api',             cover_category_api),
    ('reading-steiner-git',      cover_reading_steiner_git),
    ('death-note',               cover_death_note),
    ('jojo-stands',              cover_jojo_stands),
    ('unlimited-void',           cover_unlimited_void),
    ('at-field',                 cover_at_field),
    ('equivalent-exchange-fs',   cover_equivalent_exchange),
    ('vanguard-anticheat',       cover_vanguard_anticheat),
]


def main():
    print(f'Generating {len(COVERS)} project covers → {OUTPUT_DIR}')
    ok = fail = 0
    for slug, fn in COVERS:
        try:
            path = fn(slug)
            size = os.path.getsize(path)
            print(f'  ok  {slug}.png  ({size // 1024} KB)')
            ok += 1
        except Exception as exc:
            print(f'  ERR {slug}: {exc}', file=sys.stderr)
            fail += 1
    print(f'\nDone: {ok} generated, {fail} failed.')
    if fail:
        sys.exit(1)


if __name__ == '__main__':
    main()
