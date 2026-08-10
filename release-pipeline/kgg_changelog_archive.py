#!/usr/bin/env python3
"""Create and verify the immutable therapist changelog snapshot through v062."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

import build_therapist_source as builder


ROOT = Path(__file__).resolve().parents[1]
CHANGELOG_PATH = ROOT / "kgg-update" / "src" / "metadata" / "changelog.html"
VERSION_PATH = ROOT / "kgg-update" / "version.json"
PARTS_PATH = ROOT / "kgg-update" / "src" / "parts.json"
ARCHIVE_RELATIVE_PATH = "docs/changelog-archive/kgg-therapist-changelog-through-v062.json"
ARCHIVE_PATH = ROOT / ARCHIVE_RELATIVE_PATH
ARCHIVE_KIND = "kgg-therapist-changelog-snapshot"
ARCHIVE_VERSION_CODE = 62
ARCHIVE_VERSION_NAME = "1.0.62-tablet-recent-package-shell-geometry"
ARCHIVE_PATCH_ID = "kgg-v063-changelog-archive-window"
ARCHIVE_ENTRY_COUNT = 34
RETAINED_ENTRY_COUNT = 14
ARCHIVE_ENTRIES_SHA256 = "d1b3a5d67dd78ae6819bfbf28b321c66cdacdc173b4c39b358344e380fb30fef"


class ChangelogArchiveError(RuntimeError):
    pass


def canonical_entries_bytes(entries: list[dict[str, Any]]) -> bytes:
    return json.dumps(
        entries,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def entries_sha256(entries: list[dict[str, Any]]) -> str:
    return hashlib.sha256(canonical_entries_bytes(entries)).hexdigest()


def _json_script(text: str, element_id: str) -> tuple[dict[str, Any], tuple[int, int], str, str]:
    pattern = re.compile(
        rf'(<script\b[^>]*\bid="{re.escape(element_id)}"[^>]*>\s*)(.*?)(\s*</script>)',
        flags=re.DOTALL | re.IGNORECASE,
    )
    match = pattern.search(text)
    if not match:
        raise ChangelogArchiveError(f"JSON block not found: {element_id}")
    try:
        data = json.loads(match.group(2))
    except json.JSONDecodeError as exc:
        raise ChangelogArchiveError(f"Invalid JSON in {element_id}: {exc}") from exc
    if not isinstance(data, dict):
        raise ChangelogArchiveError(f"JSON block must contain an object: {element_id}")
    return data, (match.start(), match.end()), match.group(1), match.group(3)


def _replace_json_script(text: str, element_id: str, data: dict[str, Any]) -> str:
    _current, span, prefix, suffix = _json_script(text, element_id)
    encoded = json.dumps(data, ensure_ascii=False, indent=2)
    return text[: span[0]] + prefix + encoded + suffix + text[span[1] :]


def load_embedded(path: Path = CHANGELOG_PATH) -> tuple[str, dict[str, Any]]:
    text = path.read_text(encoding="utf-8")
    data, _span, _prefix, _suffix = _json_script(text, "kgg-changelog")
    return text, data


def archive_reference() -> dict[str, Any]:
    return {
        "repositoryPath": ARCHIVE_RELATIVE_PATH,
        "snapshotVersionCode": ARCHIVE_VERSION_CODE,
        "entryCount": ARCHIVE_ENTRY_COUNT,
        "entriesSha256": ARCHIVE_ENTRIES_SHA256,
        "retainedEntryCountAtCompaction": RETAINED_ENTRY_COUNT,
        "createdByPatchId": ARCHIVE_PATCH_ID,
    }


def archive_document(entries: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema": 1,
        "kind": ARCHIVE_KIND,
        "source": {
            "path": "kgg-update/src/metadata/changelog.html",
            "elementId": "kgg-changelog",
            "versionCode": ARCHIVE_VERSION_CODE,
            "versionName": ARCHIVE_VERSION_NAME,
        },
        "createdByPatchId": ARCHIVE_PATCH_ID,
        "entryOrder": "newest-first",
        "entryCount": len(entries),
        "entriesSha256": entries_sha256(entries),
        "canonicalization": {
            "scope": "entries",
            "encoding": "utf-8",
            "ensureAscii": False,
            "sortObjectKeys": True,
            "separators": [",", ":"],
            "allowNaN": False,
            "trailingNewline": False,
        },
        "entries": entries,
    }


def validate_changelog_archives(
    changelog: dict[str, Any],
    root: Path = ROOT,
    *,
    required: bool = False,
) -> dict[str, Any] | None:
    snapshots = changelog.get("archiveSnapshots")
    if snapshots is None and not required:
        return None
    if not isinstance(snapshots, list) or len(snapshots) != 1:
        raise ChangelogArchiveError("kgg-changelog.archiveSnapshots must contain exactly one snapshot")
    reference = snapshots[0]
    if reference != archive_reference():
        raise ChangelogArchiveError("kgg-changelog archive snapshot reference does not match the v062 contract")

    path = root / ARCHIVE_RELATIVE_PATH
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ChangelogArchiveError(f"Missing changelog archive: {ARCHIVE_RELATIVE_PATH}") from exc
    except json.JSONDecodeError as exc:
        raise ChangelogArchiveError(f"Invalid changelog archive JSON: {exc}") from exc

    entries = document.get("entries")
    if not isinstance(entries, list) or not all(isinstance(entry, dict) for entry in entries):
        raise ChangelogArchiveError("Changelog archive entries must be a list of objects")
    if document.get("schema") != 1 or document.get("kind") != ARCHIVE_KIND:
        raise ChangelogArchiveError("Changelog archive schema/kind mismatch")
    if document.get("entryOrder") != "newest-first":
        raise ChangelogArchiveError("Changelog archive entry order contract mismatch")
    if document.get("entryCount") != ARCHIVE_ENTRY_COUNT or len(entries) != ARCHIVE_ENTRY_COUNT:
        raise ChangelogArchiveError("Changelog archive must retain exactly 34 entries")
    digest = entries_sha256(entries)
    if digest != ARCHIVE_ENTRIES_SHA256 or document.get("entriesSha256") != digest:
        raise ChangelogArchiveError("Changelog archive entries SHA-256 mismatch")
    if document.get("source") != archive_document(entries)["source"]:
        raise ChangelogArchiveError("Changelog archive source identity mismatch")
    if document.get("createdByPatchId") != ARCHIVE_PATCH_ID:
        raise ChangelogArchiveError("Changelog archive patch identity mismatch")

    embedded = changelog.get("entries")
    if not isinstance(embedded, list) or len(embedded) < RETAINED_ENTRY_COUNT:
        raise ChangelogArchiveError("Embedded changelog no longer retains the 14-entry v062 window")
    if embedded[-RETAINED_ENTRY_COUNT:] != entries[:RETAINED_ENTRY_COUNT]:
        raise ChangelogArchiveError("Embedded changelog suffix no longer matches the archived v062 window")
    if changelog.get("latestVersionCode") != embedded[0].get("versionCode"):
        raise ChangelogArchiveError("Embedded changelog latestVersionCode does not match its first entry")
    return document


def validate_repository(root: Path = ROOT) -> None:
    _text, changelog = load_embedded(root / "kgg-update" / "src" / "metadata" / "changelog.html")
    validate_changelog_archives(changelog, root, required=True)
    version = json.loads((root / "kgg-update" / "version.json").read_text(encoding="utf-8"))
    entries = changelog["entries"]
    if version.get("versionCode") != entries[0].get("versionCode"):
        raise ChangelogArchiveError("version.json and embedded changelog versionCode differ")
    if version.get("versionName") != entries[0].get("versionName"):
        raise ChangelogArchiveError("version.json and embedded changelog versionName differ")
    parts = json.loads((root / "kgg-update" / "src" / "parts.json").read_text(encoding="utf-8"))
    if any(ARCHIVE_RELATIVE_PATH in str(item) for item in parts.get("parts", [])):
        raise ChangelogArchiveError("External changelog archive must never be embedded in parts.json")


def migrate(root: Path = ROOT) -> None:
    changelog_path = root / "kgg-update" / "src" / "metadata" / "changelog.html"
    archive_path = root / ARCHIVE_RELATIVE_PATH
    original_text, changelog = load_embedded(changelog_path)
    entries = changelog.get("entries")
    if archive_path.exists() or changelog.get("archiveSnapshots") is not None:
        raise ChangelogArchiveError("Changelog archive migration was already applied")
    if changelog.get("latestVersionCode") != ARCHIVE_VERSION_CODE:
        raise ChangelogArchiveError("Migration requires the unchanged v062 changelog")
    if not isinstance(entries, list) or len(entries) != ARCHIVE_ENTRY_COUNT:
        raise ChangelogArchiveError("Migration requires exactly 34 embedded v062 entries")
    if entries_sha256(entries) != ARCHIVE_ENTRIES_SHA256:
        raise ChangelogArchiveError("Migration input does not match the reviewed v062 changelog hash")

    archived_entries = deepcopy(entries)
    document = archive_document(archived_entries)
    compacted = deepcopy(changelog)
    compacted["entries"] = deepcopy(entries[:RETAINED_ENTRY_COUNT])
    compacted["archiveSnapshots"] = [archive_reference()]
    archive_raw = (json.dumps(document, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    changelog_raw = _replace_json_script(original_text, "kgg-changelog", compacted).encode("utf-8")

    try:
        builder.atomic_write(archive_path, archive_raw)
        builder.atomic_write(changelog_path, changelog_raw)
        validate_changelog_archives(compacted, root, required=True)
    except Exception:
        builder.atomic_write(changelog_path, original_text.encode("utf-8"))
        if archive_path.exists():
            archive_path.unlink()
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--migrate", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.migrate:
            migrate()
            print(f"Wrote {ARCHIVE_RELATIVE_PATH} and retained {RETAINED_ENTRY_COUNT} embedded v062 entries")
        else:
            validate_repository()
            print("KGG changelog archive OK")
        return 0
    except (OSError, UnicodeError, json.JSONDecodeError, ChangelogArchiveError, builder.BuildError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
