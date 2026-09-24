#!/usr/bin/env python3
"""VC08 tests for versioned, persistent UI-Lab Quick Flows."""

from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SERVER_PATH = ROOT / "kgg-plugin" / "mcp" / "server.py"
SPEC = importlib.util.spec_from_file_location("kgg_plugin_mcp_server_vc08", SERVER_PATH)
assert SPEC and SPEC.loader
server = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(server)


SHA = "6" * 40


def flow(*, version: str = "1.0.0", fingerprint: str = "fixture-v1") -> dict[str, object]:
    return {
        "schema": "kgg-ui-lab/flow/v1",
        "flow_id": "synthetic-restart-flow",
        "name": "Synthetic restart flow",
        "project": "synthetic-project",
        "scope": "project",
        "store": "USER_SAVED_FLOWS",
        "version": version,
        "status": "active",
        "start_conditions": ["admin-preview", "synthetic-data-only"],
        "steps": [
            {"sequence": 1, "operation": "observe", "label": "ready", "expected_state": "ready"},
            {"sequence": 2, "operation": "click", "label": "bounded-action", "target": {"kind": "action_id", "value": "bounded-action"}, "expected_state": "done"},
            {"sequence": 3, "operation": "swipe", "label": "bounded-swipe", "target": {"kind": "action_id", "value": "swipe-surface"}, "start": {"x": 100, "y": 300}, "end": {"x": 240, "y": 300}, "duration_ms": 250, "expected_state": "swiped"},
            {"sequence": 4, "operation": "wait", "label": "settled", "timeout_ms": 50},
        ],
        "expected_states": {"intermediate": ["ready", "done", "swiped"], "final": "swiped"},
        "toggle_states": {"before": {"language": "de"}, "after": {"language": "en"}},
        "viewport_constraints": {"min_width": 240, "max_width": 2000, "min_height": 240, "max_height": 1400, "device_scale_factor": [0.5, 2]},
        "device_constraints": ["custom"],
        "binding": {"source_fingerprint": fingerprint, "app_name": "admin"},
        "safety_class": "synthetic-bounded",
        "metadata": {"source": "vc08-test", "synthetic": True},
    }


def session(session_id: str = "flow-session-001", request_id: str = "flow-request-001") -> dict[str, object]:
    return {
        "schema": server.SESSION_SCHEMA,
        "session_id": session_id,
        "status": "created",
        "active_actor": "codex",
        "request_id": request_id,
        "lease": {"owner": "codex", "issued_at": "2026-01-01T00:00:00Z", "expires_at": "2030-01-01T00:00:00Z"},
        "runner": {"runner_id": "flow-runner-001", "version": "1.0.0", "browser_revision": "synthetic", "capabilities": ["browser", "quick_flows", "capture"]},
        "app": {"name": "admin", "url": "https://preview.example.test/admin", "main_sha": SHA, "preview_sha": "7" * 40},
        "device_profile": "custom",
        "viewport": {"width": 1280, "height": 800, "device_scale_factor": 1},
        "quick_flow": {"name": "synthetic-restart-flow", "version": "1.0.0"},
        "timeout": {"timeout_ms": 120000, "cleanup_on_cancel": True},
        "artifacts": [],
    }


def request(session_id: str, request_id: str) -> dict[str, object]:
    return {
        "schema": server.REQUEST_SCHEMA,
        "request_id": request_id,
        "session_id": session_id,
        "actor": "codex",
        "operation": "run_flow",
        "main_sha": SHA,
        "payload_sha256": hashlib.sha256(b"synthetic-persistent-flow").hexdigest(),
    }


def call(runtime: object, call_id: int, name: str, arguments: dict[str, object]) -> dict[str, object]:
    response = server.handle(runtime, {"jsonrpc": "2.0", "id": call_id, "method": "tools/call", "params": {"name": name, "arguments": arguments}})
    assert response is not None
    return response["result"]


class KggUiLabFlowPersistenceTests(unittest.TestCase):
    def test_builtins_are_exactly_the_three_kgg_certificates(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = server.Runtime(flow_store_path=Path(directory) / "flows.json").flow_store
            builtins = store.list_flows(project="kgg-ui-lab", scope="project")
        self.assertEqual([item["flow_id"] for item in builtins], ["admin-start-baseline", "pilot-180-reproduce", "synthetic-qr-preview-link"])
        for item in builtins:
            self.assertEqual(item["store"], "BUILTIN_VERSIONED_FLOWS")
            self.assertTrue(item["binding"]["source_fingerprint"])
            self.assertEqual(item["metadata"]["synthetic"], True)

    def test_save_restart_list_get_and_run_are_persistent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "flows.json"
            first = server.Runtime(flow_store_path=path)
            saved = first.save_flow({"flow": flow()})
            self.assertEqual(saved["flow"]["version"], "1.0.0")
            restarted = server.Runtime(flow_store_path=path)
            listed = restarted.list_flows({"project": "synthetic-project", "scope": "project"})
            self.assertEqual([item["flow_id"] for item in listed["flows"]], ["synthetic-restart-flow"])
            self.assertEqual(restarted.get_flow({"flow_id": "synthetic-restart-flow", "project": "synthetic-project", "scope": "project", "version": "1.0.0"})["flow"]["name"], "Synthetic restart flow")
            started = restarted.start(session("flow-session-001", "flow-request-001"))
            result = restarted.run_flow({
                "request": request("flow-session-001", "flow-request-001"),
                "flow_id": "synthetic-restart-flow",
                "project": "synthetic-project",
                "scope": "project",
                "version": "1.0.0",
                "binding_fingerprint": "fixture-v1",
                "toggle_states": {"before": {"language": "de"}},
            })
            self.assertEqual(started["session"]["status"], "ready")
            self.assertEqual(result["result"]["status"], "PASS")
            self.assertEqual(result["result"]["final_state"], "swiped")
            self.assertEqual(result["result"]["toggle_states"]["after"], {"language": "en"})

    def test_all_flow_operations_cross_the_mcp_boundary(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runtime = server.Runtime(flow_store_path=Path(directory) / "flows.json")
            saved = call(runtime, 1, "save_flow", {"flow": flow()})
            self.assertFalse(saved.get("isError", False))
            listed = call(runtime, 2, "list_flows", {"project": "synthetic-project", "scope": "project"})
            self.assertEqual([item["version"] for item in listed["structuredContent"]["flows"]], ["1.0.0"])
            fetched = call(runtime, 3, "get_flow", {"flow": {"flow_id": "synthetic-restart-flow", "project": "synthetic-project", "scope": "project", "version": "1.0.0"}})
            self.assertEqual(fetched["structuredContent"]["flow"]["store"], "USER_SAVED_FLOWS")
            call(runtime, 4, "start_ui_session", {"session": session()})
            ran = call(runtime, 5, "run_flow", {
                "request": request("flow-session-001", "flow-request-001"),
                "flow_id": "synthetic-restart-flow", "project": "synthetic-project", "scope": "project", "version": "1.0.0", "binding_fingerprint": "fixture-v1", "toggle_states": {"before": {"language": "de"}},
            })
            self.assertEqual(ran["structuredContent"]["result"]["status"], "PASS")
            newer = flow(version="1.1.0")
            newer["name"] = "Synthetic restart flow v1.1"
            versioned = call(runtime, 6, "create_new_version", {"flow": newer})
            self.assertEqual(versioned["structuredContent"]["flow"]["version"], "1.1.0")
            deprecated = call(runtime, 7, "deprecate_flow", {"flow": {"flow_id": "synthetic-restart-flow", "project": "synthetic-project", "scope": "project", "version": "1.0.0"}})
            self.assertEqual(deprecated["structuredContent"]["flow"]["status"], "deprecated")

    def test_new_version_is_append_only_and_deprecation_is_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runtime = server.Runtime(flow_store_path=Path(directory) / "flows.json")
            runtime.save_flow({"flow": flow()})
            with self.assertRaises(server.ServerError) as duplicate:
                runtime.save_flow({"flow": flow()})
            self.assertEqual(duplicate.exception.code, "flow_version_exists")
            newer = flow(version="1.1.0")
            newer["name"] = "Synthetic restart flow v1.1"
            created = runtime.create_new_version({"flow": newer})
            self.assertEqual(created["flow"]["version"], "1.1.0")
            self.assertEqual(runtime.get_flow({"flow_id": "synthetic-restart-flow", "project": "synthetic-project", "scope": "project", "version": "1.0.0"})["flow"]["name"], "Synthetic restart flow")
            deprecated = runtime.deprecate_flow({"flow_id": "synthetic-restart-flow", "project": "synthetic-project", "scope": "project", "version": "1.0.0"})
            self.assertEqual(deprecated["flow"]["status"], "deprecated")
            self.assertEqual([item["version"] for item in runtime.list_flows({"project": "synthetic-project", "scope": "project"})["flows"]], ["1.1.0"])

    def test_drift_toggle_and_sensitive_flow_inputs_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            runtime = server.Runtime(flow_store_path=Path(directory) / "flows.json")
            runtime.save_flow({"flow": flow()})
            runtime.start(session())
            with self.assertRaises(server.ServerError) as drift:
                runtime.run_flow({
                    "request": request("flow-session-001", "flow-request-001"),
                    "flow_id": "synthetic-restart-flow", "project": "synthetic-project", "scope": "project", "version": "1.0.0", "binding_fingerprint": "fixture-v2",
                })
            self.assertEqual(drift.exception.code, "flow_drift_detected")
            with self.assertRaises(server.ServerError) as toggle:
                runtime.run_flow({
                    "request": request("flow-session-001", "flow-request-001"),
                    "flow_id": "synthetic-restart-flow", "project": "synthetic-project", "scope": "project", "version": "1.0.0", "binding_fingerprint": "fixture-v1", "toggle_states": {"before": {"language": "en"}},
                })
            self.assertEqual(toggle.exception.code, "flow_toggle_precondition_mismatch")
            with self.assertRaises(server.ServerError) as sensitive:
                runtime.save_flow({"flow": {**flow(), "metadata": {"patient_data": "synthetic"}}})
            self.assertEqual(sensitive.exception.code, "sensitive_field")


if __name__ == "__main__":
    unittest.main()
