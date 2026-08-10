#!/usr/bin/env python3
"""Guarded modular Custom GPT preview, PR and Admin-beta payload handling for KGG."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from html import escape as escape_html
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import build_therapist_source as builder
import kgg_new_patch as module_patch
import release_pipeline as pipeline


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "kgg-update" / "index.html"
VERSION_PATH = ROOT / "kgg-update" / "version.json"
PREVIEW_BASE_URL = "https://raw.githubusercontent.com/Kayus24/kgg/gpt-preview/previews"
PREVIEW_INDEX = "previews/index.json"
PREVIEW_MARKER_START = "<!-- KGG_PREVIEW_MARKER_START -->"
PREVIEW_MARKER_END = "<!-- KGG_PREVIEW_MARKER_END -->"
MAX_PAYLOAD_BYTES = 120_000
MAX_CONTENT_BYTES = 80_000
MAX_REGRESSION_ASSERTIONS = 12
MAX_REGRESSION_VALUE_CHARS = 300
REGRESSION_ROOT = ROOT / "release-pipeline" / "gpt-regressions"

SECRET_PATTERN = re.compile(
    "("
    + "sk-" + "proj-"
    + r"|gh[pousr]_[A-Za-z0-9_]{20,}"
    + "|AI" + r"za[0-9A-Za-z_-]{25,}"
    + ")"
)
REQUEST_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{5,63}$")
SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PROTECTED_TOKENS = (
    "KGGDataStore.currentPlan",
    "finishWithPdf",
    "finishWithPatientApp",
    "scanQrFromImageFile",
    "KGGAndroidPdf",
    "KGGReleaseControl",
    "API-Key",
    "apiKey",
    "android_update_manifest",
    "KGG_ADMIN_ONLY_START",
    "KGG_ADMIN_ONLY_END",
)
FORBIDDEN_CONTENT_TOKENS = (
    "<!doctype",
    "<html",
    "</html",
    "<body",
    "</body",
    "<script src=",
    "<script type=\"application/json\" id=\"kgg-source-truth\"",
    "<script type=\"application/json\" id=\"kgg-changelog\"",
    "const VERSION=",
    "const KGG_BUILD_INFO=",
    "<!-- KGG PATCH START",
    "<!-- KGG PATCH END",
)
LEGACY_PAYLOAD_FIELDS = ("operations", "old_text", "oldText", "new_text", "newText", "path", "file", "filename", "target")
CROSS_APP_SCOPE = "cross-app-qr-preview"
CROSS_APP_PROTECTED_AREAS = {"QR/Patienten-App", "Scan/OCR"}
CROSS_APP_ALLOWED_PROTECTED_TOKENS = {"scanQrFromImageFile"}
MAIN_APPROVAL_PHRASE = "Gut für Main"
CRITICAL_TEST = "cmd /c release-pipeline\\run-kgg-tests.cmd --level critical"
UI_REGRESSION_TEST = "cmd /c release-pipeline\\run-kgg-tests.cmd --suite ui-stability --level regression"
CAMERA_QR_TEST = "cmd /c release-pipeline\\run-kgg-tests.cmd --suite camera-qr --level regression"
PATIENT_SCAN_TEST = "cmd /c release-pipeline\\run-kgg-tests.cmd --suite patient-scan --level regression"


class GateError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise GateError(message)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"Cannot read JSON {path}: {exc}")


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def canonical_payload(payload: dict[str, Any]) -> str:
    value = {
        "patch_content": payload["patch_content"],
        "protected_scope": payload["protected_scope"],
        "regression_contract": payload["regression_contract"],
        "request_id": payload["request_id"],
        "required_tests": payload["required_tests"],
        "summary": payload["summary"],
        "title": payload["title"],
        "touched_areas": payload["touched_areas"],
        "version_slug": payload["version_slug"],
    }
    return json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"))


def patch_hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_payload(payload).encode("utf-8")).hexdigest()


def git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return ""


def clean_ascii(value: str, fallback: str, limit: int) -> str:
    value = (value or "").strip()
    value = value.encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"\s+", " ", value).strip()
    return (value or fallback)[:limit].rstrip()


def normalize_area(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.casefold().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss"))


def normalized_string_list(payload: dict[str, Any], *keys: str) -> list[str]:
    raw = None
    for key in keys:
        if key in payload:
            raw = payload[key]
            break
    if not isinstance(raw, list):
        fail(f"{keys[0]} must be a non-empty list of strings")
    values = [str(item).strip() for item in raw if isinstance(item, str) and item.strip()]
    if not values or len(values) != len(raw):
        fail(f"{keys[0]} must be a non-empty list of non-empty strings")
    return list(dict.fromkeys(values))


def reject_legacy_payload(payload: dict[str, Any]) -> None:
    if "operations" in payload:
        fail(
            "payload v2 rejects operations/replace_exact. kgg-update/index.html is generated output; "
            "provide patch_content and let the gate create kgg-update/src/patches/vNNN-<slug>.html."
        )
    present = [field for field in LEGACY_PAYLOAD_FIELDS if field in payload]
    if present:
        fail(
            "payload v2 rejects legacy direct-file fields: "
            + ", ".join(sorted(present))
            + ". Provide patch_content only; the gate owns the module path."
        )


def validate_patch_content(content: str, protected_scope: str = "none") -> str:
    if not isinstance(content, str) or not content.strip():
        fail("patch_content must be a non-empty HTML fragment")
    if len(content.encode("utf-8")) > MAX_CONTENT_BYTES:
        fail("patch_content is too large")
    normalized = content.replace("\r\n", "\n").replace("\r", "\n").strip() + "\n"
    if "__KGG_PATCH_ID__" not in normalized:
        fail("patch_content must contain the __KGG_PATCH_ID__ placeholder")
    lower = normalized.lower()
    for token in FORBIDDEN_CONTENT_TOKENS:
        if token.lower() in lower:
            fail(f"patch_content contains forbidden generated-output token: {token}")
    if SECRET_PATTERN.search(normalized):
        fail("patch_content contains a token-shaped secret")
    allowed = CROSS_APP_ALLOWED_PROTECTED_TOKENS if protected_scope == CROSS_APP_SCOPE else set()
    touched = [token for token in PROTECTED_TOKENS if token in normalized and token not in allowed]
    if touched:
        fail("patch_content touches protected area tokens: " + ", ".join(touched))
    try:
        module_patch.render_patch_module("kgg-v999-self-test", "GPT content validation", normalized).decode("utf-8", errors="strict")
    except UnicodeError as exc:
        fail(f"patch_content must be valid UTF-8 text: {exc}")
    return normalized


def validate_regression_contract(value: Any, protected_scope: str) -> list[dict[str, str]]:
    if value is None:
        return []
    if not isinstance(value, list) or not value or len(value) > MAX_REGRESSION_ASSERTIONS:
        fail(f"regression_contract must contain 1 to {MAX_REGRESSION_ASSERTIONS} assertions")
    allowed_protected = CROSS_APP_ALLOWED_PROTECTED_TOKENS if protected_scope == CROSS_APP_SCOPE else set()
    assertions: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for index, item in enumerate(value, start=1):
        if not isinstance(item, dict):
            fail(f"regression_contract assertion {index} must be an object")
        kind = str(item.get("kind") or "").strip().lower()
        token = item.get("value")
        if kind not in {"contains", "not_contains"}:
            fail(f"regression_contract assertion {index} kind must be contains or not_contains")
        if not isinstance(token, str):
            fail(f"regression_contract assertion {index} value must be a string")
        token = token.replace("\r\n", "\n").replace("\r", "\n").strip()
        if len(token) < 3 or len(token) > MAX_REGRESSION_VALUE_CHARS or "\x00" in token:
            fail(
                f"regression_contract assertion {index} value must contain 3 to "
                f"{MAX_REGRESSION_VALUE_CHARS} safe characters"
            )
        if SECRET_PATTERN.search(token):
            fail(f"regression_contract assertion {index} contains a token-shaped secret")
        protected = [name for name in PROTECTED_TOKENS if name in token and name not in allowed_protected]
        if protected:
            fail(
                f"regression_contract assertion {index} touches protected tokens: "
                + ", ".join(protected)
            )
        key = (kind, token)
        if key not in seen:
            assertions.append({"kind": kind, "value": token})
            seen.add(key)
    if not any(item["kind"] == "contains" for item in assertions):
        fail("regression_contract requires at least one contains assertion")
    return assertions


def validate_payload(raw: str) -> dict[str, Any]:
    if len(raw.encode("utf-8")) > MAX_PAYLOAD_BYTES:
        fail("payload_json is too large")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        fail(f"payload_json is invalid JSON: {exc}")
    if not isinstance(payload, dict):
        fail("payload_json must be an object")
    reject_legacy_payload(payload)

    request_id = str(payload.get("request_id") or payload.get("requestId") or "").strip().lower()
    if not REQUEST_ID_PATTERN.fullmatch(request_id):
        fail("request_id must match [a-z0-9][a-z0-9-]{5,63}")
    title = str(payload.get("title") or "").strip()
    summary = str(payload.get("summary") or "").strip()
    if not title or not summary:
        fail("title and summary are required")
    version_slug = str(payload.get("version_slug") or payload.get("versionSlug") or "").strip().lower()
    if not SLUG_PATTERN.fullmatch(version_slug):
        fail("version_slug must contain lowercase letters/numbers separated by single hyphens")
    touched_areas = normalized_string_list(payload, "touched_areas", "touchedAreas")
    required_tests = normalized_string_list(payload, "required_tests", "requiredTests")
    protected_scope = str(payload.get("protected_scope") or payload.get("protectedScope") or "none").strip().lower()
    if protected_scope not in {"none", CROSS_APP_SCOPE}:
        fail(f"protected_scope must be none or {CROSS_APP_SCOPE}")
    patch_content = validate_patch_content(
        payload.get("patch_content") or payload.get("patchContent"),
        protected_scope,
    )
    regression_contract = validate_regression_contract(
        payload.get("regression_contract", payload.get("regressionContract")),
        protected_scope,
    )

    protected_norm = {normalize_area(area): area for area in module_patch.PROTECTED_AREAS}
    selected_protected = [protected_norm[normalize_area(area)] for area in touched_areas if normalize_area(area) in protected_norm]
    if selected_protected and protected_scope != CROSS_APP_SCOPE:
        fail("protected touched_areas require explicit Max approval outside the GPT gate: " + ", ".join(selected_protected))
    if protected_scope == CROSS_APP_SCOPE:
        unexpected_protected = sorted(set(selected_protected) - CROSS_APP_PROTECTED_AREAS)
        if unexpected_protected:
            fail("cross-app QR scope cannot touch protected areas: " + ", ".join(unexpected_protected))
        if not set(selected_protected) & CROSS_APP_PROTECTED_AREAS:
            fail("cross-app QR scope requires QR/Patienten-App or Scan/OCR in touched_areas")
        declared = {item.casefold() for item in required_tests}
        missing = [
            required
            for required in (CRITICAL_TEST, UI_REGRESSION_TEST, CAMERA_QR_TEST, PATIENT_SCAN_TEST)
            if required.casefold() not in declared
        ]
        if missing:
            fail("cross-app QR scope requires these exact tests: " + "; ".join(missing))

    combined_text = json.dumps(
        {
            "title": title,
            "summary": summary,
            "version_slug": version_slug,
            "touched_areas": touched_areas,
            "required_tests": required_tests,
            "patch_content": patch_content,
            "protected_scope": protected_scope,
            "regression_contract": regression_contract,
        },
        ensure_ascii=False,
    )
    if SECRET_PATTERN.search(combined_text):
        fail("payload contains a token-shaped secret")

    return {
        "request_id": request_id,
        "title": title,
        "summary": summary,
        "version_slug": version_slug,
        "touched_areas": touched_areas,
        "required_tests": required_tests,
        "patch_content": patch_content,
        "protected_scope": protected_scope,
        "regression_contract": regression_contract,
    }


def plan_modular_patch(payload: dict[str, Any]) -> tuple[dict[Path, bytes], dict[str, Any]]:
    args = SimpleNamespace(
        slug=payload["version_slug"],
        title=payload["title"],
        summary=payload["summary"],
        area=payload["touched_areas"],
        version_name=None,
        allow_protected=payload["protected_scope"] == CROSS_APP_SCOPE,
        allow_changelog_overflow=False,
        approval_note=(
            "Gate-managed cross-app QR Preview scope authorized by Max; PR/Main still require the exact final approval phrase."
            if payload["protected_scope"] == CROSS_APP_SCOPE
            else ""
        ),
        patch_content=payload["patch_content"],
    )
    planned, report = module_patch.prepare(args)
    patch_file = str(report.get("patchFile", ""))
    if not re.fullmatch(r"patches/v[0-9]{3}-[a-z0-9]+(?:-[a-z0-9]+)*\.html", patch_file):
        fail(f"unsafe generated patch file: {patch_file}")
    patch_path = (ROOT / "kgg-update" / "src" / patch_file).resolve()
    try:
        patch_path.relative_to(ROOT / "kgg-update" / "src" / "patches")
    except ValueError as exc:
        raise GateError(f"generated patch file escapes patches directory: {patch_file}") from exc
    if payload["regression_contract"]:
        contract_path = (REGRESSION_ROOT / f"{payload['request_id']}.json").resolve()
        try:
            contract_path.relative_to(REGRESSION_ROOT.resolve())
        except ValueError as exc:
            raise GateError("generated regression contract path is unsafe") from exc
        contract = {
            "schemaVersion": 1,
            "requestId": payload["request_id"],
            "patchId": str(report["patchId"]),
            "assertions": payload["regression_contract"],
        }
        planned[contract_path] = (json.dumps(contract, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        report["regressionContractFile"] = str(contract_path.relative_to(ROOT)).replace("\\", "/")
    return planned, report


def apply_planned(planned: dict[Path, bytes]) -> None:
    module_patch.apply(planned)
    builder.check(builder.DEFAULT_MANIFEST)


def strip_preview_banner(html: str) -> str:
    html = re.sub(
        re.escape(PREVIEW_MARKER_START) + r".*?" + re.escape(PREVIEW_MARKER_END),
        "",
        html,
        flags=re.I | re.S,
    )
    return re.sub(
        r'\s*<div\b[^>]*\bid=(["\'])kgg-gpt-preview-banner\1[^>]*>.*?</div>',
        "",
        html,
        flags=re.I | re.S,
    )


def inject_preview_banner(html: str, payload: dict[str, Any], digest: str) -> str:
    request_id = payload["request_id"]
    title = clean_ascii(str(payload.get("title") or request_id), request_id, 120)
    escaped_request = escape_html(request_id, quote=True)
    escaped_title = escape_html(title, quote=True)
    escaped_digest = escape_html(digest, quote=True)
    short_digest = escaped_digest[:4]
    banner = (
        PREVIEW_MARKER_START
        + "\n"
        + '<div id="kgg-gpt-preview-banner" data-kgg-preview-marker="compact-v2" '
        + 'style="all:initial!important;position:fixed!important;'
        + 'top:max(6px,env(safe-area-inset-top,0px))!important;right:6px!important;'
        + 'bottom:auto!important;left:auto!important;z-index:2147483000!important;'
        + 'display:block!important;box-sizing:border-box!important;width:92px!important;'
        + 'min-width:92px!important;max-width:92px!important;height:24px!important;'
        + 'min-height:24px!important;max-height:24px!important;overflow:visible!important;'
        + 'pointer-events:none!important;contain:layout style!important">'
        + '<button id="kgg-gpt-preview-toggle" type="button" '
        + 'aria-controls="kgg-gpt-preview-details" aria-expanded="false" '
        + f'aria-label="KGG Test-Preview {short_digest}; Details anzeigen" '
        + 'style="all:initial!important;display:flex!important;box-sizing:border-box!important;'
        + 'width:92px!important;min-width:92px!important;max-width:92px!important;'
        + 'height:24px!important;min-height:24px!important;max-height:24px!important;'
        + 'align-items:center!important;justify-content:center!important;overflow:hidden!important;'
        + 'white-space:nowrap!important;background:#111827!important;color:#fff!important;'
        + 'padding:0 6px!important;border:0!important;border-radius:5px!important;'
        + 'font:700 10px/1 system-ui,sans-serif!important;letter-spacing:0!important;'
        + 'text-transform:none!important;-webkit-text-size-adjust:none!important;'
        + 'text-size-adjust:none!important;box-shadow:0 1px 4px rgba(0,0,0,.22)!important;'
        + 'opacity:.9!important;cursor:pointer!important;pointer-events:auto!important">'
        + f"TEST &middot; {short_digest}</button>"
        + '<div id="kgg-gpt-preview-details" role="status" aria-live="polite" '
        + 'style="all:initial!important;position:absolute!important;top:28px!important;right:0!important;'
        + 'display:none!important;box-sizing:border-box!important;width:320px!important;'
        + 'max-width:calc(100vw - 12px)!important;max-height:40vh!important;overflow:auto!important;'
        + 'background:#111827!important;color:#fff!important;padding:10px!important;'
        + 'border:1px solid rgba(255,255,255,.24)!important;border-radius:7px!important;'
        + 'font:12px/1.35 system-ui,sans-serif!important;letter-spacing:0!important;'
        + 'white-space:normal!important;overflow-wrap:anywhere!important;'
        + 'box-shadow:0 4px 16px rgba(0,0,0,.28)!important;pointer-events:auto!important">'
        + f'<strong style="all:initial!important;display:block!important;color:#fff!important;'
        + f'font:700 12px/1.35 system-ui,sans-serif!important">{escaped_title}</strong>'
        + f'<span style="all:initial!important;display:block!important;color:#dbeafe!important;'
        + f'font:11px/1.35 ui-monospace,monospace!important;margin-top:6px!important">{escaped_request}</span>'
        + f'<span style="all:initial!important;display:block!important;color:#cbd5e1!important;'
        + f'font:10px/1.35 ui-monospace,monospace!important;margin-top:4px!important">{escaped_digest}</span>'
        + "</div></div>"
        + '<script id="kgg-gpt-preview-banner-script">(function(){"use strict";'
        + 'var marker=document.getElementById("kgg-gpt-preview-banner");'
        + 'var toggle=document.getElementById("kgg-gpt-preview-toggle");'
        + 'var details=document.getElementById("kgg-gpt-preview-details");'
        + 'if(!marker||!toggle||!details)return;'
        + 'function setOpen(open){marker.dataset.open=open?"1":"0";'
        + 'toggle.setAttribute("aria-expanded",open?"true":"false");'
        + 'details.style.setProperty("display",open?"block":"none","important");}'
        + 'toggle.addEventListener("click",function(){setOpen(marker.dataset.open!=="1");});'
        + 'document.addEventListener("pointerdown",function(event){'
        + 'if(marker.dataset.open==="1"&&!marker.contains(event.target))setOpen(false);},true);'
        + 'document.addEventListener("keydown",function(event){'
        + 'if(event.key==="Escape"&&marker.dataset.open==="1"){setOpen(false);toggle.focus();}});'
        + "setOpen(false);})();</script>\n"
        + PREVIEW_MARKER_END
    )
    clean_html = strip_preview_banner(html)
    rendered, count = re.subn(r"(<body[^>]*>)", r"\1\n" + banner, clean_html, count=1, flags=re.I)
    if count != 1:
        fail("Preview HTML is missing a body element for the marker.")
    return rendered


def write_preview(preview_root: Path, html: str, payload: dict[str, Any], digest: str, report: dict[str, Any]) -> dict[str, Any]:
    request_id = payload["request_id"]
    rollout_code = int(os.environ.get("GITHUB_RUN_NUMBER") or int(time.time()))
    if rollout_code < 1_000_000_000:
        rollout_code = int(time.time())
    preview_dir = preview_root / "previews" / request_id
    preview_dir.mkdir(parents=True, exist_ok=True)
    html_path = preview_dir / "admin.html"
    meta_path = preview_dir / "meta.json"
    html_path.write_text(html, encoding="utf-8", newline="\n")
    meta = {
        "kind": "kgg_gpt_preview",
        "requestId": request_id,
        "patchHash": digest,
        "baseSha": git_sha(),
        "baseVersionCode": read_json(VERSION_PATH).get("versionCode"),
        "rolloutCode": rollout_code,
        "title": clean_ascii(str(payload.get("title") or request_id), request_id, 120),
        "summary": clean_ascii(str(payload.get("summary") or request_id), request_id, 220),
        "patchId": str(report["patchId"]),
        "patchFile": str(report["patchFile"]),
        "versionName": str(report["versionName"]),
        "createdAt": utc_now(),
        "url": f"{PREVIEW_BASE_URL}/{request_id}/admin.html",
        "sha256": hashlib.sha256(html.encode("utf-8")).hexdigest(),
    }
    write_json(meta_path, meta)

    index_path = preview_root / PREVIEW_INDEX
    if index_path.exists():
        index = read_json(index_path)
    else:
        index = {"kind": "kgg_gpt_preview_manifest", "version": 1, "previews": []}
    previews = [item for item in index.get("previews", []) if item.get("requestId") != request_id]
    previews.insert(0, meta)
    index["kind"] = "kgg_gpt_preview_manifest"
    index["version"] = 1
    index["latest"] = meta
    index["previews"] = previews[:20]
    write_json(index_path, index)
    return meta


def load_preview_meta(preview_root: Path, request_id: str) -> dict[str, Any]:
    meta_path = preview_root / "previews" / request_id / "meta.json"
    if not meta_path.exists():
        fail(f"missing preview meta for request_id {request_id}")
    return read_json(meta_path)


def next_release_id() -> str:
    numbers: set[int] = set()
    releases = ROOT / "therapist-app" / "releases" / "web"
    if releases.exists():
        for child in releases.iterdir():
            match = re.fullmatch(r"r([0-9]{3,8})", child.name)
            if child.is_dir() and match:
                numbers.add(int(match.group(1)))
    manifest = read_json(ROOT / "therapist-app" / "android_update_manifest.json")
    candidates = [manifest.get("latestWebVersion"), manifest.get("adminHtmlUrl"), manifest.get("colleagueHtmlUrl")]
    channels = manifest.get("channels") if isinstance(manifest.get("channels"), dict) else {}
    for channel in channels.values():
        if isinstance(channel, dict):
            candidates.append(channel.get("releaseId"))
            candidates.append(channel.get("url"))
    for value in candidates:
        for match in re.finditer(r"r([0-9]{3,8})", str(value or "")):
            numbers.add(int(match.group(1)))
    if not numbers:
        fail("cannot determine next release id")
    return f"r{max(numbers) + 1:04d}"


def write_github_output(path: str | None, values: dict[str, str]) -> None:
    if not path:
        return
    with open(path, "a", encoding="utf-8") as output:
        for key, value in values.items():
            if "\n" in value:
                output.write(f"{key}<<KGG_EOF\n{value}\nKGG_EOF\n")
            else:
                output.write(f"{key}={value}\n")


def verify_preview_acceptance(preview_root: Path, payload: dict[str, Any], digest: str) -> dict[str, Any]:
    meta = load_preview_meta(preview_root, payload["request_id"])
    if meta.get("patchHash") != digest:
        fail("patch_hash does not match the accepted preview")
    if meta.get("baseSha") != git_sha():
        fail("main has changed since preview; create a fresh preview before PR")
    return meta


def impact_outputs(payload: dict[str, Any]) -> dict[str, str]:
    cross_app = payload["protected_scope"] == CROSS_APP_SCOPE
    return {
        "run_camera_qr": str(cross_app).lower(),
        "run_patient_scan": str(cross_app).lower(),
        "run_ui_stability": str(cross_app).lower(),
    }


def run(
    payload: dict[str, Any],
    mode: str,
    preview_root: Path | None,
    github_output: str | None,
    approval_phrase: str = "",
) -> None:
    digest = patch_hash(payload)
    planned, report = plan_modular_patch(payload)

    if mode == "validate_only":
        write_github_output(
            github_output,
            {
                "request_id": payload["request_id"],
                "patch_hash": digest,
                "patch_id": str(report["patchId"]),
                "patch_file": str(report["patchFile"]),
                "version_name": str(report["versionName"]),
                "validation": "ok",
                **impact_outputs(payload),
            },
        )
        return

    if mode in {"create_pr", "publish_admin_beta"}:
        if approval_phrase.strip() != MAIN_APPROVAL_PHRASE:
            fail(f"{mode} requires Max's exact approval phrase: {MAIN_APPROVAL_PHRASE}")
        if preview_root is None:
            fail(f"--preview-root is required for {mode}")
        verify_preview_acceptance(preview_root, payload, digest)

    apply_planned(planned)
    versioned = SOURCE_PATH.read_text(encoding="utf-8")
    pipeline.validate_html(versioned, "Versioned modular GPT Admin HTML")

    if mode == "publish_preview":
        if preview_root is None:
            fail("--preview-root is required for publish_preview")
        preview_html = inject_preview_banner(versioned, payload, digest)
        meta = write_preview(preview_root, preview_html, payload, digest, report)
        write_github_output(
            github_output,
            {
                "request_id": payload["request_id"],
                "patch_hash": digest,
                "patch_id": str(report["patchId"]),
                "patch_file": str(report["patchFile"]),
                "preview_url": str(meta["url"]),
                "preview_sha256": str(meta["sha256"]),
                "rollout_code": str(meta["rolloutCode"]),
                **impact_outputs(payload),
            },
        )
        return

    if mode in {"create_pr", "publish_admin_beta"}:
        release = {
            "releaseId": next_release_id(),
            "versionName": str(report["versionName"]),
            "notes": f"v{str(report['versionCode']).zfill(3)}: {payload['summary']}",
        }
        (ROOT / "release-inbox").mkdir(exist_ok=True)
        (ROOT / "release-inbox" / "admin.html").write_text(versioned, encoding="utf-8", newline="\n")
        write_json(ROOT / "release-inbox" / "release.json", release)
        write_github_output(
            github_output,
            {
                "request_id": payload["request_id"],
                "patch_hash": digest,
                "patch_id": str(report["patchId"]),
                "patch_file": str(report["patchFile"]),
                "version_name": str(report["versionName"]),
                "release_id": str(release["releaseId"]),
                **impact_outputs(payload),
            },
        )
        return

    fail(f"unsupported mode: {mode}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply a guarded modular GPT patch for preview, PR or Admin beta.")
    parser.add_argument("--mode", required=True, choices=["validate_only", "publish_preview", "create_pr", "publish_admin_beta"])
    parser.add_argument("--payload-file", required=True, type=Path)
    parser.add_argument("--preview-root", type=Path)
    parser.add_argument("--github-output", default=os.environ.get("GITHUB_OUTPUT"))
    parser.add_argument("--approval-phrase", default="")
    args = parser.parse_args()

    try:
        payload = validate_payload(args.payload_file.read_text(encoding="utf-8-sig"))
        preview_root = args.preview_root.resolve() if args.preview_root else None
        run(payload, args.mode, preview_root, args.github_output, args.approval_phrase)
        print(f"KGG GPT write gate OK: {args.mode} {payload['request_id']} {patch_hash(payload)[:12]}")
        return 0
    except (GateError, pipeline.ReleaseError, module_patch.ScaffoldError, builder.BuildError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
