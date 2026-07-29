#!/usr/bin/env python3
"""Static safety and syntax checks for the patient update recovery page."""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML_PATH = ROOT / "update-recovery.html"
WORKER_PATH = ROOT / "service-worker.js"


def fail(message: str) -> None:
    raise SystemExit(f"Update recovery smoke failed: {message}")


def require(text: str, *fragments: str) -> None:
    for fragment in fragments:
        if fragment not in text:
            fail(f"missing required fragment {fragment!r}")


def forbid(text: str, *fragments: str) -> None:
    lowered = text.lower()
    for fragment in fragments:
        if fragment.lower() in lowered:
            fail(f"forbidden data-destructive fragment {fragment!r}")


def validate_html() -> None:
    html = HTML_PATH.read_text(encoding="utf-8")
    worker = WORKER_PATH.read_text(encoding="utf-8")
    version_match = re.search(r"const APP_VERSION = '([0-9]+)';", worker)
    if not version_match:
        fail("service-worker.js has no numeric APP_VERSION")
    version = version_match.group(1)
    require(
        html,
        f"const RELEASE='{version}';",
        "const CACHE_PREFIX='kgg-handyplan-';",
        "navigator.serviceWorker.getRegistrations()",
        "registration.unregister()",
        "keys.filter(key=>key.startsWith(CACHE_PREFIX))",
        "updateViaCache:'none'",
        "service-worker.js?recovery=",
        "GET_UPDATE_DIAGNOSTICS",
        "String(info.version||'')!==RELEASE",
        "location.replace('./?recovered='+RELEASE",
    )
    forbid(
        html,
        "localStorage.clear",
        "sessionStorage.clear",
        "indexedDB.deleteDatabase",
        "localStorage.removeItem",
        "indexedDB.open",
        "caches.keys().then(keys=>Promise.all(keys.map",
    )

    scripts = re.findall(r"<script>([\s\S]*?)</script>", html, flags=re.IGNORECASE)
    if len(scripts) != 1:
        fail("recovery page must contain exactly one inline script")
    node = shutil.which("node")
    if node:
        with tempfile.NamedTemporaryFile("w", suffix=".js", encoding="utf-8", delete=False) as handle:
            handle.write(scripts[0])
            temp_path = Path(handle.name)
        try:
            result = subprocess.run(
                [node, "--check", str(temp_path)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                fail(f"inline recovery script is invalid JavaScript: {result.stderr.strip()}")
        finally:
            temp_path.unlink(missing_ok=True)


def validate_worker() -> None:
    worker = WORKER_PATH.read_text(encoding="utf-8")
    version_match = re.search(r"const APP_VERSION = '([0-9]+)';", worker)
    if not version_match:
        fail("service-worker.js has no numeric APP_VERSION")
    version = version_match.group(1)
    require(
        worker,
        f"kgg-handyplan-v{version}-",
        f"const APP_VERSION = '{version}';",
        "const RECOVERY_PATH = './update-recovery.html';",
        "GET_UPDATE_DIAGNOSTICS",
        "recoveryPath:RECOVERY_PATH",
        "isRecoveryRequest(event.request)",
        "fetch(event.request,{cache:'no-store'})",
    )


def main() -> int:
    validate_html()
    validate_worker()
    print("Patient update recovery smoke: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
