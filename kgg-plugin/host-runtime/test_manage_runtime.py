"""Synthetic, filesystem-isolated tests; never point at the user's live runtime."""
import hashlib
import importlib.util
import json
from pathlib import Path
from unittest.mock import patch
import tempfile
import unittest

MODULE = Path(__file__).with_name("manage_runtime.py")
spec = importlib.util.spec_from_file_location("kgg_runtime_tool", MODULE)
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


def fake_source(version, catalog=None, *, emit=False):
    return ("SERVER_VERSION = " + repr(version) + "\n"
            + "def tool_catalog():\n"
            + ("    print('MCP protocol pollution')\n" if emit else "")
            + "    return " + repr(catalog if catalog is not None else [{"name": "get_current_state", "inputSchema": {"type": "object"}}]) + "\n")


class RuntimeUpdate(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.catalog = [{"name": "get_current_state", "inputSchema": {"type": "object"}}]
        self.digest = tool.sha(json.dumps(self.catalog, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf8"))
        self.original_sha = self.stage("r1", "1.4.0")
        self.new_sha = self.stage("r2", "1.4.1")
        self.old = tool.candidate(self.root, "r1", self.original_sha, contract=self.digest)
        tool._write_atomic(self.root, "current.json", self.old)

    def stage(self, release, version, catalog=None, emit=False):
        p = self.root / release / "mcp" / "server.py"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(fake_source(version, catalog, emit=emit), encoding="utf8")
        return tool.sha(p.read_bytes())

    def etag(self):
        return tool.sha((self.root / "current.json").read_bytes())

    def promote(self, **kw):
        return tool.promote("r2", self.new_sha, self.etag(), root=self.root, contract=self.digest, **kw)

    def test_positive_promotion_previous_and_rollback(self):
        old_sha = self.etag()
        p = self.promote()
        self.assertEqual(p["state"], "POINTER_SWITCHED_NOT_RESTARTED")
        self.assertEqual(tool.status(self.root, contract=self.digest)["release"], "r2")
        self.assertEqual(json.loads((self.root / "previous.json").read_text())["release"], "r1")
        self.assertNotEqual(old_sha, self.etag())
        res = tool.rollback(self.etag(), root=self.root, contract=self.digest)
        self.assertEqual(res["state"], "POINTER_ROLLED_BACK_NOT_RESTARTED")
        self.assertEqual(tool.status(self.root, contract=self.digest)["release"], "r1")

    def test_repeated_promotion_is_noop(self):
        self.promote()
        p = self.promote()
        self.assertEqual(p["state"], "UNCHANGED")

    def test_stale_active_pointer_is_rejected(self):
        with self.assertRaisesRegex(tool.PromotionError, "active_pointer_changed"):
            tool.promote("r2", self.new_sha, "0"*64, root=self.root, contract=self.digest)

    def test_wrong_pinned_server_hash_rejected(self):
        with self.assertRaisesRegex(tool.PromotionError, "candidate_hash_mismatch"):
            tool.promote("r2", "0"*64, self.etag(), root=self.root, contract=self.digest)
        self.assertEqual(tool.status(self.root, contract=self.digest)["release"], "r1")

    def test_tool_contract_drift_rejected(self):
        self.new_sha = self.stage("r2", "1.4.1", catalog=[{"name": "unsafe_new_tool"}])
        with self.assertRaisesRegex(tool.PromotionError, "tool_contract_or_version_mismatch"):
            self.promote()
        self.assertFalse((self.root / "previous.json").exists())

    def test_version_invalid_rejected(self):
        self.new_sha = self.stage("r2", "2.0-dev")
        with self.assertRaisesRegex(tool.PromotionError, "candidate_invalid_version"):
            self.promote()

    def test_server_protocol_stdout_rejected(self):
        self.new_sha = self.stage("r2", "1.4.1", emit=True)
        with self.assertRaisesRegex(tool.PromotionError, "candidate_protocol_stdout"):
            self.promote()

    def test_release_path_is_bounded(self):
        for unsafe in ["../escape", "..", "."]:
            with self.assertRaises(tool.PromotionError):
                tool.candidate(self.root, unsafe, self.new_sha, contract=self.digest)
        self.assertEqual(tool.status(self.root, contract=self.digest)["release"], "r1")

    def test_candidate_file_tampering_blocks_promotion(self):
        self.stage("r2", "1.4.2")
        with self.assertRaisesRegex(tool.PromotionError, "candidate_hash_mismatch"):
            self.promote()

    def test_current_file_tampering_blocks_promotion(self):
        f = self.root / "r1" / "mcp" / "server.py"
        f.write_text(fake_source("1.4.2"), encoding="utf8")
        with self.assertRaisesRegex(tool.PromotionError, "release_hash_mismatch"):
            self.promote()

    def test_post_switch_failure_rolls_back(self):
        baseline = self.old.copy()
        def fail():
            raise RuntimeError("synthetic failed health probe")
        with self.assertRaisesRegex(RuntimeError, "synthetic failed"):
            self.promote(post_switch_check=fail)
        self.assertEqual(tool.status(self.root, contract=self.digest), baseline)

    def test_invalid_previous_prevents_rollback(self):
        self.promote()
        old = self.etag()
        (self.root / "previous.json").write_text('{"release":"../escape"}', encoding="utf8")
        with self.assertRaises(tool.PromotionError):
            tool.rollback(self.etag(), root=self.root, contract=self.digest)
        self.assertEqual(self.etag(), old)

    def test_pointer_swap_leaves_no_pending_files(self):
        self.promote()
        self.assertFalse(list(self.root.glob("*.pending")))


class VersionedContractTransitionTests(unittest.TestCase):
    """Synthetic transition: never reads or modifies the installed KGG host."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.old_tools = [{"name": "get_current_state", "inputSchema": {}}]
        self.new_tools = [{"name": "get_current_state", "inputSchema": {"new": True}}]
        self.old_digest = tool.sha(json.dumps(self.old_tools, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode())
        self.new_digest = tool.sha(json.dumps(self.new_tools, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode())
        self.approved = (self.old_digest, self.new_digest)
        self.launcher = self.root / "launcher.py"
        self.candidate_launcher = MODULE.with_name("kgg_ui_lab_mcp_real_v2_candidate.py")
        self.patches = patch.multiple(
            tool,
            APPROVED_CONTRACT=self.old_digest,
            STAGED_PREVIEW_CONTRACT=self.new_digest,
            APPROVED_CONTRACTS=self.approved,
            TRUSTED_MIGRATED_LAUNCHER=self.launcher,
            TRUSTED_MIGRATED_LAUNCHER_SHA256=tool.sha(self.candidate_launcher.read_bytes()),
        )
        self.patches.start()
        self.addCleanup(self.patches.stop)
        self.old_sha = self.stage("old", "1.4.0", self.old_tools)
        self.new_sha = self.stage("new", "1.5.0", self.new_tools)
        self.old_manifest = tool.candidate(self.root, "old", self.old_sha, contract=self.approved)
        tool._write_atomic(self.root, "current.json", self.old_manifest)

    def stage(self, name, version, catalog):
        f = self.root / name / "mcp" / "server.py"
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(fake_source(version, catalog), encoding="utf-8")
        return tool.sha(f.read_bytes())

    def etag(self):
        return tool.sha((self.root / "current.json").read_bytes())

    def promote(self, approved=False):
        return tool.promote(
            "new", self.new_sha, self.etag(), root=self.root,
            contract=self.approved, approve_contract_transition=approved,
        )

    def test_default_only_one_runtime_would_refuse_new_catalog(self):
        with self.assertRaisesRegex(tool.PromotionError, "tool_contract_or_version_mismatch"):
            tool.candidate(self.root, "new", self.new_sha, contract=self.old_digest)

    def test_cross_contract_promotion_requires_explicit_operator_flag(self):
        before = self.etag()
        with self.assertRaisesRegex(tool.PromotionError, "contract_transition_requires_explicit_operator_enable"):
            self.promote()
        self.assertEqual(before, self.etag())
        self.assertFalse((self.root / "previous.json").exists())

    def test_cross_contract_promotion_rejects_missing_or_wrong_launcher(self):
        before = self.etag()
        with self.assertRaisesRegex(tool.PromotionError, "trusted_dual_contract_launcher_not_installed"):
            self.promote(approved=True)
        self.launcher.write_bytes(b"unauthorized fake launcher")
        with self.assertRaisesRegex(tool.PromotionError, "trusted_dual_contract_launcher_not_installed"):
            self.promote(approved=True)
        self.assertEqual(before, self.etag())
        self.assertFalse((self.root / "previous.json").exists())

    def test_versioned_promotion_and_old_contract_rollback(self):
        self.launcher.write_bytes(self.candidate_launcher.read_bytes())
        old_pointer = self.etag()
        outcome = self.promote(approved=True)
        self.assertEqual(outcome["state"], "POINTER_SWITCHED_NOT_RESTARTED")
        self.assertEqual(tool.status(self.root, contract=self.approved)["tool_contract_sha256"], self.new_digest)
        self.assertNotEqual(old_pointer, self.etag())
        restored = tool.rollback(self.etag(), root=self.root, contract=self.approved)
        self.assertEqual(restored["state"], "POINTER_ROLLED_BACK_NOT_RESTARTED")
        self.assertEqual(tool.status(self.root, contract=self.approved)["tool_contract_sha256"], self.old_digest)

    def test_rollback_cannot_reactivate_new_contract_from_old(self):
        new = tool.candidate(self.root, "new", self.new_sha, contract=self.approved)
        tool._write_atomic(self.root, "previous.json", new)
        before = self.etag()
        with self.assertRaisesRegex(tool.PromotionError, "rollback_cannot_activate_new_contract"):
            tool.rollback(before, root=self.root, contract=self.approved)
        self.assertEqual(before, self.etag())

    def test_unknown_catalog_or_old_version_with_new_schema_rejected(self):
        with self.assertRaisesRegex(tool.PromotionError, "tool_contract_or_version_mismatch"):
            bad_sha = self.stage("new", "1.5.0", [{"name": "unreviewed_tool"}])
            tool.candidate(self.root, "new", bad_sha, contract=self.approved)
        old_version_sha = self.stage("new", "1.4.0", self.new_tools)
        with self.assertRaisesRegex(tool.PromotionError, "preview_contract_requires_server_1_5_0"):
            tool.candidate(self.root, "new", old_version_sha, contract=self.approved)

    def test_unsupported_contract_policy_rejected(self):
        for bad in [(), (self.old_digest,) * 2, ["not-an-immutable-policy"], ("x" * 64, "g" * 64)]:
            with self.subTest(bad=bad), self.assertRaisesRegex(tool.PromotionError, "approved_contract_policy_invalid"):
                tool.candidate(self.root, "old", self.old_sha, contract=bad)

    def test_migrated_launcher_source_hash_is_pinned(self):
        self.assertEqual(
            tool.sha(self.candidate_launcher.read_bytes()),
            tool.TRUSTED_MIGRATED_LAUNCHER_SHA256,
        )


if __name__ == "__main__":
    unittest.main()
