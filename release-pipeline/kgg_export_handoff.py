#!/usr/bin/env python3
"""Export a certified, review-only handoff bundle from the local module sandbox."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import build_therapist_source as builder
import kgg_selftest_build as gate


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE = "e96b259812a44053e48d70c1f198ead01920e8c0"
HANDOFF_ROOT = ROOT / "tmp" / "kgg-selftest" / "handoff"
BLOCKED_PREFIXES = (
    ".github/",
    "android-wrapper/",
    "mobile-inbox/",
    "release-inbox/",
    "update-inbox/",
    "therapist-app/releases/",
)
BLOCKED_FILES = {
    "therapist-app/kgg_update_manifest.json",
    "therapist-app/android_update_manifest.json",
}


class HandoffError(RuntimeError):
    pass


def git(*args: str, binary: bool = False) -> str | bytes:
    proc = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=not binary,
    )
    if proc.returncode != 0:
        error = proc.stderr.decode("utf-8", errors="replace") if binary else proc.stderr
        raise HandoffError(f"git {' '.join(args)} failed: {error.strip()}")
    return proc.stdout


def ensure_safe_repo(base: str) -> tuple[str, str, list[str]]:
    if str(git("status", "--porcelain")).strip():
        raise HandoffError("working tree must be clean before handoff export")
    if str(git("remote")).strip():
        raise HandoffError("sandbox handoff export requires a repository without remotes")
    branch = str(git("branch", "--show-current")).strip()
    if not branch.startswith("sandbox/"):
        raise HandoffError(f"handoff export is restricted to sandbox/* branches, got {branch!r}")
    base_commit = str(git("rev-parse", f"{base}^{{commit}}" )).strip()
    head_commit = str(git("rev-parse", "HEAD")).strip()
    names = [line.strip() for line in str(git("diff", "--name-only", base_commit, "HEAD", "--")).splitlines() if line.strip()]
    blocked = [path for path in names if path in BLOCKED_FILES or path.startswith(BLOCKED_PREFIXES)]
    if blocked:
        raise HandoffError("production/release paths changed in sandbox: " + ", ".join(blocked))
    return base_commit, head_commit, names


def verify_green() -> tuple[dict, str, str]:
    report = gate.read_json(gate.LATEST_PATH)
    if report.get("status") != "passed":
        raise HandoffError("latest self-test report is not green")
    _, output, version_path, parts, assembled = builder.load_build(builder.DEFAULT_MANIFEST)
    if output.read_bytes() != assembled:
        raise HandoffError("generated index.html differs from modular source")
    candidate_hash = hashlib.sha256(assembled).hexdigest()
    source_hash, _ = gate.source_state(parts)
    if report.get("candidateHash") != candidate_hash:
        raise HandoffError("latest green report belongs to a different HTML candidate")
    if report.get("sourceHash") != source_hash:
        raise HandoffError("latest green report belongs to a different module source state")
    version = json.loads(version_path.read_text(encoding="utf-8"))
    if version.get("sha256") != candidate_hash or version.get("versionCode") != report.get("versionCode"):
        raise HandoffError("version manifest does not match the certified candidate")
    return report, candidate_hash, source_hash


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default=DEFAULT_BASE, help="production baseline commit included in the handoff diff")
    args = parser.parse_args()
    try:
        base, head, files = ensure_safe_repo(args.base)
        report, candidate_hash, source_hash = verify_green()
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        destination = HANDOFF_ROOT / stamp
        if destination.exists():
            raise HandoffError(f"handoff destination already exists: {destination}")
        (destination / "evidence").mkdir(parents=True)
        (destination / "candidate").mkdir(parents=True)

        patch = git("diff", "--binary", "--full-index", base, "HEAD", "--", binary=True)
        (destination / "sandbox-changes.patch").write_bytes(patch)
        shutil.copy2(ROOT / "kgg-update" / "index.html", destination / "candidate" / "KGG_MODULE_CANDIDATE.html")
        shutil.copy2(ROOT / "kgg-update" / "version.json", destination / "candidate" / "version.json")
        shutil.copy2(ROOT / "kgg-update" / "src" / "parts.json", destination / "candidate" / "parts.json")

        run_dir = gate.RUNS_ROOT / str(report.get("runId"))
        for name in ("report.json", "report.md", "report.html", "transaction.json"):
            source = run_dir / name
            if source.exists():
                shutil.copy2(source, destination / "evidence" / name)
        screenshots_source = run_dir / "screenshots"
        if screenshots_source.exists():
            shutil.copytree(screenshots_source, destination / "evidence" / "screenshots")

        manifest = {
            "schema": 1,
            "kind": "kgg-module-sandbox-handoff",
            "createdAt": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "baseCommit": base,
            "headCommit": head,
            "branch": str(git("branch", "--show-current")).strip(),
            "candidateHash": candidate_hash,
            "sourceHash": source_hash,
            "certificationRunId": report.get("runId"),
            "versionCode": report.get("versionCode"),
            "versionName": report.get("versionName"),
            "changedFiles": files,
            "productionUntouched": True,
            "automaticPublish": False,
        }
        (destination / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        (destination / "README.md").write_text(
            "# KGG module sandbox handoff\n\n"
            "Review-only export. It does not publish, push, update manifests or build an APK.\n\n"
            f"- Baseline: `{base}`\n"
            f"- Candidate: `{head}`\n"
            f"- HTML SHA-256: `{candidate_hash}`\n"
            f"- Certification: `{report.get('runId')}`\n\n"
            "Port only after explicit approval to a fresh production branch and rerun the full certification there.\n",
            encoding="utf-8",
            newline="\n",
        )
        archive = shutil.make_archive(str(destination), "zip", root_dir=destination)
        print(json.dumps({"handoff": str(destination), "archive": archive, "manifest": manifest}, ensure_ascii=False, indent=2))
        return 0
    except (OSError, UnicodeError, json.JSONDecodeError, HandoffError, gate.GateError, builder.BuildError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
