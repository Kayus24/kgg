#!/usr/bin/env python3
"""Compact Android probe for the KGG Preview/Test APK channel."""

from __future__ import annotations

import argparse
import binascii
import json
import os
import re
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
import struct
import zlib
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_AVD = "KGG_Lite_API35"
DEFAULT_PACKAGE = "de.kgg.preview"
DEFAULT_MARKER = "Neuen Plan erstellen"


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
    options: dict[str, Any] = {
        "cwd": str(ROOT),
        "input": None,
        "text": not binary,
        "capture_output": True,
        "timeout": timeout,
    }
    if not binary:
        options.update({"encoding": "utf-8", "errors": "replace"})
    return subprocess.run(args, **options)


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


def start_emulator(emulator_path: str, avd: str) -> subprocess.Popen[Any]:
    return subprocess.Popen(
        [
            emulator_path,
            "-avd",
            avd,
            "-no-window",
            "-no-audio",
            "-no-boot-anim",
            "-no-snapshot-load",
            "-no-snapshot-save",
            "-gpu",
            "swiftshader_indirect",
            "-memory",
            "2048",
            "-cores",
            "2",
        ],
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
            serial = devices[0]
            boot = adb(adb_path, serial, ["shell", "getprop", "sys.boot_completed"], timeout=10)
            if boot.returncode == 0 and boot.stdout.strip() == "1":
                return serial
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
    tree_present = "<hierarchy" in xml_text and "android.webkit.WebView" in xml_text
    return {
        "ok": proc.returncode == 0 and tree_present,
        "path": str(ui_path),
        "marker_found": marker in xml_text,
        "summary": summary,
    }


def wait_for_app_window(adb_path: str, serial: str, package: str, timeout_s: int = 35) -> bool:
    deadline = time.time() + timeout_s
    package_lower = package.lower()
    while time.time() < deadline:
        proc = adb(adb_path, serial, ["shell", "dumpsys", "window", "windows"], timeout=15)
        text = ((proc.stdout or "") + "\n" + (proc.stderr or "")).lower()
        has_package = package_lower in text
        has_splash = "splash screen " + package_lower in text or "starting " + package_lower in text
        if proc.returncode == 0 and has_package and not has_splash:
            return True
        time.sleep(2)
    return False


def screenshot(adb_path: str, serial: str, out_dir: Path) -> dict[str, Any]:
    path = out_dir / "screenshot.png"
    proc = adb(adb_path, serial, ["exec-out", "screencap", "-p"], timeout=30, binary=True)
    data = proc.stdout if isinstance(proc.stdout, bytes) else bytes(proc.stdout or "", "utf-8")
    if proc.returncode == 0 and data:
        path.write_bytes(data)
        visual = png_visual_health(data)
        return {"ok": True, "path": str(path), **visual}
    return {"ok": False, "path": str(path), "notes": str(proc.stderr)[-300:]}


def png_visual_health(data: bytes) -> dict[str, Any]:
    try:
        if not data.startswith(b"\x89PNG\r\n\x1a\n"):
            raise ValueError("not a PNG")
        offset = 8
        width = height = color_type = bit_depth = interlace = 0
        compressed = bytearray()
        while offset + 12 <= len(data):
            length = struct.unpack(">I", data[offset : offset + 4])[0]
            kind = data[offset + 4 : offset + 8]
            payload = data[offset + 8 : offset + 8 + length]
            offset += 12 + length
            if kind == b"IHDR":
                width, height, bit_depth, color_type, _compression, _filter, interlace = struct.unpack(
                    ">IIBBBBB", payload
                )
            elif kind == b"IDAT":
                compressed.extend(payload)
            elif kind == b"IEND":
                break
        channels = {2: 3, 6: 4}.get(color_type)
        if not width or not height or bit_depth != 8 or interlace != 0 or channels is None:
            raise ValueError("unsupported PNG layout")
        raw = zlib.decompress(bytes(compressed))
        stride = width * channels
        previous = bytearray(stride)
        cursor = 0
        min_channel = 255
        max_channel = 0
        sampled = 0
        sample_step = max(1, min(width, height) // 80)
        for y in range(height):
            filter_type = raw[cursor]
            cursor += 1
            encoded = raw[cursor : cursor + stride]
            cursor += stride
            current = bytearray(stride)
            for index, value in enumerate(encoded):
                left = current[index - channels] if index >= channels else 0
                up = previous[index]
                upper_left = previous[index - channels] if index >= channels else 0
                if filter_type == 0:
                    decoded = value
                elif filter_type == 1:
                    decoded = (value + left) & 255
                elif filter_type == 2:
                    decoded = (value + up) & 255
                elif filter_type == 3:
                    decoded = (value + ((left + up) // 2)) & 255
                elif filter_type == 4:
                    estimate = left + up - upper_left
                    pa, pb, pc = abs(estimate - left), abs(estimate - up), abs(estimate - upper_left)
                    predictor = left if pa <= pb and pa <= pc else up if pb <= pc else upper_left
                    decoded = (value + predictor) & 255
                else:
                    raise ValueError("unsupported PNG filter")
                current[index] = decoded
            if y % sample_step == 0:
                for x in range(0, width, sample_step):
                    start = x * channels
                    rgb = current[start : start + 3]
                    min_channel = min(min_channel, *rgb)
                    max_channel = max(max_channel, *rgb)
                    sampled += 1
            previous = current
        channel_range = max_channel - min_channel
        return {
            "visual_nonblank": sampled > 0 and channel_range >= 24,
            "visual_channel_range": channel_range,
            "visual_samples": sampled,
        }
    except Exception as exc:  # noqa: BLE001 - compact probe evidence
        return {"visual_nonblank": False, "visual_error": str(exc)}


def probe_self_test() -> None:
    def chunk(kind: bytes, payload: bytes) -> bytes:
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", binascii.crc32(kind + payload) & 0xFFFFFFFF)

    def png(pixels: list[tuple[int, int, int]]) -> bytes:
        rows = b"".join(
            b"\x00" + bytes(channel for pixel in pixels[index : index + 2] for channel in pixel)
            for index in range(0, 4, 2)
        )
        return (
            b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", 2, 2, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(rows))
            + chunk(b"IEND", b"")
        )

    white = png([(255, 255, 255)] * 4)
    varied = png([(255, 255, 255), (0, 0, 0), (40, 120, 220), (255, 255, 255)])
    if png_visual_health(white).get("visual_nonblank"):
        raise RuntimeError("blank screenshot self-test was accepted")
    if not png_visual_health(varied).get("visual_nonblank"):
        raise RuntimeError("nonblank screenshot self-test was rejected")
    print("KGG Android Preview probe self-test OK")


def wait_for_visual(adb_path: str, serial: str, out_dir: Path, timeout_s: int = 30) -> dict[str, Any]:
    deadline = time.time() + timeout_s
    latest: dict[str, Any] = {"ok": False, "visual_nonblank": False}
    while time.time() < deadline:
        latest = screenshot(adb_path, serial, out_dir)
        if latest.get("ok") and latest.get("visual_nonblank"):
            return latest
        time.sleep(2)
    return latest


def crash_log(adb_path: str, serial: str, out_dir: Path, package: str) -> dict[str, Any]:
    proc = adb(adb_path, serial, ["logcat", "-d", "-b", "crash"], timeout=20)
    text = ((proc.stdout or "") + "\n" + (proc.stderr or "")).strip()
    path = out_dir / "logcat-crash.txt"
    path.write_text(text, encoding="utf-8", newline="\n")
    crash_lines = [line for line in text.splitlines() if package in line or "FATAL EXCEPTION" in line]
    return {
        "ok": proc.returncode == 0,
        "path": str(path),
        "crash_detected": bool(crash_lines),
        "summary": crash_lines[-10:],
    }


def system_ui_health(adb_path: str, serial: str, out_dir: Path, ui_summary: list[str]) -> dict[str, Any]:
    proc = adb(adb_path, serial, ["logcat", "-d", "-v", "brief"], timeout=30)
    text = (proc.stdout + "\n" + proc.stderr).strip()
    relevant = [
        line
        for line in text.splitlines()
        if "ANR in com.android.systemui" in line
        or "System UI isn't responding" in line
        or ("ActivityManager" in line and "com.android.systemui" in line and "ANR" in line)
    ]
    dialog_visible = any("System UI isn't responding" in item for item in ui_summary)
    path = out_dir / "logcat-system-ui.txt"
    path.write_text("\n".join(relevant) + ("\n" if relevant else ""), encoding="utf-8", newline="\n")
    return {
        "ok": proc.returncode == 0,
        "path": str(path),
        "anr_detected": bool(relevant) or dialog_visible,
        "dialog_visible": dialog_visible,
        "summary": relevant[-10:],
    }


def stop_emulator(adb_path: str, serial: str) -> None:
    try:
        adb(adb_path, serial, ["emu", "kill"], timeout=20)
    except Exception:
        pass


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
    parser.add_argument("--self-test", action="store_true", help="Run dependency-free screenshot health checks.")
    parser.add_argument("--timeout", type=int, default=180, help="Seconds to wait for emulator boot/device.")
    args = parser.parse_args()
    if args.self_test:
        probe_self_test()
        return 0

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
        "app_window_ready": False,
        "visible_marker_found": False,
        "screenshot_path": None,
        "ui_summary": [],
        "crash_detected": None,
        "log_summary": [],
        "system_ui_anr": None,
        "emulator_started_by_probe": False,
    }

    serial: str | None = None
    emulator_started = False
    emulator_process: subprocess.Popen[Any] | None = None
    try:
        devices = list_devices(adb_path)
        if not devices and args.start_emulator:
            emulator_process = start_emulator(emulator_path, args.avd)
            emulator_started = True
            result["emulator_started_by_probe"] = True
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
        time.sleep(2)
        result["app_window_ready"] = wait_for_app_window(adb_path, serial, args.package)

        shot = wait_for_visual(adb_path, serial, out_dir)
        result["screenshot_path"] = shot.get("path")
        result["screenshot_ok"] = shot.get("ok")
        result["visual_nonblank"] = shot.get("visual_nonblank")
        result["visual_channel_range"] = shot.get("visual_channel_range")

        ui = dump_ui(adb_path, serial, out_dir, args.marker)
        result["ui_path"] = ui.get("path")
        result["visible_marker_found"] = ui.get("marker_found")
        result["ui_summary"] = ui.get("summary")

        logs = crash_log(adb_path, serial, out_dir, args.package)
        result["crash_detected"] = logs.get("crash_detected")
        result["crash_log_path"] = logs.get("path")
        result["log_summary"] = logs.get("summary")

        system_ui = system_ui_health(adb_path, serial, out_dir, result["ui_summary"])
        result["system_ui_anr"] = system_ui.get("anr_detected")
        result["system_ui_log_path"] = system_ui.get("path")
        result["system_ui_summary"] = system_ui.get("summary")

        result["ok"] = bool(
            started["ok"]
            and result["app_window_ready"]
            and shot.get("ok")
            and shot.get("visual_nonblank")
            and ui.get("ok")
            and not result["crash_detected"]
            and not result["system_ui_anr"]
        )
        if result["system_ui_anr"]:
            result["error"] = "emulator SystemUI ANR; use the physical Test-App as the visual approval gate"
        elif not shot.get("visual_nonblank"):
            result["error"] = "emulator app window stayed visually blank"
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["ok"] else 5
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        result["error"] = str(exc)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1
    finally:
        if emulator_started and serial:
            stop_emulator(adb_path, serial)
            time.sleep(12)
        if emulator_process is not None:
            try:
                emulator_process.wait(timeout=45)
            except subprocess.TimeoutExpired:
                emulator_process.terminate()


if __name__ == "__main__":
    raise SystemExit(main())
