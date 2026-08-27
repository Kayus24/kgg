#!/usr/bin/env python3
"""Deterministic checks for the KGG Custom GPT playbook and fixtures."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "release-pipeline"))
import kgg_gpt_write_gate as write_gate  # noqa: E402


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


def run_stabilize_self_test() -> None:
    proc = subprocess.run(
        [sys.executable, "release-pipeline/kgg_gpt_stabilize.py", "--self-test"],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        output = (proc.stdout + "\n" + proc.stderr).strip()
        fail(f"stabilize self-test failed: {output}")


def run_preview_status_self_test() -> None:
    proc = subprocess.run(
        [sys.executable, "release-pipeline/kgg_preview_status.py", "--self-test"],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        output = (proc.stdout + "\n" + proc.stderr).strip()
        fail(f"Preview status self-test failed: {output}")


def run_mock_eval_self_test() -> None:
    proc = subprocess.run(
        [sys.executable, "release-pipeline/kgg_gpt_mock_eval.py", "--self-test"],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        output = (proc.stdout + "\n" + proc.stderr).strip()
        fail(f"mock eval self-test failed: {output}")


def run_brain_relay_worker_self_test() -> None:
    proc = subprocess.run(
        [sys.executable, "release-pipeline/kgg_brain_relay_worker.py", "--self-test"],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        output = (proc.stdout + "\n" + proc.stderr).strip()
        fail(f"Brain-Relay-Worker self-test failed: {output}")


def run_repair_lab_self_tests() -> None:
    commands = [
        [sys.executable, "release-pipeline/kgg_gpt_repair_lab.py", "--self-test"],
        [sys.executable, "release-pipeline/kgg_gpt_repair_stabilize.py", "--self-test"],
        [sys.executable, "release-pipeline/kgg_custom_gpt_resource_audit.py", "--self-test"],
    ]
    for command in commands:
        proc = subprocess.run(command, cwd=str(ROOT), text=True, capture_output=True)
        if proc.returncode != 0:
            output = (proc.stdout + "\n" + proc.stderr).strip()
            fail(f"Repair-Lab self-test failed ({' '.join(command)}): {output}")


def run_validate_only_self_test() -> None:
    tracked = subprocess.run(
        ["git", "ls-files", "kgg-update", "docs", "release-pipeline"],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        check=True,
    ).stdout.splitlines()
    before = {path: (ROOT / path).read_bytes() for path in tracked if (ROOT / path).exists()}
    payload = {
        "request_id": "gpt-validate-only-self-test",
        "title": "Validate only self-test",
        "summary": "Validate-only must not write source files.",
        "version_slug": "validate-only-self-test",
        "touched_areas": ["Admin-Web UI"],
        "required_tests": [
            "cmd /c release-pipeline\\run-kgg-tests.cmd --level critical",
            "cmd /c release-pipeline\\run-kgg-tests.cmd --suite ui-stability --level regression",
        ],
        "patch_content": (
            "<style id=\"__KGG_PATCH_ID__-style\">\n"
            ".kgg-validate-only-self-test{display:none}\n"
            "</style>\n"
            "<script id=\"__KGG_PATCH_ID__\">\n"
            "(function(){\"use strict\";const PATCH_ID=\"__KGG_PATCH_ID__\";"
            "window.KGG_PATCHES=window.KGG_PATCHES||{};window.KGG_PATCHES[PATCH_ID]={installed:true};})();\n"
            "</script>\n"
        ),
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
    after = {path: (ROOT / path).read_bytes() for path in tracked if (ROOT / path).exists()}
    if after != before:
        fail("validate_only self-test modified tracked files")
    if proc.returncode != 0:
        output = (proc.stdout + "\n" + proc.stderr).strip()
        fail(f"validate_only self-test failed: {output}")


def run_main_approval_self_test() -> None:
    payload = {
        "request_id": "gpt-main-approval-self-test",
        "title": "Main approval self test",
        "summary": "PR and Main modes must require Max's exact final approval phrase.",
        "version_slug": "main-approval-self-test",
        "protected_scope": "none",
        "touched_areas": ["Admin-Web UI"],
        "required_tests": [
            "cmd /c release-pipeline\\run-kgg-tests.cmd --level critical",
            "cmd /c release-pipeline\\run-kgg-tests.cmd --suite ui-stability --level regression",
        ],
        "patch_content": (
            '<style id="__KGG_PATCH_ID__-style">.kgg-main-approval-self-test{display:none}</style>\n'
            '<script id="__KGG_PATCH_ID__">(function(){"use strict";const PATCH_ID="__KGG_PATCH_ID__";'
            'window.KGG_PATCHES=window.KGG_PATCHES||{};window.KGG_PATCHES[PATCH_ID]={installed:true};})();</script>\n'
        ),
    }
    validated = write_gate.validate_payload(json.dumps(payload, ensure_ascii=False))
    try:
        write_gate.run(validated, "create_pr", None, None)
    except write_gate.GateError as exc:
        require(str(exc), "Gut für Main", "exact Main approval gate")
    else:
        fail("create_pr was accepted without Max's exact approval phrase")


def run_preview_banner_self_test() -> None:
    payload = {
        "request_id": "preview-banner-self-test",
        "title": "Preview marker self-test",
        "summary": "The marker must identify the loaded Preview without entering the app layout.",
    }
    legacy = (
        '<!doctype html><html><body style="display:flex">'
        '<div id="kgg-gpt-preview-banner" style="position:sticky">KGG PREVIEW | old full-width banner</div>'
        '<button id="menu">Menu</button></body></html>'
    )
    digest = "a" * 64
    rendered = write_gate.inject_preview_banner(legacy, payload, digest)
    require_all(
        rendered,
        [
            write_gate.PREVIEW_MARKER_START,
            write_gate.PREVIEW_MARKER_END,
            'id="kgg-gpt-preview-banner"',
            'data-kgg-preview-marker="compact-v2"',
            "position:fixed!important",
            "pointer-events:none!important",
            "width:92px!important",
            "height:24px!important",
            'id="kgg-gpt-preview-toggle"',
            "TEST &middot; aaaa",
            'id="kgg-gpt-preview-details"',
            "preview-banner-self-test",
            digest,
        ],
        "compact identifiable Preview marker",
    )
    if "position:sticky" in rendered or "old full-width banner" in rendered:
        fail("legacy Preview banner must be replaced, not preserved")
    if rendered.count('id="kgg-gpt-preview-banner"') != 1:
        fail("Preview marker must be injected exactly once")
    visible = re.search(r'id="kgg-gpt-preview-toggle"[^>]*>([^<]*)</button>', rendered)
    if visible is None or visible.group(1) != "TEST &middot; aaaa":
        fail("collapsed Preview marker must contain only the compact identifier")

    replaced = write_gate.inject_preview_banner(rendered, payload, "b" * 64)
    if replaced.count('id="kgg-gpt-preview-banner"') != 1:
        fail("reinjection must replace the owned Preview marker without duplication")
    if digest in replaced or "TEST &middot; aaaa" in replaced or "position:sticky" in replaced:
        fail("reinjection left stale Preview identity or legacy layout CSS")
    require_all(replaced, ["TEST &middot; bbbb", "b" * 64], "refreshed Preview identity")

    try:
        write_gate.inject_preview_banner("<html><div>missing body</div></html>", payload, digest)
    except write_gate.GateError:
        pass
    else:
        fail("Preview marker injection must reject HTML without a body")


def run_modular_rollback_self_test() -> None:
    payload = {
        "request_id": "gpt-rollback-self-test",
        "title": "Rollback self-test",
        "summary": "Rollback must restore modular files if apply fails.",
        "version_slug": "rollback-self-test",
        "touched_areas": ["Admin-Web UI"],
        "required_tests": [
            "cmd /c release-pipeline\\run-kgg-tests.cmd --level critical",
            "cmd /c release-pipeline\\run-kgg-tests.cmd --suite ui-stability --level regression",
        ],
        "patch_content": (
            "<style id=\"__KGG_PATCH_ID__-style\">\n"
            ".kgg-rollback-self-test{display:none}\n"
            "</style>\n"
            "<script id=\"__KGG_PATCH_ID__\">\n"
            "(function(){\"use strict\";const PATCH_ID=\"__KGG_PATCH_ID__\";"
            "window.KGG_PATCHES=window.KGG_PATCHES||{};window.KGG_PATCHES[PATCH_ID]={installed:true};})();\n"
            "</script>\n"
        ),
    }
    validated = write_gate.validate_payload(json.dumps(payload, ensure_ascii=False))
    planned, _report = write_gate.plan_modular_patch(validated)
    originals = {path: path.read_bytes() if path.exists() else None for path in planned}
    planned[ROOT / "kgg-update" / "index.html"] = b"broken generated html\n"
    try:
        write_gate.apply_planned(planned)
    except Exception:
        pass
    else:
        fail("rollback self-test unexpectedly applied a broken modular patch")
    for path, raw in originals.items():
        if raw is None:
            if path.exists():
                fail(f"rollback self-test left new file behind: {path.relative_to(ROOT)}")
        elif not path.exists() or path.read_bytes() != raw:
            fail(f"rollback self-test did not restore {path.relative_to(ROOT)}")


def check_playbook() -> None:
    playbook = read("docs/kgg-custom-gpt-playbook.md")
    require_all(
        playbook,
        [
            "docs/kgg-gpt-context.md",
            "docs/kgg-custom-gpt-action-schema.md",
            "docs/kgg-gpt-bug-lessons.md",
            "docs/kgg-gpt-area-routes.md",
            "Keine Erfolgsmeldung",
            "Guard-Tokens",
            "validate_only",
            "patch_content",
            "kgg-update/src/patches",
            "kgg-update/index.html",
            "generated output",
            "human_preview_fail",
            "submitKggPreviewAuto",
            "Test-APK",
            "ci_tooling",
            "publish_admin_beta",
            "tabletLayoutFreeTools",
            "tabletLayoutResizeHandle",
            "--kgg-tablet-left-col",
            "updateTabletLayoutHandle()",
            "initTabletLayoutControls()",
            "getKggMemoryIndex",
            "getKggMemoryPack",
            "pack_name",
            "workflow.md",
            "nie `memory/packs/...`",
            "submitKggMemoryUpdate",
            "needs_approval",
            "supersedes",
            "Kayus24/kgg-project-memory",
            "zeitlimitierten Antwort",
            "Vorheriger sichtbarer Zustand/Run-ID",
            "Reaktivierungsaktion",
            "aendern niemals Regeln automatisch",
        ],
        "playbook contract",
    )


def check_workflow_obstacle_lesson() -> None:
    lesson = read("docs/bug-debug/2026-08-13-custom-gpt-answer-turn-editor-drift.md")
    require_all(
        lesson,
        [
            "Zeit",
            "GPT",
            "Auftrag/Ziel",
            "Vorheriger sichtbarer Zustand/Run-ID",
            "Beleg",
            "Auswirkung",
            "Reaktivierungsaktion",
            "Ergebnis",
            "Folgeaktion",
            "empty_response",
            "aborted_response",
            "answer_timeout",
            "keine Regel automatisch",
            "Feature-PR mergen",
            "separaten Commit/PR",
            "alten Live-Sync in einem Ressourcen-Aenderungsbranch",
            "Antwort stoppen",
            "model_ui_ambiguous",
            "Editor-Auswahl und das Action-Verhalten",
        ],
        "Custom-GPT workflow-obstacle lesson",
    )
    index = json.loads(read("docs/kgg-gpt-bug-index.json"))
    records = index.get("records")
    if not isinstance(records, list):
        fail("Custom-GPT bug index must expose records")
    workflow_records = [
        record
        for record in records
        if isinstance(record, dict)
        and record.get("source_path")
        == "docs/bug-debug/2026-08-13-custom-gpt-answer-turn-editor-drift.md"
    ]
    if len(workflow_records) != 1:
        fail("workflow-obstacle lesson must have exactly one indexed incident record")
    if any(
        isinstance(record, dict)
        and record.get("title")
        == "Custom-GPT-Workflow-Hindernis (gleicher Bug-Debug-Log, kein zweites System)"
        for record in records
    ):
        fail("README workflow guidance must not duplicate the dated workflow incident")
    sources = index.get("sources")
    if not isinstance(sources, list) or "docs/bug-debug/README.md" not in sources:
        fail("Bug-Debug README must remain discoverable as routing guidance")


def check_prompt_and_expected_docs() -> None:
    prompts = read("docs/kgg-custom-gpt-test-prompts.md")
    expected = read("docs/kgg-custom-gpt-expected-results.md")
    report = read("docs/kgg-custom-gpt-test-report.md")
    action_schema = read("docs/kgg-custom-gpt-action-schema.md")
    brain_relay_workflow = read("docs/kgg-brain-relay-worker-workflow.md")
    negative_examples = read("docs/kgg-custom-gpt-negative-examples.md")
    runbook = read("docs/kgg-custom-gpt-preview-runbook.md")
    report_template = read("docs/kgg-custom-gpt-preview-report-template.md")
    knowledge_pack = read("docs/kgg-custom-gpt-knowledge-pack.md")
    openapi_schema = read("docs/kgg-custom-gpt-action-openapi.yaml")
    api_openapi_schema = read("docs/kgg-custom-gpt-action-api-openapi.yaml")
    patient_openapi_schema = read("docs/kgg-patient-custom-gpt-action-openapi.yaml")
    admin_chunk_pattern = 'pattern: "^chunk-([0-9]{3}|v2-[0-9a-f]{16})\\\\.md$"'
    patient_chunk_pattern = 'pattern: "^chunk-[0-9]{3}\\\\.md$"'
    cases = [
        "tablet-splitter",
        "failed-preview-run",
        "protected-token-payload",
        "payload-schema-path",
        "modular-payload",
        "mockup-restore",
        "preview-apk-icon",
        "beta-html-request",
        "action-schema-validate-only",
        "missing-required-tests",
        "false-preview-claim",
        "preview-run-autopoll",
        "human-preview-fail",
        "stale-context",
        "analysis-no-dispatch",
        "ci-tooling-pdftoppm",
        "admin-beta-push-gate",
        "memory-safe-auto-update",
        "memory-conflict-needs-approval",
        "cross-app-camera-qr",
        "preview-autonomy",
        "main-approval-phrase",
        "agent-coordination",
        "patient-camera-visual-404",
        "manifest-bootstrap-version",
        "patient-camera-interface-404",
        "patient-preview-literal-urls",
        "brain-relay-routing",
        "brain-relay-capsule",
        "brain-relay-rotation",
        "brain-relay-browser-fallback",
        "brain-relay-ticket-master",
        "brain-relay-sol-guard",
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
            "patch_content",
            "kgg-update/src/patches/vNNN-<slug>.html",
            "__KGG_PATCH_ID__",
            "kgg_gpt_mock_eval.py",
            "mockup-restore",
            "`json`-Codeblock",
            "vollstaendigen `critical`- und `ui-stability regression`-Kommandos",
            "validate_only",
            "Preview-Profil",
            "publish_preview",
            "publish_admin_beta",
            "payload_schema",
            "ci_tooling",
            "false_claim",
            "human_preview_fail",
            "stale_context",
            "poppler-utils",
            "submitKggPreviewAuto",
            "meta.json",
            "listKggPreviewAutoRuns",
            "getKggMemoryIndex",
            "getKggMemoryPack",
            "getKggMemoryUpdateStatus",
            "needs_approval",
            "supersedes",
            "cross-app-qr-preview",
            "camera-qr",
            "patient-scan",
            "Gut für Main",
            "submitKggAgentCoordinationEvent",
            "coordination_unavailable",
            "object-fit: cover",
            "patient-start-scan.js",
            "patient-camera",
            "Preview-URL: https://...",
            "Recovery-URL: https://...",
            "coordination-v2",
            "Generation",
            "meaningful events",
            "Neuer Chat",
            "RETIRED",
            "SLEEPING",
            "NEEDS_SOL",
            "private-memory-gate",
            "technical enforcement",
            "policy-only",
            "proxy",
        ],
        "expected behavior text",
    )
    require_all(
        brain_relay_workflow,
        [
            "Luna Manager",
            "Lead-GPT",
            "Luna Relay",
            "Luna-Max-Worker",
            "CI und menschliche Abnahme",
            "hoechstens vier",
            "drei Luna-Max-Worker",
            "meaningful events",
            "30 Minuten",
            "Neuer Chat",
            "RETIRED",
            "Ticket Master",
            "SLEEPING",
            "L0-L3",
            "technisches Enforcement",
            "Policy-only",
            "Proxy",
            "Abschluss- und Blockerbericht",
        ],
        "Brain-Relay-Worker workflow",
    )
    require_all(
        action_schema,
        [
            "validate_only",
            "publish_preview",
            "create_pr",
            "publish_admin_beta",
            "patch_content",
            "touched_areas",
            "__KGG_PATCH_ID__",
            "artifact",
            "meta.json",
            "listKggPreviewAutoRuns",
            "gpt-preview/status/latest.json",
            "Test-APK",
            "Max accepts the Test-APK",
            "Admin beta",
            "api.github.com",
            "raw.githubusercontent.com",
            "duplicate action domains",
            "KGG Project Memory Gate",
            "getKggMemoryIndex",
            "getKggMemoryPack",
            "submitKggMemoryUpdate",
            "needs_approval",
            "supersedes",
            "cross-app-qr-preview",
            "submitKggMainGate",
            "Gut für Main",
            "submitKggPatientPreviewFromAdmin",
            "getKggAgentCoordinationIndex",
            "getKggAgentCoordinationTask",
            "getKggAgentCoordinationHandoff",
            "getKggAgentCricketEvent",
        ],
        "action schema text",
    )
    require_all(
        openapi_schema,
        [
            "version: 1.6.0",
            "getKggCustomGptResourceManifest",
            "getKggProjectContext",
            "getKggSourceIndex",
            "getKggSourceChunk",
            "getKggPatientContextForAdmin",
            "getKggPatientSourceIndexForAdmin",
            "getKggPatientSourceChunkForAdmin",
            "getKggPatientPreviewIndexForAdmin",
            "getKggBrainRelayWorkerWorkflow",
            admin_chunk_pattern,
            patient_chunk_pattern,
        ],
        "custom GPT OpenAPI schema",
    )
    require(
        patient_openapi_schema,
        patient_chunk_pattern,
        "patient source chunk pattern",
    )
    if openapi_schema.count(admin_chunk_pattern) != 1:
        fail("Admin raw action must expose the v1/v2 union for exactly one Admin endpoint")
    if openapi_schema.count(patient_chunk_pattern) != 1:
        fail("Admin raw action must keep its Patient endpoint on numeric v1 chunks")
    if "v2-" in patient_openapi_schema:
        fail("patient source action must remain on numeric v1 chunk names")

    admin_chunk_name = re.compile(r"^chunk-([0-9]{3}|v2-[0-9a-f]{16})\.md$")
    patient_chunk_name = re.compile(r"^chunk-[0-9]{3}\.md$")
    for name in ["chunk-000.md", "chunk-v2-0123456789abcdef.md"]:
        if admin_chunk_name.fullmatch(name) is None:
            fail(f"Admin source action rejected supported chunk name: {name}")
    for name in ["chunk-v2-0123456789abcde.md", "chunk-v2-0123456789ABCDEf.md", "../chunk-000.md"]:
        if admin_chunk_name.fullmatch(name) is not None:
            fail(f"Admin source action accepted invalid chunk name: {name}")
    if patient_chunk_name.fullmatch("chunk-000.md") is None:
        fail("patient source action rejected numeric v1 chunk name")
    if patient_chunk_name.fullmatch("chunk-v2-0123456789abcdef.md") is not None:
        fail("patient source action accepted an Admin-only v2 chunk name")
    require_all(
        api_openapi_schema,
        [
            "submitKggPreviewAuto",
            "submitKggMainGate",
            "validate_only",
            "publish_preview",
            "create_pr",
            "publish_admin_beta",
            "listKggPreviewAutoRuns",
            "getKggPreviewGateRun",
            "getKggPreviewGateJobs",
            "getKggPreviewGateArtifacts",
            "required_tests",
            "patch_content",
            "schemas: {}",
            "properties:",
            "getKggMemoryIndex",
            "getKggMemoryPack",
            "Basename from memory/index.json",
            "Never include memory/packs/",
            "getKggMemoryRecord",
            "getKggMemoryHistory",
            "submitKggMemoryUpdate",
            "listKggMemoryUpdateRuns",
            "getKggMemoryUpdateRun",
            "getKggMemoryUpdateStatus",
            "getKggMemoryUpdateArtifacts",
            "submitKggPatientPreviewFromAdmin",
            "getKggAgentCoordinationIndex",
            "getKggAgentCoordinationThread",
            "submitKggAgentCoordinationEvent",
            "listKggAgentCoordinationRuns",
            "getKggAgentCoordinationTask",
            "getKggAgentCoordinationHandoff",
            "getKggAgentCricketEvent",
            "Gut für Main",
        ],
        "custom GPT API-only OpenAPI schema",
    )
    require_all(
        negative_examples,
        ["operations", "path", "patch_content", "API-Key", "Roter Run", "Manuelle Versionierung", "Test-App"],
        "negative examples text",
    )
    require_all(
        runbook,
        ["single auto dispatch", "validate_only", "status/latest.json", "artifact", "meta.json", "html_url", "Max acceptance", "Admin beta merge", "ci_tooling"],
        "preview runbook text",
    )
    preview_workflow = read(".github/workflows/kgg-gpt-preview-auto.yml")
    require_all(
        preview_workflow,
        [
            "status-validating",
            "pull-requests: write",
            "mode: validate_only",
            "status-publishing",
            "mode: publish_preview",
            "status-final",
            "kgg_preview_status.py",
            "KGG Preview Status",
        ],
        "automatic Preview workflow",
    )
    require_all(
        report_template,
        [
            "run_id",
            "conclusion",
            "failed_step",
            "meta_url",
            "html_url",
            "patch_file",
            "artifact_name",
            "test_apk_channel",
            "max_acceptance",
            "admin_beta_pr",
            "admin_beta_merge",
            "admin_html_url",
            "visible_scaler_canary",
        ],
        "preview report template text",
    )
    cycle_report = read("docs/kgg-custom-gpt-cycle-report.md")
    require_all(report, ["PASS", "FAIL", "PENDING", "run_id", "artifact_name", "html_url", "docs/kgg-custom-gpt-cycle-report.md"], "report states")
    require_all(
        cycle_report,
        [
            "payload_schema",
            "preview_gate",
            "ci_tooling",
            "unsafe_patch",
            "ui_logic",
            "false_claim",
            "stale_context",
            "human_preview_fail",
            "Confirmed green rounds",
        ],
        "cycle report states",
    )
    require_all(
        knowledge_pack,
        [
            "KGG Custom GPT Knowledge Pack",
            "docs/kgg-custom-gpt-playbook.md",
            "docs/kgg-brain-relay-worker-workflow.md",
            "docs/kgg-custom-gpt-preview-runbook.md",
            "ci_tooling",
            "publish_admin_beta",
        ],
        "knowledge pack text",
    )


def check_area_routes() -> None:
    route_json = ROOT / "docs" / "kgg-gpt-area-routes.json"
    source_index_json = ROOT / "docs" / "kgg-gpt-source-index.json"
    if not route_json.exists():
        fail("missing docs/kgg-gpt-area-routes.json; run kgg_gpt_source_context.py --write")
    if not source_index_json.exists():
        fail("missing docs/kgg-gpt-source-index.json; run kgg_gpt_source_context.py --write")
    data = json.loads(route_json.read_text(encoding="utf-8"))
    source_index = json.loads(source_index_json.read_text(encoding="utf-8"))
    if data.get("version") != 2 or data.get("sourceIndex") != "docs/kgg-gpt-source-index.json":
        fail("area routes must use source-local schema v2")
    if source_index.get("version") != 2:
        fail("Admin source index must use content-addressed schema v2")
    sources = source_index.get("sources")
    if not isinstance(sources, list) or not sources or sources[0].get("path") != "kgg-update/src/parts.json":
        fail("Admin source index must start with kgg-update/src/parts.json")
    routes = {route["id"]: route for route in data.get("routes", [])}
    for route_id in ["tablet-layout", "phone-layout", "qr-patient", "camera-qr", "pdf", "android-apk", "sync", "preview-gate"]:
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
    for chunk in tablet["sourceChunks"]:
        required_chunk_fields = {
            "sourcePath",
            "sourceSha256",
            "name",
            "path",
            "payloadSha256",
            "payloadBytes",
            "payloadLines",
        }
        if not isinstance(chunk, dict) or not required_chunk_fields.issubset(chunk):
            fail("area route sourceChunks must expose source-local hash metadata")
        if re.fullmatch(r"chunk-v2-[0-9a-f]{16}\.md", str(chunk["name"])) is None:
            fail("area route references a non-v2 Admin source chunk")
    for marker in tablet.get("markers", []):
        if marker.get("marker") in required and (
            not marker.get("sourcePath")
            or not isinstance(marker.get("sourceLine"), int)
            or not marker.get("payloadSha256")
        ):
            fail("tablet-layout marker is missing source-local v2 metadata")


def check_repair_lab_contract() -> None:
    lab_doc = read("docs/kgg-custom-gpt-repair-lab.md")
    report = read("docs/kgg-custom-gpt-repair-lab-report.md")
    eval_knowledge = read("docs/kgg-custom-gpt-eval-knowledge.md")
    raw_schema = read("docs/kgg-custom-gpt-repair-lab-raw-openapi.yaml")
    api_schema = read("docs/kgg-custom-gpt-repair-lab-api-openapi.yaml")
    workflow = read(".github/workflows/kgg-gpt-repair-lab.yml")
    require_all(
        lab_doc,
        ["Acht Kernbereiche", "zwei verdeckten Holdouts", "Golden `PASS`", "beschaedigt `FAIL`", "Kontrollreparatur `PASS`", "drei gleichen Fehlerklassen"],
        "Repair-Lab runbook",
    )
    require_all(report, ["8/8", "2/2", "GPT-5.6 Thinking", "Echte Blindrunden"], "Repair-Lab report")
    require_all(
        eval_knowledge,
        ["solution-free", "Do not use Web Search", "__KGG_PATCH_ID__", "three consecutive failures", "Never claim PASS"],
        "isolated Eval Knowledge",
    )
    require_all(raw_schema, ["gpt-repair-lab", "getKggRepairLabIndex", "getKggRepairChallenge", "getKggRepairSourceChunk"], "Repair-Lab raw schema")
    require_all(api_schema, ["submitKggRepairAttempt", "evaluate_attempt", "listKggRepairLabRuns", "getKggRepairLabArtifacts"], "Repair-Lab API schema")
    require_all(
        workflow,
        ["publish_challenges", "evaluate_attempt", "--include-holdouts", "kgg-repair-lab/public", "kgg-repair-result/report.json"],
        "Repair-Lab workflow",
    )


def main() -> int:
    try:
        check_playbook()
        check_workflow_obstacle_lesson()
        check_prompt_and_expected_docs()
        check_area_routes()
        check_repair_lab_contract()
        run_preflight_self_test()
        run_preview_status_self_test()
        run_stabilize_self_test()
        run_mock_eval_self_test()
        run_brain_relay_worker_self_test()
        run_repair_lab_self_tests()
        run_validate_only_self_test()
        run_main_approval_self_test()
        run_preview_banner_self_test()
        run_modular_rollback_self_test()
        print("KGG Custom GPT eval OK")
        return 0
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
