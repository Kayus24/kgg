#!/usr/bin/env python3
"""Named negative tests required by the Plugin-Candidate plan."""

from __future__ import annotations

import unittest
from pathlib import Path

import kgg_plugin_candidate_gate as gate


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "kgg-plugin"


class KggPluginCandidateGateTests(unittest.TestCase):
    def assert_gate(self, code: str, **kwargs: object) -> None:
        with self.assertRaisesRegex(gate.CandidateGateError, rf"^{code}"):
            gate.validate_candidate(PLUGIN, **kwargs)

    def test_candidate_passes_all_static_and_surface_gates(self) -> None:
        result = gate.validate_candidate(PLUGIN, surface_capabilities={"codex": {"mcp"}, "chatgpt": {"mcp"}})
        self.assertEqual(result["status"], "PASS")

    def test_skill_missing_is_typed(self) -> None:
        self.assert_gate("skill_missing", skill_names=gate.REQUIRED_SKILLS - {"kgg-safety"})

    def test_version_and_hash_drift_is_typed(self) -> None:
        self.assert_gate("version_hash_drift", expected_version="0.2.0")
        self.assert_gate("version_hash_drift", hash_overrides={"docs/kgg-ui-lab-v1-goal-prompt.md": "0" * 64})

    def test_mcp_availability_authorization_and_fresh_main_are_typed(self) -> None:
        self.assert_gate("mcp_unavailable", mcp_available=False)
        self.assert_gate("mcp_auth_denied", mcp_authorized=False)
        self.assert_gate("mcp_stale_main", fresh_main=False)

    def test_duplicate_tool_and_hook_rejection_are_typed(self) -> None:
        self.assert_gate("duplicate_tool_request", requested_tool_request_id="req-001", seen_request_ids={"req-001"})
        self.assert_gate("hook_reject", hook_accepted=False)

    def test_capability_and_surface_drift_are_typed(self) -> None:
        self.assert_gate("capability_drift", available_tools=gate.REQUIRED_TOOLS - {"run_width_sweep"})
        self.assert_gate("surface_unavailable", surface="chatgpt", surface_capabilities={"codex": {"mcp"}})
        self.assert_gate("surface_unavailable", surface="chatgpt", surface_capabilities={"chatgpt": set()})


if __name__ == "__main__":
    unittest.main()
