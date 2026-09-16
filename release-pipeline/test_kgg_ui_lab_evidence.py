#!/usr/bin/env python3
"""Contract tests for immutable, synthetic UI Lab evidence."""

from __future__ import annotations

import unittest

import kgg_ui_lab_contract as contract
import kgg_ui_lab_evidence as evidence


def valid_session() -> dict:
    return {
        "schema": contract.SESSION_SCHEMA,
        "session_id": "ui-lab-evidence-001",
        "status": "ready",
        "active_actor": "custom_gpt",
        "request_id": "ui-request-001",
        "lease": {
            "owner": "custom_gpt",
            "issued_at": "2026-09-14T08:00:00Z",
            "expires_at": "2026-09-14T08:30:00Z",
        },
        "runner": {
            "runner_id": "runner-local-001",
            "version": "1.0.0",
            "browser_revision": "chromium-140",
            "capabilities": ["browser", "quick_flows", "capture"],
        },
        "app": {
            "name": "admin",
            "url": "https://preview.example.test/admin",
            "main_sha": "a" * 40,
            "preview_sha": "b" * 40,
        },
        "device_profile": "tab-s9",
        "viewport": {"width": 1280, "height": 800, "device_scale_factor": 1},
        "quick_flow": {"name": "open-tablet-layout", "version": "1.0.0"},
        "timeout": {"timeout_ms": 120000, "cleanup_on_cancel": True},
        "artifacts": [],
    }


def pass_steps() -> list[dict]:
    return [
        {
            "sequence": 1,
            "label": "initial-state",
            "expected": "layout-ready",
            "actual": "layout-ready",
            "status": "pass",
            "artifact_refs": [],
        },
        {
            "sequence": 2,
            "label": "tablet-layout",
            "expected": "tablet-layout-visible",
            "actual": "tablet-layout-visible",
            "status": "pass",
            "artifact_refs": ["shot-001"],
        },
    ]


def screenshot() -> dict:
    return {"id": "shot-001", "kind": "screenshot", "ref": "artifacts/ui-001.png", "sha256": "c" * 64}


class KggUiLabEvidenceTests(unittest.TestCase):
    def test_pass_evidence_is_canonical_and_hashable(self) -> None:
        artifact = evidence.build_evidence(
            session=valid_session(),
            started_at="2026-09-14T08:05:00Z",
            ended_at="2026-09-14T08:06:00Z",
            status="PASS",
            error_class="",
            steps=pass_steps(),
            artifacts=[screenshot()],
        )
        validated = evidence.validate_evidence(artifact)
        self.assertEqual(validated["schema"], evidence.EVIDENCE_SCHEMA)
        self.assertEqual(len(validated["provenance_sha256"]), 64)

    def test_required_screenshot_cannot_be_missing(self) -> None:
        with self.assertRaisesRegex(evidence.ContractError, "evidence_missing"):
            evidence.build_evidence(
                session=valid_session(),
                started_at="2026-09-14T08:05:00Z",
                ended_at="2026-09-14T08:06:00Z",
                status="PASS",
                error_class="",
                steps=pass_steps(),
                artifacts=[],
                required_artifact_kinds={"screenshot"},
            )

    def test_pass_step_with_conflicting_actual_state_is_rejected(self) -> None:
        steps = pass_steps()
        steps[1]["actual"] = "layout-hidden"
        with self.assertRaisesRegex(evidence.ContractError, "evidence_conflict"):
            evidence.build_evidence(
                session=valid_session(),
                started_at="2026-09-14T08:05:00Z",
                ended_at="2026-09-14T08:06:00Z",
                status="PASS",
                error_class="",
                steps=steps,
                artifacts=[screenshot()],
            )

    def test_tampering_after_creation_is_detected(self) -> None:
        artifact = evidence.build_evidence(
            session=valid_session(),
            started_at="2026-09-14T08:05:00Z",
            ended_at="2026-09-14T08:06:00Z",
            status="PASS",
            error_class="",
            steps=pass_steps(),
            artifacts=[screenshot()],
        )
        artifact["steps"][0]["actual"] = "tampered"
        with self.assertRaisesRegex(evidence.ContractError, "evidence_hash"):
            evidence.validate_evidence(artifact)

    def test_sensitive_evidence_is_rejected(self) -> None:
        artifact = screenshot()
        artifact["kind"] = "raw_qr"
        with self.assertRaisesRegex(evidence.ContractError, "sensitive"):
            evidence.build_evidence(
                session=valid_session(),
                started_at="2026-09-14T08:05:00Z",
                ended_at="2026-09-14T08:06:00Z",
                status="FAIL",
                error_class="app_behavior",
                steps=pass_steps(),
                artifacts=[artifact],
            )


if __name__ == "__main__":
    unittest.main()

