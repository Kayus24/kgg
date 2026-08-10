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
    re.compile(r"\bconst\s+VERSION\s*=\s*['\"]KGG_GITHUB_UPDATE_v([0-9]{3,8})_[a-z0-9_]+['\"]", re.I),
    re.compile(r"<title>\s*KGG\s+Update\s+v0*([0-9]+)\b", re.I),
)
SOURCE_TRUTH_PATTERN = re.compile(
    r"^[ \t]*<script\b[^>]*\bid=['\"]kgg-source-truth['\"][^>]*>\s*(.*?)\s*</script>",
    re.I | re.M | re.S,
)


def html_version_code(html: str) -> int | None:
    for pattern in VERSION_PATTERNS:
        match = pattern.search(html)
        if match:
            return int(match.group(1))
    return None


def html_source_marker_code(html: str) -> int | None:
    match = VERSION_PATTERNS[0].search(html)
    return int(match.group(1)) if match else None


def html_title(html: str) -> str:
    match = re.search(r"<title>(.*?)</title>", html, re.I | re.S)
    if not match:
        return "Admin HTML vom Handy"
    title = re.sub(r"\s+", " ", match.group(1)).strip()
    return title[:90] or "Admin HTML vom Handy"


def html_source_identity(html: str) -> tuple[int, str]:
    matches = SOURCE_TRUTH_PATTERN.findall(html)
    if len(matches) != 1:
        pipeline.fail("Mobile Inbox candidate requires exactly one kgg-source-truth block")
    try:
        source_truth = json.loads(matches[0])
    except json.JSONDecodeError as exc:
        pipeline.fail(f"Mobile Inbox candidate has invalid kgg-source-truth JSON: {exc}")
    current = source_truth.get("currentVersion") if isinstance(source_truth, dict) else None
    if not isinstance(current, dict):
        pipeline.fail("Mobile Inbox candidate is missing kgg-source-truth.currentVersion")
    code = current.get("versionCode")
    version_name = current.get("versionName")
    if isinstance(code, bool) or not isinstance(code, int) or code <= 0:
        pipeline.fail("Mobile Inbox candidate source versionCode must be a positive integer")
    if not isinstance(version_name, str) or version_name != version_name.strip():
        pipeline.fail("Mobile Inbox candidate source versionName must be a non-empty string")
    pipeline.validate_semver(version_name, "Mobile Inbox candidate source versionName")
    parsed_version = pipeline.SEMVER_PATTERN.fullmatch(version_name)
    if (
        parsed_version is None
        or int(parsed_version.group("major")) != 1
        or int(parsed_version.group("minor")) != 0
        or int(parsed_version.group("patch")) != code
    ):
        pipeline.fail("Mobile Inbox candidate source versionName must use 1.0.<versionCode>")
    marker_code = html_source_marker_code(html)
    if marker_code != code:
        pipeline.fail("Mobile Inbox candidate VERSION marker and kgg-source-truth versionCode differ")
    return code, version_name


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


def validate_mobile_candidate(candidate: Path, root: Path) -> tuple[str, int, str]:
    html = pipeline.read_text(candidate)
    pipeline.validate_html(html, "Mobile Inbox candidate")
    if SECRET_PATTERN.search(html):
        pipeline.fail("Mobile Inbox candidate contains a token-shaped secret")

    current_version = pipeline.load_json(root / "kgg-update" / "version.json")
    current_code = current_version.get("versionCode")
    if not isinstance(current_code, int):
        pipeline.fail("kgg-update/version.json versionCode must be an integer")
    candidate_code, candidate_version_name = html_source_identity(html)
    if candidate_code < current_code:
        pipeline.fail(
            f"Mobile Inbox candidate is based on v{candidate_code:03d}, "
            f"but current source truth is v{current_code:03d}"
        )
    current_version_name = current_version.get("versionName")
    if candidate_code == current_code and candidate_version_name != current_version_name:
        pipeline.fail("Mobile Inbox candidate versionName differs from the current source truth")

    colleague = pipeline.derive_colleague(html)
    pipeline.validate_html(colleague, "Mobile Inbox colleague build")
    if pipeline.sha256_text(html) == pipeline.sha256_text(colleague):
        pipeline.fail("Mobile Inbox Admin and colleague builds would be identical")
    return html, candidate_code, candidate_version_name


def prepare(candidate: Path, release_json: Path, copy_to: Path, root: Path) -> dict:
    html, _candidate_code, version_name = validate_mobile_candidate(candidate, root)
    release_id = next_release_id(root)
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
