#!/usr/bin/env python3
"""Contracts for persistent gpt-preview publication, immutable device-test PWA runs, and writer serialization."""

from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/kgg-gpt-preview-gate.yml"
AUTO_WORKFLOW = ROOT / ".github/workflows/kgg-gpt-preview-auto.yml"


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

    def test_device_test_patient_pwa_is_immutable_per_run(self) -> None:
        workflow = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn('run_key="${GITHUB_RUN_ID}-${GITHUB_RUN_ATTEMPT}"', workflow)
        self.assertIn(
            'patient_pwa_url="https://kayus24.github.io/kgg-patient-preview/device-test/$request_id/$run_key/"',
            workflow,
        )
        self.assertIn('echo "patient_pwa_rel=device-test/$request_id/$run_key"', workflow)
        self.assertIn('target="patient-preview/$KGG_PATIENT_PWA_REL"', workflow)
        self.assertIn('diff -qr "$RUNNER_TEMP/kgg-device-test-pwa" "$target"', workflow)
        self.assertIn("Immutable patient test PWA path already exists with different content", workflow)
        self.assertIn('git add "$KGG_PATIENT_PWA_REL"', workflow)
        self.assertIn('meta_url="${KGG_PATIENT_PWA_URL}device-test-meta.json"', workflow)
        self.assertNotIn("rm -rf patient-preview/device-test", workflow)
        self.assertNotIn(
            "meta_url='https://kayus24.github.io/kgg-patient-preview/device-test/device-test-meta.json'",
            workflow,
        )

    def test_all_gpt_preview_writers_share_one_serialization_group(self) -> None:
        gate = WORKFLOW.read_text(encoding="utf-8")
        auto = AUTO_WORKFLOW.read_text(encoding="utf-8")
        self.assertIn(
            "(inputs.mode == 'publish_preview' || inputs.mode == 'publish_device_test') && 'publish'",
            gate,
        )
        self.assertIn("group: kgg-gpt-preview-auto", auto)

        boundaries = (
            ("status-validating", "validate"),
            ("status-publishing", "publish"),
            ("status-final", None),
        )
        for job_name, next_job_name in boundaries:
            start_marker = f"\n  {job_name}:"
            self.assertIn(start_marker, auto)
            start = auto.index(start_marker) + 1
            if next_job_name is None:
                block = auto[start:]
            else:
                end_marker = f"\n  {next_job_name}:"
                self.assertIn(end_marker, auto[start:])
                end = auto.index(end_marker, start)
                block = auto[start:end]
            self.assertIn("concurrency:", block)
            self.assertIn("group: kgg-gpt-preview-publish", block)
            self.assertIn("cancel-in-progress: false", block)
        self.assertEqual(auto.count("group: kgg-gpt-preview-publish"), 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
