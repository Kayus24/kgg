#!/usr/bin/env python3
"""Create a guarded Admin editor live-sync snapshot-only pull request."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from typing import Any

import kgg_admin_editor_sync_candidate as candidate
import kgg_admin_editor_sync_preflight as preflight
import kgg_custom_gpt_resource_audit as audit


ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_REL = Path("docs/kgg-custom-gpt-editor-snapshot.json")
SNAPSHOT = ROOT / SNAPSHOT_REL
MAIN_BRANCH = "main"
APPROVAL_PHRASE = "Gut für Main"
BRANCH_PREFIX = "admin-editor-sync"
SUCCESS_STATES = {"pr_created", "existing_pr", "no_change", "existing_request"}
_MAIN_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class PrGateError(RuntimeError):
    pass


def _run(
    args: list[str],
    *,
    cwd: Path = ROOT,
    check: bool = True,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        args,
        cwd=str(cwd),
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    if check and proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip() or "command failed"
        raise PrGateError(f"{' '.join(args)}: {detail}")
    return proc


def _git(repo_root: Path, *args: str, check: bool = True) -> str:
    return _run(
        ["git", "-C", str(repo_root), *args],
        cwd=repo_root,
        check=check,
    ).stdout.strip()


def _safe_error(value: Exception | str) -> str:
    text = str(value).replace("\x00", "").strip()
    return text[:1000] or "unknown Admin editor sync PR-gate failure"


def read_repository_name() -> str:
    repository = os.environ.get("GITHUB_REPOSITORY", "").strip()
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise PrGateError("GITHUB_REPOSITORY is missing or invalid")
    return repository


def branch_name_for_request(request_id: str) -> str:
    if not preflight.REQUEST_ID_RE.fullmatch(request_id):
        raise PrGateError("request_id contains unsupported characters")
    return f"{BRANCH_PREFIX}/{request_id}"


def _gh_json(args: list[str], *, repo_root: Path = ROOT) -> Any:
    proc = _run(["gh", *args], cwd=repo_root)
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise PrGateError("GitHub CLI returned invalid JSON") from exc


def find_existing_request_pr(
    repository: str,
    branch_name: str,
    *,
    repo_root: Path = ROOT,
) -> dict[str, Any] | None:
    records = _gh_json(
        [
            "pr",
            "list",
            "--repo",
            repository,
            "--head",
            branch_name,
            "--state",
            "all",
            "--limit",
            "20",
            "--json",
            "number,url,state,headRefName,baseRefName,title",
        ],
        repo_root=repo_root,
    )
    if not isinstance(records, list):
        raise PrGateError("GitHub PR lookup returned an invalid result")
    matches = [
        item
        for item in records
        if isinstance(item, dict)
        and item.get("headRefName") == branch_name
        and item.get("baseRefName") == MAIN_BRANCH
    ]
    if not matches:
        return None
    matches.sort(key=lambda item: item.get("state") != "OPEN")
    return matches[0]


def remote_branch_exists(
    repo_root: Path,
    branch_name: str,
) -> bool:
    proc = _run(
        [
            "git",
            "-C",
            str(repo_root),
            "ls-remote",
            "--exit-code",
            "origin",
            f"refs/heads/{branch_name}",
        ],
        cwd=repo_root,
        check=False,
    )
    if proc.returncode == 0:
        return True
    if proc.returncode == 2:
        return False
    detail = proc.stderr.strip() or proc.stdout.strip() or "git ls-remote failed"
    raise PrGateError(detail)


def _json_object(text: str, *, label: str) -> dict[str, Any]:
    try:
        value = json.loads(text)
    except json.JSONDecodeError as exc:
        raise PrGateError(f"{label} is not valid JSON") from exc
    if not isinstance(value, dict):
        raise PrGateError(f"{label} must be a JSON object")
    return value


def read_snapshot_from_git(repo_root: Path, ref: str) -> dict[str, Any]:
    text = _git(repo_root, "show", f"{ref}:{SNAPSHOT_REL.as_posix()}")
    return _json_object(text, label=f"snapshot at {ref}")


def read_snapshot_file(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception as exc:  # noqa: BLE001
        raise PrGateError(f"cannot read Admin editor snapshot: {exc}") from exc
    return _json_object(text, label="working Admin editor snapshot")


def changed_snapshot_fields(
    before: dict[str, Any],
    after: dict[str, Any],
) -> set[str]:
    return candidate.changed_top_level_fields(before, after)


def write_snapshot_file(path: Path, document: dict[str, Any]) -> None:
    path.write_text(
        json.dumps(document, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _status_paths(repo_root: Path) -> set[str]:
    raw = _run(
        [
            "git",
            "-C",
            str(repo_root),
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
        ],
        cwd=repo_root,
    ).stdout.rstrip("\n")
    paths: set[str] = set()
    for line in raw.splitlines():
        if not line:
            continue
        if len(line) < 4:
            raise PrGateError("cannot parse git status during snapshot-only diff check")
        path = line[3:]
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        paths.add(path)
    return paths


def validate_snapshot_only_worktree(
    repo_root: Path,
    *,
    base_sha: str,
    snapshot_path: Path,
) -> list[str]:
    expected_path = SNAPSHOT_REL.as_posix()
    status_paths = _status_paths(repo_root)
    if status_paths != {expected_path}:
        raise PrGateError(
            "snapshot PR worktree must change exactly one file: "
            + ", ".join(sorted(status_paths))
        )
    diff_paths = {
        line.strip()
        for line in _git(repo_root, "diff", "--name-only", "--").splitlines()
        if line.strip()
    }
    if diff_paths != {expected_path}:
        raise PrGateError(
            "snapshot PR diff must contain exactly the Admin editor snapshot"
        )
    if _run(
        ["git", "-C", str(repo_root), "diff", "--check"],
        cwd=repo_root,
        check=False,
    ).returncode != 0:
        raise PrGateError("snapshot PR diff failed git diff --check")
    before = read_snapshot_from_git(repo_root, base_sha)
    after = read_snapshot_file(snapshot_path)
    fields = changed_snapshot_fields(before, after)
    if fields != candidate.ALLOWED_CERTIFICATION_FIELDS:
        raise PrGateError(
            "snapshot PR must change exactly the three certification fields; got "
            + ", ".join(sorted(fields))
        )
    return sorted(fields)


def validate_staged_snapshot_only(repo_root: Path, *, base_sha: str) -> None:
    expected_path = SNAPSHOT_REL.as_posix()
    staged_paths = {
        line.strip()
        for line in _git(repo_root, "diff", "--cached", "--name-only").splitlines()
        if line.strip()
    }
    if staged_paths != {expected_path}:
        raise PrGateError("staged PR diff must contain exactly one snapshot file")
    proc = _run(
        ["git", "-C", str(repo_root), "diff", "--cached", "--check"],
        cwd=repo_root,
        check=False,
    )
    if proc.returncode != 0:
        raise PrGateError("staged snapshot PR failed git diff --cached --check")
    before = read_snapshot_from_git(repo_root, base_sha)
    after_text = _git(repo_root, "show", f":{SNAPSHOT_REL.as_posix()}")
    after = _json_object(after_text, label="staged Admin editor snapshot")
    fields = changed_snapshot_fields(before, after)
    if fields != candidate.ALLOWED_CERTIFICATION_FIELDS:
        raise PrGateError(
            "staged snapshot PR changed forbidden certification fields"
        )


def validate_committed_snapshot_only(repo_root: Path) -> None:
    expected_path = SNAPSHOT_REL.as_posix()
    files = {
        line.strip()
        for line in _git(
            repo_root,
            "diff-tree",
            "--no-commit-id",
            "--name-only",
            "-r",
            "HEAD",
        ).splitlines()
        if line.strip()
    }
    if files != {expected_path}:
        raise PrGateError("commit must contain exactly one Admin editor snapshot file")
    before = read_snapshot_from_git(repo_root, "HEAD^")
    after = read_snapshot_from_git(repo_root, "HEAD")
    fields = changed_snapshot_fields(before, after)
    if fields != candidate.ALLOWED_CERTIFICATION_FIELDS:
        raise PrGateError("committed snapshot changed forbidden certification fields")


def cleanup_local_branch(repo_root: Path, branch_name: str, base_sha: str) -> None:
    _git(repo_root, "restore", "--staged", "--worktree", "--", SNAPSHOT_REL.as_posix(), check=False)
    _git(repo_root, "switch", "--detach", base_sha, check=False)
    _git(repo_root, "branch", "-D", branch_name, check=False)


def cleanup_remote_branch(repo_root: Path, branch_name: str) -> None:
    _git(repo_root, "push", "origin", "--delete", branch_name, check=False)


def create_pull_request(
    *,
    repository: str,
    branch_name: str,
    request_id: str,
    base_sha: str,
    repo_root: Path,
) -> dict[str, Any]:
    body = (
        "Guarded Admin editor live-sync snapshot certification.\n\n"
        f"- request_id: `{request_id}`\n"
        f"- certified resource base: `{base_sha}`\n"
        "- changed file: `docs/kgg-custom-gpt-editor-snapshot.json`\n"
        "- allowed fields: `syncStatus`, `lastVerifiedAt`, `lastVerifiedMainCommit`\n\n"
        "This pull request never writes directly to `main` and is not auto-merged.\n"
    )
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="\n",
        prefix="kgg-admin-editor-sync-pr-",
        suffix=".md",
        delete=False,
    ) as handle:
        body_path = Path(handle.name)
        handle.write(body)
    try:
        proc = _run(
            [
                "gh",
                "pr",
                "create",
                "--repo",
                repository,
                "--base",
                MAIN_BRANCH,
                "--head",
                branch_name,
                "--title",
                f"[admin-editor-sync] {request_id}",
                "--body-file",
                str(body_path),
            ],
            cwd=repo_root,
        )
    finally:
        body_path.unlink(missing_ok=True)
    url = proc.stdout.strip()
    match = re.fullmatch(r"https://github\.com/[^/]+/[^/]+/pull/(\d+)", url)
    if not match:
        raise PrGateError("GitHub PR creation did not return a canonical PR URL")
    return {"number": int(match.group(1)), "url": url, "state": "OPEN"}


def _result_template(request_id: str, branch_name: str | None = None) -> dict[str, Any]:
    return {
        "request_id": request_id,
        "startMainSha": None,
        "preWriteMainSha": None,
        "finalMainSha": None,
        "resourceAudit": "not_run",
        "candidateAudit": "not_run",
        "branchAudit": "not_run",
        "changedFields": [],
        "changedFileCount": 0,
        "branchName": branch_name,
        "prNumber": None,
        "prUrl": None,
        "endStatus": "failed",
    }


def _propagate_preflight_failure(result: dict[str, Any], phase2a: dict[str, Any]) -> dict[str, Any]:
    status = phase2a.get("preflightStatus")
    if status in {"stale_context", "stale_base"}:
        result["endStatus"] = status
    else:
        result["endStatus"] = "failed"
    if phase2a.get("error"):
        result["error"] = _safe_error(str(phase2a["error"]))
    return result


def create_snapshot_branch_and_pr(
    *,
    request_id: str,
    repository: str,
    branch_name: str,
    base_sha: str,
    candidate_document: dict[str, Any],
    repo_root: Path = ROOT,
    snapshot_path: Path | None = None,
) -> dict[str, Any]:
    snapshot_path = snapshot_path or (repo_root / SNAPSHOT_REL)
    evidence: dict[str, Any] = {
        "branchAudit": "not_run",
        "changedFields": [],
        "changedFileCount": 0,
        "finalMainSha": None,
        "prNumber": None,
        "prUrl": None,
        "status": "failed",
    }
    branch_created = False
    remote_pushed = False
    try:
        _git(repo_root, "switch", "-c", branch_name, base_sha)
        branch_created = True
        write_snapshot_file(snapshot_path, candidate_document)
        fields = validate_snapshot_only_worktree(
            repo_root,
            base_sha=base_sha,
            snapshot_path=snapshot_path,
        )
        evidence["changedFields"] = fields
        evidence["changedFileCount"] = 1

        strict = candidate.run_canonical_audit(
            snapshot_path,
            require_live_synced=True,
            repo_root=repo_root,
        )
        if strict.get("status") != audit.LIVE_PASS:
            raise PrGateError(
                f"working snapshot strict audit returned {strict.get('status')!r}"
            )

        latest_main = preflight.read_current_main_sha(repo_root, MAIN_BRANCH)
        evidence["finalMainSha"] = latest_main
        if latest_main != base_sha:
            cleanup_local_branch(repo_root, branch_name, base_sha)
            evidence["status"] = "stale_base"
            return evidence

        _git(repo_root, "config", "user.name", "github-actions[bot]")
        _git(
            repo_root,
            "config",
            "user.email",
            "41898282+github-actions[bot]@users.noreply.github.com",
        )
        _git(repo_root, "add", "--", SNAPSHOT_REL.as_posix())
        validate_staged_snapshot_only(repo_root, base_sha=base_sha)
        _git(repo_root, "commit", "-m", f"certify admin editor sync {request_id}")
        validate_committed_snapshot_only(repo_root)

        branch_strict = candidate.run_canonical_audit(
            snapshot_path,
            require_live_synced=True,
            repo_root=repo_root,
        )
        if branch_strict.get("status") != audit.LIVE_PASS:
            cleanup_local_branch(repo_root, branch_name, base_sha)
            raise PrGateError(
                f"committed branch strict audit returned {branch_strict.get('status')!r}"
            )
        evidence["branchAudit"] = audit.LIVE_PASS

        latest_main = preflight.read_current_main_sha(repo_root, MAIN_BRANCH)
        evidence["finalMainSha"] = latest_main
        if latest_main != base_sha:
            cleanup_local_branch(repo_root, branch_name, base_sha)
            evidence["status"] = "stale_base"
            return evidence

        _git(repo_root, "push", "--set-upstream", "origin", f"HEAD:refs/heads/{branch_name}")
        remote_pushed = True
        _git(
            repo_root,
            "fetch",
            "--no-tags",
            "origin",
            f"refs/heads/{branch_name}:refs/remotes/origin/{branch_name}",
        )
        local_sha = _git(repo_root, "rev-parse", "HEAD")
        remote_sha = _git(repo_root, "rev-parse", f"refs/remotes/origin/{branch_name}")
        if local_sha != remote_sha:
            cleanup_remote_branch(repo_root, branch_name)
            raise PrGateError("pushed Admin editor sync branch SHA mismatch")

        existing = find_existing_request_pr(
            repository,
            branch_name,
            repo_root=repo_root,
        )
        if existing:
            evidence["prNumber"] = existing.get("number")
            evidence["prUrl"] = existing.get("url")
            evidence["status"] = "existing_pr"
            return evidence

        try:
            created = create_pull_request(
                repository=repository,
                branch_name=branch_name,
                request_id=request_id,
                base_sha=base_sha,
                repo_root=repo_root,
            )
        except Exception:
            cleanup_remote_branch(repo_root, branch_name)
            raise
        evidence["prNumber"] = created["number"]
        evidence["prUrl"] = created["url"]
        evidence["status"] = "pr_created"
        return evidence
    except candidate.CandidateError as exc:
        if remote_pushed:
            cleanup_remote_branch(repo_root, branch_name)
        if branch_created:
            cleanup_local_branch(repo_root, branch_name, base_sha)
        evidence["error"] = _safe_error(exc)
        evidence["status"] = "failed"
        return evidence
    except Exception as exc:  # noqa: BLE001
        if remote_pushed:
            cleanup_remote_branch(repo_root, branch_name)
        if branch_created:
            cleanup_local_branch(repo_root, branch_name, base_sha)
        evidence["error"] = _safe_error(exc)
        evidence["status"] = "failed"
        return evidence


def run_gate(
    request_id: str,
    approval_phrase: str,
    *,
    repo_root: Path = ROOT,
    snapshot_path: Path | None = None,
) -> dict[str, Any]:
    branch_name: str | None = None
    try:
        branch_name = branch_name_for_request(request_id)
    except PrGateError as exc:
        result = _result_template(request_id)
        result["error"] = _safe_error(exc)
        return result

    result = _result_template(request_id, branch_name)
    if approval_phrase != APPROVAL_PHRASE:
        result["endStatus"] = "approval_required"
        result["error"] = "approval_phrase must exactly equal 'Gut für Main'"
        return result

    snapshot_path = snapshot_path or (repo_root / SNAPSHOT_REL)
    try:
        default_branch = preflight.read_default_branch()
        if default_branch != MAIN_BRANCH:
            raise PrGateError(
                f"default branch must remain {MAIN_BRANCH!r}, got {default_branch!r}"
            )
        repository = read_repository_name()

        phase2a = preflight.run_preflight(
            request_id,
            repo_root=repo_root,
            snapshot_path=snapshot_path,
        )
        result["startMainSha"] = phase2a.get("startMainSha")
        result["resourceAudit"] = phase2a.get("resourceAudit", "not_run")
        result["candidateAudit"] = phase2a.get("candidateAudit", "not_run")
        result["changedFields"] = phase2a.get("changedFields") or []

        phase2a_status = phase2a.get("preflightStatus")
        if phase2a_status == "no_change":
            if result["resourceAudit"] != audit.LIVE_PASS:
                result["error"] = "no_change requires LIVE_PASS on the real snapshot"
                return result
            result["endStatus"] = "no_change"
            return result
        if phase2a_status != "would_certify":
            return _propagate_preflight_failure(result, phase2a)
        if (
            result["resourceAudit"] != audit.TARGET_PASS
            or result["candidateAudit"] != audit.LIVE_PASS
            or set(result["changedFields"]) != candidate.ALLOWED_CERTIFICATION_FIELDS
        ):
            result["error"] = "Phase-2A evidence contract is inconsistent"
            return result

        existing_pr = find_existing_request_pr(
            repository,
            branch_name,
            repo_root=repo_root,
        )
        if existing_pr:
            result["prNumber"] = existing_pr.get("number")
            result["prUrl"] = existing_pr.get("url")
            if existing_pr.get("state") == "OPEN":
                result["endStatus"] = "existing_pr"
            else:
                result["endStatus"] = "existing_request"
            return result
        if remote_branch_exists(repo_root, branch_name):
            result["endStatus"] = "existing_request"
            result["error"] = (
                "deterministic request branch already exists without a matching open PR"
            )
            return result

        base_sha = str(result["startMainSha"] or "")
        if not _MAIN_SHA_RE.fullmatch(base_sha):
            result["error"] = "Phase-2A startMainSha is missing or invalid"
            return result

        rebuilt = candidate.build_candidate(
            repo_root=repo_root,
            snapshot_path=snapshot_path,
            main_sha_reader=lambda _root: base_sha,
        )
        if rebuilt.get("status") != audit.LIVE_PASS:
            result["candidateAudit"] = rebuilt.get("status") or "FAIL"
            if rebuilt.get("status") == "stale_context":
                result["endStatus"] = "stale_context"
            result["error"] = _safe_error(
                str(rebuilt.get("error") or "fresh candidate lost LIVE_PASS")
            )
            return result
        rebuilt_fields = set(rebuilt.get("changedFields", []))
        if rebuilt_fields != candidate.ALLOWED_CERTIFICATION_FIELDS:
            result["candidateAudit"] = "FAIL"
            result["error"] = "fresh candidate changed forbidden snapshot fields"
            return result
        rebuilt_document = rebuilt.get("candidate")
        if not isinstance(rebuilt_document, dict):
            result["candidateAudit"] = "FAIL"
            result["error"] = "fresh candidate document is missing"
            return result
        result["candidateAudit"] = audit.LIVE_PASS
        result["changedFields"] = sorted(rebuilt_fields)

        pre_write_main_sha = preflight.read_current_main_sha(
            repo_root,
            default_branch,
        )
        result["preWriteMainSha"] = pre_write_main_sha
        if pre_write_main_sha != base_sha:
            result["finalMainSha"] = pre_write_main_sha
            result["endStatus"] = "stale_base"
            result["error"] = (
                f"main changed before snapshot write: "
                f"start={base_sha} preWrite={pre_write_main_sha}"
            )
            return result

        write_result = create_snapshot_branch_and_pr(
            request_id=request_id,
            repository=repository,
            branch_name=branch_name,
            base_sha=base_sha,
            candidate_document=rebuilt_document,
            repo_root=repo_root,
            snapshot_path=snapshot_path,
        )
        result["branchAudit"] = write_result.get("branchAudit", "not_run")
        result["changedFields"] = write_result.get("changedFields") or result["changedFields"]
        result["changedFileCount"] = int(write_result.get("changedFileCount") or 0)
        result["finalMainSha"] = write_result.get("finalMainSha")
        result["prNumber"] = write_result.get("prNumber")
        result["prUrl"] = write_result.get("prUrl")
        result["endStatus"] = write_result.get("status") or "failed"
        if write_result.get("error"):
            result["error"] = _safe_error(str(write_result["error"]))
        return result
    except candidate.CandidateError as exc:
        result["endStatus"] = "stale_context"
        result["error"] = _safe_error(exc)
        return result
    except Exception as exc:  # noqa: BLE001
        result["endStatus"] = "failed"
        result["error"] = _safe_error(exc)
        return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request-id", required=True)
    parser.add_argument("--approval-phrase", required=True)
    args = parser.parse_args()
    result = run_gate(args.request_id, args.approval_phrase)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    status = result.get("endStatus")
    if status in SUCCESS_STATES:
        return 0
    if status == "approval_required":
        return 2
    if status == "stale_context":
        return 3
    if status == "stale_base":
        return 4
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
