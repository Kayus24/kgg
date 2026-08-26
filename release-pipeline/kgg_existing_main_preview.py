#!/usr/bin/env python3
"""Publish an exact pinned main HTML into the existing GPT Preview web channel."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REQUEST_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{5,63}$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
HASH_RE = re.compile(r"^[0-9a-f]{64}$")
PREVIEW_KIND = "kgg_gpt_preview"
MANIFEST_KIND = "kgg_gpt_preview_manifest"
PREVIEW_BASE_URL = "https://raw.githubusercontent.com/Kayus24/kgg/gpt-preview/previews"


class PreviewError(RuntimeError):
    pass


def fail(message: str) -> None:
    raise PreviewError(message)


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read JSON {path}: {exc}")
    if not isinstance(value, dict):
        fail(f"JSON root must be an object: {path}")
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_version_matches(version: dict[str, Any], html: bytes) -> bool:
    expected = str(version.get("sha256") or "").strip().lower()
    if not HASH_RE.fullmatch(expected):
        return False
    raw = sha256_hex(html)
    normalized = sha256_hex(html.replace(b"\r\n", b"\n").replace(b"\r", b"\n"))
    return expected in {raw, normalized}


def next_rollout_code(index: dict[str, Any]) -> int:
    values: list[int] = []
    latest = index.get("latest")
    if isinstance(latest, dict) and isinstance(latest.get("rolloutCode"), int):
        values.append(latest["rolloutCode"])
    previews = index.get("previews")
    if isinstance(previews, list):
        values.extend(
            item["rolloutCode"]
            for item in previews
            if isinstance(item, dict) and isinstance(item.get("rolloutCode"), int)
        )
    return max(int(time.time()), max(values, default=0) + 1)


def stage_preview(
    *,
    source_html: Path,
    version_json: Path,
    preview_root: Path,
    request_id: str,
    source_sha: str,
    patch_hash: str,
    rollout_code: int | None = None,
    created_at: str | None = None,
) -> dict[str, Any]:
    if not REQUEST_ID_RE.fullmatch(request_id):
        fail("request_id contains unsupported characters")
    if not SHA_RE.fullmatch(source_sha):
        fail("source_sha must be a full lowercase commit SHA")
    if not HASH_RE.fullmatch(patch_hash):
        fail("patch_hash must be a lowercase SHA-256 hex digest")

    html = source_html.read_bytes()
    if not html.lower().startswith(b"<!doctype html>"):
        fail("pinned kgg-update/index.html is not a complete HTML document")
    version = read_json(version_json)
    if not canonical_version_matches(version, html):
        fail("kgg-update/version.json does not match the pinned index.html")

    version_code = version.get("versionCode")
    version_name = str(version.get("versionName") or "").strip()
    if not isinstance(version_code, int) or version_code <= 0 or not version_name:
        fail("pinned version.json has invalid version metadata")

    index_path = preview_root / "previews" / "index.json"
    if index_path.exists():
        index = read_json(index_path)
        if index.get("kind") != MANIFEST_KIND:
            fail("existing Preview index has an unexpected kind")
        if not isinstance(index.get("previews"), list):
            fail("existing Preview index previews must be a list")
    else:
        index = {"kind": MANIFEST_KIND, "version": 1, "previews": []}

    if rollout_code is None:
        rollout_code = next_rollout_code(index)
    if not isinstance(rollout_code, int) or rollout_code <= 0:
        fail("rollout_code must be positive")

    created_at = created_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    html_sha = sha256_hex(html)
    preview_dir = preview_root / "previews" / request_id
    html_path = preview_dir / "admin.html"
    meta_path = preview_dir / "meta.json"
    preview_dir.mkdir(parents=True, exist_ok=True)
    html_path.write_bytes(html)

    meta: dict[str, Any] = {
        "kind": PREVIEW_KIND,
        "sourceType": "existing-main",
        "requestId": request_id,
        "patchHash": patch_hash,
        "sourceSha": source_sha,
        "baseSha": source_sha,
        "commitSha": source_sha,
        "baseVersionCode": version_code,
        "rolloutCode": rollout_code,
        "title": "Pinned main device test",
        "summary": "Exact kgg-update/index.html from the pinned main commit; no GPT patch module was created.",
        "versionName": version_name,
        "createdAt": created_at,
        "url": f"{PREVIEW_BASE_URL}/{request_id}/admin.html",
        "sha256": html_sha,
    }
    write_json(meta_path, meta)

    previews = [
        item
        for item in index["previews"]
        if isinstance(item, dict) and item.get("requestId") != request_id
    ]
    index["previews"] = [meta, *previews][:20]
    index["latest"] = meta
    write_json(index_path, index)

    if html_path.read_bytes() != html:
        fail("staged Preview HTML differs from pinned source bytes")
    if read_json(meta_path).get("sourceSha") != source_sha:
        fail("staged Preview metadata lost the exact source_sha")
    return meta


def write_github_output(path: str | None, meta: dict[str, Any]) -> None:
    if not path:
        return
    with Path(path).open("a", encoding="utf-8", newline="\n") as handle:
        for key, value in (
            ("preview_url", meta["url"]),
            ("preview_source_sha", meta["sourceSha"]),
            ("preview_rollout_code", meta["rolloutCode"]),
        ):
            handle.write(f"{key}={value}\n")


def self_test() -> None:
    html = b"<!doctype html><html><head><meta charset=\"utf-8\"></head><body>KGG pinned</body></html>\n"
    source_sha = "b" * 40
    patch_hash = "c" * 64
    with tempfile.TemporaryDirectory(prefix="kgg-existing-main-preview-") as tmp:
        root = Path(tmp)
        source = root / "source"
        preview = root / "preview"
        source.mkdir()
        (source / "index.html").write_bytes(html)
        write_json(
            source / "version.json",
            {
                "versionCode": 81,
                "versionName": "1.0.81-self-test",
                "indexUrl": "index.html?v=81",
                "sha256": sha256_hex(html),
            },
        )
        write_json(
            preview / "previews" / "index.json",
            {
                "kind": MANIFEST_KIND,
                "version": 1,
                "previews": [
                    {
                        "kind": PREVIEW_KIND,
                        "requestId": "older-preview",
                        "rolloutCode": 99,
                    }
                ],
                "latest": {
                    "kind": PREVIEW_KIND,
                    "requestId": "older-preview",
                    "rolloutCode": 99,
                },
            },
        )
        before_source = {
            path.relative_to(source): path.read_bytes()
            for path in source.rglob("*")
            if path.is_file()
        }
        meta = stage_preview(
            source_html=source / "index.html",
            version_json=source / "version.json",
            preview_root=preview,
            request_id="existing-main-self-test",
            source_sha=source_sha,
            patch_hash=patch_hash,
            rollout_code=100,
            created_at="2026-08-26T00:00:00Z",
        )
        after_source = {
            path.relative_to(source): path.read_bytes()
            for path in source.rglob("*")
            if path.is_file()
        }
        if before_source != after_source:
            fail("Existing-Main Preview modified canonical source files")
        if (preview / "previews" / "existing-main-self-test" / "admin.html").read_bytes() != html:
            fail("Existing-Main Preview did not preserve exact HTML bytes")
        if meta.get("sourceSha") != source_sha or meta.get("baseSha") != source_sha:
            fail("Existing-Main Preview metadata does not pin source_sha")
        if "patchFile" in meta or "patchId" in meta:
            fail("Existing-Main Preview must not pretend to own a vNNN patch module")
        index = read_json(preview / "previews" / "index.json")
        if index.get("latest", {}).get("requestId") != "existing-main-self-test":
            fail("Existing-Main Preview was not promoted to Preview latest")
        if index.get("latest", {}).get("sourceSha") != source_sha:
            fail("Preview latest does not expose exact source_sha")
        if [item.get("requestId") for item in index["previews"]].count("existing-main-self-test") != 1:
            fail("Existing-Main Preview duplicated the request in Preview index")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-html", type=Path)
    parser.add_argument("--version-json", type=Path)
    parser.add_argument("--preview-root", type=Path)
    parser.add_argument("--request-id")
    parser.add_argument("--source-sha")
    parser.add_argument("--patch-hash")
    parser.add_argument("--github-output")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    try:
        if args.self_test:
            self_test()
            print("KGG existing-main Preview self-test OK")
            return 0
        required = {
            "--source-html": args.source_html,
            "--version-json": args.version_json,
            "--preview-root": args.preview_root,
            "--request-id": args.request_id,
            "--source-sha": args.source_sha,
            "--patch-hash": args.patch_hash,
        }
        missing = [name for name, value in required.items() if value is None]
        if missing:
            fail("missing required arguments: " + ", ".join(missing))
        meta = stage_preview(
            source_html=args.source_html.resolve(),
            version_json=args.version_json.resolve(),
            preview_root=args.preview_root.resolve(),
            request_id=args.request_id,
            source_sha=args.source_sha,
            patch_hash=args.patch_hash,
        )
        write_github_output(args.github_output, meta)
        print(json.dumps(meta, ensure_ascii=False, sort_keys=True))
        return 0
    except (PreviewError, OSError) as exc:
        print(f"ERROR: {exc}", file=os.sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
