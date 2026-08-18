"""domain_expansion.adapters -- presentation and I/O layers.

These modules may import :mod:`domain_expansion.core` and
:mod:`commons.adapters`, but the core never imports them. matplotlib is reached
only lazily through :func:`commons.core.optional.try_import`, so importing any
adapter with the standard library alone never fails; the optional PNG exporter
raises a clear :class:`~domain_expansion.adapters.viz.OptionalDependencyError`
only when explicitly invoked without matplotlib.
"""

from __future__ import annotations
