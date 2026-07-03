#!/usr/bin/env python3
"""Preflight Custom GPT payloads before dispatching the KGG write gate."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "kgg-update" / "index.html"

sys.path.insert(0, str(ROOT / "release-pipeline"))
import kgg_gpt_write_gate as write_gate  # noqa: E402


class PreflightError(RuntimeError):
    pass


UI_KEYWORDS = (
    "ui",
    "layout",
    "tablet",
    "phone",
    "splitter",
    "drag",
    "swipe",
    "flicker",
    "button",
    "menu",
    "html",
)


def fail(message: str) -> None:
    raise PreflightError(message)


def load_payload(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:  # noqa: BLE001 - user-facing CLI error
        fail(f"Cannot read payload JSON {path}: {exc}")


def payload_text(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def declared_tests(payload: dict[str, Any]) -> str:
    fields = [
        payload.get("required_tests"),
        payload.get("requiredTests"),
        payload.get("tests"),
        payload.get("test_plan"),
        payload.get("testPlan"),
    ]
    return " ".join(json.dumps(item, ensure_ascii=False) for item in fields if item is not None).lower()


def looks_like_ui_payload(payload: dict[str, Any]) -> bool:
    text = payload_text(payload).lower()
    return any(word in text for word in UI_KEYWORDS)


def require_ui_tests(payload: dict[str, Any]) -> None:
    if not looks_like_ui_payload(payload):
        return
    tests = declared_tests(payload)
    if "critical" not in tests:
        fail("UI-like payloads must declare the critical test battery.")
    if "ui-stability" not in tests or "regression" not in tests:
        fail("UI-like payloads must declare ui-stability regression.")


def reject_broad_body_append(payload: dict[str, Any]) -> None:
    if payload.get("allow_body_append") is True or payload.get("allowBodyAppend") is True:
        return
    for index, operation in enumerate(payload["operations"]):
        old = operation["old_text"].strip().lower()
        new = operation["new_text"].strip().lower()
        if old in {"</body>", "</body>\n</html>", "</html>"} and ("<script" in new or "<style" in new):
            fail(
                f"operation {index} appends script/style at the document end. "
                "Patch the existing local CSS/JS block unless this is explicitly reviewed."
            )


def check_source_matches(payload: dict[str, Any]) -> None:
    source = SOURCE_PATH.read_text(encoding="utf-8", errors="replace")
    for index, operation in enumerate(payload["operations"]):
        count = source.count(operation["old_text"])
        if count != 1:
            fail(f"operation {index} old_text must match kgg-update/index.html exactly once, found {count}.")


def preflight_payload(payload: dict[str, Any], *, check_source: bool = True) -> dict[str, Any]:
    validated = write_gate.validate_payload(json.dumps(payload, ensure_ascii=False))
    reject_broad_body_append(validated)
    require_ui_tests(validated)
    if check_source:
        check_source_matches(validated)
    return validated


def expect_failure(name: str, payload: dict[str, Any], expected: str) -> None:
    try:
        preflight_payload(payload, check_source=False)
    except Exception as exc:  # noqa: BLE001 - self-test checks message text
        if expected not in str(exc):
            fail(f"self-test {name} failed with unexpected message: {exc}")
        return
    fail(f"self-test {name} unexpectedly passed")


def expect_success(name: str, payload: dict[str, Any]) -> None:
    try:
        preflight_payload(payload, check_source=False)
    except Exception as exc:  # noqa: BLE001 - user-facing CLI error
        fail(f"self-test {name} unexpectedly failed: {exc}")


def self_test() -> None:
    base = {
        "request_id": "gpt-preflight-self-test",
        "title": "Tablet Splitter",
        "summary": "Tablet layout probe",
        "version_slug": "tablet-splitter",
        "required_tests": [
            "cmd /c release-pipeline\\run-kgg-tests.cmd --level critical",
            "cmd /c release-pipeline\\run-kgg-tests.cmd --suite ui-stability --level regression",
        ],
    }
    expect_failure(
        "protected-token-comment",
        {
            **base,
            "operations": [
                {
                    "path": "kgg-update/index.html",
                    "old_text": ".tabletLayoutResizeHandle{display:none}",
                    "new_text": ".tabletLayoutResizeHandle{display:block} /* keine API-Key Aenderung */",
                }
            ],
        },
        "protected area tokens",
    )
    expect_failure(
        "broad-body-append",
        {
            **base,
            "operations": [
                {
                    "path": "kgg-update/index.html",
                    "old_text": "</body>\n</html>",
                    "new_text": "<script>window.KGG_TEST=true;</script>\n</body>\n</html>",
                }
            ],
        },
        "appends script/style",
    )
    expect_failure(
        "operation-file-key",
        {
            **base,
            "operations": [
                {
                    "file": "kgg-update/index.html",
                    "old_text": ".tabletLayoutResizeHandle{display:none}",
                    "new_text": ".tabletLayoutResizeHandle{display:block}",
                }
            ],
        },
        "v1 only allows kgg-update/index.html",
    )
    expect_failure(
        "ui-tests-missing",
        {
            "request_id": "gpt-preflight-no-tests",
            "title": "Tablet Splitter",
            "summary": "Tablet layout probe",
            "version_slug": "tablet-splitter",
            "operations": [
                {
                    "path": "kgg-update/index.html",
                    "old_text": ".tabletLayoutResizeHandle{display:none}",
                    "new_text": ".tabletLayoutResizeHandle{display:block}",
                }
            ],
        },
        "critical",
    )
    expect_success(
        "good-ui-payload",
        {
            **base,
            "operations": [
                {
                    "path": "kgg-update/index.html",
                    "old_text": ".tabletLayoutResizeHandle{display:none}",
                    "new_text": ".tabletLayoutResizeHandle{display:block}",
                }
            ],
        },
    )
    print("KGG GPT payload preflight self-test OK")


def main() -> int:
    parser = argparse.ArgumentParser(description="Preflight KGG Custom GPT payload JSON.")
    parser.add_argument("--payload-file", type=Path, help="Payload JSON file to validate.")
    parser.add_argument("--self-test", action="store_true", help="Run built-in preflight fixtures.")
    args = parser.parse_args()

    try:
        if args.self_test:
            self_test()
            return 0
        if not args.payload_file:
            fail("--payload-file is required unless --self-test is used")
        payload = load_payload(args.payload_file)
        validated = preflight_payload(payload)
        print(f"KGG GPT payload preflight OK: {validated['request_id']}")
        return 0
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
