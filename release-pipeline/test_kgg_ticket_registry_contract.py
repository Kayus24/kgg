from __future__ import annotations

import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class KggTicketRegistryContractTests(unittest.TestCase):
    def test_canonical_locations_and_lifecycle_contract_are_documented(self):
        schema = (ROOT / "docs" / "kgg-custom-gpt-action-schema.md").read_text(encoding="utf-8")
        playbook = (ROOT / "docs" / "kgg-custom-gpt-playbook.md").read_text(encoding="utf-8")
        operations = (ROOT / "docs" / "kgg-custom-gpt-knowledge-operations.md").read_text(encoding="utf-8")
        for text in (schema, playbook, operations):
            self.assertIn("Ticket-Metadaten: v1", text)
            self.assertIn("Lifecycle:", text)
            self.assertIn("history.json", text)
        self.assertIn("memory/records", schema)
        self.assertIn("validate_only", schema)
        self.assertIn("Rejected or failed upload runs", schema)

    def test_editor_snapshot_does_not_claim_live_after_knowledge_change(self):
        snapshot = json.loads(
            (ROOT / "docs" / "kgg-custom-gpt-editor-snapshot.json").read_text(encoding="utf-8")
        )
        self.assertEqual("target-pending-live-editor-sync", snapshot["syncStatus"])
        self.assertNotIn("lastVerifiedAt", snapshot)
        self.assertNotIn("lastVerifiedMainCommit", snapshot)


if __name__ == "__main__":
    unittest.main()
