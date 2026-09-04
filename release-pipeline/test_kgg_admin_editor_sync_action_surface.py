#!/usr/bin/env python3
"""Contract tests for the Phase-3 Admin editor-sync Action surface."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PIPELINE = ROOT / "release-pipeline"
sys.path.insert(0, str(PIPELINE))

import kgg_custom_gpt_resource_audit as audit  # noqa: E402

API = ROOT / "docs" / "kgg-custom-gpt-action-api-openapi.yaml"
MANIFEST = ROOT / "docs" / "kgg-custom-gpt-resource-manifest.json"
SNAPSHOT = ROOT / "docs" / "kgg-custom-gpt-editor-snapshot.json"

OLD_ADMIN_API_SHA256 = "eadf91edc3f00b5516baaf178f84a57f46ee78675da2c0d11924553d634b8b08"
ADMIN_READ_SHA256 = "c55030bb9acd46b8940bc518c95383ba00a80c629cd85ef0ab02639fac7bd464"
ADMIN_BOOTSTRAP_SHA256 = "b123c7e0dcf770cdb8d86b62cf4af5e9501ace08eb813b40608f7ed5ce4e4676"
ADMIN_KNOWLEDGE_SHA256 = [
    "708f445be148ded8faec90863860b9cba4503294526c5e9679f7808e599400e6",
    "00996d86c382b4740d4b1be0aa0c5f0e8f313568b96597c0a6cd5dda00f32090",
    "388584bbe581bfe01458657d3a19cbc5a7c5ebf7602a4452a5c8e4bdc1b6f611",
    "526435598da7fdf5a2081588cf18103c839389ea81fc8109ab8e7142a6348688",
]
PATIENT_CONTRACT = {
    "profileVersion": "1.2.0",
    "bootstrap": "689c7b51eca49f7488f3a11a376e3ed218ee72ab6987083739f81ec5baf7a3e2",
    "knowledge": [
        "c28f7edde1fcd1c291b926f2c76a959c070f24135b9bce65aa9efd697578cf3e",
        "1b487391ee3d92b14999bd4d8e232003c00440fefb30377954de293261c25b78",
        "6690fd17e3a9eb09bb7d5db8f24b7020a976a7d812e69ee799bc5b0adc8013e7",
        "25949464f0180ebbec1e5617c7682b6c7202b9d415bf3f9ad29081feff076407",
    ],
    "actions": [
        "7ba1c0e4da45161823dfd34a0ea2c061ab320e191b88dd11e86a546850477ab2",
        "316e7e32e55920ec6417888912c559d4af981b73077cc0a271950458b99cf304",
    ],
}


def normalized_sha(path: Path) -> str:
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def path_block(text: str, workflow: str) -> str:
    marker = f"  /repos/Kayus24/kgg/actions/workflows/{workflow}/dispatches:\n"
    start = text.index(marker)
    end = text.find("\n  /", start + len(marker))
    return text[start:] if end == -1 else text[start:end]


def workflow_input_properties(block: str) -> set[str]:
    inputs = block.index("                inputs:\n")
    part = block[inputs:]
    return set(re.findall(r"(?m)^                    ([a-zA-Z0-9_]+):\s*$", part))


class Phase3ActionSurfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = API.read_text(encoding="utf-8")
        cls.manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        cls.snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
        cls.preflight = path_block(cls.text, "kgg-admin-editor-sync-preflight.yml")
        cls.pr_gate = path_block(cls.text, "kgg-admin-editor-sync-snapshot-pr.yml")

    def test_openapi_yaml_is_syntactically_loadable_when_ruby_is_available(self) -> None:
        ruby = shutil.which("ruby")
        if ruby is None:
            self.skipTest("Ruby YAML parser not installed")
        proc = subprocess.run(
            [ruby, "-e", "require 'yaml'; d=YAML.load_file(ARGV[0]); abort('bad openapi') unless d['openapi']=='3.1.0'", str(API)],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )
        self.assertEqual(0, proc.returncode, proc.stderr)

    def test_operation_ids_are_unique_and_new_operations_exist_once(self) -> None:
        ids = re.findall(r"(?m)^\s+operationId:\s+(\S+)\s*$", self.text)
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(1, ids.count("submitKggAdminEditorSyncPreflight"))
        self.assertEqual(1, ids.count("submitKggAdminEditorSyncSnapshotPr"))
        self.assertLessEqual(len(ids), audit.CUSTOM_GPT_ACTION_LIMIT)

    def test_preflight_has_only_request_id_and_is_non_consequential(self) -> None:
        self.assertEqual({"request_id"}, workflow_input_properties(self.preflight))
        self.assertIn("required: [request_id]", self.preflight)
        self.assertIn("x-openai-isConsequential: false", self.preflight)
        self.assertNotIn("approval_phrase:", self.preflight)
        for forbidden in ("source_sha:", "timestamp:", "snapshot_path:", "snapshot_json:", "resource_hash", "branch_name:"):
            self.assertNotIn(forbidden, self.preflight)

    def test_pr_gate_has_exact_inputs_and_exact_approval(self) -> None:
        self.assertEqual({"request_id", "approval_phrase"}, workflow_input_properties(self.pr_gate))
        self.assertIn("required: [request_id, approval_phrase]", self.pr_gate)
        self.assertIn("enum: [Gut für Main]", self.pr_gate)
        self.assertIn("x-openai-isConsequential: true", self.pr_gate)
        for forbidden in ("source_sha:", "timestamp:", "snapshot_path:", "snapshot_json:", "resource_hash", "branch_name:"):
            self.assertNotIn(forbidden, self.pr_gate)

    def test_contract_documents_human_attestation_server_ownership_and_idempotency(self) -> None:
        for required in (
            "Editor geprüft, Sync zertifizieren.",
            "TARGET_PASS",
            "would_certify",
            "Gut für Main",
            "LIVE_PASS",
            "UTC RFC3339 certification time",
            "current main SHA",
            "snapshot candidate",
            "preserve_live_synced_when_target_unchanged: true",
            "product_commits_do_not_invalidate_unchanged_editor_sync: true",
        ):
            self.assertIn(required, self.text)

    def test_manifest_contains_deterministic_admin_action_hash_and_unchanged_admin_resources(self) -> None:
        prod = self.manifest["production"]
        actions = [item["sha256"] for item in prod["actions"]]
        self.assertEqual(ADMIN_READ_SHA256, actions[0])
        self.assertEqual(normalized_sha(API), actions[1])
        self.assertNotEqual(OLD_ADMIN_API_SHA256, actions[1])
        self.assertEqual(ADMIN_BOOTSTRAP_SHA256, prod["editorBootstrap"]["sha256"])
        self.assertEqual(ADMIN_KNOWLEDGE_SHA256, [item["sha256"] for item in prod["knowledge"]])

    def test_patient_contract_is_fully_unchanged(self) -> None:
        patient = self.manifest["patientProduction"]
        self.assertEqual(PATIENT_CONTRACT["profileVersion"], patient["profileVersion"])
        self.assertEqual(PATIENT_CONTRACT["bootstrap"], patient["editorBootstrap"]["sha256"])
        self.assertEqual(PATIENT_CONTRACT["knowledge"], [item["sha256"] for item in patient["knowledge"]])
        self.assertEqual(PATIENT_CONTRACT["actions"], [item["sha256"] for item in patient["actions"]])

    def test_real_action_drift_refreshes_snapshot_to_pending_and_then_is_idempotent(self) -> None:
        current_actions = [item["sha256"] for item in self.manifest["production"]["actions"]]
        self.assertEqual(current_actions, self.snapshot["actionSha256"])
        self.assertEqual(audit.TARGET_PENDING_SYNC_STATUS, self.snapshot["syncStatus"])
        self.assertNotIn("lastVerifiedAt", self.snapshot)
        self.assertNotIn("lastVerifiedMainCommit", self.snapshot)

        synthetic = dict(self.snapshot)
        synthetic["actionSha256"] = [ADMIN_READ_SHA256, OLD_ADMIN_API_SHA256]
        synthetic["syncStatus"] = audit.LIVE_SYNC_STATUS
        synthetic["lastVerifiedAt"] = "2026-09-03T18:00:00Z"
        synthetic["lastVerifiedMainCommit"] = "a" * 40
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "snapshot.json"
            path.write_text(json.dumps(synthetic, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            audit.refresh_target_snapshot(path, "production")
            refreshed = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(current_actions, refreshed["actionSha256"])
            self.assertEqual(audit.TARGET_PENDING_SYNC_STATUS, refreshed["syncStatus"])
            self.assertNotIn("lastVerifiedAt", refreshed)
            self.assertNotIn("lastVerifiedMainCommit", refreshed)
            before = path.read_bytes()
            audit.refresh_target_snapshot(path, "production")
            self.assertEqual(before, path.read_bytes())


if __name__ == "__main__":
    unittest.main(verbosity=2)
