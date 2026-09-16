#!/usr/bin/env python3
"""Tests for the Phase 2 read-only parity fixtures."""

from __future__ import annotations

import unittest

import kgg_plugin_candidate_parity as parity


class KggPluginCandidateParityTests(unittest.TestCase):
    def test_exact_three_fixtures_are_valid(self) -> None:
        value = parity.validate_bundle(parity.sample_bundle())
        self.assertEqual(set(value), set(parity.FIXTURE_NAMES))
        self.assertTrue(all(item["mode"] == "read_only" for item in value.values()))

    def test_missing_fixture_is_rejected(self) -> None:
        value = parity.sample_bundle()
        value.pop("ticket_plan")
        with self.assertRaisesRegex(parity.ParityFixtureError, "fixture_bundle_incomplete"):
            parity.validate_bundle(value)

    def test_write_and_sensitive_fields_are_rejected(self) -> None:
        value = parity.sample_bundle()
        value["safe_canary"]["payload"] = {"dispatches": 1}
        with self.assertRaisesRegex(parity.ParityFixtureError, "fixture_forbidden_field"):
            parity.validate_bundle(value)

        value = parity.sample_bundle()
        value["current_state"]["payload"] = {"api_key": "synthetic"}
        with self.assertRaisesRegex(parity.ParityFixtureError, "fixture_forbidden_field"):
            parity.validate_bundle(value)

    def test_invalid_source_hash_and_non_read_only_mode_are_rejected(self) -> None:
        value = parity.sample_bundle()
        value["current_state"]["source_sha256"] = "bad"
        with self.assertRaisesRegex(parity.ParityFixtureError, "fixture_source_hash_invalid"):
            parity.validate_bundle(value)

        value = parity.sample_bundle()
        value["ticket_plan"]["mode"] = "write"
        with self.assertRaisesRegex(parity.ParityFixtureError, "fixture_mode_invalid"):
            parity.validate_bundle(value)


if __name__ == "__main__":
    unittest.main()
