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
MAX_PAYLOAD_BYTES = 120_000
MAX_CONTENT_BYTES = 80_000

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


def validate_patch_content(content: str) -> str:
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
    touched = [token for token in PROTECTED_TOKENS if token in normalized]
    if touched:
        fail("patch_content touches protected area tokens: " + ", ".join(touched))
    try:
        module_patch.render_patch_module("kgg-v999-self-test", "GPT content validation", normalized).decode("utf-8", errors="strict")
    except UnicodeError as exc:
        fail(f"patch_content must be valid UTF-8 text: {exc}")
    return normalized


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
    patch_content = validate_patch_content(payload.get("patch_content") or payload.get("patchContent"))

    protected_norm = {normalize_area(area): area for area in module_patch.PROTECTED_AREAS}
    selected_protected = [protected_norm[normalize_area(area)] for area in touched_areas if normalize_area(area) in protected_norm]
    if selected_protected:
        fail("protected touched_areas require explicit Max approval outside the GPT gate: " + ", ".join(selected_protected))

    combined_text = json.dumps(
        {
            "title": title,
            "summary": summary,
            "version_slug": version_slug,
            "touched_areas": touched_areas,
            "required_tests": required_tests,
            "patch_content": patch_content,
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
    }


def plan_modular_patch(payload: dict[str, Any]) -> tuple[dict[Path, bytes], dict[str, Any]]:
    args = SimpleNamespace(
        slug=payload["version_slug"],
        title=payload["title"],
        summary=payload["summary"],
        area=payload["touched_areas"],
        version_name=None,
        allow_protected=False,
        allow_changelog_overflow=True,
        approval_note="Gate-managed Custom GPT module patch; Max approved modular GPT migration with existing embedded changelog overflow.",
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
    return planned, report


def apply_planned(planned: dict[Path, bytes]) -> None:
    module_patch.apply(planned)
    builder.check(builder.DEFAULT_MANIFEST)


def inject_preview_banner(html: str, payload: dict[str, Any], digest: str) -> str:
    request_id = payload["request_id"]
    summary = clean_ascii(str(payload.get("summary") or payload.get("title") or request_id), request_id, 180)
    banner = (
        '<div id="kgg-gpt-preview-banner" style="position:sticky;top:0;z-index:999999;'
        'background:#111827;color:#fff;padding:8px 12px;font:13px system-ui;'
        'box-shadow:0 2px 10px rgba(0,0,0,.22)">'
        f'KGG PREVIEW | {request_id} | {digest[:12]} | {summary}'
        "</div>"
    )
    if 'id="kgg-gpt-preview-banner"' in html:
        return html
    return re.sub(r"(<body[^>]*>)", r"\1\n" + banner, html, count=1, flags=re.I)


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


def run(payload: dict[str, Any], mode: str, preview_root: Path | None, github_output: str | None) -> None:
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
            },
        )
        return

    if mode in {"create_pr", "publish_admin_beta"}:
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
    args = parser.parse_args()

    try:
        payload = validate_payload(args.payload_file.read_text(encoding="utf-8-sig"))
        preview_root = args.preview_root.resolve() if args.preview_root else None
        run(payload, args.mode, preview_root, args.github_output)
        print(f"KGG GPT write gate OK: {args.mode} {payload['request_id']} {patch_hash(payload)[:12]}")
        return 0
    except (GateError, pipeline.ReleaseError, module_patch.ScaffoldError, builder.BuildError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
