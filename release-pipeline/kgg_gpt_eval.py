#!/usr/bin/env python3
"""Deterministic checks for the KGG Custom GPT playbook and fixtures."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class EvalError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise EvalError(message)


def read(path: str) -> str:
    full = ROOT / path
    if not full.exists():
        fail(f"missing required GPT eval file: {path}")
    return full.read_text(encoding="utf-8")


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        fail(f"missing {label}: {needle}")


def require_all(text: str, needles: list[str], label: str) -> None:
    for needle in needles:
        require(text, needle, label)


def run_preflight_self_test() -> None:
    proc = subprocess.run(
        [sys.executable, "release-pipeline/kgg_gpt_payload_preflight.py", "--self-test"],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        output = (proc.stdout + "\n" + proc.stderr).strip()
        fail(f"payload preflight self-test failed: {output}")


def run_validate_only_self_test() -> None:
    source_path = ROOT / "kgg-update" / "index.html"
    before = source_path.read_text(encoding="utf-8")
    old_text = "<html"
    if before.count(old_text) != 1:
        fail("validate_only self-test needs exactly one <html marker")
    payload = {
        "request_id": "gpt-validate-only-self-test",
        "title": "Validate only self-test",
        "summary": "Validate-only must not write source files.",
        "version_slug": "validate-only-self-test",
        "required_tests": [
            "cmd /c release-pipeline\\run-kgg-tests.cmd --level critical",
            "cmd /c release-pipeline\\run-kgg-tests.cmd --suite ui-stability --level regression",
        ],
        "operations": [
            {
                "type": "replace_exact",
                "path": "kgg-update/index.html",
                "old_text": old_text,
                "new_text": '<html data-kgg-gpt-validate="1"',
            }
        ],
    }
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".json", delete=False) as handle:
        json.dump(payload, handle, ensure_ascii=False)
        payload_path = Path(handle.name)
    try:
        proc = subprocess.run(
            [
                sys.executable,
                "release-pipeline/kgg_gpt_write_gate.py",
                "--mode",
                "validate_only",
                "--payload-file",
                str(payload_path),
            ],
            cwd=str(ROOT),
            text=True,
            capture_output=True,
        )
    finally:
        payload_path.unlink(missing_ok=True)
    after = source_path.read_text(encoding="utf-8")
    if after != before:
        fail("validate_only self-test modified kgg-update/index.html")
    if proc.returncode != 0:
        output = (proc.stdout + "\n" + proc.stderr).strip()
        fail(f"validate_only self-test failed: {output}")


def check_playbook() -> None:
    playbook = read("docs/kgg-custom-gpt-playbook.md")
    require_all(
        playbook,
        [
            "docs/kgg-gpt-context.md",
            "docs/kgg-custom-gpt-action-schema.md",
            "docs/kgg-custom-gpt-negative-examples.md",
            "docs/kgg-custom-gpt-preview-runbook.md",
            "docs/kgg-custom-gpt-preview-report-template.md",
            "docs/kgg-gpt-bug-lessons.md",
            "docs/kgg-gpt-area-routes.md",
            "Keine Erfolgsmeldung",
            "Guard-Tokens",
            "validate_only",
            "ui_stability=true",
            "tabletLayoutFreeTools",
            "tabletLayoutResizeHandle",
            "--kgg-tablet-left-col",
            "updateTabletLayoutHandle()",
            "initTabletLayoutControls()",
        ],
        "playbook contract",
    )


def check_prompt_and_expected_docs() -> None:
    prompts = read("docs/kgg-custom-gpt-test-prompts.md")
    expected = read("docs/kgg-custom-gpt-expected-results.md")
    report = read("docs/kgg-custom-gpt-test-report.md")
    action_schema = read("docs/kgg-custom-gpt-action-schema.md")
    negative_examples = read("docs/kgg-custom-gpt-negative-examples.md")
    runbook = read("docs/kgg-custom-gpt-preview-runbook.md")
    report_template = read("docs/kgg-custom-gpt-preview-report-template.md")
    cases = [
        "tablet-splitter",
        "failed-preview-run",
        "protected-token-payload",
        "payload-schema-path",
        "preview-apk-icon",
        "beta-html-request",
    ]
    for case in cases:
        require(prompts, f"## {case}", f"prompt fixture {case}")
        require(expected, f"## {case}", f"expected fixture {case}")
        require(report, case, f"report row {case}")
    require_all(
        expected,
        [
            "tabletLayoutFreeTools",
            "tabletLayoutResizeHandle",
            "--kgg-tablet-left-col",
            "Preflight guarded GPT payload",
            "Patch-Kommentaren verboten",
            "path: \"kgg-update/index.html\"",
            "v1 only allows kgg-update/index.html",
            "validate_only",
            "Preview-Profil",
            "publish_preview",
            "meta.json",
        ],
        "expected behavior text",
    )
    require_all(
        action_schema,
        ["validate_only", "publish_preview", "create_pr", "path", "artifact", "meta.json"],
        "action schema text",
    )
    require_all(
        negative_examples,
        ["file", "path", "protected words", "Broken JSON", "Red run plus missing meta"],
        "negative examples text",
    )
    require_all(
        runbook,
        ["dispatch -> run status", "validate_only", "artifact", "meta.json", "html_url"],
        "preview runbook text",
    )
    require_all(
        report_template,
        ["run_id", "conclusion", "failed_step", "meta_url", "html_url", "artifact_name"],
        "preview report template text",
    )
    require_all(report, ["PASS", "FAIL", "PENDING", "run_id", "artifact_name", "html_url"], "report states")


def check_area_routes() -> None:
    route_json = ROOT / "docs" / "kgg-gpt-area-routes.json"
    if not route_json.exists():
        fail("missing docs/kgg-gpt-area-routes.json; run kgg_gpt_source_context.py --write")
    data = json.loads(route_json.read_text(encoding="utf-8"))
    routes = {route["id"]: route for route in data.get("routes", [])}
    for route_id in ["tablet-layout", "phone-layout", "qr-patient", "pdf", "android-apk", "sync", "preview-gate"]:
        if route_id not in routes:
            fail(f"missing area route: {route_id}")
    tablet = routes["tablet-layout"]
    markers = {item["marker"] for item in tablet.get("markers", [])}
    required = {
        "tabletLayoutFreeTools",
        "tabletLayoutResizeHandle",
        "--kgg-tablet-left-col",
        "updateTabletLayoutHandle",
        "initTabletLayoutControls",
    }
    missing = sorted(required - markers)
    if missing:
        fail("tablet-layout route missing markers: " + ", ".join(missing))
    if not tablet.get("sourceChunks"):
        fail("tablet-layout route must resolve source chunks")


def main() -> int:
    try:
        check_playbook()
        check_prompt_and_expected_docs()
        check_area_routes()
        run_preflight_self_test()
        run_validate_only_self_test()
        print("KGG Custom GPT eval OK")
        return 0
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
