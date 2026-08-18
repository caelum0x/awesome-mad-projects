"""SCMS / Eberly height-ridge: the crest of maximal Rickness (numpy-backed).

Two distinct, both-honest readings of the "Central Finite Curve" (CFC) live in
this package:

    * ZERO SET ``R^{-1}(0)`` -- the *boundary wall*.
      :mod:`mobius_rickness.core.tracer` traces where the sign-changing Rickness
      field ``R(u, v)`` vanishes: the codimension-1 dividing line between the
      Rick-positive and Rick-negative universes. It is a *level set* -- the frontier
      of the enclosure, generically passing through ``R = 0``.

    * SCMS RIDGE -- the *crest line* (this module).
      The Ozertem-Erdogmus / Eberly principal-curve ridge is the intrinsic 1-D
      spine of *maximal* Rickness: the locus where the field is a local maximum in
      the transverse direction. It is NOT a level set -- along a genuine crest
      ``R`` is far from ``0`` in general; it is the argmax-ridge ("Rick-maximal
      spine"), not the argmax-boundary.

Both are legitimate "Central Finite Curve" formalizations, but they are different
objects: the zero set answers *where does Rickness change sign*, the ridge answers
*where is Rickness maximal along a 1-D crest*.

Mathematics (Eberly height-ridge, traced by Subspace-Constrained Mean Shift):
    Let ``g = grad R`` and ``H = Hess R`` at a point ``x = (u, v)``. Diagonalize
    the symmetric ``H`` with ascending eigenvalues ``lambda_1 <= lambda_2`` and
    orthonormal eigenvectors ``e_1, e_2``. For a 1-D ridge in the 2-D ``(u, v)``
    domain the *minor* (ridge-transverse) subspace is spanned by the eigenvector
    ``e_1`` of the SMALLEST (most negative) eigenvalue ``lambda_1``. A point lies on
    the ridge iff

        |g . e_1| = 0          (gradient orthogonal to the minor eigenvector) AND
        lambda_1 < 0           (a genuine crest -- concave transverse, not a valley).

    SCMS drives seed points onto this set by repeatedly projecting a
    gradient-ascent step onto the minor subspace ``V = [e_1]``:

        x <- x + t e_1,   t = -(g . e_1) / lambda_1   (Newton on the transverse
                                                        gradient; lambda_1 < 0),

    iterating until ``|g . e_1| < tol``. Points that converge with ``lambda_1 < 0``
    are kept, deduplicated into a polyline, and lifted to 3D via the Mobius map.

Seam handling: the Mobius gluing ``r(2*pi, v) = r(0, -v)`` (a ``v``-flip across the
``u = 0 / 2*pi`` seam) is applied through a ``wrap`` callable so gradients/Hessians
stay correct as a ridge point crosses the seam and so iterates stay in-domain.
For the Mobius Rickness field the default wrap is
:func:`mobius_rickness.core.geometry.mobius_seam_wrap`.

numpy is OPTIONAL: it is reached only through
:func:`commons.core.optional.try_import`, never hard-imported at module top level.
Calling any ridge routine without numpy raises :class:`OptionalDependencyError`.
This module lives OUTSIDE ``core`` and is never imported by ``core``.
"""

from __future__ import annotations

from typing import Any, Callable, List, NamedTuple, Optional, Sequence, Tuple

from commons.core.optional import try_import

# Reuse the single deferred-dependency error type the accel backend already
# defines, so callers catch one exception for every optional numpy path.
from mobius_rickness.accel.numpy_backend import OptionalDependencyError
from mobius_rickness.core.geometry import mobius_seam_wrap
from mobius_rickness.core.mobius import (
    U_MAX,
    U_MIN,
    V_MAX,
    V_MIN,
    surface as mobius_surface,
)
from mobius_rickness.core.rickness import rickness

# A scalar field ``R(u, v) -> float`` and a domain ``wrap`` map ``(u, v) -> (u, v)``.
Field = Callable[[float, float], float]
Wrap = Callable[[float, float], Tuple[float, float]]

# numpy arrays are typed as ``Any`` (numpy is optional, never imported at top level).
NDArray = Any

# Central-difference step for gradient/Hessian; near-optimal for double precision
# second derivatives (truncation O(h**2) vs round-off O(eps/h**2)).
DEFAULT_H = 1e-4
# Convergence tolerance on the transverse gradient component |g . e_minor|.
DEFAULT_TOL = 1e-8
DEFAULT_MAX_ITER = 100
# Gradient-ascent fallback rate used only when the transverse curvature is not
# negative (lambda_minor >= 0); a genuine crest never enters this branch.
_ASCENT_RATE = 0.1

__all__ = [
    "OptionalDependencyError",
    "RidgePoint",
    "MobiusRidgePoint",
    "RidgeConvergence",
    "identity_wrap",
    "ridge_condition",
    "scms_point",
    "scms_point_history",
    "scms_ridge",
    "scms_ridge_history",
    "dedupe_ridge",
    "mobius_seeds",
    "trace_mobius_ridge",
    "verify_ridge",
    "U_MIN",
    "U_MAX",
    "V_MIN",
    "V_MAX",
]


class RidgePoint(NamedTuple):
    """A seed's SCMS outcome in the ``(u, v)`` domain (immutable)."""

    u: float
    v: float
    r: float  # field value R(u, v) at the converged location
    minor_eigval: float  # smallest Hessian eigenvalue lambda_1 (< 0 on a crest)
    grad_dot_minor: float  # g . e_1 (the transverse gradient component)
    iterations: int
    converged: bool


class MobiusRidgePoint(NamedTuple):
    """A converged Mobius ridge point lifted to 3D (immutable)."""

    u: float
    v: float
    x: float
    y: float
    z: float
    r: float
    minor_eigval: float
    grad_dot_minor: float


def _require_numpy() -> Any:
    """Return the numpy module or raise a clear :class:`OptionalDependencyError`."""
    numpy = try_import("numpy")
    if numpy is None:
        raise OptionalDependencyError(
            "the SCMS ridge backend requires numpy, which is not installed. "
            "Install the optional 'accel'/'ridge' extra, or use the pure zero-set "
            "tracer in mobius_rickness.core.tracer, which needs no third-party deps."
        )
    return numpy


def identity_wrap(u: float, v: float) -> Tuple[float, float]:
    """No-op domain wrap (for generic, non-seamed fields)."""
    return (u, v)


# ---------------------------------------------------------------------------
# Central-difference gradient and Hessian of a scalar field
# ---------------------------------------------------------------------------

def _grad(np: Any, f: Field, u: float, v: float, h: float) -> NDArray:
    """Central-difference gradient ``[dR/du, dR/dv]`` as a length-2 array."""
    fu = (f(u + h, v) - f(u - h, v)) / (2.0 * h)
    fv = (f(u, v + h) - f(u, v - h)) / (2.0 * h)
    return np.array([fu, fv], dtype=float)


def _hess(np: Any, f: Field, u: float, v: float, h: float) -> NDArray:
    """Central-difference symmetric Hessian ``[[Ruu, Ruv], [Ruv, Rvv]]``."""
    f0 = f(u, v)
    fuu = (f(u + h, v) - 2.0 * f0 + f(u - h, v)) / (h * h)
    fvv = (f(u, v + h) - 2.0 * f0 + f(u, v - h)) / (h * h)
    fuv = (
        f(u + h, v + h) - f(u + h, v - h) - f(u - h, v + h) + f(u - h, v - h)
    ) / (4.0 * h * h)
    return np.array([[fuu, fuv], [fuv, fvv]], dtype=float)


def _minor_eig(np: Any, H: NDArray) -> Tuple[float, NDArray]:
    """Return ``(lambda_min, e_min)`` -- smallest eigenpair of symmetric ``H``.

    Uses ``numpy.linalg.eigh`` (ascending eigenvalues); the minor / ridge-transverse
    direction is the eigenvector of the smallest (most negative) eigenvalue.
    """
    eigvals, eigvecs = np.linalg.eigh(H)
    return float(eigvals[0]), eigvecs[:, 0]


def _wrapped_field(field: Field, wrap: Wrap) -> Field:
    """Compose ``field`` with the domain ``wrap`` so every evaluation is in-domain."""

    def wf(u: float, v: float) -> float:
        wu, wv = wrap(u, v)
        return field(wu, wv)

    return wf


def _clamp_v(v: float, v_bounds: Optional[Tuple[float, float]]) -> float:
    """Clamp ``v`` into ``v_bounds`` if given (keeps iterates on the strip)."""
    if v_bounds is None:
        return v
    lo, hi = v_bounds
    return min(max(v, lo), hi)


# ---------------------------------------------------------------------------
# One SCMS step, factored out so the iterate-to-convergence loop and the
# history-returning variants share EXACTLY the same per-iteration behaviour.
# ---------------------------------------------------------------------------

def _scms_probe(
    np: Any, wf: Field, u: float, v: float, h: float
) -> Tuple[float, float, NDArray]:
    """Return ``(g . e_minor, lambda_minor, e_minor)`` at ``(u, v)`` (one probe)."""
    g = _grad(np, wf, u, v, h)
    H = _hess(np, wf, u, v, h)
    minor_eigval, e = _minor_eig(np, H)
    return float(g @ e), float(minor_eigval), e


def _scms_advance(
    np: Any,
    u: float,
    v: float,
    *,
    proj: float,
    minor_eigval: float,
    e: NDArray,
    step: float,
    wrap: Wrap,
    v_bounds: Optional[Tuple[float, float]],
) -> Tuple[float, float]:
    """Apply one projected SCMS update from ``(u, v)`` and return the next point.

    On a concave-transverse crest (``lambda_minor < 0``) this is the Newton update
    ``t = -(g . e_minor) / lambda_minor``; otherwise it falls back to a gentle
    gradient-ascent along the minor direction. The result is domain-wrapped and
    ``v``-clamped, identical to the body of :func:`scms_point`.
    """
    if minor_eigval < 0.0:
        t = -step * proj / minor_eigval
    else:
        t = _ASCENT_RATE * step * proj
    x = np.array([u, v], dtype=float) + t * e
    nu, nv = wrap(float(x[0]), float(x[1]))
    return nu, _clamp_v(nv, v_bounds)


# ---------------------------------------------------------------------------
# Ridge condition and single-seed SCMS
# ---------------------------------------------------------------------------

def ridge_condition(
    field: Field,
    u: float,
    v: float,
    *,
    wrap: Wrap = identity_wrap,
    h: float = DEFAULT_H,
) -> Tuple[float, float]:
    """Return ``(g . e_minor, lambda_minor)`` at ``(u, v)`` (numpy-backed).

    A point is on the Eberly 1-D ridge iff ``abs(g . e_minor) ~ 0`` and
    ``lambda_minor < 0``. Independent of the SCMS iteration, so tests can
    re-verify a converged point from scratch.
    """
    np = _require_numpy()
    wf = _wrapped_field(field, wrap)
    g = _grad(np, wf, u, v, h)
    H = _hess(np, wf, u, v, h)
    lam, e = _minor_eig(np, H)
    return float(g @ e), lam


def scms_point(
    field: Field,
    u0: float,
    v0: float,
    *,
    wrap: Wrap = identity_wrap,
    h: float = DEFAULT_H,
    tol: float = DEFAULT_TOL,
    max_iter: int = DEFAULT_MAX_ITER,
    v_bounds: Optional[Tuple[float, float]] = None,
    step: float = 1.0,
) -> RidgePoint:
    """Run Subspace-Constrained Mean Shift from one seed onto the ridge.

    Repeatedly project a gradient-ascent step onto the minor (most-negative-
    eigenvalue) subspace until ``|g . e_minor| < tol``. On a concave-transverse
    crest (``lambda_minor < 0``) the projected step is the Newton update
    ``t = -(g . e_minor) / lambda_minor``, which lands on the crest exactly for a
    locally quadratic field.
    """
    if max_iter < 1:
        raise ValueError("max_iter must be >= 1")
    if h <= 0.0:
        raise ValueError("h must be positive")
    np = _require_numpy()
    wf = _wrapped_field(field, wrap)

    u, v = wrap(u0, v0)
    v = _clamp_v(v, v_bounds)
    converged = False
    proj = float("nan")
    minor_eigval = float("nan")
    it = 0
    for it in range(1, max_iter + 1):
        proj, minor_eigval, e = _scms_probe(np, wf, u, v, h)
        if abs(proj) < tol:
            converged = True
            break
        u, v = _scms_advance(
            np, u, v,
            proj=proj, minor_eigval=minor_eigval, e=e,
            step=step, wrap=wrap, v_bounds=v_bounds,
        )

    r = wf(u, v)
    return RidgePoint(
        u=float(u),
        v=float(v),
        r=float(r),
        minor_eigval=float(minor_eigval),
        grad_dot_minor=float(proj),
        iterations=it,
        converged=converged,
    )


class RidgeConvergence(NamedTuple):
    """Per-iteration record of a whole seed cloud migrating onto the ridge.

    ``snapshots[k]`` is an ``(n_seeds, 2)`` numpy array of every seed's ``(u, v)``
    position at the START of SCMS iteration ``k`` (before that iteration's step);
    ``residuals[k]`` is the mean ridge-condition residual
    ``mean_i |g_i . e_minor_i|`` over the cloud at that same snapshot -- the number
    that shrinks toward ``0`` as the cloud settles onto the crest. ``points`` is the
    final per-seed :class:`RidgePoint` (unfiltered, in seed order), so callers can
    reproduce :func:`scms_ridge` by keeping ``converged and minor_eigval < 0``.
    """

    snapshots: List[NDArray]
    residuals: List[float]
    points: List[RidgePoint]


def scms_point_history(
    field: Field,
    u0: float,
    v0: float,
    *,
    wrap: Wrap = identity_wrap,
    h: float = DEFAULT_H,
    tol: float = DEFAULT_TOL,
    max_iter: int = DEFAULT_MAX_ITER,
    v_bounds: Optional[Tuple[float, float]] = None,
    step: float = 1.0,
) -> List[Tuple[float, float]]:
    """SCMS from one seed, returning the full ``(u, v)`` trajectory it walks.

    Identical iteration to :func:`scms_point` (same probe + projected step) but it
    records every visited point: the returned list starts at the domain-wrapped
    seed and appends each subsequent iterate up to and including the converged
    location. The final element is where :func:`scms_point` would land.
    """
    if max_iter < 1:
        raise ValueError("max_iter must be >= 1")
    if h <= 0.0:
        raise ValueError("h must be positive")
    np = _require_numpy()
    wf = _wrapped_field(field, wrap)

    u, v = wrap(u0, v0)
    v = _clamp_v(v, v_bounds)
    history: List[Tuple[float, float]] = [(float(u), float(v))]
    for _ in range(1, max_iter + 1):
        proj, minor_eigval, e = _scms_probe(np, wf, u, v, h)
        if abs(proj) < tol:
            break
        u, v = _scms_advance(
            np, u, v,
            proj=proj, minor_eigval=minor_eigval, e=e,
            step=step, wrap=wrap, v_bounds=v_bounds,
        )
        history.append((float(u), float(v)))
    return history


def scms_ridge_history(
    field: Field,
    seeds: Sequence[Tuple[float, float]],
    *,
    wrap: Wrap = identity_wrap,
    h: float = DEFAULT_H,
    tol: float = DEFAULT_TOL,
    max_iter: int = DEFAULT_MAX_ITER,
    v_bounds: Optional[Tuple[float, float]] = None,
    step: float = 1.0,
) -> RidgeConvergence:
    """Advance ALL seeds together, one SCMS step per iteration, recording the cloud.

    Every seed takes the same per-step update as :func:`scms_point`; a seed that
    reaches the ridge (``|g . e_minor| < tol``) is frozen so its final position
    matches the independent :func:`scms_point`/:func:`scms_ridge` result. Returns a
    :class:`RidgeConvergence` whose ``snapshots``/``residuals`` are the per-iteration
    scatter and mean residual (the residual is non-increasing as the cloud settles),
    and whose ``points`` are the final per-seed outcomes in seed order.
    """
    if max_iter < 1:
        raise ValueError("max_iter must be >= 1")
    if h <= 0.0:
        raise ValueError("h must be positive")
    if len(seeds) < 1:
        raise ValueError("seeds must be non-empty")
    np = _require_numpy()
    wf = _wrapped_field(field, wrap)

    n = len(seeds)
    us: List[float] = []
    vs: List[float] = []
    for (u0, v0) in seeds:
        wu, wv = wrap(u0, v0)
        us.append(float(wu))
        vs.append(_clamp_v(float(wv), v_bounds))

    converged = [False] * n
    last_proj = [float("nan")] * n
    last_minor = [float("nan")] * n
    iters = [0] * n

    snapshots: List[NDArray] = []
    residuals: List[float] = []

    for it in range(1, max_iter + 1):
        # Snapshot the cloud BEFORE this iteration's step, and probe every seed.
        snapshots.append(
            np.array([[us[i], vs[i]] for i in range(n)], dtype=float)
        )
        pending: List[Tuple[int, float, float, NDArray]] = []
        abs_projs: List[float] = []
        for i in range(n):
            if converged[i]:
                abs_projs.append(abs(last_proj[i]))
                continue
            proj, minor_eigval, e = _scms_probe(np, wf, us[i], vs[i], h)
            last_proj[i] = proj
            last_minor[i] = minor_eigval
            abs_projs.append(abs(proj))
            if abs(proj) < tol:
                converged[i] = True
                iters[i] = it
            else:
                iters[i] = it
                pending.append((i, proj, minor_eigval, e))
        residuals.append(float(sum(abs_projs) / n))
        if not pending:  # every seed has reached the ridge
            break
        # Apply this iteration's projected step to the not-yet-converged seeds.
        for i, proj, minor_eigval, e in pending:
            nu, nv = _scms_advance(
                np, us[i], vs[i],
                proj=proj, minor_eigval=minor_eigval, e=e,
                step=step, wrap=wrap, v_bounds=v_bounds,
            )
            us[i], vs[i] = nu, nv

    points = [
        RidgePoint(
            u=us[i],
            v=vs[i],
            r=float(wf(us[i], vs[i])),
            minor_eigval=last_minor[i],
            grad_dot_minor=last_proj[i],
            iterations=iters[i],
            converged=converged[i],
        )
        for i in range(n)
    ]
    return RidgeConvergence(snapshots=snapshots, residuals=residuals, points=points)


def dedupe_ridge(points: Sequence[RidgePoint], snap: float) -> List[RidgePoint]:
    """Deduplicate ridge points by snapping ``(u, v)`` to a grid; order by ``u``.

    Turns the scattered converged seeds into an ordered polyline. Keeps the first
    point seen per snapped cell (immutable: builds and returns a new list).
    """
    if snap <= 0.0:
        raise ValueError("snap must be positive")
    seen: dict = {}
    for p in points:
        key = (round(p.u / snap), round(p.v / snap))
        if key not in seen:
            seen[key] = p
    return sorted(seen.values(), key=lambda p: (p.u, p.v))


def scms_ridge(
    field: Field,
    seeds: Sequence[Tuple[float, float]],
    *,
    wrap: Wrap = identity_wrap,
    h: float = DEFAULT_H,
    tol: float = DEFAULT_TOL,
    max_iter: int = DEFAULT_MAX_ITER,
    v_bounds: Optional[Tuple[float, float]] = None,
    step: float = 1.0,
    snap: Optional[float] = None,
) -> List[RidgePoint]:
    """Run SCMS from every seed; keep genuine ridge points, optionally deduped.

    A kept point converged (``|g . e_minor| < tol``) AND satisfies the crest
    condition ``lambda_minor < 0``. When ``snap`` is given the survivors are
    deduplicated into an ordered polyline.
    """
    raw = [
        scms_point(
            field,
            u0,
            v0,
            wrap=wrap,
            h=h,
            tol=tol,
            max_iter=max_iter,
            v_bounds=v_bounds,
            step=step,
        )
        for (u0, v0) in seeds
    ]
    kept = [p for p in raw if p.converged and p.minor_eigval < 0.0]
    if snap is not None:
        kept = dedupe_ridge(kept, snap)
    return kept


def verify_ridge(
    field: Field,
    points: Sequence[RidgePoint],
    *,
    wrap: Wrap = identity_wrap,
    h: float = DEFAULT_H,
    tol: float = 1e-6,
) -> None:
    """Assert every point satisfies the Eberly ridge condition (re-evaluated).

    Raises :class:`AssertionError` if any point has ``abs(g . e_minor) >= tol`` or
    ``lambda_minor >= 0`` (not a genuine crest).
    """
    for p in points:
        proj, lam = ridge_condition(field, p.u, p.v, wrap=wrap, h=h)
        assert abs(proj) < tol, (
            f"gradient not orthogonal to minor eigvec at u={p.u}, v={p.v}: "
            f"|g . e_minor|={abs(proj):.3e} >= tol {tol:.0e}"
        )
        assert lam < 0.0, (
            f"minor eigenvalue not negative at u={p.u}, v={p.v}: "
            f"lambda_minor={lam:.3e} (a valley, not a crest)"
        )


# ---------------------------------------------------------------------------
# Mobius-specific ridge: seeds, seam-wrapped SCMS, 3D lift
# ---------------------------------------------------------------------------

def mobius_seeds(n_u: int = 24, n_v: int = 5) -> List[Tuple[float, float]]:
    """Grid of ``(u, v)`` seeds over the Mobius domain (interior ``v`` samples)."""
    if n_u < 1 or n_v < 1:
        raise ValueError("n_u and n_v must be >= 1")
    du = (U_MAX - U_MIN) / n_u  # cell-centre u samples avoid the exact seam
    dv = (V_MAX - V_MIN) / (n_v + 1)
    seeds: List[Tuple[float, float]] = []
    for i in range(n_u):
        u = U_MIN + (i + 0.5) * du
        for j in range(1, n_v + 1):
            v = V_MIN + j * dv
            seeds.append((u, v))
    return seeds


def trace_mobius_ridge(
    *,
    n_u: int = 24,
    n_v: int = 5,
    h: float = DEFAULT_H,
    tol: float = DEFAULT_TOL,
    max_iter: int = DEFAULT_MAX_ITER,
    snap: Optional[float] = None,
    field: Field = rickness,
) -> List[MobiusRidgePoint]:
    """Trace the SCMS crest of the Mobius Rickness field, lifted to 3D.

    Uses the seam-aware :func:`mobius_rickness.core.geometry.mobius_seam_wrap` so a
    ridge point crossing ``u = 0 / 2*pi`` continues smoothly under the ``v``-flip,
    and clamps ``v`` to the strip ``[V_MIN, V_MAX]``.
    """
    if snap is None:
        snap = min((U_MAX - U_MIN) / n_u, (V_MAX - V_MIN) / (n_v + 1)) / 4.0
    seeds = mobius_seeds(n_u=n_u, n_v=n_v)
    kept = scms_ridge(
        field,
        seeds,
        wrap=mobius_seam_wrap,
        h=h,
        tol=tol,
        max_iter=max_iter,
        v_bounds=(V_MIN, V_MAX),
        step=1.0,
        snap=snap,
    )
    lifted: List[MobiusRidgePoint] = []
    for p in kept:
        x, y, z = mobius_surface(p.u, p.v)
        lifted.append(
            MobiusRidgePoint(
                u=p.u,
                v=p.v,
                x=x,
                y=y,
                z=z,
                r=p.r,
                minor_eigval=p.minor_eigval,
                grad_dot_minor=p.grad_dot_minor,
            )
        )
    return lifted
