"""Lens 3 (2-D) -- a real Riemannian-manifold geodesic solver. FORMIDABLE.

An ENHANCEMENT beyond the essay's one-dimensional treatment: instead of the
scalar line element ``ds = Omega(x) dx`` of :mod:`gojo_infinity.core.riemannian`,
this module builds a genuine two-dimensional, conformally flat Riemannian
manifold around Gojo and integrates its geodesics.

The model (consistent with the 1-D lens)
----------------------------------------
Gojo sits at a point ``g`` in ``R^2`` (default: the **origin**). For the radial
distance ``d = |x - g|`` the conformal factor is the 2-D radial version of the
existing 1-D ``Omega`` -- the SAME RIKEN Gaussian kernel, ``sigma`` and
``lambda``::

    Omega(x) = 1 + lambda * exp(-d^2 / sigma^2) / d.

It tends to ``1`` as ``d -> inf`` (flat far away) and to ``+infinity`` as
``d -> 0`` (the barrier). Because the 1-D ``gap = x_gojo - x`` equals the radial
distance for an inbound attacker, a purely radial approach here reproduces the
1-D felt length exactly (see :meth:`ConformalMetric.felt_length_to_reach` and the
parity test). The metric tensor is conformally flat::

    g_ij(x) = Omega(x)^2 * delta_ij      (2x2, symmetric, positive-definite).

Geodesics
---------
With ``phi = ln(Omega)`` a conformal metric ``g_ij = e^{2 phi} delta_ij`` has the
closed-form Christoffel symbols::

    Gamma^k_ij = delta^k_i d_j phi + delta^k_j d_i phi - delta_ij d_k phi,

so ``x''^k = -Gamma^k_ij x'^i x'^j`` collapses to the vector geodesic equation::

    x'' = |x'|^2 grad(phi) - 2 (grad(phi) . x') x'.

:meth:`christoffel_general` recomputes the SAME symbols from finite differences of
``g_ij`` (the standard ``1/2 g^{kl}(d_i g_jl + d_j g_il - d_l g_ij)``) to
cross-validate the closed form. ``grad(phi)`` is ANALYTIC here (documented below).

Pure core: stdlib + ``commons.core`` only (uses ``adaptive_integral`` and
``central_difference``). numpy/matplotlib never appear -- a numpy batch mirror
lives in ``gojo_infinity.accel`` and PNGs in ``adapters.viz``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Tuple

from commons.core import adaptive_integral, central_difference

from gojo_infinity.core.riemannian import DEFAULT_LAMBDA, DEFAULT_SIGMA
from gojo_infinity.core.riemannian_manifold_nd import conformal_acceleration
from gojo_infinity.core.verdicts import RIEMANNIAN_VERDICT, Verdict

Vec2 = Tuple[float, float]
Mat2 = Tuple[Tuple[float, float], Tuple[float, float]]
Christoffel = Tuple[Mat2, Mat2]  # Gamma[k][i][j]

DEFAULT_GOJO: Vec2 = (0.0, 0.0)  # Gojo stands at the origin of R^2


# ---------------------------------------------------------------------------
# Small pure-stdlib 2-vector helpers (immutable tuple arithmetic)
# ---------------------------------------------------------------------------

def _sub(a: Vec2, b: Vec2) -> Vec2:
    return (a[0] - b[0], a[1] - b[1])


def _dot(a: Vec2, b: Vec2) -> float:
    return a[0] * b[0] + a[1] * b[1]


def _norm(a: Vec2) -> float:
    return math.hypot(a[0], a[1])


# ---------------------------------------------------------------------------
# The conformal metric g_ij = Omega^2 delta_ij
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ConformalMetric:
    """A conformally flat 2-D Riemannian metric ``g_ij = Omega(x)^2 delta_ij``.

    Immutable value object carrying the RIKEN kernel width ``sigma``, the
    calibrated ``lam`` (both defaulting to the 1-D lens constants for
    consistency), and Gojo's location ``gojo`` (default: the origin). Every
    method returns fresh values; nothing is mutated in place.

    Raises :class:`ValueError` for ``sigma <= 0`` or ``lam < 0``.
    """

    sigma: float = DEFAULT_SIGMA
    lam: float = DEFAULT_LAMBDA
    gojo: Vec2 = DEFAULT_GOJO

    def __post_init__(self) -> None:
        if self.sigma <= 0:
            raise ValueError("sigma must be positive")
        if self.lam < 0:
            raise ValueError("lam must be non-negative")

    # -- scalar field -------------------------------------------------------

    def radius(self, p: Vec2) -> float:
        """Euclidean distance ``d = |p - gojo|`` from Gojo."""
        return _norm(_sub(p, self.gojo))

    def omega_radial(self, d: float) -> float:
        """Conformal factor as a function of the radius ``d = |x - gojo|``.

        ``Omega(d) = 1 + lam * exp(-d^2/sigma^2) / d`` (``d > 0``). This is the
        SAME functional form as the 1-D ``conformal_factor`` in ``gap = x_g - x``,
        which is why radial approaches match the 1-D lens exactly.
        """
        if d <= 0.0:
            raise ValueError("Omega diverges at Gojo (d must be > 0)")
        return 1.0 + self.lam * math.exp(-(d * d) / (self.sigma * self.sigma)) / d

    def omega(self, p: Vec2) -> float:
        """Conformal factor ``Omega(x)`` at the 2-D point ``p`` (``p != gojo``)."""
        return self.omega_radial(self.radius(p))

    def phi(self, p: Vec2) -> float:
        """Log conformal potential ``phi(x) = ln(Omega(x))`` (drives geodesics)."""
        return math.log(self.omega(p))

    def grad_omega(self, p: Vec2) -> Vec2:
        """ANALYTIC gradient of ``Omega`` at ``p``.

        With ``f(d) = exp(-d^2/sigma^2)/d`` and unit radial ``u = (p-g)/d``,
        ``grad Omega = lam f'(d) u`` where
        ``f'(d) = exp(-d^2/sigma^2) * (-2 d^2/sigma^2 - 1) / d^2``.
        """
        rel = _sub(p, self.gojo)
        d = _norm(rel)
        if d <= 0.0:
            raise ValueError("grad Omega is singular at Gojo (d must be > 0)")
        s2 = self.sigma * self.sigma
        kernel = math.exp(-(d * d) / s2)
        f_prime = kernel * (-2.0 * d * d / s2 - 1.0) / (d * d)
        scale = self.lam * f_prime / d  # divide once more to turn rel into unit u
        return (scale * rel[0], scale * rel[1])

    def grad_phi(self, p: Vec2) -> Vec2:
        """ANALYTIC gradient of ``phi = ln(Omega)``: ``grad(Omega) / Omega``."""
        omega = self.omega(p)
        g = self.grad_omega(p)
        return (g[0] / omega, g[1] / omega)

    # -- tensors ------------------------------------------------------------

    def metric_tensor(self, p: Vec2) -> Mat2:
        """The 2x2 metric ``g_ij(p) = Omega(p)^2 delta_ij`` (SPD, symmetric)."""
        w = self.omega(p) ** 2
        return ((w, 0.0), (0.0, w))

    def inverse_metric(self, p: Vec2) -> Mat2:
        """The inverse metric ``g^{ij}(p) = Omega(p)^{-2} delta^{ij}``."""
        inv = 1.0 / (self.omega(p) ** 2)
        return ((inv, 0.0), (0.0, inv))

    def metric_speed_squared(self, p: Vec2, v: Vec2) -> float:
        """The metric norm ``g_ij v^i v^j = Omega(p)^2 |v|^2`` (the affine energy)."""
        return self.omega(p) ** 2 * _dot(v, v)

    # -- Christoffel symbols ------------------------------------------------

    def christoffel_conformal(self, p: Vec2) -> Christoffel:
        """Christoffel symbols via the conformal CLOSED FORM.

        ``Gamma^k_ij = delta^k_i d_j phi + delta^k_j d_i phi - delta_ij d_k phi``,
        returned as ``Gamma[k][i][j]`` (a 2x2x2 nested tuple).
        """
        dphi = self.grad_phi(p)
        blocks = []
        for k in range(2):
            rows = []
            for i in range(2):
                row = []
                for j in range(2):
                    val = 0.0
                    if k == i:
                        val += dphi[j]
                    if k == j:
                        val += dphi[i]
                    if i == j:
                        val -= dphi[k]
                    row.append(val)
                rows.append((row[0], row[1]))
            blocks.append((rows[0], rows[1]))
        return (blocks[0], blocks[1])

    def christoffel_general(self, p: Vec2, *, h: float = 1e-5) -> Christoffel:
        """Christoffel symbols from the GENERAL metric-derivative formula.

        ``Gamma^k_ij = 1/2 g^{kl}(d_i g_jl + d_j g_il - d_l g_ij)`` with the metric
        partials taken by :func:`commons.core.central_difference`. Used to
        cross-validate :meth:`christoffel_conformal`. Because ``g^{kl}`` is
        diagonal only the ``l = k`` term survives.
        """
        inv = self.inverse_metric(p)

        def dg(m: int, i: int, j: int) -> float:
            def component(t: float) -> float:
                q = (t, p[1]) if m == 0 else (p[0], t)
                return self.metric_tensor(q)[i][j]

            return central_difference(component, p[m], h)

        blocks = []
        for k in range(2):
            rows = []
            for i in range(2):
                row = []
                for j in range(2):
                    term = dg(i, j, k) + dg(j, i, k) - dg(k, i, j)
                    row.append(0.5 * inv[k][k] * term)
                rows.append((row[0], row[1]))
            blocks.append((rows[0], rows[1]))
        return (blocks[0], blocks[1])

    # -- geodesic dynamics --------------------------------------------------

    def geodesic_rhs(self, state: "GeodesicState") -> "GeodesicState":
        """Right-hand side of the first-order geodesic system.

        Maps ``(x, v)`` to ``(v, a)`` with the conformal acceleration
        ``a = |v|^2 grad(phi) - 2 (grad(phi) . v) v``, delegating to the shared
        dimension-agnostic :func:`conformal_acceleration` (the single copy of the
        geodesic RHS). Returned as a :class:`GeodesicState` so RK4 can combine
        states with plain arithmetic.
        """
        p = (state.x, state.y)
        v = (state.vx, state.vy)
        g = self.grad_phi(p)
        ax, ay = conformal_acceleration(g, v)
        return GeodesicState(v[0], v[1], ax, ay)

    def integrate_geodesic(
        self,
        p0: Vec2,
        v0: Vec2,
        *,
        dtau: float = 1e-3,
        max_steps: int = 200_000,
        target_radius: float | None = None,
        arc_length_cap: float | None = None,
        min_radius: float = 1e-9,
    ) -> "GeodesicResult":
        """Integrate a geodesic from ``(p0, v0)`` with fixed-step RK4.

        The affine-parameter equation ``x'' = |x'|^2 grad(phi) - 2(grad(phi).x')x'``
        is advanced by classic 4th-order Runge-Kutta. Integration stops when the
        trajectory first enters ``target_radius`` of Gojo, when the accumulated
        felt (arc) length ``s = integral Omega |v| dtau`` exceeds
        ``arc_length_cap``, when ``min_radius`` is breached, or after
        ``max_steps``. The felt length is accumulated by the trapezoid rule on
        ``Omega(x)|v|`` (which is the conserved ``sqrt(energy)``, so it is
        essentially exact). Returns an immutable :class:`GeodesicResult`.
        """
        if dtau <= 0.0:
            raise ValueError("dtau must be positive")
        if max_steps < 1:
            raise ValueError("max_steps must be >= 1")

        state = GeodesicState(p0[0], p0[1], v0[0], v0[1])
        points: list[Vec2] = [(state.x, state.y)]
        energy0 = self.metric_speed_squared((state.x, state.y), (state.vx, state.vy))
        arc_length = 0.0
        f_prev = self.omega((state.x, state.y)) * _norm((state.vx, state.vy))
        stop = "max_steps"
        steps = 0
        for _ in range(max_steps):
            state = self._rk4_step(state, dtau)
            steps += 1
            p = (state.x, state.y)
            f_now = self.omega(p) * _norm((state.vx, state.vy))
            arc_length += 0.5 * (f_prev + f_now) * dtau
            f_prev = f_now
            points.append(p)
            r = self.radius(p)
            if target_radius is not None and r <= target_radius:
                stop = "reached_target"
                break
            if r <= min_radius:
                stop = "min_radius"
                break
            if arc_length_cap is not None and arc_length >= arc_length_cap:
                stop = "arc_cap"
                break
        energy1 = self.metric_speed_squared((state.x, state.y), (state.vx, state.vy))
        return GeodesicResult(
            points=tuple(points),
            initial_velocity=(v0[0], v0[1]),
            final_velocity=(state.vx, state.vy),
            arc_length=arc_length,
            tau=steps * dtau,
            steps=steps,
            final_radius=self.radius((state.x, state.y)),
            energy_start=energy0,
            energy_end=energy1,
            stop_reason=stop,
        )

    def _rk4_step(self, state: "GeodesicState", h: float) -> "GeodesicState":
        """One classic RK4 step of the geodesic system with step ``h``."""
        k1 = self.geodesic_rhs(state)
        k2 = self.geodesic_rhs(state.axpy(0.5 * h, k1))
        k3 = self.geodesic_rhs(state.axpy(0.5 * h, k2))
        k4 = self.geodesic_rhs(state.axpy(h, k3))
        increment = k1.add(k2.scale(2.0)).add(k3.scale(2.0)).add(k4).scale(h / 6.0)
        return state.add(increment)

    # -- felt (radial) length and its divergence ---------------------------

    def felt_length_to_reach(
        self, target_radius: float, *, start_radius: float, tol: float = 1e-10
    ) -> float:
        """Felt geodesic length of a radial approach from ``start_radius`` inward.

        Returns ``integral_{target_radius}^{start_radius} Omega(r) dr`` -- the
        Riemannian length of the radial geodesic from radius ``start_radius`` down
        to ``target_radius``. Equals the 1-D lens ``geodesic_length(1 -
        start_radius, 1 - target_radius)`` exactly (same integrand under
        ``r = gap``). Diverges as ``target_radius -> 0``. Raises
        :class:`ValueError` for non-positive radii or ``start_radius <=
        target_radius``.
        """
        if target_radius <= 0.0:
            raise ValueError("target_radius must be positive")
        if start_radius <= target_radius:
            raise ValueError("require start_radius > target_radius")
        return adaptive_integral(self.omega_radial, target_radius, start_radius, tol=tol)

    def felt_length_divergence(
        self, deltas: list[float], *, start_radius: float, tol: float = 1e-11
    ) -> list[tuple[float, float]]:
        """Felt length to reach each ``delta`` of Gojo -- monotone, unbounded.

        Returns ``[(delta, L), ...]``. As ``delta -> 0`` the felt length keeps
        growing without bound (the ``-lam ln(delta)`` tail): Infinity is
        FORMIDABLE in 2-D as well. Raises :class:`ValueError` for a bad ``delta``.
        """
        out: list[tuple[float, float]] = []
        for delta in deltas:
            out.append(
                (delta, self.felt_length_to_reach(delta, start_radius=start_radius, tol=tol))
            )
        return out


# ---------------------------------------------------------------------------
# Immutable state and result records
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class GeodesicState:
    """An immutable phase-space state ``(x, y, vx, vy)`` for the RK4 integrator."""

    x: float
    y: float
    vx: float
    vy: float

    def add(self, other: "GeodesicState") -> "GeodesicState":
        """Return the componentwise sum (a fresh state)."""
        return GeodesicState(
            self.x + other.x, self.y + other.y, self.vx + other.vx, self.vy + other.vy
        )

    def scale(self, factor: float) -> "GeodesicState":
        """Return this state scaled by ``factor`` (a fresh state)."""
        return GeodesicState(
            self.x * factor, self.y * factor, self.vx * factor, self.vy * factor
        )

    def axpy(self, factor: float, other: "GeodesicState") -> "GeodesicState":
        """Return ``self + factor * other`` (a fresh state)."""
        return self.add(other.scale(factor))


@dataclass(frozen=True)
class GeodesicResult:
    """Immutable result of :meth:`ConformalMetric.integrate_geodesic`."""

    points: Tuple[Vec2, ...]
    initial_velocity: Vec2
    final_velocity: Vec2
    arc_length: float
    tau: float
    steps: int
    final_radius: float
    energy_start: float
    energy_end: float
    stop_reason: str

    @property
    def energy_drift(self) -> float:
        """Relative drift of the conserved affine energy ``Omega^2 |v|^2``."""
        if self.energy_start == 0.0:
            return abs(self.energy_end)
        return abs(self.energy_end - self.energy_start) / abs(self.energy_start)

    @property
    def deflection_angle(self) -> float:
        """Signed turning angle from the initial to the final velocity (radians).

        Positive is a counter-clockwise turn. A grazing geodesic bends TOWARD
        Gojo, so a non-zero magnitude here is the light-bending / lensing analog.
        """
        return signed_angle(self.initial_velocity, self.final_velocity)


# ---------------------------------------------------------------------------
# Free helpers
# ---------------------------------------------------------------------------

def signed_angle(a: Vec2, b: Vec2) -> float:
    """Signed angle (radians) rotating vector ``a`` onto ``b`` in ``(-pi, pi]``."""
    cross = a[0] * b[1] - a[1] * b[0]
    dot = a[0] * b[0] + a[1] * b[1]
    return math.atan2(cross, dot)


def max_christoffel_difference(metric: ConformalMetric, points: list[Vec2], *,
                               h: float = 1e-5) -> float:
    """Max ``|closed-form - general|`` Christoffel component over ``points``.

    The cross-check that the conformal closed form matches the finite-difference
    general formula; used by the demo and tests. Returns the largest absolute
    componentwise difference across all sampled points.
    """
    worst = 0.0
    for p in points:
        closed = metric.christoffel_conformal(p)
        general = metric.christoffel_general(p, h=h)
        for k in range(2):
            for i in range(2):
                for j in range(2):
                    worst = max(worst, abs(closed[k][i][j] - general[k][i][j]))
    return worst


def verdict() -> Verdict:
    """2-D Riemannian verdict: FORMIDABLE -- radial felt length still diverges."""
    return RIEMANNIAN_VERDICT
