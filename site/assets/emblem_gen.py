"""
emblem_gen.py — original ink-on-cream emblems for awesome-mad-projects.
Outputs PNG files to site/assets/emblems/.
All geometry is original generative art: no anime stills, no PDF figures.
Run with:
    /path/to/.venv/bin/python site/assets/emblem_gen.py
"""

import os
import math
import pathlib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import numpy as np

# ── Design tokens ──────────────────────────────────────────────────────────
CREAM      = "#f6f2e9"
INK        = "#16150f"
INK_2      = "#3d3b32"
MUTED      = "#6b6760"
ACCENT     = "#d1341a"
RULE_RGBA  = (22/255, 21/255, 15/255, 0.18)

OUT = pathlib.Path(__file__).parent / "emblems"
OUT.mkdir(exist_ok=True)

DPI = 150          # output DPI
W = H = 6         # figure size inches (square)

def new_fig():
    fig, ax = plt.subplots(figsize=(W, H), dpi=DPI)
    fig.patch.set_facecolor(CREAM)
    ax.set_facecolor(CREAM)
    ax.set_xlim(-1, 1); ax.set_ylim(-1, 1)
    ax.set_aspect("equal")
    ax.axis("off")
    return fig, ax

def save(fig, name):
    path = OUT / name
    fig.savefig(path, dpi=DPI, facecolor=CREAM, bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    kb = path.stat().st_size / 1024
    print(f"  {name}  ({kb:.0f} kB)")


# ══════════════════════════════════════════════════════════════════════════
# 1. gojo_infinity
#    Lemniscate (∞) drawn as a proper Bernoulli curve, with a hexagonal
#    geodesic-field overlay — six converging ray-pairs.
# ══════════════════════════════════════════════════════════════════════════
def emblem_gojo():
    fig, ax = new_fig()

    # Geodesic field background: faint radial lines converging to origin
    n_rays = 24
    for i in range(n_rays):
        theta = 2 * math.pi * i / n_rays
        x1, y1 = 0.96 * math.cos(theta), 0.96 * math.sin(theta)
        ax.plot([0, x1], [0, y1], color=MUTED, alpha=0.18, lw=0.6, zorder=1)

    # Concentric rings (felt-distance shells) — fading outward
    for r, alpha in [(0.20, 0.40), (0.38, 0.28), (0.55, 0.20),
                     (0.70, 0.14), (0.84, 0.10)]:
        circle = plt.Circle((0, 0), r, color=INK_2, fill=False,
                             lw=0.7, alpha=alpha, zorder=2)
        ax.add_patch(circle)

    # Six-point star (hexagram) outline — two interlocked triangles
    def triangle_pts(center, r, rot_deg):
        cx, cy = center
        pts = []
        for k in range(3):
            a = math.radians(rot_deg + 120 * k)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
        pts.append(pts[0])
        return pts

    tri1 = triangle_pts((0, 0), 0.58, 90)
    tri2 = triangle_pts((0, 0), 0.58, -90)
    xs1, ys1 = zip(*tri1)
    xs2, ys2 = zip(*tri2)
    ax.plot(xs1, ys1, color=INK, lw=1.6, alpha=0.50, zorder=3)
    ax.plot(xs2, ys2, color=INK, lw=1.6, alpha=0.50, zorder=3)

    # Bernoulli lemniscate: (x²+y²)² = 2a²(x²−y²)  →  parametric
    # x = a·cos(t)/(1+sin²t),  y = a·sin(t)cos(t)/(1+sin²t)
    a = 0.70
    t = np.linspace(0, 2 * math.pi, 1200)
    denom = 1 + np.sin(t) ** 2
    lx = a * np.cos(t) / denom
    ly = a * np.sin(t) * np.cos(t) / denom

    # Thick cream halo then ink stroke (calligraphic two-stroke)
    ax.plot(lx, ly, color=CREAM, lw=8, alpha=0.9, zorder=4, solid_capstyle="round")
    ax.plot(lx, ly, color=INK, lw=2.6, alpha=0.92, zorder=5, solid_capstyle="round")

    # Accent highlight on the lemniscate — thin vermilion line along top arc
    mask = np.sin(t) > 0
    ax.plot(lx[mask], ly[mask], color=ACCENT, lw=0.9, alpha=0.80, zorder=6)
    mask2 = np.sin(t) < 0
    ax.plot(lx[mask2], ly[mask2], color=ACCENT, lw=0.9, alpha=0.80, zorder=6)

    # Central pole dot
    ax.plot(0, 0, "o", color=ACCENT, ms=5, zorder=8)

    # Legend / label
    ax.text(0, -0.93, "GOJO INFINITY", ha="center", va="bottom",
            fontsize=7, fontweight="bold", color=MUTED,
            fontfamily="monospace")
    ax.text(0, -0.985, "∞  · Riemannian conformal geometry",
            ha="center", va="bottom", fontsize=5.5, color=MUTED, fontfamily="monospace")

    # Hairline border
    rect = mpatches.FancyBboxPatch((-0.998, -0.998), 1.996, 1.996,
                                    boxstyle="square,pad=0",
                                    linewidth=0.6, edgecolor=RULE_RGBA,
                                    facecolor="none", zorder=10)
    ax.add_patch(rect)
    save(fig, "gojo_infinity.png")


# ══════════════════════════════════════════════════════════════════════════
# 2. mobius_rickness
#    A topological portal ring (one-sided band / Möbius cross-section)
#    with a sign-changing field gradient inside it.
# ══════════════════════════════════════════════════════════════════════════
def emblem_mobius():
    fig, ax = new_fig()

    # Background: field heatmap on a flat disc
    res = 400
    xs = np.linspace(-1, 1, res)
    ys = np.linspace(-1, 1, res)
    X, Y = np.meshgrid(xs, ys)
    R = np.sqrt(X**2 + Y**2)

    # Rickness field: cos(u) + 0.4v cos(u/2) mapped to polar
    u = np.arctan2(Y, X)
    v = R - 0.5  # offset so zero-set isn't at origin
    field = np.cos(u) + 0.4 * v * np.cos(u / 2) + 0.2 * np.sin(u)
    # Mask outside disk
    field[R > 0.88] = np.nan

    cmap = matplotlib.colors.LinearSegmentedColormap.from_list(
        "ink_cream",
        [(0.0, "#dbd5c6"), (0.42, CREAM), (0.50, CREAM), (0.58, "#e8e3d8"), (1.0, INK_2)],
    )
    ax.contourf(X, Y, field, levels=40, cmap=cmap, alpha=0.55, zorder=1)

    # Zero-set contour — the Central Finite Curve on Möbius
    cs = ax.contour(X, Y, field, levels=[0], colors=[INK], linewidths=[2.2], zorder=4)
    ax.contour(X, Y, field, levels=[0], colors=[ACCENT], linewidths=[0.8], zorder=5)

    # Portal ring: two offset ellipses giving depth
    for lw, col, alpha in [(12, CREAM, 1.0), (3.0, INK, 0.85), (1.0, ACCENT, 0.6)]:
        ell = mpatches.Ellipse((0, 0), 1.72, 1.72, linewidth=lw,
                                edgecolor=col, facecolor="none", alpha=alpha, zorder=6)
        ax.add_patch(ell)

    # Inner ellipse (depth effect)
    ell_inner = mpatches.Ellipse((0.05, 0.05), 1.48, 1.32,
                                  linewidth=1.0, edgecolor=INK_2,
                                  facecolor="none", alpha=0.30, zorder=6,
                                  linestyle="--")
    ax.add_patch(ell_inner)

    # Möbius seam tick marks
    for angle_deg in range(0, 360, 30):
        angle = math.radians(angle_deg)
        r_o, r_i = 0.87, 0.80
        x0, y0 = r_i * math.cos(angle), r_i * math.sin(angle)
        x1, y1 = r_o * math.cos(angle), r_o * math.sin(angle)
        ax.plot([x0, x1], [y0, y1], color=INK, lw=0.6, alpha=0.35, zorder=7)

    # Labels
    ax.text(0, -0.93, "MÖBIUS / RICKNESS", ha="center", va="bottom",
            fontsize=7, fontweight="bold", color=MUTED, fontfamily="monospace")
    ax.text(0, -0.985, "Central Finite Curve  ·  K < 0 everywhere",
            ha="center", va="bottom", fontsize=5.5, color=MUTED, fontfamily="monospace")

    rect = mpatches.FancyBboxPatch((-0.998, -0.998), 1.996, 1.996,
                                    boxstyle="square,pad=0",
                                    linewidth=0.6, edgecolor=RULE_RGBA,
                                    facecolor="none", zorder=10)
    ax.add_patch(rect)
    save(fig, "mobius_rickness.png")


# ══════════════════════════════════════════════════════════════════════════
# 3. central_finite_curve
#    Portal-gun ring with a MCMC random-walk trace along the Rickness ridge.
# ══════════════════════════════════════════════════════════════════════════
def emblem_central_finite():
    fig, ax = new_fig()
    rng = np.random.default_rng(137)

    # Dim concentric grid (multiverse coordinates)
    for r in np.arange(0.15, 0.95, 0.15):
        circle = plt.Circle((0, 0), r, color=INK, fill=False, lw=0.4, alpha=0.12, zorder=1)
        ax.add_patch(circle)
    for angle_deg in range(0, 360, 30):
        angle = math.radians(angle_deg)
        ax.plot([0, 0.90 * math.cos(angle)], [0, 0.90 * math.sin(angle)],
                color=INK, lw=0.3, alpha=0.12, zorder=1)

    # Simulate MCMC walk along a high-Rickness curve
    n_pts = 320
    theta = 0.0
    walk_x, walk_y = [0.72], [0.0]
    for _ in range(n_pts - 1):
        dtheta = rng.normal(0, 0.09)
        dr = rng.normal(0, 0.012)
        theta += dtheta
        r = np.clip(walk_x[-1] ** 2 + walk_y[-1] ** 2, 0.4, 0.82) ** 0.5 + dr
        r = np.clip(r, 0.60, 0.82)
        walk_x.append(r * math.cos(theta))
        walk_y.append(r * math.sin(theta))

    # Glow halo
    ax.plot(walk_x, walk_y, color=CREAM, lw=7, alpha=0.7, zorder=2, solid_capstyle="round")
    # Main curve
    ax.plot(walk_x, walk_y, color=INK, lw=1.8, alpha=0.85, zorder=3, solid_capstyle="round")
    ax.plot(walk_x, walk_y, color=ACCENT, lw=0.6, alpha=0.70, zorder=4, solid_capstyle="round")

    # Walk nodes
    ax.scatter(walk_x[::20], walk_y[::20], s=6, color=INK_2, zorder=5, alpha=0.50)

    # Portal ring
    for lw, col, alpha in [(10, CREAM, 1.0), (2.5, INK, 0.85)]:
        ell = mpatches.Ellipse((0, 0), 1.78, 1.78, linewidth=lw,
                                edgecolor=col, facecolor="none", alpha=alpha, zorder=6)
        ax.add_patch(ell)
    ell_acc = mpatches.Ellipse((0, 0), 1.78, 1.78, linewidth=0.8,
                                edgecolor=ACCENT, facecolor="none", alpha=0.55, zorder=7)
    ax.add_patch(ell_acc)

    ax.text(0, -0.93, "CENTRAL FINITE CURVE", ha="center", va="bottom",
            fontsize=7, fontweight="bold", color=MUTED, fontfamily="monospace")
    ax.text(0, -0.985, "Near-maximal Rickness ridge  ·  MCMC walk",
            ha="center", va="bottom", fontsize=5.5, color=MUTED, fontfamily="monospace")

    rect = mpatches.FancyBboxPatch((-0.998, -0.998), 1.996, 1.996,
                                    boxstyle="square,pad=0",
                                    linewidth=0.6, edgecolor=RULE_RGBA,
                                    facecolor="none", zorder=10)
    ax.add_patch(rect)
    save(fig, "central_finite_curve.png")


# ══════════════════════════════════════════════════════════════════════════
# 4. calabi_yau_latent — torus cross-sections in a 2x2 grid
# ══════════════════════════════════════════════════════════════════════════
def emblem_calabi():
    fig, ax = new_fig()

    # Torus outline: parametric (R + r cos v) cos u
    u = np.linspace(0, 2 * math.pi, 400)
    v = np.linspace(0, 2 * math.pi, 80)
    R_big, r_small = 0.52, 0.22

    for vi in v[::6]:
        xc = (R_big + r_small * math.cos(vi)) * np.cos(u)
        yc = (R_big + r_small * math.cos(vi)) * np.sin(u)
        zc = r_small * math.sin(vi)
        alpha = 0.35 * (1 - abs(vi / math.pi - 1)) + 0.08
        lw = 0.5 if abs(vi - math.pi) > 0.5 else 0.8
        ax.plot(xc * 0.85, yc * 0.85, color=INK, lw=lw, alpha=alpha, zorder=2)

    # Outer and inner circles
    for r2, lw2, alpha2 in [(0.74, 2.0, 0.7), (0.30, 1.4, 0.6)]:
        c = plt.Circle((0, 0), r2, color=INK, fill=False, lw=lw2, alpha=alpha2, zorder=3)
        ax.add_patch(c)

    # Accent wrap line
    wrap_u = np.linspace(0, 4 * math.pi, 600)
    xw = 0.52 * np.cos(wrap_u * 0.5)
    yw = 0.52 * np.sin(wrap_u * 0.5) + 0.22 * np.sin(wrap_u * 2)
    ax.plot(xw * 0.85, yw * 0.85, color=ACCENT, lw=1.0, alpha=0.60, zorder=4)

    # Seam markers
    for angle_deg in [0, 90, 180, 270]:
        angle = math.radians(angle_deg)
        x0, y0 = 0.62 * math.cos(angle), 0.62 * math.sin(angle)
        ax.plot(x0, y0, "o", color=ACCENT, ms=4, zorder=5, alpha=0.60)

    ax.text(0, -0.93, "CALABI–YAU LATENT", ha="center", va="bottom",
            fontsize=7, fontweight="bold", color=MUTED, fontfamily="monospace")
    ax.text(0, -0.985, "Rᵏ × Tᵐ  ·  periodic compactification",
            ha="center", va="bottom", fontsize=5.5, color=MUTED, fontfamily="monospace")
    rect = mpatches.FancyBboxPatch((-0.998, -0.998), 1.996, 1.996,
                                    boxstyle="square,pad=0",
                                    linewidth=0.6, edgecolor=RULE_RGBA,
                                    facecolor="none", zorder=10)
    ax.add_patch(rect)
    save(fig, "calabi_yau_latent.png")


# ══════════════════════════════════════════════════════════════════════════
# 5. domain_expansion — a Laplace field on a grid
# ══════════════════════════════════════════════════════════════════════════
def emblem_domain():
    fig, ax = new_fig()

    # Laplace potential field lines (simulate with simple radial + sin)
    theta_f = np.linspace(0, 2 * math.pi, 300)
    for r2 in np.arange(0.10, 0.90, 0.12):
        xc = r2 * np.cos(theta_f)
        yc = r2 * np.sin(theta_f)
        alpha = 0.22 + 0.18 * (1 - r2)
        ax.plot(xc, yc, color=INK_2, lw=0.5, alpha=alpha, zorder=1)

    # Field isolines at angles
    n_lines = 16
    for i in range(n_lines):
        ang = 2 * math.pi * i / n_lines
        xs = np.linspace(0, 0.88 * math.cos(ang), 60)
        ys = np.linspace(0, 0.88 * math.sin(ang), 60)
        ax.plot(xs, ys, color=INK_2, lw=0.4, alpha=0.15, zorder=1)

    # Boundary box (the closed domain)
    box = mpatches.FancyBboxPatch((-0.72, -0.72), 1.44, 1.44,
                                   boxstyle="square,pad=0",
                                   linewidth=2.0, edgecolor=INK,
                                   facecolor="none", alpha=0.7, zorder=5)
    ax.add_patch(box)
    box2 = mpatches.FancyBboxPatch((-0.62, -0.62), 1.24, 1.24,
                                    boxstyle="square,pad=0",
                                    linewidth=0.8, edgecolor=ACCENT,
                                    facecolor="none", alpha=0.40, zorder=6)
    ax.add_patch(box2)

    # Central intensity dot
    ax.plot(0, 0, "o", color=INK, ms=10, zorder=7, alpha=0.9)
    ax.plot(0, 0, "o", color=ACCENT, ms=4, zorder=8, alpha=1.0)

    ax.text(0, -0.93, "DOMAIN EXPANSION", ha="center", va="bottom",
            fontsize=7, fontweight="bold", color=MUTED, fontfamily="monospace")
    ax.text(0, -0.985, "∇²u = 0  ·  coupled constraint solver",
            ha="center", va="bottom", fontsize=5.5, color=MUTED, fontfamily="monospace")
    rect = mpatches.FancyBboxPatch((-0.998, -0.998), 1.996, 1.996,
                                    boxstyle="square,pad=0",
                                    linewidth=0.6, edgecolor=RULE_RGBA,
                                    facecolor="none", zorder=10)
    ax.add_patch(rect)
    save(fig, "domain_expansion.png")


# ══════════════════════════════════════════════════════════════════════════
# 6. divergence_meter — nixie tube digit silhouette
# ══════════════════════════════════════════════════════════════════════════
def emblem_divergence():
    fig, ax = new_fig()
    ax.set_xlim(-1.1, 1.1); ax.set_ylim(-0.7, 0.7)

    # Nixie tube body
    tube = mpatches.FancyBboxPatch((-0.95, -0.55), 1.90, 1.10,
                                    boxstyle="round,pad=0.05",
                                    linewidth=1.8, edgecolor=INK,
                                    facecolor=CREAM, alpha=0.95, zorder=2)
    ax.add_patch(tube)

    # Seven-segment display drawing for "1.048596" (abbreviated)
    def seg(x0, y0, x1, y1, on=True):
        c = INK if on else MUTED
        alpha = 0.85 if on else 0.08
        ax.plot([x0, x1], [y0, y1], color=c, lw=3.5, alpha=alpha,
                solid_capstyle="round", zorder=4)

    # Digits as simplified vertical bars — stylised nixie look
    digit_x = [-0.78, -0.56, -0.44, -0.28, -0.12, 0.08, 0.24, 0.40, 0.58, 0.74]
    chars    = ["1",   ".",   "0",   "4",   "8",   "5",   "9",   "6"]
    col_idx  = 0
    for i, char in enumerate(chars):
        x = digit_x[i] if i < len(digit_x) else 0
        if char == ".":
            ax.plot(x, -0.28, "o", color=ACCENT, ms=5, zorder=5)
        else:
            # Top
            seg(x - 0.08, 0.30, x + 0.08, 0.30, char in "02356789")
            # Top-left
            seg(x - 0.09, 0.05, x - 0.09, 0.28, char in "045689")
            # Top-right
            seg(x + 0.09, 0.05, x + 0.09, 0.28, char in "01234789")
            # Middle
            seg(x - 0.08, 0.03, x + 0.08, 0.03, char in "2345689")
            # Bottom-left
            seg(x - 0.09, -0.28, x - 0.09, 0.02, char in "02689")
            # Bottom-right
            seg(x + 0.09, -0.28, x + 0.09, 0.02, char in "01345679")
            # Bottom
            seg(x - 0.08, -0.30, x + 0.08, -0.30, char in "02356789")

    ax.text(0, -0.60, "DIVERGENCE METER  ·  SHA-256 worldline hash",
            ha="center", va="center", fontsize=5.5, color=MUTED, fontfamily="monospace")
    rect = mpatches.FancyBboxPatch((-1.09, -0.69), 2.18, 1.38,
                                    boxstyle="square,pad=0",
                                    linewidth=0.6, edgecolor=RULE_RGBA,
                                    facecolor="none", zorder=10)
    ax.add_patch(rect)
    save(fig, "divergence-meter.png")


# ══════════════════════════════════════════════════════════════════════════
# 7. padic_embeddings — ultrametric tree
# ══════════════════════════════════════════════════════════════════════════
def emblem_padic():
    fig, ax = new_fig()

    def draw_tree(x, y, dx, dy, depth, max_depth=4):
        if depth > max_depth:
            return
        alpha = 0.85 - 0.15 * depth
        lw = 2.0 - 0.3 * depth
        color = INK if depth % 2 == 0 else INK_2
        ax.plot([x, x + dx], [y, y + dy], color=color, lw=lw, alpha=alpha, zorder=3)
        # p=2: binary split
        rot = 0.6 - 0.08 * depth
        cx, cy = math.cos(rot), math.sin(rot)
        sx, sy = math.sin(rot), -math.cos(rot)
        scale = 0.55
        nx, ny = dx * scale, dy * scale
        draw_tree(x + dx, y + dy, nx * cx - ny * sx, nx * sx + ny * cy,
                  depth + 1, max_depth)
        draw_tree(x + dx, y + dy, nx * cx + ny * sx, -nx * sx + ny * cy,
                  depth + 1, max_depth)

    # Root
    draw_tree(0, -0.8, 0, 0.55, 0, max_depth=4)

    # p-adic distance annotation
    for i, (label, y2, x2) in enumerate([
        ("|8|₂=1/8", 0.50, -0.50), ("|4|₂=1/4", 0.22, -0.50),
        ("|2|₂=1/2", -0.05, -0.50), ("|1|₂=1", -0.30, -0.50),
    ]):
        ax.text(x2, y2, label, fontsize=5, color=MUTED, fontfamily="monospace",
                ha="right", va="center", zorder=5, alpha=0.70)

    ax.text(0, -0.93, "p-ADIC EMBEDDINGS", ha="center", va="bottom",
            fontsize=7, fontweight="bold", color=MUTED, fontfamily="monospace")
    ax.text(0, -0.985, "ultrametric tree  ·  |x|_p = p^(-v_p(x))",
            ha="center", va="bottom", fontsize=5.5, color=MUTED, fontfamily="monospace")
    rect = mpatches.FancyBboxPatch((-0.998, -0.998), 1.996, 1.996,
                                    boxstyle="square,pad=0",
                                    linewidth=0.6, edgecolor=RULE_RGBA,
                                    facecolor="none", zorder=10)
    ax.add_patch(rect)
    save(fig, "padic-embeddings.png")


# ══════════════════════════════════════════════════════════════════════════
# 8. madoka_entropy — entropy ledger
# ══════════════════════════════════════════════════════════════════════════
def emblem_madoka():
    fig, ax = new_fig()

    # Rising entropy curve
    t_arr = np.linspace(0, 1, 200)
    S_total = 0.1 + 0.7 * t_arr ** 0.7
    S_local = 0.5 - 0.3 * t_arr
    S_global = S_total - S_local

    ax.plot(t_arr * 1.6 - 0.8, S_total * 1.4 - 0.72, color=INK, lw=2.2, alpha=0.85, label="S_total", zorder=4)
    ax.plot(t_arr * 1.6 - 0.8, S_local * 1.4 - 0.72, color=ACCENT, lw=1.4, alpha=0.70, label="S_local", zorder=3, linestyle="--")
    ax.plot(t_arr * 1.6 - 0.8, S_global * 1.4 - 0.72, color=MUTED, lw=1.0, alpha=0.55, label="S_global", zorder=2, linestyle=":")

    # dS/dt > 0 annotation arrow
    ax.annotate("", xy=(0.40, 0.50), xytext=(0.05, 0.30),
                arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.2), zorder=5)
    ax.text(0.42, 0.52, "ΔS≥0", fontsize=7, color=INK, fontfamily="monospace",
            va="bottom", zorder=5)

    # Wish impulses (vertical drops in S_local)
    for tx in [0.18, 0.42, 0.68]:
        ax.axvline(tx * 1.6 - 0.8, color=ACCENT, lw=0.7, alpha=0.30, linestyle="--", zorder=1)

    ax.text(0, -0.93, "MADOKA ENTROPY", ha="center", va="bottom",
            fontsize=7, fontweight="bold", color=MUTED, fontfamily="monospace")
    ax.text(0, -0.985, "ΔS_global = k·x  (k>1)  ·  closed system",
            ha="center", va="bottom", fontsize=5.5, color=MUTED, fontfamily="monospace")
    rect = mpatches.FancyBboxPatch((-0.998, -0.998), 1.996, 1.996,
                                    boxstyle="square,pad=0",
                                    linewidth=0.6, edgecolor=RULE_RGBA,
                                    facecolor="none", zorder=10)
    ax.add_patch(rect)
    save(fig, "madoka-entropy.png")


# ══════════════════════════════════════════════════════════════════════════
# Run all
# ══════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print("Generating emblems...")
    emblem_gojo()
    emblem_mobius()
    emblem_central_finite()
    emblem_calabi()
    emblem_domain()
    emblem_divergence()
    emblem_padic()
    emblem_madoka()
    print(f"Done — written to {OUT}")
