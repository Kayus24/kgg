"""Width sweep acceptance: real captures, bounded failures, no visual-parity claim."""
import base64
import hashlib
import struct
import unittest
import zlib
from unittest.mock import patch

from test_kgg_real_browser_bridge import server, _runtime_available, _real_runtime, _session, local_fixture_server


VIEWPORTS = [
    {"width": 390, "height": 844, "device_scale_factor": 1},
    {"width": 820, "height": 1180, "device_scale_factor": 1},
    {"width": 1440, "height": 900, "device_scale_factor": 1},
]


class WidthSweepTests(unittest.TestCase):
    def start(self, runtime, url="https://example.invalid/synthetic", capabilities=None):
        session = _session(url, session_id="width-sweep-session", capabilities=capabilities or ["browser", "capture", "width_sweep"], device_profile="custom")
        runtime.start(session)
        return session["session_id"]

    def test_no_real_opt_in_stays_preview_only(self):
        runtime = server.Runtime()
        sid = self.start(runtime, "https://kayus24.github.io/kgg/kgg-update/index.html")
        result = runtime.sweep(sid, "codex", VIEWPORTS)
        self.assertEqual(result["status"], "PREVIEW_ONLY")
        self.assertEqual(result.get("verification_scope"), "capture_only")
        self.assertEqual(result["visual_comparison"], "NOT_RUN")
        self.assertFalse(runtime.evidence.get(sid))

    def test_invalid_viewports_actor_and_lease_never_launch_browser(self):
        browser = server._load_real_browser_module()
        runtime = server.Runtime()
        sid = self.start(runtime, "https://kayus24.github.io/kgg/kgg-update/index.html")
        invalid = [[], VIEWPORTS * 4, [True], [{**VIEWPORTS[0], "width": True}], [{**VIEWPORTS[0], "height": 1}], [{**VIEWPORTS[0], "device_scale_factor": float("nan")}]]
        with patch.object(server, "_load_real_browser_module", return_value=browser), patch.object(browser, "run_real_flow") as launch:
            for viewports in invalid:
                with self.subTest(viewports=viewports), self.assertRaises(server.ServerError):
                    runtime.sweep(sid, "codex", viewports)
            with self.assertRaisesRegex(server.ServerError, "mcp_auth_denied"):
                runtime.sweep(sid, "custom_gpt", VIEWPORTS)
            runtime.sessions[sid]["lease"]["expires_at"] = "2020-01-01T00:00:00Z"
            with self.assertRaisesRegex(server.ServerError, "lease_expired"):
                runtime.sweep(sid, "codex", VIEWPORTS)
        launch.assert_not_called()

    def test_bridge_failure_marks_following_widths_not_run(self):
        browser = server._load_real_browser_module()
        runtime = server.Runtime(browser_bootstrap=browser.BrowserBootstrap(enabled=True, policy=browser.BrowserPolicy.kgg()))
        sid = self.start(runtime, "http://127.0.0.1:8765/kgg_ui_lab_real_fixture.html")
        with patch.object(server, "_load_real_browser_module", return_value=browser), patch.object(browser, "run_real_flow", side_effect=browser.RealBrowserError("real_browser_timeout")) as launch:
            result = runtime.sweep(sid, "codex", VIEWPORTS)
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual([item["status"] for item in result["results"]], ["FAIL", "NOT_RUN", "NOT_RUN"])
        self.assertEqual(result["error_class"], "real_browser_timeout")
        self.assertEqual(result["evidence"]["status"], "FAIL")
        self.assertEqual(launch.call_count, 1)
        self.assertLessEqual(launch.call_args.kwargs["wait_budget_seconds"], 30)

    def test_claimed_pass_without_screenshot_fails_closed(self):
        browser = server._load_real_browser_module()
        runtime = server.Runtime(browser_bootstrap=browser.BrowserBootstrap(enabled=True, policy=browser.BrowserPolicy.kgg()))
        sid = self.start(runtime, "http://127.0.0.1:8765/kgg_ui_lab_real_fixture.html")
        response = {"status": "PASS", "error_class": "", "steps": [], "artifacts": [], "images": [], "final_state": "admin-ready", "runtime_ms": 1}
        with patch.object(server, "_load_real_browser_module", return_value=browser), patch.object(browser, "run_real_flow", return_value=response):
            result = runtime.sweep(sid, "codex", VIEWPORTS)
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["error_class"], "width_sweep_screenshot_missing")

    def test_wrong_screenshot_dimensions_cannot_pass_as_requested_viewport(self):
        browser = server._load_real_browser_module()
        runtime = server.Runtime(browser_bootstrap=browser.BrowserBootstrap(enabled=True, policy=browser.BrowserPolicy.kgg()))
        sid = self.start(runtime, "http://127.0.0.1:8765/kgg_ui_lab_real_fixture.html")
        def chunk(kind, data):
            return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)
        raw = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(b"\0\0\0\0")) + chunk(b"IEND", b"")
        digest = hashlib.sha256(raw).hexdigest()
        artifact = {"id": "wrong-size-shot", "kind": "screenshot", "ref": "memory://wrong-size-shot", "sha256": digest}
        response = {"status": "PASS", "error_class": "", "steps": [], "artifacts": [artifact], "images": [{"data_base64": base64.b64encode(raw).decode(), "mime_type": "image/png", "sha256": digest}], "final_state": "admin-ready", "runtime_ms": 1}
        with patch.object(server, "_load_real_browser_module", return_value=browser), patch.object(browser, "run_real_flow", return_value=response):
            result = runtime.sweep(sid, "codex", VIEWPORTS)
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["error_class"], "width_sweep_viewport_mismatch")
        self.assertEqual([item["status"] for item in result["results"]], ["FAIL", "NOT_RUN", "NOT_RUN"])

    def test_shared_deadline_does_not_start_another_browser_after_expiry(self):
        browser = server._load_real_browser_module()
        runtime = server.Runtime(browser_bootstrap=browser.BrowserBootstrap(enabled=True, policy=browser.BrowserPolicy.kgg()))
        sid = self.start(runtime, "http://127.0.0.1:8765/kgg_ui_lab_real_fixture.html")
        with patch.object(server, "_load_real_browser_module", return_value=browser), patch.object(browser, "run_real_flow") as launch, patch.object(server.time, "monotonic", side_effect=[0, 31, 31]):
            result = runtime.sweep(sid, "codex", VIEWPORTS)
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["error_class"], "width_sweep_timeout")
        launch.assert_not_called()

    def test_real_phone_tablet_desktop_captures_are_bound_to_requested_sizes(self):
        available = _runtime_available()
        self.assertIsNotNone(available, "Width sweep acceptance requires provisioned Playwright")
        node, modules = available
        with patch.dict("os.environ", {"KGG_REAL_BROWSER": "1", "KGG_BROWSER_NODE": node, "KGG_PLAYWRIGHT_NODE_PATH": modules}), local_fixture_server() as url:
            runtime = _real_runtime()
            sid = self.start(runtime, url)
            response = server.handle(runtime, {"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": "run_width_sweep", "arguments": {"session_id": sid, "actor": "codex", "viewports": VIEWPORTS}}})["result"]
        self.assertFalse(response.get("isError"), response)
        result = response["structuredContent"]
        self.assertEqual(result["status"], "PASS", result)
        self.assertEqual(result["verification_scope"], "capture_only")
        self.assertEqual(result["visual_comparison"], "NOT_RUN")
        self.assertEqual(result["evidence"]["surface"], "real_browser")
        self.assertEqual(result["evidence"]["main_sha"], "a" * 40)
        self.assertEqual([item["status"] for item in result["results"]], ["PASS"] * 3)
        self.assertEqual([item["state"] for item in result["results"]], ["admin-ready"] * 3)
        images = [item for item in response["content"] if item.get("type") == "image"]
        self.assertEqual(len(images), 3)
        for viewport, item, image in zip(VIEWPORTS, result["results"], images):
            raw = base64.b64decode(image["data"])
            self.assertEqual(struct.unpack(">II", raw[16:24]), (viewport["width"], viewport["height"]))
            self.assertEqual(item["artifact"]["sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(len({item["artifact"]["id"] for item in result["results"]}), 3)
        self.assertEqual(runtime.sessions[sid]["viewport"], {"width": 960, "height": 720, "device_scale_factor": 1})

    def test_real_fractional_dpr_uses_nearest_positive_device_pixel(self):
        available = _runtime_available()
        self.assertIsNotNone(available, "Width sweep acceptance requires provisioned Playwright")
        node, modules = available
        viewports = [
            {"width": 391, "height": 721, "device_scale_factor": 1.25},
            {"width": 390, "height": 722, "device_scale_factor": 1.25},
        ]
        with patch.dict("os.environ", {"KGG_REAL_BROWSER": "1", "KGG_BROWSER_NODE": node, "KGG_PLAYWRIGHT_NODE_PATH": modules}), local_fixture_server() as url:
            runtime = _real_runtime()
            sid = self.start(runtime, url)
            result = runtime.sweep(sid, "codex", viewports)
        self.assertEqual(result["status"], "PASS", result)
        actual = [struct.unpack(">II", base64.b64decode(image["data_base64"])[16:24]) for image in result["_images"]]
        self.assertEqual(actual, [(489, 901), (488, 903)])
        self.assertEqual([item["screenshot_size"] for item in result["results"]], [{"width": width, "height": height} for width, height in actual])


if __name__ == "__main__":
    unittest.main()
