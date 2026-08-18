"""mobius_rickness.adapters -- presentation & entry-point layer.

Adapters MAY import :mod:`mobius_rickness.core` and :mod:`commons.adapters`, but
the reverse is forbidden: nothing under ``core`` imports anything here, so the
core stays a pure, dependency-free math layer (see the purity test).

Modules:
    * :mod:`mobius_rickness.adapters.viz` -- deterministic ASCII renderers (a
      ``+/-`` sign map of the Rickness field with the traced Central Finite Curve
      overlaid, a shaded ``K_Rick`` heatmap, and the reproduced curvature table).
      All are stdlib-only via :mod:`commons.adapters.ascii_art`. An optional 3D
      PNG export is guarded behind ``commons.core.optional`` (matplotlib) and is
      deferred by default.
    * :mod:`mobius_rickness.adapters.animate_3d` -- a rotating 3-D animation
      (GIF/MP4) of the Mobius strip overlaying BOTH Central Finite Curve readings
      (the traced ``R^{-1}(0)`` zero curve and the SCMS ridge) under an orbiting
      camera. Deferred behind matplotlib + Pillow (GIF) / ffmpeg (MP4).
    * :mod:`mobius_rickness.adapters.animate_scms` -- a 2-D ``(u, v)`` animation
      (GIF/MP4) of the SCMS seed cloud converging onto the Rickness ridge.
    * :mod:`mobius_rickness.adapters.animate_panels` -- a 2x2 four-panel composite
      explainer (GIF/MP4) telling the whole Central Finite Curve story on a shared
      timeline (Mobius ``K < 0`` scan, zero-set ``R^{-1}(0)`` draw-in, SCMS ridge
      convergence, torus ``K`` sign pattern). Deferred behind matplotlib + Pillow
      (GIF) / ffmpeg (MP4) + numpy.
    * :mod:`mobius_rickness.adapters.cli` -- ``argparse`` command-line front end
      with subcommands ``curvature``, ``trace``, ``torus``, ``all`` and ``animate``.
"""

from __future__ import annotations

__all__ = ["viz", "animate_3d", "animate_scms", "animate_panels", "cli"]
