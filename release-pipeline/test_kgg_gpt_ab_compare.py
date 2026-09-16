#!/usr/bin/env python3
"""Three-surface fail-closed comparison contract tests."""

from __future__ import annotations

import unittest

import kgg_gpt_ab_compare as compare


def metrics(base_sha: str, *, quality: int = 90, runtime: int = 900) -> dict[str, object]:
    return {
        "scenario_id": "tablet-splitter-scale-drag-synth",
        "base_sha": base_sha,
        "status": "PASS",
        "reads": 8,
        "context_items": 4,
        "clarifying_questions": 0,
        "action_calls": 0,
        "dispatches": 0,
        "duplicate_dispatches": 0,
        "runtime_ms": runtime,
        "result_quality": quality,
        "root_cause_quality": quality,
        "repository_writes": 0,
        "secret_leaks": 0,
        "patient_data_leaks": 0,
        "source_regressions": 0,
        "gate_regressions": 0,
        "action_regressions": 0,
    }


class KggGptAbCompareTests(unittest.TestCase):
    def test_three_surfaces_require_identical_complete_pilot(self) -> None:
        result = compare.compare_surfaces(
            {
                "production": metrics("a" * 40),
                "candidate": metrics("a" * 40, quality=95, runtime=700),
                "codex_plugin": metrics("a" * 40, quality=94, runtime=750),
            }
        )
        self.assertEqual(result["status"], "COMPARABLE")
        self.assertTrue(result["replacement_eligible"])
        self.assertEqual(result["deltas_vs_production"]["candidate"]["runtime_ms"], -200)

    def test_missing_or_mismatched_surface_fails_closed(self) -> None:
        incomplete = compare.compare_surfaces({"production": metrics("a" * 40), "candidate": metrics("b" * 40)})
        self.assertEqual(incomplete["status"], "NOT_COMPARABLE")
        self.assertEqual(incomplete["error_class"], "pilot_incomplete")
        mismatch = compare.compare_surfaces(
            {
                "production": metrics("a" * 40),
                "candidate": dict(metrics("b" * 40), scenario_id="other-synthetic-case"),
                "codex_plugin": metrics("c" * 40),
            }
        )
        self.assertEqual(mismatch["status"], "NOT_COMPARABLE")
        self.assertEqual(mismatch["error_class"], "stale_context")

    def test_mismatched_fresh_main_sha_fails_closed(self) -> None:
        production = metrics("a" * 40)
        candidate = metrics("b" * 40)
        result = compare.compare(production, candidate)
        self.assertEqual(result["status"], "NOT_COMPARABLE")
        self.assertEqual(result["error_class"], "stale_context")
        three_way = compare.compare_surfaces(
            {"production": production, "candidate": metrics("a" * 40), "codex_plugin": candidate}
        )
        self.assertEqual(three_way["status"], "NOT_COMPARABLE")
        self.assertEqual(three_way["error_class"], "stale_context")

    def test_safety_failure_forbids_replacement(self) -> None:
        result = compare.compare_surfaces(
            {
                "production": metrics("a" * 40),
                "candidate": dict(metrics("a" * 40, quality=95), duplicate_dispatches=1),
                "codex_plugin": metrics("a" * 40, quality=94),
            }
        )
        self.assertEqual(result["status"], "FAIL")
        self.assertFalse(result["replacement_eligible"])

    def test_root_cause_quality_regression_forbids_replacement(self) -> None:
        result = compare.compare_surfaces(
            {
                "production": metrics("a" * 40, quality=90),
                "candidate": dict(metrics("a" * 40, quality=95), root_cause_quality=89),
                "codex_plugin": metrics("a" * 40, quality=94),
            }
        )
        self.assertEqual(result["status"], "COMPARABLE")
        self.assertFalse(result["replacement_eligible"])

    def test_external_style_non_numeric_result_fails_closed(self) -> None:
        external_style = dict(
            metrics("a" * 40),
            status="COMPARABLE",
            runtime_ms="NOT_MEASURABLE",
            result_quality="NOT_MEASURABLE",
            root_cause_quality="NOT_MEASURABLE",
            source_regressions="NOT_MEASURABLE",
            gate_regressions="NOT_MEASURABLE",
            action_regressions="NOT_MEASURABLE",
        )
        result = compare.compare_surfaces(
            {
                "production": external_style,
                "candidate": external_style,
                "codex_plugin": external_style,
            }
        )
        self.assertEqual(result["status"], "NOT_COMPARABLE")
        self.assertEqual(result["error_class"], "payload_schema")
        self.assertFalse(result["replacement_eligible"])

    def test_bounded_failure_envelope_is_observability_blocker(self) -> None:
        failure = {
            "status": "FAIL",
            "error_class": "NUMERIC_METRICS_NOT_VERIFIABLE",
        }
        result = compare.compare_surfaces(
            {
                "production": failure,
                "candidate": metrics("b" * 40),
                "codex_plugin": metrics("c" * 40),
            }
        )
        self.assertEqual(result["status"], "NOT_COMPARABLE")
        self.assertEqual(result["error_class"], "pilot_incomplete")
        self.assertEqual(result["failure_classes"]["production"], "NUMERIC_METRICS_NOT_VERIFIABLE")
        self.assertFalse(result["replacement_eligible"])

    def test_unknown_failure_envelope_is_rejected(self) -> None:
        failure = {"status": "FAIL", "error_class": "ARBITRARY_UNTRUSTED_TEXT"}
        result = compare.compare_surfaces(
            {
                "production": failure,
                "candidate": metrics("b" * 40),
                "codex_plugin": metrics("c" * 40),
            }
        )
        self.assertEqual(result["status"], "NOT_COMPARABLE")
        self.assertEqual(result["error_class"], "payload_schema")
        self.assertFalse(result["replacement_eligible"])

    def test_extra_fields_are_rejected_as_payload_schema(self) -> None:
        result = compare.compare_surfaces(
            {
                "production": dict(metrics("a" * 40), raw_transcript="synthetic-only fixture"),
                "candidate": metrics("b" * 40),
                "codex_plugin": metrics("c" * 40),
            }
        )
        self.assertEqual(result["status"], "NOT_COMPARABLE")
        self.assertEqual(result["error_class"], "payload_schema")
        self.assertFalse(result["replacement_eligible"])

    def test_non_hex_fresh_main_sha_is_rejected(self) -> None:
        result = compare.compare_surfaces(
            {
                "production": metrics("z" * 40),
                "candidate": metrics("z" * 40),
                "codex_plugin": metrics("z" * 40),
            }
        )
        self.assertEqual(result["status"], "NOT_COMPARABLE")
        self.assertEqual(result["error_class"], "payload_schema")
        self.assertFalse(result["replacement_eligible"])

    def test_next_run_draft_covers_the_complete_metric_contract(self) -> None:
        draft = (compare.Path(__file__).resolve().parents[1] / "docs" / "kgg-ui-lab-v1-production-control-next-run-draft-2026-09-14.md").read_text(encoding="utf-8")
        for field in compare.REQUIRED:
            self.assertIn(f'"{field}"', draft)
        self.assertIn('"status": "FAIL"', draft)
        self.assertIn('"error_class": "NUMERIC_METRICS_NOT_VERIFIABLE"', draft)
        self.assertIn("NOT_SENT / PENDING_USER_CONFIRMATION", draft)
        self.assertNotIn('"runtime_ms": "NOT_MEASURABLE"', draft)


if __name__ == "__main__":
    unittest.main()
