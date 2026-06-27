#!/usr/bin/env python3
"""Guard KGG PRs against dirty or half-prepared patch states."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class HygieneError(RuntimeError):
    pass


def log(message: str) -> None:
    print(message, flush=True)


def git(args: list[str], root: Path, *, check: bool = True) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(["git", *args], cwd=str(root), text=True, capture_output=True)
    if check and proc.returncode != 0:
        details = (proc.stderr or proc.stdout or "").strip()
        raise HygieneError(f"git {' '.join(args)} failed ({proc.returncode}): {details}")
    return proc


def normalize_path(path: str) -> str:
    return path.strip().replace("\\", "/").strip('"')


def status_paths(root: Path) -> set[str]:
    proc = git(["status", "--porcelain=v1", "--untracked-files=all"], root)
    paths: set[str] = set()
    for raw in proc.stdout.splitlines():
        if not raw:
            continue
        payload = raw[3:] if len(raw) > 3 else raw
        if " -> " in payload:
            left, right = payload.split(" -> ", 1)
            paths.add(normalize_path(left))
            paths.add(normalize_path(right))
        else:
            paths.add(normalize_path(payload))
    return {path for path in paths if path}


def changed_paths_since_main(root: Path) -> set[str]:
    if git(["rev-parse", "--verify", "origin/main"], root, check=False).returncode != 0:
        raise HygieneError("Cannot find origin/main. Run `git fetch origin main` before the test battery.")
    proc = git(["diff", "--name-only", "origin/main...HEAD"], root)
    return {normalize_path(line) for line in proc.stdout.splitlines() if line.strip()}


def is_origin_main_ancestor(root: Path) -> bool:
    return git(["merge-base", "--is-ancestor", "origin/main", "HEAD"], root, check=False).returncode == 0


def file_exists(root: Path, path: str) -> bool:
    return (root / path).exists()


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - surfaced as a hygiene error
        raise HygieneError(f"Cannot read JSON {path}: {exc}") from exc


def lf_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def html_version_marker(path: Path) -> int | None:
    if not path.exists() or not path.is_file():
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    for pattern in (
        r"KGG_GITHUB_UPDATE_v0*([0-9]+)",
        r"<title>\s*KGG\s+Update\s+v0*([0-9]+)\b",
    ):
        match = re.search(pattern, text, re.I)
        if match:
            return int(match.group(1))
    return None


def manifest_admin_html(root: Path) -> Path | None:
    manifest_path = root / "therapist-app" / "android_update_manifest.json"
    if not manifest_path.exists():
        return None
    manifest = read_json(manifest_path)
    admin_url = str(manifest.get("adminHtmlUrl") or manifest.get("channels", {}).get("admin", {}).get("url") or "")
    match = re.search(r"/therapist-app/releases/web/(r[0-9]{4,})/admin\.html$", admin_url)
    if not match:
        return None
    return root / "therapist-app" / "releases" / "web" / match.group(1) / "admin.html"


def assert_no_test_lab(paths: set[str]) -> None:
    blocked = sorted(path for path in paths if path == "therapist-app/test-lab" or path.startswith("therapist-app/test-lab/"))
    if blocked and os.environ.get("KGG_ALLOW_TEST_LAB_IN_RELEASE") != "1":
        sample = ", ".join(blocked[:6])
        raise HygieneError(
            "Patch hygiene blocked therapist-app/test-lab changes in a release/app PR. "
            f"Keep idea experiments out of release branches: {sample}"
        )


def assert_release_inbox_pair(root: Path) -> None:
    admin = file_exists(root, "release-inbox/admin.html")
    release = file_exists(root, "release-inbox/release.json")
    if admin != release:
        raise HygieneError(
            "release-inbox is half-prepared. "
            "release-inbox/admin.html and release-inbox/release.json must both exist or both be absent."
        )


def assert_version_json_for_index(root: Path, touched: set[str]) -> None:
    if "kgg-update/index.html" not in touched:
        return
    if "kgg-update/version.json" not in touched:
        raise HygieneError("kgg-update/index.html changed, but kgg-update/version.json was not changed.")

    version_path = root / "kgg-update" / "version.json"
    index_path = root / "kgg-update" / "index.html"
    data = read_json(version_path)
    digest = lf_sha256(index_path)
    if data.get("sha256") != digest:
        raise HygieneError(
            "kgg-update/version.json sha256 must match kgg-update/index.html "
            f"using LF-normalized hashing. expected={digest} actual={data.get('sha256')}"
        )
    version_code = data.get("versionCode")
    if data.get("indexUrl") != f"index.html?v={version_code}":
        raise HygieneError("kgg-update/version.json indexUrl must match versionCode.")


def assert_source_release_alignment(root: Path) -> None:
    source_code = html_version_marker(root / "kgg-update" / "index.html")
    if source_code is None:
        raise HygieneError("Cannot read KGG source version marker from kgg-update/index.html.")

    inbox_code = html_version_marker(root / "release-inbox" / "admin.html")
    if inbox_code == source_code:
        return

    admin_path = manifest_admin_html(root)
    admin_code = html_version_marker(admin_path) if admin_path else None
    if admin_code == source_code:
        return

    if os.environ.get("KGG_ALLOW_RELEASE_DRIFT") == "1":
        log(
            "WARN: Patch hygiene allows source/release drift because KGG_ALLOW_RELEASE_DRIFT=1 "
            f"(source v{source_code:03d}, release-inbox v{inbox_code}, manifest admin v{admin_code})."
        )
        return

    raise HygieneError(
        "kgg-update source is not aligned with a prepared/live Admin release "
        f"(source v{source_code:03d}, release-inbox v{inbox_code}, manifest admin v{admin_code}). "
        "Add release-inbox/admin.html + release-inbox/release.json, or set KGG_ALLOW_RELEASE_DRIFT=1 for an explicit no-release PR."
    )


def run(root: Path) -> None:
    changed = changed_paths_since_main(root)
    dirty = status_paths(root)
    touched = changed | dirty

    if not is_origin_main_ancestor(root):
        message = "Current branch is stale: origin/main is not an ancestor of HEAD. Start from fresh origin/main."
        if os.environ.get("KGG_ALLOW_STALE_BRANCH") == "1":
            log("WARN: " + message + " Continuing because KGG_ALLOW_STALE_BRANCH=1.")
        else:
            raise HygieneError(message)

    assert_no_test_lab(touched)
    assert_release_inbox_pair(root)
    assert_version_json_for_index(root, touched)
    assert_source_release_alignment(root)
    log("Patch hygiene OK")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check KGG patch hygiene before release/test batteries.")
    parser.add_argument("--root", default=ROOT, type=Path)
    args = parser.parse_args()

    try:
        run(args.root.resolve())
        return 0
    except HygieneError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
