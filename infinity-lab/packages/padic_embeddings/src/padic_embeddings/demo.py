"""Runnable demo: the p-adic embedding space end to end.

Reproduces the canonical showcase -- embed a list of integers chosen to reveal the
2-adic tree structure, print their valuations and pairwise distance matrix, verify
the ultrametric law exhaustively, and show the induced residue-class clusters and
nearest neighbours -- sharing exactly one source of truth with the CLI and the tests
(:mod:`padic_embeddings.adapters.cli`).

Run:  python -m padic_embeddings.demo
"""

from __future__ import annotations

from padic_embeddings.adapters import cli

_HEADLINE = "THE p-ADIC EMBEDDING SPACE -- closeness is divisibility by a prime"
_SUBTITLE = (
    "Items map to integer coordinates in Z; two are close when their difference is "
    "highly divisible by p. The geometry is an ultrametric tree, not a Euclidean cloud."
)


def render_demo() -> str:
    """Return the full demo text: headline, subtitle, and the canonical report."""
    report = cli.run_cli(["--p", "2"])
    return "\n".join([_HEADLINE, _SUBTITLE, "", report])


def main() -> int:
    """Print the demo. Returns process exit code 0."""
    print(render_demo())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
