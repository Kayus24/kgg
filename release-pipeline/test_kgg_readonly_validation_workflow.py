#!/usr/bin/env python3
"""Contract tests for the bounded read-only validation workflow."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
PIPELINE = ROOT / "release-pipeline"
WORKFLOW = ROOT / ".github" / "workflows" / "kgg-gpt-readonly-validation.yml"
API = ROOT / "docs" / "kgg-custom-gpt-action-api-openapi.yaml"

if str(PIPELINE) not in sys.path:
    sys.path.insert(0, str(PIPELINE))

import kgg_gpt_run_reconcile as reconcile_helper


class ReadOnlyValidationWorkflowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")
        cls.api = API.read_text(encoding="utf-8")

    def test_workflow_is_dispatchable_with_bounded_inputs(self) -> None:
        for required in (
            "workflow_dispatch:",
            "request_id:",
            "source_sha:",
            "validation_profile:",
            "tablet-splitter-scale-drag",
            "gpt-contracts",
            "ref: main",
            "fetch-depth: 1",
        ):
            self.assertIn(required, self.workflow)
        self.assertIn("cancel-in-progress: false", self.workflow)

    def test_workflow_has_no_repository_write_scope_or_write_command(self) -> None:
        for forbidden in ("contents: write", "issues: write", "pull-requests: write", "git push", "gh pr", "submitKggPreviewAuto"):
            self.assertNotIn(forbidden, self.workflow)
        self.assertIn("contents: read", self.workflow)
        self.assertIn("actions: read", self.workflow)
        self.assertIn("REPOSITORY_WRITE_DETECTED: \"false\"", self.workflow)

    def test_source_verification_is_fail_closed_and_result_is_always_published(self) -> None:
        self.assertIn("set -euo pipefail", self.workflow)
        self.assertIn("EXPECTED_SOURCE_SHA", self.workflow)
        self.assertIn('[[ "$EXPECTED_SOURCE_SHA" =~ ^[0-9a-f]{40}$ ]]', self.workflow)
        self.assertIn("if: always()", self.workflow)
        self.assertIn("kgg_gpt_result.py --write", self.workflow)
        self.assertIn("actions/upload-artifact@v4", self.workflow)

    def test_workflow_preserves_failure_artifact_then_fails_closed(self) -> None:
        for required in (
            "id: result",
            "id: upload",
            "name: Enforce final validation outcome",
            "steps.source.outcome",
            "steps.tooling.outcome",
            "steps.validation.outcome",
            "steps.result.outcome",
            "steps.upload.outcome",
            "inputs.validation_profile == 'tablet-splitter-scale-drag'",
        ):
            self.assertIn(required, self.workflow)
        self.assertLess(self.workflow.index("name: Upload safe read-only result artifact"), self.workflow.index("name: Enforce final validation outcome"))

    def test_action_schema_pins_same_workflow_and_allowlist(self) -> None:
        self.assertEqual(1, self.api.count("operationId: submitKggReadOnlyValidation"))
        self.assertEqual(1, self.api.count("operationId: listKggReadOnlyValidationRuns"))
        self.assertIn("/actions/workflows/kgg-gpt-readonly-validation.yml/dispatches:", self.api)
        self.assertIn("enum: [tablet-splitter-scale-drag, gpt-contracts]", self.api)
        self.assertIn("x-openai-isConsequential: false", self.api)

    def test_reconcile_matches_only_exact_request_id_segments(self) -> None:
        sha = "a" * 40
        exact = {"id": 10, "display_title": "KGG GPT Read-only Validation | audit-035", "head_sha": sha}
        prefix = {"id": 11, "display_title": "KGG GPT Read-only Validation | prefix-audit-035", "head_sha": sha}
        suffix = {"id": 12, "display_title": "KGG GPT Read-only Validation | audit-035-extra", "head_sha": sha}
        adjacent = {"id": 13, "display_title": "KGG GPT Read-only Validation | audit-0352", "head_sha": sha}
        self.assertTrue(reconcile_helper.run_matches(exact, "audit-035", sha))
        self.assertFalse(reconcile_helper.run_matches(prefix, "audit-035", sha))
        self.assertFalse(reconcile_helper.run_matches(suffix, "audit-035", sha))
        self.assertFalse(reconcile_helper.run_matches(adjacent, "audit-035", sha))

    def test_reconcile_requires_exact_head_sha_when_base_sha_is_requested(self) -> None:
        sha = "a" * 40
        wrong = {"id": 20, "display_title": "KGG GPT Read-only Validation | audit-035", "head_sha": "b" * 40}
        missing = {"id": 21, "display_title": "KGG GPT Read-only Validation | audit-035"}
        exact = {"id": 22, "display_title": "KGG GPT Read-only Validation | audit-035", "head_sha": sha}
        self.assertFalse(reconcile_helper.run_matches(wrong, "audit-035", sha))
        self.assertFalse(reconcile_helper.run_matches(missing, "audit-035", sha))
        self.assertTrue(reconcile_helper.run_matches(exact, "audit-035", sha))

    def test_reconcile_stops_on_multiple_exact_matches(self) -> None:
        sha = "a" * 40
        payload = {
            "workflow_runs": [
                {"id": 30, "display_title": "KGG GPT Read-only Validation | audit-035", "head_sha": sha, "status": "completed", "conclusion": "success"},
                {"id": 31, "display_title": "KGG GPT Read-only Validation | audit-035", "head_sha": sha, "status": "completed", "conclusion": "success"},
            ]
        }
        result = reconcile_helper.reconcile("success", payload, "audit-035", sha)
        self.assertEqual("AMBIGUOUS_MATCH", result["status"])
        self.assertEqual(2, result["match_count"])
        self.assertNotIn("run_id", result)

    def test_supporting_helpers_pass_their_self_tests(self) -> None:
        for name in ("kgg_gpt_result.py", "kgg_gpt_run_reconcile.py"):
            proc = subprocess.run([sys.executable, str(PIPELINE / name), "--self-test"], cwd=ROOT, text=True, capture_output=True)
            self.assertEqual(0, proc.returncode, proc.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
