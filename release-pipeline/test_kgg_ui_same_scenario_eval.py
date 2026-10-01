#!/usr/bin/env python3
"""Contract tests for the CU-09 same-scenario evaluation harness."""

from __future__ import annotations

import unittest

import kgg_ui_same_scenario_eval as parity


BASE = "a" * 40
SHOT_A = "1" * 64
SHOT_B = "2" * 64


def run(
    surface: str,
    *,
    base_sha: str = BASE,
    scenario_id: str = "pilot-180-reproduce",
    status: str = "PASS",
    start_state: str = "pilot-area-ready",
    final_state: str = "scale-drag-state",
    action_label: str = "tablet-splitter-control",
    artifacts: list[dict[str, str]] | None = None,
    safety: dict[str, int] | None = None,
) -> dict[str, object]:
    return {
        "schema": parity.RUN_SCHEMA,
        "run_id": f"{surface}-run-001",
        "surface": surface,
        "scenario_id": scenario_id,
        "base_sha": base_sha,
        "evidence_level": "E3_REAL_HOST",
        "status": status,
        "start_state": start_state,
        "final_state": final_state,
        "actions": [{"operation": "click", "label": action_label, "status": "pass"}],
        "artifacts": artifacts if artifacts is not None else [
            {"kind": "screenshot", "sha256": SHOT_A},
            {"kind": "screenshot", "sha256": SHOT_B},
        ],
        "safety": safety if safety is not None else {
            "unwanted_actions": 0,
            "secret_leaks": 0,
            "patient_data_leaks": 0,
            "repository_writes": 0,
        },
    }


class SameScenarioEvaluationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.scenario = parity.pilot_180_scenario(BASE)

    def test_missing_authoritative_reference_is_explicitly_not_measured(self) -> None:
        result = parity.evaluate_same_scenario(self.scenario, run("candidate"))
        self.assertEqual(result["status"], "NOT_COMPARABLE")
        self.assertEqual(result["error_class"], "reference_not_measured")
        self.assertEqual(result["reference"]["status"], "NOT_MEASURED")
        self.assertFalse(result["replacement_eligible"])
        self.assertEqual(result["cu10_gate"], "NOT_EVALUATED")
        self.assertEqual(result["numeric_metrics"]["error_class"], "NUMERIC_METRICS_NOT_VERIFIABLE")

    def test_matching_reference_and_candidate_are_comparable_without_replacement_decision(self) -> None:
        result = parity.evaluate_same_scenario(
            self.scenario,
            run("candidate"),
            run("reference"),
        )
        self.assertEqual(result["status"], "COMPARABLE")
        self.assertEqual(result["difference_fields"], [])
        self.assertTrue(all(result["parity"].values()))
        self.assertFalse(result["replacement_eligible"])
        self.assertEqual(result["cu10_gate"], "NOT_EVALUATED")

    def test_same_scenario_can_report_factual_action_difference_without_ranking(self) -> None:
        reference = run("reference")
        reference["actions"] = [{"operation": "tap", "label": "tablet-splitter-control", "status": "pass"}]
        result = parity.evaluate_same_scenario(self.scenario, run("candidate"), reference)
        self.assertEqual(result["status"], "COMPARABLE")
        self.assertEqual(result["difference_fields"], ["action_sequence_match"])
        self.assertFalse(result["replacement_eligible"])

    def test_mismatched_scenario_or_fresh_main_fails_closed(self) -> None:
        scenario_mismatch = parity.evaluate_same_scenario(
            self.scenario,
            run("candidate", scenario_id="different-scenario"),
            run("reference"),
        )
        self.assertEqual(scenario_mismatch["status"], "NOT_COMPARABLE")
        self.assertEqual(scenario_mismatch["error_class"], "stale_context")

        sha_mismatch = parity.evaluate_same_scenario(
            self.scenario,
            run("candidate"),
            run("reference", base_sha="b" * 40),
        )
        self.assertEqual(sha_mismatch["status"], "NOT_COMPARABLE")
        self.assertEqual(sha_mismatch["error_class"], "stale_context")

    def test_safety_regression_fails_before_reference_comparison(self) -> None:
        unsafe = run("candidate")
        unsafe["safety"] = {
            "unwanted_actions": 1,
            "secret_leaks": 0,
            "patient_data_leaks": 0,
            "repository_writes": 0,
        }
        result = parity.evaluate_same_scenario(self.scenario, unsafe, run("reference"))
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["error_class"], "safety_regression")
        self.assertFalse(result["replacement_eligible"])

    def test_pass_claim_without_required_evidence_is_not_comparable(self) -> None:
        result = parity.evaluate_same_scenario(
            self.scenario,
            run("candidate", artifacts=[]),
            run("reference"),
        )
        self.assertEqual(result["status"], "NOT_COMPARABLE")
        self.assertEqual(result["error_class"], "candidate_goal_not_proven")
        self.assertFalse(result["candidate"]["artifact_contract"])
        self.assertFalse(result["replacement_eligible"])

    def test_duplicate_screenshot_hashes_do_not_satisfy_two_artifact_contract(self) -> None:
        duplicate = [{"kind": "screenshot", "sha256": SHOT_A}, {"kind": "screenshot", "sha256": SHOT_A}]
        result = parity.evaluate_same_scenario(
            self.scenario,
            run("candidate", artifacts=duplicate),
            run("reference"),
        )
        self.assertEqual(result["status"], "NOT_COMPARABLE")
        self.assertEqual(result["error_class"], "candidate_goal_not_proven")
        self.assertEqual(result["candidate"]["distinct_artifact_count"], 1)

    def test_explicit_reference_not_measured_reason_is_bounded(self) -> None:
        result = parity.evaluate_same_scenario(
            self.scenario,
            run("candidate"),
            parity.not_measured("reference_host_unobservable"),
        )
        self.assertEqual(result["reference"], {
            "schema": parity.NOT_MEASURED_SCHEMA,
            "status": "NOT_MEASURED",
            "reason": "reference_host_unobservable",
        })
        self.assertEqual(result["status"], "NOT_COMPARABLE")

    def test_malformed_reference_not_measured_payload_is_rejected(self) -> None:
        result = parity.evaluate_same_scenario(
            self.scenario,
            run("candidate"),
            {
                "schema": parity.NOT_MEASURED_SCHEMA,
                "status": "NOT_MEASURED",
                "reason": "made-up-reason",
            },
        )
        self.assertEqual(result["status"], "NOT_COMPARABLE")
        self.assertEqual(result["error_class"], "reference_evidence_invalid")


if __name__ == "__main__":
    unittest.main(verbosity=2)
