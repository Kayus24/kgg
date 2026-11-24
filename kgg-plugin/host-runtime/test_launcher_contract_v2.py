"""Synthetic selection tests for a staged launcher. Never call main()."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

LAUNCHER = Path(__file__).with_name("kgg_ui_lab_mcp_real_v2_candidate.py")
spec = importlib.util.spec_from_file_location("kgg_launcher_candidate", LAUNCHER)
launcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(launcher)


class MigratedLauncherTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.old_catalog = [{"name": "get_current_state"}]
        self.new_catalog = [{"name": "get_current_state"}, {"name": "new_preview_dispatch"}]
        def digest(v):
            return hashlib.sha256(json.dumps(v, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
        self.old_digest = digest(self.old_catalog)
        self.new_digest = digest(self.new_catalog)
        self.patches = patch.multiple(
            launcher,
            RUNTIME_ROOT=self.root,
            APPROVED_TOOL_CONTRACT_SHA256=frozenset((self.old_digest, self.new_digest)),
            PREVIEW_TOOL_CONTRACT_SHA256=self.new_digest,
        )
        self.patches.start()
        self.addCleanup(self.patches.stop)

    def stage(self, name, version, catalog):
        f = self.root / name / "mcp" / "server.py"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(
            "SERVER_VERSION = " + repr(version) + "\n"
            "def tool_catalog():\n    return " + repr(catalog) + "\n",
            encoding="utf-8",
        )
        return {"schema": launcher.SCHEMA, "release": name,
                "server_sha256": hashlib.sha256(f.read_bytes()).hexdigest(),
                "server_version": version,
                "tool_contract_sha256": self.new_digest if catalog == self.new_catalog else self.old_digest}

    def select(self, manifest):
        f = self.root / "current.json"
        f.write_text(json.dumps(manifest), encoding="utf-8")
        return launcher.select_server(f)

    def test_old_runtime_keeps_old_operations(self):
        server, digest = self.select(self.stage("old", "1.4.0", self.old_catalog))
        self.assertEqual(server.parent.parent.name, "old")
        self.assertEqual(digest, self.old_digest)
        self.assertNotIn("submitKggVerifiedPatientPrPreview", launcher.workflow_operations(digest))
        self.assertIn("submitKggPreviewAuto", launcher.workflow_operations(digest))

    def test_new_runtime_enables_only_the_staged_operation(self):
        server, digest = self.select(self.stage("new", "1.5.0", self.new_catalog))
        self.assertEqual(server.parent.parent.name, "new")
        self.assertEqual(digest, self.new_digest)
        self.assertIn("submitKggVerifiedPatientPrPreview", launcher.workflow_operations(digest))
        self.assertEqual(launcher.workflow_operations(digest).count("submitKggVerifiedPatientPrPreview"), 1)

    def test_new_catalog_requires_version_1_5_0(self):
        with self.assertRaisesRegex(RuntimeError, "new_contract_requires_version_1_5_0"):
            self.select(self.stage("new", "1.4.0", self.new_catalog))

    def test_unknown_catalog_refused(self):
        bad = self.stage("unreviewed", "1.5.0", [{"name": "unknown"}])
        with self.assertRaisesRegex(RuntimeError, "runtime_contract_mismatch"):
            self.select(bad)

    def test_server_bytes_tampered_after_manifest_refused(self):
        manifest = self.stage("old", "1.4.0", self.old_catalog)
        (self.root / "old" / "mcp" / "server.py").write_text("bad", encoding="utf-8")
        with self.assertRaisesRegex(RuntimeError, "runtime_source_changed"):
            self.select(manifest)

    def test_unsafe_release_path_refused(self):
        manifest = self.stage("old", "1.4.0", self.old_catalog)
        manifest["release"] = "../outside"
        with self.assertRaisesRegex(RuntimeError, "invalid_runtime_release"):
            self.select(manifest)

    def test_unreviewed_contract_cannot_supply_workflow_permissions(self):
        with self.assertRaisesRegex(RuntimeError, "runtime_contract_mismatch"):
            launcher.workflow_operations("0" * 64)


if __name__ == "__main__":
    unittest.main()
