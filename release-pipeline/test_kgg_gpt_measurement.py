#!/usr/bin/env python3
"""Contract tests for the KGG measurement-envelope boundary."""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
PIPELINE = ROOT / "release-pipeline"
if str(PIPELINE) not in sys.path:
    sys.path.insert(0, str(PIPELINE))

import kgg_gpt_ab_compare as comparator
import kgg_gpt_measurement as measurement


class KggMeasurementTests(unittest.TestCase):
    def test_self_test_and_complete_payload_are_valid(self) -> None:
        measurement.self_test()
        envelope = measurement.validate_envelope(measurement._valid_complete_fixture())
        payload = measurement.comparator_input(envelope)
        self.assertEqual(set(payload), set(comparator.REQUIRED))
        self.assertEqual(payload["base_sha"], "a" * 40)

    def test_failure_envelope_is_bounded_and_comparator_safe(self) -> None:
        envelope = measurement.build_failure_envelope(
            request_id="measurement-failure-001",
            surface="production",
            scenario_id="tablet-splitter-scale-drag-synth",
            base_sha="UNKNOWN",
        )
        self.assertEqual(envelope["status"], "FAIL")
        self.assertIsNone(envelope["payload"])
        self.assertEqual(
            measurement.comparator_input(envelope),
            {"status": "FAIL", "error_class": "NUMERIC_METRICS_NOT_VERIFIABLE"},
        )

    def test_missing_environment_writes_failure_without_fabricating_zeroes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "measurement-envelope.json"
            old = {key: os.environ.get(key) for key in (
                "KGG_MEASUREMENT_REQUEST_ID",
                "KGG_MEASUREMENT_SURFACE",
                "KGG_MEASUREMENT_SCENARIO_ID",
                "KGG_MEASUREMENT_BASE_SHA",
                "KGG_MEASUREMENT_ENVELOPE_JSON",
            )}
            try:
                os.environ["KGG_MEASUREMENT_REQUEST_ID"] = "measurement-env-001"
                os.environ["KGG_MEASUREMENT_SURFACE"] = "production"
                os.environ["KGG_MEASUREMENT_SCENARIO_ID"] = "tablet-splitter-scale-drag-synth"
                os.environ["KGG_MEASUREMENT_BASE_SHA"] = "a" * 40
                os.environ.pop("KGG_MEASUREMENT_ENVELOPE_JSON", None)
                result = measurement.write_from_environment(output)
            finally:
                for key, value in old.items():
                    if value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = value
        self.assertEqual(result["status"], "FAIL")
        self.assertIn("reads", result["missing_fields"])
        self.assertIsNone(result["payload"])

    def test_trusted_complete_environment_is_identity_bound(self) -> None:
        envelope = measurement._valid_complete_fixture()
        old = {key: os.environ.get(key) for key in (
            "KGG_MEASUREMENT_REQUEST_ID",
            "KGG_MEASUREMENT_SURFACE",
            "KGG_MEASUREMENT_SCENARIO_ID",
            "KGG_MEASUREMENT_BASE_SHA",
            "KGG_MEASUREMENT_ENVELOPE_JSON",
        )}
        try:
            os.environ["KGG_MEASUREMENT_REQUEST_ID"] = envelope["request_id"]
            os.environ["KGG_MEASUREMENT_SURFACE"] = envelope["surface"]
            os.environ["KGG_MEASUREMENT_SCENARIO_ID"] = envelope["scenario_id"]
            os.environ["KGG_MEASUREMENT_BASE_SHA"] = envelope["base_sha"]
            os.environ["KGG_MEASUREMENT_ENVELOPE_JSON"] = json.dumps(envelope)
            with tempfile.TemporaryDirectory() as directory:
                result = measurement.write_from_environment(Path(directory) / "measurement.json")
        finally:
            for key, value in old.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["surface"], "candidate")

    def test_model_self_estimate_is_rejected_even_with_recomputed_hash(self) -> None:
        envelope = measurement._valid_complete_fixture()
        envelope["field_provenance"]["reads"]["source"] = "model_output"
        envelope["provenance_sha256"] = measurement._hash(envelope)
        with self.assertRaisesRegex(measurement.MeasurementError, "field_provenance_source_invalid"):
            measurement.validate_envelope(envelope)

    def test_tampering_and_extra_fields_are_rejected(self) -> None:
        envelope = measurement._valid_complete_fixture()
        tampered = copy.deepcopy(envelope)
        tampered["payload"]["reads"] = 999
        with self.assertRaisesRegex(measurement.MeasurementError, "provenance_hash_mismatch"):
            measurement.validate_envelope(tampered)
        extra = copy.deepcopy(envelope)
        extra["unexpected"] = True
        with self.assertRaisesRegex(measurement.MeasurementError, "envelope_fields_invalid"):
            measurement.validate_envelope(extra)

    def test_outer_and_payload_status_must_match(self) -> None:
        envelope = measurement._valid_complete_fixture()
        envelope["payload"] = dict(envelope["payload"], status="FAIL")
        envelope["provenance_sha256"] = measurement._hash(envelope)
        with self.assertRaisesRegex(measurement.MeasurementError, "status_mismatch"):
            measurement.validate_envelope(envelope)

    def test_evidence_content_is_present_hashed_and_bound_to_field(self) -> None:
        envelope = measurement._valid_complete_fixture()
        self.assertIn("content", envelope["evidence_refs"][0])
        tampered = copy.deepcopy(envelope)
        tampered["evidence_refs"][0]["content"]["reads"] = 999
        tampered["provenance_sha256"] = measurement._hash(tampered)
        with self.assertRaisesRegex(measurement.MeasurementError, "evidence_ref_sha256_mismatch"):
            measurement.validate_envelope(tampered)

    def test_field_provenance_requires_semantically_matching_evidence_kind(self) -> None:
        envelope = measurement._valid_complete_fixture()
        envelope["field_provenance"]["reads"]["evidence_ids"] = ["measurement-runtime-002"]
        envelope["evidence_refs"].append({
            "id": "measurement-runtime-002",
            "kind": "runtime",
            "content": {"runtime_ms": 10, "captured_at": envelope["captured_at"]},
            "sha256": measurement._evidence_content_hash({"runtime_ms": 10, "captured_at": envelope["captured_at"]}),
        })
        envelope["provenance_sha256"] = measurement._hash(envelope)
        with self.assertRaisesRegex(measurement.MeasurementError, "field_provenance_evidence_semantics"):
            measurement.validate_envelope(envelope)


if __name__ == "__main__":
    unittest.main(verbosity=2)
