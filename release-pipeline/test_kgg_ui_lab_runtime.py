#!/usr/bin/env python3
"""Red/green tests for bounded UI Lab retries and Bruder-GPT escalation."""

from __future__ import annotations

import json
import hashlib
from pathlib import Path
import unittest

import kgg_ui_lab_runtime as runtime


class KggUiLabRuntimeTests(unittest.TestCase):
    def test_failure_classification_is_coarse_and_stable(self) -> None:
        self.assertEqual(runtime.classify_failure("browser", "websocket connection reset"), "browser_transport")
        self.assertEqual(runtime.classify_failure("runner", "runner unavailable"), "runner_unavailable")
        self.assertEqual(runtime.classify_failure("mystery", "unrecognised"), "unknown")

    def test_transient_failure_gets_one_retry_then_bruder_handoff(self) -> None:
        first = runtime.build_fallback_decision("network_timeout", attempt=0, bruder_attempted=False)
        self.assertEqual(first["action"], "retry_same_request")
        second = runtime.build_fallback_decision("network_timeout", attempt=1, bruder_attempted=False)
        self.assertEqual(second["action"], "bruder_handoff")
        exhausted = runtime.build_fallback_decision("network_timeout", attempt=1, bruder_attempted=True)
        self.assertEqual(exhausted["action"], "pause_for_max")

    def test_permission_failure_never_delegates_gate_change(self) -> None:
        decision = runtime.build_fallback_decision("permission", attempt=0, bruder_attempted=False)
        self.assertEqual(decision["action"], "pause_for_max")
        self.assertIn("gate", decision["reason"])

    def test_bruder_handoff_is_local_safe_and_explicitly_bounded(self) -> None:
        handoff = runtime.build_bruder_handoff(
            task_id="ui-lab-demo-001",
            session_id="ui-lab-demo-001",
            request_id="ui-request-001",
            failure_class="app_behavior",
            problem_summary="The synthetic quick flow did not reach the expected state.",
            evidence=[{"kind": "screenshot", "ref": "artifacts/ui-001.png", "sha256": "a" * 64}],
        )
        self.assertEqual(handoff["transport_schema"], "kgg-brain-relay-worker/handoff-v2")
        self.assertEqual(handoff["delivery"], "local_queue_only")
        self.assertIn("do not", handoff["constraints"][0].casefold())
        with self.assertRaisesRegex(runtime.ContractError, "sensitive"):
            runtime.build_bruder_handoff(
                task_id="ui-lab-demo-001",
                session_id="ui-lab-demo-001",
                request_id="ui-request-001",
                failure_class="unknown",
                problem_summary="raw_qr must never be copied",
                evidence=[],
            )

    def test_only_tactical_bruder_goal_patch_can_be_accepted(self) -> None:
        response = {
            "schema": runtime.BRUDER_RESPONSE_SCHEMA,
            "decision": "tactical_plan",
            "plan": ["re-run the unchanged quick flow", "capture one safe screenshot"],
            "goal_patch": {"retry_budget": 1, "timeout_ms": 180000},
            "requires_max": False,
        }
        accepted = runtime.accept_bruder_response(response)
        self.assertEqual(accepted["status"], "TACTICAL_ACCEPTED")
        response["goal_patch"] = {"scope": ["release"], "retry_budget": 1}
        with self.assertRaisesRegex(runtime.ContractError, "goal_patch"):
            runtime.accept_bruder_response(response)

    def test_production_metrics_handoff_artifact_is_pending_only(self) -> None:
        root = Path(__file__).resolve().parents[1]
        artifact_path = root / "docs" / "kgg-ui-lab-v1-production-metrics-bruder-handoff-2026-09-14.json"
        artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
        self.assertEqual(artifact["schema"], runtime.BRUDER_HANDOFF_SCHEMA)
        self.assertEqual(artifact["transport_schema"], "kgg-brain-relay-worker/handoff-v2")
        self.assertEqual(artifact["delivery"], "local_queue_only")
        self.assertEqual(artifact["status"], "PENDING_USER_CONFIRMATION")
        encoded = json.dumps(artifact, ensure_ascii=False).casefold()
        self.assertNotIn("raw_qr", encoded)
        self.assertNotIn("patient_data", encoded)
        self.assertNotIn("api_key", encoded)
        self.assertNotIn("password", encoded)

    def test_historical_snapshots_are_not_treated_as_live_evidence(self) -> None:
        """Historical reports remain immutable snapshots, not live manifests."""

        root = Path(__file__).resolve().parents[1]
        handoff_path = root / "docs" / "kgg-ui-lab-v1-production-metrics-bruder-handoff-2026-09-14.json"
        comparator_path = root / "release-pipeline" / "kgg_gpt_ab_compare.py"
        gates_path = root / "docs" / "kgg-ui-lab-v1-migration-gates-2026-09-14.json"
        handoff = json.loads(handoff_path.read_text(encoding="utf-8"))
        comparator_sha = hashlib.sha256(comparator_path.read_bytes()).hexdigest()
        comparator_refs = {item["ref"]: item["sha256"] for item in handoff["observed_evidence"]}
        self.assertIn("release-pipeline/kgg_gpt_ab_compare.py", comparator_refs)
        self.assertNotEqual(comparator_refs["release-pipeline/kgg_gpt_ab_compare.py"], comparator_sha)
        gates = json.loads(gates_path.read_text(encoding="utf-8"))
        handoff_refs = gates["gates"]["SAFETY_PASS"]["evidence_refs"]
        recorded_handoff = next(item["sha256"] for item in handoff_refs if item["id"] == "production-handoff-001")
        self.assertEqual(recorded_handoff, hashlib.sha256(handoff_path.read_bytes()).hexdigest())
        critical_ref = next(
            item["sha256"]
            for gate in gates["gates"].values()
            for item in gate["evidence_refs"]
            if item["id"] == "critical-gate-001"
        )
        current_battery_sha = hashlib.sha256((root / "release-pipeline" / "kgg_test_battery.py").read_bytes()).hexdigest()
        self.assertNotEqual(critical_ref, current_battery_sha)


if __name__ == "__main__":
    unittest.main()
