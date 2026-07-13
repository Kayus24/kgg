#!/usr/bin/env python3
"""Transactional, self-testing build gate for the local KGG module sandbox."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import html as html_lib
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import build_therapist_source as builder


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "kgg-update" / "src"
IMPACT_PATH = SRC / "test-impact.json"
STATE_ROOT = ROOT / "tmp" / "kgg-selftest"
RUNS_ROOT = STATE_ROOT / "runs"
PENDING_PATH = STATE_ROOT / "pending.json"
LOCK_PATH = STATE_ROOT / "build.lock"
LATEST_PATH = STATE_ROOT / "latest.json"
LAST_FAILED_PATH = STATE_ROOT / "last-failed.json"
BATTERY = ROOT / "release-pipeline" / "kgg_test_battery.py"


def configure_console() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8", errors="backslashreplace")


class GateError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run_id() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + f"-{os.getpid()}"


def read_json(path: Path, fallback: dict | None = None) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        if fallback is not None:
            return fallback
        raise GateError(f"Missing JSON file: {path}")
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise GateError(f"Cannot read JSON {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise GateError(f"JSON root must be an object: {path}")
    return value


def atomic_json(path: Path, value: dict) -> None:
    raw = (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    builder.atomic_write(path, raw)


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def source_state(parts: list[Path], manifest_path: Path | None = None) -> tuple[str, dict[str, str]]:
    manifest_path = manifest_path or builder.DEFAULT_MANIFEST
    hashes: dict[str, str] = {}
    digest = hashlib.sha256()
    paths = [manifest_path, IMPACT_PATH, *parts]
    for path in paths:
        relative = path.relative_to(SRC).as_posix() if path.is_relative_to(SRC) else path.relative_to(ROOT).as_posix()
        raw = path.read_bytes()
        hashes[relative] = sha256(raw)
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(raw)
        digest.update(b"\0")
    return digest.hexdigest(), hashes


def changed_parts(previous: dict, current: dict[str, str]) -> list[str]:
    old = previous.get("partHashes") if isinstance(previous.get("partHashes"), dict) else {}
    return sorted(path for path in set(old) | set(current) if old.get(path) != current.get(path))


def select_tests(mode: str, changed: list[str]) -> tuple[bool, list[str], list[str]]:
    if mode == "certify":
        return True, [], ["explicit certification"]
    policy = read_json(IMPACT_PATH)
    if policy.get("schema") != 1 or not isinstance(policy.get("rules"), list):
        raise GateError("test-impact.json must use schema 1 and contain rules")
    if not LATEST_PATH.exists():
        return True, [], ["no previous green self-test report"]
    full = False
    selected: set[str] = set()
    reasons: list[str] = []
    for path in changed:
        if path == "test-impact.json":
            full = True
            reasons.append("test impact policy changed")
            continue
        matched = False
        for rule in policy["rules"]:
            pattern = rule.get("glob") if isinstance(rule, dict) else None
            if not isinstance(pattern, str) or not fnmatch.fnmatch(path, pattern):
                continue
            matched = True
            if rule.get("fullRegression") is True:
                full = True
                reasons.append(f"{path} requires full regression")
            tests = rule.get("testIds", [])
            if not isinstance(tests, list) or any(not isinstance(item, str) for item in tests):
                raise GateError(f"Invalid testIds for impact rule {pattern}")
            selected.update(tests)
        if not matched and policy.get("unknownChangesRequireFullRegression", True):
            full = True
            reasons.append(f"unknown source part: {path}")
    return full, sorted(selected), reasons


def acquire_lock() -> None:
    STATE_ROOT.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(LOCK_PATH, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        owner = LOCK_PATH.read_text(encoding="utf-8", errors="replace").strip() if LOCK_PATH.exists() else "unknown"
        raise GateError(f"Another self-test build is active ({owner})") from exc
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(f"pid={os.getpid()} started={utc_now()}\n")


def release_lock() -> None:
    try:
        LOCK_PATH.unlink()
    except FileNotFoundError:
        pass


def recover_pending() -> bool:
    if not PENDING_PATH.exists():
        return False
    pending = read_json(PENDING_PATH)
    backup_dir = Path(str(pending.get("backupDir", "")))
    output = Path(str(pending.get("output", "")))
    version = Path(str(pending.get("versionManifest", "")))
    old_output = backup_dir / "old-index.html"
    old_version = backup_dir / "old-version.json"
    if not old_output.exists() or not old_version.exists():
        raise GateError(f"Pending transaction cannot be recovered: {backup_dir}")
    builder.atomic_write(output, old_output.read_bytes())
    builder.atomic_write(version, old_version.read_bytes())
    pending["status"] = "recovered"
    pending["recoveredAt"] = utc_now()
    atomic_json(backup_dir / "transaction.json", pending)
    PENDING_PATH.unlink()
    print(f"Recovered interrupted build transaction from {backup_dir}")
    return True


def command_runner(command: list[str], env: dict[str, str]) -> tuple[int, str, float]:
    started = time.monotonic()
    proc = subprocess.run(
        command,
        cwd=str(ROOT),
        env=env,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    elapsed = time.monotonic() - started
    return proc.returncode, proc.stdout or "", elapsed


def test_commands(full: bool, test_ids: list[str]) -> list[tuple[str, list[str]]]:
    python = sys.executable
    if full:
        return [("full-regression", [python, str(BATTERY), "--level", "regression"])]
    commands: list[tuple[str, list[str]]] = [
        ("critical", [python, str(BATTERY), "--level", "critical"])
    ]
    if test_ids:
        args = [python, str(BATTERY)]
        for test_id in test_ids:
            args.extend(["--test-id", test_id])
        commands.append(("impact-regression", args))
    return commands


def render_report(report: dict) -> tuple[bytes, bytes]:
    tests = report.get("tests", [])
    md = [
        f"# KGG Self-Test {report.get('status', '').upper()}",
        "",
        f"- Run: `{report.get('runId')}`",
        f"- Mode: `{report.get('mode')}`",
        f"- Candidate: `{report.get('candidateHash')}`",
        f"- Source: `{report.get('sourceHash')}`",
        f"- Started: `{report.get('startedAt')}`",
        f"- Finished: `{report.get('finishedAt')}`",
        "",
        "## Tests",
        "",
    ]
    for item in tests:
        md.append(f"- {'PASS' if item.get('ok') else 'FAIL'} `{item.get('name')}` ({item.get('seconds', 0):.1f}s)")
    if report.get("changedParts"):
        md.extend(["", "## Changed source parts", ""])
        md.extend(f"- `{path}`" for path in report["changedParts"])
    if report.get("error"):
        md.extend(["", "## Error", "", "```text", str(report["error"]), "```"])
    md_raw = ("\n".join(md) + "\n").encode("utf-8")

    cards = "".join(
        "<li class='{}'><b>{}</b><span>{:.1f}s</span></li>".format(
            "ok" if item.get("ok") else "fail",
            html_lib.escape(str(item.get("name"))),
            float(item.get("seconds", 0)),
        )
        for item in tests
    )
    error = f"<pre>{html_lib.escape(str(report.get('error')))}</pre>" if report.get("error") else ""
    page = f"""<!doctype html>
<html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>KGG Self-Test {html_lib.escape(str(report.get('status', '')).upper())}</title>
<style>body{{font:16px system-ui;margin:24px;max-width:900px}}code{{word-break:break-all}}ul{{padding:0}}li{{display:flex;justify-content:space-between;padding:10px;margin:6px 0;border-radius:10px;background:#eef2f7}}li.ok{{border-left:6px solid #16803c}}li.fail{{border-left:6px solid #bd1e1e}}pre{{white-space:pre-wrap;background:#111827;color:#fff;padding:14px;border-radius:12px}}</style></head>
<body><h1>KGG Self-Test {html_lib.escape(str(report.get('status', '')).upper())}</h1>
<p>Modus: <b>{html_lib.escape(str(report.get('mode')))}</b></p>
<p>Kandidat: <code>{html_lib.escape(str(report.get('candidateHash')))}</code></p>
<ul>{cards}</ul>{error}</body></html>
"""
    return md_raw, page.encode("utf-8")


def write_report(run_dir: Path, report: dict, *, latest: bool) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    atomic_json(run_dir / "report.json", report)
    md_raw, html_raw = render_report(report)
    builder.atomic_write(run_dir / "report.md", md_raw)
    builder.atomic_write(run_dir / "report.html", html_raw)
    if latest:
        atomic_json(LATEST_PATH, report)
        builder.atomic_write(STATE_ROOT / "latest.md", md_raw)
        builder.atomic_write(STATE_ROOT / "latest.html", html_raw)
    else:
        atomic_json(LAST_FAILED_PATH, report)


def verify_version_progress(version: dict, candidate_hash: str, previous: dict) -> None:
    previous_hash = previous.get("candidateHash")
    if not previous_hash or previous_hash == candidate_hash:
        return
    old_code = previous.get("versionCode")
    new_code = version.get("versionCode")
    if isinstance(old_code, int) and (not isinstance(new_code, int) or new_code <= old_code):
        raise GateError(
            f"Runtime output changed but versionCode did not increase ({old_code} -> {new_code}). "
            "Create a versioned patch before building."
        )


def execute_build(
    mode: str,
    *,
    runner: Callable[[list[str], dict[str, str]], tuple[int, str, float]] = command_runner,
) -> dict:
    acquire_lock()
    transaction_installed = False
    output: Path | None = None
    version_path: Path | None = None
    backup_dir: Path | None = None
    report: dict = {
        "schema": 1,
        "runId": run_id(),
        "mode": mode,
        "status": "failed",
        "startedAt": utc_now(),
        "tests": [],
    }
    try:
        recover_pending()
        _, output, version_path, parts, assembled = builder.load_build(builder.DEFAULT_MANIFEST)
        candidate_hash = sha256(assembled)
        source_hash, part_hashes = source_state(parts)
        previous = read_json(LATEST_PATH, {})
        changed = changed_parts(previous, part_hashes)
        full, test_ids, reasons = select_tests(mode, changed)
        version = read_json(version_path)
        verify_version_progress(version, candidate_hash, previous)
        version["sha256"] = candidate_hash
        version_raw = (json.dumps(version, ensure_ascii=False, indent=2) + "\n").encode("utf-8")

        report.update(
            {
                "candidateHash": candidate_hash,
                "sourceHash": source_hash,
                "partHashes": part_hashes,
                "changedParts": changed,
                "fullRegression": full,
                "selectedTestIds": test_ids,
                "selectionReasons": reasons,
                "versionCode": version.get("versionCode"),
                "versionName": version.get("versionName"),
            }
        )

        run_dir = RUNS_ROOT / report["runId"]
        backup_dir = run_dir / "backup"
        backup_dir.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(output, backup_dir / "old-index.html")
        shutil.copyfile(version_path, backup_dir / "old-version.json")
        pending = {
            "schema": 1,
            "runId": report["runId"],
            "status": "pending",
            "startedAt": report["startedAt"],
            "backupDir": str(backup_dir),
            "output": str(output),
            "versionManifest": str(version_path),
        }
        atomic_json(PENDING_PATH, pending)
        builder.atomic_write(output, assembled)
        builder.atomic_write(version_path, version_raw)
        transaction_installed = True

        env = os.environ.copy()
        env["KGG_ALLOW_RELEASE_DRIFT"] = "1"
        env["PYTHONIOENCODING"] = "utf-8"
        env["KGG_SELFTEST_SCREENSHOT_DIR"] = str(run_dir / "screenshots")
        for name, command in test_commands(full, test_ids):
            print("+ " + " ".join(command), flush=True)
            code, log, seconds = runner(command, env)
            print(log, end="" if log.endswith("\n") else "\n", flush=True)
            item = {"name": name, "ok": code == 0, "exitCode": code, "seconds": round(seconds, 3), "log": log}
            report["tests"].append(item)
            if code != 0:
                raise GateError(f"Self-test failed: {name} (exit {code})")

        builder.check(builder.DEFAULT_MANIFEST)
        report["screenshots"] = sorted(
            path.relative_to(run_dir).as_posix() for path in (run_dir / "screenshots").glob("*.png")
        ) if (run_dir / "screenshots").exists() else []
        report["status"] = "passed"
        report["finishedAt"] = utc_now()
        pending["status"] = "passed"
        pending["finishedAt"] = report["finishedAt"]
        atomic_json(run_dir / "transaction.json", pending)
        PENDING_PATH.unlink()
        transaction_installed = False
        write_report(run_dir, report, latest=True)
        print(f"KGG self-test build PASSED: {candidate_hash}")
        return report
    except Exception as exc:
        report["error"] = str(exc)
        report["finishedAt"] = utc_now()
        if transaction_installed and output and version_path and backup_dir:
            builder.atomic_write(output, (backup_dir / "old-index.html").read_bytes())
            builder.atomic_write(version_path, (backup_dir / "old-version.json").read_bytes())
            report["restoredLastGreen"] = True
            if PENDING_PATH.exists():
                PENDING_PATH.unlink()
        failure_dir = RUNS_ROOT / report["runId"]
        write_report(failure_dir, report, latest=False)
        raise GateError(str(exc)) from exc
    finally:
        release_lock()


def watch() -> int:
    print("Watching kgg-update/src for changes. Press Ctrl+C to stop.")
    last = ""
    try:
        while True:
            _, _, _, parts, _ = builder.load_build(builder.DEFAULT_MANIFEST)
            current, _ = source_state(parts)
            if current != last:
                if last:
                    time.sleep(0.7)
                try:
                    execute_build("smart")
                except GateError as exc:
                    print(f"ERROR: {exc}", file=sys.stderr)
                last = current
            time.sleep(0.8)
    except KeyboardInterrupt:
        print("Watcher stopped.")
        return 0


def main() -> int:
    configure_console()
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--smart", action="store_true", help="run critical plus impact-selected tests")
    action.add_argument("--certify", action="store_true", help="run all critical and regression tests")
    action.add_argument("--watch", action="store_true", help="watch source modules and smart-build on save")
    args = parser.parse_args()
    try:
        if args.watch:
            return watch()
        execute_build("certify" if args.certify else "smart")
        return 0
    except (GateError, builder.BuildError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
