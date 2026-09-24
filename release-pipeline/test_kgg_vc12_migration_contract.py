#!/usr/bin/env python3
"""VC12 migration, surface-boundary, safety and provenance contract tests."""

from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "kgg-plugin" / "mcp" / "README.md"


class Vc12MigrationContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.readme = README.read_text(encoding="utf-8")

    def test_plugin_documents_the_three_surface_migration_boundary(self) -> None:
        required = (
            "## VC12 migration boundary",
            "A = existing Custom GPT (Production Control)",
            "B = ChatGPT + Plugin",
            "C = Codex + Plugin",
            "kgg_gpt_ab_compare.py",
            "test/migration harness",
            "A/B/C full parity",
            "NOT_OBSERVABLE",
        )
        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, self.readme)

    def test_plugin_documents_safety_provenance_efficiency_and_rollback_boundaries(self) -> None:
        required = (
            "PARITY_PASS",
            "SAFETY_PASS",
            "EFFICIENCY_PASS",
            "CROSS_SURFACE_PASS",
            "STABILITY_PASS",
            "NOT_MEASURED",
            "release_allowed=false",
            "rollback",
            "external Action dispatch",
            "synthetic test data",
        )
        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, self.readme)

    def test_boundary_does_not_promote_local_evidence_to_external_host_parity(self) -> None:
        self.assertIn("C-LOCAL", self.readme)
        self.assertIn("C-STDIO", self.readme)
        self.assertIn("not a B/C host claim", self.readme)
        self.assertIn("comparison_ready=false", self.readme)


if __name__ == "__main__":
    unittest.main(verbosity=2)
