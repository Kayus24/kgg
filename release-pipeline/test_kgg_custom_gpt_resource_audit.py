#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path
from unittest import mock


HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import kgg_custom_gpt_resource_audit as audit


class CustomGptResourceAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="kgg-gpt-resource-audit-")
        self.root = Path(self.temp.name)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def snapshot(
        self, *, sync_status: str, profile: str = "production", **extra: object
    ) -> Path:
        expected = audit.expected_manifest()[profile]
        document = {
            "gptId": "g-0123456789abcdef",
            "name": expected["name"],
            "profileVersion": expected["profileVersion"],
            "bootstrapVersion": expected["editorBootstrap"]["version"],
            "model": audit.HIGHEST_ACTIONS_COMPATIBLE_MODEL,
            "visibility": expected["visibility"],
            "syncStatus": sync_status,
            "capabilities": expected["capabilities"],
            "instructionsSha256": expected["editorBootstrap"]["sha256"],
            "knowledgeSha256": [item["sha256"] for item in expected["knowledge"]],
            "actionSha256": [item["sha256"] for item in expected["actions"]],
        }
        document.update(extra)
        path = self.root / "snapshot.json"
        path.write_text(json.dumps(document), encoding="utf-8")
        return path

    def test_production_profile_version_is_4_2_0(self) -> None:
        self.assertEqual("4.2.0", audit.expected_manifest()["production"]["profileVersion"])

    def test_pending_snapshot_is_an_explicit_target_pass(self) -> None:
        path = self.snapshot(sync_status=audit.TARGET_PENDING_SYNC_STATUS)

        self.assertEqual(audit.TARGET_PASS, audit.validate_snapshot(path, "production"))
        self.assertNotEqual(audit.LIVE_PASS, audit.validate_snapshot(path, "production"))

    def test_strict_mode_rejects_pending_target(self) -> None:
        path = self.snapshot(sync_status=audit.TARGET_PENDING_SYNC_STATUS)

        with self.assertRaisesRegex(audit.AuditError, "only a validated target"):
            audit.validate_snapshot(path, "production", require_live_synced=True)

    def test_live_snapshot_returns_live_pass_with_valid_evidence(self) -> None:
        path = self.snapshot(
            sync_status=audit.LIVE_SYNC_STATUS,
            lastVerifiedAt="2026-08-11T08:09:10.123Z",
            lastVerifiedMainCommit="0123456789abcdef0123456789abcdef01234567",
        )

        self.assertEqual(
            audit.LIVE_PASS,
            audit.validate_snapshot(path, "production", require_live_synced=True),
        )

    def test_live_snapshot_requires_real_rfc3339_utc_timestamp(self) -> None:
        invalid_values = [
            None,
            "2026-08-11 08:09:10Z",
            "2026-08-11T08:09:10+00:00",
            "2026-13-11T08:09:10Z",
        ]
        for value in invalid_values:
            with self.subTest(value=value):
                path = self.snapshot(
                    sync_status=audit.LIVE_SYNC_STATUS,
                    lastVerifiedAt=value,
                    lastVerifiedMainCommit="0123456789abcdef0123456789abcdef01234567",
                )
                with self.assertRaisesRegex(audit.AuditError, "RFC3339 UTC"):
                    audit.validate_snapshot(path, "production")

    def test_live_snapshot_requires_lowercase_40_character_main_commit(self) -> None:
        invalid_values = [
            None,
            "0123456",
            "0123456789ABCDEF0123456789ABCDEF01234567",
            "g123456789abcdef0123456789abcdef01234567",
        ]
        for value in invalid_values:
            with self.subTest(value=value):
                path = self.snapshot(
                    sync_status=audit.LIVE_SYNC_STATUS,
                    lastVerifiedAt="2026-08-11T08:09:10Z",
                    lastVerifiedMainCommit=value,
                )
                with self.assertRaisesRegex(audit.AuditError, "40-character lowercase"):
                    audit.validate_snapshot(path, "production")

    def test_unknown_sync_state_is_rejected(self) -> None:
        path = self.snapshot(sync_status="PASS")

        with self.assertRaisesRegex(audit.AuditError, "syncStatus must be"):
            audit.validate_snapshot(path, "production")

    def test_snapshot_requires_explicit_false_capabilities(self) -> None:
        path = self.snapshot(sync_status=audit.TARGET_PENDING_SYNC_STATUS)
        document = json.loads(path.read_text(encoding="utf-8"))
        document["capabilities"].pop("canvas")
        path.write_text(json.dumps(document), encoding="utf-8")

        with self.assertRaisesRegex(audit.AuditError, "capability mismatch: canvas"):
            audit.validate_snapshot(path, "production")

    def test_snapshot_rejects_duplicate_resource_hashes(self) -> None:
        path = self.snapshot(sync_status=audit.TARGET_PENDING_SYNC_STATUS)
        document = json.loads(path.read_text(encoding="utf-8"))
        document["knowledgeSha256"].append(document["knowledgeSha256"][0])
        path.write_text(json.dumps(document), encoding="utf-8")

        with self.assertRaisesRegex(audit.AuditError, "Knowledge digest mismatch"):
            audit.validate_snapshot(path, "production")

    def test_refresh_target_preserves_matching_admin_live_claim_byte_for_byte(self) -> None:
        path = self.snapshot(
            sync_status=audit.LIVE_SYNC_STATUS,
            lastVerifiedAt="2026-08-11T08:09:10Z",
            lastVerifiedMainCommit="0123456789abcdef0123456789abcdef01234567",
        )
        before = path.read_bytes()

        audit.refresh_target_snapshot(path, "production")

        self.assertEqual(before, path.read_bytes())
        refreshed = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(audit.LIVE_SYNC_STATUS, refreshed["syncStatus"])
        self.assertEqual("2026-08-11T08:09:10Z", refreshed["lastVerifiedAt"])
        self.assertEqual(
            "0123456789abcdef0123456789abcdef01234567",
            refreshed["lastVerifiedMainCommit"],
        )

    def test_refresh_target_invalidates_each_real_admin_target_drift(self) -> None:
        cases = {
            "profileVersion": "4.1.0",
            "knowledgeSha256": ["0" * 64],
            "actionSha256": ["1" * 64],
            "bootstrapVersion": "admin-v7",
            "instructionsSha256": "2" * 64,
        }
        for field, value in cases.items():
            with self.subTest(field=field):
                path = self.snapshot(
                    sync_status=audit.LIVE_SYNC_STATUS,
                    lastVerifiedAt="2026-08-11T08:09:10Z",
                    lastVerifiedMainCommit="0123456789abcdef0123456789abcdef01234567",
                    **{field: value},
                )

                audit.refresh_target_snapshot(path, "production")

                refreshed = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(
                    audit.TARGET_PENDING_SYNC_STATUS,
                    refreshed["syncStatus"],
                )
                self.assertNotIn("lastVerifiedAt", refreshed)
                self.assertNotIn("lastVerifiedMainCommit", refreshed)
                self.assertEqual(
                    audit.TARGET_PASS,
                    audit.validate_snapshot(path, "production"),
                )

    def test_refresh_target_updates_hashes_and_removes_live_claim(self) -> None:
        path = self.snapshot(
            sync_status=audit.LIVE_SYNC_STATUS,
            profileVersion="4.1.0",
            knowledgeSha256=["0" * 64],
            actionSha256=["1" * 64],
            lastVerifiedAt="2026-08-11T08:09:10Z",
            lastVerifiedMainCommit="0123456789abcdef0123456789abcdef01234567",
        )

        audit.refresh_target_snapshot(path, "production")

        refreshed = json.loads(path.read_text(encoding="utf-8"))
        expected = audit.expected_manifest()["production"]
        self.assertEqual("4.2.0", refreshed["profileVersion"])
        self.assertEqual(audit.TARGET_PENDING_SYNC_STATUS, refreshed["syncStatus"])
        self.assertEqual(
            [item["sha256"] for item in expected["knowledge"]],
            refreshed["knowledgeSha256"],
        )
        self.assertEqual(
            [item["sha256"] for item in expected["actions"]],
            refreshed["actionSha256"],
        )
        self.assertNotIn("lastVerifiedAt", refreshed)
        self.assertNotIn("lastVerifiedMainCommit", refreshed)
        self.assertEqual(audit.TARGET_PASS, audit.validate_snapshot(path, "production"))

    def test_refresh_target_rejects_wrong_gpt_identity(self) -> None:
        path = self.snapshot(sync_status=audit.TARGET_PENDING_SYNC_STATUS, name="Wrong GPT")

        with self.assertRaisesRegex(audit.AuditError, "GPT name mismatch"):
            audit.refresh_target_snapshot(path, "production")

    def test_patient_refresh_resets_live_claim_to_target_pending(self) -> None:
        path = self.snapshot(
            profile="patientProduction",
            sync_status=audit.LIVE_SYNC_STATUS,
            profileVersion="0.0.0",
            knowledgeSha256=["0" * 64],
            actionSha256=["1" * 64],
            lastVerifiedAt="2026-08-11T08:09:10Z",
            lastVerifiedMainCommit="0123456789abcdef0123456789abcdef01234567",
        )

        audit.refresh_target_snapshot(path, "patientProduction")

        refreshed = json.loads(path.read_text(encoding="utf-8"))
        expected = audit.expected_manifest()["patientProduction"]
        self.assertEqual(audit.TARGET_PENDING_SYNC_STATUS, refreshed["syncStatus"])
        self.assertEqual(expected["profileVersion"], refreshed["profileVersion"])
        self.assertEqual(
            [item["sha256"] for item in expected["knowledge"]],
            refreshed["knowledgeSha256"],
        )
        self.assertEqual(
            [item["sha256"] for item in expected["actions"]],
            refreshed["actionSha256"],
        )
        self.assertNotIn("lastVerifiedAt", refreshed)
        self.assertNotIn("lastVerifiedMainCommit", refreshed)
        self.assertEqual(
            audit.TARGET_PASS,
            audit.validate_snapshot(path, "patientProduction"),
        )
        with self.assertRaisesRegex(audit.AuditError, "live sync is required"):
            audit.validate_snapshot(
                path,
                "patientProduction",
                require_live_synced=True,
            )

    def test_cli_reports_target_pass_without_claiming_live_sync(self) -> None:
        snapshot = self.snapshot(sync_status=audit.TARGET_PENDING_SYNC_STATUS)
        manifest = self.root / "manifest.json"
        manifest.write_text(audit.normalize(audit.expected_manifest()), encoding="utf-8")
        stdout = StringIO()
        stderr = StringIO()
        argv = [
            "kgg_custom_gpt_resource_audit.py",
            "--check",
            "--editor-snapshot",
            str(snapshot),
            "--profile",
            "production",
        ]

        with mock.patch.object(audit, "OUTPUT", manifest), mock.patch.object(
            sys, "argv", argv
        ), redirect_stdout(stdout), redirect_stderr(stderr):
            result = audit.main()

        self.assertEqual(0, result, stderr.getvalue())
        self.assertEqual(audit.TARGET_PASS, json.loads(stdout.getvalue())["status"])

    def test_cli_strict_mode_reports_failure_for_pending_target(self) -> None:
        snapshot = self.snapshot(sync_status=audit.TARGET_PENDING_SYNC_STATUS)
        manifest = self.root / "manifest.json"
        manifest.write_text(audit.normalize(audit.expected_manifest()), encoding="utf-8")
        stdout = StringIO()
        stderr = StringIO()
        argv = [
            "kgg_custom_gpt_resource_audit.py",
            "--check",
            "--editor-snapshot",
            str(snapshot),
            "--profile",
            "production",
            "--require-live-synced",
        ]

        with mock.patch.object(audit, "OUTPUT", manifest), mock.patch.object(
            sys, "argv", argv
        ), redirect_stdout(stdout), redirect_stderr(stderr):
            result = audit.main()

        self.assertEqual(1, result)
        self.assertEqual("", stdout.getvalue())
        self.assertIn("live sync is required", stderr.getvalue())

    def test_cli_strict_mode_requires_explicit_snapshot_and_profile(self) -> None:
        stdout = StringIO()
        stderr = StringIO()
        argv = [
            "kgg_custom_gpt_resource_audit.py",
            "--check",
            "--require-live-synced",
        ]

        with mock.patch.object(sys, "argv", argv), redirect_stdout(
            stdout
        ), redirect_stderr(stderr):
            result = audit.main()

        self.assertEqual(1, result)
        self.assertEqual("", stdout.getvalue())
        self.assertIn("requires --editor-snapshot and --profile", stderr.getvalue())

    def test_cli_self_test_rejects_snapshot_validation_flags(self) -> None:
        snapshot = self.snapshot(sync_status=audit.TARGET_PENDING_SYNC_STATUS)
        stdout = StringIO()
        stderr = StringIO()
        argv = [
            "kgg_custom_gpt_resource_audit.py",
            "--self-test",
            "--editor-snapshot",
            str(snapshot),
            "--profile",
            "production",
            "--require-live-synced",
        ]

        with mock.patch.object(sys, "argv", argv), redirect_stdout(
            stdout
        ), redirect_stderr(stderr):
            result = audit.main()

        self.assertEqual(1, result)
        self.assertEqual("", stdout.getvalue())
        self.assertIn("cannot be combined", stderr.getvalue())

    def test_atomic_write_preserves_existing_file_when_replace_fails(self) -> None:
        target = self.root / "atomic.json"
        target.write_text("old\n", encoding="utf-8")
        before = set(self.root.iterdir())

        with mock.patch.object(Path, "replace", side_effect=OSError("blocked")):
            with self.assertRaisesRegex(OSError, "blocked"):
                audit.atomic_write_text(target, "new\n")

        self.assertEqual("old\n", target.read_text(encoding="utf-8"))
        self.assertEqual(before, set(self.root.iterdir()))

    def test_cli_refresh_preserves_matching_live_snapshot(self) -> None:
        snapshot = self.snapshot(
            sync_status=audit.LIVE_SYNC_STATUS,
            lastVerifiedAt="2026-08-11T08:09:10Z",
            lastVerifiedMainCommit="0123456789abcdef0123456789abcdef01234567",
        )
        before = snapshot.read_bytes()
        manifest = self.root / "manifest.json"
        stdout = StringIO()
        stderr = StringIO()
        argv = [
            "kgg_custom_gpt_resource_audit.py",
            "--refresh-target-profile",
            "production",
            "--editor-snapshot",
            str(snapshot),
        ]

        with mock.patch.object(audit, "OUTPUT", manifest), mock.patch.object(
            sys, "argv", argv
        ), redirect_stdout(stdout), redirect_stderr(stderr):
            result = audit.main()

        self.assertEqual(0, result, stderr.getvalue())
        self.assertEqual(audit.LIVE_PASS, json.loads(stdout.getvalue())["status"])
        self.assertEqual(before, snapshot.read_bytes())
        self.assertEqual(
            audit.normalize(audit.expected_manifest()),
            manifest.read_text(encoding="utf-8"),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
