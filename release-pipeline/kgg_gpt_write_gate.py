#!/usr/bin/env python3
"""Guarded Custom GPT preview and PR payload handling for KGG."""

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
from typing import Any

import release_pipeline as pipeline


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "kgg-update" / "index.html"
VERSION_PATH = ROOT / "kgg-update" / "version.json"
PREVIEW_BASE_URL = "https://raw.githubusercontent.com/Kayus24/kgg/gpt-preview/previews"
PREVIEW_INDEX = "previews/index.json"
MAX_PAYLOAD_BYTES = 90_000
MAX_OPS = 10
MAX_TEXT_BYTES = 60_000

SECRET_PATTERN = re.compile(
    "("
    + "sk-" + "proj-"
    + r"|gh[pousr]_[A-Za-z0-9_]{20,}"
    + "|AI" + r"za[0-9A-Za-z_-]{25,}"
    + ")"
)
REQUEST_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{5,63}$")
SLUG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]{2,48}$")
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
    operations = payload.get("operations")
    return json.dumps({"operations": operations}, sort_keys=True, ensure_ascii=True, separators=(",", ":"))


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


def slugify(value: str, fallback: str) -> str:
    value = clean_ascii(value, fallback, 80).lower()
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    if not SLUG_PATTERN.fullmatch(value or ""):
        value = fallback
    return value[:48].rstrip("-")


def validate_payload(raw: str) -> dict[str, Any]:
    if len(raw.encode("utf-8")) > MAX_PAYLOAD_BYTES:
        fail("payload_json is too large")
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        fail(f"payload_json is invalid JSON: {exc}")
    if not isinstance(payload, dict):
        fail("payload_json must be an object")
    request_id = str(payload.get("request_id") or payload.get("requestId") or "").strip().lower()
    if not REQUEST_ID_PATTERN.fullmatch(request_id):
        fail("request_id must match [a-z0-9][a-z0-9-]{5,63}")
    payload["request_id"] = request_id
    operations = payload.get("operations")
    if not isinstance(operations, list) or not operations or len(operations) > MAX_OPS:
        fail(f"operations must contain 1..{MAX_OPS} items")
    for index, operation in enumerate(operations):
        if not isinstance(operation, dict):
            fail(f"operation {index} must be an object")
        path = operation.get("path")
        old = operation.get("old_text", operation.get("oldText"))
        new = operation.get("new_text", operation.get("newText"))
        if path != "kgg-update/index.html":
            fail("v1 only allows kgg-update/index.html")
        if not isinstance(old, str) or not old:
            fail(f"operation {index} requires non-empty old_text")
        if not isinstance(new, str):
            fail(f"operation {index} requires new_text")
        if len(old.encode("utf-8")) > MAX_TEXT_BYTES or len(new.encode("utf-8")) > MAX_TEXT_BYTES:
            fail(f"operation {index} is too large")
        combined = old + "\n" + new
        if SECRET_PATTERN.search(combined):
            fail(f"operation {index} contains a token-shaped secret")
        touched = [token for token in PROTECTED_TOKENS if token in combined]
        if touched:
            fail(f"operation {index} touches protected area tokens: {', '.join(touched)}")
        operation["old_text"] = old
        operation["new_text"] = new
    return payload


def apply_operations(source: str, payload: dict[str, Any]) -> str:
    result = source
    for index, operation in enumerate(payload["operations"]):
        old = operation["old_text"]
        count = result.count(old)
        if count != 1:
            fail(f"operation {index} old_text must match exactly once, found {count}")
        result = result.replace(old, operation["new_text"], 1)
    if result == source:
        fail("patch produced no changes")
    if SECRET_PATTERN.search(result):
        fail("patched HTML contains a token-shaped secret")
    pipeline.validate_html(result, "GPT patched Admin HTML")
    return result


def replace_json_scripts(html: str, version_code: int, version_name: str, patch_id: str, summary: str) -> str:
    def update_source_truth(match: re.Match[str]) -> str:
        data = json.loads(match.group(2))
        fixes = data.setdefault("activeFixes", [])
        slug = patch_id.removeprefix("kgg-v")
        if slug not in fixes:
            fixes.append(slug)
        data["currentVersion"] = {
            "versionCode": version_code,
            "versionName": version_name,
            "lastPatchId": patch_id,
            "updatedBy": "kgg-gpt-write-gate",
        }
        data["latestPatchId"] = patch_id
        data["lastUpdateIntent"] = {
            "id": patch_id,
            "summary": summary,
            "touched": ["kgg-update/index.html"],
            "notTouched": [
                "PDF",
                "QR/Patienten-App",
                "Scan/OCR",
                "Parser",
                "Plan-State",
                "Medien/Upload",
                "API-Key-Logik",
                "Android/APK",
                "Manifest",
            ],
        }
        return match.group(1) + json.dumps(data, ensure_ascii=False, indent=2) + match.group(3)

    html = re.sub(
        r'(<script type="application/json" id="kgg-source-truth">\s*)(.*?)(\s*</script>)',
        update_source_truth,
        html,
        flags=re.S,
    )

    def update_changelog(match: re.Match[str]) -> str:
        data = json.loads(match.group(2))
        data["latestVersionCode"] = version_code
        entries = data.setdefault("entries", [])
        entries.insert(
            0,
            {
                "versionCode": version_code,
                "versionName": version_name,
                "patchId": patch_id,
                "status": "active",
                "type": "kgg-gpt-write-gate",
                "title": summary,
                "reason": "Custom GPT preview was accepted by Max and routed through the guarded write gate.",
                "whatChanged": [summary],
                "touchedAreas": ["kgg-update/index.html"],
                "notTouched": [
                    "PDF",
                    "QR/Patienten-App",
                    "Scan/OCR",
                    "Parser",
                    "Plan-State",
                    "Medien/Upload",
                    "API-Key-Logik",
                    "Android/APK",
                    "Manifest",
                ],
                "testStatus": {
                    "local": "pending",
                    "github": "pending",
                    "notes": "Required Gate and release-pr validate-build must pass before merge.",
                },
            },
        )
        return match.group(1) + json.dumps(data, ensure_ascii=False, indent=2) + match.group(3)

    return re.sub(
        r'(<script type="application/json" id="kgg-changelog">\s*)(.*?)(\s*</script>)',
        update_changelog,
        html,
        count=1,
        flags=re.S,
    )


def bump_version(html: str, payload: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    current = read_json(VERSION_PATH)
    old_code = current.get("versionCode")
    if not isinstance(old_code, int):
        fail("version.json versionCode must be an integer")
    version_code = old_code + 1
    request_id = payload["request_id"]
    title = clean_ascii(str(payload.get("title") or payload.get("summary") or request_id), request_id, 72)
    slug = slugify(str(payload.get("version_slug") or payload.get("versionSlug") or title), f"gpt-{request_id[:12]}")
    version_name = f"1.0.{version_code}-{slug}"
    patch_id = f"kgg-v{version_code:03d}-{slug}"
    summary = clean_ascii(str(payload.get("summary") or title), title, 220)
    marker = f"KGG_GITHUB_UPDATE_v{version_code:03d}_{slug.replace('-', '_')}"
    build_time = utc_now()

    html = replace_json_scripts(html, version_code, version_name, patch_id, summary)
    html = re.sub(r"<title>.*?</title>", f"<title>KGG Update v{version_code:03d} {title}</title>", html, count=1, flags=re.S | re.I)
    html = re.sub(r"const VERSION='KGG_GITHUB_UPDATE_v[0-9]+_[^']+';", f"const VERSION='{marker}';", html, count=1)
    html = re.sub(
        r"const KGG_BUILD_INFO=\{[^}]+\};",
        f"const KGG_BUILD_INFO={{release:'v{version_code:03d}',buildTime:'{build_time}',buildCode:'github-update-v{version_code:03d}-{slug}',htmlFile:'kgg-update/index.html'}};",
        html,
        count=1,
    )
    pipeline.validate_html(html, "Versioned GPT patched Admin HTML")
    version = dict(current)
    version.update(
        {
            "versionCode": version_code,
            "versionName": version_name,
            "indexUrl": f"index.html?v={version_code}",
            "sha256": hashlib.sha256(html.encode("utf-8")).hexdigest(),
            "notes": f"v{version_code:03d}: {summary}",
        }
    )
    return html, version


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


def write_preview(preview_root: Path, html: str, payload: dict[str, Any], digest: str) -> dict[str, Any]:
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


def run(payload: dict[str, Any], mode: str, preview_root: Path | None, github_output: str | None) -> None:
    digest = patch_hash(payload)
    source = SOURCE_PATH.read_text(encoding="utf-8")
    patched = apply_operations(source, payload)
    versioned, version_json = bump_version(patched, payload)
    if mode == "validate_only":
        write_github_output(
            github_output,
            {
                "request_id": payload["request_id"],
                "patch_hash": digest,
                "version_name": str(version_json["versionName"]),
                "validation": "ok",
            },
        )
        return

    SOURCE_PATH.write_text(versioned, encoding="utf-8", newline="\n")
    write_json(VERSION_PATH, version_json)

    if mode == "publish_preview":
        if preview_root is None:
            fail("--preview-root is required for publish_preview")
        preview_html = inject_preview_banner(versioned, payload, digest)
        meta = write_preview(preview_root, preview_html, payload, digest)
        write_github_output(
            github_output,
            {
                "request_id": payload["request_id"],
                "patch_hash": digest,
                "preview_url": str(meta["url"]),
                "preview_sha256": str(meta["sha256"]),
                "rollout_code": str(meta["rolloutCode"]),
            },
        )
        return

    if mode == "create_pr":
        if preview_root is None:
            fail("--preview-root is required for create_pr")
        meta = load_preview_meta(preview_root, payload["request_id"])
        if meta.get("patchHash") != digest:
            fail("patch_hash does not match the accepted preview")
        if meta.get("baseSha") != git_sha():
            fail("main has changed since preview; create a fresh preview before PR")
        release = {
            "releaseId": next_release_id(),
            "versionName": version_json["versionName"],
            "notes": version_json["notes"],
        }
        (ROOT / "release-inbox").mkdir(exist_ok=True)
        (ROOT / "release-inbox" / "admin.html").write_text(versioned, encoding="utf-8", newline="\n")
        write_json(ROOT / "release-inbox" / "release.json", release)
        write_github_output(
            github_output,
            {
                "request_id": payload["request_id"],
                "patch_hash": digest,
                "version_name": str(version_json["versionName"]),
                "release_id": str(release["releaseId"]),
            },
        )
        return

    fail(f"unsupported mode: {mode}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply a guarded GPT patch for preview or PR.")
    parser.add_argument("--mode", required=True, choices=["validate_only", "publish_preview", "create_pr"])
    parser.add_argument("--payload-file", required=True, type=Path)
    parser.add_argument("--preview-root", type=Path)
    parser.add_argument("--github-output", default=os.environ.get("GITHUB_OUTPUT"))
    args = parser.parse_args()

    try:
        payload = validate_payload(args.payload_file.read_text(encoding="utf-8"))
        preview_root = args.preview_root.resolve() if args.preview_root else None
        run(payload, args.mode, preview_root, args.github_output)
        print(f"KGG GPT write gate OK: {args.mode} {payload['request_id']} {patch_hash(payload)[:12]}")
        return 0
    except (GateError, pipeline.ReleaseError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
