#!/usr/bin/env python3
"""Read-only Git workspace audit and fail-closed preservation capture.

The audit command never writes.  The capture command only writes below a new
``run-<UTC>`` directory in the explicitly selected rescue root; it never
changes, cleans, prunes, moves, or deletes a source repository/worktree.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Iterable

from kgg_git_environment import sanitized_git_environment as base_git_environment


FORMAT_VERSION = 1
DEFAULT_RESCUE_ROOT = Path(r"C:\KGG_RESCUE\2026-08-10")
MAX_SCAN_DIRECTORIES = 250_000
GIT_BASE = (
    "git",
    "-c",
    "core.longpaths=true",
    "-c",
    "color.ui=false",
    "-c",
    "core.fsmonitor=false",
    "-c",
    "core.untrackedCache=false",
)
PRESERVATION_GIT_ENVIRONMENT = {
    "GIT_ATTR_NOSYSTEM",
    "GIT_ATTR_SOURCE",
    "GIT_CONFIG_GLOBAL",
    "GIT_CONFIG_NOSYSTEM",
    "GIT_CONFIG_SYSTEM",
    "GIT_INTERNAL_SUPER_PREFIX",
    "GIT_NAMESPACE",
    "GIT_QUARANTINE_PATH",
}


class PreservationError(RuntimeError):
    """Raised when a complete, verifiable capture cannot be guaranteed."""


@dataclass
class GitResult:
    returncode: int
    stdout: bytes
    stderr: bytes


@dataclass
class StatusEntry:
    path: str
    staged: bool = False
    unstaged: bool = False
    untracked: bool = False
    conflict: bool = False


@dataclass
class StatusSnapshot:
    raw: bytes
    entries: list[StatusEntry]

    @property
    def staged_paths(self) -> list[str]:
        return sorted({entry.path for entry in self.entries if entry.staged})

    @property
    def unstaged_paths(self) -> list[str]:
        return sorted({entry.path for entry in self.entries if entry.unstaged})

    @property
    def untracked_paths(self) -> list[str]:
        return sorted({entry.path for entry in self.entries if entry.untracked})

    @property
    def conflict_paths(self) -> list[str]:
        return sorted({entry.path for entry in self.entries if entry.conflict})

    @property
    def dirty_paths(self) -> list[str]:
        return sorted({entry.path for entry in self.entries})


@dataclass
class WorktreeRecord:
    path: Path
    physical_path: Path
    physical_key: str
    git_dir: Path
    common_git_dir: Path
    common_key: str
    head: str
    branch: str | None
    status: StatusSnapshot
    tracked_raw: bytes
    tracked_paths: list[str]
    ignored_raw: bytes
    ignored_paths: list[str]
    hooks_path: Path
    aliases: set[str] = field(default_factory=set)
    discovery_sources: set[str] = field(default_factory=set)
    id: str = ""


@dataclass
class RegisteredWorktree:
    path: str
    head: str | None
    branch: str | None
    detached: bool
    locked: str | None
    prunable: str | None
    exists: bool


@dataclass
class CommonGitRecord:
    path: Path
    physical_key: str
    alternate_object_dirs: list[Path] = field(default_factory=list)
    external_lfs_dirs: list[Path] = field(default_factory=list)
    external_hook_dirs: list[Path] = field(default_factory=list)
    worktree_ids: list[str] = field(default_factory=list)
    registrations: list[RegisteredWorktree] = field(default_factory=list)
    id: str = ""


@dataclass
class AuditResult:
    workspace: Path
    logical_git_roots: list[str]
    worktrees: list[WorktreeRecord]
    common_git_dirs: list[CommonGitRecord]
    root_files: list[dict[str, object]]
    loose_files: list[dict[str, object]]
    warnings: list[str]


def _decode(data: bytes) -> str:
    return data.decode("utf-8", errors="surrogateescape")


def _display_path(path: os.PathLike[str] | str) -> str:
    value = os.fspath(path)
    if os.name == "nt" and value.startswith("\\\\?\\UNC\\"):
        return "\\\\" + value[8:]
    if os.name == "nt" and value.startswith("\\\\?\\"):
        return value[4:]
    return value


def _fs_path(path: os.PathLike[str] | str) -> str:
    """Return an absolute extended-length path for direct Windows file I/O."""
    value = os.path.abspath(_display_path(path))
    if os.name != "nt" or value.startswith("\\\\?\\"):
        return value
    if value.startswith("\\\\"):
        return "\\\\?\\UNC\\" + value[2:]
    return "\\\\?\\" + value


def _absolute_lexical(path: os.PathLike[str] | str) -> Path:
    return Path(_display_path(os.path.abspath(_display_path(path))))


def canonical_path(path: os.PathLike[str] | str, *, strict: bool = True) -> Path:
    absolute = _absolute_lexical(path)
    if strict and not os.path.exists(_fs_path(absolute)):
        raise PreservationError(f"path does not exist: {absolute}")
    resolved = os.path.realpath(_fs_path(absolute))
    return Path(_display_path(resolved))


def physical_key(path: os.PathLike[str] | str) -> str:
    canonical = canonical_path(path)
    info = os.stat(_fs_path(canonical), follow_symlinks=True)
    if info.st_ino:
        return f"inode:{info.st_dev}:{info.st_ino}"
    return "path:" + os.path.normcase(str(canonical))


def sha256_file(path: os.PathLike[str] | str) -> str:
    digest = hashlib.sha256()
    with open(_fs_path(path), "rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stable_file_evidence(path: os.PathLike[str] | str) -> dict[str, object]:
    before = os.stat(_fs_path(path), follow_symlinks=False)
    digest = sha256_file(path)
    after = os.stat(_fs_path(path), follow_symlinks=False)
    before_identity = (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
    )
    after_identity = (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
    )
    if before_identity != after_identity:
        raise PreservationError(f"file changed while hashing: {path}")
    return {"bytes": before.st_size, "sha256": digest}


def sanitized_git_environment() -> dict[str, str]:
    """Drop inherited repository-routing variables before targeting a source."""
    environment = base_git_environment()
    for name in PRESERVATION_GIT_ENVIRONMENT:
        environment.pop(name, None)
    environment.update(
        {
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_OPTIONAL_LOCKS": "0",
            "GIT_PAGER": "cat",
            "LC_ALL": "C",
        }
    )
    return environment


def run_command(
    args: Iterable[os.PathLike[str] | str],
    *,
    cwd: Path | None = None,
    check: bool = True,
    input_bytes: bytes | None = None,
) -> GitResult:
    command = [os.fspath(item) for item in args]
    process = subprocess.run(
        command,
        cwd=os.fspath(cwd) if cwd else None,
        env=sanitized_git_environment(),
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    result = GitResult(process.returncode, process.stdout, process.stderr)
    if check and result.returncode != 0:
        detail = _decode(result.stderr or result.stdout).strip() or "unknown error"
        raise PreservationError(f"command failed ({' '.join(command)}): {detail}")
    return result


def run_git(
    worktree: Path,
    *args: os.PathLike[str] | str,
    check: bool = True,
    input_bytes: bytes | None = None,
) -> GitResult:
    return run_command(
        (*GIT_BASE, "-C", worktree, *args),
        check=check,
        input_bytes=input_bytes,
    )


def run_git_dir(
    git_dir: Path,
    *args: os.PathLike[str] | str,
    check: bool = True,
    input_bytes: bytes | None = None,
) -> GitResult:
    return run_command(
        (*GIT_BASE, f"--git-dir={git_dir}", *args),
        check=check,
        input_bytes=input_bytes,
    )


def _git_text(worktree: Path, *args: str) -> str:
    return _decode(run_git(worktree, *args).stdout).strip()


def discover_git_roots(
    workspace: Path, *, max_directories: int = MAX_SCAN_DIRECTORIES
) -> list[Path]:
    """Find logical .git markers while de-duplicating traversed physical dirs."""
    workspace = _absolute_lexical(workspace)
    if not os.path.isdir(_fs_path(workspace)):
        raise PreservationError(f"workspace is not a directory: {workspace}")

    roots: list[Path] = []
    stack = [workspace]
    visited: set[str] = set()
    scanned = 0
    while stack:
        directory = stack.pop()
        marker = directory / ".git"
        if os.path.isdir(_fs_path(marker)) or os.path.isfile(_fs_path(marker)):
            roots.append(directory)

        key = physical_key(directory)
        if key in visited:
            continue
        visited.add(key)
        scanned += 1
        if scanned > max_directories:
            raise PreservationError(
                f"directory scan exceeded safety limit ({max_directories})"
            )

        try:
            entries = list(os.scandir(_fs_path(directory)))
        except OSError as exc:
            raise PreservationError(f"cannot scan {directory}: {exc}") from exc
        for entry in reversed(entries):
            if entry.name == ".git":
                continue
            try:
                if entry.is_dir(follow_symlinks=True):
                    stack.append(Path(_display_path(entry.path)))
            except OSError as exc:
                raise PreservationError(f"cannot inspect {entry.path}: {exc}") from exc
    return roots


def parse_porcelain_v2(raw: bytes) -> StatusSnapshot:
    entries: list[StatusEntry] = []
    records = raw.split(b"\0")
    index = 0
    while index < len(records):
        record = records[index]
        index += 1
        if not record:
            continue
        kind = record[:1]
        if kind == b"#" or kind == b"!":
            continue
        if kind == b"?":
            entries.append(StatusEntry(_decode(record[2:]), untracked=True))
            continue
        if kind == b"1":
            fields = record.split(b" ", 8)
            if len(fields) != 9:
                raise PreservationError("malformed porcelain-v2 ordinary record")
            xy = fields[1]
            path = _decode(fields[8])
        elif kind == b"2":
            fields = record.split(b" ", 9)
            if len(fields) != 10 or index >= len(records):
                raise PreservationError("malformed porcelain-v2 rename record")
            xy = fields[1]
            path = _decode(fields[9])
            index += 1  # original path follows as a separate NUL field
        elif kind == b"u":
            fields = record.split(b" ", 10)
            if len(fields) != 11:
                raise PreservationError("malformed porcelain-v2 conflict record")
            xy = fields[1]
            path = _decode(fields[10])
            entries.append(
                StatusEntry(path, staged=True, unstaged=True, conflict=True)
            )
            continue
        else:
            raise PreservationError(f"unknown porcelain-v2 record: {_decode(record[:40])}")
        if len(xy) != 2:
            raise PreservationError("malformed porcelain-v2 XY status")
        entries.append(
            StatusEntry(path, staged=xy[:1] != b".", unstaged=xy[1:] != b".")
        )
    return StatusSnapshot(raw=raw, entries=entries)


def worktree_status(path: Path) -> StatusSnapshot:
    raw = run_git(
        path,
        "status",
        "--porcelain=v2",
        "-z",
        "--untracked-files=all",
        "--ignore-submodules=all",
    ).stdout
    return parse_porcelain_v2(raw)


def worktree_ignored(path: Path) -> tuple[bytes, list[str]]:
    raw = run_git(
        path,
        "ls-files",
        "--others",
        "--ignored",
        "--exclude-standard",
        "-z",
    ).stdout
    return raw, [_decode(item) for item in raw.split(b"\0") if item]


def worktree_tracked(path: Path) -> tuple[bytes, list[str]]:
    raw = run_git(path, "ls-files", "--cached", "-z").stdout
    return raw, [_decode(item) for item in raw.split(b"\0") if item]


def assert_no_external_filter_drivers(path: Path) -> None:
    """Reject active clean/smudge/process commands before status/diff can run them."""
    path_results = (
        run_git(path, "ls-files", "--cached", "-z").stdout,
        run_git(path, "ls-files", "--others", "--exclude-standard", "-z").stdout,
        run_git(
            path,
            "ls-files",
            "--others",
            "--ignored",
            "--exclude-standard",
            "-z",
        ).stdout,
    )
    encoded_paths = sorted(
        {
            item
            for raw in path_results
            for item in raw.split(b"\0")
            if item
        }
    )
    if not encoded_paths:
        return
    attributes = run_git(
        path,
        "check-attr",
        "-z",
        "--stdin",
        "filter",
        input_bytes=b"\0".join(encoded_paths) + b"\0",
    ).stdout.split(b"\0")
    if attributes and not attributes[-1]:
        attributes.pop()
    if len(attributes) % 3:
        raise PreservationError(f"malformed Git filter attribute output in {path}")
    drivers = {
        _decode(attributes[index + 2])
        for index in range(0, len(attributes), 3)
        if attributes[index + 1] == b"filter"
        and attributes[index + 2] != b""
    }
    configured: list[str] = []
    for driver in sorted(drivers):
        for command_name in ("clean", "smudge", "process"):
            key = f"filter.{driver}.{command_name}"
            result = run_git(path, "config", "--get", key, check=False)
            if result.returncode not in (0, 1):
                detail = _decode(result.stderr or result.stdout).strip() or "unknown error"
                raise PreservationError(
                    f"cannot inspect external Git filter configuration {key}: {detail}"
                )
            if result.returncode == 0 and result.stdout.strip():
                configured.append(key)
    if configured:
        raise PreservationError(
            "external Git filter drivers are not allowed during read-only "
            f"preservation audit: {path}: {', '.join(configured)}"
        )


def worktree_hooks_path(path: Path) -> Path:
    result = run_git(
        path,
        "rev-parse",
        "--path-format=absolute",
        "--git-path",
        "hooks",
        check=False,
    )
    if result.returncode != 0:
        result = run_git(path, "rev-parse", "--git-path", "hooks")
    value = Path(_decode(result.stdout).strip())
    if not value.is_absolute():
        value = path / value
    return _absolute_lexical(value)


def probe_worktree(path: Path, *, source: str) -> WorktreeRecord:
    path = _absolute_lexical(path)
    top = Path(_git_text(path, "rev-parse", "--show-toplevel"))
    top = _absolute_lexical(top)
    git_dir = Path(_git_text(top, "rev-parse", "--absolute-git-dir"))
    common_raw = _git_text(top, "rev-parse", "--git-common-dir")
    common = Path(common_raw)
    if not common.is_absolute():
        common = top / common
    common = canonical_path(common)
    head_result = run_git(top, "rev-parse", "--verify", "HEAD", check=False)
    if head_result.returncode != 0:
        raise PreservationError(f"unborn or unreadable HEAD in {top}")
    branch_result = run_git(top, "symbolic-ref", "--quiet", "--short", "HEAD", check=False)
    if branch_result.returncode not in (0, 1):
        raise PreservationError(f"cannot resolve branch state in {top}")
    branch = _decode(branch_result.stdout).strip() if branch_result.returncode == 0 else None
    canonical_top = canonical_path(top)
    assert_no_external_filter_drivers(top)
    ignored_raw, ignored_paths = worktree_ignored(top)
    tracked_raw, tracked_paths = worktree_tracked(top)
    return WorktreeRecord(
        path=top,
        physical_path=canonical_top,
        physical_key=physical_key(canonical_top),
        git_dir=canonical_path(git_dir),
        common_git_dir=common,
        common_key=physical_key(common),
        head=_decode(head_result.stdout).strip(),
        branch=branch,
        status=worktree_status(top),
        tracked_raw=tracked_raw,
        tracked_paths=tracked_paths,
        ignored_raw=ignored_raw,
        ignored_paths=ignored_paths,
        hooks_path=worktree_hooks_path(top),
        aliases={str(path)},
        discovery_sources={source},
    )


def parse_worktree_list(raw: bytes) -> list[RegisteredWorktree]:
    registrations: list[RegisteredWorktree] = []
    for block in raw.split(b"\0\0"):
        if not block:
            continue
        values: dict[str, str] = {}
        flags: set[str] = set()
        for line in block.split(b"\0"):
            if not line:
                continue
            key, separator, value = line.partition(b" ")
            name = _decode(key)
            if separator:
                values[name] = _decode(value)
            else:
                flags.add(name)
        if "worktree" not in values:
            raise PreservationError("malformed git worktree list output")
        path = _absolute_lexical(values["worktree"])
        registrations.append(
            RegisteredWorktree(
                path=str(path),
                head=values.get("HEAD"),
                branch=values.get("branch"),
                detached="detached" in flags,
                locked=values.get("locked") if "locked" in values else ("" if "locked" in flags else None),
                prunable=values.get("prunable") if "prunable" in values else ("" if "prunable" in flags else None),
                exists=os.path.isdir(_fs_path(path)),
            )
        )
    return registrations


def registered_worktrees(common_git_dir: Path) -> tuple[bytes, list[RegisteredWorktree]]:
    raw = run_git_dir(common_git_dir, "worktree", "list", "--porcelain", "-z").stdout
    return raw, parse_worktree_list(raw)


def _stable_file_bytes(path: Path) -> bytes:
    before = os.stat(_fs_path(path), follow_symlinks=False)
    with open(_fs_path(path), "rb") as handle:
        data = handle.read()
    after = os.stat(_fs_path(path), follow_symlinks=False)
    if (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
    ) != (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
    ):
        raise PreservationError(f"file changed while reading: {path}")
    return data


def alternate_object_directories(common_git_dir: Path) -> list[Path]:
    primary = canonical_path(common_git_dir / "objects")
    queue = [primary]
    visited = {physical_key(primary)}
    alternates: dict[str, Path] = {}
    while queue:
        object_dir = queue.pop(0)
        alternates_file = object_dir / "info" / "alternates"
        if not os.path.exists(_fs_path(alternates_file)):
            continue
        info = os.stat(_fs_path(alternates_file), follow_symlinks=False)
        if not stat.S_ISREG(info.st_mode) or os.path.islink(_fs_path(alternates_file)) or _is_reparse(info):
            raise PreservationError(f"unsupported Git alternates file: {alternates_file}")
        for raw_line in _stable_file_bytes(alternates_file).splitlines():
            if not raw_line:
                continue
            line = _decode(raw_line)
            if line.startswith('"'):
                raise PreservationError(
                    f"quoted Git alternate path is unsupported: {alternates_file}"
                )
            candidate = Path(line)
            if not candidate.is_absolute():
                candidate = object_dir / candidate
            candidate = canonical_path(candidate)
            if not os.path.isdir(_fs_path(candidate)):
                raise PreservationError(f"Git alternate is not a directory: {candidate}")
            key = physical_key(candidate)
            if key in visited:
                continue
            visited.add(key)
            alternates[key] = candidate
            queue.append(candidate)
    return sorted(alternates.values(), key=lambda item: str(item).casefold())


def configured_external_lfs_directories(
    worktrees: list[WorktreeRecord], common_git_dir: Path
) -> list[Path]:
    directories: dict[str, Path] = {}
    for worktree in worktrees:
        result = run_git(
            worktree.path,
            "config",
            "--path",
            "--get-all",
            "lfs.storage",
            check=False,
        )
        if result.returncode == 1:
            continue
        if result.returncode != 0:
            detail = _decode(result.stderr or result.stdout).strip()
            raise PreservationError(
                f"cannot read lfs.storage for {worktree.path}: {detail}"
            )
        for value in _decode(result.stdout).splitlines():
            if not value:
                continue
            candidate = Path(value)
            if not candidate.is_absolute():
                raise PreservationError(
                    f"relative lfs.storage is ambiguous and must be resolved manually: "
                    f"{worktree.path}: {value}"
                )
            candidate = canonical_path(candidate)
            if not os.path.isdir(_fs_path(candidate)):
                raise PreservationError(f"lfs.storage is not a directory: {candidate}")
            if _is_within(candidate, common_git_dir):
                continue
            directories[physical_key(candidate)] = candidate
    return sorted(directories.values(), key=lambda item: str(item).casefold())


def configured_external_hook_directories(
    worktrees: list[WorktreeRecord], covered_roots: list[Path]
) -> list[Path]:
    directories: dict[str, Path] = {}
    for worktree in worktrees:
        hooks_path = worktree.hooks_path
        if not os.path.exists(_fs_path(hooks_path)):
            continue
        if not os.path.isdir(_fs_path(hooks_path)):
            raise PreservationError(
                f"configured Git hooks path is not a directory: {hooks_path}"
            )
        hooks_path = canonical_path(hooks_path)
        if any(_is_within(hooks_path, root) for root in covered_roots):
            continue
        directories[physical_key(hooks_path)] = hooks_path
    return sorted(directories.values(), key=lambda item: str(item).casefold())


def _is_reparse(info: os.stat_result) -> bool:
    return bool(
        os.name == "nt"
        and getattr(info, "st_file_attributes", 0)
        & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    )


def _safe_workspace_file_inventory(
    workspace: Path, worktree_keys: set[str]
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    """Inventory every regular file outside an audited Git worktree."""
    root_files: list[dict[str, object]] = []
    loose_files: list[dict[str, object]] = []
    stack = [workspace]
    visited: set[str] = set()
    scanned = 0
    while stack:
        directory = stack.pop()
        key = physical_key(directory)
        if key in worktree_keys:
            continue
        if key in visited:
            continue
        visited.add(key)
        scanned += 1
        if scanned > MAX_SCAN_DIRECTORIES:
            raise PreservationError(
                f"loose-file scan exceeded safety limit ({MAX_SCAN_DIRECTORIES})"
            )
        try:
            entries = list(os.scandir(_fs_path(directory)))
        except OSError as exc:
            raise PreservationError(f"cannot enumerate loose files in {directory}: {exc}") from exc
        for entry in sorted(entries, key=lambda item: item.name.casefold(), reverse=True):
            path = Path(_display_path(entry.path))
            try:
                info = entry.stat(follow_symlinks=False)
            except OSError as exc:
                raise PreservationError(f"cannot stat loose entry {path}: {exc}") from exc
            is_link = entry.is_symlink() or _is_reparse(info)
            if is_link:
                try:
                    points_to_directory = entry.is_dir(follow_symlinks=True)
                except OSError as exc:
                    raise PreservationError(f"cannot resolve loose link {path}: {exc}") from exc
                if points_to_directory and physical_key(path) in worktree_keys:
                    continue
                raise PreservationError(
                    f"unsupported loose symlink/reparse entry outside Git coverage: {path}"
                )
            if stat.S_ISDIR(info.st_mode):
                stack.append(path)
                continue
            if not stat.S_ISREG(info.st_mode):
                raise PreservationError(f"unsupported loose special file: {path}")
            relative = path.relative_to(workspace)
            evidence = {"path": relative.as_posix(), **stable_file_evidence(path)}
            if len(relative.parts) == 1:
                root_files.append(evidence)
            else:
                loose_files.append(evidence)
    return (
        sorted(root_files, key=lambda item: str(item["path"]).casefold()),
        sorted(loose_files, key=lambda item: str(item["path"]).casefold()),
    )


def audit_workspace(workspace: Path) -> AuditResult:
    workspace = canonical_path(workspace)
    logical_roots = discover_git_roots(workspace)
    by_physical: dict[str, WorktreeRecord] = {}
    common_paths: dict[str, Path] = {}

    def add_worktree(path: Path, source: str) -> None:
        record = probe_worktree(path, source=source)
        existing = by_physical.get(record.physical_key)
        if existing:
            existing.aliases.update(record.aliases)
            existing.discovery_sources.add(source)
            return
        by_physical[record.physical_key] = record
        common_paths[record.common_key] = record.common_git_dir

    for root in logical_roots:
        add_worktree(root, "workspace-scan")

    registrations_by_common: dict[str, list[RegisteredWorktree]] = {}
    processed_common: set[str] = set()
    while True:
        pending = [(key, path) for key, path in common_paths.items() if key not in processed_common]
        if not pending:
            break
        for key, common in pending:
            processed_common.add(key)
            _raw, registrations = registered_worktrees(common)
            registrations_by_common[key] = registrations
            for registration in registrations:
                if registration.exists:
                    add_worktree(Path(registration.path), "git-registration")

    worktrees = sorted(by_physical.values(), key=lambda item: str(item.path).casefold())
    for number, record in enumerate(worktrees, 1):
        record.id = f"worktree-{number:03d}"

    common_records: list[CommonGitRecord] = []
    covered_roots = [record.physical_path for record in worktrees]
    covered_roots.extend(common_paths.values())
    for number, (key, common) in enumerate(
        sorted(common_paths.items(), key=lambda item: str(item[1]).casefold()), 1
    ):
        grouped_worktrees = [
            record for record in worktrees if record.common_key == key
        ]
        common_records.append(
            CommonGitRecord(
                path=common,
                physical_key=key,
                alternate_object_dirs=alternate_object_directories(common),
                external_lfs_dirs=configured_external_lfs_directories(
                    grouped_worktrees, common
                ),
                external_hook_dirs=configured_external_hook_directories(
                    grouped_worktrees, covered_roots
                ),
                worktree_ids=sorted(record.id for record in grouped_worktrees),
                registrations=registrations_by_common.get(key, []),
                id=f"repository-{number:03d}",
            )
        )

    warnings = []
    for common in common_records:
        for registration in common.registrations:
            if not registration.exists:
                warnings.append(
                    f"stale or inaccessible registered worktree: {registration.path}"
                )

    root_files, loose_files = _safe_workspace_file_inventory(
        workspace, {record.physical_key for record in worktrees}
    )

    return AuditResult(
        workspace=workspace,
        logical_git_roots=sorted({str(path) for path in logical_roots}, key=str.casefold),
        worktrees=worktrees,
        common_git_dirs=common_records,
        root_files=root_files,
        loose_files=loose_files,
        warnings=warnings,
    )


def audit_to_dict(audit: AuditResult, *, captured_at: str | None = None) -> dict[str, object]:
    worktrees: list[dict[str, object]] = []
    common_ids = {
        record.physical_key: record.id for record in audit.common_git_dirs
    }
    for record in audit.worktrees:
        status = record.status
        worktrees.append(
            {
                "id": record.id,
                "path": str(record.path),
                "physicalPath": str(record.physical_path),
                "outsideWorkspace": not _is_within(
                    record.physical_path, audit.workspace
                ),
                "aliases": sorted(record.aliases, key=str.casefold),
                "discoverySources": sorted(record.discovery_sources),
                "gitDir": str(record.git_dir),
                "commonGitDir": str(record.common_git_dir),
                "commonGitId": common_ids[record.common_key],
                "hooksPath": str(record.hooks_path),
                "hooksPathExists": os.path.isdir(_fs_path(record.hooks_path)),
                "head": record.head,
                "branch": record.branch,
                "detached": record.branch is None,
                "counts": {
                    "tracked": len(record.tracked_paths),
                    "dirtyPaths": len(status.dirty_paths),
                    "staged": len(status.staged_paths),
                    "unstaged": len(status.unstaged_paths),
                    "untracked": len(status.untracked_paths),
                    "ignored": len(record.ignored_paths),
                    "conflicts": len(status.conflict_paths),
                },
                "paths": {
                    "staged": status.staged_paths,
                    "unstaged": status.unstaged_paths,
                    "untracked": status.untracked_paths,
                    "ignored": sorted(record.ignored_paths),
                    "conflicts": status.conflict_paths,
                },
                "statusSha256": sha256_bytes(status.raw),
                "trackedListSha256": sha256_bytes(record.tracked_raw),
                "ignoredListSha256": sha256_bytes(record.ignored_raw),
            }
        )

    common_git_dirs: list[dict[str, object]] = []
    for record in audit.common_git_dirs:
        common_git_dirs.append(
            {
                "id": record.id,
                "path": str(record.path),
                "outsideWorkspace": not _is_within(record.path, audit.workspace),
                "alternateObjectDirs": [
                    str(path) for path in record.alternate_object_dirs
                ],
                "externalLfsDirs": [
                    str(path) for path in record.external_lfs_dirs
                ],
                "externalHookDirs": [
                    str(path) for path in record.external_hook_dirs
                ],
                "worktreeIds": record.worktree_ids,
                "registeredWorktrees": [
                    {
                        "path": item.path,
                        "head": item.head,
                        "branch": item.branch,
                        "detached": item.detached,
                        "locked": item.locked,
                        "prunable": item.prunable,
                        "exists": item.exists,
                    }
                    for item in record.registrations
                ],
            }
        )

    totals = {
        "logicalGitRoots": len(audit.logical_git_roots),
        "physicalWorktrees": len(audit.worktrees),
        "commonGitDirs": len(audit.common_git_dirs),
        "alternateObjectDirs": sum(
            len(item.alternate_object_dirs) for item in audit.common_git_dirs
        ),
        "externalLfsDirs": sum(
            len(item.external_lfs_dirs) for item in audit.common_git_dirs
        ),
        "externalHookDirs": sum(
            len(item.external_hook_dirs) for item in audit.common_git_dirs
        ),
        "cleanWorktrees": sum(not item.status.dirty_paths for item in audit.worktrees),
        "dirtyWorktrees": sum(bool(item.status.dirty_paths) for item in audit.worktrees),
        "dirtyPaths": sum(len(item.status.dirty_paths) for item in audit.worktrees),
        "tracked": sum(len(item.tracked_paths) for item in audit.worktrees),
        "staged": sum(len(item.status.staged_paths) for item in audit.worktrees),
        "unstaged": sum(len(item.status.unstaged_paths) for item in audit.worktrees),
        "untracked": sum(len(item.status.untracked_paths) for item in audit.worktrees),
        "ignored": sum(len(item.ignored_paths) for item in audit.worktrees),
        "conflicts": sum(len(item.status.conflict_paths) for item in audit.worktrees),
        "workspaceRootFiles": len(audit.root_files),
        "workspaceLooseFiles": len(audit.loose_files),
    }
    document: dict[str, object] = {
        "formatVersion": FORMAT_VERSION,
        "mode": "capture" if captured_at else "audit",
        "workspace": str(audit.workspace),
        "totals": totals,
        "logicalGitRoots": audit.logical_git_roots,
        "worktrees": worktrees,
        "commonGitDirs": common_git_dirs,
        "workspaceRootFiles": audit.root_files,
        "workspaceLooseFiles": audit.loose_files,
        "warnings": audit.warnings,
    }
    if captured_at:
        document["capturedAtUtc"] = captured_at
    return document


def _write_new_bytes(path: Path, data: bytes) -> None:
    os.makedirs(_fs_path(path.parent), exist_ok=True)
    try:
        with open(_fs_path(path), "xb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError as exc:
        raise PreservationError(f"refusing to overwrite capture file: {path}") from exc


def _write_new_text(path: Path, text: str) -> None:
    _write_new_bytes(path, text.replace("\r\n", "\n").encode("utf-8"))


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2, ensure_ascii=True, sort_keys=True) + "\n").encode(
        "utf-8"
    )


def _is_within(child: Path, parent: Path) -> bool:
    child_key = os.path.normcase(str(child))
    parent_key = os.path.normcase(str(parent))
    try:
        return os.path.commonpath([child_key, parent_key]) == parent_key
    except ValueError:
        return False


def _validate_capture_root(rescue_root: Path, audit: AuditResult) -> Path:
    rescue_root = _absolute_lexical(rescue_root)
    existing_parent = rescue_root
    while not os.path.exists(_fs_path(existing_parent)):
        if existing_parent.parent == existing_parent:
            raise PreservationError(f"cannot resolve rescue root parent: {rescue_root}")
        existing_parent = existing_parent.parent
    canonical_parent = canonical_path(existing_parent)
    suffix = rescue_root.relative_to(existing_parent)
    projected = canonical_parent / suffix
    protected = [audit.workspace]
    protected.extend(item.physical_path for item in audit.worktrees)
    protected.extend(item.path for item in audit.common_git_dirs)
    for common in audit.common_git_dirs:
        protected.extend(common.alternate_object_dirs)
        protected.extend(common.external_lfs_dirs)
        protected.extend(common.external_hook_dirs)
    for source in protected:
        source = canonical_path(source)
        if _is_within(projected, source) or _is_within(source, projected):
            raise PreservationError(
                f"rescue root overlaps protected source path: {projected} / {source}"
            )
    return rescue_root


def _safe_git_relative(relative: str) -> PurePosixPath:
    normalized = relative.replace("\\", "/")
    pure = PurePosixPath(normalized)
    if pure.is_absolute() or not pure.parts or any(part in ("", ".", "..") for part in pure.parts):
        raise PreservationError(f"unsafe Git path: {relative!r}")
    if os.name == "nt" and any(":" in part for part in pure.parts):
        raise PreservationError(f"unsafe Windows Git path: {relative!r}")
    return pure


def _safe_relative_candidate(worktree: Path, relative: str) -> tuple[Path, PurePosixPath]:
    pure = _safe_git_relative(relative)
    source = worktree.joinpath(*pure.parts)
    canonical_source = canonical_path(source)
    canonical_root = canonical_path(worktree)
    if not _is_within(canonical_source, canonical_root):
        raise PreservationError(f"Git path escapes worktree through a link: {relative!r}")
    return source, pure


def _safe_relative_path(worktree: Path, relative: str) -> tuple[Path, PurePosixPath]:
    source, pure = _safe_relative_candidate(worktree, relative)
    info = os.stat(_fs_path(source), follow_symlinks=False)
    if not stat.S_ISREG(info.st_mode) or os.path.islink(_fs_path(source)) or _is_reparse(info):
        raise PreservationError(f"unsupported untracked special file: {source}")
    return source, pure


def _copy_verified(source: Path, destination: Path) -> dict[str, object]:
    source_info = os.stat(_fs_path(source), follow_symlinks=False)
    if (
        not stat.S_ISREG(source_info.st_mode)
        or os.path.islink(_fs_path(source))
        or _is_reparse(source_info)
    ):
        raise PreservationError(f"refusing to copy special source file: {source}")
    before_size = source_info.st_size
    before_hash = sha256_file(source)
    os.makedirs(_fs_path(destination.parent), exist_ok=True)
    if os.path.exists(_fs_path(destination)):
        raise PreservationError(f"refusing to overwrite capture file: {destination}")
    shutil.copyfile(_fs_path(source), _fs_path(destination), follow_symlinks=False)
    after_hash = sha256_file(source)
    destination_hash = sha256_file(destination)
    destination_size = os.stat(_fs_path(destination), follow_symlinks=False).st_size
    if before_hash != after_hash or before_hash != destination_hash or before_size != destination_size:
        raise PreservationError(f"source changed or copy verification failed: {source}")
    return {"bytes": before_size, "sha256": before_hash}


def _physical_tree_manifest(root: Path) -> list[dict[str, object]]:
    """Hash a physical directory tree without following links or reparse points."""
    root = _absolute_lexical(root)
    if not os.path.isdir(_fs_path(root)):
        raise PreservationError(f"physical tree is not a directory: {root}")
    entries: list[dict[str, object]] = []
    stack = [root]
    while stack:
        directory = stack.pop()
        try:
            children = list(os.scandir(_fs_path(directory)))
        except OSError as exc:
            raise PreservationError(f"cannot scan physical tree {directory}: {exc}") from exc
        for child in sorted(children, key=lambda item: item.name.casefold(), reverse=True):
            path = Path(_display_path(child.path))
            relative = path.relative_to(root).as_posix()
            try:
                info = child.stat(follow_symlinks=False)
            except OSError as exc:
                raise PreservationError(f"cannot stat physical tree entry {path}: {exc}") from exc
            if child.is_symlink() or _is_reparse(info):
                raise PreservationError(
                    f"physical tree contains unsupported symlink/reparse entry: {path}"
                )
            if stat.S_ISDIR(info.st_mode):
                entries.append({"path": relative, "type": "directory"})
                stack.append(path)
            elif stat.S_ISREG(info.st_mode):
                entries.append(
                    {"path": relative, "type": "file", **stable_file_evidence(path)}
                )
            else:
                raise PreservationError(
                    f"physical tree contains unsupported special entry: {path}"
                )
    return sorted(entries, key=lambda item: (str(item["path"]), str(item["type"])))


def _copy_physical_tree(source: Path, destination: Path) -> list[dict[str, object]]:
    if os.path.exists(_fs_path(destination)):
        raise PreservationError(f"refusing to overwrite physical capture: {destination}")
    before = _physical_tree_manifest(source)
    os.makedirs(_fs_path(destination), exist_ok=False)
    for item in before:
        pure = PurePosixPath(str(item["path"]))
        target = destination.joinpath(*pure.parts)
        source_path = source.joinpath(*pure.parts)
        if item["type"] == "directory":
            os.makedirs(_fs_path(target), exist_ok=False)
        else:
            copied = _copy_verified(source_path, target)
            if copied != {"bytes": item["bytes"], "sha256": item["sha256"]}:
                raise PreservationError(f"physical source changed during copy: {source_path}")
    after = _physical_tree_manifest(source)
    captured = _physical_tree_manifest(destination)
    if before != after:
        raise PreservationError(f"physical source tree changed during copy: {source}")
    if before != captured:
        raise PreservationError(f"physical tree copy verification failed: {source}")
    return before


def _manifest_sha256(manifest: list[dict[str, object]]) -> str:
    return sha256_bytes(_json_bytes(manifest))


def _worktree_evidence(record: WorktreeRecord) -> dict[str, object]:
    assert_no_external_filter_drivers(record.path)
    status = run_git(
        record.path,
        "status",
        "--porcelain=v2",
        "-z",
        "--untracked-files=all",
        "--ignore-submodules=all",
    ).stdout
    staged = run_git(
        record.path,
        "diff",
        "--cached",
        "--binary",
        "--full-index",
        "--no-ext-diff",
        "--no-textconv",
        "--ignore-submodules=all",
    ).stdout
    unstaged = run_git(
        record.path,
        "diff",
        "--binary",
        "--full-index",
        "--no-ext-diff",
        "--no-textconv",
        "--ignore-submodules=all",
    ).stdout
    untracked_raw = run_git(
        record.path, "ls-files", "--others", "--exclude-standard", "-z"
    ).stdout
    untracked = [_decode(item) for item in untracked_raw.split(b"\0") if item]
    tracked_raw, tracked = worktree_tracked(record.path)
    ignored_raw, ignored = worktree_ignored(record.path)
    head = _git_text(record.path, "rev-parse", "--verify", "HEAD")
    return {
        "status": status,
        "staged": staged,
        "unstaged": unstaged,
        "untrackedRaw": untracked_raw,
        "untracked": untracked,
        "trackedRaw": tracked_raw,
        "tracked": tracked,
        "ignoredRaw": ignored_raw,
        "ignored": ignored,
        "head": head,
    }


def _assert_evidence_unchanged(
    record: WorktreeRecord, before: dict[str, object], after: dict[str, object]
) -> None:
    for field_name in (
        "status",
        "staged",
        "unstaged",
        "untrackedRaw",
        "trackedRaw",
        "ignoredRaw",
        "head",
    ):
        if before[field_name] != after[field_name]:
            raise PreservationError(
                f"worktree changed during capture ({field_name}): {record.path}"
            )


def _capture_tracked_entries(
    record: WorktreeRecord,
    relatives: list[str],
    destination: Path,
    nested_worktrees: dict[str, str],
) -> list[dict[str, object]]:
    manifest: list[dict[str, object]] = []
    for relative in relatives:
        pure = _safe_git_relative(relative)
        source = record.path.joinpath(*pure.parts)
        if not os.path.lexists(_fs_path(source)):
            existing_parent = source.parent
            while not os.path.exists(_fs_path(existing_parent)):
                if existing_parent == record.path:
                    break
                existing_parent = existing_parent.parent
            if not _is_within(canonical_path(existing_parent), record.physical_path):
                raise PreservationError(
                    f"missing tracked path escapes through a parent link: {source}"
                )
            manifest.append({"path": relative, "type": "missing"})
            continue
        source, pure = _safe_relative_candidate(record.path, relative)
        info = os.stat(_fs_path(source), follow_symlinks=False)
        if stat.S_ISDIR(info.st_mode) and not os.path.islink(_fs_path(source)) and not _is_reparse(info):
            nested_id = nested_worktrees.get(physical_key(source))
            if nested_id is not None and nested_id != record.id:
                manifest.append(
                    {
                        "path": relative,
                        "type": "directory",
                        "coveredByWorktreeId": nested_id,
                    }
                )
                continue
            with os.scandir(_fs_path(source)) as children:
                if next(children, None) is not None:
                    raise PreservationError(
                        f"tracked directory has raw content outside nested-worktree coverage: {source}"
                    )
            manifest.append({"path": relative, "type": "empty-directory"})
            continue
        source, pure = _safe_relative_path(record.path, relative)
        target = destination / "tracked-worktree" / Path(*pure.parts)
        evidence = _copy_verified(source, target)
        manifest.append({"path": relative, "type": "file", **evidence})
    return manifest


def _require_unique_paths(label: str, paths: list[str]) -> None:
    if len(paths) != len(set(paths)):
        raise PreservationError(f"duplicate {label} path in Git inventory")


def _capture_git_loose_entries(
    record: WorktreeRecord,
    relatives: list[str],
    kind: str,
    destination: Path,
    nested_worktrees: dict[str, str],
) -> list[dict[str, object]]:
    manifest: list[dict[str, object]] = []
    for relative in relatives:
        source, pure = _safe_relative_candidate(record.path, relative)
        info = os.stat(_fs_path(source), follow_symlinks=False)
        if stat.S_ISDIR(info.st_mode) and not os.path.islink(_fs_path(source)) and not _is_reparse(info):
            nested_id = nested_worktrees.get(physical_key(source))
            if nested_id is None or nested_id == record.id:
                raise PreservationError(
                    f"{kind} directory is not covered by a separate audited worktree: {source}"
                )
            manifest.append(
                {"path": relative, "kind": kind, "coveredByWorktreeId": nested_id}
            )
            continue
        source, pure = _safe_relative_path(record.path, relative)
        target = destination / kind / Path(*pure.parts)
        evidence = _copy_verified(source, target)
        manifest.append({"path": relative, "kind": kind, **evidence})
    return manifest


def _capture_worktree(
    record: WorktreeRecord,
    destination: Path,
    nested_worktrees: dict[str, str],
) -> dict[str, object]:
    before = _worktree_evidence(record)
    _write_new_bytes(destination / "status.porcelain-v2.z", before["status"])
    _write_new_bytes(destination / "staged.patch", before["staged"])
    _write_new_bytes(destination / "unstaged.patch", before["unstaged"])

    index_source = record.git_dir / "index"
    if not os.path.isfile(_fs_path(index_source)):
        raise PreservationError(f"worktree Git index is missing: {index_source}")
    index_evidence = _copy_verified(index_source, destination / "index.raw")

    marker = record.path / ".git"
    marker_evidence: dict[str, object] | None = None
    if os.path.isfile(_fs_path(marker)):
        marker_evidence = _copy_verified(marker, destination / "git-marker.raw")
    elif not os.path.isdir(_fs_path(marker)):
        raise PreservationError(f"worktree .git marker is missing: {marker}")

    admin_manifest: list[dict[str, object]] | None = None
    if physical_key(record.git_dir) != record.common_key:
        admin_manifest = _copy_physical_tree(
            record.git_dir, destination / "git-admin-physical"
        )
        _write_new_bytes(
            destination / "git-admin-physical.json", _json_bytes(admin_manifest)
        )

    head_bundle = destination / "head.bundle"
    run_git(record.path, "bundle", "create", head_bundle, "HEAD")
    verify = run_git(record.path, "bundle", "verify", head_bundle)
    _write_new_bytes(destination / "head-bundle-verify.stdout.txt", verify.stdout)
    _write_new_bytes(destination / "head-bundle-verify.stderr.txt", verify.stderr)

    if not all(isinstance(item, str) for item in before["tracked"]):
        raise PreservationError("invalid internal tracked-file inventory")
    if not all(isinstance(item, str) for item in before["untracked"]):
        raise PreservationError("invalid internal untracked-file inventory")
    if not all(isinstance(item, str) for item in before["ignored"]):
        raise PreservationError("invalid internal ignored-file inventory")
    _require_unique_paths("tracked", before["tracked"])
    _require_unique_paths("untracked", before["untracked"])
    _require_unique_paths("ignored", before["ignored"])
    tracked_manifest = _capture_tracked_entries(
        record,
        before["tracked"],
        destination,
        nested_worktrees,
    )
    _write_new_bytes(
        destination / "tracked-worktree-hashes.json", _json_bytes(tracked_manifest)
    )
    untracked_manifest = _capture_git_loose_entries(
        record,
        before["untracked"],
        "untracked",
        destination,
        nested_worktrees,
    )
    ignored_manifest = _capture_git_loose_entries(
        record,
        before["ignored"],
        "ignored",
        destination,
        nested_worktrees,
    )
    _write_new_bytes(
        destination / "untracked-hashes.json", _json_bytes(untracked_manifest)
    )
    _write_new_bytes(
        destination / "ignored-hashes.json", _json_bytes(ignored_manifest)
    )

    after = _worktree_evidence(record)
    _assert_evidence_unchanged(record, before, after)
    return {
        "statusSha256": sha256_bytes(before["status"]),
        "stagedPatchSha256": sha256_bytes(before["staged"]),
        "unstagedPatchSha256": sha256_bytes(before["unstaged"]),
        "trackedListSha256": sha256_bytes(before["trackedRaw"]),
        "untrackedListSha256": sha256_bytes(before["untrackedRaw"]),
        "ignoredListSha256": sha256_bytes(before["ignoredRaw"]),
        "untrackedFiles": len(untracked_manifest),
        "trackedEntries": len(tracked_manifest),
        "trackedManifestSha256": _manifest_sha256(tracked_manifest),
        "untrackedManifestSha256": _manifest_sha256(untracked_manifest),
        "ignoredManifestSha256": _manifest_sha256(ignored_manifest),
        "ignoredFiles": len(ignored_manifest),
        "indexSha256": index_evidence["sha256"],
        "gitMarkerSha256": marker_evidence["sha256"] if marker_evidence else None,
        "gitAdminPhysicalSha256": (
            _manifest_sha256(admin_manifest) if admin_manifest is not None else None
        ),
        "head": before["head"],
        "headBundleSha256": sha256_file(head_bundle),
    }


def _verify_final_worktree(
    record: WorktreeRecord,
    destination: Path,
    expected: dict[str, object],
    nested_worktrees: dict[str, str],
) -> None:
    current = _worktree_evidence(record)
    checks = {
        "statusSha256": sha256_bytes(current["status"]),
        "stagedPatchSha256": sha256_bytes(current["staged"]),
        "unstagedPatchSha256": sha256_bytes(current["unstaged"]),
        "trackedListSha256": sha256_bytes(current["trackedRaw"]),
        "untrackedListSha256": sha256_bytes(current["untrackedRaw"]),
        "ignoredListSha256": sha256_bytes(current["ignoredRaw"]),
        "head": current["head"],
    }
    for name, value in checks.items():
        if expected.get(name) != value:
            raise PreservationError(
                f"worktree changed before capture finalization ({name}): {record.path}"
            )

    index_source = record.git_dir / "index"
    if (
        sha256_file(index_source) != expected.get("indexSha256")
        or sha256_file(destination / "index.raw") != expected.get("indexSha256")
    ):
        raise PreservationError(
            f"worktree Git index changed before capture finalization: {index_source}"
        )
    marker = record.path / ".git"
    if expected.get("gitMarkerSha256") is not None:
        if (
            sha256_file(marker) != expected["gitMarkerSha256"]
            or sha256_file(destination / "git-marker.raw")
            != expected["gitMarkerSha256"]
        ):
            raise PreservationError(
                f"worktree .git marker changed before capture finalization: {marker}"
            )
    if expected.get("gitAdminPhysicalSha256") is not None:
        source_manifest = _physical_tree_manifest(record.git_dir)
        captured_manifest = _physical_tree_manifest(
            destination / "git-admin-physical"
        )
        if (
            _manifest_sha256(source_manifest)
            != expected["gitAdminPhysicalSha256"]
            or _manifest_sha256(captured_manifest)
            != expected["gitAdminPhysicalSha256"]
        ):
            raise PreservationError(
                f"worktree Git admin state changed before finalization: {record.git_dir}"
            )

    tracked_manifest_path = destination / "tracked-worktree-hashes.json"
    try:
        with open(_fs_path(tracked_manifest_path), "r", encoding="utf-8") as handle:
            tracked_manifest = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise PreservationError(
            f"cannot re-read {tracked_manifest_path}: {exc}"
        ) from exc
    if not isinstance(tracked_manifest, list):
        raise PreservationError(
            f"invalid tracked worktree manifest: {tracked_manifest_path}"
        )
    tracked_paths = [
        item.get("path") if isinstance(item, dict) else None
        for item in tracked_manifest
    ]
    if (
        not isinstance(current["tracked"], list)
        or tracked_paths != current["tracked"]
        or len(tracked_manifest) != expected.get("trackedEntries")
        or len(tracked_paths) != len(set(tracked_paths))
        or _manifest_sha256(tracked_manifest)
        != expected.get("trackedManifestSha256")
        or sha256_file(tracked_manifest_path)
        != expected.get("trackedManifestSha256")
    ):
        raise PreservationError(
            f"tracked worktree manifest membership changed: {tracked_manifest_path}"
        )
    for item in tracked_manifest:
        if not isinstance(item, dict) or not isinstance(item.get("path"), str):
            raise PreservationError(
                f"invalid tracked worktree entry: {tracked_manifest_path}"
            )
        pure = _safe_git_relative(item["path"])
        source = record.path.joinpath(*pure.parts)
        entry_type = item.get("type")
        if entry_type == "missing":
            if os.path.lexists(_fs_path(source)):
                raise PreservationError(
                    f"missing tracked path appeared before finalization: {source}"
                )
            continue
        source, pure = _safe_relative_candidate(record.path, item["path"])
        if entry_type in ("directory", "empty-directory"):
            if not os.path.isdir(_fs_path(source)):
                raise PreservationError(
                    f"tracked directory changed before finalization: {source}"
                )
            if entry_type == "directory":
                if nested_worktrees.get(physical_key(source)) != item.get(
                    "coveredByWorktreeId"
                ):
                    raise PreservationError(
                        f"tracked nested-worktree coverage changed: {source}"
                    )
            else:
                with os.scandir(_fs_path(source)) as children:
                    if next(children, None) is not None:
                        raise PreservationError(
                            f"tracked empty directory gained content: {source}"
                        )
            continue
        if entry_type != "file":
            raise PreservationError(f"unknown tracked entry type: {entry_type!r}")
        source, pure = _safe_relative_path(record.path, item["path"])
        captured = destination / "tracked-worktree" / Path(*pure.parts)
        if (
            sha256_file(source) != item.get("sha256")
            or sha256_file(captured) != item.get("sha256")
            or os.stat(_fs_path(source), follow_symlinks=False).st_size
            != item.get("bytes")
        ):
            raise PreservationError(
                f"tracked working-tree bytes changed before finalization: {source}"
            )

    for kind in ("untracked", "ignored"):
        manifest_path = destination / f"{kind}-hashes.json"
        try:
            with open(_fs_path(manifest_path), "r", encoding="utf-8") as handle:
                manifest = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise PreservationError(f"cannot re-read {manifest_path}: {exc}") from exc
        if not isinstance(manifest, list):
            raise PreservationError(f"invalid captured {kind} manifest: {manifest_path}")
        current_paths = current[kind]
        manifest_paths = [
            item.get("path") if isinstance(item, dict) else None for item in manifest
        ]
        expected_count = expected.get(f"{kind}Files")
        expected_hash = expected.get(f"{kind}ManifestSha256")
        if (
            not isinstance(current_paths, list)
            or manifest_paths != current_paths
            or len(manifest) != expected_count
            or len(manifest_paths) != len(set(manifest_paths))
            or _manifest_sha256(manifest) != expected_hash
            or sha256_file(manifest_path) != expected_hash
        ):
            raise PreservationError(
                f"{kind} manifest membership changed: {manifest_path}"
            )
        for item in manifest:
            if not isinstance(item, dict) or not isinstance(item.get("path"), str):
                raise PreservationError(f"invalid captured {kind} entry: {manifest_path}")
            source, pure = _safe_relative_candidate(record.path, item["path"])
            covered_by = item.get("coveredByWorktreeId")
            if covered_by is not None:
                if not os.path.isdir(_fs_path(source)) or nested_worktrees.get(
                    physical_key(source)
                ) != covered_by:
                    raise PreservationError(
                        f"nested worktree coverage changed before finalization: {source}"
                    )
                continue
            source, pure = _safe_relative_path(record.path, item["path"])
            captured = destination / kind / Path(*pure.parts)
            if (
                sha256_file(source) != item.get("sha256")
                or sha256_file(captured) != item.get("sha256")
                or os.stat(_fs_path(source), follow_symlinks=False).st_size
                != item.get("bytes")
            ):
                raise PreservationError(
                    f"{kind} file changed before capture finalization: {source}"
                )


def _common_refs(common: Path) -> bytes:
    return run_git_dir(
        common,
        "for-each-ref",
        "--format=%(refname)%00%(objectname)%00%(objecttype)",
    ).stdout


def _capture_common_git(record: CommonGitRecord, destination: Path) -> dict[str, object]:
    refs_before = _common_refs(record.path)
    registrations_before, _parsed = registered_worktrees(record.path)

    common_manifest = _copy_physical_tree(
        record.path, destination / "common-git-physical"
    )
    _write_new_bytes(
        destination / "common-git-physical.json", _json_bytes(common_manifest)
    )
    alternate_evidence: list[dict[str, object]] = []
    for number, alternate in enumerate(record.alternate_object_dirs, 1):
        alternate_id = f"alternate-{number:03d}"
        manifest = _copy_physical_tree(
            alternate,
            destination / "alternate-object-dirs" / alternate_id / "objects-physical",
        )
        _write_new_bytes(
            destination
            / "alternate-object-dirs"
            / alternate_id
            / "objects-physical.json",
            _json_bytes(manifest),
        )
        alternate_evidence.append(
            {
                "id": alternate_id,
                "source": str(alternate),
                "physicalSha256": _manifest_sha256(manifest),
            }
        )
    lfs_evidence: list[dict[str, object]] = []
    for number, lfs_dir in enumerate(record.external_lfs_dirs, 1):
        lfs_id = f"lfs-{number:03d}"
        manifest = _copy_physical_tree(
            lfs_dir,
            destination / "external-lfs-dirs" / lfs_id / "storage-physical",
        )
        _write_new_bytes(
            destination
            / "external-lfs-dirs"
            / lfs_id
            / "storage-physical.json",
            _json_bytes(manifest),
        )
        lfs_evidence.append(
            {
                "id": lfs_id,
                "source": str(lfs_dir),
                "physicalSha256": _manifest_sha256(manifest),
            }
        )
    hook_evidence: list[dict[str, object]] = []
    for number, hook_dir in enumerate(record.external_hook_dirs, 1):
        hook_id = f"hooks-{number:03d}"
        manifest = _copy_physical_tree(
            hook_dir,
            destination / "external-hook-dirs" / hook_id / "hooks-physical",
        )
        _write_new_bytes(
            destination
            / "external-hook-dirs"
            / hook_id
            / "hooks-physical.json",
            _json_bytes(manifest),
        )
        hook_evidence.append(
            {
                "id": hook_id,
                "source": str(hook_dir),
                "physicalSha256": _manifest_sha256(manifest),
            }
        )

    source_fsck = run_git_dir(record.path, "fsck", "--full", "--strict", check=False)
    _write_new_bytes(destination / "source-fsck.stdout.txt", source_fsck.stdout)
    _write_new_bytes(destination / "source-fsck.stderr.txt", source_fsck.stderr)
    if source_fsck.returncode != 0:
        raise PreservationError(f"source git fsck failed: {record.path}")

    bundle = destination / "repository.bundle"
    run_git_dir(record.path, "bundle", "create", bundle, "--all")
    bundle_verify = run_git_dir(record.path, "bundle", "verify", bundle)
    _write_new_bytes(destination / "bundle-verify.stdout.txt", bundle_verify.stdout)
    _write_new_bytes(destination / "bundle-verify.stderr.txt", bundle_verify.stderr)

    mirror = destination / "mirror.git"
    run_command((*GIT_BASE, "clone", "--mirror", "--no-local", record.path, mirror))
    mirror_fsck = run_git_dir(mirror, "fsck", "--full", "--strict", check=False)
    _write_new_bytes(destination / "mirror-fsck.stdout.txt", mirror_fsck.stdout)
    _write_new_bytes(destination / "mirror-fsck.stderr.txt", mirror_fsck.stderr)
    if mirror_fsck.returncode != 0:
        raise PreservationError(f"captured mirror git fsck failed: {record.path}")

    refs_after = _common_refs(record.path)
    registrations_after, _parsed_after = registered_worktrees(record.path)
    if refs_before != refs_after or registrations_before != registrations_after:
        raise PreservationError(f"Git refs/worktree registrations changed during capture: {record.path}")
    _write_new_bytes(destination / "refs.txt", refs_before)
    _write_new_bytes(destination / "worktree-list.porcelain.z", registrations_before)
    return {
        "bundleSha256": sha256_file(bundle),
        "commonGitPhysicalSha256": _manifest_sha256(common_manifest),
        "alternateObjectDirs": alternate_evidence,
        "externalLfsDirs": lfs_evidence,
        "externalHookDirs": hook_evidence,
        "refsSha256": sha256_bytes(refs_before),
        "worktreeListSha256": sha256_bytes(registrations_before),
        "sourceFsckReturnCode": source_fsck.returncode,
        "mirrorFsckReturnCode": mirror_fsck.returncode,
    }


def _verify_final_common_git(
    record: CommonGitRecord, destination: Path, expected: dict[str, object]
) -> None:
    refs = _common_refs(record.path)
    registrations, _parsed = registered_worktrees(record.path)
    if sha256_bytes(refs) != expected.get("refsSha256"):
        raise PreservationError(
            f"Git refs changed before capture finalization: {record.path}"
        )
    if sha256_bytes(registrations) != expected.get("worktreeListSha256"):
        raise PreservationError(
            f"worktree registrations changed before capture finalization: {record.path}"
        )
    source_manifest = _physical_tree_manifest(record.path)
    captured_manifest = _physical_tree_manifest(
        destination / "common-git-physical"
    )
    if (
        _manifest_sha256(source_manifest) != expected.get("commonGitPhysicalSha256")
        or _manifest_sha256(captured_manifest)
        != expected.get("commonGitPhysicalSha256")
    ):
        raise PreservationError(
            f"common Git physical state changed before finalization: {record.path}"
        )
    alternate_expected = expected.get("alternateObjectDirs")
    if not isinstance(alternate_expected, list) or len(alternate_expected) != len(
        record.alternate_object_dirs
    ):
        raise PreservationError("invalid captured Git alternate evidence")
    for alternate, item in zip(record.alternate_object_dirs, alternate_expected):
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            raise PreservationError("invalid captured Git alternate entry")
        captured = (
            destination
            / "alternate-object-dirs"
            / item["id"]
            / "objects-physical"
        )
        if (
            _manifest_sha256(_physical_tree_manifest(alternate))
            != item.get("physicalSha256")
            or _manifest_sha256(_physical_tree_manifest(captured))
            != item.get("physicalSha256")
        ):
            raise PreservationError(
                f"Git alternate object directory changed before finalization: {alternate}"
            )
    lfs_expected = expected.get("externalLfsDirs")
    if not isinstance(lfs_expected, list) or len(lfs_expected) != len(
        record.external_lfs_dirs
    ):
        raise PreservationError("invalid captured external LFS evidence")
    for lfs_dir, item in zip(record.external_lfs_dirs, lfs_expected):
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            raise PreservationError("invalid captured external LFS entry")
        captured = (
            destination
            / "external-lfs-dirs"
            / item["id"]
            / "storage-physical"
        )
        if (
            _manifest_sha256(_physical_tree_manifest(lfs_dir))
            != item.get("physicalSha256")
            or _manifest_sha256(_physical_tree_manifest(captured))
            != item.get("physicalSha256")
        ):
            raise PreservationError(
                f"external LFS storage changed before finalization: {lfs_dir}"
            )
    hook_expected = expected.get("externalHookDirs")
    if not isinstance(hook_expected, list) or len(hook_expected) != len(
        record.external_hook_dirs
    ):
        raise PreservationError("invalid captured external hooks evidence")
    for hook_dir, item in zip(record.external_hook_dirs, hook_expected):
        if not isinstance(item, dict) or not isinstance(item.get("id"), str):
            raise PreservationError("invalid captured external hooks entry")
        captured = (
            destination
            / "external-hook-dirs"
            / item["id"]
            / "hooks-physical"
        )
        if (
            _manifest_sha256(_physical_tree_manifest(hook_dir))
            != item.get("physicalSha256")
            or _manifest_sha256(_physical_tree_manifest(captured))
            != item.get("physicalSha256")
        ):
            raise PreservationError(
                f"external Git hooks directory changed before finalization: {hook_dir}"
            )


def _restore_instructions() -> str:
    return """# Restore-Anleitung (Rettungspaket)

Dieses Paket ist eine Beweissicherung, keine automatische Bereinigung.

1. Alle Dateien zunächst gegen `CAPTURE_SHA256.json` prüfen; danach
   `inventory.json` und die inhaltlichen Nachweise in `capture-evidence.json`
   prüfen.
2. `common-git-physical/` ist die byteweise forensische Kopie einschließlich
   Reflogs, Config, Hooks, unerreichbarer Objekte und lokaler LFS-Daten. Sie
   niemals direkt ausführen oder als aktives Repository öffnen; zunächst eine
   weitere schreibgeschützte Kopie erstellen und Config, Hooks und Lockdateien
   manuell prüfen. Externe Object-Alternates liegen separat unter
   `alternate-object-dirs/`, extern konfigurierte LFS-Speicher unter
   `external-lfs-dirs/` und externe Hooks unter `external-hook-dirs/`. Hook-
   Dateien niemals aus dem Rettungspaket ausführen.
3. Für jedes `repositories/repository-NNN/mirror.git` zuerst
   `git --git-dir <mirror.git> fsck --full --strict` ausführen.
4. Aus dem Mirror in einen **neuen** Zielpfad klonen. Niemals über einen noch
   vorhandenen Original-Worktree restaurieren.
5. Falls ein detached oder sonst nicht referenzierter Worktree-HEAD benötigt
   wird, dessen `worktrees/worktree-NNN/head.bundle` in den neuen Klon fetchen.
6. `tracked-worktree/` enthält die rohen Bytes aller physisch vorhandenen
   regulären getrackten Dateien, einschließlich durch Assume-unchanged,
   Skip-worktree, Clean-/EOL-Filter oder Intent-to-add sonst unsichtbarer
   Zustände. Nur anhand von `tracked-worktree-hashes.json` in die Wegwerfkopie
   übertragen.
7. `index.raw`, `git-marker.raw` und `git-admin-physical/` bewahren auch
   Intent-to-add/Index-Flags und laufende Worktree-Adminzustände. Diese Dateien
   nur nach Prüfung von HEAD, Objektbestand und absoluten Gitdir-Verweisen in
   einer Wegwerfkopie verwenden; nicht blind in einen neuen Klon kopieren.
8. Zuerst `staged.patch` mit `git apply --index --binary`, danach
   `unstaged.patch` mit `git apply --binary` anwenden. Leere Patchdateien sind
   zulässig.
9. Dateien aus `untracked/` und `ignored/` anhand ihrer Hash-Manifeste einzeln
   kopieren und danach erneut SHA-256 prüfen.
10. Dateien unter `workspace-root-files/` und `workspace-loose-files/` nur in
   einen separat geprüften Archivpfad kopieren und ihre Hash-Manifeste prüfen.
11. Erst nach manueller Sichtung und einem zweiten unabhängigen Backup über eine
   Bereinigung alter Worktrees entscheiden. Dieses Werkzeug führt weder
   `clean`, `reset`, `prune`, Löschungen, Verschiebungen noch Überschreibungen aus.

Hinweis: Warnungen in `inventory.json`, Spezialdateien oder ein partielles Paket
dürfen nicht übergangen werden. NTFS-ACLs, Alternate Data Streams und
Hardlink-Beziehungen sind keine durch SHA-256 belegten Paketbestandteile.
"""


def _captured_tree_hashes(root: Path) -> list[dict[str, object]]:
    entries: list[dict[str, object]] = []
    excluded = {"CAPTURE_COMPLETE.txt", "CAPTURE_SHA256.json"}
    for current_raw, directories, filenames in os.walk(
        _fs_path(root), topdown=True, followlinks=False
    ):
        current = Path(_display_path(current_raw))
        for name in directories:
            directory = current / name
            info = os.stat(_fs_path(directory), follow_symlinks=False)
            reparse = bool(
                os.name == "nt"
                and getattr(info, "st_file_attributes", 0)
                & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
            )
            if os.path.islink(_fs_path(directory)) or reparse:
                raise PreservationError(
                    f"unexpected link/reparse directory in capture: {directory}"
                )
        for name in filenames:
            path = current / name
            relative = path.relative_to(root).as_posix()
            if relative in excluded:
                continue
            info = os.stat(_fs_path(path), follow_symlinks=False)
            reparse = bool(
                os.name == "nt"
                and getattr(info, "st_file_attributes", 0)
                & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
            )
            if not stat.S_ISREG(info.st_mode) or os.path.islink(_fs_path(path)) or reparse:
                raise PreservationError(
                    f"unexpected special file in capture: {path}"
                )
            entries.append(
                {"path": relative, "bytes": info.st_size, "sha256": sha256_file(path)}
            )
    return sorted(entries, key=lambda item: str(item["path"]))


def _verify_captured_tree_hashes(root: Path, expected: list[dict[str, object]]) -> None:
    if _captured_tree_hashes(root) != expected:
        raise PreservationError("captured rescue tree changed before finalization")


def capture_workspace(
    workspace: Path,
    rescue_root: Path = DEFAULT_RESCUE_ROOT,
    *,
    now: datetime | None = None,
) -> Path:
    audit = audit_workspace(workspace)
    conflicted = [
        f"{record.path}: {', '.join(record.status.conflict_paths)}"
        for record in audit.worktrees
        if record.status.conflict_paths
    ]
    if conflicted:
        raise PreservationError(
            "capture refused because unmerged index stages cannot be restored "
            "losslessly from patches: " + "; ".join(conflicted)
        )
    if audit.warnings:
        raise PreservationError(
            "capture refused because registered worktrees are stale/inaccessible: "
            + "; ".join(audit.warnings)
        )
    rescue_root = _validate_capture_root(rescue_root, audit)
    os.makedirs(_fs_path(rescue_root), exist_ok=True)

    moment = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    timestamp = moment.strftime("%Y%m%dT%H%M%S.%fZ")
    final = rescue_root / f"run-{timestamp}"
    partial = rescue_root / f".run-{timestamp}.partial-{uuid.uuid4().hex}"
    if os.path.exists(_fs_path(final)) or os.path.exists(_fs_path(partial)):
        raise PreservationError(f"capture destination already exists: {final}")
    os.makedirs(_fs_path(partial), exist_ok=False)

    try:
        document = audit_to_dict(audit, captured_at=moment.isoformat().replace("+00:00", "Z"))
        _write_new_bytes(partial / "inventory.json", _json_bytes(document))
        _write_new_text(partial / "RESTORE.md", _restore_instructions())

        capture_evidence: dict[str, object] = {"repositories": {}, "worktrees": {}}
        worktree_ids_by_physical = {
            record.physical_key: record.id for record in audit.worktrees
        }
        for common in audit.common_git_dirs:
            evidence = _capture_common_git(
                common, partial / "repositories" / common.id
            )
            capture_evidence["repositories"][common.id] = evidence

        for worktree in audit.worktrees:
            evidence = _capture_worktree(
                worktree,
                partial / "worktrees" / worktree.id,
                worktree_ids_by_physical,
            )
            capture_evidence["worktrees"][worktree.id] = evidence

        root_manifest: list[dict[str, object]] = []
        for root_file in audit.root_files:
            relative = str(root_file["path"])
            source = audit.workspace / relative
            destination = partial / "workspace-root-files" / relative
            copied = _copy_verified(source, destination)
            if copied != {"bytes": root_file["bytes"], "sha256": root_file["sha256"]}:
                raise PreservationError(f"workspace root file changed during capture: {source}")
            root_manifest.append({"path": relative, **copied})
        _write_new_bytes(
            partial / "workspace-root-files.json", _json_bytes(root_manifest)
        )

        loose_manifest: list[dict[str, object]] = []
        for loose_file in audit.loose_files:
            relative = str(loose_file["path"])
            pure = PurePosixPath(relative)
            source = audit.workspace.joinpath(*pure.parts)
            destination = partial / "workspace-loose-files" / Path(*pure.parts)
            copied = _copy_verified(source, destination)
            if copied != {
                "bytes": loose_file["bytes"],
                "sha256": loose_file["sha256"],
            }:
                raise PreservationError(
                    f"workspace loose file changed during capture: {source}"
                )
            loose_manifest.append({"path": relative, **copied})
        _write_new_bytes(
            partial / "workspace-loose-files.json", _json_bytes(loose_manifest)
        )

        final_audit = audit_workspace(workspace)
        if audit_to_dict(final_audit) != audit_to_dict(audit):
            raise PreservationError(
                "workspace inventory changed before capture finalization"
            )
        for common in audit.common_git_dirs:
            expected = capture_evidence["repositories"][common.id]
            if not isinstance(expected, dict):
                raise PreservationError("invalid internal repository evidence")
            _verify_final_common_git(
                common, partial / "repositories" / common.id, expected
            )
        for worktree in audit.worktrees:
            expected = capture_evidence["worktrees"][worktree.id]
            if not isinstance(expected, dict):
                raise PreservationError("invalid internal worktree evidence")
            _verify_final_worktree(
                worktree,
                partial / "worktrees" / worktree.id,
                expected,
                worktree_ids_by_physical,
            )
        for item in root_manifest:
            source = audit.workspace / str(item["path"])
            captured = partial / "workspace-root-files" / str(item["path"])
            if (
                sha256_file(source) != item["sha256"]
                or sha256_file(captured) != item["sha256"]
            ):
                raise PreservationError(
                    f"workspace root file changed before capture finalization: {source}"
                )
        for item in loose_manifest:
            pure = PurePosixPath(str(item["path"]))
            source = audit.workspace.joinpath(*pure.parts)
            captured = partial / "workspace-loose-files" / Path(*pure.parts)
            if (
                sha256_file(source) != item["sha256"]
                or sha256_file(captured) != item["sha256"]
            ):
                raise PreservationError(
                    f"workspace loose file changed before capture finalization: {source}"
                )
        _write_new_bytes(partial / "capture-evidence.json", _json_bytes(capture_evidence))
        tree_hashes = _captured_tree_hashes(partial)
        _write_new_bytes(partial / "CAPTURE_SHA256.json", _json_bytes(tree_hashes))
        _verify_captured_tree_hashes(partial, tree_hashes)
        os.replace(_fs_path(partial), _fs_path(final))
        pending_complete = final / ".CAPTURE_COMPLETE.pending"
        _write_new_text(pending_complete, f"PASS {timestamp}\n")
        os.replace(
            _fs_path(pending_complete),
            _fs_path(final / "CAPTURE_COMPLETE.txt"),
        )
        return final
    except Exception as exc:
        failure_root = final if os.path.isdir(_fs_path(final)) else partial
        try:
            _write_new_text(failure_root / "CAPTURE_FAILED.txt", f"FAIL: {exc}\n")
        except Exception:
            pass
        raise


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)
    audit_parser = subcommands.add_parser("audit", help="read-only JSON inventory")
    audit_parser.add_argument("--workspace", type=Path, required=True)
    capture_parser = subcommands.add_parser(
        "capture", help="create a new verified rescue package"
    )
    capture_parser.add_argument("--workspace", type=Path, required=True)
    capture_parser.add_argument(
        "--rescue-root", type=Path, default=DEFAULT_RESCUE_ROOT
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "audit":
            audit = audit_workspace(args.workspace)
            confirmation = audit_workspace(args.workspace)
            if audit_to_dict(audit) != audit_to_dict(confirmation):
                raise PreservationError("workspace changed during read-only audit")
            print(json.dumps(audit_to_dict(audit), indent=2, ensure_ascii=True, sort_keys=True))
        else:
            destination = capture_workspace(args.workspace, args.rescue_root)
            print(json.dumps({"status": "PASS", "capture": str(destination)}))
        return 0
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"status": "FAIL", "error": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
