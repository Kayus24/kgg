#!/usr/bin/env python3
"""Preflight modular Custom GPT payloads before dispatching the KGG write gate."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

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

CRITICAL_TEST = "cmd /c release-pipeline\\run-kgg-tests.cmd --level critical"
UI_REGRESSION_TEST = "cmd /c release-pipeline\\run-kgg-tests.cmd --suite ui-stability --level regression"


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
    tests = {str(item).strip().lower() for item in payload.get("required_tests", [])}
    if CRITICAL_TEST.lower() not in tests:
        fail(
            "UI-like modular payloads must declare the critical test battery in required_tests: "
            f"{CRITICAL_TEST}"
        )
    if UI_REGRESSION_TEST.lower() not in tests:
        fail(
            "UI-like modular payloads must declare ui-stability regression in required_tests: "
            f"{UI_REGRESSION_TEST}"
        )


def reject_manual_version_bump(payload: dict[str, Any]) -> None:
    patch_content = str(payload.get("patch_content") or payload.get("patchContent") or "")
    version_tokens = (
        "const VERSION=",
        "const KGG_BUILD_INFO=",
        "id=\"kgg-source-truth\"",
        "id=\"kgg-changelog\"",
        "kgg-update/version.json",
    )
    if any(token in patch_content for token in version_tokens):
        fail("patch_content tries to edit version/build metadata. The modular Preview Gate owns version bumps.")


def preflight_payload(payload: dict[str, Any], *, check_source: bool = True) -> dict[str, Any]:
    reject_manual_version_bump(payload)
    validated = write_gate.validate_payload(json.dumps(payload, ensure_ascii=False))
    require_ui_tests(validated)
    if check_source:
        write_gate.plan_modular_patch(validated)
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


def good_patch_content() -> str:
    return """<style id="__KGG_PATCH_ID__-style">
.kgg-gpt-self-test-marker{display:none}
</style>
<script id="__KGG_PATCH_ID__">
(function(){
  "use strict";
  const PATCH_ID="__KGG_PATCH_ID__";
  window.KGG_PATCHES=window.KGG_PATCHES||{};
  window.KGG_PATCHES[PATCH_ID]={installed:true};
})();
</script>
"""


def self_test() -> None:
    base = {
        "request_id": "gpt-preflight-self-test",
        "title": "Tablet Splitter",
        "summary": "Tablet layout probe",
        "version_slug": "tablet-splitter",
        "touched_areas": ["Tablet-Layout"],
        "required_tests": [
            "cmd /c release-pipeline\\run-kgg-tests.cmd --level critical",
            "cmd /c release-pipeline\\run-kgg-tests.cmd --suite ui-stability --level regression",
        ],
        "patch_content": good_patch_content(),
    }
    expect_failure(
        "protected-token-comment",
        {
            **base,
            "patch_content": good_patch_content() + "\n<!-- keine API-Key Aenderung -->\n",
        },
        "protected area tokens",
    )
    expect_failure(
        "legacy-operations-index-path",
        {
            **{key: value for key, value in base.items() if key != "patch_content"},
            "operations": [
                {
                    "path": "kgg-update/index.html",
                    "old_text": ".tabletLayoutResizeHandle{display:none}",
                    "new_text": ".tabletLayoutResizeHandle{display:block}",
                }
            ],
        },
        "payload v2 rejects operations",
    )
    expect_failure(
        "legacy-file-key",
        {
            **base,
            "file": "kgg-update/index.html",
        },
        "legacy direct-file fields",
    )
    expect_failure(
        "ui-tests-missing",
        {
            **base,
            "required_tests": ["cmd /c echo placeholder"],
        },
        "critical",
    )
    expect_failure(
        "ui-tests-shorthand",
        {
            **base,
            "required_tests": ["critical", "ui-stability regression"],
        },
        CRITICAL_TEST,
    )
    expect_failure(
        "manual-version-bump",
        {
            **base,
            "patch_content": good_patch_content() + "\n<script>const VERSION='KGG_GITHUB_UPDATE_v999_bad';</script>\n",
        },
        "Preview Gate owns version bumps",
    )
    expect_failure(
        "missing-patch-id-placeholder",
        {
            **base,
            "patch_content": good_patch_content().replace("__KGG_PATCH_ID__", "static-id"),
        },
        "__KGG_PATCH_ID__",
    )
    expect_success("good-modular-payload", base)
    print("KGG GPT payload preflight self-test OK")


def main() -> int:
    parser = argparse.ArgumentParser(description="Preflight KGG Custom GPT modular payload JSON.")
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
