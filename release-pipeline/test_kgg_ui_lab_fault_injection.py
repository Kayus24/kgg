#!/usr/bin/env python3
"""Tests for the deterministic Phase 7 fault-injection matrix."""

from __future__ import annotations

import unittest

import kgg_ui_lab_fault_injection as faults


class KggUiLabFaultInjectionTests(unittest.TestCase):
    def test_all_named_faults_are_bounded_without_external_writes(self) -> None:
        results = faults.execute_matrix()
        self.assertEqual(len(results), 11)
        self.assertEqual([item["case_id"] for item in results], [case_id for case_id, _ in faults.FAULT_CASES])
        self.assertTrue(all(item["status"] == "BOUNDED" for item in results))
        self.assertTrue(all(item["external_write"] is False for item in results))

    def test_transient_faults_use_retry_then_bruder_and_protected_faults_stop(self) -> None:
        self.assertEqual(faults.execute_case("browser-timeout")["actions"], ["retry_same_request", "bruder_handoff"])
        self.assertEqual(faults.execute_case("missing-bruder")["actions"], ["bruder_handoff", "pause_for_max"])
        self.assertEqual(faults.execute_case("duplicate-request-id")["actions"], ["pause_for_max"])
        self.assertEqual(faults.execute_case("mcp-hook-outage")["actions"], ["pause_for_max"])

    def test_unknown_fault_id_is_rejected(self) -> None:
        with self.assertRaisesRegex(faults.FaultInjectionError, "fault_case_unknown"):
            faults.execute_case("not-a-real-fault")


if __name__ == "__main__":
    unittest.main()
