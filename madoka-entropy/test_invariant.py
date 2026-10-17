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

    def test_local_entropy_clamped_at_zero(self):
        # Requesting more order than the subsystem still holds must not drive
        # local_entropy negative -- it should floor at 0, exactly like purity
        # above. Only the entropy that actually existed can be exported, so
        # purity should decay by the APPLIED amount (5.0), not the requested
        # one (10.0).
        g = MagicalGirl("Kyoko", purity=1.0, local_entropy=5.0)
        g2 = g.cast(local_order=10.0, decay_per_order=0.1)
        self.assertEqual(g2.local_entropy, 0.0)
        self.assertAlmostEqual(g2.purity, 0.5)  # 1.0 - 0.1 * 5.0 applied units

    def test_local_entropy_never_negative_when_already_exhausted(self):
        g = MagicalGirl("Kyoko", purity=1.0, local_entropy=0.0)
        g2 = g.cast(local_order=3.0, decay_per_order=0.2)
        self.assertEqual(g2.local_entropy, 0.0)
        self.assertEqual(g2.purity, 1.0)  # nothing left to export -> no decay


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

    def test_local_entropy_never_goes_negative(self):
        # Regression: with a small decay_per_order and a small starting
        # budget, girls take many casts before crossing the witch threshold,
        # which used to drive MagicalGirl.local_entropy deeply negative
        # (observed as low as ~-80) because `cast()` had no floor -- unlike
        # `purity`, which was always clamped at 0. "Entropy" in this model is
        # documented as a subsystem's honest physical quantity and must never
        # go negative, at every step and in the final roster.
        for seed in range(10):
            cfg = SimConfig(
                seed=seed,
                steps=300,
                decay_per_order=0.01,
                base_local_entropy=5.0,
                witch_threshold=0.15,
                wish_probability=0.9,
            )
            r = run_simulation(cfg)
            for rec in r.records:
                self.assertGreaterEqual(rec.local_entropy, -1e-9, f"seed {seed}")
            for girl in r.final_girls:
                self.assertGreaterEqual(girl.local_entropy, 0.0, f"seed {seed}")
            self.assertTrue(r.invariant_holds, f"seed {seed}")

    def test_ledger_local_entropy_matches_sum_of_girls_before_witching(self):
        # The ledger tracks local_entropy via deltas independently of the
        # per-girl fields; they must stay exactly in sync at every step (the
        # capped wish delta applied to the ledger must equal the amount
        # actually applied to the girl).
        cfg = SimConfig(
            steps=50,
            decay_per_order=0.01,
            base_local_entropy=5.0,
            wish_probability=0.9,
            seed=3,
        )
        r = run_simulation(cfg)
        living_sum = sum(g.local_entropy for g in r.final_girls if not g.is_witch)
        # Witches evacuate their exact local_entropy into the global
        # reservoir, so the ledger's running local_entropy should equal the
        # sum over still-living girls only.
        self.assertAlmostEqual(r.records[-1].local_entropy, living_sum, places=6)


if __name__ == "__main__":
    unittest.main()
