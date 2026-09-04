#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import kgg_admin_editor_sync_candidate as candidate
import kgg_admin_editor_sync_preflight as preflight


class AdminEditorSyncPreflightTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="kgg-admin-editor-preflight-")
        self.root = Path(self.temp.name)
        (self.root / "docs").mkdir(parents=True)
        self.snapshot = self.root / "docs" / "kgg-custom-gpt-editor-snapshot.json"
        self.snapshot.write_text(
            json.dumps({"syncStatus": "target-pending-live-editor-sync"}) + "\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def run_case(
        self,
        *,
        audit_runner,
        candidate_builder,
        main_shas: list[str] | None = None,
        checkout_sha: str = "a" * 40,
        worktree_values: list[str] | None = None,
    ) -> dict:
        main_values = iter(main_shas or ["a" * 40, "a" * 40])
        worktree_values_iter = iter(worktree_values or ["", ""])
        return preflight.run_preflight(
            "admin-sync-001",
            repo_root=self.root,
            snapshot_path=self.snapshot,
            default_branch_reader=lambda: "main",
            current_main_sha_reader=lambda _root, _branch: next(main_values),
            checkout_sha_reader=lambda _root: checkout_sha,
            worktree_reader=lambda _root: next(worktree_values_iter),
            audit_runner=audit_runner,
            candidate_builder=candidate_builder,
        )

    def test_target_pass_to_live_pass_is_would_certify_without_write(self) -> None:
        before = self.snapshot.read_bytes()

        result = self.run_case(
            audit_runner=lambda *_args, **_kwargs: {"status": "TARGET_PASS"},
            candidate_builder=lambda **_kwargs: {
                "status": "LIVE_PASS",
                "changedFields": sorted(candidate.ALLOWED_CERTIFICATION_FIELDS),
                "candidate": {"must": "not leak"},
            },
        )

        self.assertEqual("would_certify", result["preflightStatus"])
        self.assertEqual("TARGET_PASS", result["resourceAudit"])
        self.assertEqual("LIVE_PASS", result["candidateAudit"])
        self.assertEqual(
            candidate.ALLOWED_CERTIFICATION_FIELDS,
            set(result["changedFields"]),
        )
        self.assertTrue(result["snapshotUnchanged"])
        self.assertFalse(result["repositoryWriteDetected"])
        self.assertEqual(before, self.snapshot.read_bytes())
        self.assertNotIn("candidate", result)

    def test_resource_drift_is_stale_context(self) -> None:
        before = self.snapshot.read_bytes()

        def mismatching_audit(*_args, **_kwargs):
            raise candidate.CandidateError("Knowledge digest mismatch")

        result = self.run_case(
            audit_runner=mismatching_audit,
            candidate_builder=lambda **_kwargs: self.fail("candidate must not run"),
        )

        self.assertEqual("stale_context", result["preflightStatus"])
        self.assertEqual("FAIL", result["resourceAudit"])
        self.assertEqual(before, self.snapshot.read_bytes())

    def test_main_drift_is_stale_base(self) -> None:
        result = self.run_case(
            audit_runner=lambda *_args, **_kwargs: {"status": "TARGET_PASS"},
            candidate_builder=lambda **_kwargs: {
                "status": "LIVE_PASS",
                "changedFields": sorted(candidate.ALLOWED_CERTIFICATION_FIELDS),
            },
            main_shas=["a" * 40, "b" * 40],
        )

        self.assertEqual("stale_base", result["preflightStatus"])
        self.assertEqual("a" * 40, result["startMainSha"])
        self.assertEqual("b" * 40, result["endMainSha"])
        self.assertFalse(result["repositoryWriteDetected"])

    def test_live_base_is_no_change(self) -> None:
        result = self.run_case(
            audit_runner=lambda *_args, **_kwargs: {"status": "LIVE_PASS"},
            candidate_builder=lambda **_kwargs: self.fail("candidate must not run"),
        )

        self.assertEqual("no_change", result["preflightStatus"])
        self.assertEqual("LIVE_PASS", result["resourceAudit"])
        self.assertEqual("not_run", result["candidateAudit"])
        self.assertEqual([], result["changedFields"])

    def test_snapshot_or_repository_mutation_is_failed(self) -> None:
        def mutating_builder(**_kwargs):
            self.snapshot.write_text("{}\n", encoding="utf-8")
            return {
                "status": "LIVE_PASS",
                "changedFields": sorted(candidate.ALLOWED_CERTIFICATION_FIELDS),
            }

        result = self.run_case(
            audit_runner=lambda *_args, **_kwargs: {"status": "TARGET_PASS"},
            candidate_builder=mutating_builder,
            worktree_values=["", " M docs/kgg-custom-gpt-editor-snapshot.json"],
        )

        self.assertEqual("failed", result["preflightStatus"])
        self.assertTrue(result["repositoryWriteDetected"])
        self.assertFalse(result["snapshotUnchanged"])

    def test_wrong_candidate_field_set_is_failed(self) -> None:
        result = self.run_case(
            audit_runner=lambda *_args, **_kwargs: {"status": "TARGET_PASS"},
            candidate_builder=lambda **_kwargs: {
                "status": "LIVE_PASS",
                "changedFields": ["syncStatus"],
            },
        )

        self.assertEqual("failed", result["preflightStatus"])
        self.assertEqual("FAIL", result["candidateAudit"])

    def test_workflow_is_read_only_and_has_only_request_id_input(self) -> None:
        workflow = (
            HERE.parent / ".github" / "workflows" / "kgg-admin-editor-sync-preflight.yml"
        ).read_text(encoding="utf-8")

        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertNotIn("contents: write", workflow)
        self.assertNotIn("pull-requests: write", workflow)
        self.assertNotIn("issues: write", workflow)
        self.assertIn("request_id:", workflow)
        for forbidden_input in (
            "source_sha:",
            "timestamp:",
            "snapshot_path:",
            "payload_json:",
            "branch:",
            "approval_phrase:",
        ):
            self.assertNotIn(forbidden_input, workflow)
        for forbidden_write in (
            "git push",
            "git commit",
            "git checkout -b",
            "git switch -c",
            "gh pr",
            "create-pull-request",
            "refresh-target-profile",
            "publish_preview",
            "publish_admin_beta",
        ):
            self.assertNotIn(forbidden_write, workflow)
        self.assertIn("actions/upload-artifact@v4", workflow)
        self.assertIn("github.event.repository.default_branch", workflow)
        self.assertIn("${{ runner.temp }}", workflow)
        self.assertNotIn("kgg-custom-gpt-action-api-openapi.yaml", workflow)


if __name__ == "__main__":
    unittest.main(verbosity=2)
