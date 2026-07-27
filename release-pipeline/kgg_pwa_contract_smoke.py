#!/usr/bin/env python3
"""Validate the patient PWA manifest, icon and service-worker delivery contract."""

from __future__ import annotations

import json
import shutil
import struct
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = "65"
MANIFEST_PATHS = (ROOT / "manifest.json", ROOT / "manifest-v64.webmanifest")
ICON_CONTRACT = {
    "kgg-icon-192-v63.png": (192, 192, "any"),
    "kgg-icon-512-v63.png": (512, 512, "any"),
    "kgg-icon-maskable-512-v63.png": (512, 512, "maskable"),
}


def fail(message: str) -> None:
    raise SystemExit(f"PWA contract failed: {message}")


def read_png_size(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        fail(f"{path.name} is not a readable PNG")
    if data[12:16] != b"IHDR":
        fail(f"{path.name} has no PNG IHDR header")
    return struct.unpack(">II", data[16:24])


def load_manifest(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot parse {path.name}: {exc}")


def validate_manifest(manifest: dict, path: Path) -> None:
    expected = {
        "name": "KGG Handyplan",
        "short_name": "KGG Plan",
        "start_url": "./",
        "scope": "./",
        "display": "standalone",
    }
    for key, value in expected.items():
        if manifest.get(key) != value:
            fail(f"{path.name} has {key}={manifest.get(key)!r}, expected {value!r}")

    icons = manifest.get("icons")
    if not isinstance(icons, list) or len(icons) != len(ICON_CONTRACT):
        fail(f"{path.name} must contain exactly {len(ICON_CONTRACT)} icons")

    by_src = {entry.get("src"): entry for entry in icons if isinstance(entry, dict)}
    if set(by_src) != set(ICON_CONTRACT):
        fail(f"{path.name} icon sources do not match the v63 icon contract")

    for src, (width, height, purpose) in ICON_CONTRACT.items():
        entry = by_src[src]
        if entry.get("type") != "image/png":
            fail(f"{src} must be declared as image/png")
        if entry.get("sizes") != f"{width}x{height}":
            fail(f"{src} has the wrong declared size")
        if entry.get("purpose") != purpose:
            fail(f"{src} has purpose={entry.get('purpose')!r}, expected {purpose!r}")
        actual_size = read_png_size(ROOT / src)
        if actual_size != (width, height):
            fail(f"{src} is {actual_size[0]}x{actual_size[1]}, expected {width}x{height}")


def validate_worker() -> None:
    worker_path = ROOT / "service-worker.js"
    worker = worker_path.read_text(encoding="utf-8")

    required_fragments = (
        "kgg-handyplan-v65-set-summary-range",
        "const APP_VERSION = '65';",
        "./manifest-v64.webmanifest",
        "./kgg-icon-192-v63.png",
        "./kgg-icon-512-v63.png",
        "./kgg-icon-maskable-512-v63.png",
        "./patient-version-label.js?v=65",
        "./patient-set-summary-groups.js?v=set-summary-groups-2-range-label",
        'rel="manifest" href="./manifest-v64.webmanifest"',
        'rel="icon" type="image/png" sizes="192x192" href="./kgg-icon-192-v63.png"',
        'rel="apple-touch-icon" sizes="192x192" href="./kgg-icon-192-v63.png"',
    )
    for fragment in required_fragments:
        if fragment not in worker:
            fail(f"service-worker.js is missing {fragment!r}")

    if "v59.png" in worker or "v59'" in worker or 'v59"' in worker:
        fail("service-worker.js still contains a v59 icon reference")

    node = shutil.which("node")
    if node:
        result = subprocess.run(
            [node, "--check", str(worker_path)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            fail(f"service-worker.js is invalid JavaScript: {result.stderr.strip()}")


def validate_update_lifecycle() -> None:
    label = (ROOT / "patient-version-label.js").read_text(encoding="utf-8")
    if "const RELEASE='65';" not in label:
        fail("patient-version-label.js is not aligned with release 65")


def validate_static_compatibility(manifest: dict) -> None:
    html = (ROOT / "index.html").read_text(encoding="utf-8-sig")
    if '<link rel="manifest" href="manifest.json">' not in html:
        fail("index.html no longer exposes the first-load compatibility manifest")
    if load_manifest(ROOT / "manifest.json") != manifest:
        fail("manifest.json and manifest-v64.webmanifest must remain identical")


def main() -> int:
    manifests = [load_manifest(path) for path in MANIFEST_PATHS]
    for manifest, path in zip(manifests, MANIFEST_PATHS):
        validate_manifest(manifest, path)
    validate_static_compatibility(manifests[1])
    validate_worker()
    validate_update_lifecycle()
    print("Patient PWA contract: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
