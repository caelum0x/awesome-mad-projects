"""Deterministic visualisations for the four Infinity lenses.

ASCII renderers are ALWAYS available: they delegate to
:mod:`commons.adapters.ascii_art` and use only the standard library, so every
function returns a non-empty, byte-for-byte deterministic ``str`` that is safe
to pin in tests and to print in any terminal.

Three canonical pictures are rendered:
    * :func:`render_zeno_convergence` -- the crossed-fraction series
      ``S_n = 1 - (1/2)^n`` climbing to its limit ``1``.
    * :func:`render_omega_blowup` -- the conformal factor ``Omega(x)`` erupting
      toward ``+infinity`` as ``x -> x_gojo`` (the Riemannian metric blow-up).
    * :func:`render_cover_convergence` -- the total covering length
      ``sum eps/2^n`` shrinking down onto ``eps`` (Lebesgue ``m(Z) = 0``).

OPTIONAL PNG exports are provided behind the ``commons.core.optional``
matplotlib guard -- one per lens:
    * :func:`save_series_convergence_png` -- Lens 1, ``S_n -> 1`` with residual.
    * :func:`save_covering_png`           -- Lens 2, covering length ``-> eps``.
    * :func:`save_metric_blowup_png`      -- Lens 3, ``Omega(x) -> +infinity``
      near Gojo, with the far/near step markers ``g(0.1)`` / ``g(0.8)``.
Plus the generic :func:`save_convergence_png` they build on. All are DEFERRED:
with no matplotlib installed they raise a clear :class:`OptionalDependencyError`
instead of failing at import time, so the module stays importable with the
standard library alone, and always render headless on the Agg backend.

This is an adapter: it imports ``core`` and ``commons.adapters`` but is never
imported by ``core``.
"""

from __future__ import annotations

from fractions import Fraction
from typing import Any, List, Sequence, Tuple

from commons.adapters.ascii_art import render_convergence, render_line_plot
from commons.core.optional import try_import

from gojo_infinity.core import (
    ConformalMetric,
    ConformalMetricND,
    X_GOJO,
    conformal_factor,
    metric_g11,
    partial_sum,
    residual,
    total_cover_length,
)

# Defaults chosen so every renderer produces a compact, readable block.
_DEFAULT_HEIGHT = 12


class OptionalDependencyError(RuntimeError):
    """Raised when an optional viz backend (e.g. matplotlib) is unavailable.

    The ASCII renderers never raise this; only the deferred PNG export does,
    and only when the caller explicitly requests it without the dependency.
    """


# ---------------------------------------------------------------------------
# Lens 1 -- Zeno partial sums converge to 1
# ---------------------------------------------------------------------------

def zeno_series_values(max_n: int) -> List[float]:
    """Return ``[S_1, ..., S_max_n]`` as floats, where ``S_n = 1 - (1/2)^n``.

    Delegates to the exact core :func:`gojo_infinity.core.partial_sum` and casts
    to ``float`` only for plotting. Raises :class:`ValueError` for ``max_n < 1``.
    """
    if max_n < 1:
        raise ValueError("max_n must be >= 1")
    return [float(partial_sum(n)) for n in range(1, max_n + 1)]


def render_zeno_convergence(max_n: int = 12, *, height: int = _DEFAULT_HEIGHT) -> str:
    """ASCII trace of ``S_n -> 1`` (the crossed fraction of the gap).

    The attacker's crossed fraction climbs monotonically toward the limit ``1``;
    the legend reports the final residual ``|S_max_n - 1| = (1/2)^max_n``.
    """
    ys = zeno_series_values(max_n)
    return render_convergence(
        ys, 1.0, height=height, title="Lens 1 - Zeno: S_n = 1 - (1/2)^n -> 1"
    )


# ---------------------------------------------------------------------------
# Lens 3 -- the conformal factor Omega(x) blows up toward the barrier
# ---------------------------------------------------------------------------

def omega_profile(
    x0: float, x1: float, samples: int, *, x_gojo: float = X_GOJO
) -> List[float]:
    """Sample ``Omega(x)`` at ``samples`` points on ``[x0, x1]`` (``x1 < x_gojo``).

    Points are evenly spaced and stop strictly short of the pole at ``x_gojo``.
    Raises :class:`ValueError` for ``samples < 2`` or a range touching the pole.
    """
    if samples < 2:
        raise ValueError("samples must be >= 2")
    if not (x0 < x1 < x_gojo):
        raise ValueError("require x0 < x1 < x_gojo (stay strictly before the pole)")
    step = (x1 - x0) / (samples - 1)
    return [conformal_factor(x0 + i * step, x_gojo=x_gojo) for i in range(samples)]


def render_omega_blowup(
    x0: float = 0.1,
    x1: float = 0.98,
    samples: int = 40,
    *,
    height: int = _DEFAULT_HEIGHT,
) -> str:
    """ASCII line chart of ``Omega(x)`` erupting toward ``+infinity`` near ``x_gojo``.

    Far from Gojo ``Omega ~ 1``; approaching the barrier the ``1/(x_gojo - x)``
    pole drives it up sharply -- the metric blow-up that makes felt distance
    diverge (Lens 3, FORMIDABLE).
    """
    ys = omega_profile(x0, x1, samples)
    return render_line_plot(
        ys, height=height, title="Lens 3 - Omega(x) blow-up toward x_gojo (metric)"
    )


# ---------------------------------------------------------------------------
# Lens 2 -- the total covering length shrinks onto eps
# ---------------------------------------------------------------------------

def cover_length_values(eps: Fraction, max_terms: int) -> List[float]:
    """Return partial total cover lengths ``[T_1, ..., T_max_terms]`` as floats.

    ``T_k = sum_{n=1}^k eps/2^n`` climbs toward ``eps`` from below. Uses the exact
    core :func:`gojo_infinity.core.total_cover_length`. Raises for ``max_terms < 1``.
    """
    if max_terms < 1:
        raise ValueError("max_terms must be >= 1")
    return [float(total_cover_length(eps, terms)) for terms in range(1, max_terms + 1)]


def render_cover_convergence(
    eps: Fraction = Fraction(1, 10),
    max_terms: int = 12,
    *,
    height: int = _DEFAULT_HEIGHT,
) -> str:
    """ASCII trace of the covering length ``sum eps/2^n -> eps`` (Lebesgue ``m(Z)=0``).

    The whole countable barrier ``Z`` is covered by intervals of total length
    that converges to the arbitrary ``eps``; since ``eps`` is free, the infimum
    -- hence ``m(Z)`` -- is ``0``.
    """
    ys = cover_length_values(eps, max_terms)
    return render_convergence(
        ys,
        float(eps),
        height=height,
        title=f"Lens 2 - cover length sum eps/2^n -> eps={float(eps):.3f}",
    )


# ---------------------------------------------------------------------------
# Optional PNG export -- DEFERRED behind the matplotlib guard
# ---------------------------------------------------------------------------

_PNG_HELP = (
    "PNG export requires matplotlib, which is not installed. Install the "
    "optional 'viz' extra (pip install -e '.[viz]'), or use the ASCII renderers "
    "(render_zeno_convergence / render_omega_blowup / render_cover_convergence), "
    "which need no dependencies."
)


def _load_pyplot() -> Any:
    """Return ``matplotlib.pyplot`` bound to the headless Agg backend, or raise.

    matplotlib is reached exclusively through
    :func:`commons.core.optional.try_import`, never imported at module top level,
    so importing this module needs only the standard library. When matplotlib is
    absent this raises :class:`OptionalDependencyError` (deferred behaviour); it
    never silently degrades. The Agg backend is selected so rendering is headless
    and deterministic with no display attached.
    """
    matplotlib = try_import("matplotlib")
    if matplotlib is None:
        raise OptionalDependencyError(_PNG_HELP)
    matplotlib.use("Agg")  # headless, deterministic, no display needed
    pyplot = try_import("matplotlib.pyplot")
    if pyplot is None:  # pragma: no cover - matplotlib without pyplot is degenerate
        raise OptionalDependencyError("matplotlib is present but pyplot is unavailable")
    return pyplot


def save_convergence_png(
    ys: Sequence[float],
    target: float,
    path: str,
    *,
    title: str = "convergence",
) -> str:
    """Write a PNG line chart of ``ys`` toward ``target`` to ``path`` (matplotlib).

    The generic OPTIONAL renderer underlying the lens-specific exporters below.
    matplotlib is imported lazily via :func:`_load_pyplot`; if it is unavailable
    this raises :class:`OptionalDependencyError`. Returns ``path`` on success.
    """
    if len(ys) == 0:
        raise ValueError("ys must be non-empty")
    pyplot = _load_pyplot()
    figure, axes = pyplot.subplots()
    axes.plot(range(len(ys)), list(ys), marker="o", label="series")
    axes.axhline(target, linestyle="--", label=f"target={target:g}")
    axes.set_title(title)
    axes.set_xlabel("n")
    axes.set_ylabel("value")
    axes.legend()
    figure.savefig(path)
    pyplot.close(figure)
    return path


# ---------------------------------------------------------------------------
# Lens-specific PNG exporters (each raises OptionalDependencyError w/o matplotlib)
# ---------------------------------------------------------------------------

def _omega_profile_xy(
    x0: float, x1: float, samples: int, *, x_gojo: float = X_GOJO
) -> Tuple[List[float], List[float]]:
    """Return ``(xs, ys)`` for ``Omega`` sampled on ``[x0, x1]`` (``x1 < x_gojo``).

    Companion to :func:`omega_profile` that also yields the abscissae, so the PNG
    renderer can plot ``Omega`` against physical position ``x`` (not just index).
    """
    ys = omega_profile(x0, x1, samples, x_gojo=x_gojo)
    step = (x1 - x0) / (samples - 1)
    xs = [x0 + i * step for i in range(samples)]
    return xs, ys


def save_metric_blowup_png(
    path: str,
    *,
    x0: float = 0.1,
    x1: float = 0.98,
    samples: int = 60,
    x_far: float = 0.1,
    x_near: float = 0.8,
) -> str:
    """Write Lens 3's ``Omega(x)`` metric blow-up toward ``x_gojo`` to ``path``.

    Plots the conformal factor ``Omega(x)`` erupting toward ``+infinity`` as
    ``x -> x_gojo`` (Gojo at ``x = 1``), with the calibration step markers at the
    FAR (``x_far``, ``g(0.1) ~ 1``) and NEAR (``x_near``, ``g(0.8) ~ 4.1``) points
    annotated with their metric value ``g = Omega^2``. matplotlib is imported
    lazily; raises :class:`OptionalDependencyError` when it is absent. Returns
    ``path`` on success.
    """
    xs, ys = _omega_profile_xy(x0, x1, samples)
    pyplot = _load_pyplot()
    figure, axes = pyplot.subplots()
    axes.plot(xs, ys, label="Omega(x) = 1 + lam*K/(x_g - x)")
    axes.axvline(X_GOJO, linestyle="--", color="grey", label=f"Gojo x_g={X_GOJO:g}")
    for label, x_mark in (("far", x_far), ("near", x_near)):
        omega_mark = conformal_factor(x_mark)
        g_mark = metric_g11(x_mark)
        axes.plot([x_mark], [omega_mark], marker="o")
        axes.annotate(
            f"{label}: g({x_mark:g})={g_mark:.2f}",
            xy=(x_mark, omega_mark),
            xytext=(x_mark, omega_mark + 0.5),
        )
    axes.set_title("Lens 3 - Omega(x) blow-up toward x_gojo (metric FORMIDABLE)")
    axes.set_xlabel("x (attacker position; barrier at x_g)")
    axes.set_ylabel("Omega(x)")
    axes.legend()
    figure.savefig(path)
    pyplot.close(figure)
    return path


def save_series_convergence_png(
    path: str,
    *,
    max_n: int = 12,
) -> str:
    """Write Lens 1's Zeno series ``S_n -> 1`` with its residual to ``path``.

    Plots the partial sums ``S_n = 1 - (1/2)^n`` climbing to the limit ``1`` and,
    on the same axes, the residual gap ``(1/2)^n`` decaying to ``0``. matplotlib
    is imported lazily; raises :class:`OptionalDependencyError` when it is absent.
    Returns ``path`` on success.
    """
    ys = zeno_series_values(max_n)
    ns = list(range(1, max_n + 1))
    residuals = [float(residual(n)) for n in ns]
    pyplot = _load_pyplot()
    figure, axes = pyplot.subplots()
    axes.plot(ns, ys, marker="o", label="S_n = 1 - (1/2)^n")
    axes.plot(ns, residuals, marker="x", linestyle=":", label="residual (1/2)^n")
    axes.axhline(1.0, linestyle="--", label="limit = 1")
    axes.set_title("Lens 1 - Zeno: S_n -> 1 with residual (FRAGILE)")
    axes.set_xlabel("n (steps)")
    axes.set_ylabel("value")
    axes.legend()
    figure.savefig(path)
    pyplot.close(figure)
    return path


def save_covering_png(
    path: str,
    *,
    eps: Fraction = Fraction(1, 10),
    max_terms: int = 12,
) -> str:
    """Write Lens 2's covering length ``sum eps/2^n -> eps`` to ``path``.

    Plots the partial total cover length ``T_k = sum_{n=1}^k eps/2^n`` climbing
    toward the arbitrary ``eps`` from below (Lebesgue ``m(Z) = 0``). matplotlib is
    imported lazily; raises :class:`OptionalDependencyError` when it is absent.
    Returns ``path`` on success.
    """
    ys = cover_length_values(eps, max_terms)
    ks = list(range(1, max_terms + 1))
    pyplot = _load_pyplot()
    figure, axes = pyplot.subplots()
    axes.plot(ks, ys, marker="o", label="sum eps/2^n")
    axes.axhline(float(eps), linestyle="--", label=f"eps={float(eps):g}")
    axes.set_title("Lens 2 - covering length -> eps (measure zero, FRAGILE)")
    axes.set_xlabel("terms k")
    axes.set_ylabel("total cover length")
    axes.legend()
    figure.savefig(path)
    pyplot.close(figure)
    return path


# ---------------------------------------------------------------------------
# Lens 3 (2-D) -- geodesics bending around Gojo, and the length divergence
# ---------------------------------------------------------------------------

def save_geodesic_bundle_png(
    path: str,
    *,
    impact_parameters: Sequence[float] = (0.25, 0.5, 0.75, 1.0, 1.5, 2.0),
    x_start: float = -3.0,
    dtau: float = 1e-3,
    max_steps: int = 6000,
) -> str:
    """Write a bundle of 2-D geodesics bending around Gojo (streamlines) to ``path``.

    Each ray starts at ``(x_start, b)`` for an impact parameter ``b`` and travels
    in ``+x``; the conformal metric ``g_ij = Omega^2 delta_ij`` bends it TOWARD
    Gojo (at the origin), the light-bending analog. matplotlib is imported lazily;
    raises :class:`OptionalDependencyError` when it is absent. Returns ``path``.
    """
    metric = ConformalMetric()
    pyplot = _load_pyplot()
    figure, axes = pyplot.subplots()
    for b in impact_parameters:
        res = metric.integrate_geodesic(
            (x_start, b), (1.0, 0.0), dtau=dtau, max_steps=max_steps, min_radius=1e-3
        )
        xs = [p[0] for p in res.points]
        ys = [p[1] for p in res.points]
        axes.plot(xs, ys, linewidth=1.0, label=f"b={b:g}")
    axes.plot([0.0], [0.0], marker="*", markersize=14, color="black", label="Gojo")
    axes.set_title("Lens 3 (2-D) - geodesics bending around Gojo (FORMIDABLE)")
    axes.set_xlabel("x")
    axes.set_ylabel("y")
    axes.set_aspect("equal", adjustable="datalim")
    axes.legend(fontsize="small")
    figure.savefig(path)
    pyplot.close(figure)
    return path


def save_length_divergence_png(
    path: str,
    *,
    start_radius: float = 0.9,
    min_exponent: int = 8,
) -> str:
    """Write the felt-length-vs-delta divergence curve to ``path``.

    Plots the felt geodesic length to reach within ``delta`` of Gojo against
    ``delta`` on a log-x axis: as ``delta -> 0`` the length climbs without bound
    (the ``-lam ln(delta)`` tail). matplotlib is imported lazily; raises
    :class:`OptionalDependencyError` when it is absent. Returns ``path``.
    """
    metric = ConformalMetric()
    deltas = [10.0 ** (-k) for k in range(1, min_exponent + 1)]
    table = metric.felt_length_divergence(deltas, start_radius=start_radius)
    xs = [d for d, _ in table]
    ys = [L for _, L in table]
    pyplot = _load_pyplot()
    figure, axes = pyplot.subplots()
    axes.semilogx(xs, ys, marker="o", label="felt length L(delta)")
    axes.invert_xaxis()  # approaching Gojo (delta -> 0) reads left-to-right
    axes.set_title("Lens 3 (2-D) - felt length diverges as delta -> 0")
    axes.set_xlabel("delta (distance short of Gojo)")
    axes.set_ylabel("felt geodesic length")
    axes.legend()
    figure.savefig(path)
    pyplot.close(figure)
    return path


# ---------------------------------------------------------------------------
# Lens 3 (3-D) -- a bundle of geodesics bending around Gojo in R^3
# ---------------------------------------------------------------------------

def save_geodesic_3d_png(
    path: str,
    *,
    offsets: Sequence[Tuple[float, float]] = (
        (0.5, 0.0), (0.0, 0.5), (0.5, 0.5), (-0.6, 0.3), (0.3, -0.6), (0.9, 0.9),
    ),
    x_start: float = -3.0,
    dtau: float = 1e-3,
    max_steps: int = 6000,
) -> str:
    """Write a bundle of 3-D geodesics bending around Gojo (in ``R^3``) to ``path``.

    Each ray starts at ``(x_start, y0, z0)`` for a transverse offset
    ``(y0, z0)`` and travels in ``+x``; the conformal metric ``g_ij = Omega^2
    delta_ij`` bends it TOWARD Gojo at the origin (the 3-D light-bending analog).
    Rendered with ``mpl_toolkits.mplot3d``; matplotlib is imported lazily, so this
    raises :class:`OptionalDependencyError` when it is absent. Returns ``path``.
    """
    metric = ConformalMetricND()  # Gojo at the origin of R^3
    pyplot = _load_pyplot()
    # Importing pyplot registers the 3-D projection; request it explicitly.
    figure = pyplot.figure()
    axes = figure.add_subplot(111, projection="3d")
    for y0, z0 in offsets:
        res = metric.integrate_geodesic(
            (x_start, y0, z0), (1.0, 0.0, 0.0),
            dtau=dtau, max_steps=max_steps, min_radius=1e-3,
        )
        xs = [p[0] for p in res.points]
        ys = [p[1] for p in res.points]
        zs = [p[2] for p in res.points]
        axes.plot(xs, ys, zs, linewidth=1.0, label=f"({y0:g},{z0:g})")
    axes.scatter([0.0], [0.0], [0.0], marker="*", s=160, color="black", label="Gojo")
    axes.set_title("Lens 3 (3-D) - geodesics bending around Gojo (FORMIDABLE)")
    axes.set_xlabel("x")
    axes.set_ylabel("y")
    axes.set_zlabel("z")
    axes.legend(fontsize="small")
    figure.savefig(path)
    pyplot.close(figure)
    return path
