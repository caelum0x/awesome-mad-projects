"""Tests for the SCMS ridge-convergence history + its animation (GIF + MP4).

DEFERRED and layered so the suite behaves on both interpreters:

    * The **history** variants (:func:`scms_ridge_history` /
      :func:`scms_point_history`) need only numpy -> the module gate is
      ``pytest.importorskip("numpy")``, so everything SKIPS on the stdlib-only
      system interpreter and RUNS on the venv.
    * The **GIF** tests additionally ``importorskip`` matplotlib AND Pillow.
    * The **MP4** tests ``importorskip`` matplotlib, then :func:`pytest.skip` when
      the ffmpeg writer is unavailable.
    * The **negative** test forces ffmpeg unavailable (monkeypatching
      :func:`shutil.which` to ``None``) and asserts the MP4 saver raises
      :class:`OptionalDependencyError`.

The history tests assert the animation's core claim numerically: advancing the
whole seed cloud one SCMS step at a time drives the mean ridge-condition residual
DOWN to ~0 (monotonically on a near-quadratic field), and the final positions agree
with the independent iterate-to-convergence :func:`scms_ridge`. Every animation is
rendered SHORT (few seeds, few iterations, coarse backdrop) into ``tmp_path``.
"""

from __future__ import annotations

import math
import os

import pytest

np = pytest.importorskip("numpy")

from mobius_rickness.ridge.scms import (  # noqa: E402
    ridge_condition,
    scms_point_history,
    scms_ridge,
    scms_ridge_history,
)

_GIF_SIGNATURES = (b"GIF87a", b"GIF89a")
_MIN_BYTES = 1024

# Near-quadratic synthetic field with a known analytic ridge ``v = sin(u)``; SCMS
# Newton-converges monotonically on it, so the mean residual is non-increasing.
_TOL = 1e-9
_MAX_ITER = 200
_VERIFY_TOL = 1e-6

# Small render parameters shared by the animation tests to keep them fast.
_FAST = dict(
    seed_n_u=6,
    seed_n_v=2,
    backdrop_n_u=31,
    backdrop_n_v=13,
    tol=1e-8,
    max_iter=30,
    hold=2,
    fps=5,
)


def _synthetic(u: float, v: float) -> float:
    """Field whose crest of maxima is the analytic ridge ``v = sin(u)``."""
    return -((v - math.sin(u)) ** 2)


def _synthetic_seeds() -> list:
    us = [0.3, 1.0, 2.0, 3.5, 5.0]
    vs = [-0.8, -0.2, 0.0, 0.4, 0.9]
    return [(u, v) for u in us for v in vs]


def _assert_valid_gif(path: str) -> None:
    assert os.path.exists(path), f"expected GIF at {path}"
    with open(path, "rb") as handle:
        head = handle.read(6)
    assert head in _GIF_SIGNATURES, f"not a GIF signature: {head!r}"
    assert os.path.getsize(path) > _MIN_BYTES, "GIF is suspiciously small (< 1 KiB)"


def _assert_valid_mp4(path: str) -> None:
    assert os.path.exists(path), f"expected MP4 at {path}"
    with open(path, "rb") as handle:
        head = handle.read(12)
    assert head[4:8] == b"ftyp", f"not an ISO-BMFF/MP4 (bytes 4..8): {head[4:8]!r}"
    assert os.path.getsize(path) > _MIN_BYTES, "MP4 is suspiciously small (< 1 KiB)"


# ---------------------------------------------------------------------------
# History: residual shrinks monotonically to ~0 and stays consistent
# ---------------------------------------------------------------------------

def test_scms_ridge_history_residual_decreases_to_zero() -> None:
    seeds = _synthetic_seeds()
    history = scms_ridge_history(_synthetic, seeds, tol=_TOL, max_iter=_MAX_ITER)
    residuals = history.residuals
    assert len(residuals) >= 2, "expected several iteration snapshots"
    assert len(history.snapshots) == len(residuals)
    assert all(s.shape == (len(seeds), 2) for s in history.snapshots)
    # Monotonically non-increasing (allow a tiny numerical wiggle on a quadratic).
    for prev, nxt in zip(residuals, residuals[1:]):
        assert nxt <= prev + 1e-12, (
            f"mean residual increased: {prev:.3e} -> {nxt:.3e}"
        )
    # It genuinely shrinks, and the final scatter sits on the ridge.
    assert residuals[0] > residuals[-1]
    assert residuals[-1] < _TOL, f"final residual {residuals[-1]:.3e} not < {_TOL:.0e}"


def test_scms_ridge_history_matches_scms_ridge() -> None:
    seeds = _synthetic_seeds()
    history = scms_ridge_history(_synthetic, seeds, tol=_TOL, max_iter=_MAX_ITER)
    kept_hist = [p for p in history.points if p.converged and p.minor_eigval < 0.0]
    kept_ref = scms_ridge(_synthetic, seeds, tol=_TOL, max_iter=_MAX_ITER)
    assert len(kept_hist) == len(kept_ref)
    for a, b in zip(kept_hist, kept_ref):
        assert abs(a.u - b.u) < 1e-9, f"u mismatch: {a.u} vs {b.u}"
        assert abs(a.v - b.v) < 1e-9, f"v mismatch: {a.v} vs {b.v}"
    # Every kept final point really is on the ridge (re-verified from the field).
    for p in kept_hist:
        proj, lam = ridge_condition(_synthetic, p.u, p.v)
        assert abs(proj) < _VERIFY_TOL
        assert lam < 0.0


def test_scms_point_history_walks_from_seed_onto_ridge() -> None:
    history = scms_point_history(_synthetic, 2.0, 0.9, tol=_TOL, max_iter=_MAX_ITER)
    assert history[0] == (2.0, 0.9), "history must start at the (wrapped) seed"
    assert len(history) >= 2, "expected at least one SCMS step"
    u_end, v_end = history[-1]
    # The final point satisfies the Eberly ridge condition (it lands on v = sin u).
    proj, lam = ridge_condition(_synthetic, u_end, v_end)
    assert abs(proj) < _VERIFY_TOL
    assert lam < 0.0
    assert abs(v_end - math.sin(u_end)) < 1e-5


def test_scms_ridge_history_validates_arguments() -> None:
    with pytest.raises(ValueError):
        scms_ridge_history(_synthetic, [(0.0, 0.0)], max_iter=0)
    with pytest.raises(ValueError):
        scms_ridge_history(_synthetic, [], max_iter=10)


# ---------------------------------------------------------------------------
# GIF export (matplotlib + Pillow + numpy -> runs on the venv)
# ---------------------------------------------------------------------------

def test_save_ridge_convergence_gif(tmp_path) -> None:
    pytest.importorskip("matplotlib")
    pytest.importorskip("PIL")
    from mobius_rickness.adapters import animate_scms

    path = str(tmp_path / "convergence.gif")
    out = animate_scms.save_ridge_convergence_gif(path, **_FAST)
    assert out == path
    _assert_valid_gif(path)


def test_cli_animate_scms_writes_convergence_gif(tmp_path) -> None:
    pytest.importorskip("matplotlib")
    pytest.importorskip("PIL")
    from mobius_rickness.adapters import cli

    outdir = str(tmp_path / "anim")
    text = cli.run(["animate", outdir, "--scms"])
    assert "SCMS ridge-convergence GIF" in text
    files = set(os.listdir(outdir))
    assert {"mobius_rotating.gif", "mobius_ridge_convergence.gif"} <= files
    _assert_valid_gif(os.path.join(outdir, "mobius_ridge_convergence.gif"))


def test_convergence_gif_validates_arguments() -> None:
    pytest.importorskip("matplotlib")
    pytest.importorskip("PIL")
    from mobius_rickness.adapters import animate_scms

    with pytest.raises(ValueError):
        animate_scms.save_ridge_convergence_gif("unused.gif", fps=0)
    with pytest.raises(ValueError):
        animate_scms.save_ridge_convergence_gif("unused.gif", hold=-1)


# ---------------------------------------------------------------------------
# MP4 export (matplotlib + ffmpeg -> skip when ffmpeg writer unavailable)
# ---------------------------------------------------------------------------

def _require_ffmpeg() -> None:
    pytest.importorskip("matplotlib")
    from mobius_rickness.adapters.animate_3d import ffmpeg_is_available

    if not ffmpeg_is_available():
        pytest.skip("ffmpeg writer unavailable (no ffmpeg binary on PATH)")


def test_save_ridge_convergence_mp4(tmp_path) -> None:
    _require_ffmpeg()
    from mobius_rickness.adapters import animate_scms

    path = str(tmp_path / "convergence.mp4")
    out = animate_scms.save_ridge_convergence_mp4(path, **_FAST)
    assert out == path
    _assert_valid_mp4(path)


# ---------------------------------------------------------------------------
# Negative test: ffmpeg forced unavailable -> OptionalDependencyError
# ---------------------------------------------------------------------------

def test_mp4_raises_when_ffmpeg_unavailable(tmp_path, monkeypatch) -> None:
    pytest.importorskip("matplotlib")
    import shutil

    from mobius_rickness.adapters import animate_scms
    from mobius_rickness.adapters.animate_3d import ffmpeg_is_available
    from mobius_rickness.adapters.viz import OptionalDependencyError

    # Force shutil.which("ffmpeg") -> None so the availability probe fails, even
    # though ffmpeg may really be installed here.
    monkeypatch.setattr(shutil, "which", lambda _name: None)
    assert ffmpeg_is_available() is False

    with pytest.raises(OptionalDependencyError):
        animate_scms.save_ridge_convergence_mp4(str(tmp_path / "nope.mp4"), **_FAST)


def test_convergence_mp4_validates_arguments() -> None:
    pytest.importorskip("matplotlib")
    from mobius_rickness.adapters import animate_scms

    with pytest.raises(ValueError):
        animate_scms.save_ridge_convergence_mp4("unused.mp4", fps=0)
