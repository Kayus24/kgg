from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from typing import Any, Callable, Mapping
from urllib.parse import quote

ROUTE_SCHEMA = "project-route/v1"
MAPPING_SCHEMA = "kgg-project-status/v1"
TELEMETRY_REPO = "Kayus24/project-status-telemetry"
MAPPING_FILE = ".kgg-project-status.json"
PROJECT_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{1,63}$")


@dataclass(frozen=True)
class ProjectMapping:
    project_id: str


def find_project_mapping(cwd: str) -> ProjectMapping | None:
    try:
        current = Path(cwd).expanduser().resolve(strict=False)
    except OSError:
        current = Path(cwd).expanduser().absolute()

    for directory in (current, *current.parents):
        candidate = directory / MAPPING_FILE
        if not candidate.is_file():
            continue
        try:
            data = json.loads(candidate.read_text(encoding="utf-8"))
        except Exception:
            return None
        if not isinstance(data, dict) or data.get("schema") != MAPPING_SCHEMA:
            return None
        if set(data) - {"schema", "project_id"}:
            return None
        project_id = data.get("project_id")
        if not isinstance(project_id, str):
            return None
        project_id = project_id.strip()
        if not PROJECT_ID_RE.fullmatch(project_id):
            return None
        return ProjectMapping(project_id=project_id)
    return None


def session_is_persisted(
    session_id: str,
    *,
    index_path: Path | None = None,
    retries: int = 3,
    delay_seconds: float = 0.35,
) -> bool:
    path = index_path or (Path.home() / ".codex" / "session_index.jsonl")
    for attempt in range(max(1, retries)):
        try:
            if path.is_file():
                with path.open("r", encoding="utf-8", errors="replace") as handle:
                    for line in handle:
                        try:
                            item = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        if isinstance(item, dict) and item.get("id") == session_id:
                            return True
        except OSError:
            pass
        if attempt + 1 < max(1, retries):
            time.sleep(max(0.0, delay_seconds))
    return False


def codex_protocol_available() -> bool:
    if os.name != "nt":
        return False
    try:
        import winreg

        for root in (winreg.HKEY_CURRENT_USER, winreg.HKEY_CLASSES_ROOT):
            try:
                with winreg.OpenKey(root, r"Software\Classes\codex" if root == winreg.HKEY_CURRENT_USER else r"codex") as key:
                    winreg.QueryValueEx(key, "URL Protocol")
                    return True
            except OSError:
                continue
    except Exception:
        return False
    return False


def build_route_body(
    project_id: str,
    session_id: str,
    *,
    verified: bool,
) -> str:
    if not PROJECT_ID_RE.fullmatch(project_id):
        raise ValueError("project_id_invalid")
    if (
        not session_id
        or len(session_id) > 256
        or any(ch in session_id for ch in "\r\n")
        or any(ord(ch) < 32 or ord(ch) == 127 for ch in session_id)
    ):
        raise ValueError("session_id_invalid")

    lines = [
        f"schema: {ROUTE_SCHEMA}",
        f"project_id: {project_id}",
        "surface: codex",
        f"session_ref: {session_id}",
    ]
    if verified:
        lines.append(f"open_url: codex://threads/{quote(session_id, safe='')}")
        lines.append("route_state: verified")
    else:
        lines.append("route_state: correlation_only")
    return "\n".join(lines)


def _route_identity(body: str) -> tuple[str, str] | None:
    values: dict[str, str] = {}
    for raw in body.splitlines():
        if ":" not in raw:
            continue
        key, value = raw.split(":", 1)
        key = key.strip().lstrip("\ufeff")
        if key in values:
            return None
        values[key] = value.strip()
    if values.get("schema") != ROUTE_SCHEMA:
        return None
    project_id = values.get("project_id")
    surface = values.get("surface")
    if not project_id or surface not in {"chatgpt", "codex"}:
        return None
    return project_id, surface


def plan_route_write(
    issues: list[Mapping[str, Any]],
    project_id: str,
    desired_body: str,
) -> tuple[str, int | None, tuple[int, ...]]:
    matches: list[Mapping[str, Any]] = []
    for issue in issues:
        if issue.get("state") != "open" or "pull_request" in issue:
            continue
        body = issue.get("body")
        if not isinstance(body, str):
            continue
        if _route_identity(body) == (project_id, "codex"):
            matches.append(issue)

    if not matches:
        return "create", None, ()
    if len(matches) > 1:
        numbers = tuple(
            sorted(
                int(item["number"])
                for item in matches
                if isinstance(item.get("number"), int)
            )
        )
        return "fail_duplicate", None, numbers

    issue = matches[0]
    number = issue.get("number")
    if not isinstance(number, int) or number <= 0:
        return "fail_duplicate", None, ()
    title = str(issue.get("title") or "")
    desired_title = f"[route:codex] {project_id}"
    existing_body = str(issue.get("body") or "").strip()
    if title == desired_title and existing_body == desired_body:
        return "noop", number, ()
    return "update", number, ()


def _run(
    args: list[str],
    *,
    timeout: float,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )


def sync_route(
    payload: Mapping[str, Any],
    *,
    run_command: Callable[..., subprocess.CompletedProcess[str]] = _run,
    index_path: Path | None = None,
    protocol_available: bool | None = None,
) -> str:
    if payload.get("hook_event_name") != "SessionStart":
        return "ignored_event"

    session_id = str(payload.get("session_id") or "").strip()
    cwd = str(payload.get("cwd") or "").strip()
    if not session_id or not cwd:
        return "invalid_identity"

    mapping = find_project_mapping(cwd)
    if mapping is None:
        return "no_mapping"

    verified = (
        codex_protocol_available() if protocol_available is None else protocol_available
    ) and session_is_persisted(
        session_id,
        index_path=index_path,
    )
    body = build_route_body(
        mapping.project_id,
        session_id,
        verified=verified,
    )

    if shutil.which("gh") is None and run_command is _run:
        return "gh_unavailable"

    try:
        fetched = run_command(
            [
                "gh",
                "api",
                "--method",
                "GET",
                f"repos/{TELEMETRY_REPO}/issues",
                "-f",
                "state=open",
                "-f",
                "per_page=100",
            ],
            timeout=8.0,
        )
    except Exception:
        return "fetch_failed"
    if fetched.returncode != 0:
        return "fetch_failed"
    try:
        items = json.loads(fetched.stdout)
    except json.JSONDecodeError:
        return "fetch_invalid"
    if not isinstance(items, list):
        return "fetch_invalid"

    action, issue_number, _duplicates = plan_route_write(
        items,
        mapping.project_id,
        body,
    )
    title = f"[route:codex] {mapping.project_id}"
    if action == "fail_duplicate":
        return action
    if action == "noop":
        return action

    if action == "create":
        args = [
            "gh",
            "issue",
            "create",
            "--repo",
            TELEMETRY_REPO,
            "--title",
            title,
            "--body",
            body,
        ]
    else:
        assert issue_number is not None
        args = [
            "gh",
            "issue",
            "edit",
            str(issue_number),
            "--repo",
            TELEMETRY_REPO,
            "--title",
            title,
            "--body",
            body,
        ]

    try:
        written = run_command(args, timeout=8.0)
    except Exception:
        return "write_failed"
    if written.returncode != 0:
        return "write_failed"
    return "created" if action == "create" else "updated"


def main() -> int:
    try:
        raw = sys.stdin.read()
        payload = json.loads(raw)
        if isinstance(payload, dict):
            sync_route(payload)
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
