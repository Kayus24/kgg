#!/usr/bin/env python3
"""Tests for the local complete-metric surface pilot."""

from __future__ import annotations

import unittest
from unittest.mock import patch

import kgg_gpt_ab_compare as comparator
import kgg_gpt_measurement as measurement
import kgg_ui_lab_surface_metrics as metrics


class KggUiLabSurfaceMetricsTests(unittest.TestCase):
    def test_candidate_emits_complete_pass_payload(self) -> None:
        with patch.object(metrics.candidate_gate, "validate_candidate", return_value={"status": "PASS"}):
            result = metrics.build_candidate_metrics(base_sha="a" * 40)
        self.assertEqual(set(result), set(comparator.REQUIRED))
        self.assertEqual(result["scenario_id"], metrics.SCENARIO_ID)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["reads"], 4)
        self.assertEqual(result["action_calls"], 7)
        self.assertGreaterEqual(result["runtime_ms"], 0)
        self.assertEqual(result["result_quality"], 100)
        self.assertEqual(result["root_cause_quality"], 0)
        for field in comparator.NON_NEGATIVE:
            self.assertIsInstance(result[field], int)
            self.assertGreaterEqual(result[field], 0)

    def test_candidate_payload_is_comparable_when_replayed_as_same_local_surface(self) -> None:
        with patch.object(metrics.candidate_gate, "validate_candidate", return_value={"status": "PASS"}):
            first = metrics.build_candidate_metrics(base_sha="a" * 40)
            second = metrics.build_candidate_metrics(base_sha="a" * 40)
        result = comparator.compare_surfaces(
            {"production": first, "candidate": second, "codex_plugin": second}
        )
        self.assertEqual(result["status"], "COMPARABLE")
        self.assertIsInstance(result["replacement_eligible"], bool)

    def test_complete_envelope_contains_provenance_for_every_field(self) -> None:
        with patch.object(metrics.candidate_gate, "validate_candidate", return_value={"status": "PASS"}):
            envelope = metrics.build_candidate_measurement_envelope(base_sha="a" * 40)
        normalized = measurement.validate_envelope(envelope)
        self.assertEqual(normalized["status"], "PASS")
        self.assertEqual(set(normalized["field_provenance"]), set(measurement.PAYLOAD_FIELDS))
        self.assertEqual(normalized["field_provenance"]["result_quality"]["observed_by"], "independent_evaluator")
        self.assertEqual(normalized["field_provenance"]["reads"]["observed_by"], "host")
        self.assertEqual(measurement.comparator_input(normalized), normalized["payload"])

    def test_real_candidate_gate_emits_provenance_ready_envelope(self) -> None:
        envelope = metrics.build_candidate_measurement_envelope(base_sha="3fcdad7696f8f9c9800f7acf629a15f7152f97df")
        self.assertEqual(envelope["status"], "PASS")
        self.assertEqual(measurement.comparator_input(envelope), envelope["payload"])
        self.assertEqual(envelope["payload"]["base_sha"], "3fcdad7696f8f9c9800f7acf629a15f7152f97df")

    def test_invalid_base_sha_fails_closed(self) -> None:
        with self.assertRaisesRegex(metrics.SurfaceMetricsError, "base_sha"):
            metrics.build_candidate_metrics(base_sha="not-a-sha")


if __name__ == "__main__":
    unittest.main()
