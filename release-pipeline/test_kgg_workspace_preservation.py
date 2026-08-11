#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock


HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import kgg_workspace_preservation as preservation  # noqa: E402


def git(path: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [
            "git",
            "-c",
            "core.longpaths=true",
            "-c",
            "color.ui=false",
            "-C",
            str(path),
            *args,
        ],
        env=preservation.sanitized_git_environment(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )


def init_repo(path: Path) -> None:
    path.mkdir(parents=True)
    git(path, "init", "--quiet")
    git(path, "config", "user.name", "KGG Preservation Test")
    git(path, "config", "user.email", "preservation-test@example.invalid")
    (path / "tracked-a.txt").write_text("a0\n", encoding="utf-8", newline="\n")
    (path / "tracked-b.txt").write_text("b0\n", encoding="utf-8", newline="\n")
    git(path, "add", "tracked-a.txt", "tracked-b.txt")
    git(path, "commit", "--quiet", "-m", "fixture")


class WorkspacePreservationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="kgg-preservation-")
        self.base = Path(self.temp.name)
        self.links: list[Path] = []

    def tearDown(self) -> None:
        for link in self.links:
            try:
                if link.exists() or link.is_symlink():
                    os.rmdir(preservation._fs_path(link))
            except OSError:
                pass
        shutil.rmtree(preservation._fs_path(self.base), ignore_errors=True)
        self.temp.cleanup()

    def _make_directory_alias(self, target: Path, alias: Path) -> bool:
        try:
            os.symlink(target, alias, target_is_directory=True)
        except (OSError, NotImplementedError):
            if os.name != "nt":
                return False
            process = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(alias), str(target)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
            if process.returncode != 0:
                return False
        self.links.append(alias)
        return True

    def _configure_side_effect_filter(
        self, repo: Path, driver: str, marker: Path
    ) -> None:
        script = self.base / f"filter-{driver}-side-effect.py"
        script.write_text(
            "from pathlib import Path\n"
            "import sys\n"
            "Path(sys.argv[1]).write_text('FILTER RAN', encoding='utf-8')\n"
            "sys.stdout.buffer.write(sys.stdin.buffer.read())\n",
            encoding="utf-8",
            newline="\n",
        )
        command = f'"{sys.executable}" "{script}" "{marker}"'
        git(repo, "config", f"filter.{driver}.clean", command)

    def test_porcelain_counts_staged_unstaged_and_each_untracked_file(self) -> None:
        workspace = self.base / "workspace"
        repo = workspace / "repo"
        init_repo(repo)
        (repo / "tracked-a.txt").write_text("a1\n", encoding="utf-8")
        (repo / "tracked-b.txt").write_text("b1\n", encoding="utf-8")
        git(repo, "add", "tracked-b.txt")
        (repo / "new-dir").mkdir()
        (repo / "new-dir" / "one.txt").write_text("one", encoding="utf-8")
        (repo / "new-dir" / "two.txt").write_text("two", encoding="utf-8")

        result = preservation.audit_workspace(workspace)
        self.assertEqual(1, len(result.worktrees))
        status = result.worktrees[0].status
        self.assertEqual(["tracked-b.txt"], status.staged_paths)
        self.assertEqual(["tracked-a.txt"], status.unstaged_paths)
        self.assertEqual(
            ["new-dir/one.txt", "new-dir/two.txt"], status.untracked_paths
        )
        self.assertEqual(4, len(status.dirty_paths))
        totals = preservation.audit_to_dict(result)["totals"]
        self.assertEqual(1, totals["staged"])
        self.assertEqual(1, totals["unstaged"])
        self.assertEqual(2, totals["untracked"])
        self.assertEqual(4, totals["dirtyPaths"])

    def test_inherited_git_routing_environment_cannot_redirect_audit(self) -> None:
        workspace = self.base / "workspace"
        target = workspace / "target"
        other = self.base / "other"
        init_repo(target)
        init_repo(other)
        target_head = git(target, "rev-parse", "HEAD").stdout.decode().strip()
        (other / "other-only.txt").write_text("other", encoding="utf-8")

        poisoned = {
            "GIT_DIR": str(other / ".git"),
            "GIT_WORK_TREE": str(other),
            "GIT_INDEX_FILE": str(other / ".git" / "index"),
        }
        with mock.patch.dict(os.environ, poisoned, clear=False):
            result = preservation.audit_workspace(workspace)

        self.assertEqual(1, len(result.worktrees))
        self.assertEqual(target_head, result.worktrees[0].head)
        self.assertEqual(target.resolve(), result.worktrees[0].physical_path)

    def test_audit_refuses_external_filter_before_it_can_run(self) -> None:
        workspace = self.base / "workspace"
        repo = workspace / "repo"
        marker = self.base / "filter-ran.txt"
        init_repo(repo)
        (repo / ".gitattributes").write_text(
            "*.txt filter=set\n",
            encoding="utf-8",
            newline="\n",
        )
        git(repo, "add", ".gitattributes")
        git(repo, "commit", "--quiet", "-m", "filter attributes")
        self._configure_side_effect_filter(repo, "set", marker)
        (repo / "tracked-a.txt").write_text("would invoke filter\n", encoding="utf-8")

        with self.assertRaisesRegex(
            preservation.PreservationError, "external Git filter drivers"
        ):
            preservation.audit_workspace(workspace)
        self.assertFalse(marker.exists())

    def test_audit_allows_configured_but_inactive_filter(self) -> None:
        workspace = self.base / "workspace"
        repo = workspace / "repo"
        marker = self.base / "inactive-filter-ran.txt"
        init_repo(repo)
        self._configure_side_effect_filter(repo, "inactive", marker)

        result = preservation.audit_workspace(workspace)

        self.assertEqual(1, len(result.worktrees))
        self.assertFalse(marker.exists())

    def test_evidence_rechecks_filter_activation_before_status(self) -> None:
        workspace = self.base / "workspace"
        repo = workspace / "repo"
        marker = self.base / "late-filter-ran.txt"
        init_repo(repo)
        record = preservation.audit_workspace(workspace).worktrees[0]
        (repo / ".gitattributes").write_text(
            "*.txt filter=late\n", encoding="utf-8", newline="\n"
        )
        self._configure_side_effect_filter(repo, "late", marker)

        with self.assertRaisesRegex(
            preservation.PreservationError, "external Git filter drivers"
        ):
            preservation._worktree_evidence(record)
        self.assertFalse(marker.exists())

    def test_nested_gitlink_filter_is_rejected_without_parent_recursion(self) -> None:
        workspace = self.base / "workspace"
        repo = workspace / "repo"
        nested = repo / "nested"
        marker = self.base / "nested-filter-ran.txt"
        init_repo(repo)
        init_repo(nested)
        git(repo, "add", "nested")
        git(repo, "commit", "--quiet", "-m", "nested gitlink")
        (nested / ".gitattributes").write_text(
            "*.txt filter=set\n", encoding="utf-8", newline="\n"
        )
        git(nested, "add", ".gitattributes")
        git(nested, "commit", "--quiet", "-m", "nested attributes")
        self._configure_side_effect_filter(nested, "set", marker)
        (nested / "tracked-a.txt").write_text(
            "nested would invoke filter\n", encoding="utf-8"
        )

        with self.assertRaisesRegex(
            preservation.PreservationError, "external Git filter drivers"
        ):
            preservation.audit_workspace(workspace)
        self.assertFalse(marker.exists())

    def test_junction_or_symlink_alias_is_logical_but_physically_deduplicated(self) -> None:
        workspace = self.base / "workspace"
        repo = workspace / "repo"
        init_repo(repo)
        alias = workspace / "repo-alias"
        if not self._make_directory_alias(repo, alias):
            self.skipTest("directory symlink/junction creation is unavailable")

        result = preservation.audit_workspace(workspace)
        self.assertEqual(1, len(result.worktrees))
        self.assertEqual(2, len(result.logical_git_roots))
        aliases = result.worktrees[0].aliases
        self.assertIn("repo-alias", {Path(item).name for item in aliases})
        self.assertIn("repo", {Path(item).name for item in aliases})

    def test_conflicted_path_is_counted_explicitly(self) -> None:
        workspace = self.base / "workspace"
        repo = workspace / "repo"
        init_repo(repo)
        original_branch = git(repo, "branch", "--show-current").stdout.decode().strip()
        (repo / "conflict.txt").write_text("base\n", encoding="utf-8", newline="\n")
        git(repo, "add", "conflict.txt")
        git(repo, "commit", "--quiet", "-m", "conflict base")
        git(repo, "switch", "--quiet", "-c", "conflicting-side")
        (repo / "conflict.txt").write_text("side\n", encoding="utf-8", newline="\n")
        git(repo, "commit", "--quiet", "-am", "side")
        git(repo, "switch", "--quiet", original_branch)
        (repo / "conflict.txt").write_text("main\n", encoding="utf-8", newline="\n")
        git(repo, "commit", "--quiet", "-am", "main")
        merge = subprocess.run(
            ["git", "-C", str(repo), "merge", "conflicting-side"],
            env=preservation.sanitized_git_environment(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertNotEqual(0, merge.returncode)

        result = preservation.audit_workspace(workspace)
        status = result.worktrees[0].status
        self.assertEqual(["conflict.txt"], status.conflict_paths)
        totals = preservation.audit_to_dict(result)["totals"]
        self.assertEqual(1, totals["conflicts"])
        with self.assertRaisesRegex(
            preservation.PreservationError, "unmerged index stages"
        ):
            preservation.capture_workspace(workspace, self.base / "rescue")

    def test_capture_includes_shared_git_mirror_bundles_diffs_and_long_untracked(self) -> None:
        workspace = self.base / "workspace"
        repo = workspace / "repo"
        external = self.base / "external-worktree"
        alternate = self.base / "alternate.git"
        external_lfs = self.base / "external-lfs"
        external_hooks = self.base / "external-hooks"
        rescue = self.base / "rescue"
        init_repo(repo)
        (repo / ".gitignore").write_text("ignored-dir/\n", encoding="utf-8")
        (repo / "assume-hidden.txt").write_text("assume base\n", encoding="utf-8")
        (repo / "skip-hidden.txt").write_text("skip base\n", encoding="utf-8")
        git(repo, "add", ".gitignore", "assume-hidden.txt", "skip-hidden.txt")
        git(repo, "commit", "--quiet", "-m", "ignore fixture")
        git(repo, "update-index", "--assume-unchanged", "assume-hidden.txt")
        git(repo, "update-index", "--skip-worktree", "skip-hidden.txt")
        (repo / "assume-hidden.txt").write_bytes(b"assume raw changed\r\n")
        (repo / "skip-hidden.txt").write_bytes(b"skip raw changed\r\n")
        hidden_status = git(repo, "status", "--porcelain=v2", "-z").stdout
        self.assertNotIn(b"assume-hidden.txt", hidden_status)
        self.assertNotIn(b"skip-hidden.txt", hidden_status)
        external_lfs.mkdir()
        (external_lfs / "lfs-object.bin").write_bytes(b"external lfs object")
        git(repo, "config", "lfs.storage", str(external_lfs.resolve()))
        git(repo, "worktree", "add", "--quiet", "--detach", str(external), "HEAD")
        external_hooks.mkdir()
        (external_hooks / "pre-commit.disabled").write_bytes(b"external hook evidence")
        git(repo, "config", "core.hooksPath", str(external_hooks.resolve()))

        alternate.mkdir()
        subprocess.run(
            ["git", "init", "--quiet", "--bare"],
            cwd=alternate,
            env=preservation.sanitized_git_environment(),
            check=True,
        )
        alternate_payload = self.base / "alternate-payload.bin"
        alternate_payload.write_bytes(b"unreachable alternate object")
        alternate_sha = preservation.run_git_dir(
            alternate, "hash-object", "-w", alternate_payload
        ).stdout.decode().strip()
        alternates_file = repo / ".git" / "objects" / "info" / "alternates"
        alternates_file.write_text(
            str((alternate / "objects").resolve()) + "\n", encoding="utf-8"
        )

        unreachable_payload = self.base / "unreachable-payload.bin"
        unreachable_payload.write_bytes(b"unreachable common object")
        unreachable_sha = git(repo, "hash-object", "-w", str(unreachable_payload)).stdout.decode().strip()

        (repo / "tracked-a.txt").write_text("unstaged\n", encoding="utf-8")
        (repo / "intent-to-add.txt").write_text("intent\n", encoding="utf-8")
        git(repo, "add", "-N", "intent-to-add.txt")
        (external / "tracked-b.txt").write_text("staged\n", encoding="utf-8")
        git(external, "add", "tracked-b.txt")
        ignored_source = external / "ignored-dir" / "ignored.bin"
        ignored_source.parent.mkdir()
        ignored_source.write_bytes(b"ignored evidence")
        external_git_dir = Path(
            git(external, "rev-parse", "--absolute-git-dir").stdout.decode().strip()
        )
        (external_git_dir / "preservation-state").write_bytes(b"worktree admin state")
        long_relative = Path(*(["segment-" + "x" * 24] * 7)) / "evidence.bin"
        long_source = external / long_relative
        os.makedirs(preservation._fs_path(long_source.parent), exist_ok=True)
        with open(preservation._fs_path(long_source), "wb") as handle:
            handle.write(b"long-path-evidence\x00\xff")
        workspace.mkdir(exist_ok=True)
        (workspace / "important-root.html").write_bytes(b"<p>evidence</p>\n")
        workspace_loose = workspace / "loose" / "nested" / "evidence.txt"
        workspace_loose.parent.mkdir(parents=True)
        workspace_loose.write_bytes(b"nested loose evidence")

        destination = preservation.capture_workspace(
            workspace,
            rescue,
            now=datetime(2026, 8, 10, 12, 34, 56, 123456, tzinfo=timezone.utc),
        )
        self.assertEqual("run-20260810T123456.123456Z", destination.name)
        self.assertTrue((destination / "CAPTURE_COMPLETE.txt").is_file())
        tree_hashes = json.loads((destination / "CAPTURE_SHA256.json").read_text("utf-8"))
        self.assertTrue(
            any(item["path"].endswith("/mirror.git/HEAD") for item in tree_hashes)
        )
        self.assertFalse(any(rescue.glob(".run-*.partial-*")))

        inventory = json.loads((destination / "inventory.json").read_text("utf-8"))
        self.assertEqual(2, inventory["totals"]["physicalWorktrees"])
        self.assertEqual(1, inventory["totals"]["commonGitDirs"])
        self.assertEqual(1, inventory["totals"]["alternateObjectDirs"])
        self.assertEqual(1, inventory["totals"]["externalLfsDirs"])
        self.assertEqual(1, inventory["totals"]["externalHookDirs"])
        self.assertEqual(1, inventory["totals"]["ignored"])
        self.assertEqual(1, inventory["totals"]["workspaceLooseFiles"])
        external_entry = next(
            item
            for item in inventory["worktrees"]
            if Path(item["path"]).name == "external-worktree"
        )
        repo_entry = next(
            item for item in inventory["worktrees"] if Path(item["path"]).name == "repo"
        )
        repo_capture = destination / "worktrees" / repo_entry["id"]
        self.assertEqual(
            (repo / ".git" / "index").read_bytes(),
            (repo_capture / "index.raw").read_bytes(),
        )
        self.assertNotIn(
            b"intent-to-add.txt",
            git(repo, "diff", "--cached", "--name-only").stdout,
        )
        self.assertIn(
            b"intent-to-add.txt", git(repo, "diff", "--name-only").stdout
        )
        self.assertEqual(
            b"assume raw changed\r\n",
            (repo_capture / "tracked-worktree" / "assume-hidden.txt").read_bytes(),
        )
        self.assertEqual(
            b"skip raw changed\r\n",
            (repo_capture / "tracked-worktree" / "skip-hidden.txt").read_bytes(),
        )
        self.assertTrue(external_entry["outsideWorkspace"])
        external_capture = destination / "worktrees" / external_entry["id"]
        hashes = json.loads(
            (external_capture / "untracked-hashes.json").read_text("utf-8")
        )
        expected_relative = long_relative.as_posix()
        self.assertEqual([expected_relative], [item["path"] for item in hashes])
        copied = external_capture / "untracked" / long_relative
        self.assertEqual(preservation.sha256_file(long_source), preservation.sha256_file(copied))
        self.assertTrue((external_capture / "head.bundle").is_file())
        self.assertTrue((external_capture / "staged.patch").read_bytes())
        self.assertEqual(
            (external_git_dir / "index").read_bytes(),
            (external_capture / "index.raw").read_bytes(),
        )
        self.assertEqual(
            b"worktree admin state",
            (
                external_capture
                / "git-admin-physical"
                / "preservation-state"
            ).read_bytes(),
        )
        ignored_hashes = json.loads(
            (external_capture / "ignored-hashes.json").read_text("utf-8")
        )
        self.assertEqual(["ignored-dir/ignored.bin"], [item["path"] for item in ignored_hashes])
        self.assertEqual(
            ignored_source.read_bytes(),
            (external_capture / "ignored" / "ignored-dir" / "ignored.bin").read_bytes(),
        )

        repository_capture = destination / "repositories" / "repository-001"
        self.assertTrue((repository_capture / "repository.bundle").is_file())
        self.assertTrue((repository_capture / "mirror.git").is_dir())
        self.assertTrue((repository_capture / "common-git-physical" / "config").is_file())
        self.assertTrue(
            (
                repository_capture
                / "common-git-physical"
                / "objects"
                / unreachable_sha[:2]
                / unreachable_sha[2:]
            ).is_file()
        )
        self.assertEqual(
            b"external lfs object",
            (
                repository_capture
                / "external-lfs-dirs"
                / "lfs-001"
                / "storage-physical"
                / "lfs-object.bin"
            ).read_bytes(),
        )
        self.assertEqual(
            b"external hook evidence",
            (
                repository_capture
                / "external-hook-dirs"
                / "hooks-001"
                / "hooks-physical"
                / "pre-commit.disabled"
            ).read_bytes(),
        )
        self.assertTrue(
            (
                repository_capture
                / "alternate-object-dirs"
                / "alternate-001"
                / "objects-physical"
                / alternate_sha[:2]
                / alternate_sha[2:]
            ).is_file()
        )
        verify = subprocess.run(
            [
                "git",
                "--git-dir",
                str(repository_capture / "mirror.git"),
                "fsck",
                "--full",
                "--strict",
            ],
            env=preservation.sanitized_git_environment(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(0, verify.returncode, verify.stderr.decode(errors="replace"))
        self.assertEqual(
            b"<p>evidence</p>\n",
            (destination / "workspace-root-files" / "important-root.html").read_bytes(),
        )
        self.assertEqual(
            b"nested loose evidence",
            (
                destination
                / "workspace-loose-files"
                / "loose"
                / "nested"
                / "evidence.txt"
            ).read_bytes(),
        )
        self.assertIn("git apply --index --binary", (destination / "RESTORE.md").read_text("utf-8"))

        capture_evidence = json.loads(
            (destination / "capture-evidence.json").read_text("utf-8")
        )
        final_audit = preservation.audit_workspace(workspace)
        records = {record.id: record for record in final_audit.worktrees}
        nested_worktrees = {
            record.physical_key: record.id for record in final_audit.worktrees
        }
        for worktree_id, manifest_name, label in (
            (
                repo_entry["id"],
                "tracked-worktree-hashes.json",
                "tracked worktree",
            ),
            (external_entry["id"], "untracked-hashes.json", "untracked"),
            (external_entry["id"], "ignored-hashes.json", "ignored"),
        ):
            capture_dir = destination / "worktrees" / worktree_id
            manifest_path = capture_dir / manifest_name
            original = manifest_path.read_bytes()
            manifest = json.loads(original.decode("utf-8"))
            self.assertTrue(manifest)
            for tampered in (manifest[:-1], [*manifest, manifest[0]]):
                try:
                    manifest_path.write_bytes(preservation._json_bytes(tampered))
                    with self.assertRaisesRegex(
                        preservation.PreservationError,
                        f"{label} manifest membership changed",
                    ):
                        preservation._verify_final_worktree(
                            records[worktree_id],
                            capture_dir,
                            capture_evidence["worktrees"][worktree_id],
                            nested_worktrees,
                        )
                finally:
                    manifest_path.write_bytes(original)

    def test_capture_refuses_destination_overlap(self) -> None:
        workspace = self.base / "workspace"
        repo = workspace / "repo"
        init_repo(repo)
        with self.assertRaisesRegex(preservation.PreservationError, "overlaps"):
            preservation.capture_workspace(workspace, workspace / "rescue")

    def test_failed_final_directory_promotion_never_claims_complete(self) -> None:
        workspace = self.base / "workspace"
        repo = workspace / "repo"
        rescue = self.base / "rescue"
        init_repo(repo)
        real_replace = preservation.os.replace

        def fail_final_promotion(source: str, destination: str) -> None:
            source_name = Path(preservation._display_path(source)).name
            destination_name = Path(preservation._display_path(destination)).name
            if source_name.startswith(".run-") and destination_name.startswith("run-"):
                raise OSError("intentional final promotion failure")
            real_replace(source, destination)

        with mock.patch.object(
            preservation.os, "replace", side_effect=fail_final_promotion
        ):
            with self.assertRaisesRegex(OSError, "intentional final promotion failure"):
                preservation.capture_workspace(workspace, rescue)

        partials = list(rescue.glob(".run-*.partial-*"))
        self.assertEqual(1, len(partials))
        self.assertTrue((partials[0] / "CAPTURE_FAILED.txt").is_file())
        self.assertFalse((partials[0] / "CAPTURE_COMPLETE.txt").exists())
        self.assertFalse(any(rescue.glob("run-*")))

    def test_failed_complete_marker_promotion_never_claims_complete(self) -> None:
        workspace = self.base / "workspace"
        repo = workspace / "repo"
        rescue = self.base / "rescue"
        init_repo(repo)
        real_replace = preservation.os.replace

        def fail_marker_promotion(source: str, destination: str) -> None:
            source_name = Path(preservation._display_path(source)).name
            if source_name == ".CAPTURE_COMPLETE.pending":
                raise OSError("intentional marker promotion failure")
            real_replace(source, destination)

        with mock.patch.object(
            preservation.os, "replace", side_effect=fail_marker_promotion
        ):
            with self.assertRaisesRegex(OSError, "intentional marker promotion failure"):
                preservation.capture_workspace(workspace, rescue)

        finals = list(rescue.glob("run-*"))
        self.assertEqual(1, len(finals))
        self.assertTrue((finals[0] / "CAPTURE_FAILED.txt").is_file())
        self.assertFalse((finals[0] / "CAPTURE_COMPLETE.txt").exists())

    def test_failed_complete_marker_write_never_claims_complete(self) -> None:
        workspace = self.base / "workspace"
        repo = workspace / "repo"
        rescue = self.base / "rescue"
        init_repo(repo)
        real_write = preservation._write_new_text

        def fail_pending_write(path: Path, text: str) -> None:
            if path.name == ".CAPTURE_COMPLETE.pending":
                raise OSError("intentional marker write failure")
            real_write(path, text)

        with mock.patch.object(
            preservation, "_write_new_text", side_effect=fail_pending_write
        ):
            with self.assertRaisesRegex(OSError, "intentional marker write failure"):
                preservation.capture_workspace(workspace, rescue)

        finals = list(rescue.glob("run-*"))
        self.assertEqual(1, len(finals))
        self.assertTrue((finals[0] / "CAPTURE_FAILED.txt").is_file())
        self.assertFalse((finals[0] / "CAPTURE_COMPLETE.txt").exists())

    def test_capture_refuses_stale_registered_worktree(self) -> None:
        workspace = self.base / "workspace"
        repo = workspace / "repo"
        external = self.base / "soon-missing"
        init_repo(repo)
        git(repo, "worktree", "add", "--quiet", "--detach", str(external), "HEAD")
        shutil.rmtree(external)
        result = preservation.audit_workspace(workspace)
        self.assertTrue(result.warnings)
        with self.assertRaisesRegex(preservation.PreservationError, "stale/inaccessible"):
            preservation.capture_workspace(workspace, self.base / "rescue")

    def test_capture_refuses_git_admin_junction_or_symlink(self) -> None:
        workspace = self.base / "workspace"
        repo = workspace / "repo"
        outside = self.base / "outside-admin"
        init_repo(repo)
        outside.mkdir()
        alias = repo / ".git" / "unsafe-admin-link"
        if not self._make_directory_alias(outside, alias):
            self.skipTest("directory symlink/junction creation is unavailable")
        with self.assertRaisesRegex(
            preservation.PreservationError, "physical tree contains unsupported"
        ):
            preservation.capture_workspace(workspace, self.base / "rescue")

    def test_capture_refuses_untracked_link_that_escapes_worktree(self) -> None:
        workspace = self.base / "workspace"
        repo = workspace / "repo"
        outside = self.base / "outside.txt"
        init_repo(repo)
        outside.write_text("outside", encoding="utf-8")
        link = repo / "untracked-link.txt"
        try:
            os.symlink(outside, link)
        except (OSError, NotImplementedError):
            self.skipTest("file symlink creation is unavailable")
        with self.assertRaisesRegex(preservation.PreservationError, "escapes|special"):
            preservation.capture_workspace(workspace, self.base / "rescue")


if __name__ == "__main__":
    unittest.main(verbosity=2)
