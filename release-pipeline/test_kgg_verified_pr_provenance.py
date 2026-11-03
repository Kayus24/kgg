#!/usr/bin/env python3
"""Negative and positive offline tests for KGG generic PR provenance."""

from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).with_name("kgg_verified_pr_provenance.py")
spec = importlib.util.spec_from_file_location("kgg_verified_pr_provenance", MODULE)
gate = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(gate)

SHA = "a" * 40
BRANCH = "fix/verified-cockpit"
BASE = "fix/plan-card-space-v132"
RUN_ID = 41614544379
PR_NUM = 359


def valid_records() -> tuple[dict, dict]:
    repo = {"full_name": gate.REPO}
    pr = {
        "number": PR_NUM, "state": "open", "draft": True,
        "head": {"ref": BRANCH, "sha": SHA, "repo": {"full_name": gate.REPO}},
        "base": {"ref": BASE, "repo": {"full_name": gate.REPO}},
        "author_association": "OWNER",
        "labels": [{"name": gate.NO_RELEASE_LABEL}, {"name": gate.APPROVAL_LABEL}],
    }
    run = {
        "id": RUN_ID, "status": "completed", "conclusion": "success",
        "event": "pull_request", "name": gate.WORKFLOW_NAME,
        "path": gate.WORKFLOW_PATH, "workflow_id": gate.WORKFLOW_ID,
        "head_sha": SHA, "head_branch": BRANCH,
        "repository": {"full_name": gate.REPO}, "head_repository": {"full_name": gate.REPO},
        "pull_requests": [{"number": PR_NUM, "head": {"sha": SHA}}],
    }
    return pr, run


def check(pr: dict, run: dict, **overrides: object) -> dict:
    values = {"pr_number": PR_NUM, "sha": SHA, "branch": BRANCH,
              "base_branch": BASE, "run_id": RUN_ID}
    values.update(overrides)
    return gate.validate(pr, run, **values)


class GateTests(unittest.TestCase):
    def test_known_good_never_authorizes_publish(self) -> None:
        pr, run = valid_records()
        result = check(pr, run)
        self.assertEqual(result["status"], "PASS")
        self.assertFalse(result["publishingAuthorized"])
        self.assertEqual(result["sha"], SHA)
        self.assertEqual(result["contract"], gate.CONTRACT)

    def test_denies_security_and_identity_mismatches(self) -> None:
        cases = {
            "approval": lambda p, r: p.update(labels=[{"name": gate.NO_RELEASE_LABEL}]),
            "release_label": lambda p, r: p.update(labels=[{"name": gate.APPROVAL_LABEL}]),
            "head_drift": lambda p, r: p["head"].update(sha="b" * 40),
            "base_drift": lambda p, r: p["base"].update(ref="main"),
            "branch_drift": lambda p, r: p["head"].update(ref="malicious"),
            "fork": lambda p, r: p["head"]["repo"].update(full_name="outside/fork"),
            "closed": lambda p, r: p.update(state="closed"),
            "not_draft": lambda p, r: p.update(draft=False),
            "author_untrusted": lambda p, r: p.update(author_association="NONE"),
            "run_failed": lambda p, r: r.update(conclusion="failure"),
            "run_running": lambda p, r: r.update(status="in_progress"),
            "run_event": lambda p, r: r.update(event="workflow_dispatch"),
            "run_name": lambda p, r: r.update(name="Arbitrary green workflow"),
            "run_path": lambda p, r: r.update(path=".github/workflows/bypass.yml"),
            "run_workflow_id": lambda p, r: r.update(workflow_id=999),
            "run_head": lambda p, r: r.update(head_sha="b" * 40),
            "run_branch": lambda p, r: r.update(head_branch="elsewhere"),
            "run_repo": lambda p, r: r["repository"].update(full_name="outside/repo"),
            "run_head_repo": lambda p, r: r["head_repository"].update(full_name="outside/repo"),
            "run_pr_mismatch": lambda p, r: r.update(pull_requests=[{"number": 500, "head": {"sha": SHA}}]),
            "run_pr_sha": lambda p, r: r["pull_requests"][0]["head"].update(sha="b" * 40),
            "run_pr_duplicate": lambda p, r: r["pull_requests"].append(copy.deepcopy(r["pull_requests"][0])),
            "run_id_drift": lambda p, r: r.update(id=123),
            "pr_bool_number": lambda p, r: p.update(number=True),
            "run_bool_id": lambda p, r: r.update(id=True),
        }
        for label, mutate in cases.items():
            with self.subTest(label=label):
                pr, run = valid_records()
                # The two records intentionally get independent object trees.
                pr = copy.deepcopy(pr)
                run = copy.deepcopy(run)
                mutate(pr, run)
                with self.assertRaises(gate.ProvenanceError):
                    check(pr, run)

    def test_denies_invalid_requested_inputs(self) -> None:
        invalid = [
            {"pr_number": True},
            {"run_id": 0},
            {"sha": "not-a-sha"},
            {"branch": "refs/heads/../bad"},
            {"base_branch": "bad//base"},
            {"branch": "x;echo secret"},
            {"base_branch": "/leading-slash"},
        ]
        for bad in invalid:
            with self.subTest(bad=bad):
                pr, run = valid_records()
                with self.assertRaises(gate.ProvenanceError):
                    check(pr, run, **bad)

    def test_cli_rejects_missing_approval_then_accepts_test_fixture(self) -> None:
        pr, run = valid_records()
        with tempfile.TemporaryDirectory(prefix="kgg-provenance-") as tmp:
            root = Path(tmp)
            pr_path = root / "pr.json"
            run_path = root / "run.json"
            def invoke() -> subprocess.CompletedProcess:
                pr_path.write_text(json.dumps(pr), encoding="utf-8")
                run_path.write_text(json.dumps(run), encoding="utf-8")
                return subprocess.run([
                    sys.executable, str(MODULE), "--pr-file", str(pr_path),
                    "--run-file", str(run_path), "--pr-number", str(PR_NUM),
                    "--sha", SHA, "--branch", BRANCH, "--base-branch", BASE,
                    "--run-id", str(RUN_ID),
                ], capture_output=True, text=True, timeout=12)
            pr["labels"].pop()
            denied = invoke()
            self.assertEqual(denied.returncode, 1, denied.stdout)
            self.assertEqual(json.loads(denied.stdout)["code"], "preview_approval_missing")
            pr["labels"].append({"name": gate.APPROVAL_LABEL})
            accepted = invoke()
            self.assertEqual(accepted.returncode, 0, accepted.stdout)
            self.assertFalse(json.loads(accepted.stdout)["publishingAuthorized"])


if __name__ == "__main__":
    unittest.main()
