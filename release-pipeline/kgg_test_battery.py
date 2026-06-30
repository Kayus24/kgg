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


def run_ui_stability(level: str, case_name: str | None = None) -> None:
    label = f"{level} / {case_name}" if case_name else level
    log(f"== UI stability battery: {label} ==")
    case_args = ["--case", case_name] if case_name else []
    if level in {"regression", "all"}:
        npm = npm_executable()
        if npm:
            if os.environ.get("KGG_SKIP_PLAYWRIGHT_INSTALL") != "1":
                run([npm, "exec", "--yes", "--package=playwright@1.61.1", "--", "playwright", "install", "chromium"])
            run([npm, "exec", "--yes", "--package=playwright@1.61.1", "--", "node", "release-pipeline/kgg_ui_stability_smoke.js", "--level", level, *case_args])
            return
    run([node_executable(), "release-pipeline/kgg_ui_stability_smoke.js", "--level", level, *case_args])


def run_native_sync_bridge_contract() -> None:
    log("== Native Android sync bridge contract ==")
    bridge = (ROOT / "android-wrapper" / "app" / "src" / "main" / "java" / "de" / "kgg" / "app" / "KggSyncBridge.java").read_text(
        encoding="utf-8"
    )
    bootstrap = (ROOT / "android-wrapper" / "app" / "src" / "main" / "assets" / "android" / "kgg_android_sync_bootstrap.js").read_text(
        encoding="utf-8"
    )
    required_bridge_tokens = [
        "public String getStatus()",
        "public String readSyncJson()",
        "public String listPeerSyncJson()",
        "public boolean writeSyncJson(String json)",
        "public String readFollowConfig()",
        "public boolean writeFollowConfig(String json)",
        "kgg_cross_data_safe_sync_v2.json",
        "PUBLIC_SYNC_DIR_NAME = \"KGG Sync\"",
        "private boolean isSafeExerciseBankSyncPayload(String json)",
        "access_token",
        "refresh_token",
        "rawpayload",
        "base64payload",
    ]
    missing_bridge = [token for token in required_bridge_tokens if token not in bridge]
    if missing_bridge:
        raise BatteryError("Android native sync bridge contract missing: " + ", ".join(missing_bridge))
    required_bootstrap_tokens = [
        "window.KGGNativeSync",
        "status: function()",
        "read: function()",
        "write: function(syncDocument)",
        "listPeers: function()",
        "getFollowConfig: function()",
        "setFollowConfig: function(config)",
        "kgg:native-sync-ready",
    ]
    missing_bootstrap = [token for token in required_bootstrap_tokens if token not in bootstrap]
    if missing_bootstrap:
        raise BatteryError("Android native sync JS bootstrap contract missing: " + ", ".join(missing_bootstrap))

    forbidden_network_tokens = [
        "HttpURLConnection",
        "java.net.URL",
        "new URL(",
        "http://",
        "https://",
        "github",
        "raw.githubusercontent",
        "fetch(",
        "XMLHttpRequest",
        "WebSocket",
    ]
    bridge_network = [token for token in forbidden_network_tokens if token.lower() in bridge.lower()]
    bootstrap_network = [token for token in forbidden_network_tokens if token.lower() in bootstrap.lower()]
    if bridge_network or bootstrap_network:
        details = []
        if bridge_network:
            details.append("KggSyncBridge.java: " + ", ".join(bridge_network))
        if bootstrap_network:
            details.append("kgg_android_sync_bootstrap.js: " + ", ".join(bootstrap_network))
        raise BatteryError("Native sync bridge must stay local-only/no-network: " + " | ".join(details))
    log("Native Android sync bridge contract OK")


def run_native_sync() -> None:
    log("== Native sync battery ==")
    run_html_logic("native-sync-regression")
    run_native_sync_bridge_contract()


def run_patch_hygiene() -> None:
    log("== Patch hygiene check ==")
    run([sys.executable, "release-pipeline/kgg_patch_hygiene.py"])


def run_release_contracts() -> None:
    log("== Release contract tests ==")
    run([sys.executable, "-m", "unittest", "release-pipeline/test_release_pipeline.py", "release-pipeline/test_encoding_guard.py"])


def run_encoding_guard() -> None:
    log("== Encoding guard ==")
    run([sys.executable, "release-pipeline/kgg_encoding_guard.py"])


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
        "id": "patch-hygiene",
        "level": "critical",
        "suite": "hygiene",
        "reason": "Dirty branches, half release-inbox payloads and idea/test-lab files must be blocked early.",
        "run": run_patch_hygiene,
    },
    {
        "id": "release-contracts",
        "level": "critical",
        "suite": "release",
        "reason": "Release artifacts and manifests must stay buildable before any merge.",
        "run": run_release_contracts,
    },
    {
        "id": "encoding-guard",
        "level": "critical",
        "suite": "syntax",
        "reason": "UTF-8 charset must be declared before visible non-ASCII text and mojibake must never ship.",
        "run": run_encoding_guard,
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
        "run": lambda: run_ui_stability("regression", "gestures"),
    },
    {
        "id": "ui-bank-thumbnails",
        "level": "regression",
        "suite": "ui-stability",
        "reason": "Exercise-bank rows with image attachments must keep rendering visible thumbnail placeholders/previews.",
        "run": lambda: run_ui_stability("regression", "bank-thumbnails"),
    },
    {
        "id": "ui-phone-admin-menu",
        "level": "regression",
        "suite": "ui-stability",
        "reason": "Phone admin, exercise-bank share and QR actions must stay in the compact top-right submenu.",
        "run": lambda: run_ui_stability("regression", "phone-admin-menu"),
    },
    {
        "id": "ui-phone-scan-dock",
        "level": "regression",
        "suite": "ui-stability",
        "reason": "Phone scan button must stay fixed at the bottom and the finish button must join it once exercises exist.",
        "run": lambda: run_ui_stability("regression", "phone-scan-dock"),
    },
    {
        "id": "ui-phone-history-packages",
        "level": "regression",
        "suite": "ui-stability",
        "reason": "Phone Plan-Historie and Uebungspakete buttons must open/close without hanging after dock/layout patches.",
        "run": lambda: run_ui_stability("regression", "phone-history-packages"),
    },
    {
        "id": "ui-phone-bank-align",
        "level": "regression",
        "suite": "ui-stability",
        "reason": "Opening the phone exercise bank must align its bottom above the fixed scan dock.",
        "run": lambda: run_ui_stability("regression", "phone-bank-align"),
    },
    {
        "id": "ui-tablet-layout-button",
        "level": "regression",
        "suite": "ui-stability",
        "reason": "Tablet Layout anpassen must open and close the existing layout controls reliably.",
        "run": lambda: run_ui_stability("regression", "tablet-layout-button"),
    },
    {
        "id": "ui-tablet-card-reorder",
        "level": "regression",
        "suite": "ui-stability",
        "reason": "Tablet exercise cards must start reorder by long-pressing the card surface, not only the drag handle.",
        "run": lambda: run_ui_stability("regression", "tablet-card-reorder"),
    },
    {
        "id": "ui-tablet-layout-visual",
        "level": "regression",
        "suite": "ui-stability",
        "reason": "Tablet layout must remain visibly usable: menu, plan list and card reorder cannot be blocked by phone/layout patches.",
        "run": lambda: run_ui_stability("regression", "tablet-layout-visual"),
    },
    {
        "id": "ui-tablet-app-boot",
        "level": "regression",
        "suite": "ui-stability",
        "reason": "Wide tablet viewports must boot the real app scripts without phone runtime patches freezing startup.",
        "run": lambda: run_ui_stability("regression", "tablet-app-boot"),
    },
    {
        "id": "ui-tablet-split-phone-layout",
        "level": "regression",
        "suite": "ui-stability",
        "reason": "Tablet split-screen below the phone breakpoint must still get the phone UI and cleanly return to tablet UI when widened.",
        "run": lambda: run_ui_stability("regression", "tablet-split-phone-layout"),
    },
    {
        "id": "ui-phone-landscape-tablet-menu",
        "level": "regression",
        "suite": "ui-stability",
        "reason": "Phone landscape must switch to the tablet workspace/menu while phone portrait and tablet split-screen remain protected.",
        "run": lambda: run_ui_stability("regression", "phone-landscape-tablet-menu"),
    },
    {
        "id": "native-sync-regression",
        "level": "regression",
        "suite": "native-sync",
        "reason": "Peer mesh, auto-download rules and Android sync bridge contract must stay compatible.",
        "run": run_native_sync,
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
        choices=["all", "hygiene", "mobile-inbox", "sync", "native-sync", "textblocks", "ui-stability", "syntax", "security", "release"],
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
