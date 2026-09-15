#!/usr/bin/env python3
"""Write the bounded, non-sensitive result artifact for read-only validation."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

RESULT_SCHEMA = 1
FAILURE_MESSAGES = {
    "ci_tooling": "The validation tooling did not complete successfully.",
    "browser_runtime": "The isolated browser probe did not complete successfully.",
    "ui_logic": "The candidate UI did not satisfy the required behavior.",
    "source_drift": "The checked-out source was not the expected canonical revision.",
    "permission": "The requested operation was not permitted by the guarded workflow.",
    "unknown": "The guarded workflow failed without a safe public classification.",
}


def classify_failure(step: str, detail: str = "") -> str:
    text = f"{step} {detail}".casefold()
    if any(token in text for token in ("npm", "node", "playwright", "setup-")):
        return "ci_tooling"
    if any(token in text for token in ("source", "sha", "revision")):
        return "source_drift"
    if any(token in text for token in ("permission", "forbidden", "403", "access denied")):
        return "permission"
    if any(token in text for token in ("browser", "chromium", "selector", "page")):
        return "browser_runtime"
    if any(token in text for token in ("ui", "layout", "assertion")):
        return "ui_logic"
    return "unknown"


def build_result(
    *,
    request_id: str,
    mode: str,
    base_sha: str,
    run_id: str,
    run_attempt: str,
    status: str,
    error_class: str = "",
    repository_write_detected: bool = False,
    reconciled_after_transport_error: bool = False,
) -> dict[str, object]:
    status = status.casefold()
    if status not in {"success", "failure", "cancelled", "unknown"}:
        status = "unknown"
    if status == "success":
        error_class = ""
    elif error_class not in FAILURE_MESSAGES:
        error_class = "unknown"
    return {
        "schema": RESULT_SCHEMA,
        "request_id": request_id,
        "mode": mode,
        "base_sha": base_sha,
        "run_id": str(run_id),
        "run_attempt": str(run_attempt),
        "status": status,
        "error_class": error_class,
        "safe_message": "Guarded Custom GPT workflow completed successfully." if status == "success" else FAILURE_MESSAGES[error_class],
        "repository_write_detected": bool(repository_write_detected),
        "reconciled_after_transport_error": bool(reconciled_after_transport_error),
    }


def _env_status() -> tuple[str, str]:
    requested = os.environ.get("KGG_RESULT_STATUS", os.environ.get("JOB_STATUS", "unknown")).casefold()
    if requested == "success":
        return "success", ""
    if requested == "cancelled":
        return "cancelled", "unknown"
    for step, outcome in (
        ("source", os.environ.get("SOURCE_OUTCOME", "")),
        ("tooling", os.environ.get("TOOLING_OUTCOME", "")),
        ("validation", os.environ.get("VALIDATION_OUTCOME", "")),
    ):
        if outcome.casefold() == "failure":
            if step == "tooling":
                return "failure", os.environ.get("TOOLING_ERROR_CLASS", "ci_tooling")
            if step == "validation":
                return "failure", os.environ.get("VALIDATION_ERROR_CLASS", "ui_logic")
            return "failure", "source_drift"
    return "unknown", "unknown"


def write_from_environment(path: Path) -> dict[str, object]:
    status, error_class = _env_status()
    result = build_result(
        request_id=os.environ.get("KGG_REQUEST_ID", ""),
        mode=os.environ.get("KGG_MODE", "unknown"),
        base_sha=os.environ.get("GITHUB_SHA", ""),
        run_id=os.environ.get("GITHUB_RUN_ID", ""),
        run_attempt=os.environ.get("GITHUB_RUN_ATTEMPT", ""),
        status=status,
        error_class=error_class,
        repository_write_detected=os.environ.get("REPOSITORY_WRITE_DETECTED", "false").casefold() == "true",
        reconciled_after_transport_error=os.environ.get("RECONCILED_AFTER_TRANSPORT_ERROR", "false").casefold() == "true",
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return result


def self_test() -> None:
    result = build_result(request_id="result-self-test", mode="validate_only", base_sha="a" * 40, run_id="1", run_attempt="1", status="failure", error_class="ui_logic")
    assert result["safe_message"] == FAILURE_MESSAGES["ui_logic"]
    assert classify_failure("tooling", "npm missing") == "ci_tooling"
    assert classify_failure("source", "SHA mismatch") == "source_drift"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write", type=Path)
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print(json.dumps({"status": "PASS", "test": "kgg_gpt_result"}))
        return 0
    if not args.write:
        parser.error("--write is required unless --self-test is used")
    print(json.dumps(write_from_environment(args.write.resolve()), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
