"""A failed real browser must leave bounded, retrievable diagnostic evidence."""

import sys
from itertools import product
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import Mock, patch

from test_kgg_real_browser_bridge import server, _session, _request


class VisualFailureEvidenceTests(unittest.TestCase):
    def test_invalid_host_json_and_live_host_timeout_remain_distinct(self):
        browser_module = server._load_real_browser_module()
        bootstrap = browser_module.BrowserBootstrap(enabled=True, node_command=sys.executable)
        cases = (
            ("import sys\nsys.stdin.readline()\nprint('<html>', flush=True)\n",
             "real_browser_session_response_invalid"),
            ("import sys, time\nsys.stdin.readline()\ntime.sleep(30)\n",
             "real_browser_timeout"),
        )
        with tempfile.TemporaryDirectory() as directory:
            helper = Path(directory) / "host.py"
            for source, expected in cases:
                with self.subTest(expected=expected):
                    helper.write_text(source, encoding="utf-8")
                    with patch.object(browser_module, "_session_helper_path", return_value=helper), \
                         patch.object(browser_module, "_foreground_wait_seconds", return_value=0.5):
                        with self.assertRaisesRegex(browser_module.RealBrowserError, "^" + expected + "$"):
                            browser_module.PersistentRealBrowser(
                                url="http://127.0.0.1:8765/synthetic",
                                viewport={"width": 390, "height": 844, "device_scale_factor": 1},
                                run_id="issue376-host-negative", timeout_ms=1000, bootstrap=bootstrap,
                            )

    def test_host_exit_without_json_is_not_reported_as_timeout(self):
        browser_module = server._load_real_browser_module()
        # A real child exits immediately: Python cannot execute the JS helper.
        # This models a failed Node/module startup without altering the live host.
        bootstrap = browser_module.BrowserBootstrap(enabled=True, node_command=sys.executable)
        started = time.monotonic()
        with patch.object(browser_module, "_foreground_wait_seconds", return_value=2):
            with self.assertRaisesRegex(browser_module.RealBrowserError, "^real_browser_process_failed$"):
                browser_module.PersistentRealBrowser(
                    url="http://127.0.0.1:8765/synthetic",
                    viewport={"width": 390, "height": 844, "device_scale_factor": 1},
                    run_id="issue376-early-host-exit", timeout_ms=1000, bootstrap=bootstrap,
                )
        self.assertLess(time.monotonic() - started, 2)

    def test_browser_failure_is_retained_at_each_visual_phase(self):
        browser_module = server._load_real_browser_module()
        for phase, code in product(("initialize", "observe", "act", "verify"),
                                   ("real_browser_timeout", "real_browser_process_failed")):
            with self.subTest(phase=phase, code=code):
                runtime = server.Runtime(browser_bootstrap=browser_module.BrowserBootstrap(enabled=True))
                session = _session("http://127.0.0.1:8765/synthetic", capabilities=["browser", "capture", "visual_loop"])
                runtime.start(session)
                sid = session["session_id"]
                browser = Mock()
                failure = browser_module.RealBrowserError(code)
                factory = Mock(return_value=browser)
                operation = "observe_visual_state" if phase in ("initialize", "observe") else "execute_visual_action"
                request = _request(request_id="failure-evidence-01", operation=operation)
                if phase == "initialize":
                    factory.side_effect = failure
                elif phase == "observe":
                    browser.observe.side_effect = failure
                else:
                    runtime.visual_sessions[sid] = browser
                    runtime.sessions[sid]["visual_observation"] = {"id": "c" * 64, "state": "initial"}
                    browser.act.return_value = {"action": {"before_state": "initial"}}
                    if phase == "act":
                        browser.act.side_effect = failure
                    else:
                        browser.observe.side_effect = failure
                with patch.object(server, "_load_real_browser_module", return_value=browser_module), patch.object(browser_module, "PersistentRealBrowser", factory):
                    with self.assertRaisesRegex(server.ServerError, code):
                        if operation == "observe_visual_state":
                            runtime.observe_visual(request)
                        else:
                            runtime.execute_visual_action(request, {
                                "operation": "click", "label": "synthetic-button",
                                "observation_id": "c" * 64, "expected_state_after": "next",
                            })
                evidence = runtime.evidence_read(sid, "codex")["evidence"]
                self.assertEqual(len(evidence), 1)
                self.assertEqual(evidence[0], {
                    "schema": "kgg-ui-lab/visual-evidence/v1", "status": "FAIL",
                    "surface": "real_browser", "operation": operation, "phase": phase,
                    "request_id": request["request_id"], "main_sha": session["app"]["main_sha"],
                    "error_class": code, "artifacts": [],
                })
                self.assertEqual(runtime.status_read(sid, "codex")["status"], "failed")
                self.assertNotIn(sid, runtime.visual_sessions)
                if phase != "initialize":
                    browser.close.assert_called_once()
                with self.assertRaisesRegex(server.ServerError, "mcp_auth_denied"):
                    runtime.evidence_read(sid, "custom_gpt")

    def test_rejected_request_does_not_launch_or_add_evidence(self):
        browser_module = server._load_real_browser_module()
        runtime = server.Runtime(browser_bootstrap=browser_module.BrowserBootstrap(enabled=True))
        session = _session("http://127.0.0.1:8765/synthetic", capabilities=["browser", "capture", "visual_loop"])
        runtime.start(session)
        request = _request(request_id="failure-evidence-02", operation="observe_visual_state")
        request["actor"] = "custom_gpt"
        with patch.object(server, "_load_real_browser_module", return_value=browser_module), patch.object(browser_module, "PersistentRealBrowser") as factory:
            with self.assertRaisesRegex(server.ServerError, "mcp_auth_denied"):
                runtime.observe_visual(request)
        factory.assert_not_called()
        self.assertEqual(runtime.evidence_read(session["session_id"], "codex")["evidence"], [])


if __name__ == "__main__":
    unittest.main()
