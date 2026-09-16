#!/usr/bin/env python3
"""Contract tests for the local UI-Lab MCP-shaped adapter."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import unittest

import kgg_ui_lab_contract as contract
import kgg_ui_lab_mcp_adapter as adapter
from kgg_ui_lab_session import QuickFlowRegistry, RunnerRegistry, SessionStore


class Clock:
    def __init__(self) -> None:
        self.value = datetime(2026, 9, 14, 8, 5, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        current = self.value
        self.value += timedelta(seconds=1)
        return current


MAIN_SHA = "a" * 40


def session() -> dict:
    return {
        "schema": contract.SESSION_SCHEMA,
        "session_id": "mcp-session-001",
        "status": "ready",
        "active_actor": "custom_gpt",
        "request_id": "mcp-request-001",
        "lease": {"owner": "custom_gpt", "issued_at": "2026-09-14T08:00:00Z", "expires_at": "2026-09-14T08:30:00Z"},
        "runner": {"runner_id": "runner-mcp-001", "version": "1.0.0", "browser_revision": "chromium-140", "capabilities": ["browser", "quick_flows", "capture", "width_sweep"]},
        "app": {"name": "admin", "url": "https://preview.example.test/admin", "main_sha": MAIN_SHA, "preview_sha": "b" * 40},
        "device_profile": "tab-s9",
        "viewport": {"width": 1280, "height": 800, "device_scale_factor": 1},
        "quick_flow": {"name": "admin-start-state", "version": "1.0.0"},
        "timeout": {"timeout_ms": 120000, "cleanup_on_cancel": True},
        "artifacts": [],
    }


def request(operation: str = "run_quick_flow", *, main_sha: str = MAIN_SHA, actor: str = "custom_gpt") -> dict:
    return {
        "schema": contract.REQUEST_SCHEMA,
        "request_id": "mcp-request-001",
        "session_id": "mcp-session-001",
        "actor": actor,
        "operation": operation,
        "main_sha": main_sha,
        "payload_sha256": hashlib.sha256(b"synthetic-flow").hexdigest(),
    }


def flow() -> dict:
    return {"name": "admin-start-state", "version": "1.0.0", "steps": [{"operation": "read_state", "label": "admin-ready"}, {"operation": "capture_screenshot", "label": "baseline-screen"}]}


def observe(step: dict) -> dict:
    if step["operation"] == "capture_screenshot":
        return {"expected": "baseline-visible", "actual": "baseline-visible", "status": "pass", "artifacts": [{"id": "shot-001", "kind": "screenshot", "ref": "artifacts/baseline.png", "sha256": "c" * 64}]}
    return {"expected": "admin-ready", "actual": "admin-ready", "status": "pass", "artifacts": []}


def make_adapter(clock: Clock) -> adapter.KggUiLabMcpAdapter:
    runners = RunnerRegistry()
    runners.register(session()["runner"])
    flows = QuickFlowRegistry()
    flows.register(flow())
    return adapter.KggUiLabMcpAdapter(
        main_sha=MAIN_SHA,
        now=clock,
        runner_registry=runners,
        flow_registry=flows,
        session_store=SessionStore(now=clock),
    )


class KggUiLabMcpAdapterTests(unittest.TestCase):
    def test_catalog_is_fixed_and_start_run_evidence_status_are_bounded(self) -> None:
        clock = Clock()
        lab = make_adapter(clock)
        self.assertEqual(lab.tool_catalog(), adapter.TOOL_CATALOG)
        started = lab.start_ui_session(session())
        self.assertEqual(started["operation"], "start_ui_session")
        result = lab.run_quick_flow(request(), observe)
        self.assertEqual(result["result"]["status"], "PASS")
        self.assertEqual(result["session_status"], "completed")
        self.assertEqual(lab.get_session_status("mcp-session-001", "custom_gpt")["event_count"], 3)
        self.assertEqual(len(lab.get_test_evidence("mcp-session-001", "custom_gpt")["evidence"]), 1)

    def test_duplicate_request_and_stale_main_fail_closed(self) -> None:
        clock = Clock()
        lab = make_adapter(clock)
        lab.start_ui_session(session())
        lab.run_quick_flow(request(), observe)
        with self.assertRaisesRegex(adapter.McpAdapterError, "duplicate_request"):
            lab.run_quick_flow(request(), observe)

        other = make_adapter(Clock())
        stale = dict(session(), app=dict(session()["app"], main_sha="d" * 40))
        with self.assertRaisesRegex(adapter.McpAdapterError, "mcp_stale_main"):
            other.start_ui_session(stale)

    def test_actor_and_capability_gates_are_server_side(self) -> None:
        clock = Clock()
        lab = make_adapter(clock)
        lab.start_ui_session(session())
        with self.assertRaisesRegex(adapter.McpAdapterError, "mcp_auth_denied"):
            lab.get_session_status("mcp-session-001", "codex")
        no_width = dict(session(), runner=dict(session()["runner"], capabilities=["browser", "quick_flows", "capture"]))
        no_width_lab = adapter.KggUiLabMcpAdapter(main_sha=MAIN_SHA, now=Clock(), runner_registry=RunnerRegistry(), flow_registry=QuickFlowRegistry(), session_store=SessionStore(now=Clock()))
        no_width_lab.runners.register(no_width["runner"])
        no_width_lab.start_ui_session(no_width)
        with self.assertRaisesRegex(adapter.McpAdapterError, "capability_missing"):
            no_width_lab.run_width_sweep("mcp-session-001", "custom_gpt", [{"width": 820, "height": 1180, "device_scale_factor": 1}])

    def test_screenshot_requires_an_artifact(self) -> None:
        clock = Clock()
        lab = make_adapter(clock)
        lab.start_ui_session(session())
        with self.assertRaisesRegex(adapter.McpAdapterError, "evidence_missing"):
            lab.capture_screenshot(request("capture_screenshot"), lambda _: {"expected": "screen", "actual": "screen", "status": "pass", "artifacts": []})


if __name__ == "__main__":
    unittest.main()
