#!/usr/bin/env python3
"""Contract and security tests for the Preview-only Tab S9 test station."""

from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "release-pipeline"))

import kgg_gpt_write_gate as gate  # noqa: E402
import kgg_preview_context as preview_context  # noqa: E402


BRIDGE = ROOT / "android-wrapper/app/src/preview/java/de/kgg/app/KggDeviceTestStationBridge.java"
PREVIEW_FACTORY = ROOT / "android-wrapper/app/src/preview/java/de/kgg/app/KggReleaseControllerFactory.java"
PREVIEW_JS = ROOT / "android-wrapper/app/src/preview/assets/android/kgg_device_test_station.js"
BUILD_GRADLE = ROOT / "android-wrapper/app/build.gradle"


class TabS9TestStationContractTests(unittest.TestCase):
    def test_preview_only_files_and_native_surface(self) -> None:
        bridge = BRIDGE.read_text(encoding="utf-8")
        factory = PREVIEW_FACTORY.read_text(encoding="utf-8")
        self.assertEqual(
            re.findall(
                r"@JavascriptInterface\s+public\s+[A-Za-z0-9_<>\[\]]+\s+([A-Za-z0-9_]+)\s*\(",
                bridge,
            ),
            ["getDeviceInfo", "beginSession", "endSession", "openReportIssue"],
        )
        self.assertIn("KGGDeviceTestStation", factory)
        self.assertIn("kgg_device_test_station.js", factory)
        self.assertIn("kgg_preview_context.js", factory)
        self.assertIn("KggDeviceTestStationBridge", factory)
        for forbidden in (
            "Build.SERIAL",
            "CookieManager",
            "AccountManager",
            "LocationManager",
            "ConnectivityManager",
            "Uri.parse",
            "https://example",
        ):
            self.assertNotIn(forbidden, bridge)
        self.assertIn(
            "https://github.com/Kayus24/kgg-device-test-reports/issues/new",
            bridge,
        )
        self.assertIn('appendQueryParameter("title"', bridge)
        self.assertIn('appendQueryParameter("body"', bridge)
        self.assertIn("syntheticOnly", bridge)
        self.assertIn("REPORT_SCHEMA_VERSION = 1", bridge)
        self.assertIn('private static final String APP_VERSION_CODE', bridge)
        self.assertIn('preferences.getString(PREVIEW_VERSION, BuildConfig.VERSION_NAME)', bridge)

        isolated_source = []
        for path in (
            ROOT / "android-wrapper/app/src/admin",
            ROOT / "android-wrapper/app/src/kollegen",
        ):
            for candidate in path.rglob("*"):
                if candidate.is_file() and candidate.suffix in {".java", ".js"}:
                    isolated_source.append(candidate.read_text(encoding="utf-8"))
        joined = "\n".join(isolated_source)
        for forbidden in (
            "KggDeviceTestStationBridge",
            "KGGDeviceTestStation",
            "kgg_device_test_station.js",
            "kgg_preview_context.js",
            "KGG_PREVIEW_REQUEST_ID",
        ):
            self.assertNotIn(forbidden, joined)

    def test_guided_steps_cover_all_requested_blocks(self) -> None:
        source = PREVIEW_JS.read_text(encoding="utf-8")
        ids = re.findall(r'id:\s*"([^"]+)"', source)
        self.assertEqual(ids, list(preview_context.STATION_TEST_IDS))
        for value in (
            "bestanden",
            "fehlgeschlagen",
            "blockiert",
            "optional übersprungen",
            "Hochformat",
            "Querformat",
            "Split-Screen",
            "Paket-Schaltfläche",
            "Sieben synthetische Übungen",
            "Reihenfolge und Neuladen",
            "Erststart",
            "Plan hinzufügen",
            "Plan ersetzen und abbrechen",
            "Planwechsel",
            "Umbenennen",
            "Werte nach Neuladen",
            "Offline und Wiederherstellung",
            "Oppo nur als QR-Anzeige",
            "KGGH2",
            "KGGH3",
            "sieben Übungen",
            "zwölf Übungen",
            "20 Übungen",
            "Winkel und Abstand",
            "schwaches synthetisches Bild",
            "Foto-Ausweichweg",
            "Stream muss sauber enden",
            "blockiert – echtes Tab nötig",
        ):
            self.assertIn(value, source)
        for forbidden in (
            "document.cookie",
            "navigator.geolocation",
            "navigator.sendBeacon",
            "CookieManager",
            "fetch(",
            "getUserMedia(",
        ):
            self.assertNotIn(forbidden, source)

    def test_v403_and_context_hooks_are_preview_scoped(self) -> None:
        gradle = BUILD_GRADLE.read_text(encoding="utf-8")
        self.assertIn('defaultPreviewVersion = "0.2.13-v403-tab-s9-test-station"', gradle)
        self.assertIn("versionCode 35", gradle)
        self.assertIn("versionName defaultPreviewVersion", gradle)
        self.assertIn("KGG_PREVIEW_CONTEXT_FILE", gradle)
        self.assertIn("kgg_preview_context.js", gradle)
        self.assertIn("KGG_PREVIEW_PATCH_HASH", gradle)
        self.assertIn("KGG_PREVIEW_BASE_SHA", gradle)
        self.assertIn("KGG_PREVIEW_COMMIT_SHA", gradle)
        self.assertIn("KGG_PREVIEW_REQUIRED_TESTS", gradle)
        self.assertIn('versionCode 33', gradle)
        self.assertIn('versionName "0.2.11-v401-share-apk-provider"', gradle)

    def test_preview_html_receives_safe_context(self) -> None:
        html = "<!doctype html><html><head></head><body><main>synthetic</main></body></html>"
        payload = {
            "request_id": "tab-s9-contract-preview",
            "title": "Tab S9",
            "required_tests": ["critical", "ui-stability"],
        }
        rendered = gate.inject_preview_banner(
            html,
            payload,
            "a" * 64,
            {"versionName": "1.0.72-contract"},
        )
        self.assertIn('id="kgg-preview-context"', rendered)
        self.assertIn('"requestId":"tab-s9-contract-preview"', rendered)
        self.assertIn('"patchHash":"aaaaaaaa', rendered)
        self.assertIn('"stationTestIds"', rendered)
        self.assertNotIn("</script><script", rendered)
        self.assertNotIn("Cookie", rendered)


if __name__ == "__main__":
    unittest.main(verbosity=2)
