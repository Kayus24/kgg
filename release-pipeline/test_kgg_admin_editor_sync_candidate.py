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
import kgg_custom_gpt_resource_audit as audit


class AdminEditorSyncCandidateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="kgg-admin-editor-sync-")
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def snapshot(self, **extra: object) -> Path:
        expected = audit.expected_manifest()["production"]
        document = {
            "gptId": "g-0123456789abcdef",
            "name": expected["name"],
            "profileVersion": expected["profileVersion"],
            "bootstrapVersion": expected["editorBootstrap"]["version"],
            "model": audit.HIGHEST_ACTIONS_COMPATIBLE_MODEL,
            "visibility": expected["visibility"],
            "syncStatus": audit.TARGET_PENDING_SYNC_STATUS,
            "capabilities": expected["capabilities"],
            "instructionsSha256": expected["editorBootstrap"]["sha256"],
            "knowledgeSha256": [item["sha256"] for item in expected["knowledge"]],
            "actionSha256": [item["sha256"] for item in expected["actions"]],
        }
        document.update(extra)
        path = self.root / "snapshot.json"
        path.write_text(json.dumps(document), encoding="utf-8")
        return path

    def audit_runner(
        self,
        path: Path,
        *,
        require_live_synced: bool,
        repo_root: Path,
    ) -> dict:
        del repo_root
        try:
            status = audit.validate_snapshot(
                path,
                "production",
                require_live_synced=require_live_synced,
            )
        except audit.AuditError as exc:
            raise candidate.CandidateError(str(exc)) from exc
        return {"status": status}

    def test_candidate_uses_server_values_and_changes_only_certification_fields(self) -> None:
        snapshot = self.snapshot()
        before = snapshot.read_bytes()
        result = candidate.build_candidate(
            repo_root=self.root,
            snapshot_path=snapshot,
            main_sha_reader=lambda _: "b" * 40,
            now_reader=lambda: "2026-09-03T17:42:31Z",
            audit_runner=self.audit_runner,
        )

        self.assertEqual("LIVE_PASS", result["status"])
        self.assertEqual("b" * 40, result["mainSha"])
        self.assertEqual("2026-09-03T17:42:31Z", result["lastVerifiedAt"])
        self.assertEqual(
            {
                "syncStatus",
                "lastVerifiedAt",
                "lastVerifiedMainCommit",
            },
            set(result["changedFields"]),
        )
        self.assertEqual(audit.LIVE_SYNC_STATUS, result["candidate"]["syncStatus"])
        self.assertEqual(
            audit.LIVE_PASS,
            self.audit_runner_for_document(result["candidate"]),
        )
        self.assertEqual(before, snapshot.read_bytes())

    def audit_runner_for_document(self, document: dict) -> str:
        path = self.root / "candidate.json"
        path.write_text(json.dumps(document), encoding="utf-8")
        return audit.validate_snapshot(
            path,
            "production",
            require_live_synced=True,
        )

    def test_resource_mismatch_returns_stale_context_without_snapshot_write(self) -> None:
        snapshot = self.snapshot(knowledgeSha256=["0" * 64])
        before = snapshot.read_bytes()
        result = candidate.build_candidate(
            repo_root=self.root,
            snapshot_path=snapshot,
            main_sha_reader=lambda _: "b" * 40,
            now_reader=lambda: "2026-09-03T17:42:31Z",
            audit_runner=self.audit_runner,
        )

        self.assertEqual("stale_context", result["status"])
        self.assertEqual(before, snapshot.read_bytes())

    def test_non_target_base_is_blocked_before_candidate_generation(self) -> None:
        snapshot = self.snapshot(
            syncStatus=audit.LIVE_SYNC_STATUS,
            lastVerifiedAt="2026-09-03T17:42:31Z",
            lastVerifiedMainCommit="b" * 40,
        )
        before = snapshot.read_bytes()
        result = candidate.build_candidate(
            repo_root=self.root,
            snapshot_path=snapshot,
            main_sha_reader=lambda _: "c" * 40,
            now_reader=lambda: "2026-09-03T18:00:00Z",
            audit_runner=self.audit_runner,
        )

        self.assertEqual("stale_context", result["status"])
        self.assertEqual(before, snapshot.read_bytes())


if __name__ == "__main__":
    unittest.main(verbosity=2)
