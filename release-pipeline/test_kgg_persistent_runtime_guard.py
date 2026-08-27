#!/usr/bin/env python3
"""Contracts for binding a persistent device-test runtime to the HTML actually loaded in WebView."""

from __future__ import annotations

import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FACTORY = ROOT / "android-wrapper/app/src/preview/java/de/kgg/app/KggReleaseControllerFactory.java"
GUARD = ROOT / "android-wrapper/app/src/preview/assets/android/kgg_device_test_runtime_guard.js"
UPDATE_BRIDGE = ROOT / "android-wrapper/app/src/preview/java/de/kgg/app/KggPreviewWebUpdateBridge.java"
SMOKE = ROOT / "release-pipeline/kgg_persistent_runtime_guard_smoke.js"
DEVICE_WORKFLOW = ROOT / ".github/workflows/kgg-gpt-device-test.yml"


class PersistentRuntimeGuardTests(unittest.TestCase):
    def test_runtime_guard_is_preview_only_and_injected_before_station(self) -> None:
        factory = FACTORY.read_text(encoding="utf-8")
        guard = GUARD.read_text(encoding="utf-8")
        update_bridge = UPDATE_BRIDGE.read_text(encoding="utf-8")

        self.assertIn('"KGGDeviceTestStationNative"', factory)
        self.assertIn('"KGGPreviewWebUpdateNative"', factory)
        self.assertIn('"android/kgg_device_test_runtime_guard.js"', factory)
        self.assertLess(
            factory.index("kgg_device_test_runtime_guard.js"),
            factory.index("kgg_device_test_station.js"),
        )
        self.assertIn("KGGDeviceTestStationNative", guard)
        self.assertIn("KGGPreviewWebUpdateNative", guard)
        self.assertIn("KGGAndroidApp", guard)
        self.assertIn("requestPreviewWebUpdate", guard)
        self.assertIn("preview_html_not_current", guard)
        self.assertIn("preview_html_not_healthy", guard)
        self.assertIn("status.rolloutCode", guard)
        self.assertIn("status.releaseId", guard)
        self.assertIn("status.pendingHealthCheck", guard)
        self.assertIn('getDeclaredMethod("checkForPreviewWebAppUpdate")', update_bridge)
        self.assertNotIn("checkForAppUpdate", update_bridge)
        self.assertNotIn("checkForAndroidAppUpdate", update_bridge)
        for forbidden in (
            "fetch(",
            "XMLHttpRequest",
            "eval(",
            "new Function",
            "CookieManager",
            "KGG_PATIENT_AUTOMATION_TOKEN",
            "ghp_",
            "github_pat_",
        ):
            self.assertNotIn(forbidden, guard)

    def test_device_action_has_no_pr_or_issue_write_permission(self) -> None:
        workflow = DEVICE_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("mode: publish_device_test", workflow)
        self.assertIn("contents: write", workflow)
        self.assertNotIn("pull-requests: write", workflow)
        self.assertNotIn("issues: write", workflow)
        self.assertNotIn("create_pr", workflow)
        self.assertNotIn("publish_admin_beta", workflow)

    def test_stale_html_a_requests_runtime_b_without_native_session(self) -> None:
        result = subprocess.run(
            ["node", str(SMOKE.relative_to(ROOT))],
            cwd=ROOT,
            check=False,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('"staleHtmlBlocked":true', result.stdout)
        self.assertIn('"foregroundUpdateRequested":true', result.stdout)
        self.assertIn('"duplicateUpdateSuppressed":true', result.stdout)
        self.assertIn('"pendingHealthBlocked":true', result.stdout)
        self.assertIn('"activeRequest":"preview-job-b"', result.stdout)
        self.assertIn('"activeProfile":"quick"', result.stdout)
        self.assertIn('"activeRollout":202', result.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
