#!/usr/bin/env python3
"""Deterministic checks for the KGG Custom GPT playbook and fixtures."""

from __future__ import annotations

import json
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


def run_repair_lab_self_tests() -> None:
    commands = [
        [sys.executable, "release-pipeline/kgg_gpt_repair_lab.py", "--self-test"],
        [sys.executable, "release-pipeline/kgg_gpt_repair_stabilize.py", "--self-test"],
        [sys.executable, "release-pipeline/kgg_gpt_natural_ui_lab.py", "--self-test"],
        [sys.executable, "release-pipeline/kgg_gpt_natural_ui_stabilize.py", "--self-test"],
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


def run_preview_banner_self_test() -> None:
    payload = {
        "request_id": "preview-banner-self-test",
        "title": "Preview banner self-test",
        "summary": "The marker must not enter the app flex layout or block its controls.",
    }
    source = '<!doctype html><html><body style="display:flex"><button id="menu">Menu</button></body></html>'
    rendered = write_gate.inject_preview_banner(source, payload, "a" * 64)
    require_all(
        rendered,
        [
            'id="kgg-gpt-preview-banner"',
            "position:fixed",
            "pointer-events:none",
            "white-space:nowrap",
            "text-overflow:ellipsis",
        ],
        "non-blocking preview banner",
    )
    if "position:sticky" in rendered:
        fail("preview banner must not participate in the app flex layout")
    if rendered.count('id="kgg-gpt-preview-banner"') != 1:
        fail("preview banner must be injected exactly once")


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
            "submitKggMemoryUpdate",
            "needs_approval",
            "supersedes",
            "Kayus24/kgg-project-memory",
            "getKggCustomGptResourceManifest",
            "GitHub Pages ist kein Memory-Fallback",
            "docs/kgg-custom-gpt-editor-bootstrap.md",
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
    knowledge_pack = read("docs/kgg-custom-gpt-knowledge-pack.md")
    editor_bootstrap = read("docs/kgg-custom-gpt-editor-bootstrap.md")
    resource_manifest = read("docs/kgg-custom-gpt-resource-manifest.json")
    openapi_schema = read("docs/kgg-custom-gpt-action-openapi.yaml")
    api_openapi_schema = read("docs/kgg-custom-gpt-action-api-openapi.yaml")
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
        "human-preview-fail",
        "stale-context",
        "analysis-no-dispatch",
        "ci-tooling-pdftoppm",
        "admin-beta-push-gate",
        "memory-safe-auto-update",
        "memory-conflict-needs-approval",
        "memory-no-change",
        "memory-private-unavailable",
        "editor-resource-drift",
        "natural-language-ui-understanding",
        "natural-language-one-clarification",
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
            "submitKggPreviewGate",
            "meta.json",
            "listKggPreviewGateRuns",
            "getKggMemoryIndex",
            "getKggMemoryPack",
            "getKggMemoryUpdateStatus",
            "needs_approval",
            "supersedes",
            "GitHub Pages",
            "Bootstrap `v2`",
            "getKggCustomGptResourceManifest",
        ],
        "expected behavior text",
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
            "listKggPreviewGateRuns",
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
            "getKggCustomGptResourceManifest",
            "kgg-custom-gpt-editor-bootstrap.md",
            "GitHub Pages is not a project-memory source",
        ],
        "action schema text",
    )
    require_all(
        openapi_schema,
        [
            "getKggCustomGptResourceManifest",
            "getKggProjectContext",
            "getKggCustomGptPlaybook",
            "getKggSourceIndex",
            "getKggSourceChunk",
            "getKggVersion",
            "getKggPreviewIndex",
            "getKggPreviewMeta",
        ],
        "custom GPT raw OpenAPI schema",
    )
    if "\n  /repos/" in openapi_schema or "api.github.com" in openapi_schema:
        fail("raw OpenAPI schema duplicates authenticated GitHub API operations")
    if openapi_schema.count("operationId:") > 30:
        fail("raw OpenAPI schema exceeds the Custom GPT 30-operation limit")
    require_all(
        api_openapi_schema,
        [
            "submitKggPreviewGate",
            "- validate_only",
            "- publish_preview",
            "- create_pr",
            "- publish_admin_beta",
            "listKggPreviewGateRuns",
            "getKggPreviewGateRun",
            "getKggPreviewGateJobs",
            "getKggPreviewGateArtifacts",
            "required_tests",
            "patch_content",
            "schemas: {}",
            "properties:",
            "getKggMemoryIndex",
            "getKggMemoryPack",
            "getKggMemoryRecord",
            "getKggMemoryHistory",
            "submitKggMemoryUpdate",
            "listKggMemoryUpdateRuns",
            "getKggMemoryUpdateRun",
            "getKggMemoryUpdateStatus",
            "getKggMemoryUpdateArtifacts",
        ],
        "custom GPT API-only OpenAPI schema",
    )
    if api_openapi_schema.count("operationId:") > 30:
        fail("API-only OpenAPI schema exceeds the Custom GPT 30-operation limit")
    require_all(
        negative_examples,
        [
            "operations",
            "path",
            "patch_content",
            "API-Key",
            "Roter Run",
            "Manuelle Versionierung",
            "Test-App",
            "GitHub Pages ist keine Memory-Quelle",
            "Editor-Ressourcen sind stale",
        ],
        "negative examples text",
    )
    require_all(
        editor_bootstrap,
        [
            "KGG Update-Agent Editor Bootstrap v2",
            "getKggCustomGptResourceManifest",
            "getKggProjectContext",
            "getKggCustomGptPlaybook",
            "getKggMemoryIndex",
            "GitHub Pages ist weder Memory-Quelle noch Fallback",
            "validate_only -> publish_preview",
        ],
        "editor bootstrap",
    )
    require_all(
        resource_manifest,
        [
            '"schema": 2',
            '"profileVersion": "2.1.0"',
            '"editorBootstrap"',
            '"version": "v2"',
            "kgg-custom-gpt-editor-bootstrap.md",
        ],
        "resource manifest",
    )
    require_all(
        runbook,
        ["dispatch -> run status", "validate_only", "artifact", "meta.json", "html_url", "Max acceptance", "Admin beta merge", "ci_tooling"],
        "preview runbook text",
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
            "docs/kgg-custom-gpt-preview-runbook.md",
            "ci_tooling",
            "publish_admin_beta",
        ],
        "knowledge pack text",
    )


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
    if data.get("sourcePath") != "kgg-update/src":
        fail("area routes must be generated from modular source kgg-update/src")
    if not tablet.get("sourceChunks"):
        fail("tablet-layout route must resolve source chunks")


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
        [
            "solution-free",
            "Do not use Web Search",
            "__KGG_PATCH_ID__",
            "<!-- KGG PATCH START",
            "getKggRepairResult",
            "three consecutive failures",
            "Never claim PASS",
        ],
        "isolated Eval Knowledge",
    )
    require_all(
        raw_schema,
        [
            "gpt-repair-lab",
            "getKggRepairLabIndex",
            "getKggRepairChallenge",
            "getKggRepairSourceChunk",
            "getKggRepairResult",
            "sanitized evaluator outcome",
        ],
        "Repair-Lab raw schema",
    )
    require_all(api_schema, ["submitKggRepairAttempt", "evaluate_attempt", "listKggRepairLabRuns", "getKggRepairLabArtifacts"], "Repair-Lab API schema")
    require_all(
        workflow,
        [
            "publish_challenges",
            "evaluate_attempt",
            "--include-holdouts",
            "kgg-repair-lab/public",
            "kgg-repair-result/report.json",
            "kgg-repair-result/outcome.json",
            "Publish sanitized evaluation outcome",
        ],
        "Repair-Lab workflow",
    )


def check_natural_ui_lab_contract() -> None:
    lab_doc = read("docs/kgg-custom-gpt-natural-ui-lab.md")
    report = read("docs/kgg-custom-gpt-natural-ui-lab-report.md")
    eval_knowledge = read("docs/kgg-custom-gpt-eval-knowledge.md")
    raw_schema = read("docs/kgg-custom-gpt-repair-lab-raw-openapi.yaml")
    api_schema = read("docs/kgg-custom-gpt-repair-lab-api-openapi.yaml")
    workflow = read(".github/workflows/kgg-gpt-repair-lab.yml")
    runner = read("release-pipeline/kgg_gpt_natural_ui_lab.py")
    stabilize = read("release-pipeline/kgg_gpt_natural_ui_stabilize.py")
    require_all(
        lab_doc,
        [
            "Sechs Klassen",
            "genau einer notwendigen Rueckfrage",
            "Kanonische Absicht",
            "gpt-natural-ui-lab",
            "validate_only -> publish_preview",
        ],
        "Natural UI Lab runbook",
    )
    require_all(
        report,
        [
            "HARNESS GREEN",
            "Eindeutige verrauschte UI-Anfrage",
            "Echte Mehrdeutigkeit",
            "Runde 1",
            "Runde 2",
            "Max Test-App-Freigabe",
        ],
        "Natural UI Lab report",
    )
    require_all(
        eval_knowledge,
        [
            "Natural UI Mode",
            "clarification",
            "confidence",
            "low",
            "medium",
            "high",
            "getKggNaturalUiResult",
            "canonical intent",
            "executable HTML fragment",
            "Bare CSS or JavaScript",
            "final cascade",
            "guessed child containers",
        ],
        "Natural UI Eval Knowledge",
    )
    require_all(
        raw_schema,
        [
            "gpt-natural-ui-lab",
            "getKggNaturalUiLabIndex",
            "getKggNaturalUiChallenge",
            "getKggNaturalUiScreenshot",
            "getKggNaturalUiSourceChunk",
            "getKggNaturalUiResult",
        ],
        "Natural UI raw schema",
    )
    require_all(
        api_schema,
        [
            "evaluate_natural_attempt",
            "submission_json",
            "patch_content",
            "Omit payload.patch_content",
            "never JSON-encode",
            "natural",
        ],
        "Natural UI API schema",
    )
    require_all(
        workflow,
        [
            "publish_natural_challenges",
            "evaluate_natural_attempt",
            "kgg-natural-ui-lab/public",
            "kgg-natural-ui-result/report.json",
            "Publish sanitized natural-language evaluation outcome",
            '[[ -n "$PATCH_CONTENT" ]]',
            '"patch_content" in payload',
            'payload["patch_content"] = os.environ["PATCH_CONTENT"]',
            'npm install --prefix "$runtime" --no-package-lock --no-save playwright@1.61.1',
            'echo "NODE_PATH=$runtime/node_modules" >> "$GITHUB_ENV"',
        ],
        "Natural UI workflow",
    )
    require_all(
        runner,
        [
            "canonical_intent_groups",
            "canonical_diagnosis_groups",
            "assert_public_is_blind",
            "marked-problem.png",
            "interpretation",
            "interpretation_types",
            "patch_content_format",
            "validate_patch_fragment",
            "computed display, columns or geometry",
        ],
        "Natural UI runner",
    )
    require_all(
        stabilize,
        [
            "REQUIRED_PER_ROUND = 6",
            "REQUIRED_GREEN_ROUNDS = 2",
            "MIN_FIRST_ATTEMPT_PASSES = 10",
            "MAX_ATTEMPTS_TO_PASS = 2",
            "STOP_ALTERNATIVE_REQUIRED",
        ],
        "Natural UI stabilizer",
    )


def main() -> int:
    try:
        check_playbook()
        check_prompt_and_expected_docs()
        check_area_routes()
        check_repair_lab_contract()
        check_natural_ui_lab_contract()
        run_preflight_self_test()
        run_stabilize_self_test()
        run_mock_eval_self_test()
        run_repair_lab_self_tests()
        run_validate_only_self_test()
        run_preview_banner_self_test()
        run_modular_rollback_self_test()
        print("KGG Custom GPT eval OK")
        return 0
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
