#!/usr/bin/env python3
"""Run and document the KGG Custom GPT stabilization cycle."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "docs" / "kgg-custom-gpt-cycle-report.md"

ERROR_CLASSES: dict[str, str] = {
    "payload_schema": "Invalid payload shape, JSON, operation path or missing required_tests.",
    "preview_gate": "GitHub Preview Gate, run, artifact, meta.json or publish-preview failure.",
    "unsafe_patch": "Protected token, manual versioning, broad append or unsafe patch surface.",
    "ui_logic": "UI behavior mismatch such as splitter/scale overlap or visible artifacts.",
    "false_claim": "The GPT claimed success without verified run/test/artifact evidence.",
    "stale_context": "The GPT used outdated repo context, source chunks or wrong base file.",
    "human_preview_fail": "Max rejected the result in the Test-APK or preview channel.",
}

GPT_PROMPTS = [
    "tablet-splitter",
    "failed-preview-run",
    "protected-token-payload",
    "payload-schema-path",
    "preview-apk-icon",
    "beta-html-request",
    "action-schema-validate-only",
    "missing-required-tests",
    "false-preview-claim",
    "human-preview-fail",
    "stale-context",
    "analysis-no-dispatch",
]

PREVIEW_CHECKS = [
    "validate_only",
    "publish_preview",
    "artifact",
    "meta_json",
    "html_url",
    "test_apk_channel",
    "max_test_apk_acceptance",
]


@dataclass
class CheckResult:
    name: str
    status: str
    error_class: str
    notes: str


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_status(value: str | None) -> str:
    status = str(value or "PENDING").strip().upper()
    if status not in {"PASS", "FAIL", "PENDING", "SKIP"}:
        raise ValueError(f"unknown status: {value}")
    return status


def classify_failure(text: str) -> str:
    lower = text.lower()
    if any(token in lower for token in ["required_tests", "required tests", "payload", "json", "file", "path"]):
        return "payload_schema"
    if any(token in lower for token in ["protected", "guard", "api-key", "version", "body append", "</body>", "</html>"]):
        return "unsafe_patch"
    if any(token in lower for token in ["preview", "artifact", "meta.json", "publish", "validate_only", "github run"]):
        return "preview_gate"
    if any(token in lower for token in ["tablet", "splitter", "scale", "ui-stability", "layout", "artifacte", "artefakt"]):
        return "ui_logic"
    if any(token in lower for token in ["claimed", "behauptet", "success", "green", "gruen", "run_id"]):
        return "false_claim"
    if any(token in lower for token in ["stale", "context", "source chunk", "base file", "version"]):
        return "stale_context"
    return "preview_gate"


def command_label(args: list[str]) -> str:
    return " ".join(args)


def run_command(name: str, args: list[str]) -> CheckResult:
    proc = subprocess.run(args, cwd=str(ROOT), text=True, capture_output=True)
    output = (proc.stdout + "\n" + proc.stderr).strip()
    if proc.returncode == 0:
        return CheckResult(name=name, status="PASS", error_class="", notes="OK")
    details = output.splitlines()[-1] if output else f"exit {proc.returncode}: {command_label(args)}"
    return CheckResult(name=name, status="FAIL", error_class=classify_failure(output), notes=details[:500])


def gpt_suite_command() -> list[str]:
    if os.name == "nt":
        return ["cmd", "/c", "release-pipeline\\run-kgg-tests.cmd", "--suite", "gpt", "--level", "critical"]
    return [sys.executable, "release-pipeline/kgg_test_battery.py", "--suite", "gpt", "--level", "critical"]


def ui_splitter_probe_command() -> list[str]:
    if os.name == "nt":
        npm = os.environ.get("KGG_NPM") or "C:\\Program Files\\nodejs\\npm.cmd"
        return [
            npm,
            "exec",
            "--yes",
            "--package=playwright@1.61.1",
            "--",
            "node",
            "release-pipeline\\kgg_ui_stability_smoke.js",
            "--level",
            "regression",
            "--case",
            "tablet-splitter-scale-drag",
        ]
    return [
        "npm",
        "exec",
        "--yes",
        "--package=playwright@1.61.1",
        "--",
        "node",
        "release-pipeline/kgg_ui_stability_smoke.js",
        "--level",
        "regression",
        "--case",
        "tablet-splitter-scale-drag",
    ]


def local_checks(include_ui_probe: bool) -> list[CheckResult]:
    commands = [
        ("context-check", [sys.executable, "release-pipeline/kgg_gpt_context.py", "--check"]),
        ("bug-knowledge-check", [sys.executable, "release-pipeline/kgg_bug_knowledge.py", "--check"]),
        ("source-context-check", [sys.executable, "release-pipeline/kgg_gpt_source_context.py", "--check"]),
        ("payload-preflight-self-test", [sys.executable, "release-pipeline/kgg_gpt_payload_preflight.py", "--self-test"]),
        ("gpt-eval", [sys.executable, "release-pipeline/kgg_gpt_eval.py"]),
        ("gpt-suite-critical", gpt_suite_command()),
    ]
    if include_ui_probe:
        commands.append(("tablet-splitter-scale-drag-probe", ui_splitter_probe_command()))
    return [run_command(name, args) for name, args in commands]


def load_manual_results(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        raise RuntimeError(f"cannot read manual result JSON {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise RuntimeError("manual result JSON must be an object")
    return data


def manual_records(data: dict[str, Any], key: str, expected_names: list[str], name_field: str) -> list[CheckResult]:
    raw_items = data.get(key)
    by_name: dict[str, dict[str, Any]] = {}
    if isinstance(raw_items, list):
        for item in raw_items:
            if isinstance(item, dict) and item.get(name_field):
                by_name[str(item[name_field])] = item
    records: list[CheckResult] = []
    for name in expected_names:
        item = by_name.get(name)
        if not item:
            records.append(CheckResult(name=name, status="PENDING", error_class="", notes="not tested in this cycle"))
            continue
        status = normalize_status(str(item.get("status", "PENDING")))
        notes = str(item.get("notes") or item.get("error") or "")
        error_class = str(item.get("error_class") or "")
        if status == "FAIL" and error_class not in ERROR_CLASSES:
            error_class = classify_failure(notes or name)
        records.append(CheckResult(name=name, status=status, error_class=error_class, notes=notes[:500] or status))
    return records


def cycle_status(groups: list[list[CheckResult]], green_rounds: int) -> str:
    all_records = [record for group in groups for record in group]
    if any(record.status == "FAIL" for record in all_records):
        return "FAIL"
    if any(record.status == "PENDING" for record in all_records):
        return "PENDING"
    if green_rounds < 2:
        return "PENDING"
    return "PASS"


def result_table(records: list[CheckResult], *, include_error_class: bool = True) -> list[str]:
    if include_error_class:
        lines = ["| Check | Status | Fehlerklasse | Notiz |", "| --- | --- | --- | --- |"]
        for record in records:
            lines.append(f"| `{record.name}` | {record.status} | `{record.error_class}` | {record.notes or '-'} |")
        return lines
    lines = ["| Check | Status | Notiz |", "| --- | --- | --- |"]
    for record in records:
        lines.append(f"| `{record.name}` | {record.status} | {record.notes or '-'} |")
    return lines


def render_report(
    *,
    local: list[CheckResult],
    gpt: list[CheckResult],
    preview: list[CheckResult],
    status: str,
    green_rounds: int,
    include_ui_probe: bool,
) -> str:
    lines = [
        "# KGG Custom GPT Stabilization Cycle Report",
        "",
        f"Generated: {utc_now()}",
        f"Status: {status}",
        f"Confirmed green rounds: {green_rounds} / 2",
        f"Tablet splitter UI probe included: {'yes' if include_ui_probe else 'no'}",
        "",
        "## Fehlerklassen",
        "",
        "| Klasse | Bedeutung |",
        "| --- | --- |",
    ]
    for key, description in ERROR_CLASSES.items():
        lines.append(f"| `{key}` | {description} |")
    lines.extend(["", "## Lokale Checks", "", *result_table(local)])
    lines.extend(["", "## Echter Custom-GPT-Test", "", *result_table(gpt)])
    lines.extend(["", "## Preview/Test-APK-Gate", "", *result_table(preview)])
    lines.extend(
        [
            "",
            "## Akzeptanz",
            "",
            "- PASS erst nach zwei kompletten gruenen Runden.",
            "- `validate_only` muss vor `publish_preview` gruen sein.",
            "- Test-APK/Preview-Kanal muss aktualisiert und von Max akzeptiert sein.",
            "- Jeder FAIL wird als Regression aufgenommen, bevor der gleiche Prompt erneut getestet wird.",
            "",
        ]
    )
    return "\n".join(lines)


def self_test() -> None:
    required = {
        "payload_schema",
        "preview_gate",
        "unsafe_patch",
        "ui_logic",
        "false_claim",
        "stale_context",
        "human_preview_fail",
    }
    missing = sorted(required - set(ERROR_CLASSES))
    if missing:
        raise RuntimeError("missing error classes: " + ", ".join(missing))
    prompts = (ROOT / "docs" / "kgg-custom-gpt-test-prompts.md").read_text(encoding="utf-8")
    expected = (ROOT / "docs" / "kgg-custom-gpt-expected-results.md").read_text(encoding="utf-8")
    playbook = (ROOT / "docs" / "kgg-custom-gpt-playbook.md").read_text(encoding="utf-8")
    for prompt in GPT_PROMPTS:
        if f"## {prompt}" not in prompts:
            raise RuntimeError(f"missing GPT prompt fixture: {prompt}")
        if f"## {prompt}" not in expected:
            raise RuntimeError(f"missing expected result fixture: {prompt}")
    for token in ["kgg_gpt_stabilize.py", "human_preview_fail", "Test-APK", "zwei kompletten gruenen Runden"]:
        if token not in playbook:
            raise RuntimeError(f"playbook missing stabilization token: {token}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run KGG Custom GPT stabilization checks.")
    parser.add_argument("--manual-results", type=Path, help="JSON with real GPT/Test-APK results.")
    parser.add_argument("--write-report", action="store_true", help="Write docs/kgg-custom-gpt-cycle-report.md.")
    parser.add_argument("--strict", action="store_true", help="Fail if any GPT/Preview check is pending.")
    parser.add_argument("--include-ui-probe", action="store_true", help="Also run the targeted tablet splitter browser probe.")
    parser.add_argument("--self-test", action="store_true", help="Check stabilization fixtures without running commands.")
    args = parser.parse_args()

    try:
        if args.self_test:
            self_test()
            print("KGG Custom GPT stabilize self-test OK")
            return 0
        manual = load_manual_results(args.manual_results)
        local = local_checks(args.include_ui_probe)
        gpt = manual_records(manual, "gpt_results", GPT_PROMPTS, "prompt")
        preview = manual_records(manual, "preview_results", PREVIEW_CHECKS, "check")
        green_rounds = int(manual.get("green_rounds_confirmed") or 0)
        status = cycle_status([local, gpt, preview], green_rounds)
        report = render_report(
            local=local,
            gpt=gpt,
            preview=preview,
            status=status,
            green_rounds=green_rounds,
            include_ui_probe=args.include_ui_probe,
        )
        if args.write_report:
            REPORT_PATH.write_text(report, encoding="utf-8", newline="\n")
            print(f"Wrote {REPORT_PATH.relative_to(ROOT)}")
        else:
            print(report)
        if status == "FAIL" or (args.strict and status != "PASS"):
            return 1
        return 0
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
