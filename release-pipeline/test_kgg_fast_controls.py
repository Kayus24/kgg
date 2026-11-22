"""Fail-closed, synthetic control discovery in the existing UI-Lab visual loop."""
import unittest
from test_kgg_real_browser_bridge import server, _runtime_available, local_fixture_server, _session, _visual_request


def browser_for(url, run_id):
    node, module_path = _runtime_available()
    module = server._load_real_browser_module()
    return module.PersistentRealBrowser(
        url=url, viewport={"width": 390, "height": 844, "device_scale_factor": 1},
        run_id=run_id, timeout_ms=8000,
        bootstrap=module.BrowserBootstrap(
            enabled=True, node_command=node, playwright_module_path=module_path,
        ),
    )


class FastControlDiscoveryTests(unittest.TestCase):
    def setUp(self):
        if _runtime_available() is None:
            self.skipTest("pre-provisioned Playwright unavailable")

    def test_bounded_controls_allow_label_only_language_action(self):
        with local_fixture_server("kgg_ui_lab_control_targets_fixture.html") as url:
            browser = browser_for(url, "fast-controls-positive")
            try:
                before = browser.observe()
                self.assertEqual(before["state"], "lang-de")
                self.assertEqual(before["controls"], [
                    {"role": "button", "label": "language-toggle"},
                    {"role": "button", "label": "pilot-action"},
                ])
                self.assertNotIn("Synthetic plan text", str(before["controls"]))
                action = browser.act({"operation": "click", "label": "language-toggle"})
                self.assertEqual(action["action"]["before_state"], "lang-de")
                after = browser.observe()
                self.assertEqual(after["state"], "lang-en")
                self.assertNotEqual(before["artifacts"][0]["sha256"], after["artifacts"][0]["sha256"])
            finally:
                browser.close()

    def test_duplicate_hidden_and_disabled_targets_never_click(self):
        cases = {
            "duplicate": "action_target_ambiguous",
            "disabled": "action_target_disabled",
            "hidden": "action_target_not_visible",
            "aria-hidden": "action_target_not_visible",
        }
        with local_fixture_server("kgg_ui_lab_control_targets_fixture.html") as url:
            for mode, error in cases.items():
                with self.subTest(mode=mode):
                    browser = browser_for(f"{url}?mode={mode}", f"fast-controls-{mode}")
                    try:
                        before = browser.observe()
                        self.assertNotIn("pilot-action", [c["label"] for c in before["controls"]])
                        with self.assertRaisesRegex(Exception, error):
                            browser.act({"operation": "click", "label": "pilot-action"})
                        self.assertEqual(browser.observe()["state"], "lang-de")
                    finally:
                        browser.close()


    def test_mcp_observation_and_action_without_coordinates(self):
        node, module_path = _runtime_available()
        module = server._load_real_browser_module()
        bootstrap = module.BrowserBootstrap(
            enabled=True, node_command=node, playwright_module_path=module_path,
        )
        with local_fixture_server("kgg_ui_lab_control_targets_fixture.html") as url:
            runtime = server.Runtime(browser_bootstrap=bootstrap)
            sid = "fast-controls-mcp-session"
            session = _session(
                url, session_id=sid, request_id="fast-controls-mcp-start",
                capabilities=["browser", "capture", "visual_loop"],
                viewport={"width": 390, "height": 844, "device_scale_factor": 1},
                device_profile="custom",
            )
            def call(index, name, args):
                return server.handle(runtime, {
                    "jsonrpc": "2.0", "id": index, "method": "tools/call",
                    "params": {"name": name, "arguments": args},
                })["result"]
            started = call(1, "start_ui_session", {"session": session})
            self.assertFalse(started.get("isError"), started)
            observed = call(2, "observe_visual_state", {"request": _visual_request(
                session_id=sid, request_id="fast-controls-mcp-observe", operation="observe_visual_state",
            )})
            self.assertFalse(observed.get("isError"), observed)
            before = observed["structuredContent"]["observation"]
            self.assertEqual(before["controls"], [
                {"role": "button", "label": "language-toggle"},
                {"role": "button", "label": "pilot-action"},
            ])
            acted = call(3, "execute_visual_action", {
                "request": _visual_request(
                    session_id=sid, request_id="fast-controls-mcp-action", operation="execute_visual_action",
                ),
                "decision": {"operation": "click", "label": "language-toggle",
                             "expected_state_after": "lang-en", "observation_id": before["id"]},
            })
            self.assertFalse(acted.get("isError"), acted)
            self.assertEqual(acted["structuredContent"]["result"]["state_after"], "lang-en")
            evidence = call(4, "get_test_evidence", {"session_id": sid, "actor": "codex"})
            self.assertEqual([e["status"] for e in evidence["structuredContent"]["evidence"]], ["OBSERVED", "PASS"])
            status = call(5, "get_session_status", {"session_id": sid, "actor": "codex"})
            self.assertEqual(status["structuredContent"]["status"], "completed")
            self.assertEqual(status["structuredContent"]["event_count"], 1)


    def test_malformed_or_duplicate_controls_are_rejected_at_mcp_boundary(self):
        module = server._load_real_browser_module()
        invalid = [
            [{"role": "button", "label": "Patient John"}],
            [{"role": "button", "label": "language-toggle"},
             {"role": "button", "label": "language-toggle"}],
            [{"role": "textbox", "label": "language-toggle"}],
            [{"role": "button", "label": "language-toggle", "text": "secret"}],
        ]
        for controls in invalid:
            with self.subTest(controls=controls):
                with self.assertRaisesRegex(module.RealBrowserError, "real_browser_controls_invalid"):
                    module._validate_session_response({
                        "status": "PASS", "error_class": "", "state": "lang-de",
                        "artifacts": [], "controls": controls,
                    })


if __name__ == "__main__":
    unittest.main()
