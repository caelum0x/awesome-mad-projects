"""padic_embeddings.core -- the pure p-adic engine (stdlib + commons.core only).

Every module here imports ONLY the standard library and :mod:`commons.core`;
nothing imports an adapter (render / cli / viz) or hard-imports numpy/matplotlib,
so the core stays deterministic and dependency free. The public API is re-exported
for convenient one-stop imports.

Layers:
    * :mod:`~padic_embeddings.core.padic`     -- valuation, |x|_p, distance,
      exact ultrametric triple check.
    * :mod:`~padic_embeddings.core.embedding` -- map items to Z, distance matrix,
      k-nearest-neighbor, exhaustive ultrametric verifier, residue-class balls.
"""

from __future__ import annotations

from padic_embeddings.core.embedding import (
    DEFAULT_MODULUS,
    Item,
    cluster_by_valuation,
    distance_matrix,
    embed,
    embed_item,
    nearest_neighbors,
    sample_integers,
    verify_ultrametric,
)
from padic_embeddings.core.padic import (
    Number,
    distance,
    distance_exact,
    is_prime,
    is_ultrametric_triple,
    p_adic_abs,
    p_adic_abs_exact,
    valuation,
)

__all__ = [
    # padic math
    "Number",
    "is_prime",
    "valuation",
    "p_adic_abs",
    "p_adic_abs_exact",
    "distance",
    "distance_exact",
    "is_ultrametric_triple",
    # embedding
    "Item",
    "DEFAULT_MODULUS",
    "embed_item",
    "embed",
    "distance_matrix",
    "nearest_neighbors",
    "verify_ultrametric",
    "cluster_by_valuation",
    "sample_integers",
]
