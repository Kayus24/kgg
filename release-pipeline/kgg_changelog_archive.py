#!/usr/bin/env python3
"""Create and verify immutable therapist changelog snapshots."""

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
CURRENT_RETAINED_ENTRY_COUNT = 15


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


def archive_document(
    entries: list[dict[str, Any]],
    *,
    source_version_code: int | None = None,
    source_version_name: str | None = None,
    created_by_patch_id: str | None = None,
) -> dict[str, Any]:
    if not entries or not isinstance(entries[0], dict):
        raise ChangelogArchiveError("Changelog archive needs at least one entry")
    first = entries[0]
    return {
        "schema": 1,
        "kind": ARCHIVE_KIND,
        "source": {
            "path": "kgg-update/src/metadata/changelog.html",
            "elementId": "kgg-changelog",
            "versionCode": source_version_code if source_version_code is not None else first.get("versionCode"),
            "versionName": source_version_name if source_version_name is not None else first.get("versionName"),
        },
        "createdByPatchId": created_by_patch_id or ARCHIVE_PATCH_ID,
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


def _archive_path(root: Path, reference: dict[str, Any]) -> Path:
    relative = reference.get("repositoryPath")
    if not isinstance(relative, str) or not relative.startswith("docs/changelog-archive/"):
        raise ChangelogArchiveError("Changelog archive path must stay under docs/changelog-archive")
    path = (root / relative).resolve()
    try:
        path.relative_to((root / "docs" / "changelog-archive").resolve())
    except ValueError as exc:
        raise ChangelogArchiveError("Changelog archive path escapes docs/changelog-archive") from exc
    return path


def _load_archive_document(reference: dict[str, Any], root: Path, *, legacy: bool) -> dict[str, Any]:
    path = _archive_path(root, reference)
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ChangelogArchiveError(f"Missing changelog archive: {reference.get('repositoryPath')}") from exc
    except json.JSONDecodeError as exc:
        raise ChangelogArchiveError(f"Invalid changelog archive JSON: {reference.get('repositoryPath')}") from exc

    entries = document.get("entries")
    if not isinstance(entries, list) or not entries or not all(isinstance(entry, dict) for entry in entries):
        raise ChangelogArchiveError("Changelog archive entries must be a non-empty list of objects")
    if document.get("schema") != 1 or document.get("kind") != ARCHIVE_KIND:
        raise ChangelogArchiveError("Changelog archive schema/kind mismatch")
    if document.get("entryOrder") != "newest-first":
        raise ChangelogArchiveError("Changelog archive entry order contract mismatch")
    digest = entries_sha256(entries)
    if document.get("entryCount") != len(entries) or document.get("entriesSha256") != digest:
        raise ChangelogArchiveError("Changelog archive entry count/hash mismatch")
    if document.get("source") != archive_document(entries)["source"]:
        raise ChangelogArchiveError("Changelog archive source identity mismatch")
    if document.get("createdByPatchId") != reference.get("createdByPatchId"):
        raise ChangelogArchiveError("Changelog archive patch identity mismatch")
    if reference.get("entryCount") != len(entries) or reference.get("entriesSha256") != digest:
        raise ChangelogArchiveError("Changelog archive reference count/hash mismatch")
    if reference.get("snapshotVersionCode") != entries[0].get("versionCode"):
        raise ChangelogArchiveError("Changelog archive reference version mismatch")
    if legacy:
        if reference != archive_reference():
            raise ChangelogArchiveError("kgg-changelog legacy archive reference does not match the v062 contract")
        if len(entries) != ARCHIVE_ENTRY_COUNT or digest != ARCHIVE_ENTRIES_SHA256:
            raise ChangelogArchiveError("Changelog archive must retain the reviewed 34-entry v062 snapshot")
        if document.get("source") != archive_document(entries)["source"]:
            raise ChangelogArchiveError("Changelog archive v062 source identity mismatch")
    return document


def validate_changelog_archives(
    changelog: dict[str, Any],
    root: Path = ROOT,
    *,
    required: bool = False,
) -> dict[str, Any] | None:
    snapshots = changelog.get("archiveSnapshots")
    if snapshots is None and not required:
        return None
    if not isinstance(snapshots, list) or not snapshots:
        raise ChangelogArchiveError("kgg-changelog.archiveSnapshots must contain at least the legacy v062 snapshot")
    if not all(isinstance(item, dict) for item in snapshots):
        raise ChangelogArchiveError("kgg-changelog.archiveSnapshots must contain objects")
    paths = [item.get("repositoryPath") for item in snapshots]
    if any(not isinstance(path, str) for path in paths):
        raise ChangelogArchiveError("kgg-changelog archive snapshot paths must be strings")
    if len(paths) != len(set(paths)):
        raise ChangelogArchiveError("kgg-changelog archive snapshot paths must be unique")

    legacy_refs = [item for item in snapshots if item == archive_reference()]
    if len(legacy_refs) != 1:
        raise ChangelogArchiveError("kgg-changelog.archiveSnapshots must contain exactly one legacy v062 snapshot")
    legacy_document = _load_archive_document(legacy_refs[0], root, legacy=True)

    current_documents: list[dict[str, Any]] = []
    for reference in snapshots:
        if reference == archive_reference():
            continue
        current_documents.append(_load_archive_document(reference, root, legacy=False))

    embedded = changelog.get("entries")
    if not isinstance(embedded, list) or not embedded:
        raise ChangelogArchiveError("Embedded changelog entries must be a non-empty list")
    if changelog.get("latestVersionCode") != embedded[0].get("versionCode"):
        raise ChangelogArchiveError("Embedded changelog latestVersionCode does not match its first entry")

    if current_documents:
        latest_document = max(current_documents, key=lambda item: int(item["source"]["versionCode"]))
        matching_references = [
            item for item in snapshots
            if item.get("createdByPatchId") == latest_document.get("createdByPatchId")
            and item.get("entriesSha256") == latest_document.get("entriesSha256")
        ]
        if len(matching_references) != 1:
            raise ChangelogArchiveError("Current changelog archive reference is ambiguous")
        matching_reference = matching_references[0]
        retained = matching_reference.get("retainedEntryCountAtCompaction")
        if not isinstance(retained, int) or retained < 1 or retained > len(latest_document["entries"]):
            raise ChangelogArchiveError("Current changelog archive retained-entry count is invalid")
        if embedded != latest_document["entries"][:retained]:
            raise ChangelogArchiveError("Embedded changelog no longer matches the latest full pre-compaction snapshot")
        return latest_document

    if len(embedded) < RETAINED_ENTRY_COUNT:
        raise ChangelogArchiveError("Embedded changelog no longer retains the 14-entry v062 window")
    if embedded[-RETAINED_ENTRY_COUNT:] != legacy_document["entries"][:RETAINED_ENTRY_COUNT]:
        raise ChangelogArchiveError("Embedded changelog suffix no longer matches the archived v062 window")
    return legacy_document


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


def compact_current(root: Path = ROOT, *, created_by_patch_id: str | None = None) -> dict[str, Any]:
    changelog_path = root / "kgg-update" / "src" / "metadata" / "changelog.html"
    original_text, changelog = load_embedded(changelog_path)
    validate_changelog_archives(changelog, root, required=True)
    entries = changelog.get("entries")
    if not isinstance(entries, list) or len(entries) <= CURRENT_RETAINED_ENTRY_COUNT:
        raise ChangelogArchiveError(
            f"Current changelog needs more than {CURRENT_RETAINED_ENTRY_COUNT} entries before compaction"
        )
    latest = entries[0]
    code = latest.get("versionCode")
    name = latest.get("versionName")
    patch_id = created_by_patch_id or latest.get("patchId")
    if not isinstance(code, int) or not isinstance(name, str) or not isinstance(patch_id, str) or not patch_id:
        raise ChangelogArchiveError("Current changelog latest entry has no valid archive identity")
    relative = f"docs/changelog-archive/kgg-therapist-changelog-through-v{code:03d}.json"
    archive_path = root / relative
    snapshots = changelog.get("archiveSnapshots")
    if not isinstance(snapshots, list):
        raise ChangelogArchiveError("kgg-changelog.archiveSnapshots must be a list")
    if any(item.get("repositoryPath") == relative for item in snapshots if isinstance(item, dict)):
        raise ChangelogArchiveError(f"Current changelog archive already exists: {relative}")

    document = archive_document(
        entries,
        source_version_code=code,
        source_version_name=name,
        created_by_patch_id=patch_id,
    )
    reference = {
        "repositoryPath": relative,
        "snapshotVersionCode": code,
        "entryCount": len(entries),
        "entriesSha256": document["entriesSha256"],
        "retainedEntryCountAtCompaction": CURRENT_RETAINED_ENTRY_COUNT,
        "createdByPatchId": patch_id,
    }
    compacted = deepcopy(changelog)
    compacted["entries"] = deepcopy(entries[:CURRENT_RETAINED_ENTRY_COUNT])
    compacted["archiveSnapshots"] = [*snapshots, reference]
    archive_raw = (json.dumps(document, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    changelog_raw = _replace_json_script(original_text, "kgg-changelog", compacted).encode("utf-8")
    old_archive = archive_path.read_bytes() if archive_path.exists() else None
    try:
        builder.atomic_write(archive_path, archive_raw)
        builder.atomic_write(changelog_path, changelog_raw)
        validate_repository(root)
    except Exception:
        builder.atomic_write(changelog_path, original_text.encode("utf-8"))
        if old_archive is None:
            try:
                archive_path.unlink()
            except FileNotFoundError:
                pass
        else:
            builder.atomic_write(archive_path, old_archive)
        raise
    return {
        "archivePath": relative,
        "snapshotVersionCode": code,
        "entryCount": len(entries),
        "retainedEntryCount": CURRENT_RETAINED_ENTRY_COUNT,
        "entriesSha256": document["entriesSha256"],
    }


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
    mode.add_argument("--compact-current", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.migrate:
            migrate()
            print(f"Wrote {ARCHIVE_RELATIVE_PATH} and retained {RETAINED_ENTRY_COUNT} embedded v062 entries")
        elif args.compact_current:
            result = compact_current()
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            validate_repository()
            print("KGG changelog archive OK")
        return 0
    except (OSError, UnicodeError, json.JSONDecodeError, ChangelogArchiveError, builder.BuildError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
