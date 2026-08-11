#!/usr/bin/env python3
from __future__ import annotations

import io
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

    def test_read_only_audit_never_creates_a_scratch_index(self) -> None:
        workspace = self.base / "workspace"
        init_repo(workspace / "repo")

        with mock.patch.object(
            preservation,
            "_scratch_index_environment",
            side_effect=AssertionError("audit attempted scratch-index creation"),
        ):
            result = preservation.audit_workspace(workspace)

        self.assertEqual(1, len(result.worktrees))

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
        with mock.patch.dict(
            os.environ,
            {
                "GIT_ALTERNATE_OBJECT_DIRECTORIES": str(other / ".git" / "objects"),
                "GIT_NO_LAZY_FETCH": "0",
            },
            clear=False,
        ):
            environment = preservation.sanitized_git_environment()
        self.assertNotIn("GIT_ALTERNATE_OBJECT_DIRECTORIES", environment)
        self.assertEqual("1", environment["GIT_NO_LAZY_FETCH"])

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
            preservation._worktree_evidence(
                record, self.base / "evidence-output"
            )
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
        self.assertEqual(2, inventory["formatVersion"])
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

    def test_capture_recovers_missing_reachable_objects_without_source_mutation(self) -> None:
        workspace = self.base / "workspace"
        repo = workspace / "repo"
        provider = self.base / "provider"
        rescue_without_provider = self.base / "rescue-without-provider"
        rescue = self.base / "rescue"
        init_repo(repo)
        missing_commit = git(repo, "rev-parse", "HEAD").stdout.decode().strip()
        (repo / "tracked-a.txt").write_text("a1\n", encoding="utf-8", newline="\n")
        git(repo, "commit", "--quiet", "-am", "child of soon-missing commit")
        shutil.copytree(repo, provider)
        missing_object = (
            repo / ".git" / "objects" / missing_commit[:2] / missing_commit[2:]
        )
        self.assertTrue(missing_object.is_file())
        missing_object.chmod(0o666)
        missing_object.unlink()
        self.assertNotEqual(
            0,
            preservation.run_git(
                repo, "fsck", "--full", "--strict", check=False
            ).returncode,
        )

        with self.assertRaisesRegex(
            preservation.PreservationError, "--recovery-object-repo"
        ):
            preservation.capture_workspace(repo, rescue_without_provider)
        failed_runs = list(rescue_without_provider.glob(".run-*.partial-*"))
        self.assertEqual(1, len(failed_runs))
        self.assertTrue((failed_runs[0] / "CAPTURE_FAILED.txt").is_file())
        self.assertFalse(any(rescue_without_provider.rglob("CAPTURE_COMPLETE.txt")))

        destination = preservation.capture_workspace(
            repo,
            rescue,
            recovery_object_repo=provider,
            now=datetime(2026, 8, 11, 8, 9, 10, 111213, tzinfo=timezone.utc),
        )
        self.assertFalse(missing_object.exists())
        self.assertTrue(
            (destination / "CAPTURE_COMPLETE.txt")
            .read_text("utf-8")
            .startswith("PASS_WITH_RECOVERED_SOURCE_DEFECTS ")
        )
        evidence = json.loads(
            (destination / "capture-evidence.json").read_text("utf-8")
        )
        repository = evidence["repositories"]["repository-001"]
        self.assertNotEqual(0, repository["sourceFsckReturnCode"])
        self.assertEqual(0, repository["mirrorFsckReturnCode"])
        recovered = repository["recovery"]
        recovered_ids = {item["oid"] for item in recovered["objects"]}
        self.assertIn(missing_commit, recovered_ids)
        self.assertEqual(len(recovered_ids), recovered["objectCount"])
        self.assertEqual(
            preservation.sha256_bytes(
                ("".join(f"{oid}\n" for oid in sorted(recovered_ids))).encode(
                    "ascii"
                )
            ),
            recovered["objectIdsSha256"],
        )
        repository_capture = destination / "repositories" / "repository-001"
        self.assertFalse(
            (
                repository_capture
                / "common-git-physical"
                / "objects"
                / missing_commit[:2]
                / missing_commit[2:]
            ).exists()
        )
        mirror = repository_capture / "mirror.git"
        self.assertEqual(
            0,
            preservation.run_git_dir(
                mirror, "cat-file", "-e", f"{missing_commit}^{{commit}}", check=False
            ).returncode,
        )
        self.assertEqual(
            0,
            preservation.run_git_dir(
                mirror, "fsck", "--full", "--strict", check=False
            ).returncode,
        )
        mirror_alternates = mirror / "objects" / "info" / "alternates"
        self.assertFalse(
            mirror_alternates.exists() and mirror_alternates.read_bytes().strip()
        )

    def test_recovery_handles_direct_broken_ref_and_index_only_blob(self) -> None:
        workspace = self.base / "workspace"
        repo = workspace / "repo"
        provider = self.base / "provider"
        rescue = self.base / "rescue"
        init_repo(repo)
        missing_commit = git(repo, "rev-parse", "HEAD").stdout.decode().strip()
        git(repo, "update-ref", "refs/archive/lost", missing_commit)
        tree = git(repo, "write-tree").stdout.decode().strip()
        root_process = subprocess.run(
            ["git", "-C", str(repo), "commit-tree", tree],
            input=b"independent current root\n",
            env=preservation.sanitized_git_environment(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        independent_root = root_process.stdout.decode().strip()
        branch = git(repo, "branch", "--show-current").stdout.decode().strip()
        git(repo, "update-ref", f"refs/heads/{branch}", independent_root)
        index_only = repo / "index-only.txt"
        index_only.write_text("staged only\n", encoding="utf-8", newline="\n")
        git(repo, "add", "index-only.txt")
        missing_blob = git(repo, "hash-object", "index-only.txt").stdout.decode().strip()
        shutil.copytree(repo, provider)

        for object_id in (missing_commit, missing_blob):
            object_path = repo / ".git" / "objects" / object_id[:2] / object_id[2:]
            self.assertTrue(object_path.is_file())
            object_path.chmod(0o666)
            object_path.unlink()

        destination = preservation.capture_workspace(
            workspace, rescue, recovery_object_repo=provider
        )
        repository = json.loads(
            (destination / "capture-evidence.json").read_text("utf-8")
        )["repositories"]["repository-001"]["recovery"]
        self.assertIn(missing_commit, repository["normalRefObjectIds"])
        self.assertIn(missing_blob, repository["fsckOnlyObjectIds"])
        self.assertTrue(
            (destination / "worktrees" / "worktree-001" / "staged.patch")
            .read_bytes()
            .strip()
        )

    def test_recovered_cacheinfo_blob_never_refreshes_source_index(self) -> None:
        workspace = self.base / "workspace"
        repo = workspace / "repo"
        provider = self.base / "provider"
        rescue = self.base / "rescue"
        init_repo(repo)

        index_only = repo / "cacheinfo-only.txt"
        index_only.write_bytes(b"provider-backed index entry\n")
        missing_blob = git(
            repo, "hash-object", "-w", "--", "cacheinfo-only.txt"
        ).stdout.decode().strip()
        git(
            repo,
            "update-index",
            "--add",
            "--cacheinfo",
            "100644",
            missing_blob,
            "cacheinfo-only.txt",
        )
        shutil.copytree(repo, provider)

        source_object = (
            repo / ".git" / "objects" / missing_blob[:2] / missing_blob[2:]
        )
        self.assertTrue(source_object.is_file())
        source_object.chmod(0o666)
        source_object.unlink()
        source_index = repo / ".git" / "index"
        index_before = source_index.read_bytes()
        index_sha_before = preservation.sha256_file(source_index)

        destination = preservation.capture_workspace(
            workspace, rescue, recovery_object_repo=provider
        )

        self.assertEqual(index_sha_before, preservation.sha256_file(source_index))
        self.assertEqual(index_before, source_index.read_bytes())
        captured_index = (
            destination / "worktrees" / "worktree-001" / "index.raw"
        )
        self.assertEqual(index_sha_before, preservation.sha256_file(captured_index))
        self.assertEqual(
            index_before,
            captured_index.read_bytes(),
        )
        self.assertFalse(any(destination.rglob(".index-scratch-*")))
        self.assertTrue(
            (destination / "CAPTURE_COMPLETE.txt")
            .read_text("utf-8")
            .startswith("PASS_WITH_RECOVERED_SOURCE_DEFECTS ")
        )
        recovery = json.loads(
            (destination / "capture-evidence.json").read_text("utf-8")
        )["repositories"]["repository-001"]["recovery"]
        self.assertIn(missing_blob, recovery["fsckOnlyObjectIds"])
        self.assertTrue(
            (destination / "worktrees" / "worktree-001" / "staged.patch")
            .read_bytes()
            .strip()
        )

    def test_missing_fsck_root_parser_accepts_pointer_and_reflog_errors(self) -> None:
        pointer = "1" * 40
        reflog = "2" * 40
        result = preservation.GitResult(
            2,
            b"",
            (
                f"error: refs/archive/lost: invalid sha1 pointer {pointer}\n"
                f"error: refs/heads/main@{{1}}: invalid reflog entry {reflog}\n"
            ).encode("ascii"),
        )
        self.assertEqual(
            [pointer, reflog], preservation._missing_fsck_roots(result)
        )

    def test_capture_rejects_broken_recovery_object_provider(self) -> None:
        workspace = self.base / "workspace"
        repo = workspace / "repo"
        provider = self.base / "provider"
        init_repo(repo)
        shutil.copytree(repo, provider)
        provider_head = git(provider, "rev-parse", "HEAD").stdout.decode().strip()
        provider_object = (
            provider
            / ".git"
            / "objects"
            / provider_head[:2]
            / provider_head[2:]
        )
        self.assertTrue(provider_object.is_file())
        provider_object.chmod(0o666)
        provider_object.unlink()

        with self.assertRaisesRegex(
            preservation.PreservationError,
            "recovery object provider does not pass git fsck",
        ):
            preservation.capture_workspace(
                workspace,
                self.base / "rescue",
                recovery_object_repo=provider,
            )
        self.assertFalse((self.base / "rescue").exists())

    def test_capture_rejects_recovery_provider_with_alternates(self) -> None:
        workspace = self.base / "workspace"
        repo = workspace / "repo"
        provider = self.base / "provider"
        alternate = self.base / "alternate.git"
        init_repo(repo)
        shutil.copytree(repo, provider)
        alternate.mkdir()
        subprocess.run(
            ["git", "init", "--quiet", "--bare"],
            cwd=alternate,
            env=preservation.sanitized_git_environment(),
            check=True,
        )
        alternates_file = provider / ".git" / "objects" / "info" / "alternates"
        alternates_file.write_text(
            str((alternate / "objects").resolve()) + "\n", encoding="utf-8"
        )

        with self.assertRaisesRegex(
            preservation.PreservationError, "unsupported alternates"
        ):
            preservation.capture_workspace(
                workspace,
                self.base / "rescue",
                recovery_object_repo=provider,
            )
        self.assertFalse((self.base / "rescue").exists())

    def test_capture_rejects_partial_recovery_provider(self) -> None:
        workspace = self.base / "workspace"
        repo = workspace / "repo"
        provider = self.base / "provider"
        init_repo(repo)
        shutil.copytree(repo, provider)
        git(provider, "config", "remote.origin.promisor", "true")

        with self.assertRaisesRegex(
            preservation.PreservationError, "partial/promisor"
        ):
            preservation.capture_workspace(
                workspace,
                self.base / "rescue",
                recovery_object_repo=provider,
            )
        self.assertFalse((self.base / "rescue").exists())

    def test_cli_reports_recovered_source_defect_status(self) -> None:
        destination = self.base / "run-test"
        destination.mkdir()
        (destination / "CAPTURE_COMPLETE.txt").write_text(
            "PASS_WITH_RECOVERED_SOURCE_DEFECTS test\n", encoding="utf-8"
        )
        with mock.patch.object(
            preservation, "capture_workspace", return_value=destination
        ), mock.patch("sys.stdout", new_callable=io.StringIO) as stdout:
            result = preservation.main(
                [
                    "capture",
                    "--workspace",
                    str(self.base / "workspace"),
                    "--rescue-root",
                    str(self.base / "rescue"),
                ]
            )
        self.assertEqual(0, result)
        self.assertEqual(
            "PASS_WITH_RECOVERED_SOURCE_DEFECTS",
            json.loads(stdout.getvalue())["status"],
        )

    def test_capture_preserves_non_default_and_detached_common_head(self) -> None:
        for detached in (False, True):
            with self.subTest(detached=detached):
                workspace = self.base / f"workspace-head-{detached}"
                repo = workspace / "repo"
                rescue = self.base / f"rescue-head-{detached}"
                init_repo(repo)
                git(repo, "branch", "-M", "alpha")
                git(repo, "switch", "--quiet", "-c", "zeta")
                if detached:
                    git(repo, "switch", "--quiet", "--detach", "HEAD")
                    git(repo, "branch", "-D", "alpha", "zeta")
                else:
                    git(
                        repo,
                        "symbolic-ref",
                        "refs/remotes/origin/HEAD",
                        "refs/heads/alpha",
                    )
                source_head = preservation._common_head_state(repo / ".git")
                source_refs = preservation._common_refs(repo / ".git")

                destination = preservation.capture_workspace(workspace, rescue)
                mirror = (
                    destination
                    / "repositories"
                    / "repository-001"
                    / "mirror.git"
                )
                self.assertEqual(source_head, preservation._common_head_state(mirror))
                self.assertEqual(source_refs, preservation._common_refs(mirror))

    def test_recovery_covers_detached_linked_worktree_without_polluting_mirror(self) -> None:
        workspace = self.base / "workspace"
        repo = workspace / "repo"
        external = self.base / "detached-worktree"
        provider = self.base / "provider.git"
        rescue = self.base / "rescue"
        init_repo(repo)
        missing_commit = git(repo, "rev-parse", "HEAD").stdout.decode().strip()
        git(repo, "worktree", "add", "--quiet", "--detach", str(external), "HEAD")
        (external / "tracked-a.txt").write_text(
            "detached child\n", encoding="utf-8", newline="\n"
        )
        git(external, "commit", "--quiet", "-am", "detached child")
        detached_head = git(external, "rev-parse", "HEAD").stdout.decode().strip()

        tree = git(repo, "write-tree").stdout.decode().strip()
        root_process = subprocess.run(
            ["git", "-C", str(repo), "commit-tree", tree],
            input=b"independent root\n",
            env=preservation.sanitized_git_environment(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        independent_root = root_process.stdout.decode().strip()
        branch = git(repo, "branch", "--show-current").stdout.decode().strip()
        git(repo, "update-ref", f"refs/heads/{branch}", independent_root)
        git(repo, "update-ref", "refs/recovery/provider-tip", detached_head)
        subprocess.run(
            ["git", "clone", "--quiet", "--mirror", "--no-local", str(repo), str(provider)],
            env=preservation.sanitized_git_environment(),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        )
        git(repo, "update-ref", "-d", "refs/recovery/provider-tip")
        missing_object = (
            repo / ".git" / "objects" / missing_commit[:2] / missing_commit[2:]
        )
        self.assertTrue(missing_object.is_file())
        missing_object.chmod(0o666)
        missing_object.unlink()

        destination = preservation.capture_workspace(
            workspace, rescue, recovery_object_repo=provider
        )
        repository_capture = destination / "repositories" / "repository-001"
        evidence = json.loads(
            (destination / "capture-evidence.json").read_text("utf-8")
        )["repositories"]["repository-001"]["recovery"]
        self.assertIn(missing_commit, evidence["worktreeHeadObjectIds"])
        self.assertNotIn(missing_commit, evidence["normalRefObjectIds"])
        mirror = repository_capture / "mirror.git"
        self.assertNotEqual(
            0,
            preservation.run_git_dir(
                mirror, "cat-file", "-e", missing_commit, check=False
            ).returncode,
        )
        inventory = json.loads((destination / "inventory.json").read_text("utf-8"))
        detached_entry = next(
            item
            for item in inventory["worktrees"]
            if Path(item["path"]).name == external.name
        )
        head_bundle = (
            destination / "worktrees" / detached_entry["id"] / "head.bundle"
        )
        empty = self.base / "empty-verifier.git"
        subprocess.run(
            ["git", "init", "--quiet", "--bare", str(empty)],
            env=preservation.sanitized_git_environment(),
            check=True,
        )
        self.assertEqual(
            0,
            preservation.run_git_dir(
                empty, "bundle", "verify", head_bundle, check=False
            ).returncode,
        )

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
