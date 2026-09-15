#!/usr/bin/env python3
"""Contract tests for the bounded read-only validation workflow."""

from __future__ import annotations

from pathlib import Path
import re
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "kgg-gpt-readonly-validation.yml"
API = ROOT / "docs" / "kgg-custom-gpt-action-api-openapi.yaml"


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

    def test_action_schema_pins_same_workflow_and_allowlist(self) -> None:
        self.assertEqual(1, self.api.count("operationId: submitKggReadOnlyValidation"))
        self.assertEqual(1, self.api.count("operationId: listKggReadOnlyValidationRuns"))
        self.assertIn("/actions/workflows/kgg-gpt-readonly-validation.yml/dispatches:", self.api)
        self.assertIn("enum: [tablet-splitter-scale-drag, gpt-contracts]", self.api)
        self.assertIn("x-openai-isConsequential: false", self.api)

    def test_supporting_helpers_pass_their_self_tests(self) -> None:
        for name in ("kgg_gpt_result.py", "kgg_gpt_run_reconcile.py"):
            proc = subprocess.run([sys.executable, str(ROOT / "release-pipeline" / name), "--self-test"], cwd=ROOT, text=True, capture_output=True)
            self.assertEqual(0, proc.returncode, proc.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
