#!/usr/bin/env python3
"""Guarded Custom GPT patch gate for the KGG patient PWA."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PREVIEW_BASE_URL = "https://kayus24.github.io/kgg-patient-preview/previews"
PREVIEW_INDEX = Path("previews/index.json")
MAX_PAYLOAD_BYTES = 60_000
MAX_OPERATIONS = 4
MAX_REPLACEMENT_BYTES = 40_000
PATIENT_APPROVAL_PHRASE = "Gut für PAT live"

VERSION_MARKERS = (
    "const APP_VERSION",
    "const CACHE_NAME",
    "const RELEASE",
    "VERSION_LABEL_SCRIPT",
    "patient-version-label.js?v=",
)
INTERFACE_MARKERS = (
    "KGGH2",
    "KGGD1",
    "kggCurrentPlanV1",
    "localStorage",
    "sessionStorage",
    "indexedDB",
    "decodeKggH2PlanCode",
    "parseQueryPlan",
    "parseHash",
    "showQr(",
)
FORBIDDEN_NEW_SINKS = (
    "eval(",
    "new Function",
    "document.write(",
    "fetch(",
    "XMLHttpRequest",
    "sendBeacon(",
    "WebSocket(",
)
SECRET_PATTERNS = (
    re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"AIza[0-9A-Za-z_-]{20,}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)
RUNTIME_EXACT = {
    "index.html",
    "service-worker.js",
    "update-recovery.html",
    "manifest.json",
    "collapse-cards.js",
    "numpad-ui-fix.js",
}
MODULE_SCRIPT_PATTERN = re.compile(r'<script src="(?P<src>\./[^"?]+\.js(?:\?[^"?]+)?)"></script>')
DIRECT_FIRST_LOAD_MODULES = (
    "patient-plan-link-choice.js",
    "collapse-cards.js",
    "patient-card-progress.js",
    "patient-install-guide.js",
    "patient-install-prompt.js",
    "patient-plan-replace-slot-fix.js",
    "patient-start-scan.js",
    "patient-multiplan-db.js",
    "patient-plan-delete.js",
    "patient-card-settings.js",
    "patient-start-values-day1.js",
    "patient-day-history.js",
    "patient-media-retry-cache_v2.js",
    "patient-ui-micro-polish.js",
    "patient-pain-vertical-scale.js",
    "numpad-ui-fix.js",
    "patient-numpad-visibility-fix.js",
    "patient-extra-info-display.js",
    "patient-last-value-hints.js",
    "patient-set-summary-groups.js",
    "patient-qr-fullscreen.js",
    "patient-numpad-card-guard.js",
    "patient-version-label.js",
)


class GateError(RuntimeError):
    """Raised when a patient GPT payload is unsafe or stale."""


def fail(message: str) -> None:
    raise GateError(message)


def normalize(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def clean_slug(value: Any) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", str(value or "").lower()).strip("-")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,47}", slug):
        fail("version_slug must contain 3-48 lowercase ASCII letters, digits or hyphens")
    return slug


def clean_request_id(value: Any) -> str:
    request_id = str(value or "").strip().lower()
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{5,63}", request_id):
        fail("request_id must contain 6-64 lowercase ASCII letters, digits or hyphens")
    return request_id


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def git_sha(root: Path = ROOT) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        text=True,
        capture_output=True,
    )
    return result.stdout.strip()


def allowed_patient_path(relative: str) -> bool:
    if relative in RUNTIME_EXACT:
        return True
    if re.fullmatch(r"patient-[a-z0-9_-]+\.js", relative):
        return True
    if re.fullmatch(r"manifest-v[0-9]+\.webmanifest", relative):
        return True
    return False


def safe_path(root: Path, relative: str) -> Path:
    if not allowed_patient_path(relative):
        fail(f"path is outside the patient PWA allowlist: {relative}")
    target = (root / relative).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError:
        fail(f"path escapes repository root: {relative}")
    if not target.is_file():
        fail(f"patient PWA file does not exist: {relative}")
    return target


def contains_secret(text: str) -> bool:
    return any(pattern.search(text) for pattern in SECRET_PATTERNS)


def requires_patient_scan(payload: dict[str, Any]) -> bool:
    return payload["risk_class"] == "interface" or any(
        operation["path"] == "patient-start-scan.js"
        for operation in payload["operations"]
    )


def payload_hash(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def load_payload(path: Path, root: Path = ROOT) -> dict[str, Any]:
    raw = path.read_bytes()
    if len(raw) > MAX_PAYLOAD_BYTES:
        fail(f"payload exceeds {MAX_PAYLOAD_BYTES} bytes")
    try:
        data = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        fail(f"payload is not valid UTF-8 JSON: {exc}")
    if not isinstance(data, dict):
        fail("payload must be a JSON object")
    return validate_payload(data, root)


def validate_payload(data: dict[str, Any], root: Path = ROOT) -> dict[str, Any]:
    allowed_keys = {
        "request_id",
        "base_sha",
        "title",
        "summary",
        "version_slug",
        "risk_class",
        "touched_areas",
        "required_tests",
        "operations",
    }
    unexpected = sorted(set(data) - allowed_keys)
    if unexpected:
        fail("unexpected payload fields: " + ", ".join(unexpected))

    request_id = clean_request_id(data.get("request_id"))
    base_sha = str(data.get("base_sha") or "").strip().lower()
    if not re.fullmatch(r"[0-9a-f]{40}", base_sha):
        fail("base_sha must be a full 40-character Git SHA")
    current_sha = git_sha(root)
    if base_sha != current_sha:
        fail(f"base_sha is stale: payload={base_sha}, current={current_sha}")

    title = str(data.get("title") or "").strip()
    summary = str(data.get("summary") or "").strip()
    if not 5 <= len(title) <= 120:
        fail("title must contain 5-120 characters")
    if not 10 <= len(summary) <= 500:
        fail("summary must contain 10-500 characters")
    if any(character in title + summary for character in ("\r", "\n", "\0")):
        fail("title and summary must be single-line text")
    if contains_secret(title + "\n" + summary):
        fail("title or summary contains a token-shaped secret")

    risk_class = str(data.get("risk_class") or "standard").strip().lower()
    if risk_class not in {"standard", "interface"}:
        fail("risk_class must be standard or interface")

    touched_areas = data.get("touched_areas")
    required_tests = data.get("required_tests")
    if not isinstance(touched_areas, list) or not 1 <= len(touched_areas) <= 12:
        fail("touched_areas must be a non-empty array")
    if not isinstance(required_tests, list) or not 1 <= len(required_tests) <= 12:
        fail("required_tests must be a non-empty array")
    touched_areas = [str(item).strip() for item in touched_areas if str(item).strip()]
    required_tests = [str(item).strip() for item in required_tests if str(item).strip()]
    if not touched_areas or not required_tests:
        fail("touched_areas and required_tests must not contain only empty values")
    for label, values in (("touched_areas", touched_areas), ("required_tests", required_tests)):
        if any(
            len(value) > 160
            or any(character in value for character in ("\r", "\n", "\0"))
            or contains_secret(value)
            for value in values
        ):
            fail(f"{label} contains an unsafe or overlong value")

    operations = data.get("operations")
    if not isinstance(operations, list) or not 1 <= len(operations) <= MAX_OPERATIONS:
        fail(f"operations must contain 1-{MAX_OPERATIONS} replace_exact operations")

    normalized_operations: list[dict[str, str]] = []
    interface_change = False
    seen_paths: set[str] = set()
    for index, item in enumerate(operations):
        if not isinstance(item, dict):
            fail(f"operation {index + 1} must be an object")
        if set(item) != {"type", "path", "old_sha256", "old_text", "new_text"}:
            fail(
                f"operation {index + 1} must contain only "
                "type, path, old_sha256, old_text and new_text"
            )
        if item.get("type") != "replace_exact":
            fail(f"operation {index + 1} type must be replace_exact")
        relative = str(item.get("path") or "").replace("\\", "/").strip()
        if "/" in relative or relative in seen_paths:
            fail(f"operation {index + 1} path must be one unique root patient file")
        seen_paths.add(relative)
        target = safe_path(root, relative)
        source = normalize(target.read_text(encoding="utf-8"))
        expected_sha = str(item.get("old_sha256") or "").lower()
        if not re.fullmatch(r"[0-9a-f]{64}", expected_sha):
            fail(f"operation {index + 1} old_sha256 must be a SHA-256 digest")
        actual_sha = sha256_text(source)
        if expected_sha != actual_sha:
            fail(
                f"operation {index + 1} source hash is stale for {relative}: "
                f"payload={expected_sha}, current={actual_sha}"
            )
        old_text = normalize(str(item.get("old_text") or ""))
        new_text = normalize(str(item.get("new_text") or ""))
        if not old_text:
            fail(f"operation {index + 1} old_text must not be empty")
        if old_text == new_text:
            fail(f"operation {index + 1} is a no-op")
        if len(old_text.encode("utf-8")) + len(new_text.encode("utf-8")) > MAX_REPLACEMENT_BYTES:
            fail(f"operation {index + 1} replacement is too large")
        if source.count(old_text) != 1:
            fail(
                f"operation {index + 1} old_text must match exactly once in {relative}; "
                f"found {source.count(old_text)}"
            )
        combined = old_text + "\n" + new_text
        if any(marker in combined for marker in VERSION_MARKERS):
            fail(f"operation {index + 1} tries to edit gate-owned version metadata")
        if contains_secret(combined):
            fail(f"operation {index + 1} contains a token-shaped secret")
        if "localStorage.clear" in new_text or "sessionStorage.clear" in new_text:
            fail(f"operation {index + 1} may not clear patient storage")
        for sink in FORBIDDEN_NEW_SINKS:
            if new_text.count(sink) > old_text.count(sink):
                fail(f"operation {index + 1} may not introduce the security-sensitive sink {sink}")
        if any(marker in combined for marker in INTERFACE_MARKERS):
            interface_change = True
        normalized_operations.append(
            {
                "type": "replace_exact",
                "path": relative,
                "old_sha256": expected_sha,
                "old_text": old_text,
                "new_text": new_text,
            }
        )

    if interface_change and risk_class != "interface":
        fail("QR/hash/storage interface markers require risk_class=interface")
    if any(operation["path"] == "patient-start-scan.js" for operation in normalized_operations):
        if "patient-camera" not in touched_areas:
            fail("patient-start-scan.js changes require touched_areas to include patient-camera")
        if "patient-scan" not in required_tests:
            fail("patient-start-scan.js changes require required_tests to include patient-scan")

    return {
        "request_id": request_id,
        "base_sha": base_sha,
        "title": title,
        "summary": summary,
        "version_slug": clean_slug(data.get("version_slug")),
        "risk_class": risk_class,
        "touched_areas": touched_areas,
        "required_tests": required_tests,
        "operations": normalized_operations,
    }


def apply_operations(payload: dict[str, Any], root: Path = ROOT) -> list[str]:
    changed: list[str] = []
    for operation in payload["operations"]:
        target = safe_path(root, operation["path"])
        source = normalize(target.read_text(encoding="utf-8"))
        updated = source.replace(operation["old_text"], operation["new_text"], 1)
        target.write_text(updated, encoding="utf-8", newline="\n")
        changed.append(operation["path"])
    return changed


def bump_patient_version(payload: dict[str, Any], root: Path = ROOT) -> int:
    service_path = root / "service-worker.js"
    index_path = root / "index.html"
    label_path = root / "patient-version-label.js"
    recovery_path = root / "update-recovery.html"
    service = normalize(service_path.read_text(encoding="utf-8"))
    index = normalize(index_path.read_text(encoding="utf-8-sig"))
    label = normalize(label_path.read_text(encoding="utf-8"))
    recovery = normalize(recovery_path.read_text(encoding="utf-8"))
    match = re.search(r"const APP_VERSION = '([0-9]+)';", service)
    if not match:
        fail("service-worker.js is missing APP_VERSION")
    current = int(match.group(1))
    next_version = current + 1
    slug = payload["version_slug"]

    service, app_count = re.subn(
        r"const APP_VERSION = '[0-9]+';",
        f"const APP_VERSION = '{next_version}';",
        service,
        count=1,
    )
    service, cache_count = re.subn(
        r"const CACHE_NAME = 'kgg-handyplan-v[0-9]+-[a-z0-9-]+';",
        f"const CACHE_NAME = 'kgg-handyplan-v{next_version}-{slug}';",
        service,
        count=1,
    )
    service, script_count = re.subn(
        r"patient-version-label\.js\?v=[0-9]+",
        f"patient-version-label.js?v={next_version}",
        service,
    )
    index, index_script_count = re.subn(
        r"patient-version-label\.js\?v=[0-9]+",
        f"patient-version-label.js?v={next_version}",
        index,
    )
    label, label_count = re.subn(
        r"const RELEASE='[0-9]+';",
        f"const RELEASE='{next_version}';",
        label,
        count=1,
    )
    recovery, recovery_count = re.subn(
        r"const RELEASE='[0-9]+';",
        f"const RELEASE='{next_version}';",
        recovery,
        count=1,
    )
    if (
        (app_count, cache_count, label_count, recovery_count) != (1, 1, 1, 1)
        or script_count < 1
        or index_script_count != 1
    ):
        fail("patient version markers are incomplete or ambiguous")

    service_path.write_text(service, encoding="utf-8", newline="\n")
    index_path.write_text(index, encoding="utf-8", newline="\n")
    label_path.write_text(label, encoding="utf-8", newline="\n")
    recovery_path.write_text(recovery, encoding="utf-8", newline="\n")

    changelog_path = root / "CHANGELOG_PATIENT_APP.md"
    changelog = normalize(changelog_path.read_text(encoding="utf-8"))
    entry = (
        f"## v{next_version} - {datetime.now(timezone.utc).date().isoformat()}\n\n"
        f"- {payload['summary']}\n"
        f"- Guarded request: `{payload['request_id']}`.\n\n"
    )
    if changelog.startswith("# Patient App Changelog\n"):
        changelog = changelog.replace(
            "# Patient App Changelog\n",
            "# Patient App Changelog\n\n" + entry,
            1,
        )
    else:
        fail("CHANGELOG_PATIENT_APP.md has an unexpected heading")
    changelog_path.write_text(changelog, encoding="utf-8", newline="\n")
    return next_version


def patient_runtime_files(root: Path = ROOT) -> list[Path]:
    files: set[Path] = {
        root / "index.html",
        root / "service-worker.js",
        root / "update-recovery.html",
        root / "icon.svg",
    }
    for pattern in ("*.js", "manifest*.json", "manifest*.webmanifest", "kgg-icon-*.png"):
        files.update(path for path in root.glob(pattern) if path.is_file())
    return sorted(files)


def canonical_direct_first_load_modules(
    html: str, worker: str, runtime_root: Path = ROOT
) -> list[str]:
    """Require the direct root document module contract used on first visit."""
    sources = [match.group("src") for match in MODULE_SCRIPT_PATTERN.finditer(html)]
    paths = [source.split("?", 1)[0].removeprefix("./") for source in sources]
    if paths != list(DIRECT_FIRST_LOAD_MODULES):
        fail("patient preview index.html must expose the exact direct first-load module list")
    if len(paths) != len(set(paths)):
        fail("patient preview direct first-load module list contains duplicate scripts")
    missing = [relative for relative in paths if not (runtime_root / relative).is_file()]
    if missing:
        fail("patient preview direct first-load module files are missing: " + ", ".join(missing))
    if "html=html.replace('</body>'" in worker:
        fail("service-worker.js must not inject patient modules after first load")
    if not re.search(r"function\s+injectModules\(response\)\{return\s+response\}", worker):
        fail("service-worker.js must retain the direct first-load no-op module delivery")
    worker_version = re.search(r"const APP_VERSION = '([0-9]+)';", worker)
    version_source = next((source for source in sources if source.startswith("./patient-version-label.js?v=")), "")
    if not worker_version or version_source != f"./patient-version-label.js?v={worker_version.group(1)}":
        fail("patient preview direct version-label module does not match service-worker APP_VERSION")
    return sources


def synthetic_plan_query() -> str:
    plan = {
        "i": "kgg-patient-preview",
        "t": "KGG synthetischer Testplan",
        "v": 1,
        "d": 6,
        "e": [
            ["Beinpresse", 2, "B", "kg", "Wdh", "40", "10"],
            ["Rudern", 2, "LR", "kg", "Wdh", "15", "12"],
        ],
    }
    encoded = base64.urlsafe_b64encode(
        json.dumps(plan, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    ).decode("ascii").rstrip("=")
    return "KGGH2:" + encoded


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def write_preview(
    preview_root: Path,
    payload: dict[str, Any],
    digest: str,
    version: int,
    root: Path = ROOT,
) -> dict[str, Any]:
    request_id = payload["request_id"]
    preview_dir = preview_root / "previews" / request_id
    created_at = ""
    previous_meta_path = preview_dir / "meta.json"
    if previous_meta_path.is_file():
        try:
            previous_meta = json.loads(previous_meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            previous_meta = {}
        if (
            previous_meta.get("patchHash") == digest
            and previous_meta.get("baseSha") == payload["base_sha"]
        ):
            created_at = str(previous_meta.get("createdAt") or "")
    if preview_dir.exists():
        shutil.rmtree(preview_dir)
    preview_dir.mkdir(parents=True)
    for source in patient_runtime_files(root):
        shutil.copy2(source, preview_dir / source.name)
    (preview_dir / ".nojekyll").write_text("", encoding="utf-8")
    preview_index_path = preview_dir / "index.html"
    preview_index = normalize(preview_index_path.read_text(encoding="utf-8-sig"))
    preview_index, robots_count = preview_index.replace(
        "<head>",
        '<head><meta name="robots" content="noindex,nofollow,noarchive">',
        1,
    ), preview_index.count("<head>")
    if robots_count != 1:
        fail("patient preview could not add its noindex policy")
    preview_worker_path = preview_dir / "service-worker.js"
    preview_worker = normalize(preview_worker_path.read_text(encoding="utf-8"))
    preview_cache_prefix = f"kgg-patient-preview-{request_id}-"
    preview_cache_name = f"{preview_cache_prefix}v{version}"
    preview_worker, cache_name_count = re.subn(
        r"const CACHE_NAME = 'kgg-handyplan-v[0-9]+-[a-z0-9-]+';",
        f"const CACHE_NAME = '{preview_cache_name}';",
        preview_worker,
        count=1,
    )
    preview_worker, index_scope_count = re.subn(
        r"function isIndexRequest\(request\)\{[^}]+\}",
        "function isIndexRequest(request){const url=new URL(request.url);"
        "if(url.origin!==self.location.origin)return false;"
        "const scopePath=new URL(self.registration.scope).pathname;"
        "return url.pathname===scopePath||url.pathname===scopePath+'index.html'}",
        preview_worker,
        count=1,
    )
    preview_worker, recovery_scope_count = re.subn(
        r"function isRecoveryRequest\(request\)\{[^}]+\}",
        "function isRecoveryRequest(request){const url=new URL(request.url);"
        "if(url.origin!==self.location.origin)return false;"
        "const scopePath=new URL(self.registration.scope).pathname;"
        "return url.pathname===scopePath+'update-recovery.html'}",
        preview_worker,
        count=1,
    )
    if (cache_name_count, index_scope_count, recovery_scope_count) != (1, 1, 1):
        fail("patient preview could not isolate the service-worker scope")
    canonical_direct_first_load_modules(preview_index, preview_worker, preview_dir)
    preview_index_path.write_text(preview_index, encoding="utf-8", newline="\n")
    preview_worker_path.write_text(preview_worker, encoding="utf-8", newline="\n")
    preview_recovery_path = preview_dir / "update-recovery.html"
    preview_recovery = normalize(preview_recovery_path.read_text(encoding="utf-8"))
    preview_recovery, recovery_cache_count = re.subn(
        r"const CACHE_PREFIX='kgg-handyplan-';",
        f"const CACHE_PREFIX='{preview_cache_prefix}';",
        preview_recovery,
        count=1,
    )
    if recovery_cache_count != 1:
        fail("patient preview could not isolate its recovery cache")
    preview_recovery_path.write_text(preview_recovery, encoding="utf-8", newline="\n")

    plan = synthetic_plan_query()
    url = f"{PREVIEW_BASE_URL}/{request_id}/?plan={plan}"
    meta = {
        "kind": "kgg_patient_gpt_preview",
        "requestId": request_id,
        "patchHash": digest,
        "baseSha": payload["base_sha"],
        "patientVersion": version,
        "riskClass": payload["risk_class"],
        "title": payload["title"],
        "summary": payload["summary"],
        "createdAt": created_at or datetime.now(timezone.utc).isoformat(),
        "url": url,
        "recoveryUrl": f"{PREVIEW_BASE_URL}/{request_id}/update-recovery.html?auto=1&v={version}",
        "previewScopePatched": True,
        "previewCacheName": preview_cache_name,
        "firstLoadModules": True,
    }
    write_json(preview_dir / "meta.json", meta)
    index_path = preview_root / PREVIEW_INDEX
    if index_path.exists():
        try:
            index = json.loads(index_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            index = {}
    else:
        index = {}
    previews = [
        item
        for item in index.get("previews", [])
        if isinstance(item, dict) and item.get("requestId") != request_id
    ]
    previews.insert(0, meta)
    write_json(
        index_path,
        {
            "kind": "kgg_patient_gpt_preview_index",
            "version": 1,
            "latest": meta,
            "previews": previews[:20],
        },
    )
    return meta


def verify_preview(
    preview_root: Path,
    payload: dict[str, Any],
    digest: str,
    root: Path = ROOT,
) -> dict[str, Any]:
    meta_path = preview_root / "previews" / payload["request_id"] / "meta.json"
    if not meta_path.is_file():
        fail(f"matching patient preview is missing for {payload['request_id']}")
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    if meta.get("patchHash") != digest:
        fail("patient preview patchHash differs from the requested payload")
    if meta.get("baseSha") != payload["base_sha"]:
        fail("patient preview baseSha differs from the requested payload")
    preview_dir = meta_path.parent
    preview_html_path = preview_dir / "index.html"
    preview_worker_path = preview_dir / "service-worker.js"
    if meta.get("firstLoadModules") is not True or not preview_html_path.is_file() or not preview_worker_path.is_file():
        fail("patient preview is missing first-load module evidence; publish a fresh preview")
    preview_html = normalize(preview_html_path.read_text(encoding="utf-8-sig"))
    preview_worker = normalize(preview_worker_path.read_text(encoding="utf-8"))
    canonical_direct_first_load_modules(preview_html, preview_worker, preview_dir)
    if payload["base_sha"] != git_sha(root):
        fail("main changed after patient preview; start again with validate_only")
    return meta


def write_github_output(path: str | None, values: dict[str, str]) -> None:
    if not path:
        return
    with open(path, "a", encoding="utf-8") as output:
        for key, value in values.items():
            output.write(f"{key}={value}\n")


def run(
    payload: dict[str, Any],
    mode: str,
    preview_root: Path | None,
    github_output: str | None,
    root: Path = ROOT,
    approval_phrase: str = "",
) -> None:
    digest = payload_hash(payload)
    accepted_preview: dict[str, Any] | None = None
    if mode in {"create_pr", "publish_patient_live"}:
        if approval_phrase.strip() != PATIENT_APPROVAL_PHRASE:
            fail(f"{mode} requires Max's exact approval phrase: {PATIENT_APPROVAL_PHRASE}")
        if preview_root is None:
            fail(f"--preview-root is required for {mode}")
        accepted_preview = verify_preview(preview_root, payload, digest, root)

    with tempfile.TemporaryDirectory(prefix="kgg-patient-gate-") as temp_dir:
        temp_root = Path(temp_dir) / "candidate"
        temp_root.mkdir()
        for source in root.iterdir():
            if source.is_file():
                shutil.copy2(source, temp_root / source.name)
        changed = apply_operations(payload, temp_root)
        version = bump_patient_version(payload, temp_root)

        if mode == "validate_only":
            write_github_output(
                github_output,
                {
                    "request_id": payload["request_id"],
                    "patch_hash": digest,
                    "patient_version": str(version),
                    "risk_class": payload["risk_class"],
                    "run_patient_scan": str(requires_patient_scan(payload)).lower(),
                    "validation": "ok",
                },
            )
            return

        for relative in sorted(
            set(
                changed
                + [
                    "index.html",
                    "service-worker.js",
                    "patient-version-label.js",
                    "update-recovery.html",
                    "CHANGELOG_PATIENT_APP.md",
                ]
            )
        ):
            source = temp_root / relative
            target = root / relative
            target.write_bytes(source.read_bytes())

    values = {
        "request_id": payload["request_id"],
        "patch_hash": digest,
        "patient_version": str(version),
        "risk_class": payload["risk_class"],
        "run_patient_scan": str(requires_patient_scan(payload)).lower(),
    }
    if mode == "publish_preview":
        if preview_root is None:
            fail("--preview-root is required for publish_preview")
        meta = write_preview(preview_root, payload, digest, version, root)
        values["preview_url"] = str(meta["url"])
        values["recovery_url"] = str(meta["recoveryUrl"])
    elif accepted_preview is not None:
        values["preview_url"] = str(accepted_preview["url"])
        values["recovery_url"] = str(accepted_preview["recoveryUrl"])
    write_github_output(github_output, values)


def self_test(root: Path = ROOT, preview_output: Path | None = None) -> None:
    sample_path = root / "patient-card-progress.js"
    source = normalize(sample_path.read_text(encoding="utf-8"))
    old_text = source.splitlines()[0] + "\n"
    payload = {
        "request_id": "patient-gate-self-test",
        "base_sha": git_sha(root),
        "title": "Patient Gate self test",
        "summary": "Validates the patient replace-exact contract without writing files.",
        "version_slug": "gate-self-test",
        "risk_class": "standard",
        "touched_areas": ["patient-ui"],
        "required_tests": ["patient-gate-self-test"],
        "operations": [
            {
                "type": "replace_exact",
                "path": sample_path.name,
                "old_sha256": sha256_text(source),
                "old_text": old_text,
                "new_text": old_text.rstrip("\n") + " /* gate-self-test */\n",
            }
        ],
    }
    validated = validate_payload(payload, root)
    run(validated, "validate_only", None, None, root)
    try:
        run(validated, "create_pr", None, None, root)
    except GateError as exc:
        if PATIENT_APPROVAL_PHRASE not in str(exc):
            raise
    else:
        fail("self-test expected the exact Patient PR/live approval phrase")

    invalid_path = json.loads(json.dumps(payload))
    invalid_path["operations"][0]["path"] = "therapist-app/admin.html"
    try:
        validate_payload(invalid_path, root)
    except GateError:
        pass
    else:
        fail("self-test expected an allowlist failure")

    version_edit = json.loads(json.dumps(payload))
    version_edit["operations"][0]["new_text"] = "const APP_VERSION = '999';"
    try:
        validate_payload(version_edit, root)
    except GateError:
        pass
    else:
        fail("self-test expected a version metadata failure")

    network_edit = json.loads(json.dumps(payload))
    network_edit["operations"][0]["new_text"] = (
        old_text.rstrip("\n") + "\nfetch('https://example.invalid');\n"
    )
    try:
        validate_payload(network_edit, root)
    except GateError:
        pass
    else:
        fail("self-test expected a new network sink failure")

    scanner_path = root / "patient-start-scan.js"
    scanner_source = normalize(scanner_path.read_text(encoding="utf-8"))
    scanner_payload = {
        "request_id": "patient-camera-gate-self-test",
        "base_sha": git_sha(root),
        "title": "Patient camera gate self test",
        "summary": "Camera source changes must select the dedicated patient scan regression.",
        "version_slug": "camera-gate-self-test",
        "risk_class": "standard",
        "touched_areas": ["patient-camera"],
        "required_tests": ["patient-scan"],
        "operations": [
            {
                "type": "replace_exact",
                "path": scanner_path.name,
                "old_sha256": sha256_text(scanner_source),
                "old_text": "object-fit:cover",
                "new_text": "object-fit:contain",
            }
        ],
    }
    validated_scanner = validate_payload(scanner_payload, root)
    if not requires_patient_scan(validated_scanner):
        fail("self-test expected patient-start-scan.js to select patient-scan")
    missing_camera_area = json.loads(json.dumps(scanner_payload))
    missing_camera_area["touched_areas"] = ["patient-ui"]
    try:
        validate_payload(missing_camera_area, root)
    except GateError:
        pass
    else:
        fail("self-test expected patient-start-scan.js to require patient-camera")

    with tempfile.TemporaryDirectory(prefix="kgg-patient-preview-self-test-") as temp_name:
        temp = Path(temp_name)
        candidate = temp / "candidate"
        candidate.mkdir()
        for source_path in patient_runtime_files(root):
            shutil.copy2(source_path, candidate / source_path.name)
        shutil.copy2(root / "CHANGELOG_PATIENT_APP.md", candidate / "CHANGELOG_PATIENT_APP.md")
        apply_operations(validated, candidate)
        version = bump_patient_version(validated, candidate)
        preview_root = preview_output.resolve() if preview_output else temp / "preview"
        if preview_output and preview_root.exists():
            shutil.rmtree(preview_root)
        meta = write_preview(preview_root, validated, payload_hash(validated), version, candidate)
        preview_html = (preview_root / "previews" / validated["request_id"] / "index.html").read_text(
            encoding="utf-8"
        )
        preview_worker = (
            preview_root / "previews" / validated["request_id"] / "service-worker.js"
        ).read_text(encoding="utf-8")
        preview_recovery = (
            preview_root / "previews" / validated["request_id"] / "update-recovery.html"
        ).read_text(encoding="utf-8")
        if '<meta name="robots" content="noindex,nofollow,noarchive">' not in preview_html:
            fail("self-test expected a noindex patient preview")
        module_sources = canonical_direct_first_load_modules(
            preview_html,
            preview_worker,
            preview_root / "previews" / validated["request_id"],
        )
        if [source.split("?", 1)[0].removeprefix("./") for source in module_sources] != list(DIRECT_FIRST_LOAD_MODULES):
            fail("self-test expected the canonical direct first-load module order")
        missing_module_preview = preview_html.replace(module_sources[0], "./missing-first-load-module.js", 1)
        try:
            canonical_direct_first_load_modules(
                missing_module_preview,
                preview_worker,
                preview_root / "previews" / validated["request_id"],
            )
        except GateError as exc:
            if "exact direct first-load module list" not in str(exc):
                raise
        else:
            fail("self-test expected a missing direct first-load module to be rejected")
        if (
            meta.get("patientVersion") != version
            or meta.get("patchHash") != payload_hash(validated)
            or meta.get("firstLoadModules") is not True
        ):
            fail("self-test expected matching patient preview evidence")
        if (
            str(meta.get("previewCacheName") or "") not in preview_worker
            or f"const CACHE_PREFIX='kgg-patient-preview-{validated['request_id']}-';"
            not in preview_recovery
        ):
            fail("self-test expected a request-isolated patient preview cache")
        verify_preview(preview_root, validated, payload_hash(validated), root)
        legacy_meta = dict(meta)
        legacy_meta.pop("firstLoadModules", None)
        write_json(preview_root / "previews" / validated["request_id"] / "meta.json", legacy_meta)
        try:
            verify_preview(preview_root, validated, payload_hash(validated), root)
        except GateError as exc:
            if "first-load module evidence" not in str(exc):
                raise
        else:
            fail("self-test expected a legacy patient preview to be rejected")

    print("KGG patient GPT write gate self-test PASS")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=["validate_only", "publish_preview", "create_pr", "publish_patient_live"],
    )
    parser.add_argument("--payload-file", type=Path)
    parser.add_argument("--preview-root", type=Path)
    parser.add_argument("--github-output", default=os.environ.get("GITHUB_OUTPUT"))
    parser.add_argument("--approval-phrase", default="")
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--self-test-preview-root", type=Path)
    args = parser.parse_args()

    try:
        if args.self_test:
            self_test(preview_output=args.self_test_preview_root)
            return 0
        if not args.mode or not args.payload_file:
            fail("--mode and --payload-file are required")
        payload = load_payload(args.payload_file)
        run(
            payload,
            args.mode,
            args.preview_root.resolve() if args.preview_root else None,
            args.github_output,
            approval_phrase=args.approval_phrase,
        )
        print(
            "KGG patient GPT write gate OK: "
            f"{args.mode} {payload['request_id']} {payload_hash(payload)[:12]}"
        )
        return 0
    except (GateError, OSError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
