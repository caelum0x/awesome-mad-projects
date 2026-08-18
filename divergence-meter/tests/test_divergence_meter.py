"""Tests for the Divergence Meter.

Runnable with either the stdlib runner:

    python -m unittest discover -s tests

or pytest if installed:

    pytest tests
"""

from __future__ import annotations

import io
import os
import sys
import unittest

# Make the package importable when tests are run from the project root.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from divergence_meter.attractor import classify  # noqa: E402
from divergence_meter.divergence import (  # noqa: E402
    STEINS_GATE_VALUE,
    compute_divergence,
)
from divergence_meter.nixie import render  # noqa: E402
from divergence_meter.steiner import (  # noqa: E402
    SteinerError,
    divergence_delta,
    get_line,
    save_line,
)
from divergence_meter.worldstate import (  # noqa: E402
    WorldStateError,
    snapshot_from_numbers,
    snapshot_from_source,
)


class DivergenceTests(unittest.TestCase):
    def test_deterministic(self):
        snap = snapshot_from_source("Kurisu")
        a = compute_divergence(snap)
        b = compute_divergence(snapshot_from_source("Kurisu"))
        self.assertEqual(a.value, b.value)
        self.assertEqual(a.digest, b.digest)

    def test_range(self):
        for source in ("a", "b", "c", "hello world", "12345"):
            reading = compute_divergence(snapshot_from_source(source))
            self.assertGreaterEqual(reading.value, 0.0)
            self.assertLess(reading.value, 2.0)

    def test_display_format(self):
        reading = compute_divergence(snapshot_from_source("test"))
        # 1 integer digit + '.' + 6 fractional digits.
        self.assertRegex(reading.display, r"^\d\.\d{6}$")
        self.assertEqual(reading.digits, reading.display.replace(".", ""))

    def test_input_change_changes_value(self):
        a = compute_divergence(snapshot_from_source("worldline-A"))
        b = compute_divergence(snapshot_from_source("worldline-B"))
        self.assertNotEqual(a.value, b.value)

    def test_json_is_normalised(self):
        a = compute_divergence(snapshot_from_source('{"a":1,"b":2}'))
        b = compute_divergence(snapshot_from_source('{"b":2,"a":1}'))
        self.assertEqual(a.value, b.value)  # key order must not matter


class WorldStateTests(unittest.TestCase):
    def test_empty_source_rejected(self):
        with self.assertRaises(WorldStateError):
            snapshot_from_source("   ")

    def test_numbers_snapshot(self):
        snap = snapshot_from_numbers([1, 2, 3])
        self.assertIn("numbers", snap.origin)
        with self.assertRaises(WorldStateError):
            snapshot_from_numbers([])

    def test_stdin(self):
        stream = io.BytesIO(b"time travel")
        snap = snapshot_from_source("-", stdin=stream)
        self.assertEqual(snap.origin, "stdin")


class AttractorTests(unittest.TestCase):
    def test_alpha_vs_beta(self):
        self.assertEqual(classify(0.337187).cluster, "Alpha")
        self.assertEqual(classify(1.048596).cluster, "Beta")

    def test_boundary_distance(self):
        result = classify(1.048596)
        self.assertEqual(result.nearest_boundary, 1.0)
        self.assertAlmostEqual(result.distance_to_boundary, 0.048596, places=6)

    def test_steins_gate_flag(self):
        self.assertTrue(classify(STEINS_GATE_VALUE).on_steins_gate)
        self.assertFalse(classify(1.5).on_steins_gate)

    def test_rejects_non_finite(self):
        with self.assertRaises(ValueError):
            classify(float("inf"))


class NixieTests(unittest.TestCase):
    def test_render_shape(self):
        art = render("1.048596")
        lines = art.splitlines()
        # A framed block: top border + 5 body rows + bottom border = 7 lines.
        self.assertEqual(len(lines), 7)
        self.assertTrue(all(len(line) == len(lines[0]) for line in lines))

    def test_render_empty_rejected(self):
        with self.assertRaises(ValueError):
            render("")


class SteinerTests(unittest.TestCase):
    def setUp(self):
        self.store = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "_test_store.json"
        )
        if os.path.exists(self.store):
            os.remove(self.store)

    def tearDown(self):
        if os.path.exists(self.store):
            os.remove(self.store)

    def test_save_and_recall(self):
        reading = compute_divergence(snapshot_from_source("alpha-line"))
        save_line("alpha", reading, store_path=self.store)
        recalled = get_line("alpha", store_path=self.store)
        self.assertEqual(recalled.value, reading.value)
        self.assertEqual(recalled.display, reading.display)

    def test_missing_line_raises(self):
        with self.assertRaises(SteinerError):
            get_line("does-not-exist", store_path=self.store)

    def test_delta(self):
        a = compute_divergence(snapshot_from_source("line-A"))
        b = compute_divergence(snapshot_from_source("line-B"))
        delta = divergence_delta(a.value, b.value)
        self.assertAlmostEqual(delta, round(b.value - a.value, 6), places=6)


if __name__ == "__main__":
    unittest.main(verbosity=2)
