"""central_finite_curve.adapters -- presentation and I/O layers.

These modules may import :mod:`central_finite_curve.core` and
:mod:`commons.adapters`, but the core never imports them. matplotlib / Pillow /
ffmpeg are reached only lazily through :func:`commons.core.optional.try_import`, so
importing any adapter with the standard library alone never fails; the optional
renderers raise a clear :class:`~central_finite_curve.adapters.viz.OptionalDependency
Error` only when explicitly invoked without their backend.
"""

from __future__ import annotations
