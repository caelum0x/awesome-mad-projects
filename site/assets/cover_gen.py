#!/usr/bin/env python3
"""
Generate per-project cover images for awesome-mad-projects.
Each cover is a dark-background, neon-palette procedural illustration
unique to that project's mathematical theme.
Run: /Users/arhansubasi/mad-man-projects/infinity-lab/.venv/bin/python cover_gen.py
Output: site/assets/covers/<slug>.png (22 files, each < 300 KB)
"""
import hashlib
import os
import sys
import io

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.patches import FancyArrowPatch, Arc, Circle, FancyBboxPatch, Wedge
from matplotlib.collections import LineCollection, PathCollection
from matplotlib.colors import LinearSegmentedColormap
from PIL import Image

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'covers')
os.makedirs(OUTPUT_DIR, exist_ok=True)

FIG_W, FIG_H = 7.0, 4.5   # inches
DPI = 100                   # 700 x 450 px
MAX_BYTES = 290_000

# ── Palette ────────────────────────────────────────────────────────────────
BG        = '#080b14'
BLUE      = '#4fc3ff'
PURPLE    = '#b98cff'
CYAN      = '#5be7c4'
PINK      = '#ff6eb4'
ORANGE    = '#ff9f4a'
GREEN     = '#39ff8f'
RED       = '#ff4444'
GOLD      = '#ffd700'
WHITE     = '#e7e9f2'
DEEP_BLUE = '#1a2a6c'
INDIGO    = '#3a1a6c'


def slug_rng(slug: str) -> np.random.Generator:
    seed = int(hashlib.md5(slug.encode()).hexdigest()[:8], 16) % (2 ** 31)
    return np.random.default_rng(seed)


def make_fig():
    fig, ax = plt.subplots(figsize=(FIG_W, FIG_H), dpi=DPI)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    ax.set_xlim(-1, 1)
    ax.set_ylim(-1, 1)
    ax.set_aspect('auto')
    ax.axis('off')
    return fig, ax


def add_title(ax, text: str, color: str = WHITE, y: float = -0.90):
    ax.text(
        0, y, text,
        ha='center', va='bottom',
        fontsize=14, fontweight='bold',
        color=color, fontfamily='monospace',
        path_effects=[pe.withStroke(linewidth=4, foreground='#000000')],
        transform=ax.transData, zorder=20,
    )


def save(fig, slug: str) -> str:
    path = os.path.join(OUTPUT_DIR, f'{slug}.png')
    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0.08, dpi=DPI)
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


# ── Helpers ────────────────────────────────────────────────────────────────

def glow_line(ax, xs, ys, color, lw=2.0, alpha=0.9, glow_lw=8, glow_alpha=0.18, **kw):
    ax.plot(xs, ys, color=color, lw=glow_lw, alpha=glow_alpha, solid_capstyle='round', **kw)
    ax.plot(xs, ys, color=color, lw=lw, alpha=alpha, solid_capstyle='round', **kw)


def glow_scatter(ax, xs, ys, color, s=12, alpha=0.85, glow_s=60, glow_alpha=0.15):
    ax.scatter(xs, ys, s=glow_s, color=color, alpha=glow_alpha, linewidths=0)
    ax.scatter(xs, ys, s=s,      color=color, alpha=alpha,      linewidths=0)


def radial_gradient_bg(ax, center=(0, 0), radius=1.5, color='#1a2a6c', alpha=0.5):
    n = 40
    for i in range(n, 0, -1):
        r = radius * i / n
        a = alpha * (1 - i / n) * 0.8
        c = Circle(center, r, transform=ax.transData, facecolor=color, alpha=a, linewidth=0)
        ax.add_patch(c)


# ═══════════════════════════════════════════════════════════════════════════
# Per-project cover functions
# ═══════════════════════════════════════════════════════════════════════════

def cover_gojo_infinity(slug):
    """Geodesics converging to a glowing singularity — ∞ motif."""
    fig, ax = make_fig()
    rng = slug_rng(slug)
    radial_gradient_bg(ax, (0, 0), 1.3, BLUE, 0.4)

    # Draw 18 geodesic-like curves (arcs bending toward the origin)
    n_curves = 18
    for i in range(n_curves):
        theta = i / n_curves * 2 * np.pi
        r = 0.85
        sx, sy = r * np.cos(theta), r * np.sin(theta)
        # Cubic Bezier: start → slight bend → origin
        t = np.linspace(0, 1, 80)
        cx = sx * 0.3 + rng.uniform(-0.1, 0.1)
        cy = sy * 0.3 + rng.uniform(-0.1, 0.1)
        xs = (1-t)**2 * sx + 2*(1-t)*t * cx + t**2 * 0
        ys = (1-t)**2 * sy + 2*(1-t)*t * cy + t**2 * 0
        alpha_fade = 0.6 + 0.4 * np.sin(theta)
        glow_line(ax, xs, ys, CYAN, lw=0.9, alpha=0.6 * alpha_fade, glow_lw=5, glow_alpha=0.12)

    # Infinity glyph faint behind
    t = np.linspace(0, 2 * np.pi, 300)
    scale = 0.30
    lemniscate_x = scale * np.cos(t) / (1 + np.sin(t)**2)
    lemniscate_y = scale * np.sin(t) * np.cos(t) / (1 + np.sin(t)**2)
    ax.plot(lemniscate_x, lemniscate_y, color=BLUE, lw=2.5, alpha=0.35)

    # Glowing Gojo point at origin
    for r in [0.18, 0.11, 0.055, 0.02]:
        c = Circle((0, 0), r, facecolor=WHITE if r < 0.03 else CYAN,
                   alpha=0.12 if r > 0.1 else (0.4 if r > 0.05 else 0.9), linewidth=0)
        ax.add_patch(c)

    add_title(ax, 'gojo_infinity', CYAN)
    return save(fig, slug)


def cover_mobius_rickness(slug):
    """Mobius strip outline — the Central Finite Curve's real geometry."""
    fig, ax = make_fig()
    rng = slug_rng(slug)
    radial_gradient_bg(ax, (0, 0.1), 1.2, INDIGO, 0.45)

    u = np.linspace(0, 2 * np.pi, 400)
    v_vals = np.linspace(-0.28, 0.28, 6)
    for v in v_vals:
        x = (0.55 + v * np.cos(u / 2)) * np.cos(u)
        y = (0.55 + v * np.cos(u / 2)) * np.sin(u) * 0.55   # flatten vertically
        z = v * np.sin(u / 2)
        alpha = 0.5 + 0.4 * abs(v) / 0.28
        color = PURPLE if abs(v) > 0.2 else CYAN
        lw = 1.0 if abs(v) > 0.01 else 2.0
        glow_line(ax, x, y + z * 0.3, color, lw=lw, alpha=alpha, glow_lw=6, glow_alpha=0.10)

    # Zero-curve midline (bright)
    x0 = 0.55 * np.cos(u)
    y0 = 0.55 * np.sin(u) * 0.55
    glow_line(ax, x0, y0, CYAN, lw=2.0, alpha=0.95, glow_lw=10, glow_alpha=0.25)

    add_title(ax, 'mobius_rickness', PURPLE)
    return save(fig, slug)


def cover_central_finite_curve(slug):
    """Scatter of bounded realities along an arc."""
    fig, ax = make_fig()
    rng = slug_rng(slug)
    radial_gradient_bg(ax, (0, 0), 1.4, '#0a1a2a', 0.6)

    t = np.linspace(-np.pi * 0.85, np.pi * 0.85, 300)
    # Arc curve: bounded sinusoidal
    arc_x = np.sin(t) * 0.82
    arc_y = np.cos(t) * 0.35 - 0.1
    glow_line(ax, arc_x, arc_y, GREEN, lw=2.2, alpha=0.85, glow_lw=10, glow_alpha=0.2)

    # Scatter dots representing individual realities
    n = 60
    t_pts = rng.uniform(-np.pi * 0.8, np.pi * 0.8, n)
    xs = np.sin(t_pts) * 0.82 + rng.normal(0, 0.04, n)
    ys = np.cos(t_pts) * 0.35 - 0.1 + rng.normal(0, 0.04, n)
    sizes = rng.uniform(8, 40, n)
    glow_scatter(ax, xs, ys, CYAN, s=sizes * 0.4, alpha=0.7, glow_s=sizes * 2, glow_alpha=0.15)

    # Endpoint markers (the "finite" boundaries)
    for sign in [-1, 1]:
        tx = np.sin(sign * np.pi * 0.85) * 0.82
        ty = np.cos(sign * np.pi * 0.85) * 0.35 - 0.1
        for r in [0.06, 0.035, 0.015]:
            c = Circle((tx, ty), r, facecolor=GREEN, alpha=0.1 if r > 0.04 else 0.7, linewidth=0)
            ax.add_patch(c)

    add_title(ax, 'central_finite_curve', GREEN)
    return save(fig, slug)


def cover_calabi_yau_latent(slug):
    """Periodic lattice with compactified extra dimensions — torus tile."""
    fig, ax = make_fig()
    rng = slug_rng(slug)

    # Lattice background
    for i in np.linspace(-0.9, 0.9, 10):
        ax.axhline(i, color=BLUE, lw=0.3, alpha=0.2)
        ax.axvline(i, color=BLUE, lw=0.3, alpha=0.2)

    # Compactified circles at each lattice point
    for xi in np.linspace(-0.75, 0.75, 6):
        for yi in np.linspace(-0.75, 0.75, 4):
            r = 0.055 + rng.uniform(0, 0.02)
            for ring_r in [r * 1.5, r]:
                c = Circle((xi, yi), ring_r, facecolor='none',
                            edgecolor=PINK if ring_r > r else PURPLE,
                            linewidth=0.6 if ring_r > r else 1.4,
                            alpha=0.25 if ring_r > r else 0.7)
                ax.add_patch(c)

    # Central torus outline (large)
    theta = np.linspace(0, 2 * np.pi, 200)
    R, r2 = 0.36, 0.12
    tx = (R + r2 * np.cos(theta)) * np.cos(theta * 2.5) * 0.7
    ty = (R + r2 * np.cos(theta)) * np.sin(theta * 2.5) * 0.45
    glow_line(ax, tx, ty, PURPLE, lw=1.5, alpha=0.7, glow_lw=7, glow_alpha=0.2)

    add_title(ax, 'calabi_yau_latent', PINK)
    return save(fig, slug)


def cover_domain_expansion(slug):
    """Expanding constraint web — wave rings with tension lines."""
    fig, ax = make_fig()
    rng = slug_rng(slug)
    radial_gradient_bg(ax, (0, 0), 1.2, '#1a0a00', 0.5)

    # Expanding rings
    for i, r in enumerate(np.linspace(0.1, 0.92, 8)):
        alpha = 0.8 - i * 0.07
        color = ORANGE if i % 2 == 0 else RED
        c = Circle((0, 0), r, facecolor='none', edgecolor=color,
                   linewidth=2.0 - i * 0.15, alpha=alpha, linestyle='--' if i > 4 else '-')
        ax.add_patch(c)
        # Glow
        c2 = Circle((0, 0), r, facecolor='none', edgecolor=color,
                    linewidth=8, alpha=alpha * 0.12, linestyle='-')
        ax.add_patch(c2)

    # Constraint web — radial lines
    n = 16
    for i in range(n):
        angle = i / n * 2 * np.pi
        x = [0, 0.92 * np.cos(angle)]
        y = [0, 0.92 * np.sin(angle)]
        ax.plot(x, y, color=ORANGE, lw=0.5, alpha=0.35)

    # Central point
    for r in [0.08, 0.04, 0.015]:
        c = Circle((0, 0), r, facecolor=GOLD if r < 0.02 else ORANGE,
                   alpha=0.2 if r > 0.06 else 0.85, linewidth=0)
        ax.add_patch(c)

    add_title(ax, 'domain_expansion', ORANGE)
    return save(fig, slug)


def cover_divergence_meter(slug):
    """Worldline branches — Steins;Gate divergence number tree."""
    fig, ax = make_fig()
    rng = slug_rng(slug)

    ax.set_facecolor('#050810')
    fig.patch.set_facecolor('#050810')

    # Nixie-tube digit hint (amber glow)
    for i, digit in enumerate(['0', '.', '3', '3', '7', '1', '8', '7']):
        x = -0.85 + i * 0.25
        alpha = rng.uniform(0.3, 0.9)
        ax.text(x, 0.15, digit, ha='center', va='center',
                fontsize=20, color=GOLD, alpha=alpha, fontfamily='monospace',
                fontweight='bold',
                path_effects=[pe.withStroke(linewidth=3, foreground='#3a2000')])

    # Worldline branches below
    y0 = -0.1
    ax.plot([-0.5, 0.5], [y0, y0], color=GOLD, lw=2.5, alpha=0.8)
    branches = [(-0.5, -0.85, -0.2, -0.2), (0.0, -0.85, 0.6, -0.5), (0.5, -0.85, -0.1, -0.75)]
    for x1, x2, bx, by in [(-0.5, -0.85, -0.6, -0.55), (-0.5, 0.0, -0.25, -0.42),
                             (0.5, 0.2, 0.35, -0.55), (0.5, 0.75, 0.62, -0.58)]:
        t = np.linspace(0, 1, 60)
        mx, my = (x1 + x2) / 2, y0 - 0.25
        xs = (1 - t) ** 2 * x1 + 2 * (1 - t) * t * bx + t ** 2 * x2
        ys = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * (y0 - 0.3) + t ** 2 * (y0 - 0.65)
        glow_line(ax, xs, ys, GOLD, lw=1.2, alpha=0.7, glow_lw=5, glow_alpha=0.18)

    add_title(ax, 'divergence-meter', GOLD)
    return save(fig, slug)


def cover_padic_embeddings(slug):
    """p-adic tree (base-3) — ultrametric branching."""
    fig, ax = make_fig()
    p = 3

    def draw_tree(x, y, dy, depth, max_depth, color):
        if depth > max_depth:
            return
        for i in range(p):
            nx = x + (i - (p - 1) / 2) * dy * 0.8
            ny = y - dy
            glow_line(ax, [x, nx], [y, ny], color, lw=1.5 - depth * 0.2, alpha=0.8 - depth * 0.1,
                      glow_lw=6 - depth, glow_alpha=0.15)
            draw_tree(nx, ny, dy / p, depth + 1, max_depth, color)

    radial_gradient_bg(ax, (0, 0.5), 1.2, '#001a10', 0.5)
    draw_tree(0, 0.82, 0.42, 0, 3, GREEN)

    # Leaves
    lx = [-0.78, -0.39, 0.0, 0.39, 0.78, -0.59, -0.2, 0.2, 0.59]
    ly = [-0.72] * 9
    glow_scatter(ax, lx, ly, CYAN, s=18, alpha=0.9, glow_s=80, glow_alpha=0.2)

    add_title(ax, 'padic-embeddings', GREEN)
    return save(fig, slug)


def cover_madoka_entropy(slug):
    """Entropy spiral — magical energy harvested as entropy grows."""
    fig, ax = make_fig()
    rng = slug_rng(slug)
    radial_gradient_bg(ax, (0, 0), 1.3, '#1a001a', 0.5)

    # Archimedean spiral
    t = np.linspace(0, 5 * np.pi, 600)
    r = t / (5 * np.pi) * 0.9
    xs = r * np.cos(t)
    ys = r * np.sin(t) * 0.85
    glow_line(ax, xs, ys, PINK, lw=1.8, alpha=0.85, glow_lw=8, glow_alpha=0.2)

    # Entropy particles along spiral
    t_pts = np.linspace(0, 5 * np.pi, 40)
    r_pts = t_pts / (5 * np.pi) * 0.9
    px = r_pts * np.cos(t_pts) + rng.normal(0, 0.015, 40)
    py = r_pts * np.sin(t_pts) * 0.85 + rng.normal(0, 0.015, 40)
    glow_scatter(ax, px, py, PURPLE, s=6, alpha=0.8, glow_s=40, glow_alpha=0.2)

    # Center glow (magical source)
    for r2 in [0.15, 0.08, 0.03]:
        c = Circle((0, 0), r2, facecolor=PINK, alpha=0.08 if r2 > 0.1 else (0.3 if r2 > 0.05 else 0.9), linewidth=0)
        ax.add_patch(c)

    add_title(ax, 'madoka-entropy', PINK)
    return save(fig, slug)


def cover_surreal_priority(slug):
    """Surreal number tree — nested {|} representation."""
    fig, ax = make_fig()

    def draw_surreal(x, y, level, span):
        if level > 3:
            return
        color = [WHITE, BLUE, PURPLE, CYAN][level]
        alpha = 1.0 - level * 0.2
        lw = 2.5 - level * 0.5
        label = ['{|}', '{0|}', '{|0}', '{-1|1}', '{0|1}', '{1|2}'][min(level * 2, 5)]
        ax.text(x, y, label, ha='center', va='center', fontsize=9 - level * 1.2,
                color=color, alpha=alpha, fontfamily='monospace',
                path_effects=[pe.withStroke(linewidth=2, foreground='black')])
        if level < 3:
            dx = span / 2
            for sign, child_label in [(-1, 'L'), (1, 'R')]:
                nx, ny = x + sign * dx, y - 0.38
                ax.plot([x, nx], [y - 0.1, ny + 0.1], color=color, lw=lw * 0.6, alpha=alpha * 0.6)
                draw_surreal(nx, ny, level + 1, span / 2)

    radial_gradient_bg(ax, (0, 0.5), 1.3, DEEP_BLUE, 0.4)
    draw_surreal(0, 0.75, 0, 0.85)
    add_title(ax, 'surreal-priority', WHITE)
    return save(fig, slug)


def cover_statmech_scheduler(slug):
    """Phase space scatter — tasks as energy particles."""
    fig, ax = make_fig()
    rng = slug_rng(slug)

    # Background grid
    for v in np.linspace(-0.8, 0.8, 9):
        ax.axhline(v, color=ORANGE, lw=0.2, alpha=0.15)
        ax.axvline(v, color=ORANGE, lw=0.2, alpha=0.15)

    # Particles in phase space
    n = 120
    px = rng.uniform(-0.88, 0.88, n)
    py = rng.uniform(-0.88, 0.88, n)
    energy = np.sqrt(px ** 2 + py ** 2)  # proxy for energy

    # Color by energy (cold=blue, hot=red)
    cmap = LinearSegmentedColormap.from_list('thermo', [BLUE, CYAN, GREEN, ORANGE, RED])
    colors = cmap(energy / energy.max())
    for i in range(n):
        ax.scatter(px[i], py[i], s=18, color=colors[i], alpha=0.75, linewidths=0)
        ax.scatter(px[i], py[i], s=55, color=colors[i], alpha=0.12, linewidths=0)

    # Maxwell-Boltzmann density curve hint
    xe = np.linspace(0, 1.4, 100)
    ye_raw = xe ** 2 * np.exp(-xe ** 2 * 2)
    ye = ye_raw / ye_raw.max() * 0.6 - 0.88
    glow_line(ax, xe - 0.7, ye, ORANGE, lw=1.5, alpha=0.7, glow_lw=6, glow_alpha=0.2)

    add_title(ax, 'statmech-scheduler', ORANGE)
    return save(fig, slug)


def cover_hairy_ball_router(slug):
    """Sphere S² with tangent vector field arrows."""
    fig, ax = make_fig()
    rng = slug_rng(slug)

    # Sphere outline
    theta = np.linspace(0, 2 * np.pi, 200)
    ax.plot(0.7 * np.cos(theta), 0.7 * np.sin(theta), color=GREEN, lw=1.8, alpha=0.7)
    # Latitude lines
    for lat in np.linspace(-0.6, 0.6, 7):
        r_lat = np.sqrt(max(0, 0.7 ** 2 - lat ** 2))
        ax.plot(r_lat * np.cos(theta), lat + np.zeros_like(theta) * r_lat,
                color=GREEN, lw=0.5, alpha=0.25)

    # Tangent vector field (vortex — no zeros on the sphere, shown as approximation)
    n_arrows = 30
    for i in range(n_arrows):
        angle_phi = rng.uniform(0, 2 * np.pi)
        angle_theta2 = rng.uniform(0.2, np.pi - 0.2)
        x = 0.62 * np.sin(angle_theta2) * np.cos(angle_phi)
        y = 0.62 * np.cos(angle_theta2)
        # Tangent in longitude direction
        vx = -np.sin(angle_phi) * 0.12
        vy = 0.0
        # Slight meridional
        vx += rng.uniform(-0.03, 0.03)
        vy += rng.uniform(-0.03, 0.03)
        ax.annotate('', xy=(x + vx, y + vy), xytext=(x, y),
                    arrowprops=dict(arrowstyle='->', color=CYAN, lw=0.9, mutation_scale=8))

    add_title(ax, 'hairy-ball-router', GREEN)
    return save(fig, slug)


def cover_banach_tarski(slug):
    """Two duplicated spheres — free group F₂ decomposition."""
    fig, ax = make_fig()

    radial_gradient_bg(ax, (-0.38, 0.1), 0.48, '#1a0000', 0.5)
    radial_gradient_bg(ax, (0.38, 0.1), 0.48, '#001a00', 0.4)

    theta = np.linspace(0, 2 * np.pi, 200)
    # Left sphere
    for r in [0.38, 0.36, 0.34]:
        col = RED if r == 0.38 else ORANGE
        lw = 2.0 if r == 0.38 else 0.7
        alpha = 0.9 if r == 0.38 else 0.4
        ax.plot(-0.38 + r * np.cos(theta), 0.1 + r * np.sin(theta), color=col, lw=lw, alpha=alpha)
    # Right sphere
    for r in [0.38, 0.36, 0.34]:
        col = GREEN if r == 0.38 else CYAN
        lw = 2.0 if r == 0.38 else 0.7
        alpha = 0.9 if r == 0.38 else 0.4
        ax.plot(0.38 + r * np.cos(theta), 0.1 + r * np.sin(theta), color=col, lw=lw, alpha=alpha)

    # Arrow "one becomes two"
    ax.annotate('', xy=(0.12, 0.1), xytext=(-0.12, 0.1),
                arrowprops=dict(arrowstyle='->', color=WHITE, lw=1.5,
                                connectionstyle='arc3,rad=0.3', mutation_scale=14))
    ax.text(0, 0.25, '≅', ha='center', va='center', fontsize=18, color=WHITE, alpha=0.7)

    # Group elements faintly
    for i, label in enumerate(['a', 'b', 'a⁻¹', 'b⁻¹']):
        x = -0.55 + (i % 2) * 1.1
        y = -0.55 + (i // 2) * 0.3
        ax.text(x, y, label, ha='center', va='center', fontsize=9,
                color=ORANGE, alpha=0.5, fontfamily='monospace')

    add_title(ax, 'banach-tarski-dup', RED)
    return save(fig, slug)


def cover_zeno_protocol(slug):
    """Halving segments along a line — Zeno's dichotomy."""
    fig, ax = make_fig()

    radial_gradient_bg(ax, (0, 0), 1.4, DEEP_BLUE, 0.35)

    # Main line
    ax.plot([-0.88, 0.88], [0, 0], color=CYAN, lw=2.5, alpha=0.8)
    # Glow
    ax.plot([-0.88, 0.88], [0, 0], color=CYAN, lw=10, alpha=0.15)

    # Zeno segments — each half the remaining distance
    n_segments = 9
    start = -0.88
    end = 0.88
    x = start
    colors_seq = [CYAN, BLUE, PURPLE, PINK, PURPLE, BLUE, CYAN, BLUE, PURPLE]
    for i in range(n_segments):
        mid = x + (end - x) / 2
        y_offset = 0.08 + i * 0.02
        # Tick mark
        for yy in [-y_offset * 0.5, y_offset * 0.5]:
            ax.plot([mid, mid], [-0.04, 0.04], color=colors_seq[i % len(colors_seq)], lw=1.5, alpha=0.8)
        # Label
        fraction = f'1/{2**(i+1)}'
        ax.text(mid, 0.12 + i * 0.04, fraction, ha='center', va='bottom',
                fontsize=max(4, 8 - i), color=colors_seq[i % len(colors_seq)],
                alpha=max(0.3, 0.9 - i * 0.08), fontfamily='monospace')
        x = mid

    # Goal marker
    for r in [0.06, 0.035, 0.012]:
        c = Circle((end, 0), r, facecolor=GREEN if r < 0.02 else CYAN,
                   alpha=0.15 if r > 0.05 else 0.8, linewidth=0)
        ax.add_patch(c)
    ax.text(end, -0.15, 'goal', ha='center', va='top', fontsize=8,
            color=GREEN, alpha=0.8, fontfamily='monospace')

    add_title(ax, 'zeno-protocol', CYAN)
    return save(fig, slug)


def cover_infinite_hotel(slug):
    """Perspective corridor of rooms — always room for one more."""
    fig, ax = make_fig()

    ax.set_facecolor('#04070f')
    fig.patch.set_facecolor('#04070f')

    # Perspective lines toward vanishing point
    vp_x, vp_y = 0, 0.1
    n_lines = 14
    for i in range(n_lines):
        frac = i / (n_lines - 1)
        x_near = -0.9 + frac * 1.8
        # Bottom wall
        glow_line(ax, [x_near, vp_x], [-0.88, vp_y], PURPLE, lw=0.6, alpha=0.5, glow_lw=3, glow_alpha=0.1)
        # Top wall
        glow_line(ax, [x_near, vp_x], [0.88, vp_y], PURPLE, lw=0.6, alpha=0.5, glow_lw=3, glow_alpha=0.1)

    # Room doors (receding)
    door_x_positions = [0.75, 0.55, 0.38, 0.24, 0.14, 0.07]
    door_heights = [0.65, 0.50, 0.38, 0.28, 0.20, 0.14]
    colors_d = [PURPLE, BLUE, CYAN, PURPLE, BLUE, CYAN]
    for i, (dx, dh) in enumerate(zip(door_x_positions, door_heights)):
        for side in [-1, 1]:
            x0 = side * dx - 0.08 * side
            rect = FancyBboxPatch((x0 - 0.04, vp_y - dh / 2), 0.08, dh,
                                  boxstyle='square,pad=0.01',
                                  facecolor=colors_d[i], alpha=0.07, edgecolor=colors_d[i],
                                  linewidth=1.0)
            ax.add_patch(rect)
        ax.text(-door_x_positions[i] + 0.015, vp_y + door_heights[i] / 2 + 0.03,
                str(i + 1), ha='center', va='bottom', fontsize=6,
                color=CYAN, alpha=0.6, fontfamily='monospace')

    ax.text(vp_x, vp_y, '∞', ha='center', va='center', fontsize=22,
            color=WHITE, alpha=0.9,
            path_effects=[pe.withStroke(linewidth=3, foreground=PURPLE)])

    add_title(ax, 'infinite-hotel-scheduler', PURPLE)
    return save(fig, slug)


def cover_category_api(slug):
    """Commutative diagram — objects and morphisms."""
    fig, ax = make_fig()
    radial_gradient_bg(ax, (0, 0), 1.3, '#0a0a1a', 0.45)

    # Objects (nodes)
    nodes = {'A': (-0.55, 0.45), 'B': (0.55, 0.45), 'C': (0.55, -0.45), 'D': (-0.55, -0.45)}
    for label, (x, y) in nodes.items():
        for r in [0.09, 0.055]:
            c = Circle((x, y), r, facecolor=ORANGE if r < 0.06 else 'none',
                       edgecolor=ORANGE, linewidth=1.5 if r > 0.06 else 0,
                       alpha=0.7 if r > 0.06 else 0.85)
            ax.add_patch(c)
        ax.text(x, y, label, ha='center', va='center', fontsize=11,
                color=BG, fontweight='bold', fontfamily='monospace')

    # Morphisms (arrows)
    arrow_kw = dict(arrowstyle='->', color=WHITE, lw=1.5, mutation_scale=12)
    morphisms = [('A', 'B', 'f', 0.0), ('B', 'C', 'g', 0.0),
                 ('A', 'D', 'h', 0.0), ('D', 'C', 'k', 0.0),
                 ('A', 'C', 'g∘f', -0.3)]
    for src, tgt, label, rad in morphisms:
        sx, sy = nodes[src]
        tx, ty = nodes[tgt]
        style = dict(arrowstyle='->', color=ORANGE if 'f' in label else CYAN,
                     lw=1.5, mutation_scale=12,
                     connectionstyle=f'arc3,rad={rad}')
        ax.annotate('', xy=(tx, ty), xytext=(sx, sy), arrowprops=style)
        mx, my = (sx + tx) / 2, (sy + ty) / 2
        ax.text(mx + 0.06 * (1 if rad > 0 else -0.5), my, label,
                ha='center', va='center', fontsize=7,
                color=ORANGE if 'f' in label else CYAN, alpha=0.85, fontfamily='monospace')

    add_title(ax, 'category-api', ORANGE)
    return save(fig, slug)


def cover_reading_steiner_git(slug):
    """Branching worldlines — VCS divergence meter tree."""
    fig, ax = make_fig()
    rng = slug_rng(slug)
    radial_gradient_bg(ax, (0, 0.5), 1.3, DEEP_BLUE, 0.35)

    # Main trunk
    glow_line(ax, [0, 0], [0.85, -0.85], CYAN, lw=2.5, alpha=0.8, glow_lw=8, glow_alpha=0.2)

    # Commits on trunk
    commit_y = np.linspace(0.7, -0.6, 8)
    glow_scatter(ax, np.zeros(8), commit_y, CYAN, s=20, alpha=0.9, glow_s=80, glow_alpha=0.2)

    # Branches
    for i, y in enumerate(commit_y):
        if i in [2, 4, 6]:
            sign = 1 if i % 4 == 2 else -1
            branch_end_x = sign * (0.35 + rng.uniform(0, 0.15))
            branch_end_y = y - rng.uniform(0.1, 0.3)
            t = np.linspace(0, 1, 50)
            xs = t * branch_end_x
            ys = y + (branch_end_y - y) * t - 0.05 * np.sin(t * np.pi)
            color = BLUE if sign > 0 else PURPLE
            glow_line(ax, xs, ys, color, lw=1.5, alpha=0.7, glow_lw=6, glow_alpha=0.15)
            glow_scatter(ax, [branch_end_x], [branch_end_y], color, s=15, alpha=0.85, glow_s=60, glow_alpha=0.2)

    # Divergence number label
    ax.text(0.35, 0.82, '0.337187', ha='center', va='center', fontsize=10,
            color=GOLD, alpha=0.85, fontfamily='monospace',
            path_effects=[pe.withStroke(linewidth=2, foreground='black')])

    add_title(ax, 'reading-steiner-git', CYAN)
    return save(fig, slug)


def cover_death_note(slug):
    """Stylized notebook page with terminal-style process lines."""
    fig, ax = make_fig()

    ax.set_facecolor('#0a0208')
    fig.patch.set_facecolor('#0a0208')

    # Page outline (notebook)
    page = FancyBboxPatch((-0.62, -0.80), 1.24, 1.60,
                          boxstyle='round,pad=0.02',
                          facecolor='#0e0508', edgecolor=RED,
                          linewidth=2.0, alpha=0.9)
    ax.add_patch(page)

    # Page lines (ruled)
    for y in np.linspace(0.55, -0.68, 10):
        ax.plot([-0.55, 0.55], [y, y], color='#3a0a0a', lw=0.8, alpha=0.7)

    # "Process entries" — terminal-style
    entries = ['Light Yagami', 'process_id: 4096', 'cause: SIGTERM', 'L Lawliet', 'process_id: 1337', '⚠ ACCESS DENIED', 'ryuk@deathnote:~$']
    colors_e = [RED, '#cc4444', '#aa3333', RED, '#cc4444', ORANGE, GREEN]
    for i, (entry, color) in enumerate(zip(entries, colors_e)):
        y = 0.55 - i * 0.18
        ax.text(-0.5, y, entry, ha='left', va='center', fontsize=7,
                color=color, alpha=0.85, fontfamily='monospace')

    # Red glow
    for r in [0.18, 0.08]:
        c = Circle((0, 0), r, facecolor=RED, alpha=0.04 if r > 0.1 else 0.08, linewidth=0)
        ax.add_patch(c)

    add_title(ax, 'death-note', RED)
    return save(fig, slug)


def cover_jojo_stands(slug):
    """Tick-based schedule grid — Stand abilities per tick."""
    fig, ax = make_fig()
    rng = slug_rng(slug)

    stands = ['The World', 'Star Platinum', 'Crazy Diamond', 'Gold Experience', 'King Crimson']
    ticks = 14
    colors_s = [GOLD, PURPLE, CYAN, GREEN, RED]

    cell_h = 0.28
    cell_w = 0.88 / ticks

    for row, (stand, color) in enumerate(zip(stands, colors_s)):
        y = 0.6 - row * cell_h
        ax.text(-0.88, y, stand, ha='left', va='center', fontsize=6.5,
                color=color, alpha=0.85, fontfamily='monospace')
        for tick in range(ticks):
            active = rng.random() > (0.4 if 'World' in stand else 0.55)
            x = -0.12 + tick * cell_w + cell_w / 2
            if active:
                rect = FancyBboxPatch((x - cell_w * 0.42, y - cell_h * 0.36),
                                      cell_w * 0.84, cell_h * 0.72,
                                      boxstyle='round,pad=0.005',
                                      facecolor=color, alpha=0.35,
                                      edgecolor=color, linewidth=0.8)
                ax.add_patch(rect)
            else:
                ax.plot([x], [y], marker='|', markersize=4, color=color, alpha=0.2)

    # Tick labels
    for tick in range(0, ticks, 2):
        x = -0.12 + tick * cell_w + cell_w / 2
        ax.text(x, 0.78, str(tick + 1), ha='center', va='center', fontsize=5,
                color=WHITE, alpha=0.5, fontfamily='monospace')

    add_title(ax, 'jojo-stands', GOLD)
    return save(fig, slug)


def cover_unlimited_void(slug):
    """Container isolation rings — process table in void."""
    fig, ax = make_fig()
    radial_gradient_bg(ax, (0, 0), 1.4, '#000a1a', 0.6)

    theta = np.linspace(0, 2 * np.pi, 200)

    # Outer isolation rings
    for i, (r, color, alpha) in enumerate([(0.88, BLUE, 0.4), (0.72, CYAN, 0.5),
                                            (0.55, BLUE, 0.6), (0.38, PURPLE, 0.65),
                                            (0.22, CYAN, 0.75), (0.10, WHITE, 0.9)]):
        ax.plot(r * np.cos(theta), r * np.sin(theta), color=color, lw=1.2 + i * 0.2, alpha=alpha)
        ax.plot(r * np.cos(theta), r * np.sin(theta), color=color, lw=8, alpha=alpha * 0.1)

    # Process containers at various radii
    n_procs = 12
    for i in range(n_procs):
        angle = i / n_procs * 2 * np.pi
        r = 0.62 + (i % 3) * 0.13
        x, y = r * np.cos(angle), r * np.sin(angle)
        ax.scatter([x], [y], s=25, color=CYAN, alpha=0.7, linewidths=0, zorder=5)
        ax.scatter([x], [y], s=80, color=CYAN, alpha=0.12, linewidths=0, zorder=4)

    # Central void
    c = Circle((0, 0), 0.06, facecolor=WHITE, alpha=0.95, linewidth=0)
    ax.add_patch(c)

    add_title(ax, 'unlimited-void', BLUE)
    return save(fig, slug)


def cover_at_field(slug):
    """Nested hexagons — AT Field barrier layers."""
    fig, ax = make_fig()
    radial_gradient_bg(ax, (0, 0), 1.3, '#001a1a', 0.4)

    # Hexagon helper
    def hexagon(cx, cy, r, color, alpha, lw=1.5, rot=0):
        angles = np.linspace(0, 2 * np.pi, 7) + rot
        xs = cx + r * np.cos(angles)
        ys = cy + r * np.sin(angles)
        ax.plot(xs, ys, color=color, lw=lw, alpha=alpha)
        ax.plot(xs, ys, color=color, lw=lw * 5, alpha=alpha * 0.12)

    rotations = [0, np.pi / 6, 0, np.pi / 6, 0, np.pi / 6]
    radii = [0.85, 0.70, 0.55, 0.40, 0.26, 0.13]
    colors_h = [CYAN, BLUE, CYAN, PURPLE, CYAN, WHITE]
    alphas = [0.35, 0.5, 0.6, 0.7, 0.85, 0.95]

    for r, color, alpha, rot in zip(radii, colors_h, alphas, rotations):
        hexagon(0, 0, r, color, alpha, lw=1.2 + (0.85 - r), rot=rot)

    # Central core
    c = Circle((0, 0), 0.04, facecolor=WHITE, alpha=0.9, linewidth=0)
    ax.add_patch(c)

    add_title(ax, 'at-field', CYAN)
    return save(fig, slug)


def cover_equivalent_exchange(slug):
    """Balance scale — two equal shapes exchanged."""
    fig, ax = make_fig()
    radial_gradient_bg(ax, (0, 0.2), 1.3, '#1a1000', 0.45)

    # Scale beam
    glow_line(ax, [-0.6, 0.6], [0.2, 0.2], GOLD, lw=2.5, alpha=0.85, glow_lw=8, glow_alpha=0.2)
    # Pivot
    for r in [0.05, 0.025]:
        c = Circle((0, 0.2), r, facecolor=GOLD if r < 0.03 else 'none',
                   edgecolor=GOLD, linewidth=1.5, alpha=0.9 if r < 0.03 else 0.5)
        ax.add_patch(c)
    # Stand
    glow_line(ax, [0, 0], [0.2, -0.55], GOLD, lw=2.5, alpha=0.8, glow_lw=8, glow_alpha=0.18)
    # Base
    glow_line(ax, [-0.2, 0.2], [-0.55, -0.55], GOLD, lw=2.5, alpha=0.8, glow_lw=8, glow_alpha=0.18)

    # Left pan
    ax.plot(-0.6, 0.2, 'o', color=GOLD, markersize=6, alpha=0.6)
    arc_l = Arc((-0.6, 0.0), 0.35, 0.15, angle=0, theta1=180, theta2=360, color=GOLD, lw=1.8, alpha=0.7)
    ax.add_patch(arc_l)
    # Right pan
    ax.plot(0.6, 0.2, 'o', color=GOLD, markersize=6, alpha=0.6)
    arc_r = Arc((0.6, 0.0), 0.35, 0.15, angle=0, theta1=180, theta2=360, color=GOLD, lw=1.8, alpha=0.7)
    ax.add_patch(arc_r)

    # Equal items on each pan
    for x in [-0.6, 0.6]:
        for i in range(3):
            angle_i = i / 3 * 2 * np.pi
            sx = x + 0.07 * np.cos(angle_i)
            sy = -0.02 + 0.04 * np.sin(angle_i)
            ax.scatter([sx], [sy], s=20, color=ORANGE, alpha=0.8, linewidths=0)
            ax.scatter([sx], [sy], s=60, color=ORANGE, alpha=0.15, linewidths=0)

    # "=" sign
    ax.text(0, 0.48, '=', ha='center', va='center', fontsize=22,
            color=WHITE, alpha=0.8,
            path_effects=[pe.withStroke(linewidth=3, foreground='black')])

    add_title(ax, 'equivalent-exchange-fs', GOLD)
    return save(fig, slug)


def cover_vanguard_anticheat(slug):
    """Shield outline with geometric scan pattern."""
    fig, ax = make_fig()
    radial_gradient_bg(ax, (0, 0.1), 1.3, '#000a1a', 0.5)

    # Shield outline (custom path)
    shield_t = np.linspace(0, 1, 200)
    # Approximate a shield shape
    top_x = np.linspace(-0.5, 0.5, 50)
    top_y = 0.75 + np.zeros(50)
    right_x = np.linspace(0.5, 0, 50)
    right_y = np.linspace(0.75, -0.80, 50) * (1 - (right_x / 0.5) ** 2 * 0.1)
    left_x = np.linspace(0, -0.5, 50)
    left_y = np.linspace(-0.80, 0.75, 50) * (1 - (left_x / 0.5) ** 2 * 0.1)

    shield_x = np.concatenate([top_x, right_x, left_x])
    shield_y = np.concatenate([top_y, right_y, left_y])
    glow_line(ax, shield_x, shield_y, BLUE, lw=2.5, alpha=0.9, glow_lw=10, glow_alpha=0.2)

    # Internal scan lines (security sweep)
    for y in np.linspace(0.6, -0.65, 12):
        x_half = 0.48 * (1 - abs(y + 0.1) / 0.9)
        alpha = 0.3 + 0.3 * (1 - abs(y) / 0.8)
        ax.plot([-x_half, x_half], [y, y], color=CYAN, lw=0.6, alpha=alpha)

    # Central checkmark
    ck_x = [-0.15, 0.0, 0.22]
    ck_y = [0.1, -0.05, 0.25]
    glow_line(ax, ck_x, ck_y, GREEN, lw=3.5, alpha=0.9, glow_lw=12, glow_alpha=0.25)

    # Corner glow
    for r in [0.12, 0.06, 0.02]:
        c = Circle((0, 0.1), r, facecolor=GREEN if r < 0.03 else 'none',
                   edgecolor=CYAN, linewidth=1 if r > 0.03 else 0,
                   alpha=0.15 if r > 0.1 else (0.5 if r > 0.04 else 0.85))
        ax.add_patch(c)

    add_title(ax, 'vanguard-anticheat', BLUE)
    return save(fig, slug)


# ═══════════════════════════════════════════════════════════════════════════
# Registry & runner
# ═══════════════════════════════════════════════════════════════════════════

COVERS = [
    ('gojo_infinity',             cover_gojo_infinity),
    ('mobius_rickness',           cover_mobius_rickness),
    ('central_finite_curve',      cover_central_finite_curve),
    ('calabi_yau_latent',         cover_calabi_yau_latent),
    ('domain_expansion',          cover_domain_expansion),
    ('divergence-meter',          cover_divergence_meter),
    ('padic-embeddings',          cover_padic_embeddings),
    ('madoka-entropy',            cover_madoka_entropy),
    ('surreal-priority',          cover_surreal_priority),
    ('statmech-scheduler',        cover_statmech_scheduler),
    ('hairy-ball-router',         cover_hairy_ball_router),
    ('banach-tarski-dup',         cover_banach_tarski),
    ('zeno-protocol',             cover_zeno_protocol),
    ('infinite-hotel-scheduler',  cover_infinite_hotel),
    ('category-api',              cover_category_api),
    ('reading-steiner-git',       cover_reading_steiner_git),
    ('death-note',                cover_death_note),
    ('jojo-stands',               cover_jojo_stands),
    ('unlimited-void',            cover_unlimited_void),
    ('at-field',                  cover_at_field),
    ('equivalent-exchange-fs',    cover_equivalent_exchange),
    ('vanguard-anticheat',        cover_vanguard_anticheat),
]


def main():
    print(f'Generating {len(COVERS)} project covers → {OUTPUT_DIR}')
    ok, fail = 0, 0
    for slug, fn in COVERS:
        try:
            path = fn(slug)
            size = os.path.getsize(path)
            print(f'  ✓ {slug}.png  ({size // 1024} KB)')
            ok += 1
        except Exception as exc:
            print(f'  ✗ {slug}: {exc}', file=sys.stderr)
            fail += 1
    print(f'\nDone: {ok} generated, {fail} failed.')
    if fail:
        sys.exit(1)


if __name__ == '__main__':
    main()
