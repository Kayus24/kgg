"""Read-only quick test APK workflow contract and separation regression tests."""
from pathlib import Path
import re
import unittest

WORKFLOW = Path(__file__).resolve().parents[1] / ".github/workflows/android-wrapper-check.yml"


def jobs(text: str) -> dict[str, str]:
    pieces = re.split(r"(?m)^  ([a-z][a-z0-9-]+):\s*$", text.split("\njobs:\n", 1)[1])
    return {pieces[i]: pieces[i + 1] for i in range(1, len(pieces), 2)}


class QuickPreviewApkWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = WORKFLOW.read_text(encoding="utf-8")
        cls.jobs = jobs(cls.text)

    def test_existing_pr_guard_and_one_input_dispatch(self) -> None:
        self.assertIn("  workflow_dispatch:\n    inputs:\n      source_pr:", self.text)
        self.assertIn("if: github.event_name == 'pull_request'", self.jobs["build-and-separate-profiles"])
        self.assertEqual(set(self.jobs), {"build-and-separate-profiles", "quick-pr-source", "quick-preview-debug"})
        self.assertIn("if: github.event_name == 'workflow_dispatch'", self.jobs["quick-pr-source"])
        self.assertIn("if: github.event_name == 'workflow_dispatch'", self.jobs["quick-preview-debug"])

    def test_trusted_resolver_cannot_execute_pr_code(self) -> None:
        resolver = self.jobs["quick-pr-source"]
        self.assertIn("pull-requests: read", resolver)
        self.assertIn("GH_TOKEN: ${{ github.token }}", resolver)
        self.assertIn('test "$GITHUB_REF_NAME" = "main"', resolver)
        self.assertIn("gh api", resolver)
        self.assertIn(".head.repo.full_name == $repo", resolver)
        self.assertIn(".base.repo.full_name == $repo", resolver)
        self.assertNotIn("actions/checkout", resolver)
        self.assertNotIn("gradle ", resolver)

    def test_untrusted_build_has_no_privileged_credentials(self) -> None:
        quick = self.jobs["quick-preview-debug"]
        for forbidden in ("GH_TOKEN", "github.token", "pull-requests: read", "contents: write",
                          "gh api", "git push", "gh release", "assembleAdmin", "assembleKollegen",
                          "publish", "deploy", "actions/download-artifact"):
            self.assertNotIn(forbidden, quick)
        self.assertIn("needs: quick-pr-source", quick)
        self.assertIn("persist-credentials: false", quick)
        self.assertIn("ref: ${{ needs.quick-pr-source.outputs.sha }}", quick)
        self.assertIn('test "$(git rev-parse HEAD)" = "$SOURCE_SHA"', quick)

    def test_quick_apk_stays_a_verifiable_preview_debug(self) -> None:
        quick = self.jobs["quick-preview-debug"]
        self.assertIn("assemblePreviewDebug", quick)
        self.assertIn('= de.kgg.preview', quick)
        self.assertIn('"$SIGNER" verify --verbose "$APK"', quick)
        self.assertIn('context["commitSha"] == sys.argv[2]', quick)
        self.assertIn("assets/android/kgg_preview_context.js", quick)
        self.assertIn("cache-disabled: true", quick)
        self.assertNotIn("KGG_PREVIEW_TEST_APPLICATION_ID", quick)

    def test_only_unapproved_short_lived_artifact_is_exported(self) -> None:
        quick = self.jobs["quick-preview-debug"]
        self.assertIn("actions/upload-artifact@v4", quick)
        self.assertIn("name: unapproved-quick-pr-", quick)
        self.assertIn("retention-days: 7", quick)
        self.assertIn("if-no-files-found: error", quick)
        self.assertNotIn("kgg-preview-approved", quick)
        self.assertNotIn("approved-pr-", quick)
        self.assertNotIn("actions/create-release", quick)


if __name__ == "__main__":
    unittest.main()
