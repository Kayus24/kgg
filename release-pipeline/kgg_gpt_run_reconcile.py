#!/usr/bin/env python3
"""Reconcile a bounded workflow dispatch by exact request id and SHA."""

from __future__ import annotations

import argparse
import json
from typing import Any


def _run_id(run: dict[str, Any]) -> int:
    try:
        return int(run.get("id") or 0)
    except (TypeError, ValueError):
        return 0


def run_matches(run: dict[str, Any], request_id: str, base_sha: str = "") -> bool:
    labels = [str(run.get(key) or "") for key in ("display_title", "name", "run_name")]
    direct = str(run.get("request_id") or "") == request_id
    labelled = any(request_id == part.strip() for value in labels for part in value.split("|"))
    if not (direct or labelled):
        return False
    if not _run_id(run):
        return False
    if not base_sha:
        return True
    head_sha = str(run.get("head_sha") or "")
    return bool(head_sha) and head_sha == base_sha


def matching_runs(payload: dict[str, Any], request_id: str, base_sha: str = "") -> list[dict[str, Any]]:
    runs = payload.get("workflow_runs") if isinstance(payload, dict) else []
    if not isinstance(runs, list):
        return []
    return sorted((run for run in runs if isinstance(run, dict) and run_matches(run, request_id, base_sha)), key=_run_id, reverse=True)


def reconcile(dispatch_status: str, payload: dict[str, Any], request_id: str, base_sha: str = "") -> dict[str, Any]:
    matches = matching_runs(payload, request_id, base_sha)
    transport = dispatch_status.casefold() in {"timeout", "http_500", "http_502", "http_503", "network_error"}
    if not matches:
        return {"status": "PENDING_RECONCILIATION" if transport else "NOT_FOUND", "request_id": request_id, "base_sha": base_sha, "reconciled_after_transport_error": False}
    if len(matches) > 1:
        return {"status": "AMBIGUOUS_MATCH", "request_id": request_id, "base_sha": base_sha, "match_count": len(matches), "reconciled_after_transport_error": transport}
    selected = matches[0]
    return {"status": "MATCHED", "request_id": request_id, "base_sha": base_sha, "run_id": _run_id(selected), "run_status": selected.get("status"), "conclusion": selected.get("conclusion"), "reconciled_after_transport_error": transport}


def self_test() -> None:
    sha = "a" * 40
    payload = {"workflow_runs": [{"id": 10, "display_title": "KGG GPT Read-only Validation | audit-035", "head_sha": sha, "status": "completed", "conclusion": "success"}]}
    result = reconcile("http_500", payload, "audit-035", sha)
    assert result["status"] == "MATCHED" and result["run_id"] == 10 and result["reconciled_after_transport_error"] is True
    assert reconcile("timeout", {"workflow_runs": []}, "audit-035", sha)["status"] == "PENDING_RECONCILIATION"
    assert not run_matches({"id": 11, "display_title": "KGG GPT Read-only Validation | audit-035-extra", "head_sha": sha}, "audit-035", sha)
    assert not run_matches({"id": 12, "display_title": "KGG GPT Read-only Validation | prefix-audit-035", "head_sha": sha}, "audit-035", sha)
    assert not run_matches({"id": 13, "display_title": "KGG GPT Read-only Validation | audit-035", "head_sha": "b" * 40}, "audit-035", sha)
    assert not run_matches({"id": 14, "display_title": "KGG GPT Read-only Validation | audit-035"}, "audit-035", sha)
    ambiguous = reconcile(
        "success",
        {"workflow_runs": [
            {"id": 20, "display_title": "KGG GPT Read-only Validation | audit-035", "head_sha": sha},
            {"id": 21, "display_title": "KGG GPT Read-only Validation | audit-035", "head_sha": sha},
        ]},
        "audit-035",
        sha,
    )
    assert ambiguous["status"] == "AMBIGUOUS_MATCH" and ambiguous["match_count"] == 2 and "run_id" not in ambiguous


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if not args.self_test:
        parser.error("--self-test is the only supported CLI mode")
    self_test()
    print(json.dumps({"status": "PASS", "test": "kgg_gpt_run_reconcile"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
