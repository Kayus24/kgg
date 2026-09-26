from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from session_start import SCHEMA, capture_session


def payload(**overrides):
    value = {
        "hook_event_name": "SessionStart",
        "session_id": "session-123",
        "cwd": str(Path.cwd()),
        "source": "startup",
        "model": "gpt-test",
        "permission_mode": "default",
        "transcript_path": "secret-transcript.jsonl",
    }
    value.update(overrides)
    return value


class SessionStartCaptureTest(unittest.TestCase):
    def test_persists_only_allowed_identity_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            identity = capture_session(
                payload(),
                root,
                observed_at="2026-09-26T10:00:00Z",
            )

            self.assertIsNotNone(identity)
            self.assertEqual(
                {"schema", "session_id", "cwd", "source", "observed_at"},
                set(identity),
            )
            self.assertEqual(SCHEMA, identity["schema"])
            self.assertNotIn("model", identity)
            self.assertNotIn("permission_mode", identity)
            self.assertNotIn("transcript_path", identity)

    def test_session_and_latest_by_cwd_files_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            identity = capture_session(
                payload(session_id="abc"),
                root,
                observed_at="2026-09-26T10:00:00Z",
            )
            self.assertIsNotNone(identity)

            routing = root / "project-status-routing"
            session_files = list((routing / "sessions").glob("*.json"))
            cwd_files = list((routing / "latest-by-cwd").glob("*.json"))

            self.assertEqual(1, len(session_files))
            self.assertEqual(1, len(cwd_files))
            self.assertEqual(
                json.loads(session_files[0].read_text(encoding="utf-8")),
                json.loads(cwd_files[0].read_text(encoding="utf-8")),
            )

    def test_replay_same_session_is_idempotent_for_file_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first = capture_session(
                payload(session_id="same-session"),
                root,
                observed_at="2026-09-26T10:00:00Z",
            )
            second = capture_session(
                payload(session_id="same-session", source="resume"),
                root,
                observed_at="2026-09-26T10:05:00Z",
            )

            self.assertIsNotNone(first)
            self.assertIsNotNone(second)
            session_files = list(
                (root / "project-status-routing" / "sessions").glob("*.json")
            )
            self.assertEqual(1, len(session_files))
            stored = json.loads(session_files[0].read_text(encoding="utf-8"))
            self.assertEqual("resume", stored["source"])
            self.assertEqual("2026-09-26T10:05:00Z", stored["observed_at"])

    def test_new_session_same_cwd_updates_only_latest_pointer(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            capture_session(
                payload(session_id="session-a"),
                root,
                observed_at="2026-09-26T10:00:00Z",
            )
            capture_session(
                payload(session_id="session-b", source="resume"),
                root,
                observed_at="2026-09-26T10:05:00Z",
            )

            routing = root / "project-status-routing"
            self.assertEqual(2, len(list((routing / "sessions").glob("*.json"))))
            latest = list((routing / "latest-by-cwd").glob("*.json"))
            self.assertEqual(1, len(latest))
            stored = json.loads(latest[0].read_text(encoding="utf-8"))
            self.assertEqual("session-b", stored["session_id"])

    def test_different_cwds_have_separate_latest_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            first_cwd = root / "project-a"
            second_cwd = root / "project-b"
            capture_session(payload(session_id="a", cwd=str(first_cwd)), root)
            capture_session(payload(session_id="b", cwd=str(second_cwd)), root)

            latest = root / "project-status-routing" / "latest-by-cwd"
            self.assertEqual(2, len(list(latest.glob("*.json"))))

    def test_wrong_event_or_invalid_source_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            self.assertIsNone(
                capture_session(payload(hook_event_name="SessionEnd"), root)
            )
            self.assertIsNone(
                capture_session(payload(source="invented-source"), root)
            )
            self.assertFalse((root / "project-status-routing").exists())


if __name__ == "__main__":
    unittest.main()
