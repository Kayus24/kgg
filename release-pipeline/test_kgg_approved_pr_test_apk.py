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

    @staticmethod
    def _jobs(text: str) -> dict[str, str]:
        pieces = re.split(r"(?m)^  ([a-z][a-z0-9-]+):\s*$",
                          text.split("\njobs:\n", 1)[1])
        return {pieces[i]: pieces[i + 1] for i in range(1, len(pieces), 2)}

    def assert_isolated_jobs(self, text: str) -> None:
        jobs = self._jobs(text)
        self.assertEqual(set(jobs), {
            "contract", "verify-source", "build-test-apk", "finalize-test-apk"
        })
        before, build, after = (jobs[name] for name in (
            "verify-source", "build-test-apk", "finalize-test-apk"
        ))
        self.assertIn("needs: contract", before)
        self.assertIn("needs: verify-source", build)
        self.assertIn("needs: build-test-apk", after)
        for trusted in (before, after):
            self.assertIn("runs-on: ubuntu-latest", trusted)
            self.assertIn("ref: ${{ github.sha }}", trusted)
            self.assertIn("GH_TOKEN: ${{ github.token }}", trusted)
            self.assertIn("pull-requests: read", trusted)
            self.assertIn("actions: read", trusted)
            self.assertIn("path: trusted", trusted)
            self.assertIn("kgg_verified_pr_provenance.py", trusted)
            self.assertNotIn("working-directory: source", trusted)
            self.assertNotIn("python source/", trusted)
            self.assertNotIn("node release-pipeline/", trusted)
            self.assertNotIn("gradle ", trusted)
            self.assertNotIn("path: source", trusted)
        self.assertIn("permissions:\n      contents: read", build)
        for forbidden in ("GH_TOKEN:", "github.token", "gh api ", "path: trusted",
                          "kgg_verified_pr_provenance.py", "pull-requests: read",
                          "actions: read", "actions/download-artifact"):
            self.assertNotIn(forbidden, build)
        self.assertIn("ref: ${{ inputs.source_sha }}", build)
        self.assertIn("cache-disabled: true", build)
        self.assertEqual(build.count("actions/upload-artifact@v4"), 1)
        self.assertIn("untrusted-pr-", build)
        self.assertNotIn("approved-pr-", build)
        self.assertEqual(after.count("actions/upload-artifact@v4"), 1)
        self.assertLess(after.index("attestation-final.json"),
                        after.index("actions/download-artifact@v4"))
        self.assertLess(after.index("actions/download-artifact@v4"),
                        after.index("name: approved-pr-"))
        self.assertIn("never execute", after)

    def assert_independent_pins(self, text: str) -> None:
        jobs = self._jobs(text)
        for job_name in ("verify-source", "finalize-test-apk"):
            trusted = jobs[job_name]
            self.assertIn('--branch "$SOURCE_BRANCH"', trusted)
            self.assertIn('--base-branch "$SOURCE_BASE_BRANCH"', trusted)
            self.assertIn('--base-sha "$SOURCE_BASE_SHA"', trusted)
            self.assertNotIn("jq -r .head.ref", trusted)
            self.assertNotIn("jq -r .base.ref", trusted)
        for key in ("source_sha", "source_branch", "base_branch", "base_sha"):
            self.assertIn("      " + key + ":", text)

    def test_offline_gate_and_safe_trigger(self):
        text = self.text
        self.assertIn("  pull_request:\n    branches: [main]", text)
        self.assertNotIn("  push:\n", text)
        self.assertIn("      - release-pipeline/kgg_verified_pr_provenance.py", text)
        self.assertIn("      - release-pipeline/test_kgg_verified_pr_provenance.py", text)
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("if: github.event_name == 'workflow_dispatch'", text)
        self.assertIn("ref: ${{ github.sha }}", text)
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

    def test_isolation_and_independent_pins(self):
        self.assert_isolated_jobs(self.text)
        self.assert_independent_pins(self.text)

    def test_rejects_old_same_job_revalidation_and_missing_final_runner(self):
        injected = self.text.replace(
            "      - name: Stage untrusted APK data for isolated validation job",
            "      - name: Dangerous reapproval on untrusted runner\n"
            "        env:\n"
            "          GH_TOKEN: ${{ github.token }}\n"
            "        run: gh api repos/$GITHUB_REPOSITORY/pulls/$SOURCE_PR\n"
            "      - name: Stage untrusted APK data for isolated validation job", 1
        )
        with self.assertRaises(AssertionError):
            self.assert_isolated_jobs(injected)
        no_final = self.text.replace("  finalize-test-apk:", "  lost-finalize:", 1)
        with self.assertRaises(AssertionError):
            self.assert_isolated_jobs(no_final)

    def test_rejects_self_reference_in_place_of_immutable_base_pin(self):
        unsafe = self.text.replace(
            '--base-branch "$SOURCE_BASE_BRANCH"',
            '--base-branch "$(jq -r .base.ref "$RUNNER_TEMP/pr.json")"', 1
        )
        with self.assertRaises(AssertionError):
            self.assert_independent_pins(unsafe)
        unsafe = self.text.replace(
            '--base-sha "$SOURCE_BASE_SHA"',
            '--base-sha "$(jq -r .base.sha "$RUNNER_TEMP/pr.json")"', 1
        )
        with self.assertRaises(AssertionError):
            self.assert_independent_pins(unsafe)

    def assert_signed_apk_and_pinned_metadata(self, text: str) -> None:
        jobs = self._jobs(text)
        final = jobs["finalize-test-apk"]
        build = jobs["build-test-apk"]
        self.assertIn('REQUEST_ID: ${{ inputs.request_id }}', final)
        self.assertIn("contents: read", final)
        self.assertIn('contents/kgg-update/version.json?ref=$SOURCE_SHA', final)
        self.assertIn('GH_TOKEN: ${{ github.token }}', final)
        self.assertIn('python trusted/release-pipeline/kgg_verified_pr_provenance.py', final)
        self.assertIn("--verify-artifact --artifact-dir", final)
        artifact_check = final.split("--verify-artifact", 1)[1].split(
            '> "$RUNNER_TEMP/artifact-integrity.json"', 1)[0]
        self.assertIn('--github-version-file "$RUNNER_TEMP/github-source-version.json"', artifact_check)
        self.assertIn('--sha "$SOURCE_SHA"', artifact_check)
        self.assertIn('--base-sha "$SOURCE_BASE_SHA"', artifact_check)
        self.assertIn('--request-id "$REQUEST_ID"', artifact_check)
        self.assertIn('.artifactSignatureVerified==true', final)
        self.assertIn('artifact-integrity.json', final)
        self.assertLess(final.index("attestation-final.json"),
                        final.index("contents/kgg-update/version.json?ref=$SOURCE_SHA"))
        self.assertLess(final.index("contents/kgg-update/version.json?ref=$SOURCE_SHA"),
                        final.index("actions/download-artifact@v4"))
        self.assertLess(final.index("actions/download-artifact@v4"),
                        final.index("--verify-artifact"))
        self.assertLess(final.index("--verify-artifact"),
                        final.index("name: approved-pr-"))
        self.assertNotIn("github-source-version.json", build)
        self.assertNotIn("GH_TOKEN:", build)

    def test_signed_apk_integrity_guard_before_final_upload(self):
        self.assert_signed_apk_and_pinned_metadata(self.text)

    def test_rejects_missing_artifact_integrity_or_unpinned_version_source(self):
        for old, new in (
            ("--verify-artifact --artifact-dir", "--artifact-dir"),
            ("contents/kgg-update/version.json?ref=$SOURCE_SHA",
             "contents/kgg-update/version.json?ref=main"),
            ('.artifactSignatureVerified==true', '.status=="PASS"'),
            ('--base-sha "$SOURCE_BASE_SHA"', '--base-sha "$SOURCE_SHA"'),
            ('--request-id "$REQUEST_ID"', '--request-id "wrong-request"'),
        ):
            with self.subTest(removed=old):
                # Change the finalizer occurrence, not the earlier verification job.
                before, separator, after = self.text.rpartition(old)
                self.assertTrue(separator, old)
                unsafe = before + new + after
                with self.assertRaises(AssertionError):
                    self.assert_signed_apk_and_pinned_metadata(unsafe)

    def test_only_test_apk_and_required_regressions(self):
        text = self.text
        self.assertEqual(text.count("assemblePreviewDebug"), 1)
        self.assertIn("--level critical", text)
        self.assertIn("--suite ui-stability --level regression", text)
        self.assertEqual(text.count("--case=phone-cockpit-entry-390"), 2)
        self.assertIn("source/android-wrapper/app/build/outputs/apk/preview/debug/app-preview-debug.apk", text)
        self.assertEqual(len(re.findall(r"actions/upload-artifact@v4", text)), 2)
        self.assertIn("cache-disabled: true", text)
        self.assertIn("actions/download-artifact@v4", text)


if __name__ == "__main__":
    unittest.main()
