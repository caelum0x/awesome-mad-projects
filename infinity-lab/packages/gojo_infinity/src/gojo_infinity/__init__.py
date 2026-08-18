"""gojo_infinity -- Gojo Satoru's "Infinity" through four mathematical lenses.

Faithful to Achmad Roykhan Sabiq's essay, each lens reaches its own verdict:

    Lens 1  Geometric series / Zeno         -> FRAGILE
    Lens 2  Lebesgue measure                -> FRAGILE
    Lens 3  Riemannian conformal geometry   -> FORMIDABLE
    Lens 4  Topology / World-Cutting Slash  -> FALLS

The pure math lives under :mod:`gojo_infinity.core` and imports only the
standard library plus :mod:`commons.core`. Import the lenses from there, e.g.::

    from gojo_infinity.core import partial_sum_table, calibrate, conclusion_table
"""

from __future__ import annotations

__version__ = "0.1.0"
