#!/usr/bin/env python3
"""Tests for the initial three UI-Lab Quick-Flow certificates."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import unittest

import kgg_ui_lab_contract as contract
import kgg_ui_lab_quick_flows as flows
import kgg_ui_lab_mcp_adapter as adapter
from kgg_ui_lab_session import QuickFlowRegistry, RunnerRegistry, SessionStore


class Clock:
    def __init__(self) -> None:
        self.value = datetime(2026, 9, 14, 9, 0, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        current = self.value
        self.value += timedelta(seconds=1)
        return current


class KggUiLabQuickFlowTests(unittest.TestCase):
    def test_exactly_three_flows_have_numbered_steps_and_cleanup(self) -> None:
        certified = flows.validate_certified_quick_flows()
        self.assertEqual(len(certified), 3)
        self.assertEqual(
            {item["name"] for item in certified},
            {"admin-start-baseline", "pilot-180-reproduce", "synthetic-qr-preview-link"},
        )
        for flow in certified:
            self.assertEqual([step["sequence"] for step in flow["steps"]], list(range(1, len(flow["steps"]) + 1)))
            self.assertIn("screenshot", flow["required_artifact_kinds"])
            self.assertTrue(flow["cleanup"])

    def test_runtime_projection_remains_selector_free(self) -> None:
        projections = flows.runtime_flows()
        self.assertEqual(len(projections), 3)
        for flow in projections:
            for step in flow["steps"]:
                self.assertEqual(set(step), {"operation", "label"})
                self.assertNotIn("selector", step)

    def test_certificate_rejects_duplicate_or_missing_flow_metadata(self) -> None:
        original = flows.CERTIFIED_QUICK_FLOWS
        try:
            flows.CERTIFIED_QUICK_FLOWS = original[:2]  # type: ignore[misc]
            with self.assertRaisesRegex(ValueError, "count"):
                flows.validate_certified_quick_flows()
        finally:
            flows.CERTIFIED_QUICK_FLOWS = original  # type: ignore[misc]

    def test_all_three_certificates_execute_through_the_local_adapter(self) -> None:
        main_sha = "a" * 40
        runner = {
            "runner_id": "runner-three-flows",
            "version": "1.0.0",
            "browser_revision": "chromium-140",
            "capabilities": ["browser", "quick_flows", "capture", "width_sweep", "qr_image"],
        }
        for index, flow in enumerate(flows.runtime_flows(), start=1):
            clock = Clock()
            runners = RunnerRegistry()
            runners.register(runner)
            registry = QuickFlowRegistry()
            registry.register(flow)
            session_id = f"three-flow-session-{index:03d}"
            request_id = f"three-flow-request-{index:03d}"
            session = {
                "schema": contract.SESSION_SCHEMA,
                "session_id": session_id,
                "status": "ready",
                "active_actor": "custom_gpt",
                "request_id": request_id,
                "lease": {"owner": "custom_gpt", "issued_at": "2026-09-14T08:00:00Z", "expires_at": "2026-09-14T10:00:00Z"},
                "runner": runner,
                "app": {"name": "admin", "url": "https://preview.example.test/admin", "main_sha": main_sha, "preview_sha": "b" * 40},
                "device_profile": "custom",
                "viewport": {"width": 1280, "height": 800, "device_scale_factor": 1},
                "quick_flow": {"name": flow["name"], "version": flow["version"]},
                "timeout": {"timeout_ms": 120000, "cleanup_on_cancel": True},
                "artifacts": [],
            }
            lab = adapter.KggUiLabMcpAdapter(
                main_sha=main_sha,
                now=clock,
                runner_registry=runners,
                flow_registry=registry,
                session_store=SessionStore(now=clock),
            )
            lab.start_ui_session(session)

            def observe(step: dict, *, flow_name: str = flow["name"]) -> dict:
                if step["operation"] == "capture_screenshot":
                    digest = hashlib.sha256(f"{flow_name}:{step['label']}".encode("utf-8")).hexdigest()
                    return {
                        "expected": step["label"],
                        "actual": step["label"],
                        "status": "pass",
                        "artifacts": [{"id": f"shot-{index:03d}-{len(step['label']):03d}", "kind": "screenshot", "ref": f"artifacts/{flow_name}.png", "sha256": digest}],
                    }
                return {"expected": step["label"], "actual": step["label"], "status": "pass", "artifacts": []}

            request = {
                "schema": contract.REQUEST_SCHEMA,
                "request_id": request_id,
                "session_id": session_id,
                "actor": "custom_gpt",
                "operation": "run_quick_flow",
                "main_sha": main_sha,
                "payload_sha256": hashlib.sha256(flow["name"].encode("utf-8")).hexdigest(),
            }
            result = lab.run_quick_flow(request, observe)
            self.assertEqual(result["result"]["status"], "PASS", flow["name"])
            self.assertEqual(result["session_status"], "completed")
            self.assertTrue(result["evidence"]["artifacts"], flow["name"])


if __name__ == "__main__":
    unittest.main()
