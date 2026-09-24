#!/usr/bin/env python3
"""Local real-browser bridge tests using the pre-provisioned Playwright runtime."""

from __future__ import annotations

from contextlib import contextmanager
import hashlib
import http.server
import importlib.util
import os
from pathlib import Path
import re
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
def local_fixture_server(filename: str = "kgg_ui_lab_real_fixture.html"):
    handler = lambda *args, **kwargs: _QuietHandler(*args, directory=str(ROOT / "release-pipeline"), **kwargs)
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{httpd.server_port}/{filename}"
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

    def test_runtime_does_not_silently_activate_from_launcher_environment(self) -> None:
        old = os.environ.get("KGG_REAL_BROWSER")
        os.environ["KGG_REAL_BROWSER"] = "1"
        try:
            self.assertFalse(server.Runtime().browser_bootstrap.enabled)
        finally:
            if old is None:
                os.environ.pop("KGG_REAL_BROWSER", None)
            else:
                os.environ["KGG_REAL_BROWSER"] = old


class GenericBrowserCoreTests(unittest.TestCase):
    def test_non_kgg_fixture_uses_configured_core_policy(self) -> None:
        runtime = _runtime_available()
        if runtime is None:
            self.skipTest("pre-provisioned Playwright runtime is not available")
        node, module_path = runtime
        browser = server._load_real_browser_module()
        bootstrap = browser.BrowserBootstrap(
            enabled=True,
            node_command=node,
            playwright_module_path=module_path,
            policy=browser.BrowserPolicy.generic(),
        )
        steps = [
            {"operation": "read_state", "label": "generic-ready"},
            {"operation": "capture_screenshot", "label": "generic-baseline"},
            {"operation": "click", "label": "generic-toggle"},
            {"operation": "read_state", "label": "generic-toggled"},
            {"operation": "capture_screenshot", "label": "generic-evidence"},
        ]
        with local_fixture_server("generic_ui_lab_real_fixture.html") as url:
            result = browser.run_real_flow(
                url=url,
                viewport={"width": 960, "height": 720, "device_scale_factor": 1},
                steps=steps,
                run_id="generic-core-session-001",
                timeout_ms=120000,
                bootstrap=bootstrap,
            )
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["final_state"], "generic-toggled")
        self.assertEqual(result["steps"][2]["actual"], "action completed")
        self.assertTrue(all(item["ref"].startswith("memory://generic-ui-lab/") for item in result["artifacts"]))

    def test_generic_policy_rejects_public_origin_escape(self) -> None:
        browser = server._load_real_browser_module()
        policy = browser.BrowserPolicy.generic()
        with self.assertRaisesRegex(browser.RealBrowserError, "real_browser_url_invalid"):
            browser._safe_url("https://example.com/generic", policy)


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
            "record_screen",
            "observe_visual_state",
            "execute_visual_action",
            "compare_visual_reference",
            "run_flow",
        ])
        self.assertTrue(request_schema["additionalProperties"] is False)


def _session(url: str, *, session_id: str = "real-bridge-session-001", request_id: str = "real-bridge-request-001", flow_name: str = "pilot-180-reproduce", capabilities: list[str] | None = None, viewport: dict[str, object] | None = None, device_profile: str = "tab-s9") -> dict[str, object]:
    return {
        "schema": server.SESSION_SCHEMA,
        "session_id": session_id,
        "status": "created",
        "active_actor": "codex",
        "request_id": request_id,
        "lease": {"owner": "codex", "issued_at": "2026-01-01T00:00:00Z", "expires_at": "2030-01-01T00:00:00Z"},
        "runner": {"runner_id": "real-browser-runner-001", "version": "1.0.0", "browser_revision": "playwright-1.62.1", "capabilities": capabilities or ["browser", "quick_flows", "capture"]},
        "app": {"name": "admin", "url": url, "main_sha": MAIN_SHA, "preview_sha": "b" * 40},
        "device_profile": device_profile,
        "viewport": viewport or {"width": 960, "height": 720, "device_scale_factor": 1},
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


def _reference_from_observation(response: dict[str, object], *, reference_class: str = "explicit_artifact") -> dict[str, object]:
    structured = response["result"]["structuredContent"]
    observation = structured["observation"]
    image = next(item for item in response["result"]["content"] if item.get("type") == "image")
    return {
        "reference_class": reference_class,
        "reference_id": observation["artifact"]["id"],
        "reference_sha256": observation["artifact"]["sha256"],
        "content_type": "image/png",
        "image_data": image["data"],
        "viewport": {"width": 960, "height": 720, "device_scale_factor": 1},
        "threshold": {"max_changed_pixels": 0, "max_changed_ratio": 0, "pixel_delta": 0},
        "masks": [],
    }


def _real_runtime() -> server.Runtime:
    browser = server._load_real_browser_module()
    return server.Runtime(browser_bootstrap=browser.BrowserBootstrap.from_environment())


class KggRealBrowserBridgeTests(unittest.TestCase):
    def test_https_origin_and_path_allowlist_fail_closed(self) -> None:
        old = os.environ.get("KGG_REAL_BROWSER")
        os.environ["KGG_REAL_BROWSER"] = "1"
        try:
            active = _real_runtime()
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
                active = _real_runtime()
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
                active = _real_runtime()
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

    def test_visual_reference_identical_and_fixture_screenshot_pass(self) -> None:
        runtime = _runtime_available()
        if runtime is None:
            self.skipTest("pre-provisioned Playwright runtime is not available")
        node, module_path = runtime
        old = {key: os.environ.get(key) for key in ("KGG_REAL_BROWSER", "KGG_BROWSER_NODE", "KGG_PLAYWRIGHT_NODE_PATH")}
        os.environ.update({"KGG_REAL_BROWSER": "1", "KGG_BROWSER_NODE": node, "KGG_PLAYWRIGHT_NODE_PATH": module_path})
        try:
            with local_fixture_server() as base_url:
                active = _real_runtime()
                session_id = "reference-identical-session"
                started = server.handle(active, {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "start_ui_session", "arguments": {"session": _session(f"{base_url}?flow=pilot", session_id=session_id, request_id="reference-identical-start", capabilities=["browser", "capture", "visual_loop"])}}})
                self.assertFalse(started["result"].get("isError", False), started)
                observed = server.handle(active, {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "observe_visual_state", "arguments": {"request": _visual_request(session_id=session_id, request_id="reference-identical-observe", operation="observe_visual_state")}}})
                self.assertFalse(observed["result"].get("isError", False), observed)
                before = observed["result"]["structuredContent"]["observation"]
                explicit = _reference_from_observation(observed)
                compared = server.handle(active, {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "compare_visual_reference", "arguments": {"request": _visual_request(session_id=session_id, request_id="reference-identical-compare", operation="compare_visual_reference"), "reference": explicit}}})
                self.assertFalse(compared["result"].get("isError", False), compared)
                result = compared["result"]["structuredContent"]["result"]
                self.assertEqual(result["status"], "PASS")
                self.assertEqual(result["comparison"]["visual"]["changed_pixels"], 0)
                self.assertEqual(result["comparison"]["difference_classes"], [])
                self.assertEqual(len(compared["result"]["content"]), 2)
                fixture_reference = dict(explicit)
                fixture_reference.pop("image_data")
                fixture_reference["reference_class"] = "fixture_screenshot"
                fixture_reference["observation_id"] = before["id"]
                fixture_compared = server.handle(active, {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "compare_visual_reference", "arguments": {"request": _visual_request(session_id=session_id, request_id="reference-fixture-compare", operation="compare_visual_reference"), "reference": fixture_reference}}})
                self.assertFalse(fixture_compared["result"].get("isError", False), fixture_compared)
                self.assertEqual(fixture_compared["result"]["structuredContent"]["result"]["status"], "PASS")
        finally:
            for key, value in old.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def test_visual_reference_changed_ui_fails_and_explicit_mask_is_reported(self) -> None:
        runtime = _runtime_available()
        if runtime is None:
            self.skipTest("pre-provisioned Playwright runtime is not available")
        node, module_path = runtime
        old = {key: os.environ.get(key) for key in ("KGG_REAL_BROWSER", "KGG_BROWSER_NODE", "KGG_PLAYWRIGHT_NODE_PATH")}
        os.environ.update({"KGG_REAL_BROWSER": "1", "KGG_BROWSER_NODE": node, "KGG_PLAYWRIGHT_NODE_PATH": module_path})
        try:
            with local_fixture_server() as base_url:
                reference_runtime = _real_runtime()
                reference_session = "reference-golden-session"
                server.handle(reference_runtime, {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "start_ui_session", "arguments": {"session": _session(f"{base_url}?flow=pilot", session_id=reference_session, request_id="reference-golden-start", capabilities=["browser", "capture", "visual_loop"])}}})
                reference_observed = server.handle(reference_runtime, {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "observe_visual_state", "arguments": {"request": _visual_request(session_id=reference_session, request_id="reference-golden-observe", operation="observe_visual_state")}}})
                self.assertFalse(reference_observed["result"].get("isError", False), reference_observed)
                golden = _reference_from_observation(reference_observed, reference_class="approved_golden")
                golden["approval_id"] = "approved:synthetic-fixture-v1"
                current_runtime = _real_runtime()
                current_session = "reference-diff-session"
                started = server.handle(current_runtime, {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "start_ui_session", "arguments": {"session": _session(f"{base_url}?flow=pilot&drift=1", session_id=current_session, request_id="reference-diff-start", capabilities=["browser", "capture", "visual_loop"])}}})
                self.assertFalse(started["result"].get("isError", False), started)
                observed = server.handle(current_runtime, {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "observe_visual_state", "arguments": {"request": _visual_request(session_id=current_session, request_id="reference-diff-observe", operation="observe_visual_state")}}})
                self.assertFalse(observed["result"].get("isError", False), observed)
                compared = server.handle(current_runtime, {"jsonrpc": "2.0", "id": 5, "method": "tools/call", "params": {"name": "compare_visual_reference", "arguments": {"request": _visual_request(session_id=current_session, request_id="reference-diff-compare", operation="compare_visual_reference"), "reference": golden}}})
                self.assertFalse(compared["result"].get("isError", False), compared)
                result = compared["result"]["structuredContent"]["result"]
                self.assertEqual(result["status"], "FAIL")
                self.assertIn("VISUAL_DIFFERENCE", result["comparison"]["difference_classes"])
                self.assertGreater(result["comparison"]["visual"]["changed_pixels"], 0)
                masked = dict(golden)
                masked["masks"] = [{"x": 0, "y": 0, "width": 960, "height": 720}]
                masked_result = server.handle(current_runtime, {"jsonrpc": "2.0", "id": 6, "method": "tools/call", "params": {"name": "compare_visual_reference", "arguments": {"request": _visual_request(session_id=current_session, request_id="reference-mask-compare", operation="compare_visual_reference"), "reference": masked}}})
                self.assertFalse(masked_result["result"].get("isError", False), masked_result)
                masked_comparison = masked_result["result"]["structuredContent"]["result"]["comparison"]
                self.assertEqual(masked_result["result"]["structuredContent"]["result"]["status"], "PASS")
                self.assertIn("EXPECTED_DYNAMIC_DIFFERENCE", masked_comparison["difference_classes"])
        finally:
            for key, value in old.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def test_visual_reference_rejects_hash_mismatch_and_viewport_mismatch(self) -> None:
        runtime = _runtime_available()
        if runtime is None:
            self.skipTest("pre-provisioned Playwright runtime is not available")
        node, module_path = runtime
        old = {key: os.environ.get(key) for key in ("KGG_REAL_BROWSER", "KGG_BROWSER_NODE", "KGG_PLAYWRIGHT_NODE_PATH")}
        os.environ.update({"KGG_REAL_BROWSER": "1", "KGG_BROWSER_NODE": node, "KGG_PLAYWRIGHT_NODE_PATH": module_path})
        try:
            with local_fixture_server() as base_url:
                active = _real_runtime()
                session_id = "reference-negative-session"
                server.handle(active, {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "start_ui_session", "arguments": {"session": _session(f"{base_url}?flow=pilot", session_id=session_id, request_id="reference-negative-start", capabilities=["browser", "capture", "visual_loop"])}}})
                observed = server.handle(active, {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "observe_visual_state", "arguments": {"request": _visual_request(session_id=session_id, request_id="reference-negative-observe", operation="observe_visual_state")}}})
                self.assertFalse(observed["result"].get("isError", False), observed)
                invalid_hash = _reference_from_observation(observed)
                invalid_hash["reference_sha256"] = "0" * 64
                rejected_hash = server.handle(active, {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "compare_visual_reference", "arguments": {"request": _visual_request(session_id=session_id, request_id="reference-negative-hash", operation="compare_visual_reference"), "reference": invalid_hash}}})
                self.assertTrue(rejected_hash["result"]["isError"])
                self.assertIn("reference_hash_mismatch", rejected_hash["result"]["content"][0]["text"])
                invalid_viewport = _reference_from_observation(observed)
                invalid_viewport["viewport"] = {"width": 640, "height": 480, "device_scale_factor": 1}
                rejected_viewport = server.handle(active, {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "compare_visual_reference", "arguments": {"request": _visual_request(session_id=session_id, request_id="reference-negative-viewport", operation="compare_visual_reference"), "reference": invalid_viewport}}})
                self.assertTrue(rejected_viewport["result"]["isError"])
                self.assertIn("reference_viewport_mismatch", rejected_viewport["result"]["content"][0]["text"])
        finally:
            for key, value in old.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def test_persistent_swipe_supports_horizontal_desktop_and_vertical_mobile(self) -> None:
        runtime = _runtime_available()
        if runtime is None:
            self.skipTest("pre-provisioned Playwright runtime is not available")
        node, module_path = runtime
        old = {key: os.environ.get(key) for key in ("KGG_REAL_BROWSER", "KGG_BROWSER_NODE", "KGG_PLAYWRIGHT_NODE_PATH")}
        os.environ.update({"KGG_REAL_BROWSER": "1", "KGG_BROWSER_NODE": node, "KGG_PLAYWRIGHT_NODE_PATH": module_path})
        try:
            cases = (
                ("desktop-horizontal", {"width": 960, "height": 720, "device_scale_factor": 1}, "tab-s9", {"x": 120, "y": 170}, {"x": 600, "y": 170}),
                ("mobile-vertical", {"width": 360, "height": 640, "device_scale_factor": 1}, "oppo-find-x9", {"x": 180, "y": 200}, {"x": 180, "y": 350}),
            )
            for name, viewport, device_profile, start, end in cases:
                with local_fixture_server() as base_url:
                    active = _real_runtime()
                    session_id = f"swipe-{name}-session"
                    started = server.handle(active, {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "start_ui_session", "arguments": {"session": _session(f"{base_url}?flow=pilot", session_id=session_id, request_id=f"{session_id}-start", capabilities=["browser", "capture", "visual_loop"], viewport=viewport, device_profile=device_profile)}}})
                    self.assertFalse(started["result"].get("isError", False), started)
                    observed = server.handle(active, {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "observe_visual_state", "arguments": {"request": _visual_request(session_id=session_id, request_id=f"{session_id}-observe", operation="observe_visual_state")}}})
                    self.assertFalse(observed["result"].get("isError", False), observed)
                    before = observed["result"]["structuredContent"]["observation"]
                    decision = {"operation": "swipe", "label": "swipe-surface", "start": start, "end": end, "duration_ms": 120, "expected_state_after": "swipe-complete", "observation_id": before["id"]}
                    acted = server.handle(active, {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "execute_visual_action", "arguments": {"request": _visual_request(session_id=session_id, request_id=f"{session_id}-act", operation="execute_visual_action"), "decision": decision}}})
                    self.assertFalse(acted["result"].get("isError", False), acted)
                    structured = acted["result"]["structuredContent"]
                    self.assertEqual(structured["result"]["status"], "PASS")
                    self.assertEqual(structured["result"]["state_before"], "pilot-area-ready")
                    self.assertEqual(structured["result"]["state_after"], "swipe-complete")
                    self.assertEqual(structured["evidence"]["decision"]["start"], start)
                    self.assertEqual(structured["evidence"]["decision"]["end"], end)
                    self.assertEqual(len(structured["result"]["artifacts"]), 2)
                    self.assertEqual(len(active.visual_sessions), 0)
        finally:
            for key, value in old.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def test_persistent_swipe_rejects_bounds_and_stale_observations_without_side_effect(self) -> None:
        runtime = _runtime_available()
        if runtime is None:
            self.skipTest("pre-provisioned Playwright runtime is not available")
        node, module_path = runtime
        old = {key: os.environ.get(key) for key in ("KGG_REAL_BROWSER", "KGG_BROWSER_NODE", "KGG_PLAYWRIGHT_NODE_PATH")}
        os.environ.update({"KGG_REAL_BROWSER": "1", "KGG_BROWSER_NODE": node, "KGG_PLAYWRIGHT_NODE_PATH": module_path})
        try:
            with local_fixture_server() as base_url:
                active = _real_runtime()
                session_id = "swipe-negative-session"
                started = server.handle(active, {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "start_ui_session", "arguments": {"session": _session(f"{base_url}?flow=pilot", session_id=session_id, request_id="swipe-negative-start", capabilities=["browser", "capture", "visual_loop"])}}})
                self.assertFalse(started["result"].get("isError", False), started)
                observed = server.handle(active, {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "observe_visual_state", "arguments": {"request": _visual_request(session_id=session_id, request_id="swipe-negative-observe", operation="observe_visual_state")}}})
                self.assertFalse(observed["result"].get("isError", False), observed)
                before = observed["result"]["structuredContent"]["observation"]
                invalid = server.handle(active, {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "execute_visual_action", "arguments": {"request": _visual_request(session_id=session_id, request_id="swipe-negative-bounds", operation="execute_visual_action"), "decision": {"operation": "swipe", "label": "swipe-surface", "start": {"x": 120, "y": 170}, "end": {"x": 960, "y": 170}, "duration_ms": 120, "expected_state_after": "swipe-complete", "observation_id": before["id"]}}}})
                self.assertTrue(invalid["result"]["isError"])
                self.assertIn("swipe_bounds_invalid", invalid["result"]["content"][0]["text"])
                self.assertEqual(len(active.visual_sessions), 1)
                fresh = server.handle(active, {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "observe_visual_state", "arguments": {"request": _visual_request(session_id=session_id, request_id="swipe-negative-reobserve", operation="observe_visual_state")}}})
                self.assertFalse(fresh["result"].get("isError", False), fresh)
                self.assertEqual(fresh["result"]["structuredContent"]["observation"]["state"], "pilot-area-ready")
                stale = server.handle(active, {"jsonrpc": "2.0", "id": 5, "method": "tools/call", "params": {"name": "execute_visual_action", "arguments": {"request": _visual_request(session_id=session_id, request_id="swipe-negative-stale", operation="execute_visual_action"), "decision": {"operation": "swipe", "label": "swipe-surface", "start": {"x": 120, "y": 170}, "end": {"x": 600, "y": 170}, "duration_ms": 120, "expected_state_after": "swipe-complete", "observation_id": "0" * 64}}}})
                self.assertTrue(stale["result"]["isError"])
                self.assertIn("visual_observation_stale", stale["result"]["content"][0]["text"])
                self.assertEqual(len(active.visual_sessions), 1)
        finally:
            for key, value in old.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def test_persistent_swipe_rejects_unchanged_state_and_modal_overlay(self) -> None:
        runtime = _runtime_available()
        if runtime is None:
            self.skipTest("pre-provisioned Playwright runtime is not available")
        node, module_path = runtime
        old = {key: os.environ.get(key) for key in ("KGG_REAL_BROWSER", "KGG_BROWSER_NODE", "KGG_PLAYWRIGHT_NODE_PATH")}
        os.environ.update({"KGG_REAL_BROWSER": "1", "KGG_BROWSER_NODE": node, "KGG_PLAYWRIGHT_NODE_PATH": module_path})
        try:
            for suffix, expected_error, start, end in (
                ("unchanged", "visual_state_unchanged", {"x": 180, "y": 150}, {"x": 200, "y": 160}),
                ("overlay", "visual_expected_state_not_reached", {"x": 180, "y": 150}, {"x": 600, "y": 150}),
            ):
                with local_fixture_server() as base_url:
                    active = _real_runtime()
                    session_id = f"swipe-{suffix}-session"
                    query = "flow=pilot" if suffix == "unchanged" else "flow=pilot&overlay=1"
                    started = server.handle(active, {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "start_ui_session", "arguments": {"session": _session(f"{base_url}?{query}", session_id=session_id, request_id=f"{session_id}-start", capabilities=["browser", "capture", "visual_loop"])}}})
                    self.assertFalse(started["result"].get("isError", False), started)
                    observed = server.handle(active, {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "observe_visual_state", "arguments": {"request": _visual_request(session_id=session_id, request_id=f"{session_id}-observe", operation="observe_visual_state")}}})
                    self.assertFalse(observed["result"].get("isError", False), observed)
                    before = observed["result"]["structuredContent"]["observation"]
                    expected = "pilot-area-ready" if suffix == "unchanged" else "swipe-complete"
                    decision = {"operation": "swipe", "label": "swipe-surface", "start": start, "end": end, "duration_ms": 120, "expected_state_after": expected, "observation_id": before["id"]}
                    rejected = server.handle(active, {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "execute_visual_action", "arguments": {"request": _visual_request(session_id=session_id, request_id=f"{session_id}-act", operation="execute_visual_action"), "decision": decision}}})
                    self.assertTrue(rejected["result"]["isError"], rejected)
                    self.assertIn(expected_error, rejected["result"]["content"][0]["text"])
        finally:
            for key, value in old.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def test_visual_loop_uses_bounded_language_state_without_data_marker(self) -> None:
        runtime = _runtime_available()
        if runtime is None:
            self.skipTest("pre-provisioned Playwright runtime is not available")
        node, module_path = runtime
        old = {key: os.environ.get(key) for key in ("KGG_REAL_BROWSER", "KGG_BROWSER_NODE", "KGG_PLAYWRIGHT_NODE_PATH")}
        os.environ.update({"KGG_REAL_BROWSER": "1", "KGG_BROWSER_NODE": node, "KGG_PLAYWRIGHT_NODE_PATH": module_path})
        try:
            with local_fixture_server() as base_url:
                active = _real_runtime()
                session_id = "visual-loop-language-001"
                started = server.handle(active, {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "start_ui_session", "arguments": {"session": _session(f"{base_url}?fallback=language", session_id=session_id, request_id="visual-loop-language-start", capabilities=["browser", "capture", "visual_loop"])}}})
                self.assertFalse(started["result"].get("isError", False), started)
                observed = server.handle(active, {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "observe_visual_state", "arguments": {"request": _visual_request(session_id=session_id, request_id="visual-loop-language-observe", operation="observe_visual_state")}}})
                self.assertFalse(observed["result"].get("isError", False), observed)
                before = observed["result"]["structuredContent"]["observation"]
                self.assertEqual(before["state"], "lang-de")
                decision = {"operation": "click", "label": "language-toggle", "expected_state_after": "lang-en", "observation_id": before["id"]}
                acted = server.handle(active, {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "execute_visual_action", "arguments": {"request": _visual_request(session_id=session_id, request_id="visual-loop-language-act", operation="execute_visual_action"), "decision": decision}}})
                self.assertFalse(acted["result"].get("isError", False), acted)
                result = acted["result"]["structuredContent"]["result"]
                self.assertEqual(result["status"], "PASS")
                self.assertEqual(result["state_before"], "lang-de")
                self.assertEqual(result["state_after"], "lang-en")
                self.assertEqual(len(result["artifacts"]), 2)
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
                active = _real_runtime()
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
                active = _real_runtime()
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
            active = _real_runtime()
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
                        active = _real_runtime()
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
            active = _real_runtime()
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

    def test_screen_recording_returns_traceable_keyframes_for_synthetic_motion(self) -> None:
        runtime = _runtime_available()
        if runtime is None:
            self.skipTest("pre-provisioned Playwright runtime is not available")
        node, module_path = runtime
        old = {key: os.environ.get(key) for key in ("KGG_REAL_BROWSER", "KGG_BROWSER_NODE", "KGG_PLAYWRIGHT_NODE_PATH")}
        os.environ.update({"KGG_REAL_BROWSER": "1", "KGG_BROWSER_NODE": node, "KGG_PLAYWRIGHT_NODE_PATH": module_path})
        try:
            with local_fixture_server() as base_url:
                active = _real_runtime()
                session_id = "recording-motion-session"
                request_id = "recording-motion-request"
                url = f"{base_url}?flow=pilot&motion=1"
                started = server.handle(active, {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "start_ui_session", "arguments": {"session": _session(url, session_id=session_id, request_id=request_id, capabilities=["browser", "capture", "screen_recording"])}}})
                self.assertFalse(started["result"].get("isError", False), started)
                response = server.handle(active, {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "record_screen", "arguments": {"request": _request(session_id=session_id, request_id=request_id, operation="record_screen"), "duration_ms": 350, "frame_interval_ms": 100}}})
                self.assertFalse(response["result"].get("isError", False), response)
                structured = response["result"]["structuredContent"]
                result = structured["result"]
                self.assertEqual(result["status"], "PASS")
                self.assertEqual(result["recording_mode"], "KEYFRAME_FALLBACK")
                self.assertGreaterEqual(len(result["frames"]), 2)
                self.assertTrue(all(frame["timestamp_ms"] >= 0 for frame in result["frames"]))
                self.assertGreaterEqual(len({frame["state"] for frame in result["frames"]}), 2)
                for frame in result["frames"]:
                    artifact = frame["artifact"]
                    self.assertEqual(artifact["content_type"], "image/png")
                    self.assertRegex(artifact["sha256"], r"^[0-9a-f]{64}$")
                    self.assertGreater(artifact["size_bytes"], 0)
                    self.assertEqual(artifact["retention"], "session-bound")
                evidence = structured["evidence"]
                self.assertEqual(evidence["session_id"], session_id)
                self.assertEqual(evidence["run_id"], f"{session_id}-{request_id}-recording")
                self.assertEqual(evidence["recording_mode"], "KEYFRAME_FALLBACK")
                self.assertFalse(evidence["timeout"]["timed_out"])
                self.assertLessEqual(evidence["actual_duration_ms"], 350)
                self.assertEqual(active.visual_sessions, {})
                self.assertNotIn("Recording erfolgreich", response["result"]["content"][0]["text"])
        finally:
            for key, value in old.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def test_screen_recording_unchanged_replay_preserves_bounded_keyframe_contract(self) -> None:
        runtime = _runtime_available()
        if runtime is None:
            self.skipTest("pre-provisioned Playwright runtime is not available")
        node, module_path = runtime
        old = {key: os.environ.get(key) for key in ("KGG_REAL_BROWSER", "KGG_BROWSER_NODE", "KGG_PLAYWRIGHT_NODE_PATH")}
        os.environ.update({"KGG_REAL_BROWSER": "1", "KGG_BROWSER_NODE": node, "KGG_PLAYWRIGHT_NODE_PATH": module_path})
        try:
            results: list[dict[str, object]] = []
            for attempt in ("original", "replay"):
                with local_fixture_server() as base_url:
                    active = _real_runtime()
                    session_id = f"recording-replay-{attempt}-session"
                    request_id = f"recording-replay-{attempt}-request"
                    started = server.handle(active, {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "start_ui_session", "arguments": {"session": _session(f"{base_url}?flow=pilot&motion=1", session_id=session_id, request_id=request_id, capabilities=["browser", "capture", "screen_recording"])}}})
                    self.assertFalse(started["result"].get("isError", False), started)
                    response = server.handle(active, {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "record_screen", "arguments": {"request": _request(session_id=session_id, request_id=request_id, operation="record_screen"), "duration_ms": 350, "frame_interval_ms": 100}}})
                    self.assertFalse(response["result"].get("isError", False), response)
                    structured = response["result"]["structuredContent"]
                    frames = structured["result"]["frames"]
                    results.append({
                        "status": structured["result"]["status"],
                        "mode": structured["result"]["recording_mode"],
                        "count": len(frames),
                        "states": [frame["state"] for frame in frames],
                        "hashes": [frame["artifact"]["sha256"] for frame in frames],
                        "content_types": [frame["artifact"]["content_type"] for frame in frames],
                        "retentions": [frame["artifact"]["retention"] for frame in frames],
                    })
                    self.assertEqual(active.visual_sessions, {})
            self.assertEqual([item["status"] for item in results], ["PASS", "PASS"])
            self.assertEqual([item["mode"] for item in results], ["KEYFRAME_FALLBACK", "KEYFRAME_FALLBACK"])
            self.assertTrue(all(2 <= result["count"] <= 5 for result in results))
            self.assertTrue(all(state == "pilot-area-ready" or state.startswith("motion-") for result in results for state in result["states"]))
            self.assertTrue(all(re.fullmatch(r"[0-9a-f]{64}", digest) for result in results for digest in result["hashes"]))
            self.assertTrue(all(result["content_types"] == ["image/png"] * result["count"] for result in results))
            self.assertTrue(all(result["retentions"] == ["session-bound"] * result["count"] for result in results))
        finally:
            for key, value in old.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value

    def test_screen_recording_rejects_missing_capability_and_invalid_bounds_without_side_effect(self) -> None:
        active = server.Runtime()
        session_id = "recording-negative-session"
        request_id = "recording-negative-request"
        started = server.handle(active, {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "start_ui_session", "arguments": {"session": _session("https://preview.example.test/admin", session_id=session_id, request_id=request_id, capabilities=["browser", "capture"])}}})
        self.assertFalse(started["result"].get("isError", False), started)
        missing_capability = server.handle(active, {"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": {"name": "record_screen", "arguments": {"request": _request(session_id=session_id, request_id=request_id, operation="record_screen"), "duration_ms": 350, "frame_interval_ms": 100}}})
        self.assertTrue(missing_capability["result"]["isError"])
        self.assertIn("capability_missing", missing_capability["result"]["content"][0]["text"])
        self.assertEqual(active.visual_sessions, {})

        bounded_session_id = "recording-bounds-session"
        bounded_request_id = "recording-bounds-request"
        bounded = _session("https://preview.example.test/admin", session_id=bounded_session_id, request_id=bounded_request_id, capabilities=["browser", "capture", "screen_recording"])
        started_bounded = server.handle(active, {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "start_ui_session", "arguments": {"session": bounded}}})
        self.assertFalse(started_bounded["result"].get("isError", False), started_bounded)
        invalid_duration = server.handle(active, {"jsonrpc": "2.0", "id": 4, "method": "tools/call", "params": {"name": "record_screen", "arguments": {"request": _request(session_id=bounded_session_id, request_id=bounded_request_id, operation="record_screen"), "duration_ms": 10001, "frame_interval_ms": 100}}})
        self.assertTrue(invalid_duration["result"]["isError"])
        self.assertIn("recording_duration_invalid", invalid_duration["result"]["content"][0]["text"])
        self.assertEqual(active.visual_sessions, {})
        unavailable = server.handle(active, {"jsonrpc": "2.0", "id": 5, "method": "tools/call", "params": {"name": "record_screen", "arguments": {"request": _request(session_id=bounded_session_id, request_id=bounded_request_id, operation="record_screen"), "duration_ms": 350, "frame_interval_ms": 100}}})
        self.assertTrue(unavailable["result"]["isError"])
        self.assertIn("real_browser_not_enabled", unavailable["result"]["content"][0]["text"])
        self.assertEqual(active.visual_sessions, {})


if __name__ == "__main__":
    unittest.main()
