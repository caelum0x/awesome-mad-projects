"""Lens 3 (n-D) -- a dimension-agnostic conformal geodesic solver. FORMIDABLE.

The conformal geodesic mathematics is *dimension-agnostic*: for a conformally
flat metric ``g_ij = Omega(x)^2 delta_ij`` with ``phi = ln Omega`` the
Christoffel symbols and the geodesic right-hand side are the SAME closed forms in
every dimension::

    Gamma^k_ij = delta^k_i d_j phi + delta^k_j d_i phi - delta_ij d_k phi,
    x'' = |x'|^2 grad(phi) - 2 (grad(phi) . x') x'.

This module generalises the 2-D :mod:`gojo_infinity.core.riemannian_manifold`
solver to operate on ``n``-vectors (plain tuples of length ``n``), so the SAME
code serves 1-D, 2-D and 3-D. The 2-D module re-uses the shared geodesic
right-hand side :func:`conformal_acceleration` defined here -- there is exactly
ONE implementation of the geodesic RHS in the codebase.

Model (identical to the 1-D and 2-D lenses)
-------------------------------------------
Gojo sits at ``gojo`` in ``R^n`` (default: the **origin of R^3**). For the radial
distance ``d = |x - gojo|`` the conformal factor re-uses the SAME RIKEN Gaussian
kernel, ``sigma`` and ``lambda`` as the existing lenses::

    Omega(x) = 1 + lambda * exp(-d^2 / sigma^2) / d.

It tends to ``1`` far away (flat) and to ``+infinity`` at ``d -> 0`` (the
barrier). A purely radial approach reproduces the 1-D felt length exactly (the
radial parity test), and -- the key 3-D symmetry -- a geodesic stays inside the
2-plane spanned by its initial position, initial velocity and Gojo (the planarity
test), because both ``grad(phi)`` (radial) and ``x'`` lie in that plane.

Pure core: stdlib + ``commons.core`` only (uses ``adaptive_integral`` and
``central_difference``). numpy/matplotlib never appear here -- a numpy batch
mirror lives in ``gojo_infinity.accel`` and PNGs/GIFs in ``adapters``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Tuple

from commons.core import adaptive_integral, central_difference

from gojo_infinity.core.riemannian import DEFAULT_LAMBDA, DEFAULT_SIGMA
from gojo_infinity.core.verdicts import RIEMANNIAN_VERDICT, Verdict

VecN = Tuple[float, ...]
MatN = Tuple[VecN, ...]
ChristoffelN = Tuple[MatN, ...]  # Gamma[k][i][j]

DEFAULT_GOJO_3D: VecN = (0.0, 0.0, 0.0)  # Gojo stands at the origin of R^3


# ---------------------------------------------------------------------------
# Small pure-stdlib n-vector helpers (immutable tuple arithmetic)
# ---------------------------------------------------------------------------

def _sub(a: VecN, b: VecN) -> VecN:
    return tuple(ai - bi for ai, bi in zip(a, b))


def _add(a: VecN, b: VecN) -> VecN:
    return tuple(ai + bi for ai, bi in zip(a, b))


def _scale(a: VecN, s: float) -> VecN:
    return tuple(ai * s for ai in a)


def _dot(a: VecN, b: VecN) -> float:
    # Plain left-fold sum (matches the legacy 2-D component arithmetic exactly).
    return sum(ai * bi for ai, bi in zip(a, b))


def _norm(a: VecN) -> float:
    return math.sqrt(sum(ai * ai for ai in a))


def _cross3(a: VecN, b: VecN) -> VecN:
    """3-D cross product ``a x b`` (raises for non-3-vectors)."""
    if len(a) != 3 or len(b) != 3:
        raise ValueError("cross product is defined only for 3-vectors")
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


# ---------------------------------------------------------------------------
# The shared geodesic right-hand side (the ONE copy of the RHS math)
# ---------------------------------------------------------------------------

def conformal_acceleration(grad_phi: VecN, v: VecN) -> VecN:
    """Conformal geodesic acceleration ``a = |v|^2 grad(phi) - 2 (grad(phi).v) v``.

    Dimension-agnostic and used by BOTH the n-D integrator here and the legacy
    2-D :class:`gojo_infinity.core.riemannian_manifold.ConformalMetric` (its
    ``geodesic_rhs`` delegates here), so the geodesic RHS lives in exactly one
    place. Uses the same plain per-component arithmetic as the original 2-D
    formula, so 2-D numerics are unchanged bit-for-bit.
    """
    speed2 = _dot(v, v)
    gv = _dot(grad_phi, v)
    return tuple(speed2 * g - 2.0 * gv * vi for g, vi in zip(grad_phi, v))


# ---------------------------------------------------------------------------
# The conformal metric g_ij = Omega^2 delta_ij, in n dimensions
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ConformalMetricND:
    """A conformally flat ``n``-D Riemannian metric ``g_ij = Omega(x)^2 delta_ij``.

    Immutable value object carrying the RIKEN kernel width ``sigma``, the
    calibrated ``lam`` (both defaulting to the 1-D lens constants), and Gojo's
    location ``gojo`` (default: the origin of ``R^3``). The dimension ``n`` is
    inferred from ``len(gojo)``, so the SAME class serves 1-D, 2-D and 3-D. Every
    method returns fresh values; nothing is mutated in place.

    Raises :class:`ValueError` for ``sigma <= 0``, ``lam < 0`` or an empty
    ``gojo``.
    """

    sigma: float = DEFAULT_SIGMA
    lam: float = DEFAULT_LAMBDA
    gojo: VecN = DEFAULT_GOJO_3D

    def __post_init__(self) -> None:
        if self.sigma <= 0:
            raise ValueError("sigma must be positive")
        if self.lam < 0:
            raise ValueError("lam must be non-negative")
        if len(self.gojo) < 1:
            raise ValueError("gojo must have at least one coordinate")

    @property
    def dim(self) -> int:
        """The ambient dimension ``n`` (inferred from ``gojo``)."""
        return len(self.gojo)

    def _check(self, p: VecN) -> None:
        if len(p) != self.dim:
            raise ValueError(f"expected a {self.dim}-vector, got length {len(p)}")

    # -- scalar field -------------------------------------------------------

    def radius(self, p: VecN) -> float:
        """Euclidean distance ``d = |p - gojo|`` from Gojo."""
        self._check(p)
        return _norm(_sub(p, self.gojo))

    def omega_radial(self, d: float) -> float:
        """Conformal factor as a function of the radius ``d = |x - gojo|``.

        ``Omega(d) = 1 + lam * exp(-d^2/sigma^2) / d`` (``d > 0``) -- the SAME
        functional form as the 1-D/2-D lenses, which is why radial approaches
        match the 1-D lens exactly.
        """
        if d <= 0.0:
            raise ValueError("Omega diverges at Gojo (d must be > 0)")
        return 1.0 + self.lam * math.exp(-(d * d) / (self.sigma * self.sigma)) / d

    def omega(self, p: VecN) -> float:
        """Conformal factor ``Omega(x)`` at the point ``p`` (``p != gojo``)."""
        return self.omega_radial(self.radius(p))

    def phi(self, p: VecN) -> float:
        """Log conformal potential ``phi(x) = ln(Omega(x))`` (drives geodesics)."""
        return math.log(self.omega(p))

    def grad_omega(self, p: VecN) -> VecN:
        """ANALYTIC gradient of ``Omega`` at ``p``.

        With ``f(d) = exp(-d^2/sigma^2)/d`` and unit radial ``u = (p-g)/d``,
        ``grad Omega = lam f'(d) u`` where
        ``f'(d) = exp(-d^2/sigma^2) * (-2 d^2/sigma^2 - 1) / d^2``.
        """
        self._check(p)
        rel = _sub(p, self.gojo)
        d = _norm(rel)
        if d <= 0.0:
            raise ValueError("grad Omega is singular at Gojo (d must be > 0)")
        s2 = self.sigma * self.sigma
        kernel = math.exp(-(d * d) / s2)
        f_prime = kernel * (-2.0 * d * d / s2 - 1.0) / (d * d)
        scale = self.lam * f_prime / d  # divide once more to turn rel into unit u
        return _scale(rel, scale)

    def grad_phi(self, p: VecN) -> VecN:
        """ANALYTIC gradient of ``phi = ln(Omega)``: ``grad(Omega) / Omega``."""
        omega = self.omega(p)
        return _scale(self.grad_omega(p), 1.0 / omega)

    # -- tensors ------------------------------------------------------------

    def metric_tensor(self, p: VecN) -> MatN:
        """The ``n x n`` metric ``g_ij(p) = Omega(p)^2 delta_ij`` (SPD, symmetric)."""
        w = self.omega(p) ** 2
        n = self.dim
        return tuple(
            tuple(w if i == j else 0.0 for j in range(n)) for i in range(n)
        )

    def inverse_metric(self, p: VecN) -> MatN:
        """The inverse metric ``g^{ij}(p) = Omega(p)^{-2} delta^{ij}``."""
        inv = 1.0 / (self.omega(p) ** 2)
        n = self.dim
        return tuple(
            tuple(inv if i == j else 0.0 for j in range(n)) for i in range(n)
        )

    def metric_speed_squared(self, p: VecN, v: VecN) -> float:
        """The metric norm ``g_ij v^i v^j = Omega(p)^2 |v|^2`` (the affine energy)."""
        self._check(v)
        return self.omega(p) ** 2 * _dot(v, v)

    # -- Christoffel symbols ------------------------------------------------

    def christoffel_conformal(self, p: VecN) -> ChristoffelN:
        """Christoffel symbols via the conformal CLOSED FORM.

        ``Gamma^k_ij = delta^k_i d_j phi + delta^k_j d_i phi - delta_ij d_k phi``,
        returned as ``Gamma[k][i][j]`` (an ``n x n x n`` nested tuple).
        """
        dphi = self.grad_phi(p)
        n = self.dim
        blocks = []
        for k in range(n):
            rows = []
            for i in range(n):
                row = []
                for j in range(n):
                    val = 0.0
                    if k == i:
                        val += dphi[j]
                    if k == j:
                        val += dphi[i]
                    if i == j:
                        val -= dphi[k]
                    row.append(val)
                rows.append(tuple(row))
            blocks.append(tuple(rows))
        return tuple(blocks)

    def christoffel_general(self, p: VecN, *, h: float = 1e-5) -> ChristoffelN:
        """Christoffel symbols from the GENERAL metric-derivative formula.

        ``Gamma^k_ij = 1/2 g^{kl}(d_i g_jl + d_j g_il - d_l g_ij)`` with the metric
        partials taken by :func:`commons.core.central_difference`. Used to
        cross-validate :meth:`christoffel_conformal`. Because ``g^{kl}`` is
        diagonal only the ``l = k`` term survives.
        """
        self._check(p)
        inv = self.inverse_metric(p)
        n = self.dim

        def dg(m: int, i: int, j: int) -> float:
            def component(t: float) -> float:
                q = tuple(t if axis == m else p[axis] for axis in range(n))
                return self.metric_tensor(q)[i][j]

            return central_difference(component, p[m], h)

        blocks = []
        for k in range(n):
            rows = []
            for i in range(n):
                row = []
                for j in range(n):
                    term = dg(i, j, k) + dg(j, i, k) - dg(k, i, j)
                    row.append(0.5 * inv[k][k] * term)
                rows.append(tuple(row))
            blocks.append(tuple(rows))
        return tuple(blocks)

    # -- geodesic dynamics --------------------------------------------------

    def geodesic_rhs(self, state: "PhaseStateND") -> "PhaseStateND":
        """Right-hand side of the first-order geodesic system.

        Maps ``(x, v)`` to ``(v, a)`` with the conformal acceleration from the
        shared :func:`conformal_acceleration`.
        """
        g = self.grad_phi(state.pos)
        acc = conformal_acceleration(g, state.vel)
        return PhaseStateND(state.vel, acc)

    def integrate_geodesic(
        self,
        p0: VecN,
        v0: VecN,
        *,
        dtau: float = 1e-3,
        max_steps: int = 200_000,
        target_radius: float | None = None,
        arc_length_cap: float | None = None,
        min_radius: float = 1e-9,
    ) -> "GeodesicResultND":
        """Integrate an ``n``-D geodesic from ``(p0, v0)`` with fixed-step RK4.

        The affine-parameter equation ``x'' = |x'|^2 grad(phi) - 2(grad(phi).x')x'``
        is advanced by classic 4th-order Runge-Kutta. Integration stops when the
        trajectory first enters ``target_radius`` of Gojo, when the accumulated
        felt (arc) length ``s = integral Omega |v| dtau`` exceeds
        ``arc_length_cap``, when ``min_radius`` is breached, or after
        ``max_steps``. The felt length is accumulated by the trapezoid rule on
        ``Omega(x)|v|`` (the conserved ``sqrt(energy)``, so essentially exact).
        Returns an immutable :class:`GeodesicResultND`.
        """
        if dtau <= 0.0:
            raise ValueError("dtau must be positive")
        if max_steps < 1:
            raise ValueError("max_steps must be >= 1")
        self._check(p0)
        self._check(v0)

        state = PhaseStateND(tuple(p0), tuple(v0))
        points: list[VecN] = [state.pos]
        energy0 = self.metric_speed_squared(state.pos, state.vel)
        arc_length = 0.0
        f_prev = self.omega(state.pos) * _norm(state.vel)
        stop = "max_steps"
        steps = 0
        for _ in range(max_steps):
            state = self._rk4_step(state, dtau)
            steps += 1
            f_now = self.omega(state.pos) * _norm(state.vel)
            arc_length += 0.5 * (f_prev + f_now) * dtau
            f_prev = f_now
            points.append(state.pos)
            r = self.radius(state.pos)
            if target_radius is not None and r <= target_radius:
                stop = "reached_target"
                break
            if r <= min_radius:
                stop = "min_radius"
                break
            if arc_length_cap is not None and arc_length >= arc_length_cap:
                stop = "arc_cap"
                break
        energy1 = self.metric_speed_squared(state.pos, state.vel)
        return GeodesicResultND(
            points=tuple(points),
            initial_velocity=tuple(v0),
            final_velocity=state.vel,
            arc_length=arc_length,
            tau=steps * dtau,
            steps=steps,
            final_radius=self.radius(state.pos),
            energy_start=energy0,
            energy_end=energy1,
            stop_reason=stop,
        )

    def _rk4_step(self, state: "PhaseStateND", h: float) -> "PhaseStateND":
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
        to ``target_radius``. Equals the 1-D lens exactly (same integrand under
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

        Returns ``[(delta, L), ...]``. As ``delta -> 0`` the felt length grows
        without bound (the ``-lam ln(delta)`` tail): Infinity is FORMIDABLE in
        ``n``-D as well. Raises :class:`ValueError` for a bad ``delta``.
        """
        out: list[tuple[float, float]] = []
        for delta in deltas:
            out.append(
                (delta, self.felt_length_to_reach(delta, start_radius=start_radius, tol=tol))
            )
        return out

    # -- 3-D orbital-plane geometry (the planarity symmetry) ----------------

    def orbital_plane_normal(self, p0: VecN, v0: VecN) -> VecN:
        """Unit normal of the 2-plane spanned by ``p0 - gojo`` and ``v0`` (3-D).

        The geodesic stays inside the plane through Gojo spanned by the initial
        position and initial velocity, because both ``grad(phi)`` (radial) and the
        velocity lie in it. Raises :class:`ValueError` outside 3-D or when the two
        directions are parallel (no unique plane).
        """
        if self.dim != 3:
            raise ValueError("orbital_plane_normal is defined only in 3-D")
        self._check(p0)
        self._check(v0)
        normal = _cross3(_sub(p0, self.gojo), v0)
        length = _norm(normal)
        if length <= 0.0:
            raise ValueError("p0 - gojo and v0 are parallel; the plane is undefined")
        return _scale(normal, 1.0 / length)

    def out_of_plane_component(self, p: VecN, normal: VecN) -> float:
        """Signed distance of ``p`` from the plane through Gojo with unit ``normal``."""
        return _dot(_sub(p, self.gojo), normal)

    def max_out_of_plane_drift(self, points: Tuple[VecN, ...], normal: VecN) -> float:
        """Largest ``|out-of-plane component|`` over a trajectory's ``points``."""
        return max(abs(self.out_of_plane_component(p, normal)) for p in points)


# ---------------------------------------------------------------------------
# Immutable state and result records
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PhaseStateND:
    """An immutable phase-space state ``(pos, vel)`` for the RK4 integrator."""

    pos: VecN
    vel: VecN

    def add(self, other: "PhaseStateND") -> "PhaseStateND":
        """Return the componentwise sum (a fresh state)."""
        return PhaseStateND(_add(self.pos, other.pos), _add(self.vel, other.vel))

    def scale(self, factor: float) -> "PhaseStateND":
        """Return this state scaled by ``factor`` (a fresh state)."""
        return PhaseStateND(_scale(self.pos, factor), _scale(self.vel, factor))

    def axpy(self, factor: float, other: "PhaseStateND") -> "PhaseStateND":
        """Return ``self + factor * other`` (a fresh state)."""
        return self.add(other.scale(factor))


@dataclass(frozen=True)
class GeodesicResultND:
    """Immutable result of :meth:`ConformalMetricND.integrate_geodesic`."""

    points: Tuple[VecN, ...]
    initial_velocity: VecN
    final_velocity: VecN
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
        """UNSIGNED turning angle between the initial and final velocity (radians).

        In ``n``-D there is no global orientation, so this is the unsigned angle
        ``acos(v0.v1 / (|v0||v1|))``. A grazing geodesic bends TOWARD Gojo, so a
        non-zero value is the light-bending / lensing analog.
        """
        return unsigned_angle(self.initial_velocity, self.final_velocity)


# ---------------------------------------------------------------------------
# Free helpers
# ---------------------------------------------------------------------------

def unsigned_angle(a: VecN, b: VecN) -> float:
    """Unsigned angle (radians) between vectors ``a`` and ``b`` in ``[0, pi]``."""
    na = _norm(a)
    nb = _norm(b)
    if na == 0.0 or nb == 0.0:
        raise ValueError("angle is undefined for a zero vector")
    cos = _dot(a, b) / (na * nb)
    cos = max(-1.0, min(1.0, cos))  # clamp against round-off
    return math.acos(cos)


def max_christoffel_difference_nd(
    metric: ConformalMetricND, points: list[VecN], *, h: float = 1e-5
) -> float:
    """Max ``|closed-form - general|`` Christoffel component over ``points`` (n-D).

    Cross-checks that the conformal closed form matches the finite-difference
    general formula in any dimension. Returns the largest absolute componentwise
    difference across all sampled points.
    """
    worst = 0.0
    n = metric.dim
    for p in points:
        closed = metric.christoffel_conformal(p)
        general = metric.christoffel_general(p, h=h)
        for k in range(n):
            for i in range(n):
                for j in range(n):
                    worst = max(worst, abs(closed[k][i][j] - general[k][i][j]))
    return worst


def verdict() -> Verdict:
    """n-D Riemannian verdict: FORMIDABLE -- radial felt length still diverges."""
    return RIEMANNIAN_VERDICT
