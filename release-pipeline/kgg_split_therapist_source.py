#!/usr/bin/env python3
"""Split contiguous therapist source parts without changing the assembled bytes."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

import build_therapist_source as builder


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "kgg-update" / "src" / "parts.json"


class SplitError(RuntimeError):
    pass


@dataclass(frozen=True)
class Segment:
    relative: str
    path: Path
    raw: bytes


@dataclass(frozen=True)
class SplitPlan:
    manifest: dict
    manifest_raw: bytes
    source_paths: tuple[Path, ...]
    segments: tuple[Segment, ...]
    assembled: bytes


def read_plan(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SplitError(f"Cannot read split plan {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SplitError("split plan root must be an object")
    if value.get("schema") != 1:
        raise SplitError("split plan schema must be 1")
    return value


def source_relative_path(base: Path, value: object, label: str) -> tuple[str, Path]:
    if not isinstance(value, str) or not value.strip() or "\\" in value:
        raise SplitError(f"{label} must be a non-empty POSIX relative path")
    posix = PurePosixPath(value)
    if posix.is_absolute() or any(part in ("", ".", "..") for part in posix.parts):
        raise SplitError(f"{label} must stay inside the source root: {value}")
    relative = posix.as_posix()
    path = (base / Path(*posix.parts)).resolve()
    try:
        path.relative_to(base.resolve())
    except ValueError as exc:
        raise SplitError(f"{label} escapes the source root: {value}") from exc
    return relative, path


def anchor_bytes(value: object, label: str) -> bytes:
    if not isinstance(value, str) or not value:
        raise SplitError(f"{label} must be a non-empty UTF-8 string")
    if "\r" in value:
        raise SplitError(f"{label} must use LF line endings")
    try:
        return value.encode("utf-8", errors="strict")
    except UnicodeEncodeError as exc:
        raise SplitError(f"{label} is not strict UTF-8: {exc}") from exc


def occurrence_offsets(raw: bytes, needle: bytes) -> list[int]:
    offsets: list[int] = []
    cursor = 0
    while True:
        offset = raw.find(needle, cursor)
        if offset < 0:
            return offsets
        offsets.append(offset)
        cursor = offset + 1


def prepare(plan_path: Path, manifest_path: Path = DEFAULT_MANIFEST) -> SplitPlan:
    plan = read_plan(plan_path)
    manifest_path = manifest_path.resolve()
    manifest, _output, _version, _current_paths, assembled = builder.load_build(manifest_path)
    base = manifest_path.parent.resolve()
    raw_parts = manifest.get("parts")
    assert isinstance(raw_parts, list)  # validated by builder.load_build

    raw_sources = plan.get("sourceParts")
    if not isinstance(raw_sources, list) or not raw_sources:
        raise SplitError("sourceParts must be a non-empty list")
    source_entries: list[str] = []
    source_paths: list[Path] = []
    for index, value in enumerate(raw_sources):
        relative, path = source_relative_path(base, value, f"sourceParts[{index}]")
        source_entries.append(relative)
        source_paths.append(path)
    if len(set(source_entries)) != len(source_entries):
        raise SplitError("sourceParts contains duplicate paths")
    try:
        first_index = raw_parts.index(source_entries[0])
    except ValueError as exc:
        raise SplitError(f"source part is not present in parts.json: {source_entries[0]}") from exc
    if raw_parts[first_index : first_index + len(source_entries)] != source_entries:
        raise SplitError("sourceParts must match one contiguous, ordered range in parts.json")

    source_raw = b"".join(builder.read_utf8_bytes(path) for path in source_paths)
    raw_segments = plan.get("segments")
    if not isinstance(raw_segments, list) or len(raw_segments) < 2:
        raise SplitError("segments must contain at least two output definitions")

    segment_entries: list[str] = []
    segment_paths: list[Path] = []
    boundary_offsets = [0]
    for index, item in enumerate(raw_segments):
        if not isinstance(item, dict):
            raise SplitError(f"segments[{index}] must be an object")
        relative, path = source_relative_path(base, item.get("path"), f"segments[{index}].path")
        segment_entries.append(relative)
        segment_paths.append(path)
        if index == 0:
            if "startAnchor" in item:
                raise SplitError("segments[0] must not define startAnchor")
            continue
        if "startAnchor" not in item:
            raise SplitError(f"segments[{index}].startAnchor is required")
        anchor = anchor_bytes(item.get("startAnchor"), f"segments[{index}].startAnchor")
        occurrences = occurrence_offsets(source_raw, anchor)
        count = len(occurrences)
        if count == 0:
            raise SplitError(f"segments[{index}].startAnchor is missing from source bytes")
        if count != 1:
            raise SplitError(
                f"segments[{index}].startAnchor must occur exactly once; found {count}"
            )
        boundary_offsets.append(occurrences[0])

    if len(set(segment_entries)) != len(segment_entries):
        raise SplitError("segments contains duplicate output paths")
    overlap = sorted(set(segment_entries) & set(source_entries))
    if overlap:
        raise SplitError("segment output paths must differ from sourceParts: " + ", ".join(overlap))
    existing_parts = set(raw_parts) - set(source_entries)
    collision = sorted(set(segment_entries) & existing_parts)
    if collision:
        raise SplitError("segment output paths already exist in parts.json: " + ", ".join(collision))
    existing_files = [relative for relative, path in zip(segment_entries, segment_paths) if path.exists()]
    if existing_files:
        raise SplitError("segment output files already exist: " + ", ".join(existing_files))
    if boundary_offsets != sorted(boundary_offsets) or len(set(boundary_offsets)) != len(boundary_offsets):
        raise SplitError("segment anchors are in the wrong order")
    boundary_offsets.append(len(source_raw))

    segments: list[Segment] = []
    for index, (relative, path) in enumerate(zip(segment_entries, segment_paths)):
        raw = source_raw[boundary_offsets[index] : boundary_offsets[index + 1]]
        if not raw:
            raise SplitError(f"segments[{index}] would be empty")
        segments.append(Segment(relative=relative, path=path, raw=raw))
    if b"".join(segment.raw for segment in segments) != source_raw:
        raise SplitError("internal byte-identity check failed while splitting source range")

    candidate = copy.deepcopy(manifest)
    candidate["parts"] = [
        *raw_parts[:first_index],
        *segment_entries,
        *raw_parts[first_index + len(source_entries) :],
    ]
    raw_role_updates = plan.get("sourceRoleUpdates", {})
    if not isinstance(raw_role_updates, dict):
        raise SplitError("sourceRoleUpdates must be an object")
    candidate_roles = candidate.get("sourceRoles")
    if not isinstance(candidate_roles, dict):
        raise SplitError("parts.json sourceRoles must be an object")
    for role, value in raw_role_updates.items():
        if role not in candidate_roles:
            raise SplitError(f"sourceRoleUpdates contains unknown role: {role}")
        relative, _path = source_relative_path(base, value, f"sourceRoleUpdates.{role}")
        if relative not in segment_entries:
            raise SplitError(f"sourceRoleUpdates.{role} must reference a segment output: {relative}")
        candidate_roles[role] = relative
    try:
        builder.resolve_source_roles(candidate, manifest_path)
    except builder.BuildError as exc:
        raise SplitError(f"candidate sourceRoles are invalid: {exc}") from exc

    segment_by_path = {segment.path: segment.raw for segment in segments}
    candidate_paths = [builder.resolve_inside(base, item, "part") for item in candidate["parts"]]
    candidate_assembled = b"".join(
        segment_by_path[path] if path in segment_by_path else builder.read_utf8_bytes(path)
        for path in candidate_paths
    )
    if candidate_assembled != assembled:
        raise SplitError(
            "candidate assembly is not byte-identical to the current therapist source "
            f"({hashlib.sha256(candidate_assembled).hexdigest()} != {hashlib.sha256(assembled).hexdigest()})"
        )
    builder.validate_assembled(candidate_assembled, candidate)
    manifest_raw = (json.dumps(candidate, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    return SplitPlan(
        manifest=candidate,
        manifest_raw=manifest_raw,
        source_paths=tuple(source_paths),
        segments=tuple(segments),
        assembled=candidate_assembled,
    )


def apply(plan: SplitPlan, manifest_path: Path = DEFAULT_MANIFEST) -> None:
    """Install outputs + manifest and roll every touched path back on failure."""
    manifest_path = manifest_path.resolve()
    touched = [manifest_path, *plan.source_paths, *(segment.path for segment in plan.segments)]
    originals = {path: path.read_bytes() if path.exists() else None for path in touched}
    try:
        for segment in plan.segments:
            builder.atomic_write(segment.path, segment.raw)
        builder.atomic_write(manifest_path, plan.manifest_raw)
        builder.check(manifest_path)
        for source_path in plan.source_paths:
            source_path.unlink()
        builder.check(manifest_path)
    except BaseException:
        for path in reversed(touched):
            raw = originals[path]
            if raw is None:
                try:
                    path.unlink()
                except FileNotFoundError:
                    pass
            else:
                builder.atomic_write(path, raw)
        raise


def summary(plan: SplitPlan, *, wrote: bool) -> str:
    digest = hashlib.sha256(plan.assembled).hexdigest()
    mode = "wrote" if wrote else "validated"
    return (
        f"KGG source split {mode}: {len(plan.source_paths)} source part(s) -> "
        f"{len(plan.segments)} segment(s), {len(plan.assembled)} assembled bytes, sha256={digest}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--check", action="store_true", help="validate the split plan without writing")
    action.add_argument("--write", action="store_true", help="apply the split as one rollback-safe transaction")
    parser.add_argument("--plan", type=Path, required=True, help="UTF-8 JSON split plan")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()
    try:
        prepared = prepare(args.plan.resolve(), args.manifest.resolve())
        if args.write:
            apply(prepared, args.manifest.resolve())
        print(summary(prepared, wrote=args.write))
        return 0
    except (OSError, UnicodeError, SplitError, builder.BuildError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
