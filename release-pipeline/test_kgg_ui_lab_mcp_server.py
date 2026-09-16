#!/usr/bin/env python3
"""Contract tests for the installed-plugin stdio MCP server."""

from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import unittest


SERVER_PATH = Path(__file__).resolve().parents[1] / "kgg-plugin" / "mcp" / "server.py"
SPEC = importlib.util.spec_from_file_location("kgg_plugin_mcp_server", SERVER_PATH)
assert SPEC and SPEC.loader
server = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(server)


SHA = "4" * 40


def session() -> dict[str, object]:
    return {
        "schema": server.SESSION_SCHEMA,
        "session_id": "server-session-001",
        "status": "created",
        "active_actor": "codex",
        "request_id": "server-request-001",
        "lease": {"owner": "codex", "issued_at": "2026-01-01T00:00:00Z", "expires_at": "2030-01-01T00:00:00Z"},
        "runner": {"runner_id": "server-runner-001", "version": "1.0.0", "browser_revision": "synthetic", "capabilities": ["browser", "quick_flows", "capture", "width_sweep"]},
        "app": {"name": "admin", "url": "https://preview.example.test/admin", "main_sha": SHA, "preview_sha": "b" * 40},
        "device_profile": "tab-s9",
        "viewport": {"width": 1280, "height": 800, "device_scale_factor": 1},
        "quick_flow": {"name": "pilot-180-reproduce", "version": "1.0.0"},
        "timeout": {"timeout_ms": 120000, "cleanup_on_cancel": True},
        "artifacts": [],
    }


def request() -> dict[str, object]:
    return {
        "schema": server.REQUEST_SCHEMA,
        "request_id": "server-request-001",
        "session_id": "server-session-001",
        "actor": "codex",
        "operation": "run_quick_flow",
        "main_sha": SHA,
        "payload_sha256": hashlib.sha256(b"synthetic-flow").hexdigest(),
    }


class KggUiLabMcpServerTests(unittest.TestCase):
    @staticmethod
    def _call(runtime: server.Runtime, call_id: int, name: str, arguments: dict[str, object]) -> dict[str, object]:
        response = server.handle(
            runtime,
            {
                "jsonrpc": "2.0",
                "id": call_id,
                "method": "tools/call",
                "params": {"name": name, "arguments": arguments},
            },
        )
        assert response is not None
        return response["result"]

    def test_initialize_and_catalog_are_bounded(self) -> None:
        runtime = server.Runtime()
        initialized = server.handle(runtime, {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}})
        self.assertEqual(initialized["result"]["serverInfo"]["name"], "kgg-ui-lab")
        listed = server.handle(runtime, {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
        self.assertEqual([item["name"] for item in listed["result"]["tools"]], list(server.TOOL_NAMES))
        self.assertTrue(all(item["annotations"]["readOnlyHint"] for item in listed["result"]["tools"]))

    def test_synthetic_flow_is_in_memory_and_replay_is_rejected(self) -> None:
        runtime = server.Runtime()
        started = server.handle(runtime, {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "start_ui_session", "arguments": {"session": session()}}})
        self.assertFalse(started["result"].get("isError", False))
        result = server.handle(runtime, {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "run_quick_flow", "arguments": {"request": request()}}})
        self.assertFalse(result["result"].get("isError", False))
        self.assertEqual(result["result"]["structuredContent"]["result"]["status"], "PASS")
        self.assertEqual(len(result["result"]["structuredContent"]["result"]["steps"]), 4)
        replay = server.handle(runtime, {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "run_quick_flow", "arguments": {"request": request()}}})
        self.assertTrue(replay["result"]["isError"])
        self.assertIn("duplicate_request", replay["result"]["content"][0]["text"])
        self.assertEqual(len(runtime.sessions), 1)

    def test_actor_and_sensitive_input_fail_closed(self) -> None:
        runtime = server.Runtime()
        bad_actor = server.handle(runtime, {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "get_current_state", "arguments": {"actor": "unknown"}}})
        self.assertTrue(bad_actor["result"]["isError"])
        self.assertIn("mcp_auth_denied", bad_actor["result"]["content"][0]["text"])
        sensitive = server.handle(runtime, {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "get_ticket_state", "arguments": {"actor": "codex", "ticket_id": "#180", "api_key": "synthetic"}}})
        self.assertTrue(sensitive["result"]["isError"])
        self.assertIn("sensitive_field", sensitive["result"]["content"][0]["text"])

    def test_missing_capability_stale_sha_and_unavailable_tool_fail_closed(self) -> None:
        runtime = server.Runtime()
        reduced = session()
        reduced["runner"] = dict(reduced["runner"], capabilities=["browser", "capture", "width_sweep"])
        started = self._call(runtime, 1, "start_ui_session", {"session": reduced})
        self.assertFalse(started.get("isError", False))
        missing = self._call(runtime, 2, "run_quick_flow", {"request": request()})
        self.assertTrue(missing["isError"])
        self.assertIn("capability_missing", missing["content"][0]["text"])

        runtime = server.Runtime()
        self._call(runtime, 3, "start_ui_session", {"session": session()})
        stale = dict(request(), main_sha="5" * 40)
        stale_result = self._call(runtime, 4, "run_quick_flow", {"request": stale})
        self.assertTrue(stale_result["isError"])
        self.assertIn("mcp_stale_main", stale_result["content"][0]["text"])

        unavailable = server.handle(
            runtime,
            {
                "jsonrpc": "2.0",
                "id": 5,
                "method": "tools/call",
                "params": {"name": "not_a_kgg_tool", "arguments": {}},
            },
        )
        self.assertIsNotNone(unavailable)
        self.assertTrue(unavailable["result"]["isError"])
        self.assertIn("tool_not_found", unavailable["result"]["content"][0]["text"])

    def test_expired_lease_and_invalid_timeout_fail_closed(self) -> None:
        runtime = server.Runtime()
        self._call(runtime, 1, "start_ui_session", {"session": session()})
        runtime.sessions["server-session-001"]["lease"]["expires_at"] = "2020-01-01T00:00:00Z"
        expired = self._call(
            runtime,
            2,
            "set_device_profile",
            {"session_id": "server-session-001", "actor": "codex", "profile": "tab-s9"},
        )
        self.assertTrue(expired["isError"])
        self.assertIn("lease_expired", expired["content"][0]["text"])

        invalid_timeout = session()
        invalid_timeout["session_id"] = "server-session-002"
        invalid_timeout["request_id"] = "server-request-002"
        invalid_timeout["timeout"] = {"timeout_ms": 999, "cleanup_on_cancel": True}
        timeout_result = self._call(runtime, 3, "start_ui_session", {"session": invalid_timeout})
        self.assertTrue(timeout_result["isError"])
        self.assertIn("timeout_invalid", timeout_result["content"][0]["text"])


if __name__ == "__main__":
    unittest.main()
