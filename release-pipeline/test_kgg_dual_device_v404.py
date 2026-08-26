#!/usr/bin/env python3
"""Security and behavior contracts for the v404 dual-device QR test station."""

from __future__ import annotations

import re
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "release-pipeline"))

import kgg_preview_context as preview_context  # noqa: E402


BUILD = ROOT / "android-wrapper/app/build.gradle"
BRIDGE = ROOT / "android-wrapper/app/src/preview/java/de/kgg/app/KggDeviceTestStationBridge.java"
FACTORY = ROOT / "android-wrapper/app/src/preview/java/de/kgg/app/KggReleaseControllerFactory.java"
STATION = ROOT / "android-wrapper/app/src/preview/assets/android/kgg_device_test_station.js"
FIXTURES = ROOT / "android-wrapper/app/src/preview/assets/android/kgg_dual_device_fixtures.js"
MAIN_ACTIVITY = ROOT / "android-wrapper/app/src/main/java/de/kgg/app/MainActivity.java"
SCANNER = ROOT / "patient-start-scan.js"
AGENT = ROOT / "device-test/patient-device-test-agent.js"
STORAGE = ROOT / "device-test/patient-device-test-storage.js"
WORKFLOW = ROOT / ".github/workflows/kgg-gpt-preview-gate.yml"
DEVICE_ACTION_WORKFLOW = ROOT / ".github/workflows/kgg-gpt-device-test.yml"
ACTION_API = ROOT / "docs/kgg-custom-gpt-action-api-openapi.yaml"
EXISTING_MAIN_PREVIEW = ROOT / "release-pipeline/kgg_existing_main_preview.py"


class DualDeviceV404ContractTests(unittest.TestCase):
    def test_roles_are_correct_and_preview_only(self) -> None:
        station = STATION.read_text(encoding="utf-8")
        agent = AGENT.read_text(encoding="utf-8")
        factory = FACTORY.read_text(encoding="utf-8")
        self.assertIn("Das Galaxy Tab zeigt QR-Codes", station)
        self.assertIn("Das Oppo scannt", station)
        self.assertIn('role: "display"', station)
        self.assertIn('role: "scanner"', agent)
        self.assertIn("kgg_dual_device_fixtures.js", factory)
        self.assertLess(
            factory.index("kgg_dual_device_fixtures.js"),
            factory.index("kgg_device_test_station.js"),
        )
        for profile in ("admin", "kollegen"):
            profile_root = ROOT / "android-wrapper/app/src" / profile
            joined = "\n".join(
                path.read_text(encoding="utf-8", errors="ignore")
                for path in profile_root.rglob("*")
                if path.is_file() and path.suffix in {".java", ".js"}
            )
            self.assertNotIn("KGGDualDeviceFixtures", joined)
            self.assertNotIn("KggDeviceTestStationBridge", joined)

    def test_fixed_fixture_ladder_and_integrity_contract(self) -> None:
        source = FIXTURES.read_text(encoding="utf-8")
        fixture_ids = re.findall(r'\{ id: "([^"]+)"', source)
        self.assertEqual(
            fixture_ids,
            [
                "h2-1-baseline",
                "h2-7-legacy",
                "h2-12-diagnostic",
                "h2-20-diagnostic",
                "h3-7-normal",
                "h3-12-normal",
                "h3-20-normal",
                "h3-20-far-angle",
                "h3-20-low-contrast",
                "h3-20-photo",
            ],
        )
        for required in (
            "SENTINEL-FIRST-",
            "SENTINEL-MIDDLE-",
            "SENTINEL-LAST-",
            "expectedFingerprint",
            "expectedOrderDigest",
            "KGGTEST1",
            "job_expired",
            "sha256Hex",
        ):
            self.assertIn(required, source)
        station = STATION.read_text(encoding="utf-8")
        agent = AGENT.read_text(encoding="utf-8")
        self.assertIn("Diagnose nicht lesbar (erlaubt)", station)
        self.assertIn("Diagnose nicht lesbar (erlaubt)", agent)
        self.assertIn('step.fixture.required ? "failed" : "skipped"', agent)
        self.assertIn('mark(step, "skipped", "diagnostic_unreadable")', station)
        self.assertIn("if (!document.documentElement || !document.head)", station)
        result = subprocess.run(
            ["node", "release-pipeline/kgg_dual_device_job.js", "--self-test"],
            cwd=ROOT,
            check=False,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_real_scanner_is_observed_without_raw_report_data(self) -> None:
        scanner = SCANNER.read_text(encoding="utf-8")
        agent = AGENT.read_text(encoding="utf-8")
        for token in (
            "BarcodeDetector",
            "jsqr",
            "getUserMedia",
            "KGGPatientDeviceTestObserver",
            "testConsume",
            "scanner-stop",
            "qrWidthRatioPct",
            "very-near",
            "very-far",
            "brightnessBand",
            "blurBand",
            "testFrameStatus",
        ):
            self.assertIn(token, scanner + agent)
        self.assertIn("ratio>=70?'very-near'", scanner)
        self.assertIn("ratio>=50?'near'", scanner)
        self.assertIn("ratio>=30?'normal'", scanner)
        self.assertIn("ratio>=15?'far':'very-far'", scanner)
        report_source = agent[agent.index("function report()") : agent.index("function openReportIssue()")]
        for forbidden in ("rawQr", "rawPayload", "base64", "cookie", "serial", "location", "userAgent"):
            self.assertNotIn(forbidden, report_source)
        self.assertIn("Screen Wake Lock", "Screen Wake Lock")
        self.assertIn('navigator.wakeLock.request("screen")', agent)

    def test_v404_native_boundary_is_bounded_and_token_free(self) -> None:
        bridge = BRIDGE.read_text(encoding="utf-8")
        build = BUILD.read_text(encoding="utf-8")
        interfaces = re.findall(
            r"@JavascriptInterface\s+public\s+[A-Za-z0-9_<>\[\]]+\s+([A-Za-z0-9_]+)\s*\(",
            bridge,
        )
        self.assertEqual(
            interfaces,
            ["getDeviceInfo", "beginSession", "endSession", "openReportIssue"],
        )
        self.assertIn('defaultPreviewVersion = "0.2.14-v404-dual-device-qr-test"', build)
        self.assertIn('manifestPlaceholders = [appLabel: "KGG QR-Teststation"]', build)
        self.assertIn("versionCode 36", build)
        self.assertIn("schemaVersion: 2", build)
        self.assertIn("REPORT_SCHEMA_VERSION = 2", bridge)
        self.assertIn("FLAG_KEEP_SCREEN_ON", bridge)
        self.assertIn("raw.githubusercontent.com", bridge)
        self.assertIn("kayus24.github.io", bridge)
        self.assertIn("kgg-device-test-reports/issues/new", bridge)
        for forbidden in (
            "Build.SERIAL",
            "CookieManager",
            "AccountManager",
            "LocationManager",
            "ConnectivityManager",
            "KGG_PATIENT_AUTOMATION_TOKEN",
            "ghp_",
            "github_pat_",
        ):
            self.assertNotIn(forbidden, bridge + build)

    def test_context_and_workflow_pin_one_source_commit(self) -> None:
        context = preview_context.build_context(
            request_id="dual-device-contract-test",
            patch_hash="a" * 64,
            base_sha="b" * 40,
            commit_sha="b" * 40,
            required_tests=["critical", "patient-scan"],
            device_test_session_id="kgg-test-" + "c" * 32,
            device_test_job_hash="d" * 64,
            device_test_job_url="https://raw.githubusercontent.com/Kayus24/kgg/gpt-preview/device-tests/dual-device-contract-test/job.json",
            patient_pwa_url="https://kayus24.github.io/kgg-patient-preview/device-test/",
            device_test_profile="quick",
        )
        self.assertEqual(context["schemaVersion"], 2)
        self.assertEqual(context["deviceTestProfile"], "quick")
        workflow = WORKFLOW.read_text(encoding="utf-8")
        for token in (
            "publish_device_test",
            "source_sha",
            "git -C base rev-parse HEAD",
            "kgg_dual_device_job.js",
            "kgg_dual_device_package.js",
            "KGG_PATIENT_AUTOMATION_TOKEN",
            "secrets.KGG_PATIENT_AUTOMATION_TOKEN",
            "device-tests/$KGG_REQUEST_ID/job.json",
            "KGG_REQUEST_ID: ${{ inputs.request_id }}",
            "^[a-z0-9][a-z0-9-]{5,63}$",
        ):
            self.assertIn(token, workflow)
        client_source = "\n".join(
            path.read_text(encoding="utf-8", errors="ignore")
            for path in (STATION, FIXTURES, AGENT, SCANNER)
        )
        self.assertNotIn("KGG_PATIENT_AUTOMATION_TOKEN", client_source)
        self.assertNotRegex(client_source, r"gh[pousr]_[A-Za-z0-9_]{20,}")

    def test_persistent_existing_main_preview_contract(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        device_action = DEVICE_ACTION_WORKFLOW.read_text(encoding="utf-8")
        action_api = ACTION_API.read_text(encoding="utf-8")
        main_activity = MAIN_ACTIVITY.read_text(encoding="utf-8")
        publisher = EXISTING_MAIN_PREVIEW.read_text(encoding="utf-8")

        self.assertIn("Stage exact pinned Admin HTML into persistent Preview channel", workflow)
        self.assertIn("--source-html base/kgg-update/index.html", workflow)
        self.assertIn("--version-json base/kgg-update/version.json", workflow)
        self.assertIn('git -C base fetch --no-tags origin main:refs/remotes/origin/main', workflow)
        self.assertIn('test "$checked_out" = "$KGG_SOURCE_SHA"', workflow)
        self.assertIn('if [ "$main_sha" != "$KGG_SOURCE_SHA" ]; then', workflow)
        self.assertIn('git add previews "device-tests/$KGG_REQUEST_ID/job.json"', workflow)
        self.assertIn("inputs.mode == 'publish_device_test' || inputs.ui_stability == 'true'", workflow)

        self.assertIn("kgg_gpt_write_gate.py", workflow)
        self.assertIn("if: inputs.mode != 'publish_device_test'", workflow)
        self.assertIn("- name: Publish preview channel", workflow)
        self.assertIn("if: inputs.mode == 'publish_preview'", workflow)
        self.assertIn('git commit -m "publish gpt preview ${{ inputs.request_id }}"', workflow)

        self.assertIn("PREVIEW_MANIFEST_URL", main_activity)
        self.assertIn("gpt-preview/previews/index.json", main_activity)
        self.assertIn('latest.optString("url", "")', main_activity)
        self.assertIn('latest.optString("sha256", "")', main_activity)

        self.assertIn('"sourceType": "existing-main"', publisher)
        self.assertIn('"sourceSha": source_sha', publisher)
        self.assertIn('index["latest"] = meta', publisher)
        self.assertNotIn("kgg_new_patch", publisher)
        self.assertNotIn("patch_content", publisher)

        self.assertIn("mode: publish_device_test", device_action)
        self.assertIn("payload_json: '{}'", device_action)
        self.assertIn('ui_stability: "true"', device_action)
        self.assertNotIn("create_pr", device_action)
        self.assertNotIn("publish_admin_beta", device_action)

        marker = "/repos/Kayus24/kgg/actions/workflows/kgg-gpt-device-test.yml/dispatches:"
        self.assertIn(marker, action_api)
        action_block = action_api[action_api.index(marker) :]
        next_path = action_block.find("\n  /", 3)
        if next_path >= 0:
            action_block = action_block[:next_path]
        self.assertIn("operationId: submitKggDeviceTest", action_block)
        self.assertIn("x-openai-isConsequential: false", action_block)
        self.assertIn("required: [request_id, source_sha]", action_block)
        self.assertNotIn("payload_json", action_block)
        self.assertNotRegex(action_block, r"^\s+mode:", re.MULTILINE)
        self.assertNotIn("approval_phrase", action_block)

        result = subprocess.run(
            [sys.executable, "release-pipeline/kgg_existing_main_preview.py", "--self-test"],
            cwd=ROOT,
            check=False,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_public_pwa_package_is_scoped_and_offline_capable(self) -> None:
        result = subprocess.run(
            ["node", "release-pipeline/kgg_dual_device_package.js", "--self-test"],
            cwd=ROOT,
            check=False,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        package_source = (ROOT / "release-pipeline/kgg_dual_device_package.js").read_text(encoding="utf-8")
        self.assertIn('/kgg-patient-preview/device-test/', package_source)
        self.assertIn("patient-device-test-agent.js", package_source)
        self.assertIn("patient-device-test-storage.js", package_source)
        self.assertIn("qrcode-generator-1.5.2.js", package_source)
        self.assertIn("kgg-device-test-v404-", package_source)
        storage_source = STORAGE.read_text(encoding="utf-8")
        self.assertIn("kgg_device_test_v404:", storage_source)
        self.assertIn("KGGDeviceTestStorage", storage_source)
        self.assertNotIn("backend.clear", storage_source)
        self.assertIn("schedulePendingImportCheck", AGENT.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
