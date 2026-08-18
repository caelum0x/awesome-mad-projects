"""calabi_yau_latent -- a compactified latent space over R^k x T^m (TOY).

A small, runnable model of a latent space where a few dimensions are *large /
extended* (``R^k``) and the rest are *compactified* -- periodic, small-radius
circles forming a torus ``T^m``. Structure planted in the compact, periodic axes
is easy to miss under a naive Euclidean view (it tears wrap-around clusters
apart), but reappears once the periodic topology is respected.

HONEST CAVEAT: this is a flat product space, NOT a real Calabi-Yau manifold. A
real Calabi-Yau space has a Ricci-flat metric with special SU(n) holonomy; nothing
here reproduces that. The only ingredients we borrow are compactification (small,
periodic dimensions) and wrap-around topology (distances that respect
periodicity). The "holonomy" demo is a deliberately labelled cartoon. See
README.md for the full caveat.

The pure math lives under :mod:`calabi_yau_latent.core` (stdlib + ``commons.core``
only) and its public API is re-exported here. Optional numpy fast-paths live in
:mod:`calabi_yau_latent.accel`; matplotlib rendering lives in
:mod:`calabi_yau_latent.adapters` -- all lazily guarded.
"""

from __future__ import annotations

from calabi_yau_latent import core
from calabi_yau_latent.core import (
    DEFAULT,
    TWO_PI,
    CompactifiedLatentSpace,
    CYConfig,
    LatentPoint,
    circle_delta,
    cluster,
    gauss,
    generate,
    holonomy_angle,
    loop_trace,
    make_space,
    make_stream,
    naive_angular_distance,
    naive_distance,
    nearest_neighbor,
    num_clusters,
    purity,
    toroidal_angular_distance,
    toroidal_distance,
    transport_around_loop,
)

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "core",
    # config
    "CYConfig",
    "DEFAULT",
    # latent
    "TWO_PI",
    "LatentPoint",
    "CompactifiedLatentSpace",
    # distance
    "circle_delta",
    "naive_distance",
    "naive_angular_distance",
    "toroidal_distance",
    "toroidal_angular_distance",
    # sampling
    "make_stream",
    "gauss",
    # data
    "make_space",
    "generate",
    # clustering
    "nearest_neighbor",
    "cluster",
    "num_clusters",
    "purity",
    # holonomy
    "transport_around_loop",
    "holonomy_angle",
    "loop_trace",
]
