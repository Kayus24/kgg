"""Contracts for the separate verified patient PR preview."""
import copy
import tempfile
import unittest
from pathlib import Path

import kgg_patient_pr_preview as preview


class PatientPrPreviewTests(unittest.TestCase):
    def setUp(self):
        self.sha = "1" * 40
        self.base = "2" * 40
        repo = {"full_name": preview.REPO}
        self.pr = {
            "id": 123, "number": 375, "state": "open",
            "head": {"sha": self.sha, "repo": repo, "ref": "fix/patient"},
            "base": {"sha": self.base, "repo": repo, "ref": "main"},
            "labels": [{"name": "kgg-no-release"}],
        }
        self.run = {
            "id": 456, "head_sha": self.sha, "head_repository": repo,
            "event": "pull_request", "path": preview.REQUIRED_PATH,
            "workflow_id": preview.REQUIRED_ID, "status": "completed",
            "conclusion": "success", "run_attempt": 1,
            "pull_requests": [{"id": 123, "number": 375, "base": {"sha": self.base}}],
        }
        self.jobs = [{"name": "required-gate", "status": "completed", "conclusion": "success"}]

    def verify(self, pr=None, run=None, jobs=None):
        return preview.verify_binding(
            self.pr if pr is None else pr, self.run if run is None else run,
            self.jobs if jobs is None else jobs, 375, self.sha, 456, self.base,
        )

    def test_valid_binding(self):
        self.assertEqual(self.verify(), 1)

    def test_pr_drift_and_missing_scope(self):
        for side, field, value in (
            ("head", "sha", "3" * 40), ("head", "repo", {"full_name": "fork/kgg"}),
            ("base", "sha", "3" * 40), ("base", "ref", "other"),
        ):
            with self.subTest(side=side, field=field):
                pr = copy.deepcopy(self.pr)
                pr[side][field] = value
                with self.assertRaises(ValueError):
                    self.verify(pr=pr)
        with self.assertRaises(ValueError):
            self.verify(pr={**self.pr, "labels": []})

    def test_ci_failed_unknown_or_wrong_run(self):
        for field, value in (
            ("id", 457), ("conclusion", "failure"), ("conclusion", None),
            ("pull_requests", []), ("workflow_id", 0), ("head_sha", self.base),
        ):
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.verify(run={**self.run, field: value})
        with self.assertRaises(ValueError):
            self.verify(jobs=[])

    def test_replay_and_transport_integrity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            candidate = root / "candidate"
            candidate.mkdir()
            (candidate / "index.html").write_bytes(b"synthetic")
            expected = preview.file_hashes(candidate)
            (candidate / "index.html").write_bytes(b"drift")
            with self.assertRaises(ValueError):
                preview.verify_files(candidate, expected)
            (root / "previews" / "pr-375").mkdir(parents=True)
            with self.assertRaises(ValueError):
                preview.require_new(root, "pr-375")

    def test_workflow_uses_registered_main_and_separates_write_credentials(self):
        workflow = preview.ROOT / ".github/workflows/kgg-patient-pr-preview.yml"
        stage, publish = workflow.read_text().split("\n  publish:\n")
        self.assertIn("refs/heads/main", stage)
        self.assertIn("persist-credentials: false", stage)
        self.assertNotIn("secrets.", stage)
        self.assertNotIn("inputs.expected_head_sha }}\n          path:", stage)
        self.assertNotIn("npm ", publish)
        self.assertNotIn("node release-pipeline", publish)
        self.assertIn("KGG_PATIENT_PREVIEW_PUBLISH_TOKEN", publish)


if __name__ == "__main__":
    unittest.main()
