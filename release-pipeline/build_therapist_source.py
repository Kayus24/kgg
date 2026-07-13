#!/usr/bin/env python3
"""Deterministically assemble the modular KGG therapist HTML source."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "kgg-update" / "src" / "parts.json"


class BuildError(RuntimeError):
    pass


def read_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise BuildError(f"Cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise BuildError(f"JSON root must be an object: {path}")
    return value


def resolve_inside(base: Path, relative: str, label: str) -> Path:
    if not isinstance(relative, str) or not relative.strip():
        raise BuildError(f"{label} must be a non-empty relative path")
    candidate = (base / relative).resolve()
    try:
        candidate.relative_to(ROOT)
    except ValueError as exc:
        raise BuildError(f"{label} escapes repository root: {relative}") from exc
    return candidate


def read_utf8_bytes(path: Path) -> bytes:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise BuildError(f"Cannot read source part {path}: {exc}") from exc
    if raw.startswith(b"\xef\xbb\xbf"):
        raise BuildError(f"UTF-8 BOM is not allowed: {path}")
    if b"\r\n" in raw or b"\r" in raw:
        raise BuildError(f"Source parts must use LF line endings: {path}")
    try:
        raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise BuildError(f"Source part is not strict UTF-8: {path}: {exc}") from exc
    return raw


def load_build(manifest_path: Path) -> tuple[dict, Path, Path, list[Path], bytes]:
    manifest = read_json(manifest_path)
    if manifest.get("schema") != 1:
        raise BuildError("parts.json schema must be 1")
    base = manifest_path.parent
    output = resolve_inside(base, manifest.get("output", ""), "output")
    version = resolve_inside(base, manifest.get("versionManifest", ""), "versionManifest")
    raw_parts = manifest.get("parts")
    if not isinstance(raw_parts, list) or not raw_parts:
        raise BuildError("parts must be a non-empty list")
    if any(not isinstance(item, str) or not item for item in raw_parts):
        raise BuildError("every parts entry must be a non-empty string")
    if len(set(raw_parts)) != len(raw_parts):
        raise BuildError("parts contains duplicate paths")
    parts = [resolve_inside(base, item, "part") for item in raw_parts]
    assembled = b"".join(read_utf8_bytes(path) for path in parts)
    validate_assembled(assembled, manifest)
    return manifest, output, version, parts, assembled


def validate_assembled(raw: bytes, manifest: dict) -> None:
    try:
        html = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise BuildError(f"Assembled HTML is not strict UTF-8: {exc}") from exc
    if not html.startswith("<!doctype html>\n"):
        raise BuildError("assembled HTML must start with <!doctype html> and LF")
    if html.count("</body>") != 1 or html.count("</html>") != 1:
        raise BuildError("assembled HTML must contain exactly one closing body and html tag")
    if not html.endswith("</html>\n"):
        raise BuildError("assembled HTML must end with </html> and LF")
    if re.search(r"<script\b[^>]*\bsrc\s*=", html, flags=re.I):
        raise BuildError("runtime-loaded external scripts are not allowed")
    invariants = [
        "KGGDataStore.currentPlan",
        "<!-- KGG_ADMIN_ONLY_START -->",
        "<!-- KGG_ADMIN_ONLY_END -->",
        'id="kgg-source-truth"',
        'id="kgg-changelog"',
    ]
    missing = [token for token in invariants if token not in html]
    if missing:
        raise BuildError("assembled HTML lost required invariants: " + ", ".join(missing))
    patch_ids = manifest.get("requiredPatchIds")
    if not isinstance(patch_ids, list) or not patch_ids:
        raise BuildError("requiredPatchIds must be a non-empty list")
    for patch_id in patch_ids:
        start = f"<!-- KGG PATCH START {patch_id} -->"
        end = f"<!-- KGG PATCH END {patch_id} -->"
        if html.count(start) != 1 or html.count(end) != 1:
            raise BuildError(f"patch markers must occur exactly once: {patch_id}")
        if html.index(start) >= html.index(end):
            raise BuildError(f"patch end precedes start: {patch_id}")
    positions = [html.index(f"<!-- KGG PATCH START {patch_id} -->") for patch_id in patch_ids]
    if positions != sorted(positions):
        raise BuildError("required patch order differs from parts.json")


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def atomic_write(path: Path, raw: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(raw)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except OSError:
            pass
        raise


def check_version(version_path: Path, expected_digest: str) -> dict:
    version = read_json(version_path)
    if version.get("sha256") != expected_digest:
        raise BuildError(
            f"version manifest hash mismatch: {version.get('sha256')} != {expected_digest}"
        )
    code = version.get("versionCode")
    if not isinstance(code, int) or code <= 0:
        raise BuildError("versionCode must be a positive integer")
    if version.get("indexUrl") != f"index.html?v={code}":
        raise BuildError("version indexUrl must match versionCode")
    return version


def check(manifest_path: Path) -> str:
    _, output, version_path, parts, assembled = load_build(manifest_path)
    try:
        current = output.read_bytes()
    except OSError as exc:
        raise BuildError(f"Cannot read generated output {output}: {exc}") from exc
    if current != assembled:
        raise BuildError(
            "generated index.html differs from modular source; run "
            "python release-pipeline/build_therapist_source.py --write"
        )
    expected_digest = digest(assembled)
    check_version(version_path, expected_digest)
    return f"KGG module source OK: {len(parts)} parts, {len(assembled)} bytes, sha256={expected_digest}"


def write(manifest_path: Path) -> str:
    _, output, version_path, parts, assembled = load_build(manifest_path)
    expected_digest = digest(assembled)
    if not output.exists() or output.read_bytes() != assembled:
        atomic_write(output, assembled)
    version = read_json(version_path)
    if version.get("sha256") != expected_digest:
        version["sha256"] = expected_digest
        serialized = (json.dumps(version, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        atomic_write(version_path, serialized)
    check_version(version_path, expected_digest)
    return f"Built KGG therapist HTML: {len(parts)} parts, {len(assembled)} bytes, sha256={expected_digest}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--check", action="store_true", help="verify source/output/hash without writing")
    action.add_argument("--write", action="store_true", help="atomically rebuild output and hash")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    args = parser.parse_args()
    try:
        message = check(args.manifest.resolve()) if args.check else write(args.manifest.resolve())
        print(message)
        return 0
    except BuildError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
