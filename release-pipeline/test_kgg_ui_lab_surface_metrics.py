#!/usr/bin/env python3
"""Tests for the local complete-metric surface pilot."""

from __future__ import annotations

import unittest

import kgg_gpt_ab_compare as comparator
import kgg_ui_lab_surface_metrics as metrics


class KggUiLabSurfaceMetricsTests(unittest.TestCase):
    def test_candidate_emits_complete_pass_payload(self) -> None:
        result = metrics.build_candidate_metrics(base_sha="a" * 40)
        self.assertEqual(set(result), set(comparator.REQUIRED))
        self.assertEqual(result["scenario_id"], metrics.SCENARIO_ID)
        self.assertEqual(result["status"], "PASS")
        self.assertGreaterEqual(result["runtime_ms"], 0)
        self.assertEqual(result["result_quality"], 100)
        self.assertEqual(result["root_cause_quality"], 0)
        for field in comparator.NON_NEGATIVE:
            self.assertIsInstance(result[field], int)
            self.assertGreaterEqual(result[field], 0)

    def test_candidate_payload_is_comparable_when_replayed_as_same_local_surface(self) -> None:
        first = metrics.build_candidate_metrics(base_sha="a" * 40)
        second = metrics.build_candidate_metrics(base_sha="a" * 40)
        result = comparator.compare_surfaces(
            {"production": first, "candidate": second, "codex_plugin": second}
        )
        self.assertEqual(result["status"], "COMPARABLE")
        self.assertIsInstance(result["replacement_eligible"], bool)

    def test_invalid_base_sha_fails_closed(self) -> None:
        with self.assertRaisesRegex(metrics.SurfaceMetricsError, "base_sha"):
            metrics.build_candidate_metrics(base_sha="not-a-sha")


if __name__ == "__main__":
    unittest.main()
