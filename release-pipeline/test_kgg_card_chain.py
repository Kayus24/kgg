"""Synthetic native patient card -> numpad visual-chain regression."""
import unittest
from test_kgg_real_browser_bridge import server, _runtime_available, local_fixture_server, _session, _visual_request


class NativeCardChainTests(unittest.TestCase):
    def _runtime(self):
        provisioned = _runtime_available()
        if not provisioned:
            self.skipTest("pre-provisioned Playwright unavailable")
        browser = server._load_real_browser_module()
        return server.Runtime(browser_bootstrap=browser.BrowserBootstrap(
            enabled=True, node_command=provisioned[0], playwright_module_path=provisioned[1]))

    @staticmethod
    def _request(sid, suffix, operation):
        return _visual_request(session_id=sid, request_id=sid + "-" + suffix, operation=operation)

    def _start(self, runtime, url, sid):
        runtime.start(_session(url, session_id=sid, request_id=sid + "-start",
            capabilities=["browser", "capture", "visual_loop"],
            viewport={"width": 390, "height": 844, "device_scale_factor": 1},
            device_profile="custom"))
        return runtime.observe_visual(self._request(sid, "observe", "observe_visual_state"))["observation"]

    def _act(self, runtime, sid, suffix, observed, label, expected, coordinates=None):
        decision = {"operation": "click", "label": label,
                    "expected_state_after": expected, "observation_id": observed["id"]}
        if coordinates is not None:
            decision["coordinates"] = coordinates
        return runtime.execute_visual_action(self._request(sid, suffix, "execute_visual_action"), decision)

    def test_patient_card_then_numpad_requires_two_verified_steps(self):
        runtime = self._runtime()
        sid = "kg2-card-chain-positive"
        with local_fixture_server("kgg_ui_lab_card_chain_fixture.html") as url:
            before = self._start(runtime, url, sid)
            try:
                self.assertEqual(before["state"], "patient-plan")
                self.assertEqual(before["language"], "lang-de")
                first = self._act(runtime, sid, "card", before, "expand-card", "patient-card-open",
                                  coordinates={"x": 238, "y": 550})
                self.assertEqual(first["result"]["state_after"], "patient-card-open")
                next_observation = first["next_observation"]
                self.assertEqual(next_observation["state"], "patient-card-open")
                self.assertEqual(next_observation["language"], "lang-de")
                self.assertNotEqual(next_observation["id"], before["id"])
                self.assertIn(sid, runtime.visual_sessions)
                with self.assertRaisesRegex(server.ServerError, "visual_observation_stale"):
                    self._act(runtime, sid, "stale", before, "open-pad", "patient-numpad")
                second = self._act(runtime, sid, "pad", next_observation, "open-pad", "patient-numpad")
                self.assertEqual(second["result"]["state_after"], "patient-numpad")
                self.assertNotIn(sid, runtime.visual_sessions)
                self.assertNotEqual(first["result"]["artifacts"][0]["sha256"], first["result"]["artifacts"][1]["sha256"])
                self.assertNotEqual(second["result"]["artifacts"][0]["sha256"], second["result"]["artifacts"][1]["sha256"])
            finally:
                runtime._close_visual(sid)

    def test_noop_never_counts_as_verified_card_transition(self):
        runtime = self._runtime()
        sid = "kg2-card-chain-noop"
        with local_fixture_server("kgg_ui_lab_card_chain_fixture.html") as url:
            before = self._start(runtime, url, sid)
            try:
                with self.assertRaisesRegex(server.ServerError, "visual_expected_state_not_reached"):
                    self._act(runtime, sid, "noop", before, "no-change", "patient-card-open")
                self.assertNotIn(sid, runtime.visual_sessions)
            finally:
                runtime._close_visual(sid)

    def test_second_step_must_target_verified_numpad(self):
        runtime = self._runtime()
        sid = "kg2-card-chain-invalid"
        with local_fixture_server("kgg_ui_lab_card_chain_fixture.html") as url:
            before = self._start(runtime, url, sid)
            try:
                first = self._act(runtime, sid, "card", before, "expand-card", "patient-card-open")
                with self.assertRaisesRegex(server.ServerError, "visual_chain_transition_invalid"):
                    self._act(runtime, sid, "wrong", first["next_observation"], "no-change", "patient-plan")
                self.assertNotIn(sid, runtime.visual_sessions)
            finally:
                runtime._close_visual(sid)

    def test_mcp_response_exposes_bounded_next_observation(self):
        runtime = self._runtime()
        sid = "kg2-card-chain-mcp"
        with local_fixture_server("kgg_ui_lab_card_chain_fixture.html") as url:
            before = self._start(runtime, url, sid)
            def mcp_act(suffix, observed, label, expected):
                return server.handle(runtime, {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                    "params": {"name": "execute_visual_action", "arguments": {
                        "request": self._request(sid, suffix, "execute_visual_action"),
                        "decision": {"operation": "click", "label": label,
                                     "expected_state_after": expected,
                                     "observation_id": observed["id"]}}}})
            try:
                first = mcp_act("card", before, "expand-card", "patient-card-open")
                self.assertFalse(first["result"].get("isError"), first)
                next_observation = first["result"]["structuredContent"]["next_observation"]
                self.assertEqual(first["result"]["structuredContent"]["session_status"], "awaiting_followup")
                second = mcp_act("pad", next_observation, "open-pad", "patient-numpad")
                self.assertFalse(second["result"].get("isError"), second)
                self.assertEqual(second["result"]["structuredContent"]["result"]["state_after"], "patient-numpad")
                self.assertNotIn("next_observation", second["result"]["structuredContent"])
            finally:
                runtime._close_visual(sid)


if __name__ == "__main__":
    unittest.main()
