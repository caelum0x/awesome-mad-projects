"""padic_embeddings -- an embedding space governed by the p-adic metric.

Ordinary machine-learning embeddings place items in ``R^d`` and use Euclidean (or
cosine) distance: two points are close when their coordinates are numerically near.
This package instead maps each item (an integer, or a string hashed into ``Z``) to a
single integer coordinate and measures closeness with the **p-adic** metric ``d_p``:
a number is *small* when it is highly divisible by a fixed prime ``p``. The result is
an *ultrametric* space with a natural tree / hierarchy structure -- the residue class
of an integer modulo ``p**k`` is exactly a ball of radius ``p**(-k)``.

The pure math lives under :mod:`padic_embeddings.core` (stdlib + ``commons.core``
only) and its public API is re-exported here. Text rendering and the optional
matplotlib PNG export live under :mod:`padic_embeddings.adapters` -- the latter is
lazily guarded through :func:`commons.core.optional.try_import`.
"""

from __future__ import annotations

from padic_embeddings import core
from padic_embeddings.core import (
    DEFAULT_MODULUS,
    cluster_by_valuation,
    distance,
    distance_exact,
    distance_matrix,
    embed,
    embed_item,
    is_prime,
    is_ultrametric_triple,
    nearest_neighbors,
    p_adic_abs,
    p_adic_abs_exact,
    sample_integers,
    valuation,
    verify_ultrametric,
)

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "core",
    # padic math
    "is_prime",
    "valuation",
    "p_adic_abs",
    "p_adic_abs_exact",
    "distance",
    "distance_exact",
    "is_ultrametric_triple",
    # embedding
    "DEFAULT_MODULUS",
    "embed_item",
    "embed",
    "distance_matrix",
    "nearest_neighbors",
    "verify_ultrametric",
    "cluster_by_valuation",
    "sample_integers",
]
