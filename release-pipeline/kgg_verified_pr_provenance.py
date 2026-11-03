#!/usr/bin/env python3
"""Strict, offline PR provenance validation for a future generic KGG Preview gate.

This module never publishes, downloads, executes PR code or acquires credentials.
The existing v133-specific publisher stays unchanged. A separate trusted workflow
must verify source checkout, run all test gates, and hold publishing privileges.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Mapping

CONTRACT = "kgg-verified-pr-provenance/v1"
REPO = "Kayus24/kgg"
WORKFLOW_NAME = "Validate and build KGG admin beta"
WORKFLOW_PATH = ".github/workflows/release-pr.yml"
WORKFLOW_ID = 299714308
APPROVAL_LABEL = "kgg-preview-approved"
NO_RELEASE_LABEL = "kgg-no-release"
_SHA_RE = re.compile(r"[0-9a-f]{40}\Z")
_BRANCH_RE = re.compile(r"[A-Za-z0-9._/-]{1,160}\Z")


class ProvenanceError(ValueError):
    """A non-sensitive code identifying failed provenance verification."""


def _require(ok: bool, code: str) -> None:
    if not ok:
        raise ProvenanceError(code)


def _obj(value: Any, name: str) -> Mapping[str, Any]:
    _require(isinstance(value, dict), name + "_not_object")
    return value


def _eq_number(value: Any, expected: int) -> bool:
    return type(value) is int and value == expected


def _branch(value: str) -> bool:
    return isinstance(value, str) and bool(_BRANCH_RE.fullmatch(value)) and not (
        value.startswith("/") or value.endswith("/") or ".." in value or "//" in value
    )


def validate(
    pr: Mapping[str, Any],
    run: Mapping[str, Any],
    *,
    pr_number: int,
    sha: str,
    branch: str,
    base_branch: str,
    run_id: int,
) -> dict[str, Any]:
    """Validate already-fetched GitHub API PR/run JSON against immutable inputs.

    The caller MUST get this data from the authenticated GitHub REST API, not from
    an untrusted PR fixture, and MUST verify source checkout, code diffs, test
    results, permissions, and branch drift again immediately before publishing.
    """
    _require(type(pr_number) is int and pr_number > 0, "pr_number_invalid")
    _require(type(run_id) is int and run_id > 0, "run_id_invalid")
    _require(isinstance(sha, str) and bool(_SHA_RE.fullmatch(sha)), "sha_invalid")
    _require(_branch(branch), "branch_invalid")
    _require(_branch(base_branch), "base_branch_invalid")
    pr = _obj(pr, "pr")
    run = _obj(run, "run")
    _require(_eq_number(pr.get("number"), pr_number), "pr_number_mismatch")
    _require(pr.get("state") == "open" and pr.get("draft") is True, "pr_not_open_draft")
    head = _obj(pr.get("head"), "pr_head")
    base = _obj(pr.get("base"), "pr_base")
    _require(head.get("sha") == sha, "pr_sha_drift")
    _require(head.get("ref") == branch, "pr_branch_drift")
    _require(base.get("ref") == base_branch, "pr_base_drift")
    _require(_obj(head.get("repo"), "head_repo").get("full_name") == REPO, "pr_fork_denied")
    _require(_obj(base.get("repo"), "base_repo").get("full_name") == REPO, "pr_base_repo_invalid")
    _require(pr.get("author_association") in {"OWNER", "MEMBER", "COLLABORATOR"}, "pr_author_untrusted")
    labels = pr.get("labels")
    _require(isinstance(labels, list), "pr_labels_invalid")
    label_names = []
    for label in labels:
        label_names.append(_obj(label, "pr_label").get("name"))
    _require(NO_RELEASE_LABEL in label_names, "no_release_label_missing")
    _require(APPROVAL_LABEL in label_names, "preview_approval_missing")
    _require(_eq_number(run.get("id"), run_id), "run_id_mismatch")
    _require(run.get("status") == "completed" and run.get("conclusion") == "success", "run_not_green")
    _require(run.get("event") == "pull_request", "run_event_invalid")
    _require(run.get("name") == WORKFLOW_NAME, "run_workflow_name_mismatch")
    _require(run.get("path") == WORKFLOW_PATH, "run_workflow_path_mismatch")
    _require(_eq_number(run.get("workflow_id"), WORKFLOW_ID), "run_workflow_id_mismatch")
    _require(run.get("head_sha") == sha, "run_sha_mismatch")
    _require(run.get("head_branch") == branch, "run_branch_mismatch")
    _require(_obj(run.get("repository"), "run_repo").get("full_name") == REPO, "run_repo_mismatch")
    _require(_obj(run.get("head_repository"), "run_head_repo").get("full_name") == REPO, "run_head_repo_mismatch")
    associated_prs = run.get("pull_requests")
    _require(isinstance(associated_prs, list), "run_pr_associations_invalid")
    match = [
        x for x in associated_prs
        if isinstance(x, dict) and _eq_number(x.get("number"), pr_number)
        and isinstance(x.get("head"), dict) and x["head"].get("sha") == sha
    ]
    _require(len(match) == 1, "run_pr_not_bound")
    return {
        "contract": CONTRACT,
        "status": "PASS",
        "repo": REPO,
        "pr": pr_number,
        "sha": sha,
        "branch": branch,
        "baseBranch": base_branch,
        "verificationRunId": run_id,
        "approval": APPROVAL_LABEL,
        "publishingAuthorized": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pr-file", type=Path)
    parser.add_argument("--run-file", type=Path)
    parser.add_argument("--pr-number", type=int)
    parser.add_argument("--sha")
    parser.add_argument("--branch")
    parser.add_argument("--base-branch")
    parser.add_argument("--run-id", type=int)
    args = parser.parse_args()
    if not all((args.pr_file, args.run_file, args.pr_number, args.sha, args.branch, args.base_branch, args.run_id)):
        parser.error("pr-file, run-file, pr-number, sha, branch, base-branch and run-id are required")
    try:
        pr = json.loads(args.pr_file.read_text(encoding="utf-8"))
        run = json.loads(args.run_file.read_text(encoding="utf-8"))
        print(json.dumps(validate(pr, run, pr_number=args.pr_number, sha=args.sha,
                                  branch=args.branch, base_branch=args.base_branch,
                                  run_id=args.run_id), sort_keys=True))
        return 0
    except (OSError, json.JSONDecodeError, ProvenanceError) as error:
        print(json.dumps({"status": "FAIL", "code": str(error) if isinstance(error, ProvenanceError) else "invalid_input"}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
