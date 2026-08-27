#!/usr/bin/env python3
"""Contracts for first-time creation of the persistent gpt-preview device-test channel."""

from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/kgg-gpt-preview-gate.yml"


class PersistentPreviewBootstrapTests(unittest.TestCase):
    def test_missing_gpt_preview_branch_is_still_pushed(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("git checkout --orphan gpt-preview", workflow)

        start_marker = "      - name: Publish persistent device-test Preview channel"
        end_marker = "      - name: Create guarded PR from accepted preview"
        self.assertIn(start_marker, workflow)
        self.assertIn(end_marker, workflow)
        block = workflow[workflow.index(start_marker) : workflow.index(end_marker)]

        drift = "Main drift detected immediately before Preview activation"
        push = "git push origin HEAD:gpt-preview"
        self.assertIn(drift, block)
        self.assertIn(push, block)
        self.assertLess(block.index(drift), block.index(push))
        self.assertNotIn("rev-parse origin/gpt-preview", block)
        self.assertNotIn("git diff --cached --quiet ||", block)


if __name__ == "__main__":
    unittest.main(verbosity=2)
