"""Self-contained tests (stdlib unittest) for the p-adic prototype.

Run:  python3 -m unittest -v test_padic
"""

from __future__ import annotations

import math
import unittest
from fractions import Fraction

import embedding
import padic


class TestValuation(unittest.TestCase):
    def test_valuation_of_powers(self):
        self.assertEqual(padic.valuation(8, 2), 3)      # 8 = 2^3
        self.assertEqual(padic.valuation(12, 2), 2)     # 12 = 2^2 * 3
        self.assertEqual(padic.valuation(12, 3), 1)     # 12 = 3 * 4
        self.assertEqual(padic.valuation(49, 7), 2)     # 49 = 7^2
        self.assertEqual(padic.valuation(5, 2), 0)      # odd

    def test_valuation_of_zero_is_infinite(self):
        self.assertEqual(padic.valuation(0, 2), math.inf)

    def test_valuation_of_rationals(self):
        # v_2(3/4) = v_2(3) - v_2(4) = 0 - 2 = -2
        self.assertEqual(padic.valuation(Fraction(3, 4), 2), -2)

    def test_non_prime_rejected(self):
        with self.assertRaises(ValueError):
            padic.valuation(10, 4)


class TestAbsAndDistance(unittest.TestCase):
    def test_abs_values(self):
        self.assertAlmostEqual(padic.p_adic_abs(8, 2), 2 ** -3)
        self.assertEqual(padic.p_adic_abs(0, 2), 0.0)
        self.assertAlmostEqual(padic.p_adic_abs(3, 2), 1.0)  # unit

    def test_distance_symmetry_and_identity(self):
        self.assertEqual(padic.distance(5, 5, 2), 0.0)
        self.assertEqual(padic.distance(5, 13, 2), padic.distance(13, 5, 2))

    def test_distance_values(self):
        # |5 - 13|_2 = |-8|_2 = 2^-3
        self.assertAlmostEqual(padic.distance(5, 13, 2), 2 ** -3)


class TestUltrametric(unittest.TestCase):
    def test_strong_triangle_holds_on_sample(self):
        coords = [1, 3, 5, 8, 16, 17, 24, 32, 48, 64]
        ok, checked, failures = embedding.verify_ultrametric(coords, 2)
        self.assertTrue(ok)
        self.assertGreater(checked, 0)
        self.assertEqual(failures, [])

    def test_strong_triangle_holds_for_prime_7(self):
        coords = [7, 14, 49, 50, 98, 100, 343]
        ok, _, failures = embedding.verify_ultrametric(coords, 7)
        self.assertTrue(ok)
        self.assertEqual(failures, [])


class TestEmbeddingAndClusters(unittest.TestCase):
    def test_string_embedding_is_deterministic(self):
        self.assertEqual(embedding.embed_item("cat"), embedding.embed_item("cat"))

    def test_clusters_are_refined_by_level(self):
        coords = [0, 4, 8, 16, 2, 6]
        c1 = embedding.cluster_by_valuation(coords, 2, level=1)
        # all even -> single residue class mod 2
        self.assertEqual(sorted(c1.keys()), [0])
        c2 = embedding.cluster_by_valuation(coords, 2, level=2)
        # split by residue mod 4
        self.assertEqual(sorted(c2.keys()), [0, 2])

    def test_nearest_neighbor_prefers_shared_factors(self):
        # 16 shares more factors of 2 with 48 (both div by 16) than with 17.
        nn = embedding.nearest_neighbors(16, [17, 48, 5, 3], 2, k=1)
        self.assertEqual(nn[0][0], 48)


if __name__ == "__main__":
    unittest.main()
