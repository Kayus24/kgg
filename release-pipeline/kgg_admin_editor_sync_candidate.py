#!/usr/bin/env python3
"""Build and validate a non-persistent Admin editor live-sync candidate."""

from __future__ import annotations

import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Callable


ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "docs" / "kgg-custom-gpt-editor-snapshot.json"
ALLOWED_CERTIFICATION_FIELDS = {
    "syncStatus",
    "lastVerifiedAt",
    "lastVerifiedMainCommit",
}
_MAIN_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class CandidateError(RuntimeError):
    pass


def read_main_sha(repo_root: Path = ROOT) -> str:
    proc = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        check=False,
        capture_output=True,
        text=True,
    )
    sha = proc.stdout.strip()
    if proc.returncode != 0 or not _MAIN_SHA_RE.fullmatch(sha):
        detail = proc.stderr.strip() or "invalid git HEAD"
        raise CandidateError(f"cannot read server-side main SHA: {detail}")
    return sha


def utc_now_rfc3339() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def run_canonical_audit(
    snapshot: Path, *, require_live_synced: bool, repo_root: Path = ROOT
) -> dict:
    command = [
        sys.executable,
        str(repo_root / "release-pipeline" / "kgg_custom_gpt_resource_audit.py"),
        "--check",
        "--editor-snapshot",
        str(snapshot),
        "--profile",
        "production",
    ]
    if require_live_synced:
        command.append("--require-live-synced")
    proc = subprocess.run(
        command,
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip() or "resource audit failed"
        raise CandidateError(detail)
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise CandidateError("resource audit returned invalid JSON") from exc


def changed_top_level_fields(before: dict, after: dict) -> set[str]:
    return {
        key
        for key in before.keys() | after.keys()
        if before.get(key) != after.get(key)
    }


def build_candidate(
    *,
    repo_root: Path = ROOT,
    snapshot_path: Path | None = None,
    main_sha_reader: Callable[[Path], str] = read_main_sha,
    now_reader: Callable[[], str] = utc_now_rfc3339,
    audit_runner: Callable[..., dict] = run_canonical_audit,
) -> dict:
    snapshot_path = snapshot_path or (
        repo_root / "docs" / "kgg-custom-gpt-editor-snapshot.json"
    )
    try:
        preflight = audit_runner(
            snapshot_path,
            require_live_synced=False,
            repo_root=repo_root,
        )
    except CandidateError as exc:
        return {"status": "stale_context", "error": str(exc)}
    if preflight.get("status") != "TARGET_PASS":
        return {
            "status": "stale_context",
            "error": (
                "Admin editor snapshot must be TARGET_PASS, got "
                f"{preflight.get('status')!r}"
            ),
        }

    try:
        base = json.loads(snapshot_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        return {
            "status": "stale_context",
            "error": f"cannot read Admin editor snapshot: {exc}",
        }
    if not isinstance(base, dict):
        return {
            "status": "stale_context",
            "error": "Admin editor snapshot must be a JSON object",
        }

    try:
        main_sha = main_sha_reader(repo_root)
        verified_at = now_reader()
    except CandidateError as exc:
        return {"status": "stale_context", "error": str(exc)}

    candidate = copy.deepcopy(base)
    candidate["syncStatus"] = "live-synced"
    candidate["lastVerifiedAt"] = verified_at
    candidate["lastVerifiedMainCommit"] = main_sha
    changed_fields = changed_top_level_fields(base, candidate)
    if not changed_fields.issubset(ALLOWED_CERTIFICATION_FIELDS):
        raise CandidateError(
            "candidate changed forbidden snapshot fields: "
            + ", ".join(
                sorted(changed_fields - ALLOWED_CERTIFICATION_FIELDS)
            )
        )

    with tempfile.TemporaryDirectory(
        prefix="kgg-admin-editor-sync-candidate-"
    ) as temp_dir:
        candidate_path = Path(temp_dir) / "kgg-custom-gpt-editor-snapshot.json"
        candidate_path.write_text(
            json.dumps(
                candidate,
                ensure_ascii=False,
                indent=2,
                sort_keys=False,
            )
            + "\n",
            encoding="utf-8",
            newline="\n",
        )
        try:
            live_check = audit_runner(
                candidate_path,
                require_live_synced=True,
                repo_root=repo_root,
            )
        except CandidateError as exc:
            return {"status": "candidate_invalid", "error": str(exc)}

    if live_check.get("status") != "LIVE_PASS":
        return {
            "status": "candidate_invalid",
            "error": (
                "strict live audit returned "
                f"{live_check.get('status')!r}"
            ),
        }
    return {
        "status": "LIVE_PASS",
        "mainSha": main_sha,
        "lastVerifiedAt": verified_at,
        "changedFields": sorted(changed_fields),
        "candidate": candidate,
    }


def main() -> int:
    result = build_candidate()
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get("status") == "LIVE_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
