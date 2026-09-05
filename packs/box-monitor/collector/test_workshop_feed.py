#!/usr/bin/env python3
"""Unit tests for collector derived fields. No GPU."""
from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

_SRC = Path(__file__).resolve().parent / "workshop-feed.py"
_SPEC = importlib.util.spec_from_file_location("workshop_feed", _SRC)
assert _SPEC and _SPEC.loader
_MOD = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MOD)
derived = _MOD.derived
last8_rate = _MOD.last8_rate


class DerivedTests(unittest.TestCase):
    def test_before_floor(self) -> None:
        live = {
            "step": 80000,
            "tokensSeen": 1_966_080_000.0,
            "tokPerParam": 3.93,
            "last8TokS": 13653.333333333334,
        }
        dur = {
            "step": 80000.0,
            "tokensSeen": 1_966_080_000.0,
            "tokPerParam": 3.93,
            "targetTokens": 2_499_734_080.0,
            "targetTokPerParam": 5.0,
            "tokensPerStep": 24576.0,
            "maxSteps": 314301.0,
            "paramCount": 499946816.0,
        }
        d = derived(live, dur)
        self.assertFalse(d["floorMet"])
        self.assertLess(d["pct"], 100.0)
        self.assertGreater(d["hoursToFloor"], 0.0)
        self.assertEqual(d["hoursEta"], d["hoursToFloor"])
        self.assertGreater(d["remainTokens"], 0.0)

    def test_past_floor_does_not_clamp_eta_to_zero(self) -> None:
        live = {
            "step": 143720,
            "tokensSeen": 3_532_062_720.0,
            "tokPerParam": 7.065,
            "last8TokS": 13653.333333333334,
        }
        dur = {
            "step": 140000.0,
            "tokensSeen": 3_440_640_000.0,
            "tokPerParam": 6.882,
            "targetTokens": 2_499_734_080.0,
            "targetTokPerParam": 5.0,
            "tokensPerStep": 24576.0,
            "maxSteps": 314301.0,
            "paramCount": 499946816.0,
        }
        d = derived(live, dur)
        self.assertTrue(d["floorMet"])
        self.assertEqual(d["hoursToFloor"], 0.0)
        self.assertGreater(d["pctOfFloor"], 100.0)
        self.assertEqual(d["pct"], 100.0)
        self.assertGreater(d["hoursToMax"], 80.0)
        self.assertLess(d["hoursToMax"], 90.0)
        self.assertEqual(d["hoursEta"], d["hoursToMax"])
        self.assertEqual(d["remainTokens"], 0.0)
        self.assertEqual(d["remainStepsToMax"], 314301.0 - 143720)
        self.assertAlmostEqual(d["pctOfYaml"], 100.0 * 143720 / 314301.0, places=4)

    def test_last8_needs_two_rows(self) -> None:
        self.assertIsNone(last8_rate([{"tokens": 1, "elapsed": 10}]))
        rows = [
            {"tokens": 2_457_600.0, "elapsed": 61.0},
            {"tokens": 22_118_400.0, "elapsed": 247.0},
        ]
        rate = last8_rate(rows)
        self.assertIsNotNone(rate)
        self.assertAlmostEqual(rate, (22_118_400.0 - 2_457_600.0) / (247.0 - 61.0), places=6)


if __name__ == "__main__":
    unittest.main()
