import copy
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import kgg_patient_gpt_write_gate as gate
import kgg_patient_local_test as browser_job
from kgg_git_environment import sanitized_git_environment


class PatientLocalCandidateTest(unittest.TestCase):
    def setUp(self):
        workspace_tmp = gate.ROOT / "tmp"
        workspace_tmp.mkdir(exist_ok=True)
        temporary = tempfile.TemporaryDirectory(dir=workspace_tmp)
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.git("init", "-q")
        self.script = self.root / "patient-example.js"
        self.script.write_bytes(b"const example = 1;\n")
        for name in ("index.html", "service-worker.js", "update-recovery.html", "icon.svg"):
            (self.root / name).write_text(name, encoding="utf-8")
        self.git("add", ".")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "-qm", "Synthetic fixture")
        self.payload = {
            "request_id": "local-fixture-377", "base_sha": gate.git_sha(self.root),
            "title": "Synthetic patient patch", "summary": "One synthetic patient test value.",
            "version_slug": "synthetic-local", "risk_class": "standard",
            "touched_areas": ["patient-ui"], "required_tests": ["synthetic-fixture"],
            "operations": [{"type": "replace_exact", "path": self.script.name,
                            "old_sha256": gate.sha256_text("const example = 1;\n"),
                            "old_text": "const example = 1;", "new_text": "const example = 2;"}],
        }
        self.approval = {
            "schema": "kgg.patient-local-candidate.v1", "target": "patient", "test_data": "synthetic",
            "base_sha": self.payload["base_sha"], "request_id": self.payload["request_id"],
            "patch_sha256": gate.payload_hash(self.payload), "approval_phrase": "Zulassen",
        }

    def git(self, *args):
        subprocess.run(["git", *args], cwd=self.root, check=True, capture_output=True,
                       env=sanitized_git_environment())

    def prepare(self, payload=None, approval=None):
        return gate.prepare_local_candidate(payload or self.payload, approval or self.approval, self.root)

    def evidence(self):
        return gate.local_candidate_evidence(self.payload["request_id"], self.root)

    def test_exact_commit_and_deduplicated_replay(self):
        self.script.write_bytes(b"const example = 'dirty';\n")
        result = self.prepare()
        self.assertEqual(result["status"], "COMPLETE")
        self.assertEqual(result["preview_status"], "NOT_RUN")
        candidate = self.root / result["candidate"]
        self.assertEqual((candidate / self.script.name).read_bytes(), b"const example = 2;\n")
        self.assertIn("update-recovery.html", result["sha256"])
        self.assertEqual(self.script.read_bytes(), b"const example = 'dirty';\n")
        self.assertEqual(self.prepare(), result)
        self.assertEqual(self.evidence(), result)
        (candidate / self.script.name).write_bytes(b"tampered")
        self.assertEqual(self.evidence()["status"], "UNKNOWN")
        self.assertEqual(self.prepare()["status"], "UNKNOWN")

    def test_preflight_rejects_stale_and_unauthorized_inputs(self):
        for key, value in {"schema": "v0", "target": "admin", "test_data": "real", "base_sha": "0" * 40,
                           "approval_phrase": "", "patch_sha256": "0" * 64}.items():
            with self.subTest(key=key), self.assertRaises(gate.GateError):
                self.prepare(approval={**self.approval, key: value})
        invalid = copy.deepcopy(self.payload)
        invalid["operations"][0]["path"] = "../index.html"
        with self.assertRaisesRegex(gate.GateError, "root patient file"):
            self.prepare(invalid, {**self.approval, "patch_sha256": gate.payload_hash(invalid)})
        self.assertEqual(self.evidence()["status"], "NOT_RUN")

    def test_explicit_repository_ignores_parent_hook_git_environment(self):
        # An inherited hook route must never redirect fixture or candidate Git I/O.
        invalid = str(self.root / "nonexistent-parent-git")
        with patch.dict(os.environ, {"GIT_DIR": invalid, "GIT_WORK_TREE": invalid,
                                     "GIT_INDEX_FILE": invalid + ".index"}):
            self.git("status", "--porcelain")
            self.assertEqual(gate.git_sha(self.root), self.payload["base_sha"])
            self.assertEqual(self.prepare()["status"], "COMPLETE")
        self.assertFalse(Path(invalid).exists())
        self.assertFalse(Path(invalid + ".index").exists())

    def test_conflicting_replay_keeps_original_candidate(self):
        result = self.prepare()
        other = copy.deepcopy(self.payload)
        other["operations"][0]["new_text"] = "const example = 3;"
        with self.assertRaisesRegex(gate.GateError, "already bound"):
            self.prepare(other, {**self.approval, "patch_sha256": gate.payload_hash(other)})
        self.assertEqual(self.evidence(), result)

    def test_deadline_and_tool_failure_are_terminal(self):
        for error, status in ((subprocess.TimeoutExpired("git", 1), "TIMEOUT"),
                              (PermissionError("blocked"), "BLOCKED")):
            with self.subTest(status=status), patch.object(gate, "stage_local_runtime", side_effect=error) as stage:
                self.payload["request_id"] = f"local-fixture-{status.lower()}"
                self.approval.update(request_id=self.payload["request_id"], patch_sha256=gate.payload_hash(self.payload))
                result = self.prepare()
                self.assertEqual(result["status"], status)
                self.assertEqual(self.prepare(), result)
                stage.assert_called_once()
                self.assertEqual(self.evidence(), result)

    def test_interrupted_job_has_no_success_and_is_not_started_again(self):
        job = gate.local_candidate_job(self.root, self.payload["request_id"])
        job.mkdir(parents=True)
        gate.write_local_receipt(job / "start.json", {
            "schema": gate.LOCAL_CANDIDATE_SCHEMA, "job_id": job.name, "status": "RUNNING",
            "patch_sha256": self.approval["patch_sha256"], "preview_status": "NOT_RUN",
            "deadline": (datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat(),
        })
        with patch.object(gate, "stage_local_runtime") as stage:
            self.assertEqual(self.prepare()["status"], "UNKNOWN")
            stage.assert_not_called()
        self.assertEqual(self.evidence()["reason"], "deadline_without_terminal_receipt")
        self.assertFalse((job / "result.json").exists())

    def test_red_runs_before_the_patch(self):
        def red(baseline):
            self.assertEqual((baseline / self.script.name).read_text(encoding="utf-8"), "const example = 1;\n")
            self.assertFalse((baseline.parent / "candidate").exists())
            raise browser_job.TestStopped("baseline_did_not_reproduce")

        result = gate.prepare_local_candidate(self.payload, self.approval, self.root, before_patch=red)
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["reason"], "baseline_did_not_reproduce")

    def configure_browser_case(self):
        # This test exercises the host contract; the real browser is run independently.
        self.payload["required_tests"] = [browser_job.PROFILE]
        self.payload["operations"][0]["path"] = browser_job.PATIENT_FILE
        self.approval["patch_sha256"] = gate.payload_hash(self.payload)
        self.directory = browser_job.run_dir(self.root, self.payload["base_sha"], 1)

    def start_browser(self, schema=browser_job.SCHEMA, attempt=1):
        return browser_job.start(self.payload, self.approval, schema, attempt, self.root)

    def test_browser_start_deduplicates_and_recovers_unknown_without_relaunch(self):
        self.configure_browser_case()
        plan = browser_job.preflight(self.payload, browser_job.SCHEMA, 1, self.root)
        self.assertEqual(plan["confirmation"]["approval_phrase"], "")
        self.assertFalse(self.directory.exists())
        with patch.object(browser_job, "Popen") as launch:
            launch.return_value.pid = 53
            initial = self.start_browser()
            self.assertEqual(initial["pid"], 53)
            self.assertEqual(initial["status"], "RUNNING")
            self.assertEqual(initial["result_file"], plan["result_file"])
            self.assertEqual(self.start_browser()["run_id"], initial["run_id"])
            with patch.object(browser_job, "now", return_value=datetime.now(timezone.utc) + timedelta(days=1)):
                self.assertEqual(self.start_browser()["status"], "UNKNOWN")
                self.assertFalse((self.directory / "notice.md").exists())
                with self.assertRaisesRegex(gate.GateError, "previous verified"):
                    self.start_browser(attempt=2)
            launch.assert_called_once()

    def test_browser_rejects_stale_schema_and_keeps_terminal_blocked_notice(self):
        self.configure_browser_case()
        with self.assertRaisesRegex(gate.GateError, "current test schema"):
            self.start_browser(schema="kgg.patient-local-test/v0")
        with patch.object(browser_job, "Popen", side_effect=PermissionError):
            result = self.start_browser()
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["exit_codes"], {})
        self.assertTrue(browser_job.evidence(self.directory, self.root)["notice_ready"])
        self.assertTrue((self.directory / "notice.md").read_text(encoding="utf-8").endswith("ENDE notice\n"))
        (self.directory / "notice.md").write_text("ENDE notice\n", encoding="utf-8")
        self.assertFalse(browser_job.evidence(self.directory, self.root)["notice_ready"])
        self.assertEqual(self.start_browser()["status"], "BLOCKED")

    def test_browser_repair_is_bounded_and_requires_a_changed_patch(self):
        self.configure_browser_case()
        with patch.object(browser_job, "Popen") as launch:
            launch.return_value.pid = 53
            initial = self.start_browser()
        (self.directory / "proof").mkdir()
        browser_job.finish(self.directory, initial, "FAIL", "candidate_assertion_failed", {"red": 1, "green": 1})
        self.payload["request_id"] = "local-fixture-next"
        self.approval.update(request_id=self.payload["request_id"], patch_sha256=gate.payload_hash(self.payload))
        with self.assertRaisesRegex(gate.GateError, "duplicates"):
            self.start_browser(attempt=2)
        with self.assertRaisesRegex(gate.GateError, "attempt 1"):
            self.start_browser(attempt=4)
        self.payload["operations"][0]["new_text"] = "const example = 3;"
        self.approval["patch_sha256"] = gate.payload_hash(self.payload)
        with patch.object(browser_job, "Popen") as launch:
            self.assertEqual(self.start_browser(attempt=2)["attempt"], 2)
            launch.assert_called_once()


if __name__ == "__main__":
    unittest.main()
