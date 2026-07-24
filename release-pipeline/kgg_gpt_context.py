#!/usr/bin/env python3
"""Generate the live repo context used by the private KGG Custom GPT."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONTEXT_PATH = ROOT / "docs" / "kgg-gpt-context.md"
VERSION_PATH = ROOT / "kgg-update" / "version.json"
MANIFEST_PATH = ROOT / "therapist-app" / "android_update_manifest.json"


def read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RuntimeError(f"Missing required context source: {path.relative_to(ROOT)}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Invalid JSON in {path.relative_to(ROOT)}: {exc}") from exc


def value(data: dict[str, Any], key: str, default: str = "unknown") -> str:
    item = data.get(key, default)
    if item is None or item == "":
        return default
    return str(item)


def render_context() -> str:
    version = read_json(VERSION_PATH)
    manifest = read_json(MANIFEST_PATH)
    channels = manifest.get("channels", {})
    admin = channels.get("admin", {}) if isinstance(channels, dict) else {}
    colleague = channels.get("colleague", {}) if isinstance(channels, dict) else {}

    lines = [
        "# KGG GPT Live Context",
        "",
        "This file is the live repo context for the private KGG Update-Agent Custom GPT.",
        "Reload it before answering repo-, version-, patch-, beta-HTML- or test-related questions.",
        "If this file conflicts with `kgg-update/version.json` or `therapist-app/android_update_manifest.json`, trust the JSON source files and tell Max.",
        "",
        "## Repository",
        "",
        "- GitHub repo: `https://github.com/Kayus24/kgg`.",
        "- Source branch: `main`.",
        "- Modular Admin source: `kgg-update/src`.",
        "- Generated public Admin HTML: `kgg-update/index.html`.",
        "- Web update metadata: `kgg-update/version.json`.",
        "- Android/Web release manifest: `therapist-app/android_update_manifest.json`.",
        "- Release pipeline docs: `release-pipeline/README.md`.",
        "- Custom GPT playbook: `docs/kgg-custom-gpt-playbook.md`.",
        "- Custom GPT action schema: `docs/kgg-custom-gpt-action-schema.md`.",
        "- Custom GPT combined Action OpenAPI: `docs/kgg-custom-gpt-action-openapi.yaml`.",
        "- Custom GPT API-only Action OpenAPI for the current split editor setup: `docs/kgg-custom-gpt-action-api-openapi.yaml`.",
        "- Custom GPT negative examples: `docs/kgg-custom-gpt-negative-examples.md`.",
        "- Custom GPT preview runbook: `docs/kgg-custom-gpt-preview-runbook.md`.",
        "- Custom GPT preview report template: `docs/kgg-custom-gpt-preview-report-template.md`.",
        "- Custom GPT Wissen/Knowledge pack: `docs/kgg-custom-gpt-knowledge-pack.md`.",
        "- Curated production Knowledge: `docs/kgg-custom-gpt-knowledge-{architecture,operations,safety,testing}.md`.",
        "- Custom GPT model/capability/resource contract: `docs/kgg-custom-gpt-resource-manifest.json`.",
        "- Blind full-app Repair-Lab: `docs/kgg-custom-gpt-repair-lab.md`, workflow `.github/workflows/kgg-gpt-repair-lab.yml`.",
        "- Isolated Eval-GPT Knowledge: `docs/kgg-custom-gpt-eval-knowledge.md`; never upload production fixtures to this GPT.",
        "- Custom GPT stabilization cycle report: `docs/kgg-custom-gpt-cycle-report.md`.",
        "- Bug-history lessons: `docs/kgg-gpt-bug-lessons.md`, `docs/kgg-gpt-bug-index.json`, `docs/kgg-gpt-patch-patterns.md`.",
        "- Source routing: `docs/kgg-gpt-area-routes.md`, `docs/kgg-gpt-area-routes.json`.",
        "- Source chunks for GPT patch planning: `docs/kgg-gpt-source-index.json` and `docs/kgg-gpt-source/chunk-*.md`.",
        "- GPT eval fixtures: `docs/kgg-custom-gpt-test-prompts.md`, `docs/kgg-custom-gpt-expected-results.md`, `docs/kgg-custom-gpt-test-report.md`.",
        "- GPT stabilization runner: `release-pipeline/kgg_gpt_stabilize.py`.",
        "- Blind Repair-Lab runner: `release-pipeline/kgg_gpt_repair_lab.py`; acceptance tracker: `release-pipeline/kgg_gpt_repair_stabilize.py`.",
        "- GPT preview channel branch: `gpt-preview`, files below `previews/`.",
        "- Private project memory: `Kayus24/kgg-project-memory`; load `memory/index.json` first and then only the smallest matching pack.",
        "- The Custom GPT may write app changes only through `KGG GPT Preview Gate` and durable knowledge only through `KGG Project Memory Gate`; other direct writes and direct merges stay forbidden.",
        "",
        "## Current Versions",
        "",
        f"- Source web version: v{value(version, 'versionCode')} / `{value(version, 'versionName')}`.",
        f"- Source index URL: `{value(version, 'indexUrl')}`.",
        f"- Source notes: {value(version, 'notes')}",
        f"- Live Admin release: `{value(admin, 'releaseId')}` / `{value(admin, 'versionName')}`.",
        f"- Live Admin URL: `{value(manifest, 'adminHtmlUrl', value(admin, 'url'))}`.",
        f"- Live colleague release: `{value(colleague, 'releaseId')}` / `{value(colleague, 'versionName')}`.",
        f"- Live colleague URL: `{value(manifest, 'colleagueHtmlUrl', value(colleague, 'url'))}`.",
        f"- Latest Android shell: `{value(manifest, 'latestAndroidShellVersion')}`.",
        f"- Latest colleague APK: `{value(manifest, 'latestColleagueAndroidApkUrl', value(manifest, 'androidApkUrl'))}`.",
        f"- Latest Admin APK: `{value(manifest, 'latestAdminAndroidApkUrl')}`.",
        "",
        "## Hard Rules For The GPT",
        "",
        "- Work with Max in German: pragmatic, direct, few questions.",
        "- Do not rebuild the app and do not refactor unless Max explicitly asks.",
        "- Make the smallest safe patch and only one logical change per patch.",
        "- Never hardcode API keys or place secrets in GitHub, HTML, JS, JSON, tests or handoff files.",
        "- Never expose patient JSON, raw Base64 or debug payloads as normal patient output.",
        "- Treat `KGGDataStore.currentPlan` as the central plan-state source.",
        "- Do not touch PDF, QR/patient app, scan/OCR, parser, plan-state, media/upload, API-key logic, Android/APK, GitHub manifest or phone layout unless Max explicitly asks.",
        "- Existing uncommitted local changes belong to Max or another run. Do not reset them.",
        "- Automatically add confirmed durable decisions and lessons to the private project memory, but never overwrite an active instruction without Max' explicit approval.",
        "- Do not store chats, patient data, secrets or transient debug output in the project memory.",
        "",
        "## Patch Routing",
        "",
        "- Before planning a patch, load `docs/kgg-custom-gpt-playbook.md` and determine the real basis from `main`, the manifest and the target profile.",
        "- Before proposing or dispatching a patch, load the bug-history lessons and look for similar symptoms.",
        "- Before producing a patch payload, load `docs/kgg-gpt-area-routes.md` and then only the source chunks needed for the requested area.",
        "- If a known bug-history lesson matches, reuse its caution, do-not-touch rules and tests.",
        "- Run payload JSON through `python release-pipeline/kgg_gpt_payload_preflight.py --payload-file <file>` before dispatching.",
        "- New GPT patches use payload v2 with `patch_content`; direct operations against `kgg-update/index.html` are forbidden because `index.html` is generated output.",
        "- Do not assume the newest local HTML is live.",
        "- If Max asks for a beta, use `KGG GPT Preview Gate` in `validate_only` mode first, then `publish_preview` after green validation; do not create a PR until Max explicitly accepts the Test-App/Preview-APK result.",
        "- If Max asks for Test-APK review, publish only through the Preview/Test-APK channel and wait for Max' Test-APK acceptance before PR/main steps.",
        "- If Max says the preview is good, use `create_pr` only with the same `request_id` and patch hash unless Max explicitly requests the real Admin-Beta/Haupt-App push.",
        "- A positive end-to-end push test requires both `publish_preview` for Test-App/Preview-App and `publish_admin_beta` for Admin-Beta merge to `main`.",
        "- If critical fails with `Missing tool pdftoppm`, `Missing tool pdfinfo`, `poppler-utils`, `adb` or emulator tooling, classify it as `ci_tooling`, not as an app/UI patch failure.",
        "- If a Preview run fails, report the failed step and the actual error before checking `meta.json` or manifest URLs.",
        "- If the Custom GPT cannot load this context, it must say that repo context is unavailable instead of guessing or asking Max for old basis filenames.",
        "- Before each real GPT test cycle verify the highest Actions-compatible model and capability/Knowledge hashes against `docs/kgg-custom-gpt-resource-manifest.json`.",
        "- The isolated Eval GPT must not receive Web Search, production Actions, production Knowledge, intact main HTML, golden source, sample repairs or hidden assertions.",
        "- A Repair-Lab PASS is evaluation evidence only and never authorizes Preview/Test-App, PR, Admin-Beta or main.",
        "",
        "## Required Tests",
        "",
        "- Every code change: `cmd /c release-pipeline\\run-kgg-tests.cmd --level critical`.",
        "- UI, HTML, flicker, phone, tablet, card drag or layout changes: also `cmd /c release-pipeline\\run-kgg-tests.cmd --suite ui-stability --level regression`.",
        "- GPT playbook, routing, payload or bug-knowledge changes: also `python release-pipeline\\kgg_gpt_payload_preflight.py --self-test` and `python release-pipeline\\kgg_gpt_eval.py`.",
        "- Custom GPT stabilization changes: also `python release-pipeline\\kgg_gpt_stabilize.py --self-test`, `python release-pipeline\\kgg_custom_gpt_knowledge_pack.py --check` and update `docs/kgg-custom-gpt-cycle-report.md`.",
        "- Repair-Lab changes: also `python release-pipeline\\kgg_gpt_repair_lab.py --self-test`, `python release-pipeline\\kgg_gpt_repair_stabilize.py --self-test` and `python release-pipeline\\kgg_custom_gpt_resource_audit.py --check`.",
        "- Parser or text-block changes: also `cmd /c release-pipeline\\run-kgg-tests.cmd --suite textblocks --level regression`.",
        "- Sync, bank, package or peer changes: also `cmd /c release-pipeline\\run-kgg-tests.cmd --suite sync --level regression`.",
        "- Android sync bridge changes: also `cmd /c release-pipeline\\run-kgg-tests.cmd --suite native-sync --level regression`.",
        "- `mobile-inbox-live` is never automatic because it intentionally creates a new Admin beta.",
        "",
        "## GitHub Guardrails",
        "",
        "- `main` is protected and must not be written directly.",
        "- Required status check: `KGG Required Gate / required-gate`.",
        "- Admin beta auto-merge requires green checks plus the explicit `kgg-auto-merge` label.",
        "- Custom GPT write access is limited to workflow dispatch for `.github/workflows/kgg-gpt-preview-gate.yml`.",
        "- The isolated Eval GPT may dispatch only `.github/workflows/kgg-gpt-repair-lab.yml`; that workflow cannot create Preview, PR, Admin-Beta or main changes.",
        "- Project-memory write access is limited to workflow dispatch for `Kayus24/kgg-project-memory/.github/workflows/kgg-memory-gate.yml`.",
        "- Memory reads must start with `getKggMemoryIndex`, then use only matching packs; history and records are on-demand only.",
        "- A memory update uses `validate_only` before `apply`; `needs_approval` must stop until Max explicitly approves the superseding record.",
        "- GPT Action schema must expose `validate_only`, `publish_preview`, `create_pr`, `publish_admin_beta` and run/job/artifact status reads.",
        "- Current GPT editor setup uses split Actions; paste the API-only schema into `api.github.com` to avoid duplicate `raw.githubusercontent.com` domains.",
        "- Preview writes go only to branch `gpt-preview`; production writes are PR-only and never auto-merge.",
        "",
        "## Update Mechanism",
        "",
        "- This file is generated by `release-pipeline/kgg_gpt_context.py`.",
        "- Bug-history knowledge is generated by `release-pipeline/kgg_bug_knowledge.py`.",
        "- Source chunk and area-route context is generated by `release-pipeline/kgg_gpt_source_context.py`.",
        "- Custom GPT knowledge pack is generated by `release-pipeline/kgg_custom_gpt_knowledge_pack.py`.",
        "- Custom GPT resource hashes are generated by `release-pipeline/kgg_custom_gpt_resource_audit.py`.",
        "- Run `python release-pipeline/kgg_gpt_context.py --write` after changing version, release, workflow, test or durable project-rule context.",
        "- Run `python release-pipeline/kgg_bug_knowledge.py --write` after changing bug/debug docs, patch lessons or known failure rules.",
        "- Run `python release-pipeline/kgg_gpt_source_context.py --write` after changing `kgg-update/src`, generated source routing rules or modular patch behavior.",
        "- Run `python release-pipeline/kgg_gpt_eval.py` after changing Custom GPT playbook, prompts, expected results, routing or preflight behavior.",
        "- Run `python release-pipeline/kgg_custom_gpt_knowledge_pack.py --write` after changing Custom GPT docs that should be uploaded to GPT Wissen.",
        "- Run `python release-pipeline/kgg_gpt_stabilize.py --write-report` after running a GPT stabilization cycle.",
        "- CI runs GPT context, bug knowledge and source context freshness checks in the required gate so stale GPT context cannot silently merge.",
        "",
    ]
    return "\n".join(lines)


def normalize(text: str) -> str:
    return text.replace("\r\n", "\n").rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate or check KGG GPT live context.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true", help="Write docs/kgg-gpt-context.md.")
    group.add_argument("--check", action="store_true", help="Fail if docs/kgg-gpt-context.md is stale.")
    group.add_argument("--print", action="store_true", help="Print the generated context.")
    args = parser.parse_args()

    try:
        expected = normalize(render_context())
        if args.print:
            print(expected, end="")
            return 0
        if args.write:
            CONTEXT_PATH.parent.mkdir(parents=True, exist_ok=True)
            CONTEXT_PATH.write_text(expected, encoding="utf-8", newline="\n")
            print(f"Wrote {CONTEXT_PATH.relative_to(ROOT)}")
            return 0
        if not CONTEXT_PATH.exists():
            raise RuntimeError("docs/kgg-gpt-context.md is missing. Run release-pipeline/kgg_gpt_context.py --write.")
        current = normalize(CONTEXT_PATH.read_text(encoding="utf-8"))
        if current != expected:
            raise RuntimeError("docs/kgg-gpt-context.md is stale. Run release-pipeline/kgg_gpt_context.py --write.")
        print("KGG GPT context OK")
        return 0
    except RuntimeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
