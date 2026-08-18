"""Vectorised numpy batch integrator for 2-D conformal geodesics.

Mirrors :meth:`gojo_infinity.core.riemannian_manifold.ConformalMetric.integrate_geodesic`,
advancing MANY initial conditions at once with the same fixed-step RK4 scheme and
the same acceleration ``a = |v|^2 grad(phi) - 2 (grad(phi) . v) v``. numpy is
reached LAZILY via :func:`commons.core.optional.try_import`, so importing this
module never requires numpy; the batch routines raise
:class:`~gojo_infinity.accel.numpy_backend.OptionalDependencyError` when it is
absent.

Parity honesty: the pure core reduces with libm ``exp`` and Python floats; numpy
uses its own vectorised ``exp`` and pairwise reductions. Each per-step update
therefore agrees to a few ULP, so over a fixed number of steps the batch final
states and arc lengths match the pure integrator to a small tolerance (asserted
in ``tests/test_manifold_accel_parity.py``), not bit-for-bit.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Tuple

from commons.core.optional import try_import

from gojo_infinity.accel.numpy_backend import OptionalDependencyError
from gojo_infinity.core.riemannian import DEFAULT_LAMBDA, DEFAULT_SIGMA
from gojo_infinity.core.riemannian_manifold import DEFAULT_GOJO

Vec2 = Tuple[float, float]


def _numpy() -> Any:
    """Return numpy or raise :class:`OptionalDependencyError` (lazy import)."""
    np = try_import("numpy")
    if np is None:
        raise OptionalDependencyError(
            "numpy is required for gojo_infinity.accel batch geodesics but is not "
            "installed; use ConformalMetric.integrate_geodesic (pure core) instead"
        )
    return np


@dataclass(frozen=True)
class BatchGeodesicResult:
    """Immutable result of :func:`integrate_geodesics_batch` (numpy arrays)."""

    final_positions: Any   # (N, 2)
    final_velocities: Any  # (N, 2)
    arc_lengths: Any       # (N,)
    energy_start: Any      # (N,)
    energy_end: Any        # (N,)
    steps: int


def _grad_phi_batch(np: Any, pos: Any, sigma: float, lam: float, gojo: Vec2) -> Any:
    """Vectorised ``grad(phi)`` for a batch of points ``pos`` shaped ``(N, 2)``."""
    rel = pos - np.asarray(gojo, dtype=np.float64)
    d = np.sqrt(rel[:, 0] ** 2 + rel[:, 1] ** 2)
    s2 = sigma * sigma
    kernel = np.exp(-(d * d) / s2)
    omega = 1.0 + lam * kernel / d
    f_prime = kernel * (-2.0 * d * d / s2 - 1.0) / (d * d)
    # grad_omega = lam * f_prime * (rel / d); grad_phi = grad_omega / omega
    scale = lam * f_prime / (d * omega)
    return rel * scale[:, None]


def _rhs_batch(np: Any, pos: Any, vel: Any, sigma: float, lam: float, gojo: Vec2) -> Any:
    """Vectorised geodesic acceleration for a batch: returns ``(N, 2)`` array."""
    g = _grad_phi_batch(np, pos, sigma, lam, gojo)
    speed2 = vel[:, 0] ** 2 + vel[:, 1] ** 2
    gv = g[:, 0] * vel[:, 0] + g[:, 1] * vel[:, 1]
    return speed2[:, None] * g - 2.0 * gv[:, None] * vel


def _omega_norm_v(np: Any, pos: Any, vel: Any, sigma: float, lam: float, gojo: Vec2) -> Any:
    """Vectorised ``Omega(x) * |v|`` (the felt-speed ``sqrt(energy)``)."""
    rel = pos - np.asarray(gojo, dtype=np.float64)
    d = np.sqrt(rel[:, 0] ** 2 + rel[:, 1] ** 2)
    omega = 1.0 + lam * np.exp(-(d * d) / (sigma * sigma)) / d
    speed = np.sqrt(vel[:, 0] ** 2 + vel[:, 1] ** 2)
    return omega, omega * speed


def integrate_geodesics_batch(
    p0: Any,
    v0: Any,
    *,
    dtau: float = 1e-3,
    steps: int = 1000,
    sigma: float = DEFAULT_SIGMA,
    lam: float = DEFAULT_LAMBDA,
    gojo: Vec2 = DEFAULT_GOJO,
) -> BatchGeodesicResult:
    """Integrate ``N`` conformal geodesics for ``steps`` fixed RK4 steps at once.

    ``p0`` and ``v0`` are array-likes of shape ``(N, 2)`` (initial positions and
    velocities). Every trajectory takes exactly ``steps`` steps of size ``dtau``
    (no per-particle early stop), so the batch parity against the pure integrator
    is clean. Felt arc length is accumulated by the trapezoid rule on
    ``Omega|v|``. Raises :class:`ValueError` for bad shapes/args and
    :class:`OptionalDependencyError` when numpy is absent.
    """
    if dtau <= 0.0:
        raise ValueError("dtau must be positive")
    if steps < 1:
        raise ValueError("steps must be >= 1")
    np = _numpy()
    pos = np.array(p0, dtype=np.float64)
    vel = np.array(v0, dtype=np.float64)
    if pos.ndim != 2 or pos.shape[1] != 2 or pos.shape != vel.shape:
        raise ValueError("p0 and v0 must both have shape (N, 2)")

    def rhs(px: Any, vx: Any) -> Any:
        return _rhs_batch(np, px, vx, sigma, lam, gojo)

    omega0, f_prev = _omega_norm_v(np, pos, vel, sigma, lam, gojo)
    energy_start = (omega0 ** 2) * (vel[:, 0] ** 2 + vel[:, 1] ** 2)
    arc = np.zeros(pos.shape[0], dtype=np.float64)
    for _ in range(steps):
        k1p, k1v = vel, rhs(pos, vel)
        k2p, k2v = vel + 0.5 * dtau * k1v, rhs(pos + 0.5 * dtau * k1p, vel + 0.5 * dtau * k1v)
        k3p, k3v = vel + 0.5 * dtau * k2v, rhs(pos + 0.5 * dtau * k2p, vel + 0.5 * dtau * k2v)
        k4p, k4v = vel + dtau * k3v, rhs(pos + dtau * k3p, vel + dtau * k3v)
        pos = pos + (dtau / 6.0) * (k1p + 2.0 * k2p + 2.0 * k3p + k4p)
        vel = vel + (dtau / 6.0) * (k1v + 2.0 * k2v + 2.0 * k3v + k4v)
        omega, f_now = _omega_norm_v(np, pos, vel, sigma, lam, gojo)
        arc = arc + 0.5 * (f_prev + f_now) * dtau
        f_prev = f_now
    energy_end = (omega ** 2) * (vel[:, 0] ** 2 + vel[:, 1] ** 2)
    return BatchGeodesicResult(
        final_positions=pos,
        final_velocities=vel,
        arc_lengths=arc,
        energy_start=energy_start,
        energy_end=energy_end,
        steps=steps,
    )


# ---------------------------------------------------------------------------
# n-D (dimension-agnostic) batch integrator -- serves 1-D, 2-D and 3-D
# ---------------------------------------------------------------------------

VecN = Tuple[float, ...]

DEFAULT_GOJO_3D: VecN = (0.0, 0.0, 0.0)


def _grad_phi_batch_nd(np: Any, pos: Any, sigma: float, lam: float, gojo: VecN) -> Any:
    """Vectorised ``grad(phi)`` for a batch of ``(N, D)`` points, any dimension ``D``."""
    rel = pos - np.asarray(gojo, dtype=np.float64)
    d = np.sqrt(np.sum(rel * rel, axis=1))
    s2 = sigma * sigma
    kernel = np.exp(-(d * d) / s2)
    omega = 1.0 + lam * kernel / d
    f_prime = kernel * (-2.0 * d * d / s2 - 1.0) / (d * d)
    scale = lam * f_prime / (d * omega)  # grad_phi = grad_omega / omega
    return rel * scale[:, None]


def _rhs_batch_nd(np: Any, pos: Any, vel: Any, sigma: float, lam: float, gojo: VecN) -> Any:
    """Vectorised geodesic acceleration for an ``(N, D)`` batch, any dimension ``D``."""
    g = _grad_phi_batch_nd(np, pos, sigma, lam, gojo)
    speed2 = np.sum(vel * vel, axis=1)
    gv = np.sum(g * vel, axis=1)
    return speed2[:, None] * g - 2.0 * gv[:, None] * vel


def _omega_norm_v_nd(np: Any, pos: Any, vel: Any, sigma: float, lam: float, gojo: VecN) -> Any:
    """Vectorised ``(Omega, Omega * |v|)`` for an ``(N, D)`` batch, any dimension ``D``."""
    rel = pos - np.asarray(gojo, dtype=np.float64)
    d = np.sqrt(np.sum(rel * rel, axis=1))
    omega = 1.0 + lam * np.exp(-(d * d) / (sigma * sigma)) / d
    speed = np.sqrt(np.sum(vel * vel, axis=1))
    return omega, omega * speed


def integrate_geodesics_batch_nd(
    p0: Any,
    v0: Any,
    *,
    dtau: float = 1e-3,
    steps: int = 1000,
    sigma: float = DEFAULT_SIGMA,
    lam: float = DEFAULT_LAMBDA,
    gojo: VecN = DEFAULT_GOJO_3D,
) -> BatchGeodesicResult:
    """Integrate ``N`` conformal geodesics in ``R^D`` for ``steps`` RK4 steps at once.

    Dimension-agnostic mirror of
    :meth:`gojo_infinity.core.riemannian_manifold_nd.ConformalMetricND.integrate_geodesic`:
    ``p0`` and ``v0`` are array-likes of shape ``(N, D)`` (``D`` inferred from the
    arrays and matched against ``len(gojo)``). Every trajectory takes exactly
    ``steps`` fixed steps of size ``dtau`` (no per-particle early stop), so the
    batch parity against the pure integrator is clean. Felt arc length is
    accumulated by the trapezoid rule on ``Omega|v|``. Raises :class:`ValueError`
    for bad shapes/args and :class:`OptionalDependencyError` when numpy is absent.
    """
    if dtau <= 0.0:
        raise ValueError("dtau must be positive")
    if steps < 1:
        raise ValueError("steps must be >= 1")
    np = _numpy()
    pos = np.array(p0, dtype=np.float64)
    vel = np.array(v0, dtype=np.float64)
    if pos.ndim != 2 or pos.shape != vel.shape:
        raise ValueError("p0 and v0 must both have shape (N, D)")
    if pos.shape[1] != len(gojo):
        raise ValueError(f"point dimension {pos.shape[1]} != len(gojo) {len(gojo)}")

    def rhs(px: Any, vx: Any) -> Any:
        return _rhs_batch_nd(np, px, vx, sigma, lam, gojo)

    omega0, f_prev = _omega_norm_v_nd(np, pos, vel, sigma, lam, gojo)
    energy_start = (omega0 ** 2) * np.sum(vel * vel, axis=1)
    arc = np.zeros(pos.shape[0], dtype=np.float64)
    for _ in range(steps):
        k1p, k1v = vel, rhs(pos, vel)
        k2p, k2v = vel + 0.5 * dtau * k1v, rhs(pos + 0.5 * dtau * k1p, vel + 0.5 * dtau * k1v)
        k3p, k3v = vel + 0.5 * dtau * k2v, rhs(pos + 0.5 * dtau * k2p, vel + 0.5 * dtau * k2v)
        k4p, k4v = vel + dtau * k3v, rhs(pos + dtau * k3p, vel + dtau * k3v)
        pos = pos + (dtau / 6.0) * (k1p + 2.0 * k2p + 2.0 * k3p + k4p)
        vel = vel + (dtau / 6.0) * (k1v + 2.0 * k2v + 2.0 * k3v + k4v)
        omega, f_now = _omega_norm_v_nd(np, pos, vel, sigma, lam, gojo)
        arc = arc + 0.5 * (f_prev + f_now) * dtau
        f_prev = f_now
    energy_end = (omega ** 2) * np.sum(vel * vel, axis=1)
    return BatchGeodesicResult(
        final_positions=pos,
        final_velocities=vel,
        arc_lengths=arc,
        energy_start=energy_start,
        energy_end=energy_end,
        steps=steps,
    )
