#!/usr/bin/env python3
"""Tests for the fail-closed five-gate migration evaluator."""

from __future__ import annotations

import json
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import kgg_ui_lab_migration_gate as gates


def _current_bound_pending_report(root: Path) -> dict:
    """Build current-file evidence without rewriting historical reports."""

    report = gates.synthetic_pass_report()
    report["fresh_main_sha"] = "6ab3e3ccd2ca96521b96bf9e94470cac1cde93ce"
    evidence_path = root / "release-pipeline" / "kgg_ui_lab_migration_gate.py"
    evidence_rel = "release-pipeline/kgg_ui_lab_migration_gate.py"
    evidence_sha = hashlib.sha256(evidence_path.read_bytes()).hexdigest()
    pending = {"EFFICIENCY_PASS", "CROSS_SURFACE_PASS"}
    for name in gates.GATE_NAMES:
        report["gates"][name] = {
            "status": "PENDING" if name in pending else "PASS",
            "checks": {key: name not in pending for key in sorted(gates.GATE_CHECKS[name])},
            "evidence_refs": [{
                "id": f"{name.casefold().replace('_', '-')}-current",
                "kind": "result",
                "sha256": evidence_sha,
                "path": evidence_rel,
            }],
        }
    return report


class KggUiLabMigrationGateTests(unittest.TestCase):
    def test_all_five_pass_without_authorizing_release(self) -> None:
        result = gates.evaluate(gates.synthetic_pass_report())
        self.assertEqual(result["status"], "MIGRATION_ELIGIBLE")
        self.assertFalse(result["release_allowed"])
        self.assertEqual(set(result["gates"]), set(gates.GATE_NAMES))

    def test_missing_gate_is_not_silently_pending(self) -> None:
        report = gates.synthetic_pass_report()
        report["gates"].pop("STABILITY_PASS")
        with self.assertRaisesRegex(gates.MigrationGateError, "migration_gates_incomplete"):
            gates.evaluate(report)

    def test_failed_safety_gate_blocks_eligibility(self) -> None:
        report = gates.synthetic_pass_report()
        report["gates"]["SAFETY_PASS"] = {
            "status": "FAIL",
            "checks": {key: key != "no_writes" for key in sorted(gates.GATE_CHECKS["SAFETY_PASS"])},
            "evidence_refs": [{"id": "safety-ref", "kind": "result", "sha256": "c" * 64}],
        }
        result = gates.evaluate(report)
        self.assertEqual(result["status"], "NOT_ELIGIBLE")

    def test_stale_or_unsafe_evidence_is_rejected(self) -> None:
        report = gates.synthetic_pass_report()
        report["fresh_main_sha"] = "not-a-sha"
        with self.assertRaisesRegex(gates.MigrationGateError, "fresh_main_sha_invalid"):
            gates.evaluate(report)

        report = gates.synthetic_pass_report()
        report["gates"]["PARITY_PASS"]["evidence_refs"][0]["kind"] = "raw_qr"
        with self.assertRaisesRegex(gates.MigrationGateError, "evidence_ref_invalid"):
            gates.evaluate(report)

        report = gates.synthetic_pass_report()
        report["gates"]["PARITY_PASS"]["evidence_refs"][0]["path"] = "release-pipeline/kgg_ui_lab_migration_gate.py"
        with self.assertRaisesRegex(gates.MigrationGateError, "evidence_hash_mismatch"):
            gates.evaluate(report)

    def test_current_gate_report_stays_not_eligible_without_cross_surface_proof(self) -> None:
        root = Path(__file__).resolve().parents[1]
        report = _current_bound_pending_report(root)
        result = gates.evaluate(report)
        self.assertEqual(result["status"], "NOT_ELIGIBLE")
        self.assertFalse(result["release_allowed"])
        self.assertEqual(result["gates"]["CROSS_SURFACE_PASS"]["status"], "PENDING")
        self.assertEqual(result["gates"]["EFFICIENCY_PASS"]["status"], "PENDING")

    def test_cli_report_argument_evaluates_supplied_report(self) -> None:
        root = Path(__file__).resolve().parents[1]
        script = Path(__file__).resolve().parent / "kgg_ui_lab_migration_gate.py"
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "current-pending-report.json"
            path.write_text(json.dumps(_current_bound_pending_report(root)), encoding="utf-8")
            completed = subprocess.run(
                [sys.executable, str(script), "--report", str(path)],
                check=True,
                capture_output=True,
                text=True,
            )
            result = json.loads(completed.stdout)
        self.assertEqual(result["status"], "NOT_ELIGIBLE")
        self.assertFalse(result["release_allowed"])


if __name__ == "__main__":
    unittest.main()
