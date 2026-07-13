#!/usr/bin/env python3
"""Safely scaffold the next versioned KGG HTML patch in the module sandbox."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import build_therapist_source as builder


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "kgg-update" / "src"
MANIFEST = SRC / "parts.json"
VERSION = ROOT / "kgg-update" / "version.json"
SOURCE_TRUTH = SRC / "metadata" / "source-truth.html"
CHANGELOG = SRC / "metadata" / "changelog.html"
PATCH_RULES = SRC / "metadata" / "patch-rules.html"
BASE_HEAD = SRC / "base-head.html"
BASE_APP = SRC / "base-app.html"
PROTECTED_AREAS = [
    "PDF",
    "QR/Patienten-App",
    "Scan/OCR",
    "Parser",
    "Plan-State",
    "Medien/Upload",
    "API-Key-Logik",
    "Android/APK",
    "GitHub Manifest",
    "Handy-Layout",
]


class ScaffoldError(RuntimeError):
    pass


def normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.casefold().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss"))


def json_script(text: str, element_id: str) -> tuple[dict, tuple[int, int], str, str]:
    pattern = re.compile(
        rf'(<script\b[^>]*\bid="{re.escape(element_id)}"[^>]*>\s*)(.*?)(\s*</script>)',
        flags=re.DOTALL | re.IGNORECASE,
    )
    match = pattern.search(text)
    if not match:
        raise ScaffoldError(f"JSON block not found: {element_id}")
    try:
        data = json.loads(match.group(2))
    except json.JSONDecodeError as exc:
        raise ScaffoldError(f"Invalid JSON in {element_id}: {exc}") from exc
    if not isinstance(data, dict):
        raise ScaffoldError(f"JSON block must contain an object: {element_id}")
    return data, (match.start(), match.end()), match.group(1), match.group(3)


def replace_json_script(text: str, element_id: str, data: dict) -> str:
    _, span, prefix, suffix = json_script(text, element_id)
    encoded = json.dumps(data, ensure_ascii=False, indent=2)
    return text[:span[0]] + prefix + encoded + suffix + text[span[1]:]


def replace_once(text: str, pattern: str, replacement: str, label: str) -> str:
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.DOTALL)
    if count != 1:
        raise ScaffoldError(f"Expected exactly one {label}, found {count}")
    return updated


def patch_template(patch_id: str, title: str) -> bytes:
    return (
        f"<!-- KGG PATCH START {patch_id} -->\n"
        f"<!-- {title} -->\n"
        f"<script id=\"{patch_id}\">\n"
        "(function(){\n"
        "  \"use strict\";\n"
        f"  const PATCH_ID=\"{patch_id}\";\n"
        "  // Den kleinstmoeglichen Patch hier implementieren. Bestehende Hooks beibehalten.\n"
        "  window.KGG_PATCHES=window.KGG_PATCHES||{};\n"
        "  window.KGG_PATCHES[PATCH_ID]={installed:true};\n"
        "})();\n"
        "</script>\n"
        f"<!-- KGG PATCH END {patch_id} -->\n"
    ).encode("utf-8")


def prepare(args: argparse.Namespace) -> tuple[dict[Path, bytes], dict]:
    slug = args.slug.strip().lower()
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        raise ScaffoldError("slug must contain lowercase letters/numbers separated by single hyphens")
    if not args.title.strip() or not args.summary.strip():
        raise ScaffoldError("title and summary must not be empty")

    areas = list(dict.fromkeys(area.strip() for area in args.area if area.strip()))
    if not areas:
        raise ScaffoldError("at least one --area is required")
    protected_norm = {normalize(area): area for area in PROTECTED_AREAS}
    selected_protected = [protected_norm[normalize(area)] for area in areas if normalize(area) in protected_norm]
    if selected_protected and not args.allow_protected:
        raise ScaffoldError("protected area selected without --allow-protected: " + ", ".join(selected_protected))
    if (args.allow_protected or args.allow_changelog_overflow) and not args.approval_note.strip():
        raise ScaffoldError("override flags require a non-empty --approval-note")

    version = json.loads(VERSION.read_text(encoding="utf-8"))
    old_code = version.get("versionCode")
    if not isinstance(old_code, int) or old_code < 1:
        raise ScaffoldError("version.json has no valid versionCode")
    code = old_code + 1
    version_name = args.version_name or f"1.0.{code}-{slug}"
    if not re.fullmatch(rf"1\.0\.{code}-[a-z0-9]+(?:-[a-z0-9]+)*", version_name):
        raise ScaffoldError(f"version name must use 1.0.{code}-<slug>")
    patch_id = f"kgg-v{code:03d}-{slug}"
    relative_patch = f"patches/v{code:03d}-{slug}.html"
    patch_path = SRC / relative_patch
    if patch_path.exists():
        raise ScaffoldError(f"patch file already exists: {relative_patch}")

    source_text = SOURCE_TRUTH.read_text(encoding="utf-8")
    source, _, _, _ = json_script(source_text, "kgg-source-truth")
    active_fixes = source.setdefault("activeFixes", [])
    if not isinstance(active_fixes, list):
        raise ScaffoldError("kgg-source-truth.activeFixes must be a list")
    if slug not in active_fixes:
        active_fixes.append(slug)
    source["currentVersion"] = {
        "versionCode": code,
        "versionName": version_name,
        "lastPatchId": patch_id,
        "updatedBy": "kgg-module-scaffolder",
    }
    source["latestPatchId"] = patch_id
    source["lastUpdateIntent"] = {
        "id": patch_id,
        "summary": args.summary.strip(),
        "touched": areas,
        "notTouched": [area for area in PROTECTED_AREAS if area not in selected_protected],
    }

    rules_text = PATCH_RULES.read_text(encoding="utf-8")
    rules, _, _, _ = json_script(rules_text, "kgg-patch-rules")
    policy = rules.get("changelogSizePolicy") if isinstance(rules.get("changelogSizePolicy"), dict) else {}
    rules["lastUpdatedByPatchId"] = patch_id

    changelog_text = CHANGELOG.read_text(encoding="utf-8")
    changelog, _, _, _ = json_script(changelog_text, "kgg-changelog")
    entries = changelog.get("entries")
    if not isinstance(entries, list):
        raise ScaffoldError("kgg-changelog.entries must be a list")
    maximum = int(policy.get("maxEmbeddedEntries", 30))
    if len(entries) >= maximum and not args.allow_changelog_overflow:
        raise ScaffoldError(
            f"embedded changelog already has {len(entries)} entries (limit {maximum}); "
            "archive/compaction approval or --allow-changelog-overflow with --approval-note is required"
        )
    entry = {
        "versionCode": code,
        "versionName": version_name,
        "patchId": patch_id,
        "status": "scaffolded",
        "type": "module-patch",
        "title": args.title.strip(),
        "reason": args.summary.strip(),
        "whatChanged": [args.summary.strip()],
        "touchedAreas": areas,
        "notTouched": [area for area in PROTECTED_AREAS if area not in selected_protected],
        "testStatus": {"local": "pending", "certification": "pending"},
    }
    if args.approval_note.strip():
        entry["approvalNote"] = args.approval_note.strip()
    entries.insert(0, entry)
    changelog["latestVersionCode"] = code
    changelog["latestVersionName"] = version_name

    head_text = BASE_HEAD.read_text(encoding="utf-8")
    head_text = replace_json_script(head_text, "kgg-source-truth", source)
    app_text = BASE_APP.read_text(encoding="utf-8")
    app_text = replace_once(app_text, r"<title>.*?</title>", f"<title>KGG Update v{code:03d} {args.title.strip()}</title>", "HTML title")
    app_text = replace_once(
        app_text,
        r"const VERSION='[^']+';",
        f"const VERSION='KGG_GITHUB_UPDATE_v{code:03d}_{slug.replace('-', '_')}';",
        "VERSION constant",
    )
    build_time = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    app_text = replace_once(
        app_text,
        r"const KGG_BUILD_INFO=\{[^\n]+\};",
        "const KGG_BUILD_INFO=" + json.dumps(
            {"release": f"v{code:03d}", "buildTime": build_time, "buildCode": f"module-v{code:03d}-{slug}", "htmlFile": "kgg-update/index.html"},
            separators=(",", ":"),
        ) + ";",
        "KGG_BUILD_INFO constant",
    )

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    parts = manifest.get("parts")
    patch_ids = manifest.get("requiredPatchIds")
    if not isinstance(parts, list) or parts.count("footer.html") != 1 or parts[-1] != "footer.html":
        raise ScaffoldError("parts.json must contain exactly one final footer.html")
    if not isinstance(patch_ids, list):
        raise ScaffoldError("parts.json.requiredPatchIds must be a list")
    parts.insert(len(parts) - 1, relative_patch)
    patch_ids.append(patch_id)

    planned: dict[Path, bytes] = {
        SOURCE_TRUTH: replace_json_script(source_text, "kgg-source-truth", source).encode("utf-8"),
        CHANGELOG: replace_json_script(changelog_text, "kgg-changelog", changelog).encode("utf-8"),
        PATCH_RULES: replace_json_script(rules_text, "kgg-patch-rules", rules).encode("utf-8"),
        BASE_HEAD: head_text.encode("utf-8"),
        BASE_APP: app_text.encode("utf-8"),
        patch_path: patch_template(patch_id, args.title.strip()),
        MANIFEST: (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
    }
    assembled_parts = []
    for relative in parts:
        path = SRC / relative
        assembled_parts.append(planned[path] if path in planned else path.read_bytes())
    assembled = b"".join(assembled_parts)
    builder.validate_assembled(assembled, manifest)
    digest = hashlib.sha256(assembled).hexdigest()
    version.update({"versionCode": code, "versionName": version_name, "indexUrl": f"index.html?v={code}", "sha256": digest})
    planned[VERSION] = (json.dumps(version, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    planned[ROOT / "kgg-update" / "index.html"] = assembled
    report = {
        "patchId": patch_id,
        "patchFile": relative_patch,
        "versionCode": code,
        "versionName": version_name,
        "candidateHash": digest,
        "areas": areas,
        "protectedAreas": selected_protected,
        "changelogEntriesAfter": len(entries),
    }
    return planned, report


def apply(planned: dict[Path, bytes]) -> None:
    originals = {path: path.read_bytes() if path.exists() else None for path in planned}
    try:
        for path, raw in planned.items():
            builder.atomic_write(path, raw)
        builder.check(MANIFEST)
    except Exception:
        for path, raw in originals.items():
            if raw is None:
                try:
                    path.unlink()
                except FileNotFoundError:
                    pass
            else:
                builder.atomic_write(path, raw)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--slug", required=True, help="lowercase patch slug, for example patient-search-focus")
    parser.add_argument("--title", required=True, help="short human-readable patch title")
    parser.add_argument("--summary", required=True, help="one-sentence reason and intended change")
    parser.add_argument("--area", action="append", required=True, help="touched functional area; repeat as needed")
    parser.add_argument("--version-name", help="optional exact 1.0.<next>-<slug> version name")
    parser.add_argument("--allow-protected", action="store_true", help="allow an explicitly selected protected area")
    parser.add_argument("--allow-changelog-overflow", action="store_true", help="allow adding above the embedded changelog limit")
    parser.add_argument("--approval-note", default="", help="required rationale/approval for either override")
    parser.add_argument("--dry-run", action="store_true", help="validate and show the planned patch without writing")
    args = parser.parse_args()
    try:
        planned, report = prepare(args)
        if not args.dry_run:
            apply(planned)
        report["dryRun"] = bool(args.dry_run)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    except (OSError, UnicodeError, json.JSONDecodeError, ScaffoldError, builder.BuildError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
