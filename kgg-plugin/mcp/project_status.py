from __future__ import annotations

from typing import Any, Mapping
from urllib.parse import urlparse
import re

INTENT_SCHEMA = "project-status-intent/v1"
STATUS_SCHEMA = "project-status/v1"
ROUTE_SCHEMA = "project-route/v1"
REPOSITORY = "Kayus24/project-status-telemetry"

PROJECT_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{1,63}$")
STATES = {"running", "waiting", "blocked", "paused", "failed", "complete"}
ALLOWED_KEYS = {
    "project_id",
    "project_name",
    "state",
    "step",
    "source",
    "completed",
    "total",
    "blocker",
    "waiting_for",
}


class ProjectStatusError(ValueError):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _fail(code: str) -> None:
    raise ProjectStatusError(code)


def _clean_text(
    value: Any,
    label: str,
    *,
    maximum: int,
    required: bool = True,
) -> str | None:
    if value is None and not required:
        return None
    if not isinstance(value, str):
        _fail(f"{label}_invalid")
    cleaned = value.strip()
    if not cleaned and required:
        _fail(f"{label}_invalid")
    if not cleaned and not required:
        return None
    if len(cleaned) > maximum or any(ch in cleaned for ch in "\r\n"):
        _fail(f"{label}_invalid")
    return cleaned


def _source(value: Any) -> str | None:
    cleaned = _clean_text(value, "source", maximum=2048, required=False)
    if cleaned is None:
        return None
    parsed = urlparse(cleaned)
    if (
        parsed.scheme != "https"
        or not parsed.netloc
        or parsed.username
        or parsed.password
        or parsed.fragment
    ):
        _fail("source_invalid")
    return cleaned


def _progress(completed: Any, total: Any) -> tuple[int | None, int | None]:
    if (completed is None) != (total is None):
        _fail("progress_pair_invalid")
    if completed is None:
        return None, None
    if (
        isinstance(completed, bool)
        or isinstance(total, bool)
        or not isinstance(completed, int)
        or not isinstance(total, int)
        or total <= 0
        or completed < 0
        or completed > total
    ):
        _fail("progress_invalid")
    return completed, total


def extract_chatgpt_session_ref(params: Mapping[str, Any]) -> str | None:
    meta = params.get("_meta")
    if not isinstance(meta, Mapping):
        return None
    value = meta.get("openai/session")
    if not isinstance(value, str):
        return None
    cleaned = value.strip()
    if not cleaned or len(cleaned) > 512:
        return None
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in cleaned):
        return None
    return cleaned


def build_checkpoint_intent(
    arguments: Mapping[str, Any],
    *,
    session_ref: str | None,
) -> dict[str, Any]:
    if set(arguments) - ALLOWED_KEYS:
        _fail("status_arguments_invalid")

    project_id = _clean_text(arguments.get("project_id"), "project_id", maximum=64)
    assert project_id is not None
    if not PROJECT_ID_RE.fullmatch(project_id):
        _fail("project_id_invalid")

    project_name = _clean_text(
        arguments.get("project_name"),
        "project_name",
        maximum=200,
    )
    state = _clean_text(arguments.get("state"), "state", maximum=16)
    if state not in STATES:
        _fail("state_invalid")
    step = _clean_text(arguments.get("step"), "step", maximum=200)
    source = _source(arguments.get("source"))
    blocker = _clean_text(
        arguments.get("blocker"),
        "blocker",
        maximum=200,
        required=False,
    )
    waiting_for = _clean_text(
        arguments.get("waiting_for"),
        "waiting_for",
        maximum=200,
        required=False,
    )
    completed, total = _progress(
        arguments.get("completed"),
        arguments.get("total"),
    )

    body_lines = [
        f"schema: {STATUS_SCHEMA}",
        f"project_id: {project_id}",
        f"state: {state}",
        f"step: {step}",
    ]
    if completed is not None:
        body_lines.extend((f"completed: {completed}", f"total: {total}"))
    if source is not None:
        body_lines.append(f"source: {source}")
    body_lines.append("actor: chatgpt")
    if blocker is not None:
        body_lines.append(f"blocker: {blocker}")
    if waiting_for is not None:
        body_lines.append(f"waiting_for: {waiting_for}")

    status_action = "finalize_and_close" if state == "complete" else "upsert"
    status_issue = {
        "repository": REPOSITORY,
        "match": {
            "schema": STATUS_SCHEMA,
            "project_id": project_id,
            "state": "open",
        },
        "title": project_name,
        "body": "\n".join(body_lines),
        "action": status_action,
    }

    route: dict[str, Any]
    if session_ref is None:
        route = {
            "publish": False,
            "reason": "session_metadata_unavailable",
        }
    else:
        route_body = "\n".join(
            (
                f"schema: {ROUTE_SCHEMA}",
                f"project_id: {project_id}",
                "surface: chatgpt",
                f"session_ref: {session_ref}",
                "route_state: correlation_only",
            )
        )
        route = {
            "publish": True,
            "repository": REPOSITORY,
            "match": {
                "schema": ROUTE_SCHEMA,
                "project_id": project_id,
                "surface": "chatgpt",
                "state": "open",
            },
            "title": f"[route:chatgpt] {project_id}",
            "body": route_body,
            "route_state": "correlation_only",
        }

    return {
        "schema": INTENT_SCHEMA,
        "operation": "project_status_checkpoint",
        "project_id": project_id,
        "status_issue": status_issue,
        "chatgpt_route": route,
        "writer": {
            "required": "connected_github_app",
            "write_performed": False,
            "duplicate_policy": "fail_closed",
        },
    }
