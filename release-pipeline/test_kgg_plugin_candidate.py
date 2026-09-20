#!/usr/bin/env python3
"""Contract tests for the repository-local KGG Plugin Candidate."""

from __future__ import annotations

import json
import hashlib
import re
import subprocess
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "kgg-plugin"
EXPECTED_SKILLS = {
    "kgg-supervisor",
    "kgg-operations",
    "kgg-testing",
    "kgg-safety",
    "kgg-escalation",
}


class KggPluginCandidateTests(unittest.TestCase):
    def test_manifest_is_candidate_only_and_has_no_placeholder(self) -> None:
        manifest_path = PLUGIN / ".codex-plugin" / "plugin.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["name"], "kgg-plugin")
        self.assertEqual(manifest["version"].split("+", 1)[0], "0.1.0")
        self.assertNotIn("[TODO:", manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(manifest["skills"], "./skills/")
        self.assertEqual(manifest["mcpServers"], "./.mcp.json")

    def test_five_skills_have_valid_frontmatter_and_distinct_roles(self) -> None:
        actual = {path.name for path in (PLUGIN / "skills").iterdir() if path.is_dir()}
        self.assertEqual(actual, EXPECTED_SKILLS)
        for name in sorted(actual):
            contents = (PLUGIN / "skills" / name / "SKILL.md").read_text(encoding="utf-8")
            self.assertTrue(contents.startswith("---\n"), name)
            self.assertRegex(contents, rf"name: {re.escape(name)}\n")
            self.assertIn("description:", contents)
            self.assertNotIn("[TODO:", contents)

    def test_source_map_points_to_existing_canonical_sources(self) -> None:
        source_map = (PLUGIN / "references" / "source-map.md").read_text(encoding="utf-8")
        for relative in (
            "docs/kgg-ui-lab-v1-goal-prompt.md",
            "docs/kgg-custom-gpt-goal-prompt.md",
            "docs/kgg-custom-gpt-knowledge-operations.md",
            "docs/kgg-custom-gpt-knowledge-testing.md",
            "docs/kgg-custom-gpt-knowledge-safety.md",
            "release-pipeline/kgg_ui_lab_contract.py",
            "release-pipeline/kgg_ui_lab_runtime.py",
            "release-pipeline/kgg_brain_relay_worker.py",
        ):
            self.assertTrue((ROOT / relative).is_file(), relative)
            self.assertIn(f"`{relative}`", source_map)
        self.assertIn("Snapshot SHA-256", source_map)

    def test_source_map_mcp_hash_matches_architecture_manifest(self) -> None:
        source_map = (PLUGIN / "references" / "source-map.md").read_text(encoding="utf-8")
        manifest = json.loads(
            (PLUGIN / "references" / "architecture" / "source-hashes.json").read_text(
                encoding="utf-8"
            )
        )
        server_hash = next(
            entry["sha256"]
            for entry in manifest["sources"]
            if entry["path"] == "kgg-plugin/mcp/server.py"
        )
        transport_line = next(
            line for line in source_map.splitlines() if line.startswith("| Installed MCP transport |")
        )
        self.assertIn(f"`{server_hash}`", transport_line)

    def test_snapshot_hashes_and_skill_hash_claims_match(self) -> None:
        manifest_path = PLUGIN / "references" / "architecture" / "source-hashes.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertTrue(manifest["fresh_main_required"])
        for entry in manifest["sources"]:
            source = ROOT / entry["path"]
            actual = hashlib.sha256(source.read_bytes()).hexdigest()
            self.assertEqual(actual, entry["sha256"], entry["path"])
        for skill_name in EXPECTED_SKILLS:
            contents = (PLUGIN / "skills" / skill_name / "SKILL.md").read_text(encoding="utf-8")
            self.assertIn("Candidate snapshot hashes (SHA-256)", contents)
            self.assertGreaterEqual(len(re.findall(r"\b[0-9a-f]{64}\b", contents)), 1)
        self.assertTrue((PLUGIN / "scripts" / "eval" / "README.md").is_file())

    def test_mcp_boundary_forbids_unrestricted_fallback(self) -> None:
        boundary = (PLUGIN / "mcp" / "README.md").read_text(encoding="utf-8")
        self.assertIn("trusted", boundary)
        self.assertIn("boundary", boundary)
        self.assertIn("local and user-confirmable", boundary)
        self.assertIn("unrestricted shell or browser control", boundary)
        self.assertIn("typed blocker", boundary)

    def test_installed_only_evaluator_is_package_bounded(self) -> None:
        evaluator = PLUGIN / "scripts" / "eval" / "validate_candidate.py"
        completed = subprocess.run(
            [sys.executable, str(evaluator), "--installed-only"],
            check=True,
            capture_output=True,
            text=True,
        )
        result = json.loads(completed.stdout)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["verification_scope"], "package_integrity_only")
        self.assertFalse(result["comparison_ready"])
        self.assertEqual(result["fresh_main"], "not_checked")

    def test_installed_mcp_server_does_not_emit_untrusted_numeric_metrics(self) -> None:
        source = (PLUGIN / "mcp" / "server.py").read_text(encoding="utf-8")
        self.assertIn('"status": "FAIL", "error_class": "NUMERIC_METRICS_NOT_VERIFIABLE"', source)
        self.assertNotIn('"context_items": 4', source)
        self.assertNotIn('"result_quality": 100', source)
        self.assertNotIn('"root_cause_quality": 0', source)


if __name__ == "__main__":
    unittest.main()
