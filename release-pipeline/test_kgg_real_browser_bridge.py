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


def _session(url: str) -> dict[str, object]:
    return {
        "schema": server.SESSION_SCHEMA,
        "session_id": "real-bridge-session-001",
        "status": "created",
        "active_actor": "codex",
        "request_id": "real-bridge-request-001",
        "lease": {"owner": "codex", "issued_at": "2026-01-01T00:00:00Z", "expires_at": "2030-01-01T00:00:00Z"},
        "runner": {"runner_id": "real-browser-runner-001", "version": "1.0.0", "browser_revision": "playwright-1.62.1", "capabilities": ["browser", "quick_flows", "capture"]},
        "app": {"name": "admin", "url": url, "main_sha": MAIN_SHA, "preview_sha": "b" * 40},
        "device_profile": "tab-s9",
        "viewport": {"width": 960, "height": 720, "device_scale_factor": 1},
        "quick_flow": {"name": "pilot-180-reproduce", "version": "1.0.0"},
        "timeout": {"timeout_ms": 120000, "cleanup_on_cancel": True},
        "artifacts": [],
    }


def _request() -> dict[str, object]:
    return {
        "schema": server.REQUEST_SCHEMA,
        "request_id": "real-bridge-request-001",
        "session_id": "real-bridge-session-001",
        "actor": "codex",
        "operation": "run_quick_flow",
        "main_sha": MAIN_SHA,
        "payload_sha256": hashlib.sha256(b"real-browser-flow").hexdigest(),
    }


class KggRealBrowserBridgeTests(unittest.TestCase):
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
