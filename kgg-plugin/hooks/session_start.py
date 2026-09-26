from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
from typing import Any, Mapping

SCHEMA = "kgg-codex-session/v1"
ALLOWED_SOURCES = {"startup", "resume", "clear", "compact", "fork"}


def _canonical_cwd(value: str) -> str:
    path = Path(value).expanduser()
    try:
        resolved = path.resolve(strict=False)
    except OSError:
        resolved = path.absolute()
    return os.path.normcase(os.path.normpath(str(resolved)))


def _safe_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _atomic_write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + f".tmp-{os.getpid()}")
    temp.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )
    os.replace(temp, path)


def capture_session(
    payload: Mapping[str, Any],
    plugin_data: Path,
    *,
    observed_at: str | None = None,
) -> dict[str, str] | None:
    if payload.get("hook_event_name") != "SessionStart":
        return None

    session_id = str(payload.get("session_id") or "").strip()
    cwd = str(payload.get("cwd") or "").strip()
    source = str(payload.get("source") or "").strip()

    if not session_id or len(session_id) > 512:
        return None
    if not cwd or len(cwd) > 4096:
        return None
    if source not in ALLOWED_SOURCES:
        return None

    canonical_cwd = _canonical_cwd(cwd)
    timestamp = observed_at or datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    identity = {
        "schema": SCHEMA,
        "session_id": session_id,
        "cwd": canonical_cwd,
        "source": source,
        "observed_at": timestamp,
    }

    root = plugin_data / "project-status-routing"
    session_path = root / "sessions" / f"{_safe_hash(session_id)}.json"
    cwd_path = root / "latest-by-cwd" / f"{_safe_hash(canonical_cwd)}.json"

    _atomic_write_json(session_path, identity)
    _atomic_write_json(cwd_path, identity)
    return identity


def main() -> int:
    plugin_data_raw = os.environ.get("PLUGIN_DATA") or os.environ.get("CLAUDE_PLUGIN_DATA")
    if not plugin_data_raw:
        return 0

    try:
        raw = sys.stdin.read()
        payload = json.loads(raw)
        if not isinstance(payload, dict):
            return 0
        capture_session(payload, Path(plugin_data_raw))
    except Exception:
        # Session tracking must never block Codex startup/resume.
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
