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
        "- Primary Admin source: `kgg-update/index.html`.",
        "- Web update metadata: `kgg-update/version.json`.",
        "- Android/Web release manifest: `therapist-app/android_update_manifest.json`.",
        "- Release pipeline docs: `release-pipeline/README.md`.",
        "- Bug-history lessons: `docs/kgg-gpt-bug-lessons.md`, `docs/kgg-gpt-bug-index.json`, `docs/kgg-gpt-patch-patterns.md`.",
        "- The Custom GPT action is read-only. Real patches, beta HTML builds, PRs and tests run in Codex or GitHub Actions.",
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
        "",
        "## Patch Routing",
        "",
        "- Before planning a patch, determine the real basis from `main`, the manifest and the target profile.",
        "- Before proposing or dispatching a patch, load the bug-history lessons and look for similar symptoms.",
        "- If a known bug-history lesson matches, reuse its caution, do-not-touch rules and tests.",
        "- Do not assume the newest local HTML is live.",
        "- If Max asks the Custom GPT to build a beta HTML, it must explain that the action is read-only and route the actual build to Codex or the release pipeline.",
        "- If the Custom GPT cannot load this context, it must say that repo context is unavailable instead of guessing or asking Max for old basis filenames.",
        "",
        "## Required Tests",
        "",
        "- Every code change: `cmd /c release-pipeline\\run-kgg-tests.cmd --level critical`.",
        "- UI, HTML, flicker, phone, tablet, card drag or layout changes: also `cmd /c release-pipeline\\run-kgg-tests.cmd --suite ui-stability --level regression`.",
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
        "- The Custom GPT action must stay read-only in v1: no push, no merge, no workflow dispatch, no token request.",
        "",
        "## Update Mechanism",
        "",
        "- This file is generated by `release-pipeline/kgg_gpt_context.py`.",
        "- Bug-history knowledge is generated by `release-pipeline/kgg_bug_knowledge.py`.",
        "- Run `python release-pipeline/kgg_gpt_context.py --write` after changing version, release, workflow, test or durable project-rule context.",
        "- Run `python release-pipeline/kgg_bug_knowledge.py --write` after changing bug/debug docs, patch lessons or known failure rules.",
        "- CI runs `python release-pipeline/kgg_gpt_context.py --check` and `python release-pipeline/kgg_bug_knowledge.py --check` in the required gate so stale GPT context cannot silently merge.",
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
