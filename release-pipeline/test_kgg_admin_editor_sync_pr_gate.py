#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import kgg_admin_editor_sync_pr_gate as gate
import kgg_custom_gpt_resource_audit as audit


class AdminEditorSyncPrGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="kgg-admin-editor-sync-pr-")
        self.root = Path(self.temp.name)
        self.snapshot = self.root / gate.SNAPSHOT_REL
        self.snapshot.parent.mkdir(parents=True)
        self.base_document = {
            "gptId": "g-0123456789abcdef",
            "name": "KGG Update-Agent",
            "profileVersion": "4.2.0",
            "bootstrapVersion": "admin-v8",
            "model": "GPT-5.6 Thinking",
            "visibility": "private",
            "syncStatus": audit.TARGET_PENDING_SYNC_STATUS,
            "capabilities": {
                "webSearch": True,
                "codeInterpreter": True,
                "imageGeneration": True,
                "canvas": False,
                "apps": False,
                "actions": True,
            },
            "instructionsSha256": "a" * 64,
            "knowledgeSha256": ["b" * 64, "c" * 64],
            "actionSha256": ["d" * 64, "e" * 64],
        }
        self.snapshot.write_text(
            json.dumps(self.base_document, indent=2) + "\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def init_git_repo(self) -> str:
        subprocess.run(["git", "init", "-q"], cwd=self.root, check=True)
        subprocess.run(
            ["git", "config", "user.email", "tests@example.invalid"],
            cwd=self.root,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "KGG Tests"],
            cwd=self.root,
            check=True,
        )
        subprocess.run(["git", "add", "."], cwd=self.root, check=True)
        subprocess.run(
            ["git", "commit", "-q", "-m", "base"],
            cwd=self.root,
            check=True,
        )
        return subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=self.root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()

    def phase2a_would_certify(self) -> dict:
        return {
            "preflightStatus": "would_certify",
            "startMainSha": "a" * 40,
            "resourceAudit": audit.TARGET_PASS,
            "candidateAudit": audit.LIVE_PASS,
            "changedFields": sorted(gate.candidate.ALLOWED_CERTIFICATION_FIELDS),
        }

    def live_candidate(self) -> dict:
        document = dict(self.base_document)
        document.update(
            {
                "syncStatus": audit.LIVE_SYNC_STATUS,
                "lastVerifiedAt": "2026-09-03T19:17:00Z",
                "lastVerifiedMainCommit": "a" * 40,
            }
        )
        return {
            "status": audit.LIVE_PASS,
            "changedFields": sorted(gate.candidate.ALLOWED_CERTIFICATION_FIELDS),
            "candidate": document,
        }

    def common_gate_patches(self):
        return [
            mock.patch.object(gate.preflight, "read_default_branch", return_value="main"),
            mock.patch.object(gate, "read_repository_name", return_value="Kayus24/kgg"),
        ]

    def test_wrong_approval_phrase_blocks_before_any_write(self) -> None:
        with mock.patch.object(
            gate.preflight, "run_preflight"
        ) as phase2a, mock.patch.object(
            gate, "create_snapshot_branch_and_pr"
        ) as writer:
            result = gate.run_gate(
                "admin-sync-001",
                "gut für main",
                repo_root=self.root,
                snapshot_path=self.snapshot,
            )

        self.assertEqual("approval_required", result["endStatus"])
        phase2a.assert_not_called()
        writer.assert_not_called()

    def test_target_pass_is_required(self) -> None:
        patches = self.common_gate_patches()
        with patches[0], patches[1], mock.patch.object(
            gate.preflight,
            "run_preflight",
            return_value={
                "preflightStatus": "would_certify",
                "startMainSha": "a" * 40,
                "resourceAudit": audit.LIVE_PASS,
                "candidateAudit": audit.LIVE_PASS,
                "changedFields": sorted(gate.candidate.ALLOWED_CERTIFICATION_FIELDS),
            },
        ), mock.patch.object(gate, "create_snapshot_branch_and_pr") as writer:
            result = gate.run_gate(
                "admin-sync-001",
                gate.APPROVAL_PHRASE,
                repo_root=self.root,
                snapshot_path=self.snapshot,
            )

        self.assertEqual("failed", result["endStatus"])
        self.assertIn("Phase-2A evidence contract", result["error"])
        writer.assert_not_called()

    def test_candidate_must_keep_live_pass(self) -> None:
        patches = self.common_gate_patches()
        with patches[0], patches[1], mock.patch.object(
            gate.preflight,
            "run_preflight",
            return_value=self.phase2a_would_certify(),
        ), mock.patch.object(
            gate, "find_existing_request_pr", return_value=None
        ), mock.patch.object(
            gate, "remote_branch_exists", return_value=False
        ), mock.patch.object(
            gate.candidate,
            "build_candidate",
            return_value={"status": "candidate_invalid", "error": "strict audit failed"},
        ), mock.patch.object(gate, "create_snapshot_branch_and_pr") as writer:
            result = gate.run_gate(
                "admin-sync-001",
                gate.APPROVAL_PHRASE,
                repo_root=self.root,
                snapshot_path=self.snapshot,
            )

        self.assertEqual("failed", result["endStatus"])
        self.assertEqual("candidate_invalid", result["candidateAudit"])
        writer.assert_not_called()

    def test_main_drift_before_write_is_stale_base(self) -> None:
        patches = self.common_gate_patches()
        with patches[0], patches[1], mock.patch.object(
            gate.preflight,
            "run_preflight",
            return_value=self.phase2a_would_certify(),
        ), mock.patch.object(
            gate, "find_existing_request_pr", return_value=None
        ), mock.patch.object(
            gate, "remote_branch_exists", return_value=False
        ), mock.patch.object(
            gate.candidate,
            "build_candidate",
            return_value=self.live_candidate(),
        ), mock.patch.object(
            gate.preflight,
            "read_current_main_sha",
            return_value="f" * 40,
        ), mock.patch.object(gate, "create_snapshot_branch_and_pr") as writer:
            result = gate.run_gate(
                "admin-sync-001",
                gate.APPROVAL_PHRASE,
                repo_root=self.root,
                snapshot_path=self.snapshot,
            )

        self.assertEqual("stale_base", result["endStatus"])
        self.assertEqual("f" * 40, result["preWriteMainSha"])
        writer.assert_not_called()

    def test_duplicate_request_returns_existing_open_pr(self) -> None:
        patches = self.common_gate_patches()
        existing = {
            "number": 234,
            "url": "https://github.com/Kayus24/kgg/pull/234",
            "state": "OPEN",
        }
        with patches[0], patches[1], mock.patch.object(
            gate.preflight,
            "run_preflight",
            return_value=self.phase2a_would_certify(),
        ), mock.patch.object(
            gate, "find_existing_request_pr", return_value=existing
        ), mock.patch.object(
            gate.candidate, "build_candidate"
        ) as builder, mock.patch.object(
            gate, "create_snapshot_branch_and_pr"
        ) as writer:
            result = gate.run_gate(
                "admin-sync-001",
                gate.APPROVAL_PHRASE,
                repo_root=self.root,
                snapshot_path=self.snapshot,
            )

        self.assertEqual("existing_pr", result["endStatus"])
        self.assertEqual(234, result["prNumber"])
        builder.assert_not_called()
        writer.assert_not_called()

    def test_already_live_synced_is_no_change(self) -> None:
        patches = self.common_gate_patches()
        with patches[0], patches[1], mock.patch.object(
            gate.preflight,
            "run_preflight",
            return_value={
                "preflightStatus": "no_change",
                "startMainSha": "a" * 40,
                "resourceAudit": audit.LIVE_PASS,
                "candidateAudit": "not_run",
                "changedFields": [],
            },
        ), mock.patch.object(
            gate, "find_existing_request_pr"
        ) as lookup, mock.patch.object(
            gate, "create_snapshot_branch_and_pr"
        ) as writer:
            result = gate.run_gate(
                "admin-sync-001",
                gate.APPROVAL_PHRASE,
                repo_root=self.root,
                snapshot_path=self.snapshot,
            )

        self.assertEqual("no_change", result["endStatus"])
        lookup.assert_not_called()
        writer.assert_not_called()

    def test_main_drift_after_local_write_cleans_branch_before_commit(self) -> None:
        base_sha = self.init_git_repo()
        branch_name = "admin-editor-sync/admin-sync-001"
        document = dict(self.base_document)
        document.update(
            {
                "syncStatus": audit.LIVE_SYNC_STATUS,
                "lastVerifiedAt": "2026-09-03T19:17:00Z",
                "lastVerifiedMainCommit": base_sha,
            }
        )

        with mock.patch.object(
            gate.candidate,
            "run_canonical_audit",
            return_value={"status": audit.LIVE_PASS},
        ), mock.patch.object(
            gate.preflight,
            "read_current_main_sha",
            return_value="f" * 40,
        ):
            result = gate.create_snapshot_branch_and_pr(
                request_id="admin-sync-001",
                repository="Kayus24/kgg",
                branch_name=branch_name,
                base_sha=base_sha,
                candidate_document=document,
                repo_root=self.root,
                snapshot_path=self.snapshot,
            )

        self.assertEqual("stale_base", result["status"])
        branch_list = subprocess.run(
            ["git", "branch", "--list", branch_name],
            cwd=self.root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        self.assertEqual("", branch_list)
        commit_count = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            cwd=self.root,
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        self.assertEqual("1", commit_count)
        self.assertEqual(
            json.dumps(self.base_document, indent=2) + "\n",
            self.snapshot.read_text(encoding="utf-8"),
        )

    def test_snapshot_only_diff_accepts_exact_three_fields(self) -> None:
        base_sha = self.init_git_repo()
        document = dict(self.base_document)
        document.update(
            {
                "syncStatus": audit.LIVE_SYNC_STATUS,
                "lastVerifiedAt": "2026-09-03T19:17:00Z",
                "lastVerifiedMainCommit": base_sha,
            }
        )
        gate.write_snapshot_file(self.snapshot, document)

        fields = gate.validate_snapshot_only_worktree(
            self.root,
            base_sha=base_sha,
            snapshot_path=self.snapshot,
        )

        self.assertEqual(
            gate.candidate.ALLOWED_CERTIFICATION_FIELDS,
            set(fields),
        )

    def test_second_changed_file_hard_fails(self) -> None:
        base_sha = self.init_git_repo()
        document = dict(self.base_document)
        document.update(
            {
                "syncStatus": audit.LIVE_SYNC_STATUS,
                "lastVerifiedAt": "2026-09-03T19:17:00Z",
                "lastVerifiedMainCommit": base_sha,
            }
        )
        gate.write_snapshot_file(self.snapshot, document)
        (self.root / "forbidden.txt").write_text("forbidden\n", encoding="utf-8")

        with self.assertRaisesRegex(gate.PrGateError, "exactly one file"):
            gate.validate_snapshot_only_worktree(
                self.root,
                base_sha=base_sha,
                snapshot_path=self.snapshot,
            )

    def test_fourth_snapshot_field_hard_fails(self) -> None:
        base_sha = self.init_git_repo()
        document = dict(self.base_document)
        document.update(
            {
                "syncStatus": audit.LIVE_SYNC_STATUS,
                "lastVerifiedAt": "2026-09-03T19:17:00Z",
                "lastVerifiedMainCommit": base_sha,
                "unexpectedCertificationField": True,
            }
        )
        gate.write_snapshot_file(self.snapshot, document)

        with self.assertRaisesRegex(gate.PrGateError, "exactly the three"):
            gate.validate_snapshot_only_worktree(
                self.root,
                base_sha=base_sha,
                snapshot_path=self.snapshot,
            )

    def test_workflow_has_minimal_write_permissions_and_no_merge_surface(self) -> None:
        workflow = (
            HERE.parent
            / ".github"
            / "workflows"
            / "kgg-admin-editor-sync-snapshot-pr.yml"
        ).read_text(encoding="utf-8")
        source = (HERE / "kgg_admin_editor_sync_pr_gate.py").read_text(encoding="utf-8")

        self.assertIn("permissions:\n  contents: write\n  pull-requests: write", workflow)
        self.assertNotIn("issues: write", workflow)
        self.assertNotIn("actions: write", workflow)
        self.assertNotIn("deployments: write", workflow)
        self.assertIn("request_id:", workflow)
        self.assertIn("approval_phrase:", workflow)
        for forbidden_input in (
            "source_sha:",
            "timestamp:",
            "snapshot_path:",
            "payload_json:",
            "resource_hash",
            "branch_name:",
            "commit_content:",
        ):
            self.assertNotIn(forbidden_input, workflow)
        for forbidden in (
            "gh pr merge",
            "--auto",
            "HEAD:main",
            "publish_preview",
            "publish_admin_beta",
            "refresh-target-profile",
        ):
            self.assertNotIn(forbidden, workflow)
            self.assertNotIn(forbidden, source)
        self.assertNotIn("kgg-custom-gpt-action-api-openapi.yaml", workflow)
        self.assertNotIn("kgg-custom-gpt-action-api-openapi.yaml", source)


if __name__ == "__main__":
    unittest.main(verbosity=2)
