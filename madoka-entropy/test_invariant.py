"""Stdlib unittest checks for the entropy model and the 2nd-law invariant.

Run:  python3 -m unittest -v test_invariant
"""

import unittest

from entropy import EntropyLedger, wish_deltas
from incubator import Incubator
from magical_girl import MagicalGirl, make_girls
from simulation import SimConfig, run_simulation


class WishDeltaTests(unittest.TestCase):
    def test_wish_net_total_change_is_positive(self):
        d_global, d_local = wish_deltas(local_order=1.0, karmic_multiplier=1.8)
        self.assertEqual(d_local, -1.0)
        self.assertAlmostEqual(d_global, 1.8)
        self.assertGreater(d_global + d_local, 0.0)  # net entropy rises

    def test_multiplier_must_exceed_one(self):
        with self.assertRaises(ValueError):
            wish_deltas(1.0, 1.0)

    def test_order_must_be_positive(self):
        with self.assertRaises(ValueError):
            wish_deltas(0.0, 1.8)


class LedgerTests(unittest.TestCase):
    def test_ledger_is_immutable_copy_on_change(self):
        a = EntropyLedger(100.0, 50.0, 0.0)
        b = a.with_changes(d_global=5.0)
        self.assertEqual(a.global_entropy, 100.0)   # original untouched
        self.assertEqual(b.global_entropy, 105.0)
        self.assertEqual(a.total_entropy, 150.0)


class MagicalGirlTests(unittest.TestCase):
    def test_cast_decays_purity_and_imposes_order(self):
        g = MagicalGirl("Sayaka", purity=1.0, local_entropy=20.0)
        g2 = g.cast(local_order=2.0, decay_per_order=0.1)
        self.assertAlmostEqual(g2.purity, 0.8)
        self.assertAlmostEqual(g2.local_entropy, 18.0)
        self.assertEqual(g.purity, 1.0)  # original untouched (immutable)

    def test_purity_clamped_at_zero(self):
        g = MagicalGirl("Kyoko", purity=0.05, local_entropy=5.0)
        g2 = g.cast(local_order=10.0, decay_per_order=1.0)
        self.assertEqual(g2.purity, 0.0)


class IncubatorTests(unittest.TestCase):
    def test_harvest_only_from_positive_surplus(self):
        inc = Incubator(harvest_fraction=0.5)
        self.assertAlmostEqual(inc.harvest_from_wish(1.8, -1.0), 0.4)
        self.assertEqual(inc.harvest_from_wish(0.0, 0.0), 0.0)


class InvariantTests(unittest.TestCase):
    def test_invariant_holds_default(self):
        r = run_simulation(SimConfig(seed=42, steps=120))
        self.assertTrue(r.invariant_holds)
        self.assertGreaterEqual(r.min_d_total, -1e-9)

    def test_invariant_holds_many_seeds(self):
        for s in range(50):
            r = run_simulation(SimConfig(seed=s, steps=150))
            self.assertTrue(r.invariant_holds, f"seed {s} violated invariant")

    def test_global_entropy_is_non_decreasing(self):
        # Global reservoir only ever receives entropy, so it too is monotone.
        r = run_simulation(SimConfig(seed=1, steps=120))
        g = [rec.global_entropy for rec in r.records]
        for prev, cur in zip(g, g[1:]):
            self.assertGreaterEqual(cur, prev - 1e-9)


if __name__ == "__main__":
    unittest.main()
