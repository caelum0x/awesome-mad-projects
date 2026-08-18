"""Vectorised numpy fast-paths mirroring the pure scalar distance core.

Each routine reproduces, over a whole batch of points at once, a pairwise
distance that :mod:`calabi_yau_latent.core.distance` computes one pair at a time.
numpy is NEVER imported at module top level: every function calls
:func:`commons.core.optional.try_import` lazily and raises
:class:`OptionalDependencyError` when numpy is absent, so importing this module
with the standard library alone never fails.

Parity honesty
--------------
The naive metrics are plain squared differences; the wrap-aware metrics route the
angular gap through ``mod 2*pi`` and a ``> pi`` fold, exactly as
:func:`calabi_yau_latent.core.distance.circle_delta` does. The pure core and numpy
agree to within a few ULP; the parity test asserts ``allclose(atol=1e-12)``.
"""

from __future__ import annotations

from typing import Any, Sequence

from commons.core.optional import try_import


class OptionalDependencyError(RuntimeError):
    """Raised when a numpy fast-path is requested but numpy is unavailable.

    The pure core never raises this; only these deferred accel routines do, and
    only when the caller invokes them without numpy installed.
    """


def _numpy() -> Any:
    """Return the numpy module, or raise :class:`OptionalDependencyError`.

    numpy is imported LAZILY via :func:`commons.core.optional.try_import`, so this
    module stays importable with the standard library alone.
    """
    np = try_import("numpy")
    if np is None:
        raise OptionalDependencyError(
            "numpy is required for calabi_yau_latent.accel fast-paths but is not "
            "installed; install the 'viz' extra (pip install -e '.[viz]') or use "
            "the pure calabi_yau_latent.core functions instead"
        )
    return np


def _as_matrix(rows: Sequence[Sequence[float]], name: str) -> Any:
    """Return ``rows`` as a float 2-D numpy array (raises on empty)."""
    np = _numpy()
    if len(rows) == 0:
        raise ValueError(f"{name} must be non-empty")
    return np.asarray(rows, dtype=np.float64)


def _angular_gap(np: Any, angles: Any) -> Any:
    """Return the ``(n, n, m)`` shortest signed angular gaps (mod 2*pi, folded)."""
    two_pi = 2.0 * np.pi
    diff = angles[:, None, :] - angles[None, :, :]
    gap = np.mod(diff, two_pi)
    gap = np.where(gap > np.pi, gap - two_pi, gap)
    return gap


def naive_angular_distance_matrix(angles: Sequence[Sequence[float]]) -> Any:
    """``(n, n)`` Euclidean distance on RAW angle values (no wrap-around)."""
    np = _numpy()
    arr = _as_matrix(angles, "angles")
    diff = arr[:, None, :] - arr[None, :, :]
    return np.sqrt(np.sum(diff * diff, axis=2))


def toroidal_angular_distance_matrix(angles: Sequence[Sequence[float]]) -> Any:
    """``(n, n)`` radius-independent torus distance (shortest angular arcs)."""
    np = _numpy()
    arr = _as_matrix(angles, "angles")
    gap = _angular_gap(np, arr)
    return np.sqrt(np.sum(gap * gap, axis=2))


def toroidal_distance_matrix(
    extended: Sequence[Sequence[float]],
    angles: Sequence[Sequence[float]],
    radii: Sequence[float],
) -> Any:
    """``(n, n)`` full toroidal distance: Euclidean on R^k + radius-scaled arcs."""
    np = _numpy()
    ang = _as_matrix(angles, "angles")
    r = np.asarray(radii, dtype=np.float64)
    if r.shape[0] != ang.shape[1]:
        raise ValueError("radii length must match the number of compact circles")
    gap = _angular_gap(np, ang)
    total = np.sum((r[None, None, :] * gap) ** 2, axis=2)
    ext = np.asarray(extended, dtype=np.float64) if len(extended) else None
    if ext is not None and ext.size:
        ediff = ext[:, None, :] - ext[None, :, :]
        total = total + np.sum(ediff * ediff, axis=2)
    return np.sqrt(total)
