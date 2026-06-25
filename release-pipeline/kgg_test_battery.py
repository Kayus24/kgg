#!/usr/bin/env python3
"""Run local/static KGG smoke-test batteries.

Default mode is intentionally non-mutating: no push, no PR, no live GitHub
write. Use --live-mobile-inbox only when a real Admin beta release should be
created as part of the smoke test.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEVEL_RANK = {"critical": 0, "regression": 1, "comfort": 2}
SECRET_PATTERN = (
    "("
    + "sk-" + "proj-"
    + r"|gh[pousr]_[A-Za-z0-9_]{20,}"
    + "|AI" + r"za[0-9A-Za-z_-]{25,}"
    + ")"
)
SECRET_SCAN_PATHS = [
    "release-inbox",
    "release-pipeline",
    "kgg-update",
    "therapist-app/android_update_manifest.json",
    "therapist-app/releases/web",
]


class BatteryError(RuntimeError):
    pass


def log(message: str) -> None:
    print(message, flush=True)


def run(args: list[str], *, cwd: Path = ROOT) -> None:
    log("+ " + " ".join(args))
    proc = subprocess.run(args, cwd=str(cwd))
    if proc.returncode != 0:
        raise BatteryError(f"Command failed ({proc.returncode}): {' '.join(args)}")


def node_executable() -> str:
    configured = os.environ.get("KGG_NODE") or os.environ.get("NODE")
    if configured and Path(configured).exists():
        return configured

    found = shutil.which("node")
    if found:
        return found

    bundled = (
        Path.home()
        / ".cache"
        / "codex-runtimes"
        / "codex-primary-runtime"
        / "dependencies"
        / "node"
        / "bin"
        / ("node.exe" if os.name == "nt" else "node")
    )
    if bundled.exists():
        return str(bundled)

    raise BatteryError("Node.js not found. Install node or set KGG_NODE to the node executable.")


def npm_executable() -> str | None:
    configured = os.environ.get("KGG_NPM") or os.environ.get("NPM")
    if configured and Path(configured).exists():
        return configured

    names = ["npm.cmd", "npm"] if os.name == "nt" else ["npm"]
    for name in names:
        found = shutil.which(name)
        if found:
            return found
    return None


def run_mobile_inbox(live: bool) -> None:
    log("== Mobile-Inbox battery ==")
    args = [sys.executable, "release-pipeline/mobile_inbox_live_smoke.py"]
    if not live:
        args.append("--dry-run")
    run(args)


def run_html_logic(suite: str) -> None:
    log(f"== HTML logic battery: {suite} ==")
    run([node_executable(), "release-pipeline/kgg_html_logic_smoke.js", "--suite", suite])


def run_ui_stability(level: str) -> None:
    log(f"== UI stability battery: {level} ==")
    if level in {"regression", "all"}:
        npm = npm_executable()
        if npm:
            if os.environ.get("KGG_SKIP_PLAYWRIGHT_INSTALL") != "1":
                run([npm, "exec", "--yes", "--package=playwright@1.61.1", "--", "playwright", "install", "chromium"])
            run([npm, "exec", "--yes", "--package=playwright@1.61.1", "--", "node", "release-pipeline/kgg_ui_stability_smoke.js", "--level", level])
            return
    run([node_executable(), "release-pipeline/kgg_ui_stability_smoke.js", "--level", level])


def run_release_contracts() -> None:
    log("== Release contract tests ==")
    run([sys.executable, "-m", "unittest", "release-pipeline/test_release_pipeline.py"])


def run_html_syntax() -> None:
    log("== HTML JavaScript syntax ==")
    html_files = [Path("kgg-update/index.html")]
    html_files.extend(sorted(Path("therapist-app/releases/web").glob("*/*.html")))
    if len(html_files) < 2:
        raise BatteryError("No immutable release HTML files found below therapist-app/releases/web.")
    run([node_executable(), "release-pipeline/check_html_scripts.js", *[str(path) for path in html_files]])


def run_version_json_check() -> None:
    log("== version.json / index.html hash ==")
    version_path = ROOT / "kgg-update" / "version.json"
    index_path = ROOT / "kgg-update" / "index.html"
    data = json.loads(version_path.read_text(encoding="utf-8"))
    index_bytes = index_path.read_bytes()
    raw_digest = hashlib.sha256(index_bytes).hexdigest()
    normalized_digest = hashlib.sha256(index_bytes.replace(b"\r\n", b"\n")).hexdigest()
    valid_digests = {raw_digest, normalized_digest}
    if data.get("sha256") not in valid_digests:
        raise BatteryError(
            "kgg-update/version.json sha256 does not match kgg-update/index.html "
            f"({data.get('sha256')} not in raw={raw_digest}, lf-normalized={normalized_digest})"
        )
    digest_mode = "raw" if data.get("sha256") == raw_digest else "lf-normalized"
    version_code = data.get("versionCode")
    if not isinstance(version_code, int) or version_code <= 0:
        raise BatteryError("kgg-update/version.json versionCode must be a positive integer.")
    if data.get("indexUrl") != f"index.html?v={version_code}":
        raise BatteryError("kgg-update/version.json indexUrl must match versionCode.")
    log(f"version.json OK: v{version_code} {data.get('versionName')} ({digest_mode} hash)")


def run_secret_scan() -> None:
    log("== Secret scan ==")
    args = ["git", "grep", "-nE", SECRET_PATTERN, "--", *SECRET_SCAN_PATHS]
    log("+ " + " ".join(args))
    proc = subprocess.run(args, cwd=str(ROOT), text=True, capture_output=True)
    if proc.returncode == 0:
        print(proc.stdout, file=sys.stderr)
        raise BatteryError("Potential secret found in release-controlled files.")
    if proc.returncode != 1:
        if proc.stdout:
            print(proc.stdout, file=sys.stderr)
        if proc.stderr:
            print(proc.stderr, file=sys.stderr)
        raise BatteryError(f"Secret scan failed with exit code {proc.returncode}.")
    log("Secret scan OK")


def html_version_marker(path: Path) -> int | None:
    if not path.exists() or not path.is_file():
        return None
    text = path.read_text(encoding="utf-8", errors="replace")
    match = re.search(r"KGG_GITHUB_UPDATE_v0*([0-9]+)", text, re.I)
    if match:
        return int(match.group(1))
    match = re.search(r"<title>\s*KGG\s+Update\s+v0*([0-9]+)\b", text, re.I)
    return int(match.group(1)) if match else None


def run_release_drift_check() -> None:
    log("== Admin release drift check ==")
    if os.environ.get("KGG_ALLOW_RELEASE_DRIFT") == "1":
        log("Release drift check skipped by KGG_ALLOW_RELEASE_DRIFT=1")
        return
    source = ROOT / "kgg-update" / "index.html"
    source_code = html_version_marker(source)
    if source_code is None:
        raise BatteryError("Cannot read KGG source version marker from kgg-update/index.html.")

    inbox = ROOT / "release-inbox" / "admin.html"
    inbox_code = html_version_marker(inbox)
    if inbox_code == source_code:
        log(f"Release drift OK: release-inbox/admin.html carries v{source_code:03d}")
        return

    manifest = json.loads((ROOT / "therapist-app" / "android_update_manifest.json").read_text(encoding="utf-8"))
    admin_url = str(manifest.get("adminHtmlUrl") or manifest.get("channels", {}).get("admin", {}).get("url") or "")
    match = re.search(r"/therapist-app/releases/web/(r[0-9]{4,})/admin\.html$", admin_url)
    if not match:
        raise BatteryError(f"Cannot derive Admin release path from manifest admin URL: {admin_url}")
    admin_path = ROOT / "therapist-app" / "releases" / "web" / match.group(1) / "admin.html"
    admin_code = html_version_marker(admin_path)
    if admin_code == source_code:
        log(f"Release drift OK: manifest Admin {match.group(1)} carries v{source_code:03d}")
        return

    raise BatteryError(
        "kgg-update source is newer than the prepared/live Admin release "
        f"(source v{source_code:03d}, release-inbox v{inbox_code}, manifest admin v{admin_code}). "
        "Add release-inbox/admin.html for this source or set KGG_ALLOW_RELEASE_DRIFT=1 for an explicit no-release PR."
    )


TEST_REGISTRY = [
    {
        "id": "release-contracts",
        "level": "critical",
        "suite": "release",
        "reason": "Release artifacts and manifests must stay buildable before any merge.",
        "run": run_release_contracts,
    },
    {
        "id": "html-syntax",
        "level": "critical",
        "suite": "syntax",
        "reason": "Broken HTML JavaScript means the app cannot start.",
        "run": run_html_syntax,
    },
    {
        "id": "version-json",
        "level": "critical",
        "suite": "syntax",
        "reason": "APK/Web update checks depend on version.json matching index.html.",
        "run": run_version_json_check,
    },
    {
        "id": "admin-release-drift",
        "level": "critical",
        "suite": "release",
        "reason": "Source updates must not land without a matching Admin beta release or explicit no-release override.",
        "run": run_release_drift_check,
    },
    {
        "id": "secret-scan",
        "level": "critical",
        "suite": "security",
        "reason": "API keys or tokens must never enter release-controlled files.",
        "run": run_secret_scan,
    },
    {
        "id": "mobile-inbox-dry-run",
        "level": "critical",
        "suite": "mobile-inbox",
        "reason": "No-Codex upload path must keep producing valid Admin beta artifacts.",
        "run": lambda: run_mobile_inbox(False),
    },
    {
        "id": "sync-critical",
        "level": "critical",
        "suite": "sync",
        "reason": "Sync export must exclude patients/secrets and reject forbidden payload keys.",
        "run": lambda: run_html_logic("sync-critical"),
    },
    {
        "id": "textblocks-critical",
        "level": "critical",
        "suite": "textblocks",
        "reason": "Text blocks must not create Satz cards and must keep currentPlan synced.",
        "run": lambda: run_html_logic("textblocks-critical"),
    },
    {
        "id": "ui-stability-critical",
        "level": "critical",
        "suite": "ui-stability",
        "reason": "Phone card swipe/drag guards must stay present before UI patches merge.",
        "run": lambda: run_ui_stability("critical"),
    },
    {
        "id": "sync-regression",
        "level": "regression",
        "suite": "sync",
        "reason": "Peer merge of exercise banks and packages is important but less release-blocking.",
        "run": lambda: run_html_logic("sync-regression"),
    },
    {
        "id": "textblocks-regression",
        "level": "regression",
        "suite": "textblocks",
        "reason": "Broad text formats and free units are likely to regress after parser changes.",
        "run": lambda: run_html_logic("textblocks-regression"),
    },
    {
        "id": "ui-stability-regression",
        "level": "regression",
        "suite": "ui-stability",
        "reason": "Flicker/layout patches must prove phone swipe and drag/drop still work in a real browser.",
        "run": lambda: run_ui_stability("regression"),
    },
    {
        "id": "mobile-inbox-live",
        "level": "comfort",
        "suite": "mobile-inbox",
        "reason": "Live smoke proves GitHub wiring but intentionally creates a new Admin beta.",
        "run": lambda: run_mobile_inbox(True),
        "requires_live_mobile_inbox": True,
    },
]


def validate_registry() -> None:
    seen: set[str] = set()
    for test in TEST_REGISTRY:
        missing = [key for key in ("id", "level", "suite", "reason", "run") if key not in test]
        if missing:
            raise BatteryError(f"Test registry entry missing fields {missing}: {test!r}")
        test_id = str(test["id"])
        if test_id in seen:
            raise BatteryError(f"Duplicate test id in registry: {test_id}")
        seen.add(test_id)
        if test["level"] not in LEVEL_RANK:
            raise BatteryError(f"Test {test_id} has unknown level: {test['level']}")
        if not str(test["suite"]).strip():
            raise BatteryError(f"Test {test_id} has empty suite.")
        if not str(test["reason"]).strip():
            raise BatteryError(f"Test {test_id} needs a category reason.")


def selected_tests(level: str, suite: str | None) -> list[dict[str, object]]:
    max_rank = max(LEVEL_RANK.values()) if level == "all" else LEVEL_RANK[level]
    chosen = []
    for test in TEST_REGISTRY:
        if suite and suite != "all" and test["suite"] != suite:
            continue
        if LEVEL_RANK[str(test["level"])] <= max_rank:
            chosen.append(test)
    return chosen


def main() -> int:
    parser = argparse.ArgumentParser(description="Run KGG local/static test batteries")
    parser.add_argument(
        "--level",
        choices=["critical", "regression", "all"],
        default=None,
        help="Run tests by risk level. Defaults to critical unless --suite is used for legacy full-suite runs.",
    )
    parser.add_argument(
        "--suite",
        choices=["all", "mobile-inbox", "sync", "textblocks", "ui-stability", "syntax", "security", "release"],
        default=None,
        help="Optionally limit to one suite. Without --level this keeps legacy behavior and runs all non-live tests in that suite.",
    )
    parser.add_argument("--list", action="store_true", help="List registered tests with level, suite and reason.")
    parser.add_argument(
        "--live-mobile-inbox",
        action="store_true",
        help="Run the real Mobile-Inbox live smoke; this intentionally creates a new Admin beta release.",
    )
    args = parser.parse_args()
    level = args.level or ("all" if args.suite else "critical")

    try:
        validate_registry()
        tests = selected_tests(level, args.suite)
        if args.list:
            for test in tests:
                live_note = " [requires --live-mobile-inbox]" if test.get("requires_live_mobile_inbox") else ""
                log(f"{test['level']:10} {test['suite']:13} {test['id']}{live_note} - {test['reason']}")
            return 0
        if not tests:
            raise BatteryError(f"No tests selected for level={level} suite={args.suite or 'all'}.")
        log(f"KGG test battery: level={level} suite={args.suite or 'all'}")
        for test in tests:
            if test.get("requires_live_mobile_inbox") and not args.live_mobile_inbox:
                log(f"SKIP {test['id']}: requires --live-mobile-inbox ({test['reason']})")
                continue
            log(f"-- {test['id']} [{test['level']}/{test['suite']}]")
            test["run"]()
        log("KGG test battery OK")
        return 0
    except BatteryError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
