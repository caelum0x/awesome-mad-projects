"""calabi_yau_latent.adapters -- presentation and I/O layers.

These modules may import :mod:`calabi_yau_latent.core`, but the core never imports
them. matplotlib is reached only lazily through
:func:`commons.core.optional.try_import`, so importing any adapter with the
standard library alone never fails; the optional PNG renderer raises a clear
:class:`~calabi_yau_latent.adapters.viz.OptionalDependencyError` only when
explicitly invoked without matplotlib installed.
"""

from __future__ import annotations
