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
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from kgg_encoding_guard import validate_html_encoding


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "therapist-app" / "android_update_manifest.json"
RELEASES = ROOT / "therapist-app" / "releases" / "web"
BASE_ADMIN = ROOT / "kgg-update" / "index.html"
LEGACY_ADMIN = ROOT / "therapist-app" / "releases" / "v389" / "web" / "KGG_APP_ADMIN_v389_flow_stability.html"
LEGACY_COLLEAGUE = ROOT / "therapist-app" / "releases" / "v389" / "web" / "KGG_APP_KOLLEGEN_v389_flow_stability.html"
PAGES_BASE = "https://kayus24.github.io/kgg/therapist-app/releases/web"
MAX_HTML_BYTES = 5_500_000
ADMIN_START = "<!-- KGG_ADMIN_ONLY_START -->"
ADMIN_END = "<!-- KGG_ADMIN_ONLY_END -->"

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


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def validate_release_id(value: str) -> str:
    if not re.fullmatch(r"[rv][0-9]{3,8}", value or ""):
        fail("releaseId must match rNNNN (for example r0390); v389 is retained as the legacy baseline")
    return value


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
            "versionName": "KGG_APP_ADMIN_v389_flow_stability",
            "url": manifest["adminHtmlUrl"],
            "sha256": manifest["adminSha256"],
            "previousReleaseId": None,
        }
    if "colleague" not in channels:
        channels["colleague"] = {
            "rolloutCode": 0,
            "releaseId": "v389",
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
    write_json(MANIFEST, manifest)
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
    write_json(MANIFEST, manifest)
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
    write_json(MANIFEST, manifest)
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
    sub.add_parser("status")
    args = parser.parse_args()

    try:
        if args.command == "prepare":
            result = prepare((ROOT / args.candidate).resolve(), (ROOT / args.release_json).resolve())
        elif args.command == "promote":
            result = promote(args.release_id)
        elif args.command == "rollback":
            result = rollback(args.channel, args.release_id)
        else:
            result = status()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except ReleaseError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
