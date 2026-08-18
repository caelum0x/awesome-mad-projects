"""Tests for the command-line adapter (padic_embeddings.adapters.cli).

The report must contain every section on a small run, accept integers and strings,
support a nearest-neighbour query, and reject a non-prime ``p`` / bad parse. All runs
here are stdlib-only (no ``--png``), so they RUN on both interpreters.
"""

from __future__ import annotations

import pytest

from padic_embeddings.adapters import cli

_SECTIONS = (
    "p-adic Embedding Space",
    "valuation / absolute value",
    "distance matrix",
    "distance heatmap",
    "ultrametric verification",
    "clusters",
)


def test_default_run_contains_every_section() -> None:
    out = cli.run_cli(["--p", "2"])
    for marker in _SECTIONS:
        assert marker in out
    assert "HOLDS (this is a true ultrametric)" in out
    assert "nearest neighbors" in out  # default query = 16


def test_custom_integers_and_prime() -> None:
    out = cli.run_cli(["--p", "7", "--ints", "7", "14", "49", "98", "--query", "49"])
    assert "prime p = 7" in out
    assert "nearest neighbors of '49'" in out
    assert "violations found: 0" in out


def test_string_items_are_hashed() -> None:
    out = cli.run_cli(["--p", "2", "--strings", "cat", "cot", "dog", "--query", "cat"])
    assert "strings (SHA-256 hashed into Z)" in out
    assert "nearest neighbors of 'cat'" in out


def test_non_prime_p_exits() -> None:
    with pytest.raises(SystemExit):
        cli.run_cli(["--p", "4"])


def test_missing_value_errors() -> None:
    with pytest.raises(SystemExit):
        cli.run_cli(["--p"])


def test_main_prints_and_returns_zero(capsys) -> None:
    rc = cli.main(["--p", "2", "--ints", "8", "16", "32"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "p-adic Embedding Space" in captured.out
