#!/usr/bin/env python3
"""Compact Android probe for the KGG Preview/Test APK channel."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_AVD = "Medium_Phone_API_36.1"
DEFAULT_PACKAGE = "de.kgg.preview"
DEFAULT_MARKER = "Groesse 100%"


def sdk_path(*parts: str) -> Path:
    base = Path(os.environ.get("LOCALAPPDATA", "")) / "Android" / "Sdk"
    return base.joinpath(*parts)


def resolve_tool(explicit: str | None, env_name: str, default_path: Path, fallback: str) -> str:
    if explicit:
        return explicit
    env_value = os.environ.get(env_name)
    if env_value:
        return env_value
    if default_path.exists():
        return str(default_path)
    return fallback


def run(args: list[str], *, timeout: int = 30, binary: bool = False) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(
        args,
        cwd=str(ROOT),
        input=None,
        text=not binary,
        capture_output=True,
        timeout=timeout,
    )


def adb(adb_path: str, serial: str | None, args: list[str], *, timeout: int = 30, binary: bool = False) -> subprocess.CompletedProcess[Any]:
    command = [adb_path]
    if serial:
        command.extend(["-s", serial])
    command.extend(args)
    return run(command, timeout=timeout, binary=binary)


def list_devices(adb_path: str) -> list[str]:
    proc = adb(adb_path, None, ["devices"], timeout=15)
    if proc.returncode != 0:
        return []
    devices: list[str] = []
    for line in proc.stdout.splitlines()[1:]:
        parts = line.strip().split()
        if len(parts) >= 2 and parts[1] == "device":
            devices.append(parts[0])
    return devices


def start_emulator(emulator_path: str, avd: str) -> None:
    subprocess.Popen(
        [emulator_path, "-avd", avd, "-no-snapshot-save"],
        cwd=str(ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
    )


def wait_for_device(adb_path: str, timeout_s: int) -> str | None:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        devices = list_devices(adb_path)
        if devices:
            return devices[0]
        time.sleep(3)
    return None


def install_apk(adb_path: str, serial: str, apk: Path | None) -> dict[str, Any]:
    if apk is None:
        return {"attempted": False, "ok": None, "notes": "no apk supplied"}
    if not apk.exists():
        return {"attempted": True, "ok": False, "notes": f"apk missing: {apk}"}
    proc = adb(adb_path, serial, ["install", "-r", str(apk)], timeout=180)
    output = (proc.stdout + "\n" + proc.stderr).strip()
    return {"attempted": True, "ok": proc.returncode == 0, "notes": output[-600:]}


def resolve_activity(adb_path: str, serial: str, package: str) -> tuple[str | None, str]:
    proc = adb(adb_path, serial, ["shell", "cmd", "package", "resolve-activity", "--brief", package], timeout=20)
    output = (proc.stdout + "\n" + proc.stderr).strip()
    if proc.returncode != 0:
        return None, output
    for line in reversed(output.splitlines()):
        line = line.strip()
        if "/" in line and not line.startswith("No activity"):
            return line, output
    return None, output


def start_activity(adb_path: str, serial: str, activity: str) -> dict[str, Any]:
    proc = adb(adb_path, serial, ["shell", "am", "start", "-n", activity], timeout=20)
    output = (proc.stdout + "\n" + proc.stderr).strip()
    return {"ok": proc.returncode == 0 and "Error" not in output, "notes": output[-600:]}


def extract_ui_xml(raw: str) -> str:
    start = raw.find("<?xml")
    if start < 0:
        start = raw.find("<hierarchy")
    if start < 0:
        return raw
    return raw[start:].strip()


def summarize_ui(xml_text: str, limit: int = 20) -> list[str]:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []
    seen: list[str] = []
    for node in root.iter("node"):
        text = (node.attrib.get("text") or node.attrib.get("content-desc") or "").strip()
        if not text or text in seen:
            continue
        seen.append(text)
        if len(seen) >= limit:
            break
    return seen


def dump_ui(adb_path: str, serial: str, out_dir: Path, marker: str) -> dict[str, Any]:
    proc = adb(adb_path, serial, ["exec-out", "uiautomator", "dump", "/dev/tty"], timeout=30)
    raw = (proc.stdout + "\n" + proc.stderr).strip()
    xml_text = extract_ui_xml(raw)
    ui_path = out_dir / "ui.xml"
    ui_path.write_text(xml_text, encoding="utf-8", newline="\n")
    summary = summarize_ui(xml_text)
    return {
        "ok": proc.returncode == 0 and bool(summary),
        "path": str(ui_path),
        "marker_found": marker in xml_text,
        "summary": summary,
    }


def screenshot(adb_path: str, serial: str, out_dir: Path) -> dict[str, Any]:
    path = out_dir / "screenshot.png"
    proc = adb(adb_path, serial, ["exec-out", "screencap", "-p"], timeout=30, binary=True)
    data = proc.stdout if isinstance(proc.stdout, bytes) else bytes(proc.stdout or "", "utf-8")
    if proc.returncode == 0 and data:
        path.write_bytes(data)
        return {"ok": True, "path": str(path)}
    return {"ok": False, "path": str(path), "notes": str(proc.stderr)[-300:]}


def crash_log(adb_path: str, serial: str, out_dir: Path, package: str) -> dict[str, Any]:
    proc = adb(adb_path, serial, ["logcat", "-d", "-b", "crash"], timeout=20)
    text = (proc.stdout + "\n" + proc.stderr).strip()
    path = out_dir / "logcat-crash.txt"
    path.write_text(text, encoding="utf-8", newline="\n")
    crash_lines = [line for line in text.splitlines() if package in line or "FATAL EXCEPTION" in line]
    return {
        "ok": proc.returncode == 0,
        "path": str(path),
        "crash_detected": bool(crash_lines),
        "summary": crash_lines[-10:],
    }


def package_installed(adb_path: str, serial: str, package: str) -> bool:
    proc = adb(adb_path, serial, ["shell", "pm", "path", package], timeout=20)
    return proc.returncode == 0 and "package:" in proc.stdout


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe the KGG Preview/Test APK in an Android emulator.")
    parser.add_argument("--apk", type=Path, help="Optional APK to install before probing.")
    parser.add_argument("--package", default=DEFAULT_PACKAGE, help=f"Android package name, default {DEFAULT_PACKAGE}.")
    parser.add_argument("--avd", default=DEFAULT_AVD, help=f"AVD name, default {DEFAULT_AVD}.")
    parser.add_argument("--marker", default=DEFAULT_MARKER, help="Visible marker to search in UI tree, default %(default)s.")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "tmp" / "android-preview-probe", help="Output directory for screenshot/UI/logs.")
    parser.add_argument("--adb", help="Path to adb.exe.")
    parser.add_argument("--emulator", help="Path to emulator.exe.")
    parser.add_argument("--start-emulator", action="store_true", help="Start the configured AVD when no adb device is connected.")
    parser.add_argument("--timeout", type=int, default=180, help="Seconds to wait for emulator boot/device.")
    args = parser.parse_args()

    adb_path = resolve_tool(args.adb, "KGG_ADB", sdk_path("platform-tools", "adb.exe"), "adb")
    emulator_path = resolve_tool(args.emulator, "KGG_EMULATOR", sdk_path("emulator", "emulator.exe"), "emulator")
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    result: dict[str, Any] = {
        "package": args.package,
        "avd": args.avd,
        "adb": adb_path,
        "emulator": emulator_path,
        "ok": False,
        "serial": None,
        "installed": None,
        "activity": None,
        "activity_started": False,
        "visible_marker_found": False,
        "screenshot_path": None,
        "ui_summary": [],
        "crash_detected": None,
        "log_summary": [],
    }

    try:
        devices = list_devices(adb_path)
        if not devices and args.start_emulator:
            start_emulator(emulator_path, args.avd)
            serial = wait_for_device(adb_path, args.timeout)
        else:
            serial = devices[0] if devices else None
        result["serial"] = serial
        if not serial:
            result["error"] = "no adb device connected"
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 2

        install = install_apk(adb_path, serial, args.apk)
        result["install"] = install
        installed = package_installed(adb_path, serial, args.package)
        result["installed"] = installed
        if not installed:
            result["error"] = f"package not installed: {args.package}"
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 3

        activity, activity_output = resolve_activity(adb_path, serial, args.package)
        result["activity"] = activity
        result["activity_resolution"] = activity_output[-600:]
        if not activity:
            result["error"] = "cannot resolve launcher activity"
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 4

        started = start_activity(adb_path, serial, activity)
        result["activity_started"] = started["ok"]
        result["activity_start"] = started["notes"]
        time.sleep(5)

        shot = screenshot(adb_path, serial, out_dir)
        result["screenshot_path"] = shot.get("path")
        result["screenshot_ok"] = shot.get("ok")

        ui = dump_ui(adb_path, serial, out_dir, args.marker)
        result["ui_path"] = ui.get("path")
        result["visible_marker_found"] = ui.get("marker_found")
        result["ui_summary"] = ui.get("summary")

        logs = crash_log(adb_path, serial, out_dir, args.package)
        result["crash_detected"] = logs.get("crash_detected")
        result["crash_log_path"] = logs.get("path")
        result["log_summary"] = logs.get("summary")

        result["ok"] = bool(started["ok"] and not result["crash_detected"])
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["ok"] else 5
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        result["error"] = str(exc)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
