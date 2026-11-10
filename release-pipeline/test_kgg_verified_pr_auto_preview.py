"""Fail-closed contracts for automatic, HTML-only, verified PR Preview publication."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/kgg-verified-pr-auto-preview.yml"
PUBLISHER = ROOT / "release-pipeline/kgg_existing_main_preview.py"


class VerifiedPrAutoPreviewContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")
        cls.publisher = PUBLISHER.read_text(encoding="utf-8")

    def test_uses_existing_preview_manifest_and_verified_pr_mode(self):
        self.assertIn('"verified-pr"', self.publisher)
        self.assertIn('"verificationRunId": verified_run_id', self.publisher)
        self.assertIn('meta.pop("deviceTestJobUrl", None)', self.publisher)
        self.assertIn('--source-type verified-pr', self.workflow)
        self.assertIn('--source-html', self.workflow)
        self.assertIn('preview/previews/index.json', self.workflow)

    def test_auto_activation_requires_successful_named_pr_ci(self):
        self.assertIn('workflow_run:', self.workflow)
        self.assertIn('workflows: ["Validate and build KGG admin beta"]', self.workflow)
        self.assertIn("github.event.workflow_run.conclusion == 'success'", self.workflow)
        self.assertIn('.path == ".github/workflows/release-pr.yml"', self.workflow)
        self.assertIn('.head.sha == $sha', self.workflow)
        self.assertIn('index("kgg-no-release")', self.workflow)
        self.assertIn('head.repo.full_name == $repo', self.workflow)

    def test_trusted_publisher_never_executes_pr_code_or_creates_apk(self):
        self.assertIn('ref: main', self.workflow)
        self.assertIn('ref: gpt-preview', self.workflow)
        self.assertIn('git/blobs/$blob', self.workflow)
        self.assertIn('git/trees/${tree}?recursive=1', self.workflow)
        for forbidden in ('assemblePreviewDebug', 'gradle ', 'npm ci', 'actions/upload-artifact',
                          'actions/checkout@v4\n        with:\n          ref: ${{',
                          'git push origin HEAD:main', 'publish_admin_beta', 'patient-live'):
            self.assertNotIn(forbidden, self.workflow)
        self.assertIn('git -C preview push origin HEAD:gpt-preview', self.workflow)

    def test_prevents_stale_or_duplicate_preview_and_rechecks_before_push(self):
        self.assertIn('new_version < current_version', self.workflow)
        self.assertIn('SOURCE_SHA" == "$current_sha', self.workflow)
        self.assertIn('SOURCE_RUN <= current_run', self.workflow)
        self.assertIn('test ! -e "preview/previews/$request_id"', self.workflow)
        self.assertIn('git -C preview fetch --no-tags origin gpt-preview', self.workflow)
        self.assertIn('gh api "repos/$GITHUB_REPOSITORY/pulls/$SOURCE_PR"', self.workflow)
        self.assertIn('sha256sum "$RUNNER_TEMP/kgg-verified-published.html"', self.workflow)

    def test_checkout_actions_are_valid_and_separated(self):
        self.assertEqual(self.workflow.count('uses: actions/checkout@v4'), 2)
        self.assertNotIn('actions/checkout$v4', self.workflow)
        self.assertIn('ref: main\n          path: trusted\n          persist-credentials: false', self.workflow)
        self.assertIn('ref: gpt-preview\n          path: preview', self.workflow)

    def test_only_test_channel_has_write_permissions(self):
        self.assertIn('group: kgg-gpt-preview-publish', self.workflow)
        self.assertIn('contents: write', self.workflow)
        self.assertNotIn('secrets:', self.workflow)
        self.assertNotIn('patient-preview', self.workflow)
        self.assertNotIn('release-assets', self.workflow)


if __name__ == "__main__":
    unittest.main()
