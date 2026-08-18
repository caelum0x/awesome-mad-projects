"""Deterministic visualisations for the Mobius-Rickness curvature field.

ASCII renderers are ALWAYS available: they delegate to
:mod:`commons.adapters.ascii_art` and use only the standard library, so every
function returns a non-empty, byte-for-byte deterministic ``str`` that is safe to
pin in tests and to print in any terminal.

Three canonical pictures / tables are rendered:
    * :func:`render_rickness_sign_map` -- a ``+/-`` region map of the
      sign-changing Rickness ``R(u, v)`` with the traced zero curve overlaid
      (``'O'`` marks the Central Finite Curve ``R^{-1}(0)``).
    * :func:`render_k_rick_heatmap` -- the weighted curvature field
      ``K_Rick = K * R`` as a shaded grid (it straddles zero because ``K < 0``
      strictly while ``R`` changes sign).
    * :func:`render_curvature_table` -- the reproduced original sample table
      ``(K, R_naive, K_Rick_naive)`` showing why the legacy positive weighting
      had NO zero.

OPTIONAL matplotlib PNG exports are provided behind the ``commons.core.optional``
matplotlib guard:
    * :func:`save_curve_png` -- a 3D scatter of pre-traced curve points on the strip.
    * :func:`save_strip_3d_png` -- the Mobius surface with the traced Central Finite
      Curve ``R^{-1}(0)`` overlaid as a 3D line.
    * :func:`save_krick_heatmap_png` -- the ``K_Rick(u, v)`` field as a filled
      heatmap with the ``R = 0`` (equivalently ``K_Rick = 0``) zero curve contour.
    * :func:`save_ridge_png` -- the surface with the SCMS / Eberly ridge of maximal
      Rickness overlaid (guarded when numpy / the ridge subpackage is unavailable).
Each is DEFERRED: with no matplotlib installed it raises a clear
:class:`OptionalDependencyError` instead of failing at import time, so the module
stays importable with the standard library alone. matplotlib always uses the
headless ``Agg`` backend, so the exports render without a display.

This is an adapter: it imports ``core`` and ``commons.adapters`` but is never
imported by ``core``.
"""

from __future__ import annotations

import math
from typing import List, Sequence, Tuple

from commons.adapters.ascii_art import render_heatmap, render_sign_map
from commons.core.optional import try_import

from mobius_rickness.core import (
    U_MAX,
    U_MIN,
    V_MAX,
    V_MIN,
    evaluate_grid,
    flatten_columns,
    gaussian_curvature,
    linspace,
    rickness,
    rickness_naive,
    surface,
    trace_columns,
)

# Sample grid used by the reproduced curvature table (mirrors the original demo).
_SAMPLE_US: Tuple[Tuple[str, float], ...] = (
    ("0", 0.0),
    ("pi/2", math.pi / 2.0),
    ("pi", math.pi),
    ("3pi/2", 3.0 * math.pi / 2.0),
    ("7pi/4", 7.0 * math.pi / 4.0),
)
_SAMPLE_VS: Tuple[float, ...] = (0.0, 0.25, -0.25)

# Default ASCII grid resolutions (compact, terminal-friendly, deterministic).
_DEFAULT_N_U = 61
_DEFAULT_N_V = 17
_DEFAULT_WIDTH = 60


class OptionalDependencyError(RuntimeError):
    """Raised when an optional viz backend (e.g. matplotlib) is unavailable.

    The ASCII renderers never raise this; only the deferred PNG export does, and
    only when the caller explicitly requests it without the dependency.
    """


# ---------------------------------------------------------------------------
# ASCII sign map: R with the Central Finite Curve overlaid
# ---------------------------------------------------------------------------

def render_rickness_sign_map(
    n_u: int = _DEFAULT_N_U,
    n_v: int = _DEFAULT_N_V,
    *,
    width: int = _DEFAULT_WIDTH,
) -> str:
    """ASCII ``+/-`` sign map of ``R(u, v)`` with the zero curve overlaid.

    ``'+'`` marks the Rick-positive region, ``'-'`` the Rick-negative region, and
    ``'O'`` any cell on or adjacent to a sign change -- i.e. the traced Central
    Finite Curve ``R^{-1}(0)``. Rows are ``v`` (top row = ``V_MAX``), columns are
    ``u`` over ``[0, 2*pi]``. Deterministic and non-empty.
    """
    us = linspace(U_MIN, U_MAX, n_u)
    vs = linspace(V_MIN, V_MAX, n_v)
    return render_sign_map(
        rickness,
        us,
        vs,
        width=width,
        title="Rickness R(u,v) sign map  ('O' = Central Finite Curve R^-1(0))",
    )


# ---------------------------------------------------------------------------
# ASCII heatmap: the weighted K_Rick field
# ---------------------------------------------------------------------------

def render_k_rick_heatmap(
    n_u: int = _DEFAULT_N_U,
    n_v: int = _DEFAULT_N_V,
    *,
    width: int = _DEFAULT_WIDTH,
) -> str:
    """ASCII shaded heatmap of ``K_Rick(u, v) = K(u, v) * R(u, v)``.

    Because ``K < 0`` strictly on the strip while ``R`` changes sign, the field
    straddles zero. Rows are ``v`` (labelled), columns are ``u``. Deterministic
    and non-empty.
    """
    grid = evaluate_grid(n_u=n_u, n_v=n_v)
    return render_heatmap(
        grid.K_Rick,
        row_labels=grid.vs,
        width=width,
        title="K_Rick(u,v) = K*R heatmap  (K<0 strictly, R sign-changing)",
    )


# ---------------------------------------------------------------------------
# Reproduced original curvature sample table
# ---------------------------------------------------------------------------

def render_curvature_table() -> str:
    """Reproduce the original ``(K, R_naive, K_Rick_naive)`` sample table.

    Uses the LEGACY strictly-positive :func:`rickness_naive` (``+1.5`` constant),
    demonstrating that every ``K < 0`` and every ``R_naive > 0`` forces
    ``K_Rick_naive < 0`` with NO zero -- the exact reason the earlier "Central
    Finite Curve" was only a minimal-``|K_Rick|`` cop-out rather than a real
    zero set. Deterministic and non-empty.
    """
    rule = "-" * 64
    lines: List[str] = [
        "Original curvature sample table  (K, R_naive, K_Rick = K * R_naive)",
        "R_naive = 1.5 + cos(u) + 0.4 v cos(u/2) + 0.2 sin(u)  (> 0 always)",
        rule,
        f"{'u':>7} {'v':>7} {'K':>14} {'R_naive':>10} {'K_Rick':>14}",
        rule,
    ]
    for label, u in _SAMPLE_US:
        for v in _SAMPLE_VS:
            k = gaussian_curvature(u, v)
            r = rickness_naive(u, v)
            kr = k * r
            lines.append(
                f"{label:>7} {v:>+7.2f} {k:>14.6f} {r:>10.4f} {kr:>14.6f}"
            )
        lines.append(rule)
    lines.append("Every K < 0 and every R_naive > 0  =>  K_Rick < 0 with NO zero.")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Optional 3D PNG export -- DEFERRED behind the matplotlib guard
# ---------------------------------------------------------------------------

# Default PNG grid resolutions (surface sampling); denser than the ASCII grids.
_PNG_N_U = 120
_PNG_N_V = 25


def _require_pyplot():
    """Return matplotlib's ``pyplot`` on the headless ``Agg`` backend.

    matplotlib is reached exclusively through
    :func:`commons.core.optional.try_import`, never imported at module top level,
    so importing this module needs only the standard library. Raises
    :class:`OptionalDependencyError` (deferred behaviour) when matplotlib is
    unavailable -- it never silently degrades.
    """
    matplotlib = try_import("matplotlib")
    if matplotlib is None:
        raise OptionalDependencyError(
            "PNG export requires matplotlib, which is not installed. "
            "Install the optional 'viz' extra, or use the ASCII renderers "
            "(render_rickness_sign_map / render_k_rick_heatmap), which need no "
            "dependencies."
        )
    matplotlib.use("Agg")  # headless, deterministic, no display needed
    pyplot = try_import("matplotlib.pyplot")
    if pyplot is None:  # pragma: no cover - matplotlib without pyplot is degenerate
        raise OptionalDependencyError("matplotlib is present but pyplot is unavailable")
    return pyplot


def _require_pyplot_3d():
    """Return ``pyplot`` with the 3D projection registered (via mplot3d)."""
    pyplot = _require_pyplot()
    # Importing mplot3d registers the 'projection="3d"' axes as a side effect.
    if try_import("mpl_toolkits.mplot3d") is None:  # pragma: no cover - degenerate
        raise OptionalDependencyError("matplotlib is present but mplot3d is unavailable")
    return pyplot


def _surface_grids(n_u: int, n_v: int):
    """Return the strip surface ``(X, Y, Z)`` as three grids for ``plot_surface``."""
    us = linspace(U_MIN, U_MAX, n_u)
    vs = linspace(V_MIN, V_MAX, n_v)
    xs = [[surface(u, v)[0] for u in us] for v in vs]
    ys = [[surface(u, v)[1] for u in us] for v in vs]
    zs = [[surface(u, v)[2] for u in us] for v in vs]
    return _as_grid(xs), _as_grid(ys), _as_grid(zs)


def _as_grid(rows: List[List[float]]):
    """Return a numpy 2-D array if numpy is present, else the nested list.

    matplotlib's ``plot_surface`` accepts either; numpy is only used when it is
    already available so the guard stays honest (never a hard import).
    """
    numpy = try_import("numpy")
    if numpy is None:  # pragma: no cover - only when numpy absent but mpl present
        return rows
    return numpy.asarray(rows)


def save_curve_png(
    points: Sequence,
    path: str,
    *,
    n_u: int = 80,
    n_v: int = 20,
    title: str = "Central Finite Curve = R^-1(0) on the Mobius strip",
) -> str:
    """Write a 3D PNG scattering pre-traced curve points on the Mobius strip.

    ``points`` is a sequence of objects exposing ``.x/.y/.z`` (e.g.
    :class:`mobius_rickness.core.CurvePoint`). DEFERRED: raises
    :class:`OptionalDependencyError` when matplotlib is unavailable. Returns
    ``path`` on success.
    """
    pyplot = _require_pyplot_3d()
    grid_x, grid_y, grid_z = _surface_grids(n_u, n_v)

    figure = pyplot.figure(figsize=(7, 6))
    axes = figure.add_subplot(111, projection="3d")
    axes.plot_surface(grid_x, grid_y, grid_z, alpha=0.3, color="gray", linewidth=0)
    if points:
        axes.scatter(
            [p.x for p in points],
            [p.y for p in points],
            [p.z for p in points],
            color="red",
            s=8,
            label="Central Finite Curve",
        )
        axes.legend()
    axes.set_title(title)
    figure.tight_layout()
    figure.savefig(path, dpi=120)
    pyplot.close(figure)
    return path


def _traced_cfc_points(n_u: int = 120, n_v_samples: int = 200) -> List:
    """Trace the zero set ``R^{-1}(0)`` and return the lifted 3D curve points."""
    return flatten_columns(trace_columns(n_u=n_u, n_v_samples=n_v_samples))


def save_strip_3d_png(
    path: str,
    *,
    n_u: int = _PNG_N_U,
    n_v: int = _PNG_N_V,
    title: str = "Mobius strip with Central Finite Curve R^-1(0)",
) -> str:
    """Write the Mobius surface with the traced ``R^{-1}(0)`` curve as a 3D line.

    The strip is drawn with ``plot_surface``; the Central Finite Curve is traced
    fresh from the pure core (:func:`trace_columns`) and overlaid as a red 3D line.
    DEFERRED: raises :class:`OptionalDependencyError` when matplotlib is absent.
    Returns ``path`` on success.
    """
    pyplot = _require_pyplot_3d()
    grid_x, grid_y, grid_z = _surface_grids(n_u, n_v)
    points = _traced_cfc_points()

    figure = pyplot.figure(figsize=(7, 6))
    axes = figure.add_subplot(111, projection="3d")
    axes.plot_surface(grid_x, grid_y, grid_z, alpha=0.3, color="gray", linewidth=0)
    if points:
        axes.plot(
            [p.x for p in points],
            [p.y for p in points],
            [p.z for p in points],
            color="red",
            linewidth=2.0,
            label="Central Finite Curve R^-1(0)",
        )
        axes.legend()
    axes.set_title(title)
    figure.tight_layout()
    figure.savefig(path, dpi=120)
    pyplot.close(figure)
    return path


def save_krick_heatmap_png(
    path: str,
    *,
    n_u: int = _PNG_N_U,
    n_v: int = _PNG_N_V,
    title: str = "K_Rick(u,v) = K*R with zero curve R^-1(0)",
) -> str:
    """Write the ``K_Rick(u, v)`` field as a filled heatmap with the zero contour.

    The field is sampled by the pure core (:func:`evaluate_grid`); the zero curve
    is drawn as the ``R = 0`` contour (equivalently ``K_Rick = 0``, since ``K < 0``
    strictly). DEFERRED: raises :class:`OptionalDependencyError` when matplotlib is
    absent. Returns ``path`` on success.
    """
    pyplot = _require_pyplot()
    numpy = try_import("numpy")
    if numpy is None:  # pragma: no cover - matplotlib depends on numpy in practice
        raise OptionalDependencyError(
            "the K_Rick heatmap requires numpy, which is not installed."
        )
    grid = evaluate_grid(n_u=n_u, n_v=n_v)
    mesh_u, mesh_v = numpy.meshgrid(numpy.asarray(grid.us), numpy.asarray(grid.vs))
    k_rick_field = numpy.asarray(grid.K_Rick)
    r_field = numpy.asarray(grid.R)

    figure = pyplot.figure(figsize=(8, 4))
    axes = figure.add_subplot(111)
    mesh = axes.pcolormesh(mesh_u, mesh_v, k_rick_field, cmap="RdBu", shading="auto")
    figure.colorbar(mesh, ax=axes, label="K_Rick = K * R")
    contour = axes.contour(mesh_u, mesh_v, r_field, levels=[0.0], colors="black")
    axes.clabel(contour, inline=True, fontsize=8, fmt="R=0")
    axes.set_xlabel("u")
    axes.set_ylabel("v")
    axes.set_title(title)
    figure.tight_layout()
    figure.savefig(path, dpi=120)
    pyplot.close(figure)
    return path


def save_ridge_png(
    path: str,
    *,
    n_u: int = _PNG_N_U,
    n_v: int = _PNG_N_V,
    ridge_n_u: int = 24,
    ridge_n_v: int = 5,
    title: str = "Mobius strip with SCMS ridge of maximal Rickness",
) -> str:
    """Write the Mobius surface with the SCMS / Eberly ridge overlaid as a 3D line.

    The ridge is traced by :func:`mobius_rickness.ridge.trace_mobius_ridge` (the
    SECOND Central Finite Curve reading -- the crest of maximal Rickness, distinct
    from the ``R^{-1}(0)`` wall). DEFERRED on matplotlib: raises
    :class:`OptionalDependencyError` when matplotlib is absent. The ridge overlay is
    additionally GUARDED on numpy / the ridge subpackage: if numpy is unavailable
    the strip is still rendered (surface only) rather than failing. Returns ``path``.
    """
    pyplot = _require_pyplot_3d()
    grid_x, grid_y, grid_z = _surface_grids(n_u, n_v)
    ridge_points = _try_trace_ridge(ridge_n_u, ridge_n_v)

    figure = pyplot.figure(figsize=(7, 6))
    axes = figure.add_subplot(111, projection="3d")
    axes.plot_surface(grid_x, grid_y, grid_z, alpha=0.3, color="gray", linewidth=0)
    if ridge_points:
        axes.plot(
            [p.x for p in ridge_points],
            [p.y for p in ridge_points],
            [p.z for p in ridge_points],
            color="darkorange",
            linewidth=2.0,
            marker="o",
            markersize=3,
            label="SCMS ridge (max Rickness)",
        )
        axes.legend()
    axes.set_title(title)
    figure.tight_layout()
    figure.savefig(path, dpi=120)
    pyplot.close(figure)
    return path


def _try_trace_ridge(n_u: int, n_v: int) -> List:
    """Trace the SCMS ridge, returning ``[]`` when numpy / the ridge dep is absent.

    The ridge backend needs numpy; when it is missing it raises the ridge subpackage's
    :class:`OptionalDependencyError`, which we swallow here so the strip still renders
    (the numpy guard the caller asked for), rather than aborting the whole figure.
    """
    if try_import("numpy") is None:
        return []
    from mobius_rickness.ridge import (  # local import: keeps viz importable w/o numpy
        OptionalDependencyError as RidgeOptionalDependencyError,
        trace_mobius_ridge,
    )

    try:
        return list(trace_mobius_ridge(n_u=n_u, n_v=n_v))
    except RidgeOptionalDependencyError:  # pragma: no cover - numpy present here
        return []
