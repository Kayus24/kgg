"""Synthetic, filesystem-isolated tests; never point at the user's live runtime."""
import hashlib
import importlib.util
import json
from pathlib import Path
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


if __name__ == "__main__":
    unittest.main()
