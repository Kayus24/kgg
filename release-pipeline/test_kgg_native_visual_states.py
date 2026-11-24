"""Native state inference is bounded, visibility-based and KGG-only."""
import unittest
from test_kgg_real_browser_bridge import server, _runtime_available, local_fixture_server


class NativeVisualStatesTests(unittest.TestCase):
    def test_native_modals_require_visible_post_click_state(self):
        provisioned = _runtime_available()
        if not provisioned:
            self.skipTest("pre-provisioned Playwright unavailable")
        module = server._load_real_browser_module()
        with local_fixture_server("kgg_ui_lab_native_state_fixture.html") as url:
            for surface in ("patient", "therapist"):
                with self.subTest(surface=surface):
                    browser = module.PersistentRealBrowser(
                        url=url + "?surface=" + surface,
                        viewport={"width": 390, "height": 844, "device_scale_factor": 1},
                        run_id="issue376-native-state-" + surface, timeout_ms=5000,
                        bootstrap=module.BrowserBootstrap(enabled=True, node_command=provisioned[0], playwright_module_path=provisioned[1]),
                    )
                    try:
                        before = browser.observe()
                        self.assertEqual(before["state"], surface + "-plan")
                        browser.act({"operation": "click", "label": "open"})
                        after = browser.observe()
                        self.assertEqual(after["state"], "patient-numpad" if surface == "patient" else "therapist-editor")
                        self.assertNotEqual(before["artifacts"][0]["sha256"], after["artifacts"][0]["sha256"])
                    finally:
                        browser.close()

    def test_generic_policy_does_not_infer_kgg_states(self):
        provisioned = _runtime_available()
        if not provisioned:
            self.skipTest("pre-provisioned Playwright unavailable")
        module = server._load_real_browser_module()
        with local_fixture_server("kgg_ui_lab_native_state_fixture.html") as url:
            browser = module.PersistentRealBrowser(
                url=url, viewport={"width": 390, "height": 844, "device_scale_factor": 1},
                run_id="issue376-generic-state", timeout_ms=5000,
                bootstrap=module.BrowserBootstrap(enabled=True, node_command=provisioned[0], playwright_module_path=provisioned[1], policy=module.BrowserPolicy.generic()),
            )
            try:
                self.assertEqual(browser.observe()["state"], "unknown")
                browser.act({"operation": "click", "label": "Open"})
                self.assertEqual(browser.observe()["state"], "unknown")
            finally:
                browser.close()


if __name__ == "__main__":
    unittest.main()
