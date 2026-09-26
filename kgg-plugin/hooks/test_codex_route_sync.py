from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from codex_route_sync import (
    MAPPING_SCHEMA,
    ROUTE_SCHEMA,
    build_route_body,
    find_project_mapping,
    plan_route_write,
    session_is_persisted,
    sync_route,
)


def payload(**overrides):
    value = {
        "hook_event_name": "SessionStart",
        "session_id": "01a0d1e7-1b39-7b13-aa53-517c9035c2b8",
        "cwd": "C:/workspace/project",
        "source": "startup",
        "transcript_path": "must-not-be-used.jsonl",
    }
    value.update(overrides)
    return value


class FakeRunner:
    def __init__(self, issues=None, write_returncode=0):
        self.issues = issues or []
        self.write_returncode = write_returncode
        self.calls = []

    def __call__(self, args, *, timeout):
        self.calls.append((list(args), timeout))
        if args[:3] == ["gh", "api", "--method"]:
            return subprocess.CompletedProcess(
                args=args,
                returncode=0,
                stdout=json.dumps(self.issues),
                stderr="",
            )
        return subprocess.CompletedProcess(
            args=args,
            returncode=self.write_returncode,
            stdout="ok",
            stderr="",
        )


class CodexRouteSyncTest(unittest.TestCase):
    def test_mapping_is_found_from_parent_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            nested = root / "a" / "b"
            nested.mkdir(parents=True)
            (root / ".kgg-project-status.json").write_text(
                json.dumps(
                    {
                        "schema": MAPPING_SCHEMA,
                        "project_id": "test-project",
                    }
                ),
                encoding="utf-8",
            )

            mapping = find_project_mapping(str(nested))

            self.assertIsNotNone(mapping)
            self.assertEqual("test-project", mapping.project_id)

    def test_mapping_with_extra_fields_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".kgg-project-status.json").write_text(
                json.dumps(
                    {
                        "schema": MAPPING_SCHEMA,
                        "project_id": "test-project",
                        "token": "must-not-be-accepted",
                    }
                ),
                encoding="utf-8",
            )

            self.assertIsNone(find_project_mapping(str(root)))

    def test_session_index_requires_exact_session_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            index = Path(tmp) / "session_index.jsonl"
            index.write_text(
                json.dumps({"id": "session-a"}) + "\n",
                encoding="utf-8",
            )

            self.assertTrue(
                session_is_persisted(
                    "session-a",
                    index_path=index,
                    retries=1,
                )
            )
            self.assertFalse(
                session_is_persisted(
                    "session-b",
                    index_path=index,
                    retries=1,
                )
            )

    def test_verified_body_contains_exact_codex_thread_url(self):
        body = build_route_body(
            "test-project",
            "thr_123",
            verified=True,
        )

        self.assertIn(f"schema: {ROUTE_SCHEMA}", body)
        self.assertIn("surface: codex", body)
        self.assertIn("session_ref: thr_123", body)
        self.assertIn("open_url: codex://threads/thr_123", body)
        self.assertIn("route_state: verified", body)

    def test_correlation_only_body_has_no_open_url(self):
        body = build_route_body(
            "test-project",
            "thr_123",
            verified=False,
        )

        self.assertNotIn("open_url:", body)
        self.assertIn("route_state: correlation_only", body)

    def test_plan_create_noop_update_and_duplicate(self):
        desired = build_route_body("test-project", "thr_new", verified=True)
        title = "[route:codex] test-project"

        self.assertEqual(
            ("create", None, ()),
            plan_route_write([], "test-project", desired),
        )

        existing = {
            "number": 20,
            "title": title,
            "body": desired,
            "state": "open",
        }
        self.assertEqual(
            ("noop", 20, ()),
            plan_route_write([existing], "test-project", desired),
        )

        changed = dict(existing, body=build_route_body("test-project", "old", verified=True))
        self.assertEqual(
            ("update", 20, ()),
            plan_route_write([changed], "test-project", desired),
        )

        duplicate = dict(existing, number=21)
        self.assertEqual(
            ("fail_duplicate", None, (20, 21)),
            plan_route_write([existing, duplicate], "test-project", desired),
        )

    def test_other_surface_and_status_issue_do_not_match(self):
        desired = build_route_body("test-project", "thr_new", verified=True)
        issues = [
            {
                "number": 1,
                "title": "status",
                "state": "open",
                "body": "schema: project-status/v1\nproject_id: test-project\nstate: running\nstep: x",
            },
            {
                "number": 2,
                "title": "[route:chatgpt] test-project",
                "state": "open",
                "body": "schema: project-route/v1\nproject_id: test-project\nsurface: chatgpt\nsession_ref: chat\nroute_state: correlation_only",
            },
        ]

        self.assertEqual(
            ("create", None, ()),
            plan_route_write(issues, "test-project", desired),
        )

    def test_sync_without_mapping_never_calls_github(self):
        with tempfile.TemporaryDirectory() as tmp:
            runner = FakeRunner()
            result = sync_route(
                payload(cwd=tmp),
                run_command=runner,
                protocol_available=True,
            )

            self.assertEqual("no_mapping", result)
            self.assertEqual([], runner.calls)

    def test_sync_creates_verified_route_for_persisted_session(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            session_id = "01a0d1e7-1b39-7b13-aa53-517c9035c2b8"
            (root / ".kgg-project-status.json").write_text(
                json.dumps(
                    {
                        "schema": MAPPING_SCHEMA,
                        "project_id": "synthetic-codex-r2",
                    }
                ),
                encoding="utf-8",
            )
            index = root / "session_index.jsonl"
            index.write_text(
                json.dumps({"id": session_id}) + "\n",
                encoding="utf-8",
            )
            runner = FakeRunner()

            result = sync_route(
                payload(cwd=str(root), session_id=session_id),
                run_command=runner,
                index_path=index,
                protocol_available=True,
            )

            self.assertEqual("created", result)
            self.assertEqual(2, len(runner.calls))
            create_args = runner.calls[1][0]
            body = create_args[create_args.index("--body") + 1]
            self.assertIn(f"open_url: codex://threads/{session_id}", body)
            self.assertIn("route_state: verified", body)
            encoded = " ".join(create_args)
            self.assertNotIn("transcript", encoded)

    def test_sync_uses_correlation_only_when_session_not_persisted(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".kgg-project-status.json").write_text(
                json.dumps(
                    {
                        "schema": MAPPING_SCHEMA,
                        "project_id": "synthetic-codex-r2",
                    }
                ),
                encoding="utf-8",
            )
            index = root / "session_index.jsonl"
            index.write_text("", encoding="utf-8")
            runner = FakeRunner()

            result = sync_route(
                payload(cwd=str(root), session_id="not-persisted"),
                run_command=runner,
                index_path=index,
                protocol_available=True,
            )

            self.assertEqual("created", result)
            body = runner.calls[1][0][runner.calls[1][0].index("--body") + 1]
            self.assertNotIn("open_url:", body)
            self.assertIn("route_state: correlation_only", body)

    def test_duplicate_fails_closed_without_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".kgg-project-status.json").write_text(
                json.dumps(
                    {
                        "schema": MAPPING_SCHEMA,
                        "project_id": "synthetic-codex-r2",
                    }
                ),
                encoding="utf-8",
            )
            body = build_route_body("synthetic-codex-r2", "thr", verified=False)
            runner = FakeRunner(
                issues=[
                    {"number": 10, "title": "a", "body": body, "state": "open"},
                    {"number": 11, "title": "b", "body": body, "state": "open"},
                ]
            )

            result = sync_route(
                payload(cwd=str(root), session_id="thr"),
                run_command=runner,
                index_path=root / "missing-index",
                protocol_available=False,
            )

            self.assertEqual("fail_duplicate", result)
            self.assertEqual(1, len(runner.calls))


if __name__ == "__main__":
    unittest.main()
