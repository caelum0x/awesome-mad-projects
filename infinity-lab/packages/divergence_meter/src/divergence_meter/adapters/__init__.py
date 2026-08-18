"""divergence_meter.adapters -- presentation and I/O layers.

These modules may import :mod:`divergence_meter.core` and
:mod:`commons.adapters`, but the core never imports them. matplotlib is reached
only lazily through :func:`commons.core.optional.try_import`, so importing any
adapter with the standard library alone never fails; the optional PNG exporter
raises a clear :class:`~divergence_meter.adapters.viz.OptionalDependencyError`
only when explicitly invoked without matplotlib installed.
"""

from __future__ import annotations
