#!/usr/bin/env python3
"""KGG HTML release pipeline.

One implementation is used by GitHub Actions, the Android admin app and Codex/GPT.
It never writes to main directly; callers prepare changes on a branch and open a PR.
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from kgg_encoding_guard import validate_html_encoding


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "therapist-app" / "android_update_manifest.json"
LEGACY_MANIFEST = ROOT / "therapist-app" / "kgg_update_manifest.json"
RELEASES = ROOT / "therapist-app" / "releases" / "web"
BASE_ADMIN = ROOT / "kgg-update" / "index.html"
LEGACY_ADMIN = ROOT / "therapist-app" / "releases" / "v389" / "web" / "KGG_APP_ADMIN_v389_flow_stability.html"
LEGACY_COLLEAGUE = ROOT / "therapist-app" / "releases" / "v389" / "web" / "KGG_APP_KOLLEGEN_v389_flow_stability.html"
PAGES_BASE = "https://kayus24.github.io/kgg/therapist-app/releases/web"
MAX_HTML_BYTES = 5_500_000
ADMIN_START = "<!-- KGG_ADMIN_ONLY_START -->"
ADMIN_END = "<!-- KGG_ADMIN_ONLY_END -->"

SEMVER_PATTERN = re.compile(
    r"(?P<major>0|[1-9][0-9]*)\."
    r"(?P<minor>0|[1-9][0-9]*)\."
    r"(?P<patch>0|[1-9][0-9]*)"
    r"(?:-(?P<prerelease>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
    r"(?:\+(?P<build>[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?"
)
SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
ANDROID_SHELL_PATTERN = re.compile(r"v[0-9]{3,8}")

CORE_MARKERS = (
    "KGGDataStore",
    "currentPlan",
    "scanQrFromImageFile",
    "finishWithPdf",
    "finishWithPatientApp",
    "<!doctype html>",
)
FORBIDDEN_LOADERS = ("document.write(", "raw.githubusercontent.com/Kayus24/kgg/main/kgg-update")
COLLEAGUE_FORBIDDEN = (
    '<button class="mutedBtn adminConfigBtn',
    '<div class="modal" id="adminSecretsModal"',
    'id="tabletMenuAdminConfigBtn"',
    'id="tabletMenuConfigTransferBtn"',
    'id="kggAdminMenuQrModal"',
    'class="adminTestBanner"',
    'id="kggTherapistShareModal"',
    "function exposeAdminSecretApi",
    "function openKggAdminMenuQr",
    "function openKggTherapistSetupQr",
    "window.KGGAdmin",
    "KGG_ROLLOUT_PROFILE='admin'",
    'KGG_ROLLOUT_PROFILE="admin"',
    "window.KGGReleaseCenter",
    "kggReleaseCenterOpen",
    "kggPhoneUpdateCenterMenu",
)


class ReleaseError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise ReleaseError(message)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        fail(f"{path} is not valid UTF-8: {exc}")


def write_text(path: Path, value: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding="utf-8", newline="\n")


def load_json(path: Path) -> dict:
    try:
        return json.loads(read_text(path))
    except (json.JSONDecodeError, OSError) as exc:
        fail(f"Cannot read JSON {path}: {exc}")


def write_json(path: Path, value: dict) -> None:
    write_text(path, json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def render_json_bytes(value: dict) -> bytes:
    """Render checked-in JSON deterministically as UTF-8, two-space indented LF."""
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def atomic_write_bytes(path: Path, value: bytes) -> None:
    """Replace one file atomically after its complete content is on the same volume."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    except OSError as exc:
        fail(f"Cannot stage atomic write for {path}: {exc}")
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(value)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except OSError as exc:
        fail(f"Cannot atomically write {path}: {exc}")
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def validate_release_id(value: str) -> str:
    if value != "v389" and not re.fullmatch(r"r[0-9]{4,8}", value or ""):
        fail("releaseId must match rNNNN (for example r0390); only v389 is retained as a legacy sentinel")
    return value


def require_string(container: dict, key: str, label: str) -> str:
    value = container.get(key)
    if not isinstance(value, str) or not value or value != value.strip():
        fail(f"{label}.{key} must be a non-empty string without surrounding whitespace")
    return value


def validate_semver(value: str, label: str) -> str:
    match = SEMVER_PATTERN.fullmatch(value)
    if not match:
        fail(f"{label} must be a valid semantic version")
    prerelease = match.group("prerelease")
    if prerelease:
        for identifier in prerelease.split("."):
            if identifier.isdigit() and len(identifier) > 1 and identifier.startswith("0"):
                fail(f"{label} has a numeric prerelease identifier with a leading zero")
    return value


def validate_sha256(value: str, label: str) -> str:
    if not SHA256_PATTERN.fullmatch(value):
        fail(f"{label} must be a lowercase 64-character SHA-256 digest")
    return value


def validate_https_url(value: str, label: str, suffix: str) -> str:
    parsed = urlsplit(value)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or any(character.isspace() for character in value)
        or not parsed.path.lower().endswith(suffix)
    ):
        fail(f"{label} must be an HTTPS URL ending in {suffix}")
    return value


def validate_manifest_channel(channel: object, profile: str) -> dict:
    label = f"channels.{profile}"
    if not isinstance(channel, dict):
        fail(f"{label} must be an object")
    release_id = validate_release_id(require_string(channel, "releaseId", label))
    if require_string(channel, "profile", label) != profile:
        fail(f"{label}.profile must be {profile}")
    version_name = require_string(channel, "versionName", label)
    url = validate_https_url(require_string(channel, "url", label), f"{label}.url", ".html")
    if release_id == "v389":
        expected_version_name = (
            "KGG_APP_ADMIN_v389_flow_stability"
            if profile == "admin"
            else "KGG_APP_KOLLEGEN_v389_flow_stability"
        )
        if version_name != expected_version_name:
            fail(f"{label}.versionName must preserve the v389 sentinel identity")
        legacy_filename = (
            "KGG_APP_ADMIN_v389_flow_stability.html"
            if profile == "admin"
            else "KGG_APP_KOLLEGEN_v389_flow_stability.html"
        )
        expected_path = f"/v389/web/{legacy_filename}"
    else:
        validate_semver(version_name, f"{label}.versionName")
        expected_path = f"/{release_id}/{profile}.html"
    if not urlsplit(url).path.endswith(expected_path):
        fail(f"{label}.url must end in {expected_path}")
    validate_sha256(require_string(channel, "sha256", label), f"{label}.sha256")
    rollout_code = channel.get("rolloutCode")
    if isinstance(rollout_code, bool) or not isinstance(rollout_code, int) or rollout_code < 0:
        fail(f"{label}.rolloutCode must be a non-negative integer")
    previous = channel.get("previousReleaseId")
    if previous is not None:
        if not isinstance(previous, str):
            fail(f"{label}.previousReleaseId must be null or a release ID")
        validate_release_id(previous)
    return channel


def project_legacy_manifest(canonical: dict) -> dict:
    """Create the deterministic flat compatibility manifest from canonical v2 data."""
    if not isinstance(canonical, dict):
        fail("Canonical update manifest must be an object")
    if canonical.get("kind") != "kgg_android_web_update_manifest":
        fail("Canonical update manifest has an unsupported kind")
    for key in ("version", "schema"):
        value = canonical.get(key)
        if isinstance(value, bool) or not isinstance(value, int) or value != 2:
            fail(f"Canonical update manifest {key} must be integer 2")

    channels = canonical.get("channels")
    if not isinstance(channels, dict):
        fail("Canonical update manifest channels must be an object")
    admin = validate_manifest_channel(channels.get("admin"), "admin")
    colleague = validate_manifest_channel(channels.get("colleague"), "colleague")

    shell_version = require_string(canonical, "latestAndroidShellVersion", "manifest")
    if not ANDROID_SHELL_PATTERN.fullmatch(shell_version):
        fail("manifest.latestAndroidShellVersion must match vNNN")

    apk_profiles: dict[str, str] = {}
    for profile in ("colleague", "admin"):
        url_key = f"{profile}AndroidApkUrl"
        sha_key = f"{profile}AndroidApkSha256"
        apk_profiles[url_key] = validate_https_url(
            require_string(canonical, url_key, "manifest"),
            f"manifest.{url_key}",
            ".apk",
        )
        apk_profiles[sha_key] = validate_sha256(
            require_string(canonical, sha_key, "manifest"),
            f"manifest.{sha_key}",
        )

    notes = require_string(canonical, "notes", "manifest")
    return {
        "kind": "kgg_app_update_manifest",
        "version": 1,
        "latestVersion": colleague["releaseId"],
        "latestAdminReleaseId": admin["releaseId"],
        "latestColleagueReleaseId": colleague["releaseId"],
        "latestAdminVersion": admin["versionName"],
        "latestColleagueVersion": colleague["versionName"],
        "adminUrl": admin["url"],
        "colleagueUrl": colleague["url"],
        "latestUrl": colleague["url"],
        "latestAndroidShellVersion": shell_version,
        "latestAndroidApkUrl": apk_profiles["colleagueAndroidApkUrl"],
        "latestAndroidApkSha256": apk_profiles["colleagueAndroidApkSha256"],
        "latestColleagueAndroidApkUrl": apk_profiles["colleagueAndroidApkUrl"],
        "latestColleagueAndroidApkSha256": apk_profiles["colleagueAndroidApkSha256"],
        "latestAdminAndroidApkUrl": apk_profiles["adminAndroidApkUrl"],
        "latestAdminAndroidApkSha256": apk_profiles["adminAndroidApkSha256"],
        "releaseNotes": notes,
    }


def write_update_manifests(canonical: dict) -> dict:
    """Validate the pair, then replace both files with rollback on the second write."""
    legacy = project_legacy_manifest(canonical)
    canonical_bytes = render_json_bytes(canonical)
    legacy_bytes = render_json_bytes(legacy)
    originals: dict[Path, bytes | None] = {}
    for path in (MANIFEST, LEGACY_MANIFEST):
        try:
            originals[path] = path.read_bytes()
        except FileNotFoundError:
            originals[path] = None
        except OSError as exc:
            fail(f"Cannot snapshot update manifest {path}: {exc}")

    try:
        atomic_write_bytes(MANIFEST, canonical_bytes)
        atomic_write_bytes(LEGACY_MANIFEST, legacy_bytes)
    except (OSError, ReleaseError) as write_error:
        rollback_errors = []
        for path, original in originals.items():
            try:
                current = path.read_bytes()
            except FileNotFoundError:
                current = None
            except OSError as exc:
                rollback_errors.append(f"cannot inspect {path}: {exc}")
                continue
            if current == original:
                continue
            try:
                if original is None:
                    path.unlink(missing_ok=True)
                else:
                    atomic_write_bytes(path, original)
            except (OSError, ReleaseError) as rollback_error:
                rollback_errors.append(f"cannot restore {path}: {rollback_error}")
        if rollback_errors:
            fail(f"Manifest pair write failed ({write_error}); rollback failed: {'; '.join(rollback_errors)}")
        raise
    return legacy


def sync_legacy_manifest(*, check: bool = False) -> dict:
    canonical = load_json(MANIFEST)
    legacy = project_legacy_manifest(canonical)
    expected = render_json_bytes(legacy)
    if check:
        try:
            actual = LEGACY_MANIFEST.read_bytes()
        except OSError as exc:
            fail(f"Cannot read legacy manifest {LEGACY_MANIFEST}: {exc}")
        if actual != expected:
            fail("Legacy update manifest is stale; run release_pipeline.py sync-legacy")
        return {"status": "current", "path": str(LEGACY_MANIFEST.relative_to(ROOT)).replace("\\", "/")}
    atomic_write_bytes(LEGACY_MANIFEST, expected)
    return {"status": "written", "path": str(LEGACY_MANIFEST.relative_to(ROOT)).replace("\\", "/")}


def validate_html(html: str, label: str) -> None:
    size = len(html.encode("utf-8"))
    if size > MAX_HTML_BYTES:
        fail(f"{label} is too large: {size} > {MAX_HTML_BYTES}")
    encoding_findings = validate_html_encoding(html.encode("utf-8"), label)
    if encoding_findings:
        fail("; ".join(finding.message for finding in encoding_findings))
    if not html.lower().startswith("<!doctype html>"):
        fail(f"{label} must start exactly with <!doctype html>")
    for marker in CORE_MARKERS:
        if marker not in html:
            fail(f"{label} is missing protected marker: {marker}")
    for forbidden in FORBIDDEN_LOADERS:
        if forbidden in html:
            fail(f"{label} contains forbidden loader code: {forbidden}")


def strip_marked_admin_blocks(html: str) -> str:
    if html.count(ADMIN_START) != html.count(ADMIN_END):
        fail("Unbalanced KGG_ADMIN_ONLY markers")
    pattern = re.compile(re.escape(ADMIN_START) + r".*?" + re.escape(ADMIN_END), re.S)
    return pattern.sub("", html)


def remove_js_function(text: str, name: str) -> str:
    match = re.search(r"(?:^|\n)([ \t]*(?:async\s+)?function\s+" + re.escape(name) + r"\s*\([^)]*\)\s*\{)", text)
    if not match:
        fail(f"Colleague hardening could not find JavaScript function: {name}")
    start = match.start(1)
    brace = text.find("{", match.start(1))
    depth = 0
    quote = None
    escaped = False
    line_comment = False
    block_comment = False
    index = brace
    while index < len(text):
        char = text[index]
        nxt = text[index + 1] if index + 1 < len(text) else ""
        if line_comment:
            if char == "\n":
                line_comment = False
            index += 1
            continue
        if block_comment:
            if char == "*" and nxt == "/":
                block_comment = False
                index += 2
            else:
                index += 1
            continue
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            index += 1
            continue
        if char in ("'", '"', "`"):
            quote = char
        elif char == "/" and nxt == "/":
            line_comment = True
            index += 2
            continue
        elif char == "/" and nxt == "*":
            block_comment = True
            index += 2
            continue
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[:start] + text[index + 1 :]
        index += 1
    fail(f"Colleague hardening found no closing brace for: {name}")


def harden_colleague(html: str) -> str:
    # Remove the privileged UI, not merely its visibility rule.
    html, button_count = re.subn(
        r'<button\b(?=[^>]*\bid=["\']adminConfigBtn["\'])[^>]*>.*?</button>\s*',
        "",
        html,
        flags=re.I | re.S,
    )
    if button_count != 1:
        fail(f"Expected one adminConfigBtn, removed {button_count}")

    modal_start = html.find('<div class="modal" id="adminSecretsModal">')
    modal_end = html.find('<div class="modal" id="sharedBankModal">', modal_start)
    if modal_start < 0 or modal_end < 0:
        fail("Could not isolate Admin secrets modal")
    html = html[:modal_start] + html[modal_end:]

    html = remove_js_function(html, "exposeAdminSecretApi")
    html = html.replace("      exposeAdminSecretApi();\n", "")
    html = html.replace("  exposeAdminSecretApi();\n", "")
    html = re.sub(r"^.*\$\('adminConfigBtn'\).*?$", "", html, flags=re.M)
    html = re.sub(r"^.*\$\('adminSecretsModal'\)\.addEventListener.*?$", "", html, flags=re.M)
    html = re.sub(
        r"^.*\$\('(?:closeAdminSecrets|saveAdminSecrets|loadAdminSafeFile|adminSafeFileInput|importAdminCodePackage|exportAdminCodePackage|downloadAdminSafeFile|clearAdminSecrets)'\).*?$",
        "",
        html,
        flags=re.M,
    )
    html = re.sub(r"^.*window\.KGGAdmin.*?$", "", html, flags=re.M)
    return html


def remove_html_range(html: str, start_token: str, next_token: str, label: str) -> str:
    start = html.find(start_token)
    end = html.find(next_token, start + len(start_token)) if start >= 0 else -1
    if start < 0 or end < 0:
        fail(f"Colleague hardening could not isolate HTML block: {label}")
    return html[:start] + html[end:]


def remove_tag_by_id(html: str, tag: str, element_id: str, *, required: bool = True) -> str:
    pattern = re.compile(
        r"<" + re.escape(tag) + r"\b(?=[^>]*\bid=[\"']" + re.escape(element_id) + r"[\"'])[^>]*>.*?</" + re.escape(tag) + r">\s*",
        re.I | re.S,
    )
    html, count = pattern.subn("", html, count=1)
    if required and count != 1:
        fail(f"Colleague hardening could not remove {tag}#{element_id}; removed {count}")
    return html


def remove_function_if_present(text: str, name: str) -> str:
    try:
        return remove_js_function(text, name)
    except ReleaseError:
        return text


def derive_colleague(candidate: str) -> str:
    """Create the colleague artifact directly from the confirmed current Admin source.

    This intentionally removes privileged DOM and JavaScript by contract. It does
    not reuse the historical v389 delta, so later UI fixes remain intact.
    """
    html = strip_marked_admin_blocks(candidate)
    html, body_count = re.subn(r'<body class="adminMode">', '<body class="colleagueMode">', html, count=1)
    if body_count != 1:
        fail(f"Expected one adminMode body, changed {body_count}")
    html, profile_count = re.subn(
        r"window\.KGG_ROLLOUT_PROFILE\s*=\s*['\"]admin['\"]\s*;",
        "window.KGG_ROLLOUT_PROFILE='colleague';",
        html,
        count=1,
    )
    if profile_count != 1:
        fail(f"Expected one Admin rollout profile, changed {profile_count}")
    html = re.sub(r"<title>.*?</title>", "<title>KGG App Kolleg:innen</title>", html, count=1, flags=re.S)
    html, banner_count = re.subn(
        r'<div class="adminTestBanner"[^>]*>.*?</div>\s*',
        "",
        html,
        count=1,
        flags=re.S,
    )
    if banner_count != 1:
        fail(f"Expected one Admin banner, removed {banner_count}")

    html = remove_html_range(
        html,
        '<div class="kggAdminMenuQrModal" id="kggAdminMenuQrModal"',
        '<div class="kggTherapistShareModal" id="kggTherapistShareModal"',
        "Admin QR modal",
    )
    html = remove_html_range(
        html,
        '<div class="kggTherapistShareModal" id="kggTherapistShareModal"',
        '<div id="mobileScannedPlansDock"',
        "therapist share modal",
    )
    html = remove_tag_by_id(html, "script", "kgg-v12-release-center-entry-restore", required=False)
    html = remove_tag_by_id(html, "script", "kgg-v13-update-zentrale-marker", required=False)
    html = remove_function_if_present(html, "openReleaseCenter")
    html = html.replace(
        "'<div class=\"kggPhoneMenuGroup\" data-kgg-phone-menu-group=\"update\"><div class=\"kggPhoneMenuGroupTitle\">Update</div><button id=\"kggPhoneUpdateCenterMenu\" type=\"button\">Update-Zentrale</button></div>'+",
        "",
    )
    html = html.replace('    bind("kggPhoneUpdateCenterMenu",openReleaseCenter);\n', "")
    html, share_button_count = re.subn(
        r'<button\b[^>]*\bid="tabletMenuTherapistShareBtn"[^>]*>.*?</button>\s*',
        "",
        html,
        count=1,
        flags=re.I | re.S,
    )
    if share_button_count != 1:
        fail(f"Expected one therapist share button, removed {share_button_count}")

    for function_name in (
        "closeKggTherapistShareModal",
        "openKggTherapistShareModal",
        "kggTherapistAppUrl",
        "openKggTherapistAppOnlyQr",
        "openKggTherapistSetupQr",
        "openKggTherapistApiOnlyQr",
        "closeKggAdminMenuQrModal",
        "renderKggAdminMenuQr",
        "openKggAdminMenuQr",
    ):
        html = remove_js_function(html, function_name)
    html = re.sub(r"\n\s*const kggAdminMenuQrTargets=\{.*?\n\s*\};", "", html, count=1, flags=re.S)
    html = re.sub(
        r"\n\s*document\.querySelectorAll\('\[data-kgg-admin-menu-qr\]'\)\.forEach\(btn=>\{.*?\n\s*\}\);\s*\n\s*\}\);",
        "",
        html,
        count=1,
        flags=re.S,
    )
    html = re.sub(r"^.*(?:tabletMenuAdminConfigBtn|tabletMenuSharedBankBtn|tabletMenuSyncQrBtn|tabletMenuConfigTransferBtn|kggAdminMenuQrClose|kggAdminMenuQrCopy|kggAdminMenuQrOpen).*?$", "", html, flags=re.M)
    html = re.sub(r"^.*tabletMenuTherapistShareBtn.*?$", "", html, flags=re.M)
    html = harden_colleague(html)
    html, guard_count = re.subn(
        r"function initAdminModeAccess\(\)\{\s*",
        "function initAdminModeAccess(){\n    if(window.KGG_ROLLOUT_PROFILE==='colleague'){document.body.classList.remove('adminMode');document.body.classList.add('colleagueMode');return;}\n    ",
        html,
        count=1,
    )
    if guard_count != 1:
        fail(f"Expected one Admin-mode initializer, guarded {guard_count}")
    colleague_boundary = """<style id=\"kgg-colleague-boundary\">
  body.colleagueMode .adminConfigBtn,
  body.colleagueMode .sharedBankBtn,
  body.colleagueMode .adminTestBanner{display:none!important}
</style>
"""
    html = html.replace("</head>", colleague_boundary + "</head>", 1)
    for forbidden in COLLEAGUE_FORBIDDEN:
        if forbidden in html:
            fail(f"Colleague build still contains Admin-only token: {forbidden}")
    if 'class="colleagueMode"' not in html or "KGG_ROLLOUT_PROFILE='colleague'" not in html:
        fail("Colleague build is missing its profile identity")
    return html


def find_unique_block(lines: list[str], block: list[str], label: str) -> int:
    if not block:
        fail(f"Internal transform error: empty block for {label}")
    hits = []
    width = len(block)
    for index in range(0, len(lines) - width + 1):
        if lines[index : index + width] == block:
            hits.append(index)
            if len(hits) > 1:
                break
    if len(hits) != 1:
        fail(f"Profile transform {label} matched {len(hits)} times; candidate needs refreshed profile markers")
    return hits[0]


def apply_baseline_profile_transform(candidate: str) -> str:
    """Apply the audited v389 Admin->Kolleg:innen delta to a candidate.

    Exact matching makes this intentionally conservative: an edit that overlaps a
    profile-specific block fails instead of leaking Admin code.
    """
    admin_lines = read_text(LEGACY_ADMIN).splitlines(keepends=True)
    colleague_lines = read_text(LEGACY_COLLEAGUE).splitlines(keepends=True)
    candidate_lines = strip_marked_admin_blocks(candidate).splitlines(keepends=True)
    matcher = difflib.SequenceMatcher(a=admin_lines, b=colleague_lines, autojunk=False)
    changes = [op for op in matcher.get_opcodes() if op[0] != "equal"]

    for number, (tag, i1, i2, j1, j2) in enumerate(reversed(changes), start=1):
        old = admin_lines[i1:i2]
        new = colleague_lines[j1:j2]
        label = f"{len(changes) - number + 1}:{tag}"
        if old:
            at = find_unique_block(candidate_lines, old, label)
            candidate_lines[at : at + len(old)] = new
            continue

        before = admin_lines[max(0, i1 - 3) : i1]
        after = admin_lines[i1 : min(len(admin_lines), i1 + 3)]
        anchor = before + after
        at = find_unique_block(candidate_lines, anchor, label + ":anchor")
        candidate_lines[at + len(before) : at + len(before)] = new

    result = harden_colleague("".join(candidate_lines))
    for forbidden in COLLEAGUE_FORBIDDEN:
        if forbidden in result:
            fail(f"Colleague build still contains Admin-only token: {forbidden}")
    if "colleagueMode" not in result or "KGG_ROLLOUT_PROFILE" not in result:
        fail("Colleague build is missing its profile identity")
    return result


def release_entry(release_id: str, profile: str, version_name: str, html: str, notes: str) -> dict:
    filename = f"{profile}.html"
    return {
        "releaseId": release_id,
        "profile": profile,
        "versionName": version_name,
        "url": f"{PAGES_BASE}/{release_id}/{filename}",
        "sha256": sha256_text(html),
        "notes": notes,
    }


def ensure_schema_v2(manifest: dict) -> dict:
    channels = manifest.setdefault("channels", {})
    if "admin" not in channels:
        channels["admin"] = {
            "rolloutCode": 0,
            "releaseId": "v389",
            "profile": "admin",
            "versionName": "KGG_APP_ADMIN_v389_flow_stability",
            "url": manifest["adminHtmlUrl"],
            "sha256": manifest["adminSha256"],
            "previousReleaseId": None,
        }
    if "colleague" not in channels:
        channels["colleague"] = {
            "rolloutCode": 0,
            "releaseId": "v389",
            "profile": "colleague",
            "versionName": "KGG_APP_KOLLEGEN_v389_flow_stability",
            "url": manifest["colleagueHtmlUrl"],
            "sha256": manifest["colleagueSha256"],
            "previousReleaseId": None,
        }
    manifest["schema"] = 2
    return manifest


def next_rollout(channel: dict) -> int:
    return int(channel.get("rolloutCode") or 0) + 1


def prepare(candidate_path: Path, release_json_path: Path) -> dict:
    release = load_json(release_json_path)
    release_id = validate_release_id(str(release.get("releaseId", "")))
    version_name = str(release.get("versionName", "")).strip()
    notes = str(release.get("notes", "")).strip()
    if not version_name or not notes:
        fail("release.json requires non-empty versionName and notes")

    admin_html = read_text(candidate_path)
    validate_html(admin_html, "Admin candidate")
    colleague_html = derive_colleague(admin_html)
    validate_html(colleague_html, "Colleague build")
    if sha256_text(admin_html) == sha256_text(colleague_html):
        fail("Admin and colleague builds must not be identical")

    release_dir = RELEASES / release_id
    if release_dir.exists():
        fail(f"Immutable release already exists: {release_id}")
    write_text(release_dir / "admin.html", admin_html)
    write_text(release_dir / "colleague.html", colleague_html)

    metadata = {
        "schema": 1,
        "releaseId": release_id,
        "versionName": version_name,
        "notes": notes,
        "createdAt": utc_now(),
        "source": str(candidate_path.relative_to(ROOT)).replace("\\", "/"),
        "profiles": {
            "admin": release_entry(release_id, "admin", version_name, admin_html, notes),
            "colleague": release_entry(release_id, "colleague", version_name, colleague_html, notes),
        },
    }
    write_json(release_dir / "release.json", metadata)

    manifest = ensure_schema_v2(load_json(MANIFEST))
    old = manifest["channels"]["admin"]
    admin_channel = dict(metadata["profiles"]["admin"])
    admin_channel.update({
        "rolloutCode": next_rollout(old),
        "previousReleaseId": old.get("releaseId"),
        "releasedAt": utc_now(),
    })
    manifest["channels"]["admin"] = admin_channel
    manifest["adminHtmlUrl"] = admin_channel["url"]
    manifest["adminSha256"] = admin_channel["sha256"]
    manifest["notes"] = f"Admin beta {release_id}: {notes}"
    write_update_manifests(manifest)
    return metadata


def load_release(release_id: str) -> dict:
    validate_release_id(release_id)
    if release_id == "v389":
        admin_html = read_text(LEGACY_ADMIN)
        colleague_html = read_text(LEGACY_COLLEAGUE)
        return {
            "schema": 1,
            "releaseId": "v389",
            "versionName": "KGG v389 Flow Stability",
            "notes": "Last-known-good baseline before release pipeline v2.",
            "profiles": {
                "admin": {
                    "releaseId": "v389",
                    "profile": "admin",
                    "versionName": "KGG_APP_ADMIN_v389_flow_stability",
                    "url": "https://kayus24.github.io/kgg/therapist-app/releases/v389/web/KGG_APP_ADMIN_v389_flow_stability.html",
                    "sha256": sha256_text(admin_html),
                    "notes": "Legacy v389 baseline",
                },
                "colleague": {
                    "releaseId": "v389",
                    "profile": "colleague",
                    "versionName": "KGG_APP_KOLLEGEN_v389_flow_stability",
                    "url": "https://kayus24.github.io/kgg/therapist-app/releases/v389/web/KGG_APP_KOLLEGEN_v389_flow_stability.html",
                    "sha256": sha256_text(colleague_html),
                    "notes": "Legacy v389 baseline",
                },
            },
        }
    path = RELEASES / release_id / "release.json"
    if not path.exists():
        fail(f"Unknown release: {release_id}")
    return load_json(path)


def promote(release_id: str) -> dict:
    release = load_release(release_id)
    manifest = ensure_schema_v2(load_json(MANIFEST))
    old = manifest["channels"]["colleague"]
    target = dict(release["profiles"]["colleague"])
    target.update({
        "rolloutCode": next_rollout(old),
        "previousReleaseId": old.get("releaseId"),
        "releasedAt": utc_now(),
    })
    manifest["channels"]["colleague"] = target
    manifest["colleagueHtmlUrl"] = target["url"]
    manifest["colleagueSha256"] = target["sha256"]
    manifest["sha256"] = target["sha256"]
    manifest["latestWebVersion"] = release_id
    manifest["notes"] = f"Stable promotion {release_id}: {release.get('notes', '')}"
    write_update_manifests(manifest)
    return target


def rollback(channel_name: str, release_id: str) -> dict:
    release = load_release(release_id)
    manifest = ensure_schema_v2(load_json(MANIFEST))
    old = manifest["channels"][channel_name]
    target = dict(release["profiles"][channel_name])
    target.update({
        "rolloutCode": next_rollout(old),
        "previousReleaseId": old.get("releaseId"),
        "releasedAt": utc_now(),
        "rollback": True,
    })
    manifest["channels"][channel_name] = target
    if channel_name == "admin":
        manifest["adminHtmlUrl"] = target["url"]
        manifest["adminSha256"] = target["sha256"]
    else:
        manifest["colleagueHtmlUrl"] = target["url"]
        manifest["colleagueSha256"] = target["sha256"]
        manifest["sha256"] = target["sha256"]
        manifest["latestWebVersion"] = release_id
    manifest["notes"] = f"{channel_name} rollback to {release_id}"
    write_update_manifests(manifest)
    return target


def status() -> dict:
    manifest = ensure_schema_v2(load_json(MANIFEST))
    return {"schema": manifest["schema"], "channels": manifest["channels"]}


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    p_prepare = sub.add_parser("prepare")
    p_prepare.add_argument("--candidate", required=True, type=Path)
    p_prepare.add_argument("--release-json", required=True, type=Path)
    p_promote = sub.add_parser("promote")
    p_promote.add_argument("--release-id", required=True)
    p_rollback = sub.add_parser("rollback")
    p_rollback.add_argument("--channel", choices=("admin", "colleague"), required=True)
    p_rollback.add_argument("--release-id", required=True)
    p_sync_legacy = sub.add_parser("sync-legacy")
    p_sync_legacy.add_argument("--check", action="store_true")
    sub.add_parser("status")
    args = parser.parse_args()

    try:
        if args.command == "prepare":
            result = prepare((ROOT / args.candidate).resolve(), (ROOT / args.release_json).resolve())
        elif args.command == "promote":
            result = promote(args.release_id)
        elif args.command == "rollback":
            result = rollback(args.channel, args.release_id)
        elif args.command == "sync-legacy":
            result = sync_legacy_manifest(check=args.check)
        else:
            result = status()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except ReleaseError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
