#!/usr/bin/env python3
"""Run a read-only Admin editor live-sync certification preflight."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from typing import Callable

import kgg_admin_editor_sync_candidate as candidate


ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "docs" / "kgg-custom-gpt-editor-snapshot.json"
REQUEST_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{5,63}$")
MAIN_BRANCH = "main"
SUCCESS_STATES = {"would_certify", "no_change"}


class PreflightError(RuntimeError):
    pass


def _git(
    repo_root: Path,
    *args: str,
    check: bool = True,
) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if check and proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip() or "git command failed"
        raise PreflightError(detail)
    return proc.stdout.strip()


def read_default_branch() -> str:
    branch = os.environ.get("KGG_DEFAULT_BRANCH", "").strip()
    if not branch:
        raise PreflightError("KGG_DEFAULT_BRANCH is required from repository metadata")
    return branch


def read_checkout_sha(repo_root: Path = ROOT) -> str:
    sha = _git(repo_root, "rev-parse", "HEAD")
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise PreflightError("checked-out HEAD is not a full lowercase commit SHA")
    return sha


def read_current_main_sha(repo_root: Path = ROOT, branch: str = MAIN_BRANCH) -> str:
    if branch != MAIN_BRANCH:
        raise PreflightError(f"default branch must remain {MAIN_BRANCH!r}")
    _git(
        repo_root,
        "fetch",
        "--no-tags",
        "origin",
        f"refs/heads/{branch}:refs/remotes/origin/{branch}",
    )
    sha = _git(repo_root, "rev-parse", f"refs/remotes/origin/{branch}")
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise PreflightError("remote main is not a full lowercase commit SHA")
    return sha


def read_worktree_status(repo_root: Path = ROOT) -> str:
    return _git(repo_root, "status", "--porcelain", "--untracked-files=all")


def sha256_file(path: Path) -> str:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except Exception as exc:  # noqa: BLE001
        raise PreflightError(f"cannot hash Admin editor snapshot: {exc}") from exc


def _safe_error(exc: Exception | str) -> str:
    text = str(exc).strip().replace("\x00", "")
    return text[:1000] or "unknown preflight failure"


def run_preflight(
    request_id: str,
    *,
    repo_root: Path = ROOT,
    snapshot_path: Path | None = None,
    default_branch_reader: Callable[[], str] = read_default_branch,
    current_main_sha_reader: Callable[[Path, str], str] = read_current_main_sha,
    checkout_sha_reader: Callable[[Path], str] = read_checkout_sha,
    worktree_reader: Callable[[Path], str] = read_worktree_status,
    snapshot_hasher: Callable[[Path], str] = sha256_file,
    audit_runner: Callable[..., dict] = candidate.run_canonical_audit,
    candidate_builder: Callable[..., dict] = candidate.build_candidate,
) -> dict:
    result: dict[str, object] = {
        "request_id": request_id,
        "startMainSha": None,
        "endMainSha": None,
        "preflightStatus": "failed",
        "resourceAudit": "not_run",
        "candidateAudit": "not_run",
        "changedFields": [],
        "snapshotSha256Before": None,
        "snapshotSha256After": None,
        "snapshotUnchanged": False,
        "worktreeCleanBefore": False,
        "worktreeCleanAfter": False,
        "headUnchanged": False,
        "repositoryWriteDetected": False,
    }
    if not REQUEST_ID_RE.fullmatch(request_id):
        result["error"] = "request_id contains unsupported characters"
        return result

    snapshot_path = snapshot_path or (
        repo_root / "docs" / "kgg-custom-gpt-editor-snapshot.json"
    )

    try:
        default_branch = default_branch_reader()
        if default_branch != MAIN_BRANCH:
            raise PreflightError(
                f"default branch must remain {MAIN_BRANCH!r}, got {default_branch!r}"
            )
        before_snapshot_hash = snapshot_hasher(snapshot_path)
        before_worktree = worktree_reader(repo_root)
        before_head = checkout_sha_reader(repo_root)
        start_main_sha = current_main_sha_reader(repo_root, default_branch)
        result["snapshotSha256Before"] = before_snapshot_hash
        result["worktreeCleanBefore"] = before_worktree == ""
        result["startMainSha"] = start_main_sha
        if before_worktree:
            raise PreflightError("preflight requires a clean checkout")

        tentative_status = "failed"
        tentative_error: str | None = None
        if before_head != start_main_sha:
            tentative_status = "stale_base"
            tentative_error = (
                f"checked-out HEAD {before_head} does not match current main {start_main_sha}"
            )
        else:
            try:
                resource_result = audit_runner(
                    snapshot_path,
                    require_live_synced=False,
                    repo_root=repo_root,
                )
                resource_status = resource_result.get("status")
            except candidate.CandidateError as exc:
                resource_status = "FAIL"
                tentative_status = "stale_context"
                tentative_error = _safe_error(exc)
            result["resourceAudit"] = resource_status

            if resource_status == "LIVE_PASS":
                tentative_status = "no_change"
            elif resource_status == "TARGET_PASS":
                candidate_result = candidate_builder(
                    repo_root=repo_root,
                    snapshot_path=snapshot_path,
                    main_sha_reader=lambda _root: start_main_sha,
                    audit_runner=audit_runner,
                )
                candidate_status = candidate_result.get("status")
                if candidate_status == "LIVE_PASS":
                    changed_fields = set(candidate_result.get("changedFields", []))
                    if changed_fields != candidate.ALLOWED_CERTIFICATION_FIELDS:
                        result["candidateAudit"] = "FAIL"
                        tentative_status = "failed"
                        tentative_error = (
                            "candidate changedFields must be exactly the three "
                            "certification fields"
                        )
                    else:
                        result["candidateAudit"] = "LIVE_PASS"
                        result["changedFields"] = sorted(changed_fields)
                        tentative_status = "would_certify"
                elif candidate_status == "stale_context":
                    result["candidateAudit"] = "not_run"
                    tentative_status = "stale_context"
                    tentative_error = _safe_error(
                        candidate_result.get("error", "candidate context is stale")
                    )
                else:
                    result["candidateAudit"] = candidate_status or "FAIL"
                    tentative_status = "failed"
                    tentative_error = _safe_error(
                        candidate_result.get("error", "candidate validation failed")
                    )
            elif resource_status != "FAIL":
                tentative_status = "stale_context"
                tentative_error = (
                    "Admin editor snapshot must be TARGET_PASS or LIVE_PASS, got "
                    f"{resource_status!r}"
                )

        after_snapshot_hash = snapshot_hasher(snapshot_path)
        after_worktree = worktree_reader(repo_root)
        after_head = checkout_sha_reader(repo_root)
        end_main_sha = current_main_sha_reader(repo_root, default_branch)
        result["snapshotSha256After"] = after_snapshot_hash
        result["snapshotUnchanged"] = before_snapshot_hash == after_snapshot_hash
        result["worktreeCleanAfter"] = after_worktree == ""
        result["headUnchanged"] = before_head == after_head
        result["endMainSha"] = end_main_sha

        write_detected = (
            before_snapshot_hash != after_snapshot_hash
            or before_worktree != after_worktree
            or before_head != after_head
            or bool(after_worktree)
        )
        result["repositoryWriteDetected"] = write_detected
        if write_detected:
            result["preflightStatus"] = "failed"
            result["error"] = "repository or snapshot mutation detected during preflight"
            return result

        if end_main_sha != start_main_sha:
            result["preflightStatus"] = "stale_base"
            result["error"] = (
                f"main changed during preflight: start={start_main_sha} end={end_main_sha}"
            )
            return result

        result["preflightStatus"] = tentative_status
        if tentative_error:
            result["error"] = tentative_error
        return result
    except Exception as exc:  # noqa: BLE001
        result["preflightStatus"] = "failed"
        result["error"] = _safe_error(exc)
        return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request-id", required=True)
    args = parser.parse_args()
    result = run_preflight(args.request_id)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    status = result.get("preflightStatus")
    if status in SUCCESS_STATES:
        return 0
    if status == "stale_context":
        return 2
    if status == "stale_base":
        return 3
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
