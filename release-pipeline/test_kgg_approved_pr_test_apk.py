#!/usr/bin/env python3
"""Fail-closed static checks for migrated-plugin-compatible PR test-APK lane.

This lane produces only a downloadable artifact. It never grants publish rights.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "kgg-approved-pr-test-apk.yml"


class ApprovedPrTestApkWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = WORKFLOW.read_text(encoding="utf-8")

    def test_offline_gate_and_safe_trigger(self):
        text = self.text
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("if: github.event_name == 'workflow_dispatch'", text)
        self.assertIn("ref: main", text)
        self.assertIn('test "$GITHUB_REF_NAME" = "main"', text)
        self.assertIn("test_kgg_verified_pr_provenance.py", text)
        self.assertIn("kgg_verified_pr_provenance.py", text)
        self.assertGreaterEqual(text.count("kgg_verified_pr_provenance.py"), 2)

    def test_no_write_capabilities_or_release_actions(self):
        text = self.text
        for forbidden in ("contents: write", "git push", "deploy", "create-release",
                          "gh release", "submitKggMainGate", "--require-live-synced",
                          "gpt-preview", "syncStatus"):
            self.assertNotIn(forbidden, text)
        for required in ("contents: read", "pull-requests: read", "actions: read",
                         "persist-credentials: false", "upload-artifact@v4",
                         "publishingAuthorized==false"):
            self.assertIn(required, text)

    def test_sha_binding_and_reapproval(self):
        text = self.text
        self.assertIn("^[0-9a-f]{40}$", text)
        self.assertIn('git -C source rev-parse HEAD', text)
        self.assertIn("--sha \"$SOURCE_SHA\"", text)
        self.assertIn("pr-final.json", text)
        self.assertIn("run-final.json", text)
        self.assertIn("attestation-final.json", text)
        self.assertGreaterEqual(text.count("gh api \"repos/$GITHUB_REPOSITORY/pulls/$SOURCE_PR\""), 2)

    def test_only_test_apk_and_required_regressions(self):
        text = self.text
        self.assertEqual(text.count("assemblePreviewDebug"), 1)
        self.assertIn("--level critical", text)
        self.assertIn("--suite ui-stability --level regression", text)
        self.assertEqual(text.count("--case=phone-cockpit-entry-390"), 2)
        self.assertIn("source/android-wrapper/app/build/outputs/apk/preview/debug/app-preview-debug.apk", text)
        self.assertEqual(len(re.findall(r"actions/upload-artifact@v4", text)), 1)


if __name__ == "__main__":
    unittest.main()
