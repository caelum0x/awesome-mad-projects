"""calabi_yau_latent.core -- the pure engine (stdlib + commons.core only).

Every module here imports ONLY the standard library and :mod:`commons.core`;
nothing imports an adapter (cli / ascii_viz / viz) or hard-imports numpy /
matplotlib, so the core stays deterministic and dependency free. The public API
is re-exported for convenient one-stop imports.

HONESTY: this models a flat ``R^k x T^m`` product space (extended reals times a
torus), NOT a Ricci-flat Calabi-Yau manifold. See the package README caveat.

Modules:
    * :mod:`~calabi_yau_latent.core.config`      -- immutable run configuration.
    * :mod:`~calabi_yau_latent.core.latent`      -- LatentPoint + the space.
    * :mod:`~calabi_yau_latent.core.distance`    -- naive vs wrap-aware metrics.
    * :mod:`~calabi_yau_latent.core.sampling`    -- seeded Gaussian draws.
    * :mod:`~calabi_yau_latent.core.data`        -- planted seam-straddling clusters.
    * :mod:`~calabi_yau_latent.core.clustering`  -- connected-components clustering.
    * :mod:`~calabi_yau_latent.core.holonomy`    -- toy parallel-transport cartoon.
"""

from __future__ import annotations

from calabi_yau_latent.core.clustering import (
    cluster,
    nearest_neighbor,
    num_clusters,
    purity,
)
from calabi_yau_latent.core.config import DEFAULT, CYConfig
from calabi_yau_latent.core.data import generate, make_space
from calabi_yau_latent.core.distance import (
    circle_delta,
    naive_angular_distance,
    naive_distance,
    toroidal_angular_distance,
    toroidal_distance,
)
from calabi_yau_latent.core.holonomy import (
    holonomy_angle,
    loop_trace,
    transport_around_loop,
)
from calabi_yau_latent.core.latent import (
    TWO_PI,
    CompactifiedLatentSpace,
    LatentPoint,
)
from calabi_yau_latent.core.sampling import gauss, make_stream

__all__ = [
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
