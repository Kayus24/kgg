#!/usr/bin/env python3
"""End-to-end smoke test for the KGG Mobile-Inbox release path.

Dry-run mode validates and builds the current Admin HTML in a temporary clone.
Live mode pushes one smoke HTML to the `mobile-inbox` branch, waits for the
GitHub Action, and verifies that a new Admin beta was published.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REPO = "Kayus24/kgg"
DEFAULT_REMOTE = "https://github.com/Kayus24/kgg.git"
WORKFLOW_NAME = "KGG Mobile Inbox Release"
SMOKE_PATH = Path("mobile-inbox/KGG_MOBILE_INBOX_SMOKE.html")


class SmokeError(RuntimeError):
    pass


@dataclass
class CommandResult:
    stdout: str
    stderr: str


def run(
    args: list[str],
    *,
    cwd: Path = ROOT,
    check: bool = True,
    capture: bool = True,
) -> CommandResult:
    proc = subprocess.run(
        args,
        cwd=str(cwd),
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )
    stdout = proc.stdout or ""
    stderr = proc.stderr or ""
    if check and proc.returncode != 0:
        joined = " ".join(args)
        detail = (stderr or stdout).strip()
        raise SmokeError(f"Command failed ({proc.returncode}): {joined}\n{detail}")
    return CommandResult(stdout=stdout, stderr=stderr)


def log(message: str) -> None:
    print(message, flush=True)


def load_json(value: str) -> dict:
    try:
        return json.loads(value)
    except json.JSONDecodeError as exc:
        raise SmokeError(f"Invalid JSON: {exc}") from exc


def git_show(ref_path: str) -> str:
    return run(["git", "show", ref_path], cwd=ROOT).stdout


def fetch_refs() -> None:
    run(["git", "fetch", "origin", "main", "mobile-inbox"], cwd=ROOT, capture=False)


def manifest_from_ref(ref: str = "origin/main") -> dict:
    return load_json(git_show(f"{ref}:therapist-app/android_update_manifest.json"))


def admin_release_path(manifest: dict) -> Path:
    url = str(manifest.get("adminHtmlUrl") or manifest.get("channels", {}).get("admin", {}).get("url") or "")
    match = re.search(r"/therapist-app/releases/web/(r[0-9]{4,})/admin\.html$", url)
    if not match:
        raise SmokeError(f"Cannot derive Admin release path from adminHtmlUrl: {url}")
    return Path("therapist-app/releases/web") / match.group(1) / "admin.html"


def current_admin_html_from_main() -> tuple[str, dict, Path]:
    fetch_refs()
    manifest = manifest_from_ref("origin/main")
    path = Path("kgg-update/index.html")
    html = git_show(f"origin/main:{path.as_posix()}")
    return html, manifest, path


def current_admin_html_from_checkout() -> tuple[str, Path]:
    path = Path("kgg-update/index.html")
    html = (ROOT / path).read_text(encoding="utf-8")
    return html, path


def smoke_html(html: str) -> str:
    stamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return html.rstrip() + f"\n<!-- kgg-mobile-inbox-live-smoke {stamp} -->\n"


def copy_current_checkout(target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    tracked = run(["git", "ls-files", "--cached", "--others", "--exclude-standard"], cwd=ROOT).stdout.splitlines()
    for rel in tracked:
        source = ROOT / rel
        if not source.is_file():
            continue
        destination = target / rel
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def clone_branch(branch: str, target: Path, remote: str) -> None:
    run(
        ["git", "clone", "--quiet", "--single-branch", "--branch", branch, remote, str(target)],
        cwd=ROOT,
        capture=False,
    )


def run_dry_run(base_dir: Path, candidate: Path) -> dict:
    log("Dry-run: validate mobile candidate")
    run(
        [
            sys.executable,
            "release-pipeline/mobile_inbox.py",
            "--candidate",
            str(candidate),
            "--release-json",
            "release-inbox/release.json",
            "--copy-to",
            "release-inbox/admin.html",
        ],
        cwd=base_dir,
        capture=False,
    )
    log("Dry-run: build immutable release artifacts")
    result = run(
        [
            sys.executable,
            "release-pipeline/release_pipeline.py",
            "prepare",
            "--candidate",
            "release-inbox/admin.html",
            "--release-json",
            "release-inbox/release.json",
        ],
        cwd=base_dir,
    )
    metadata = load_json(result.stdout)
    release_id = metadata["releaseId"]
    log("Dry-run: run contract tests")
    run([sys.executable, "-m", "unittest", "release-pipeline/test_release_pipeline.py"], cwd=base_dir, capture=False)
    run(
        [
            "node",
            "release-pipeline/check_html_scripts.js",
            "kgg-update/index.html",
            f"therapist-app/releases/web/{release_id}/admin.html",
            f"therapist-app/releases/web/{release_id}/colleague.html",
        ],
        cwd=base_dir,
        capture=False,
    )
    return metadata


def require_gh_auth() -> None:
    run(["gh", "auth", "status"], cwd=ROOT)


def require_workflow_permissions(repo: str) -> None:
    data = load_json(
        run(
            [
                "gh",
                "api",
                f"repos/{repo}/actions/permissions/workflow",
                "-H",
                "Accept: application/vnd.github+json",
            ],
            cwd=ROOT,
        ).stdout
    )
    if data.get("default_workflow_permissions") != "write" or data.get("can_approve_pull_request_reviews") is not True:
        raise SmokeError(
            "GitHub Actions workflow permissions must be write + PR approval. "
            "Set repo Settings > Actions > General > Workflow permissions to read/write and allow PRs."
        )


def push_smoke_upload(work_dir: Path, html: str, remote: str) -> str:
    clone_branch("mobile-inbox", work_dir, remote)
    target = work_dir / SMOKE_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(smoke_html(html), encoding="utf-8", newline="\n")
    run(["git", "config", "user.name", "KGG mobile inbox smoke"], cwd=work_dir)
    run(["git", "config", "user.email", "kgg-smoke@users.noreply.github.com"], cwd=work_dir)
    run(["git", "add", SMOKE_PATH.as_posix()], cwd=work_dir)
    status = run(["git", "status", "--porcelain"], cwd=work_dir).stdout.strip()
    if not status:
        raise SmokeError("Smoke upload produced no git change")
    run(["git", "commit", "-m", "mobile inbox live smoke"], cwd=work_dir, capture=False)
    run(["git", "push", "origin", "mobile-inbox"], cwd=work_dir, capture=False)
    return run(["git", "rev-parse", "HEAD"], cwd=work_dir).stdout.strip()


def list_runs(repo: str, head_sha: str) -> list[dict]:
    raw = run(
        [
            "gh",
            "run",
            "list",
            "--repo",
            repo,
            "--workflow",
            WORKFLOW_NAME,
            "--limit",
            "20",
            "--json",
            "databaseId,status,conclusion,headBranch,headSha,createdAt,displayTitle,url",
        ],
        cwd=ROOT,
    ).stdout
    return [item for item in load_json(raw) if item.get("headSha") == head_sha]


def wait_for_run(repo: str, head_sha: str, timeout_seconds: int) -> dict:
    deadline = time.time() + timeout_seconds
    selected: dict | None = None
    while time.time() < deadline:
        runs = list_runs(repo, head_sha)
        if runs:
            selected = runs[0]
            if selected.get("status") == "completed":
                if selected.get("conclusion") != "success":
                    raise SmokeError(
                        f"Mobile-Inbox workflow failed: {selected.get('conclusion')} {selected.get('url')}"
                    )
                return selected
        time.sleep(5)
    if selected:
        raise SmokeError(f"Timed out waiting for workflow completion: {selected.get('url')}")
    raise SmokeError(f"Timed out waiting for Mobile-Inbox workflow for SHA {head_sha}")


def wait_for_public_url(url: str, timeout_seconds: int) -> None:
    deadline = time.time() + timeout_seconds
    last_error = ""
    while time.time() < deadline:
        try:
            request = urllib.request.Request(url, method="HEAD")
            with urllib.request.urlopen(request, timeout=15) as response:
                if 200 <= response.status < 300:
                    return
                last_error = f"HTTP {response.status}"
        except Exception as exc:  # noqa: BLE001 - surfaced in final smoke error
            last_error = str(exc)
        time.sleep(5)
    raise SmokeError(f"Public Pages URL did not become available: {url} ({last_error})")


def find_release_pr(repo: str, release_id: str) -> dict:
    raw = run(
        [
            "gh",
            "pr",
            "list",
            "--repo",
            repo,
            "--state",
            "all",
            "--limit",
            "20",
            "--search",
            release_id,
            "--json",
            "number,title,state,mergedAt,headRefName,baseRefName,url",
        ],
        cwd=ROOT,
    ).stdout
    for pr in load_json(raw):
        if pr.get("state") == "MERGED" and release_id in str(pr.get("title", "")):
            return pr
    raise SmokeError(f"No merged Admin beta PR found for {release_id}")


def verify_live_result(repo: str, before: dict, timeout_seconds: int) -> dict:
    deadline = time.time() + timeout_seconds
    before_admin = before["channels"]["admin"]["releaseId"]
    before_colleague = before["channels"]["colleague"]["releaseId"]
    manifest: dict | None = None
    while time.time() < deadline:
        fetch_refs()
        manifest = manifest_from_ref("origin/main")
        admin_release = manifest["channels"]["admin"]["releaseId"]
        if admin_release != before_admin:
            break
        time.sleep(5)
    if manifest is None:
        raise SmokeError("Could not read updated origin/main manifest")

    admin = manifest["channels"]["admin"]
    colleague = manifest["channels"]["colleague"]
    release_id = admin["releaseId"]
    if release_id == before_admin:
        raise SmokeError(f"Admin release did not advance from {before_admin}")
    if colleague["releaseId"] != before_colleague:
        raise SmokeError(f"Colleague release changed unexpectedly: {before_colleague} -> {colleague['releaseId']}")

    run(["git", "cat-file", "-e", f"origin/main:therapist-app/releases/web/{release_id}/admin.html"], cwd=ROOT)
    wait_for_public_url(admin["url"], timeout_seconds)
    pr = find_release_pr(repo, release_id)
    return {"releaseId": release_id, "adminUrl": admin["url"], "pr": pr}


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test the KGG Mobile-Inbox release path")
    parser.add_argument("--dry-run", action="store_true", help="Validate/build in a temporary clone without pushing to GitHub")
    parser.add_argument("--repo", default=DEFAULT_REPO)
    parser.add_argument("--remote", default=DEFAULT_REMOTE)
    parser.add_argument("--timeout", type=int, default=600, help="Seconds to wait for workflow/Pages propagation")
    parser.add_argument("--keep-temp", action="store_true", help="Keep temporary directories for inspection")
    args = parser.parse_args()

    temp_root = Path(tempfile.mkdtemp(prefix="kgg-mobile-inbox-smoke-"))
    try:
        if args.dry_run:
            html, source_path = current_admin_html_from_checkout()
            candidate = temp_root / "candidate-admin.html"
            candidate.write_text(smoke_html(html), encoding="utf-8", newline="\n")
            base = temp_root / "base"
            copy_current_checkout(base)
            log(f"Source Admin HTML: current checkout:{source_path.as_posix()}")
            metadata = run_dry_run(base, candidate)
            log(json.dumps({"mode": "dry-run", "releaseId": metadata["releaseId"], "versionName": metadata["versionName"]}, indent=2))
            return 0

        html, before_manifest, source_path = current_admin_html_from_main()
        log(f"Source Admin HTML: origin/main:{source_path.as_posix()}")
        require_gh_auth()
        require_workflow_permissions(args.repo)
        upload = temp_root / "upload"
        head_sha = push_smoke_upload(upload, html, args.remote)
        log(f"Pushed Mobile-Inbox smoke commit: {head_sha}")
        run_info = wait_for_run(args.repo, head_sha, args.timeout)
        live = verify_live_result(args.repo, before_manifest, args.timeout)
        summary = {
            "mode": "live",
            "uploadSha": head_sha,
            "workflowRun": run_info["url"],
            "releaseId": live["releaseId"],
            "adminUrl": live["adminUrl"],
            "pr": live["pr"]["url"],
        }
        log(json.dumps(summary, indent=2))
        return 0
    except SmokeError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    finally:
        if args.keep_temp:
            log(f"Kept temp dir: {temp_root}")
        else:
            shutil.rmtree(temp_root, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
