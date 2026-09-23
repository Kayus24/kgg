#!/usr/bin/env python3
"""Local real-browser bridge tests using the pre-provisioned Playwright runtime."""

from __future__ import annotations

from contextlib import contextmanager
import hashlib
import http.server
import importlib.util
import os
from pathlib import Path
import shutil
import threading
import unittest


ROOT = Path(__file__).resolve().parents[1]
SERVER_PATH = ROOT / "kgg-plugin" / "mcp" / "server.py"
SPEC = importlib.util.spec_from_file_location("kgg_plugin_mcp_server_real", SERVER_PATH)
assert SPEC and SPEC.loader
server = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(server)

MAIN_SHA = "a" * 40


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None:  # noqa: A003 - stdlib signature
        return


@contextmanager
def local_fixture_server():
    handler = lambda *args, **kwargs: _QuietHandler(*args, directory=str(ROOT / "release-pipeline"), **kwargs)
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{httpd.server_port}/kgg_ui_lab_real_fixture.html"
    finally:
        httpd.shutdown()
        thread.join(timeout=5)
        httpd.server_close()


def _runtime_available() -> tuple[str, str] | None:
    node = os.environ.get("KGG_BROWSER_NODE") or shutil.which("node")
    module_path = os.environ.get("KGG_PLAYWRIGHT_NODE_PATH")
    if not module_path:
        candidate = Path.home() / ".cache" / "codex-runtimes" / "codex-primary-runtime" / "dependencies" / "node" / "node_modules"
        if (candidate / "playwright").is_dir():
            module_path = str(candidate)
    if not node or not module_path or not (Path(module_path) / "playwright").is_dir():
        return None
    return node, module_path


class RealBrowserModuleResolutionTests(unittest.TestCase):
    def test_bridge_resolves_preprovisioned_module_without_installing(self) -> None:
        module = server._load_real_browser_module()
        old = os.environ.pop("KGG_PLAYWRIGHT_NODE_PATH", None)
        try:
            resolved = module._playwright_module_path()
            if resolved is None:
                self.skipTest("no pre-provisioned Playwright runtime is available")
            self.assertTrue((Path(resolved) / "playwright").is_dir())
        finally:
            if old is not None:
                os.environ["KGG_PLAYWRIGHT_NODE_PATH"] = old


class ToolCatalogContractTests(unittest.TestCase):
    def test_request_schema_exposes_fields_required_by_visual_tools(self) -> None:
        catalog = {item["name"]: item for item in server.tool_catalog()}
        request_schema = catalog["observe_visual_state"]["inputSchema"]["properties"]["request"]
        self.assertEqual(request_schema["properties"]["schema"]["const"], server.REQUEST_SCHEMA)
        self.assertEqual(
            request_schema["required"],
            ["schema", "request_id", "session_id", "actor", "operation", "main_sha", "payload_sha256"],
        )
        self.assertEqual(request_schema["properties"]["operation"]["enum"], [
            "run_quick_flow",
            "capture_screenshot",
            "observe_visual_state",
            "execute_visual_action",
        ])
        self.assertTrue(request_schema["additionalProperties"] is False)


def _session(url: str, *, session_id: str = "real-bridge-session-001", request_id: str = "real-bridge-request-001", flow_name: str = "pilot-180-reproduce", capabilities: list[str] | None = None) -> dict[str, object]:
    return {
        "schema": server.SESSION_SCHEMA,
        "session_id": session_id,
        "status": "created",
        "active_actor": "codex",
        "request_id": request_id,
        "lease": {"owner": "codex", "issued_at": "2026-01-01T00:00:00Z", "expires_at": "2030-01-01T00:00:00Z"},
        "runner": {"runner_id": "real-browser-runner-001", "version": "1.0.0", "browser_revision": "playwright-1.62.1", "capabilities": capabilities or ["browser", "quick_flows", "capture"]},
        "app": {"name": "admin", "url": url, "main_sha": MAIN_SHA, "preview_sha": "b" * 40},
        "device_profile": "tab-s9",
        "viewport": {"width": 960, "height": 720, "device_scale_factor": 1},
        "quick_flow": {"name": flow_name, "version": "1.0.0"},
        "timeout": {"timeout_ms": 120000, "cleanup_on_cancel": True},
        "artifacts": [],
    }


def _request(*, session_id: str = "real-bridge-session-001", request_id: str = "real-bridge-request-001", operation: str = "run_quick_flow") -> dict[str, object]:
    return {
        "schema": server.REQUEST_SCHEMA,
        "request_id": request_id,
        "session_id": session_id,
        "actor": "codex",
        "operation": operation,
        "main_sha": MAIN_SHA,
        "payload_sha256": hashlib.sha256(b"real-browser-flow").hexdigest(),
    }


def _visual_request(*, session_id: str, request_id: str, operation: str) -> dict[str, object]:
    return _request(session_id=session_id, request_id=request_id, operation=operation)


class KggRealBrowserBridgeTests(unittest.TestCase):
    def test_https_origin_and_path_allowlist_fail_closed(self) -> None:
        old = os.environ.get("KGG_REAL_BROWSER")
        os.environ["KGG_REAL_BROWSER"] = "1"
        try:
            active = server.Runtime()
            rejected = server.handle(active, {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "start_ui_session", "arguments": {"session": _session("https://example.com/kgg/", session_id="origin-blocked-session", request_id="origin-blocked-request")}}})
            self.assertTrue(rejected["result"]["isError"])
            self.assertIn("app_url_invalid", rejected["result"]["content"][0]["text"])
            accepted = server.handle(active, {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "start_ui_session", "arguments": {"session": _session("https://kayus24.github.io/kgg/", session_id="origin-allowed-session", request_id="origin-allowed-request")}}})
            self.assertFalse(accepted["result"].get("isError", False), accepted)
        finally:
            if old is None:
                os.environ.pop("KGG_REAL_BROWSER", None)
            else:
                os.environ["KGG_REAL_BROWSER"] = old

    def test_quick_flow_opens_visual_fallback_on_real_locator_drift(self) -> None:
        runtime = _runtime_available()
        if runtime is None:
            self.skipTest("pre-provisioned Playwright runtime is not available")
        node, module_path = runtime
        old = {key: os.environ.get(key) for key in ("KGG_REAL_BROWSER", "KGG_BROWSER_NODE", "KGG_PLAYWRIGHT_NODE_PATH")}
        os.environ.update({"KGG_REAL_BROWSER": "1", "KGG_BROWSER_NODE": node, "KGG_PLAYWRIGHT_NODE_PATH": module_path})
        try:
            with local_fixture_server() as base_url:
                active = server.Runtime()
                session_id = "visual-fallback-session-001"
                request_id = "visual-fallback-request-001"
                url = f"{base_url}?flow=pilot&drift=1"
                capabilities = ["browser", "quick_flows", "capture", "visual_loop"]
                started = server.handle(active, {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "start_ui_session", "arguments": {"session": _session(url, session_id=session_id, request_id=request_id, capabilities=capabilities)}}})
                self.assertFalse(started["result"].get("isError", False), started)
                response = server.handle(active, {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "run_quick_flow", "arguments": {"request": _request(session_id=session_id, request_id=request_id)}}})
                structured = response["result"]["structuredContent"]
                self.assertEqual(structured["result"]["status"], "FAIL")
                self.assertEqual(structured["result"]["error_class"], "action_target_not_found")
                fallback = structured["result"]["fallback"]
                self.assertEqual(fallback["status"], "READY")
                self.assertEqual(fallback["flow_status"], "STALE_REQUIRES_REVIEW")
                self.assertEqual(fallback["observation"]["state"], "pilot-area-ready")
                self.assertEqual(len(response["result"]["content"]), 3)  # text + failed-flow shot + fallback shot
                observation_id = fallback["observation"]["id"]
                decision = {"operation": "click", "label": "drifted-control", "expected_state_after": "scale-drag-state", "observation_id": observation_id}
                acted = server.handle(active, {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "execute_visual_action", "arguments": {"request": _visual_request(session_id=session_id, request_id="visual-fallback-request-002", operation="execute_visual_action"), "decision": decision}}})
                self.assertFalse(acted["result"].get("isError", False), acted)
                action = acted["result"]["structuredContent"]
                self.assertEqual(action["result"]["flow_status"], "STALE_REQUIRES_REVIEW")
                self.assertEqual(action["session_status"], "stale_fallback_completed")
                self.assertEqual(action["result"]["state_after"], "scale-drag-state")
                self.assertEqual(len(active.visual_sessions), 0)
        finally:
            for key, value in old.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def test_visual_loop_reuses_page_and_verifies_agent_decision(self) -> None:
        runtime = _runtime_available()
        if runtime is None:
            self.skipTest("pre-provisioned Playwright runtime is not available")
        node, module_path = runtime
        old = {key: os.environ.get(key) for key in ("KGG_REAL_BROWSER", "KGG_BROWSER_NODE", "KGG_PLAYWRIGHT_NODE_PATH")}
        os.environ.update({"KGG_REAL_BROWSER": "1", "KGG_BROWSER_NODE": node, "KGG_PLAYWRIGHT_NODE_PATH": module_path})
        try:
            with local_fixture_server() as base_url:
                url = f"{base_url}?flow=pilot"
                active = server.Runtime()
                session_id = "visual-loop-session-001"
                request_id = "visual-loop-request-001"
                started = server.handle(active, {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "start_ui_session", "arguments": {"session": _session(url, session_id=session_id, request_id=request_id, capabilities=["browser", "capture", "visual_loop"])}}})
                self.assertFalse(started["result"].get("isError", False), started)
                observed = server.handle(active, {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "observe_visual_state", "arguments": {"request": _visual_request(session_id=session_id, request_id=request_id, operation="observe_visual_state")}}})
                self.assertFalse(observed["result"].get("isError", False), observed)
                before = observed["result"]["structuredContent"]["observation"]
                self.assertEqual(before["state"], "pilot-area-ready")
                self.assertEqual(len(observed["result"]["content"]), 2)  # text + screenshot A
                decision = {"operation": "click", "label": "tablet-splitter-control", "expected_state_after": "scale-drag-state", "observation_id": before["id"]}
                acted = server.handle(active, {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "execute_visual_action", "arguments": {"request": _visual_request(session_id=session_id, request_id="visual-loop-request-002", operation="execute_visual_action"), "decision": decision}}})
                self.assertFalse(acted["result"].get("isError", False), acted)
                structured = acted["result"]["structuredContent"]
                self.assertEqual(structured["result"]["status"], "PASS")
                self.assertEqual(structured["result"]["state_before"], "pilot-area-ready")
                self.assertEqual(structured["result"]["state_after"], "scale-drag-state")
                self.assertEqual(len(structured["result"]["artifacts"]), 2)
                self.assertNotEqual(structured["result"]["artifacts"][0]["sha256"], structured["result"]["artifacts"][1]["sha256"])
                self.assertEqual(len(acted["result"]["content"]), 3)  # text + screenshot A + screenshot B
                self.assertEqual(len(active.visual_sessions), 0)
        finally:
            for key, value in old.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def test_visual_loop_rejects_unverified_expected_state(self) -> None:
        runtime = _runtime_available()
        if runtime is None:
            self.skipTest("pre-provisioned Playwright runtime is not available")
        node, module_path = runtime
        old = {key: os.environ.get(key) for key in ("KGG_REAL_BROWSER", "KGG_BROWSER_NODE", "KGG_PLAYWRIGHT_NODE_PATH")}
        os.environ.update({"KGG_REAL_BROWSER": "1", "KGG_BROWSER_NODE": node, "KGG_PLAYWRIGHT_NODE_PATH": module_path})
        try:
            with local_fixture_server() as base_url:
                active = server.Runtime()
                session_id = "visual-loop-session-002"
                started = server.handle(active, {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "start_ui_session", "arguments": {"session": _session(f"{base_url}?flow=pilot", session_id=session_id, request_id="visual-loop-request-101", capabilities=["browser", "capture", "visual_loop"])}}})
                self.assertFalse(started["result"].get("isError", False), started)
                observed = server.handle(active, {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "observe_visual_state", "arguments": {"request": _visual_request(session_id=session_id, request_id="visual-loop-request-101", operation="observe_visual_state")}}})
                self.assertFalse(observed["result"].get("isError", False), observed)
                observation_id = observed["result"]["structuredContent"]["observation"]["id"]
                rejected = server.handle(active, {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "execute_visual_action", "arguments": {"request": _visual_request(session_id=session_id, request_id="visual-loop-request-102", operation="execute_visual_action"), "decision": {"operation": "click", "label": "tablet-splitter-control", "expected_state_after": "invented-state", "observation_id": observation_id}}}})
                self.assertTrue(rejected["result"]["isError"])
                self.assertIn("visual_expected_state_not_reached", rejected["result"]["content"][0]["text"])
                self.assertNotIn("synthetic://", rejected["result"]["content"][0]["text"])
                self.assertEqual(len(active.visual_sessions), 0)
        finally:
            for key, value in old.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def test_real_flow_produces_two_hashed_screenshots_and_state_transition(self) -> None:
        runtime = _runtime_available()
        if runtime is None:
            self.skipTest("pre-provisioned Playwright runtime is not available")
        node, module_path = runtime
        old = {key: os.environ.get(key) for key in ("KGG_REAL_BROWSER", "KGG_BROWSER_NODE", "KGG_PLAYWRIGHT_NODE_PATH")}
        os.environ.update({"KGG_REAL_BROWSER": "1", "KGG_BROWSER_NODE": node, "KGG_PLAYWRIGHT_NODE_PATH": module_path})
        try:
            with local_fixture_server() as url:
                active = server.Runtime()
                started = server.handle(active, {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "start_ui_session", "arguments": {"session": _session(url)}}})
                self.assertFalse(started["result"].get("isError", False))
                response = server.handle(active, {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "run_quick_flow", "arguments": {"request": _request()}}})
                result = response["result"]
                self.assertFalse(result.get("isError", False), result)
                structured = result["structuredContent"]
                self.assertEqual(structured["result"]["status"], "PASS")
                self.assertEqual(structured["result"]["final_state"], "scale-drag-state")
                self.assertEqual(len(structured["result"]["steps"]), 5)
                artifacts = structured["result"]["artifacts"]
                self.assertEqual(len(artifacts), 2)
                self.assertNotEqual(artifacts[0]["sha256"], artifacts[1]["sha256"])
                self.assertEqual(len(result["content"]), 3)  # text + screenshot A + screenshot B
                self.assertTrue(all(item["type"] == "image" for item in result["content"][1:]))
        finally:
            for key, value in old.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def test_three_certified_flows_use_the_same_real_bridge(self) -> None:
        runtime = _runtime_available()
        if runtime is None:
            self.skipTest("pre-provisioned Playwright runtime is not available")
        node, module_path = runtime
        old = {key: os.environ.get(key) for key in ("KGG_REAL_BROWSER", "KGG_BROWSER_NODE", "KGG_PLAYWRIGHT_NODE_PATH")}
        os.environ.update({"KGG_REAL_BROWSER": "1", "KGG_BROWSER_NODE": node, "KGG_PLAYWRIGHT_NODE_PATH": module_path})
        try:
            active = server.Runtime()
            flows = (
                ("admin-start-baseline", "admin", "real-flow-session-001", "real-flow-request-001"),
                ("pilot-180-reproduce", "pilot", "real-flow-session-002", "real-flow-request-002"),
                ("synthetic-qr-preview-link", "qr", "real-flow-session-003", "real-flow-request-003"),
            )
            for flow_name, query, session_id, request_id in flows:
                with local_fixture_server() as base_url:
                    url = f"{base_url}?flow={query}"
                    started = server.handle(active, {"jsonrpc": "2.0", "id": 10, "method": "tools/call", "params": {"name": "start_ui_session", "arguments": {"session": _session(url, session_id=session_id, request_id=request_id, flow_name=flow_name)}}})
                    self.assertFalse(started["result"].get("isError", False), started)
                    response = server.handle(active, {"jsonrpc": "2.0", "id": 11, "method": "tools/call", "params": {"name": "run_quick_flow", "arguments": {"request": _request(session_id=session_id, request_id=request_id)}}})
                    result = response["result"]
                    self.assertFalse(result.get("isError", False), result)
                    structured = result["structuredContent"]
                    self.assertEqual(structured["result"]["status"], "PASS")
                    self.assertEqual(len(structured["result"]["artifacts"]), 1 if flow_name == "admin-start-baseline" else 2)
                self.assertEqual(structured["session_status"], "completed")
        finally:
            for key, value in old.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def test_three_certified_flows_have_one_unchanged_replay(self) -> None:
        runtime = _runtime_available()
        if runtime is None:
            self.skipTest("pre-provisioned Playwright runtime is not available")
        node, module_path = runtime
        old = {key: os.environ.get(key) for key in ("KGG_REAL_BROWSER", "KGG_BROWSER_NODE", "KGG_PLAYWRIGHT_NODE_PATH")}
        os.environ.update({"KGG_REAL_BROWSER": "1", "KGG_BROWSER_NODE": node, "KGG_PLAYWRIGHT_NODE_PATH": module_path})
        try:
            flows = (
                ("admin-start-baseline", "admin"),
                ("pilot-180-reproduce", "pilot"),
                ("synthetic-qr-preview-link", "qr"),
            )
            for index, (flow_name, query) in enumerate(flows, start=1):
                results: list[dict[str, object]] = []
                for attempt in ("original", "replay"):
                    with local_fixture_server() as base_url:
                        session_id = f"replay-{index}-{attempt}-session"
                        request_id = f"replay-{index}-{attempt}-request"
                        active = server.Runtime()
                        started = server.handle(active, {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "start_ui_session", "arguments": {"session": _session(f"{base_url}?flow={query}", session_id=session_id, request_id=request_id, flow_name=flow_name)}}})
                        self.assertFalse(started["result"].get("isError", False), started)
                        response = server.handle(active, {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "run_quick_flow", "arguments": {"request": _request(session_id=session_id, request_id=request_id)}}})
                        self.assertFalse(response["result"].get("isError", False), response)
                        structured = response["result"]["structuredContent"]
                        self.assertEqual(structured["result"]["status"], "PASS")
                        results.append(structured["result"])
                first, replay = results
                self.assertEqual(first["final_state"], replay["final_state"])
                self.assertEqual(
                    [(step["expected"], step["actual"], step["status"]) for step in first["steps"]],
                    [(step["expected"], step["actual"], step["status"]) for step in replay["steps"]],
                )
                self.assertEqual(
                    [artifact["sha256"] for artifact in first["artifacts"]],
                    [artifact["sha256"] for artifact in replay["artifacts"]],
                )
        finally:
            for key, value in old.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def test_real_mode_fails_closed_without_host_and_does_not_emit_synthetic_artifact(self) -> None:
        old = {key: os.environ.get(key) for key in ("KGG_REAL_BROWSER", "KGG_BROWSER_NODE")}
        os.environ.update({"KGG_REAL_BROWSER": "1", "KGG_BROWSER_NODE": str(ROOT / "does-not-exist-node")})
        try:
            active = server.Runtime()
            started = server.handle(active, {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "start_ui_session", "arguments": {"session": _session("http://127.0.0.1:9/not-running")}}})
            self.assertFalse(started["result"].get("isError", False))
            response = server.handle(active, {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "run_quick_flow", "arguments": {"request": _request()}}})
            self.assertTrue(response["result"]["isError"])
            self.assertIn("real_browser_node_unavailable", response["result"]["content"][0]["text"])
            self.assertNotIn("synthetic://", response["result"]["content"][0]["text"])
        finally:
            for key, value in old.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value


if __name__ == "__main__":
    unittest.main()
