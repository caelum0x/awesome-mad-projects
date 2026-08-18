"""gojo_infinity.adapters -- presentation & entry-point layer.

Adapters MAY import :mod:`gojo_infinity.core` and :mod:`commons.adapters`, but
the reverse is forbidden: nothing under ``core`` imports anything here, so the
core stays a pure, dependency-free math layer (see the purity test).

Modules:
    * :mod:`gojo_infinity.adapters.viz` -- deterministic ASCII renderers for the
      four lenses (always available, stdlib only) plus an optional PNG export
      guarded behind ``commons.core.optional`` (matplotlib), deferred by default.
    * :mod:`gojo_infinity.adapters.cli` -- ``argparse`` command-line front end
      with subcommands ``zeno``, ``measure``, ``riemannian``, ``topology`` and
      ``all``.
"""

from __future__ import annotations

__all__ = ["viz", "cli"]
