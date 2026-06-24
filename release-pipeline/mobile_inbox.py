#!/usr/bin/env python3
"""Validate a phone-uploaded KGG Admin HTML and create release metadata.

The mobile inbox path is intentionally small: a phone browser only uploads one
HTML file. This helper verifies that the file is based on the current KGG source
truth, writes release-inbox/admin.html and release-inbox/release.json, then the
normal immutable release pipeline can take over.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
from pathlib import Path

import release_pipeline as pipeline


SECRET_PATTERN = re.compile(
    "("
    + "|".join(
        (
            "sk-" + "proj-",
            "gh" + "[pousr]_" + "[A-Za-z0-9_]{20,}",
            "AI" + "za" + "[0-9A-Za-z_-]{25,}",
        )
    )
    + ")"
)
VERSION_PATTERNS = (
    re.compile(r"KGG_GITHUB_UPDATE_v0*([0-9]+)", re.I),
    re.compile(r"<title>\s*KGG\s+Update\s+v0*([0-9]+)\b", re.I),
)


def html_version_code(html: str) -> int | None:
    for pattern in VERSION_PATTERNS:
        match = pattern.search(html)
        if match:
            return int(match.group(1))
    return None


def html_title(html: str) -> str:
    match = re.search(r"<title>(.*?)</title>", html, re.I | re.S)
    if not match:
        return "Admin HTML vom Handy"
    title = re.sub(r"\s+", " ", match.group(1)).strip()
    return title[:90] or "Admin HTML vom Handy"


def next_release_id(root: Path) -> str:
    numbers: set[int] = set()
    releases = root / "therapist-app" / "releases" / "web"
    if releases.exists():
        for child in releases.iterdir():
            if child.is_dir():
                match = re.fullmatch(r"r([0-9]{3,8})", child.name)
                if match:
                    numbers.add(int(match.group(1)))
    manifest_path = root / "therapist-app" / "android_update_manifest.json"
    if manifest_path.exists():
        manifest = pipeline.load_json(manifest_path)
        candidates = [manifest.get("latestWebVersion"), manifest.get("adminHtmlUrl"), manifest.get("colleagueHtmlUrl")]
        channels = manifest.get("channels") if isinstance(manifest.get("channels"), dict) else {}
        for channel in channels.values():
            if isinstance(channel, dict):
                candidates.append(channel.get("releaseId"))
                candidates.append(channel.get("url"))
        for value in candidates:
            for match in re.finditer(r"r([0-9]{3,8})", str(value or "")):
                numbers.add(int(match.group(1)))
    if not numbers:
        pipeline.fail("Cannot determine next mobile inbox release ID")
    return f"r{max(numbers) + 1:04d}"


def validate_mobile_candidate(candidate: Path, root: Path) -> tuple[str, int]:
    html = pipeline.read_text(candidate)
    pipeline.validate_html(html, "Mobile Inbox candidate")
    if SECRET_PATTERN.search(html):
        pipeline.fail("Mobile Inbox candidate contains a token-shaped secret")

    current_version = pipeline.load_json(root / "kgg-update" / "version.json")
    current_code = current_version.get("versionCode")
    if not isinstance(current_code, int):
        pipeline.fail("kgg-update/version.json versionCode must be an integer")
    candidate_code = html_version_code(html)
    if candidate_code is None:
        pipeline.fail("Mobile Inbox candidate is missing KGG_GITHUB_UPDATE_vNNN or title version marker")
    if candidate_code < current_code:
        pipeline.fail(
            f"Mobile Inbox candidate is based on v{candidate_code:03d}, "
            f"but current source truth is v{current_code:03d}"
        )

    colleague = pipeline.derive_colleague(html)
    pipeline.validate_html(colleague, "Mobile Inbox colleague build")
    if pipeline.sha256_text(html) == pipeline.sha256_text(colleague):
        pipeline.fail("Mobile Inbox Admin and colleague builds would be identical")
    return html, current_code


def prepare(candidate: Path, release_json: Path, copy_to: Path, root: Path) -> dict:
    html, current_code = validate_mobile_candidate(candidate, root)
    release_id = next_release_id(root)
    version_name = f"1.0.{current_code + 1}-mobile-inbox-{release_id}"
    digest = hashlib.sha256(html.encode("utf-8")).hexdigest()[:12]
    notes = f"Mobile-Inbox {release_id}: {html_title(html)} ({digest})."

    copy_to.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(candidate, copy_to)
    release_json.parent.mkdir(parents=True, exist_ok=True)
    release = {
        "releaseId": release_id,
        "versionName": version_name,
        "notes": notes,
    }
    release_json.write_text(json.dumps(release, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return release


def write_github_output(path: str | None, values: dict[str, str]) -> None:
    if not path:
        return
    with open(path, "a", encoding="utf-8") as output:
        for key, value in values.items():
            if "\n" in value:
                output.write(f"{key}<<KGG_EOF\n{value}\nKGG_EOF\n")
            else:
                output.write(f"{key}={value}\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--release-json", required=True, type=Path)
    parser.add_argument("--copy-to", required=True, type=Path)
    parser.add_argument("--root", default=pipeline.ROOT, type=Path)
    parser.add_argument("--github-output", default=os.environ.get("GITHUB_OUTPUT"))
    args = parser.parse_args()

    try:
        root = args.root.resolve()
        release = prepare(args.candidate.resolve(), (root / args.release_json).resolve(), (root / args.copy_to).resolve(), root)
        print(json.dumps(release, ensure_ascii=False, indent=2))
        outputs = {key: str(value) for key, value in release.items()}
        outputs.update({
            "release_id": str(release["releaseId"]),
            "version_name": str(release["versionName"]),
        })
        write_github_output(args.github_output, outputs)
        return 0
    except pipeline.ReleaseError as exc:
        print(f"ERROR: {exc}", file=os.sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
