#!/usr/bin/env python3
"""VC11 parity recheck for existing Custom-GPT and UI-Lab capability sources."""

from __future__ import annotations

import re
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MATRIX = ROOT / "docs" / "kgg-project-completion" / "01a-capability-migration-matrix.md"
ACTION_API = ROOT / "docs" / "kgg-custom-gpt-action-api-openapi.yaml"


class CustomGptCapabilityParityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.matrix = MATRIX.read_text(encoding="utf-8")

    def test_g01_wrapper_and_g01a_surface_status_are_distinct(self) -> None:
        self.assertIn("G01_WRAPPER_STATUS=PASS", self.matrix)
        self.assertIn("G01A_SOURCE_MATRIX_STATUS=PASS", self.matrix)
        self.assertIn("SURFACE_PARITY_STATUS=PARTIAL", self.matrix)
        self.assertNotIn("IMPLEMENTATION_STATUS=DRAFT_MATRIX", self.matrix)

    def test_vc11_ui_capabilities_have_component_host_positive_and_negative_test(self) -> None:
        bindings = {
            "CAP-17 swipe": (
                "kgg-plugin/mcp/server.py",
                "C-LOCAL real-browser bridge; C-STDIO synthetic contract",
                "test_persistent_swipe_supports_horizontal_desktop_and_vertical_mobile",
                "test_persistent_swipe_rejects_bounds_and_stale_observations_without_side_effect",
            ),
            "CAP-18 visual compare": (
                "kgg-plugin/mcp/server.py",
                "C-LOCAL real-browser bridge; C-STDIO synthetic contract",
                "test_visual_reference_identical_and_fixture_screenshot_pass",
                "test_visual_reference_rejects_hash_mismatch_and_viewport_mismatch",
            ),
            "CAP-19 saved flows": (
                "kgg-plugin/mcp/server.py + kgg-plugin/mcp/flow_store.py",
                "C-STDIO synthetic persistence; C-LOCAL real bridge replay",
                "test_all_flow_operations_cross_the_mcp_boundary",
                "test_drift_toggle_and_sensitive_flow_inputs_fail_closed",
            ),
            "CAP-21 recording": (
                "kgg-plugin/mcp/server.py",
                "C-LOCAL allowlisted real-browser host only; C-STDIO fails closed",
                "test_screen_recording_returns_traceable_keyframes_for_synthetic_motion",
                "test_screen_recording_rejects_missing_capability_and_invalid_bounds_without_side_effect",
            ),
        }
        for capability, expected in bindings.items():
            with self.subTest(capability=capability):
                self.assertIn(capability, self.matrix)
                for value in expected:
                    self.assertIn(value, self.matrix)

    def test_existing_action_operation_inventory_remains_complete_and_no_live_parity_is_claimed(self) -> None:
        operation_ids = re.findall(r"^\s+operationId:\s+(\S+)\s*$", ACTION_API.read_text(encoding="utf-8"), re.MULTILINE)
        self.assertEqual(len(operation_ids), 30)
        for operation_id in operation_ids:
            with self.subTest(operation_id=operation_id):
                self.assertIn(f"`{operation_id}`", self.matrix)
        self.assertIn("A_B_C_FULL_PARITY=NOT_PROVEN", (ROOT / "docs" / "kgg-project-completion" / "A_B_C_CAPABILITY_MATRIX_V1.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
