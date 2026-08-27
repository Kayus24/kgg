#!/usr/bin/env python3
"""Validate the additive KGG Brain-Relay-Worker coordination contract."""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence


CAPSULE_SCHEMA = "kgg-brain-relay-worker/v2"
HANDOFF_SCHEMA = "kgg-brain-relay-worker/handoff-v2"
RESULT_SCHEMA = "kgg-brain-relay-worker/result-v2"
BROWSER_RELAY_SCHEMA = "kgg-brain-relay-worker/browser-relay-v2"
TASK_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{5,63}$")
CHAT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{1,95}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

MAX_SUB_CHATS = 4
MAX_LUNA_WORKERS = 3
MAX_VERIFIERS = 1
MAX_LUNA_ATTEMPTS = 2
ROTATION_PREPARE_AT = 35
ROTATION_HARD_AT = 40
BROWSER_TIMEOUT_SECONDS = 30 * 60
MAX_BROWSER_FRESH_RETRIES = 1

ROLE_MODELS = {
    "luna-manager": ("gpt-5.6-luna", "low"),
    "luna-relay": ("gpt-5.6-luna", "low"),
    "ticket-master": ("gpt-5.6-luna", "low"),
    "cricket": ("gpt-5.6-luna", "low"),
    "luna-max-worker": ("gpt-5.6-luna", "max"),
    "verifier": ("gpt-5.6-luna", "max"),
    "sol-endboss": ("gpt-5.6-sol", "ultra"),
    "lead-gpt": ("custom-gpt", "actions"),
    "gpt-subchat": ("custom-gpt", "actions"),
}
KNOWN_ROLES = set(ROLE_MODELS) | {"ci-acceptance", "status-read"}
FORBIDDEN_KEYS = {
    "api_key",
    "apikey",
    "base64",
    "chat_transcript",
    "credit_count",
    "hidden_cot",
    "invisible_agent",
    "patient_data",
    "raw_payload",
    "secret",
    "stop_function",
    "token",
    "token_count",
}
FORBIDDEN_SOL_ACTIONS = {
    "code",
    "debug",
    "micromanagement",
    "micromanage",
    "repo_analysis",
    "repo_grossanalyse",
    "repository_analysis",
    "large_repo_analysis",
    "repair",
    "implement",
    "solve",
    "fix",
    "test",
}
ALLOWED_TRANSITIONS = {
    ("ticket-master", "luna-manager"),
    ("luna-manager", "lead-gpt"),
    ("lead-gpt", "gpt-subchat"),
    ("gpt-subchat", "lead-gpt"),
    ("lead-gpt", "luna-relay"),
    ("luna-relay", "luna-max-worker"),
    ("luna-relay", "verifier"),
    ("luna-max-worker", "luna-relay"),
    ("verifier", "luna-relay"),
    ("luna-relay", "lead-gpt"),
    ("lead-gpt", "ci-acceptance"),
    ("ci-acceptance", "lead-gpt"),
    ("cricket", "luna-manager"),
    ("cricket", "lead-gpt"),
    ("lead-gpt", "cricket"),
    ("luna-manager", "cricket"),
}


class ContractError(ValueError):
    """Raised when a visible coordination object violates the contract."""


def _fail(message: str) -> None:
    raise ContractError(message)


def _object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        _fail(f"{label} must be an object")
    return value


def _string(value: Any, label: str, *, non_empty: bool = True) -> str:
    if not isinstance(value, str) or (non_empty and not value.strip()):
        _fail(f"{label} must be a non-empty string")
    return value


def _positive_int(value: Any, label: str, *, maximum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        _fail(f"{label} must be a positive integer")
    if maximum is not None and value > maximum:
        _fail(f"{label} must be <= {maximum}")
    return value


def _non_negative_int(value: Any, label: str, *, maximum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        _fail(f"{label} must be a non-negative integer")
    if maximum is not None and value > maximum:
        _fail(f"{label} must be <= {maximum}")
    return value


def _sha(value: Any, label: str) -> str:
    result = _string(value, label)
    if SHA256_RE.fullmatch(result) is None:
        _fail(f"{label} must be a lowercase SHA-256")
    return result


def _task_id(value: Any, label: str = "task_id") -> str:
    result = _string(value, label)
    if TASK_ID_RE.fullmatch(result) is None:
        _fail(f"{label} must match the lowercase task-id contract")
    return result


def _chat_id(value: Any, label: str) -> str:
    result = _string(value, label)
    if CHAT_ID_RE.fullmatch(result) is None:
        _fail(f"{label} is not a safe chat identifier")
    return result


def _string_list(value: Any, label: str, *, non_empty: bool = False) -> list[str]:
    if not isinstance(value, list) or (non_empty and not value):
        _fail(f"{label} must be a {'non-empty ' if non_empty else ''}list")
    result: list[str] = []
    for index, item in enumerate(value):
        result.append(_string(item, f"{label}[{index}]"))
    return result


def _check_forbidden_keys(value: Any, path: str = "root") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            normalized = str(key).strip().lower().replace("-", "_")
            if normalized in FORBIDDEN_KEYS:
                _fail(f"{path}.{key} is not allowed in coordination data")
            _check_forbidden_keys(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _check_forbidden_keys(child, f"{path}[{index}]")


def validate_agent_identity(agent: Mapping[str, Any], label: str = "agent") -> None:
    role = _string(agent.get("role"), f"{label}.role")
    if role not in ROLE_MODELS:
        _fail(f"{label}.role is not a model-governed role: {role}")
    if "model" in agent and agent["model"] != ROLE_MODELS[role][0]:
        _fail(f"{label}.model does not match the role model policy")
    if "reasoning" in agent and agent["reasoning"] != ROLE_MODELS[role][1]:
        _fail(f"{label}.reasoning does not match the role model policy")


def validate_route(
    route: Sequence[Any], *, has_sub_chats: bool = False, task_kind: str = "development"
) -> list[str]:
    if not isinstance(route, (list, tuple)) or not route:
        _fail("route must be a non-empty list")
    values = [_string(item, f"route[{index}]") for index, item in enumerate(route)]
    if task_kind == "status":
        if values != ["luna-manager", "status-read"]:
            _fail("only a pure status query may use the status-read route")
        return values
    if task_kind != "development":
        _fail("task_kind must be development or status")
    expected = ["luna-manager", "lead-gpt"]
    if has_sub_chats:
        expected.append("gpt-subchat")
    expected.extend(
        [
            "lead-synthesis",
            "luna-relay",
            "luna-max-worker",
            "luna-relay",
            "lead-gpt",
            "ci-acceptance",
        ]
    )
    if values != expected:
        _fail("real development tasks must use the complete Manager -> Lead -> Relay -> Worker -> Lead -> CI route")
    return values


def validate_retry_plan(retry: Mapping[str, Any]) -> None:
    maximum = _positive_int(retry.get("max_luna_attempts"), "retry.max_luna_attempts")
    if maximum != MAX_LUNA_ATTEMPTS:
        _fail("retry.max_luna_attempts must be exactly two")
    attempts = _non_negative_int(retry.get("luna_attempts"), "retry.luna_attempts", maximum=maximum)
    if retry.get("after_exhaustion") != "lead-gpt":
        _fail("retry.after_exhaustion must return to the Lead GPT")
    if retry.get("sol_gate") != "cricket-one-time":
        _fail("retry.sol_gate must require a one-time Cricket escalation")
    records = retry.get("attempts", [])
    if not isinstance(records, list) or len(records) > maximum:
        _fail("retry.attempts must contain at most two attempts")
    approach_hashes: set[str] = set()
    for index, record in enumerate(records):
        item = _object(record, f"retry.attempts[{index}]")
        number = _positive_int(item.get("attempt"), f"retry.attempts[{index}].attempt", maximum=maximum)
        if number != index + 1:
            _fail("retry attempts must be numbered consecutively")
        _string(item.get("approach"), f"retry.attempts[{index}].approach")
        approach_hash = _sha(item.get("approach_sha256"), f"retry.attempts[{index}].approach_sha256")
        if approach_hash in approach_hashes:
            _fail("the two Luna attempts must be substantively different")
        approach_hashes.add(approach_hash)
    if attempts != len(records):
        _fail("retry.luna_attempts must equal the number of recorded attempts")


def validate_rotation(rotation: Mapping[str, Any]) -> None:
    events = _non_negative_int(rotation.get("meaningful_events"), "rotation.meaningful_events")
    prepare_at = _positive_int(rotation.get("prepare_at"), "rotation.prepare_at")
    hard_at = _positive_int(rotation.get("hard_at"), "rotation.hard_at")
    if prepare_at != ROTATION_PREPARE_AT or hard_at != ROTATION_HARD_AT:
        _fail("rotation thresholds must be prepare=35 and hard=40 meaningful events")
    role_drift = rotation.get("role_drift", False)
    revision_drift = rotation.get("revision_drift", False)
    if not isinstance(role_drift, bool) or not isinstance(revision_drift, bool):
        _fail("rotation drift flags must be boolean")
    forced = events >= hard_at or role_drift or revision_drift
    state = rotation.get("state", "ACTIVE")
    if state not in {"ACTIVE", "PREPARE", "HARD_SWITCH"}:
        _fail("rotation.state is invalid")
    if events >= prepare_at and state == "ACTIVE" and not forced:
        _fail("rotation must be prepared at 35 meaningful events")
    if forced:
        if state != "HARD_SWITCH":
            _fail("role/revision drift and the 40-event threshold require HARD_SWITCH")
        if rotation.get("successor") != "fresh-chat":
            _fail("rotation successor must be a fresh chat")
        if rotation.get("codex_successor") != "fresh-chat":
            _fail("Codex successors must be fresh, not forks")
        if rotation.get("custom_gpt_successor") != "browser-new-chat":
            _fail("Custom-GPT successors must use the browser New Chat flow")
        if rotation.get("fork_allowed") is not False:
            _fail("forks are forbidden for a rotated generation")
        if rotation.get("old_generation") != "RETIRED":
            _fail("the old generation must be RETIRED after a hard switch")


def validate_task_capsule(capsule: Mapping[str, Any]) -> dict[str, Any]:
    data = _object(capsule, "capsule")
    _check_forbidden_keys(data)
    if data.get("schema") != CAPSULE_SCHEMA:
        _fail(f"capsule.schema must be {CAPSULE_SCHEMA}")
    task_id = _task_id(data.get("task_id"))
    task_kind = data.get("task_kind", "development")
    if task_kind not in {"development", "status"}:
        _fail("capsule.task_kind must be development or status")
    profile = _string(data.get("profile"), "capsule.profile")
    if profile not in {"admin", "patient"}:
        _fail("capsule.profile must be admin or patient")
    generation = _positive_int(data.get("generation"), "capsule.generation")
    revision = _positive_int(data.get("revision"), "capsule.revision")

    ticket = _object(data.get("ticket"), "capsule.ticket")
    _task_id(ticket.get("ticket_id"), "capsule.ticket.ticket_id")
    if ticket.get("duplicate_checked") is not True:
        _fail("Ticket Master must complete the duplicate check")
    if ticket.get("source") != "private-memory-gate":
        _fail("ticket.source must be private-memory-gate")

    lead = _object(data.get("lead"), "capsule.lead")
    validate_agent_identity(lead, "capsule.lead")
    if lead.get("role") != "lead-gpt" or lead.get("profile") != profile:
        _fail("capsule must contain exactly one Lead GPT for its selected profile")
    _chat_id(lead.get("chat_id"), "capsule.lead.chat_id")
    if lead.get("generation") != generation or lead.get("revision") != revision:
        _fail("lead generation/revision is stale")

    requirements = _object(data.get("requirements"), "capsule.requirements")
    _string(requirements.get("text"), "capsule.requirements.text")
    requirements_hash = _sha(requirements.get("sha256"), "capsule.requirements.sha256")

    _string_list(data.get("acceptance"), "capsule.acceptance", non_empty=True)
    scope = _object(data.get("scope"), "capsule.scope")
    allowed = _string_list(scope.get("allowed"), "capsule.scope.allowed", non_empty=True)
    forbidden = _string_list(scope.get("forbidden"), "capsule.scope.forbidden", non_empty=True)
    if {item.casefold() for item in allowed} & {item.casefold() for item in forbidden}:
        _fail("capsule scope allowed and forbidden entries must be disjoint")

    sub_chats = data.get("sub_chats")
    if sub_chats is None:
        sub_chats = []
    if not isinstance(sub_chats, list) or len(sub_chats) > MAX_SUB_CHATS:
        _fail("a ticket may have at most four GPT sub-chats")
    sub_chat_ids: set[str] = set()
    sub_chat_scopes: set[str] = set()
    for index, raw in enumerate(sub_chats):
        item = _object(raw, f"capsule.sub_chats[{index}]")
        validate_agent_identity(item, f"capsule.sub_chats[{index}]")
        if item.get("role") != "gpt-subchat":
            _fail("sub-chats must use the gpt-subchat role")
        if item.get("profile", profile) != profile:
            _fail("sub-chat profile must match the capsule profile")
        chat_id = _chat_id(item.get("chat_id"), f"capsule.sub_chats[{index}].chat_id")
        if chat_id in sub_chat_ids or chat_id == lead.get("chat_id"):
            _fail("Lead and sub-chat identifiers must be unique")
        sub_chat_ids.add(chat_id)
        scope_key = _string(item.get("scope"), f"capsule.sub_chats[{index}].scope").strip().casefold()
        if scope_key in sub_chat_scopes:
            _fail("sub-chat scopes must be pairwise disjoint")
        sub_chat_scopes.add(scope_key)
        if item.get("generation") != generation or item.get("revision") != revision:
            _fail("sub-chat generation/revision is stale")
        if item.get("status", "ACTIVE") not in {"ACTIVE", "RETIRED"}:
            _fail("sub-chat status must be ACTIVE or RETIRED")

    workers = data.get("workers")
    if not isinstance(workers, list):
        _fail("capsule.workers must be a list")
    worker_count = 0
    verifier_count = 0
    worker_ids: set[str] = set()
    worker_scopes: set[str] = set()
    for index, raw in enumerate(workers):
        item = _object(raw, f"capsule.workers[{index}]")
        role = _string(item.get("role"), f"capsule.workers[{index}].role")
        validate_agent_identity(item, f"capsule.workers[{index}]")
        if role == "luna-max-worker":
            worker_count += 1
        elif role == "verifier":
            verifier_count += 1
        else:
            _fail("workers may only be Luna-Max workers or one verifier")
        if worker_count > MAX_LUNA_WORKERS or verifier_count > MAX_VERIFIERS:
            _fail("worker limit is three Luna-Max workers plus one verifier")
        worker_id = _string(item.get("worker_id"), f"capsule.workers[{index}].worker_id")
        if worker_id in worker_ids:
            _fail("worker identifiers must be unique")
        worker_ids.add(worker_id)
        scope_key = _string(item.get("scope"), f"capsule.workers[{index}].scope").casefold()
        if scope_key in worker_scopes:
            _fail("worker scopes must be pairwise disjoint")
        worker_scopes.add(scope_key)
        if item.get("generation") != generation or item.get("revision") != revision:
            _fail("worker generation/revision is stale")

    if task_kind == "development" and worker_count == 0:
        _fail("a development task must have at least one Luna-Max worker")

    validate_route(
        data.get("route"),
        has_sub_chats=bool(sub_chats),
        task_kind=task_kind,
    )
    validate_retry_plan(_object(data.get("retry"), "capsule.retry"))
    validate_rotation(_object(data.get("rotation"), "capsule.rotation"))
    locks = _object(data.get("locks"), "capsule.locks")
    for key in ("merge", "release", "deploy", "ticket_close", "scope_expansion"):
        if locks.get(key) is not True:
            _fail(f"capsule.locks.{key} must remain locked")

    if task_kind == "status" and (sub_chats or workers):
        _fail("a pure status query cannot create GPT or worker work")
    return copy.deepcopy(data)


def handoff_hash_for(event: Mapping[str, Any]) -> str:
    body = {key: value for key, value in event.items() if key != "handoff_hash"}
    encoded = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def validate_handoff_event(event: Mapping[str, Any], capsule: Mapping[str, Any]) -> dict[str, Any]:
    data = _object(event, "handoff")
    validated_capsule = validate_task_capsule(capsule)
    _check_forbidden_keys(data)
    if data.get("schema") != HANDOFF_SCHEMA:
        _fail(f"handoff.schema must be {HANDOFF_SCHEMA}")
    _task_id(data.get("task_id"), "handoff.task_id")
    if data["task_id"] != validated_capsule["task_id"]:
        _fail("handoff task_id does not match the capsule")
    _positive_int(data.get("sequence"), "handoff.sequence")
    _string(data.get("event_id"), "handoff.event_id")
    _string(data.get("event_type"), "handoff.event_type")
    _positive_int(data.get("generation"), "handoff.generation")
    _positive_int(data.get("revision"), "handoff.revision")
    if data["generation"] != validated_capsule["generation"] or data["revision"] != validated_capsule["revision"]:
        _fail("stale_generation: handoff generation/revision does not match the capsule")
    from_role = _string(data.get("from_role"), "handoff.from_role")
    to_role = _string(data.get("to_role"), "handoff.to_role")
    if (from_role, to_role) not in ALLOWED_TRANSITIONS:
        _fail(f"handoff transition is not allowed: {from_role} -> {to_role}")
    _sha(data.get("requirements_sha256"), "handoff.requirements_sha256")
    if data["requirements_sha256"] != validated_capsule["requirements"]["sha256"]:
        _fail("requirements_changed: handoff requirements hash differs from the capsule")
    if (from_role == "luna-relay" or to_role == "luna-relay") and data.get("transport_only") is not True:
        _fail("Relay handoffs must declare transport_only=true")
    if data.get("requirement_delta", []) not in ([], None):
        _fail("Relay may not carry a requirement delta")
    _string(data.get("summary"), "handoff.summary")
    if not isinstance(data.get("evidence"), list):
        _fail("handoff.evidence must be a list")
    if data.get("append_only") is not True:
        _fail("coordination events are append-only")
    expected_hash = handoff_hash_for(data)
    if data.get("handoff_hash") != expected_hash:
        _fail("handoff_hash does not match the visible event")
    return copy.deepcopy(data)


RESULT_STATUSES = {"PASS", "FAIL", "BLOCKED", "PENDING", "NEEDS_LEAD", "NEEDS_SOL"}


def validate_result(result: Mapping[str, Any], capsule: Mapping[str, Any]) -> dict[str, Any]:
    data = _object(result, "result")
    validated_capsule = validate_task_capsule(capsule)
    _check_forbidden_keys(data)
    if data.get("schema") != RESULT_SCHEMA:
        _fail(f"result.schema must be {RESULT_SCHEMA}")
    _task_id(data.get("task_id"), "result.task_id")
    if data["task_id"] != validated_capsule["task_id"]:
        _fail("result task_id does not match the capsule")
    role = _string(data.get("role"), "result.role")
    if role not in KNOWN_ROLES:
        _fail("result.role is unknown")
    _positive_int(data.get("generation"), "result.generation")
    _positive_int(data.get("revision"), "result.revision")
    if data["generation"] != validated_capsule["generation"] or data["revision"] != validated_capsule["revision"]:
        _fail("stale_generation: result generation/revision does not match the capsule")
    _sha(data.get("requirements_sha256"), "result.requirements_sha256")
    if data["requirements_sha256"] != validated_capsule["requirements"]["sha256"]:
        _fail("requirements_changed: result requirements hash differs from the capsule")
    _positive_int(data.get("attempt"), "result.attempt", maximum=MAX_LUNA_ATTEMPTS)
    status = _string(data.get("status"), "result.status")
    if status not in RESULT_STATUSES:
        _fail("result.status is not a supported visible result state")
    _string(data.get("scope"), "result.scope")
    _string(data.get("summary"), "result.summary")
    if not isinstance(data.get("evidence"), list):
        _fail("result.evidence must be a list")
    _string(data.get("next_action"), "result.next_action")
    if status in {"BLOCKED", "NEEDS_LEAD", "NEEDS_SOL"}:
        blocker = _object(data.get("blocker"), "result.blocker")
        if blocker.get("level") not in {"L0", "L1", "L2", "L3"}:
            _fail("blocker.level must be L0, L1, L2 or L3")
        _string(blocker.get("code"), "result.blocker.code")
        _string(blocker.get("owner"), "result.blocker.owner")
        _string(blocker.get("next_action"), "result.blocker.next_action")
    if status == "NEEDS_SOL":
        if role not in {"lead-gpt", "luna-manager"}:
            _fail("only the Lead or Manager may mark NEEDS_SOL")
        if data.get("luna_attempts") != MAX_LUNA_ATTEMPTS:
            _fail("NEEDS_SOL requires two Luna attempts")
        if data.get("cricket_escalated") is not True:
            _fail("NEEDS_SOL requires visible Cricket escalation")
        if blocker.get("level") != "L3":
            _fail("NEEDS_SOL requires an L3 blocker")
    if data.get("completion") is True:
        if role not in {"lead-gpt", "ci-acceptance"}:
            _fail("only Lead/CI may emit a completion result")
        if data.get("ci_green") is not True or data.get("lead_accepted") is not True:
            _fail("completion requires green CI and Lead acceptance")
        if data["next_action"] != "coordination-completion":
            _fail("completion must use the Coordination completion event")
    return copy.deepcopy(data)


def validate_browser_relay_batch(batch: Mapping[str, Any], capsule: Mapping[str, Any]) -> dict[str, Any]:
    data = _object(batch, "browser_relay")
    validated_capsule = validate_task_capsule(capsule)
    _check_forbidden_keys(data)
    if data.get("schema") != BROWSER_RELAY_SCHEMA:
        _fail(f"browser_relay.schema must be {BROWSER_RELAY_SCHEMA}")
    if data.get("task_id") != validated_capsule["task_id"]:
        _fail("browser relay task_id does not match the capsule")
    if data.get("generation") != validated_capsule["generation"] or data.get("revision") != validated_capsule["revision"]:
        _fail("stale_generation: browser relay identity does not match the capsule")
    chats = data.get("chat_ids")
    if not isinstance(chats, list) or not 1 <= len(chats) <= MAX_SUB_CHATS:
        _fail("browser relay supports one to four GPT sub-chats")
    normalized_chats = [_chat_id(item, f"browser_relay.chat_ids[{index}]") for index, item in enumerate(chats)]
    if len(set(normalized_chats)) != len(normalized_chats):
        _fail("browser relay chat IDs must be unique")
    capsule_chat_ids = {
        item["chat_id"]
        for item in validated_capsule["sub_chats"]
        if isinstance(item, Mapping) and isinstance(item.get("chat_id"), str)
    }
    if not set(normalized_chats).issubset(capsule_chat_ids):
        _fail("browser relay may only target sub-chats in the Task Capsule")
    if data.get("dispatch_mode") != "single-run":
        _fail("Browser Relay must send the batch in one run")
    if data.get("wait_for_completion") is not True or data.get("status_prompts") != 0:
        _fail("Browser Relay must wait without status prompts")
    if data.get("timeout_seconds") != BROWSER_TIMEOUT_SECONDS:
        _fail("Browser Relay timeout must be 30 minutes")
    if data.get("fresh_retry_limit") != MAX_BROWSER_FRESH_RETRIES:
        _fail("Browser Relay allows at most one fresh retry")
    retries_used = _non_negative_int(data.get("retries_used", 0), "browser_relay.retries_used", maximum=MAX_BROWSER_FRESH_RETRIES)
    if data.get("completion_channel") != "coordination-action":
        _fail("completion and blockers must use the existing Coordination Action")
    if data.get("fallback") != "browser-relay":
        _fail("browser fallback must remain a transport fallback")
    if retries_used and data.get("retry_generation") != validated_capsule["generation"] + 1:
        _fail("a fresh Browser Relay retry must use a new generation")
    return copy.deepcopy(data)


def validate_ticket_action(action: Mapping[str, Any]) -> dict[str, Any]:
    data = _object(action, "ticket_action")
    _check_forbidden_keys(data)
    if data.get("role") != "ticket-master":
        _fail("only Ticket Master may use the ticket action")
    if data.get("operation") not in {"read", "create"}:
        _fail("Ticket Master may only read or create")
    if data.get("duplicate_checked") is not True:
        _fail("Ticket Master must run the duplicate check first")
    if data.get("source") != "private-memory-gate":
        _fail("tickets must use the private Memory Gate")
    for key in ("program", "close", "invent"):
        if data.get(key) is not False:
            _fail(f"Ticket Master is not allowed to {key}")
    return copy.deepcopy(data)


def validate_sol_request(request: Mapping[str, Any]) -> dict[str, Any]:
    data = _object(request, "sol_request")
    _check_forbidden_keys(data)
    if data.get("role") != "sol-endboss":
        _fail("only the Sol Endboss role may use a Sol request")
    if data.get("model") not in (None, ROLE_MODELS["sol-endboss"][0]):
        _fail("Sol request uses the Sol model only")
    if data.get("reasoning") not in (None, ROLE_MODELS["sol-endboss"][1]):
        _fail("Sol request uses Ultra reasoning only")
    state = data.get("state", "SLEEPING")
    if state not in {"SLEEPING", "ESCALATED"}:
        _fail("Sol state must be SLEEPING or an explicitly escalated state")
    action = re.sub(
        r"[\s-]+", "_", _string(data.get("requested_action"), "sol_request.requested_action").strip().lower()
    )
    if action in FORBIDDEN_SOL_ACTIONS:
        _fail("Sol may not code, repo-analyse, debug, test, repair or micromanage")
    escalation = data.get("cricket_escalation")
    approved_once = isinstance(escalation, Mapping) and escalation.get("approved_once") is True
    internal_agents = data.get("internal_sol_agents", False)
    if not isinstance(internal_agents, bool):
        _fail("sol_request.internal_sol_agents must be boolean")
    if internal_agents and not approved_once:
        _fail("internal Sol agents require a one-time Cricket escalation")
    if state == "ESCALATED":
        if not approved_once:
            _fail("an active Sol state requires one-time Cricket escalation")
        if escalation.get("single_use") is not True:
            _fail("Cricket escalation must be explicitly single-use")
        _string(escalation.get("approval_id"), "sol_request.cricket_escalation.approval_id")
        if action not in {"review_l3_blocker", "endboss_decision"}:
            _fail("escalated Sol may only review an L3 blocker or state an endboss decision")
    return copy.deepcopy(data)


def validate_cricket_event(event: Mapping[str, Any]) -> dict[str, Any]:
    data = _object(event, "cricket_event")
    _check_forbidden_keys(data)
    if data.get("schema") != HANDOFF_SCHEMA:
        _fail("Cricket facts use the handoff-v2 visible event envelope")
    if data.get("from_role") != "cricket":
        _fail("Cricket event must be emitted by Cricket")
    if data.get("level") not in {"L0", "L1", "L2", "L3"}:
        _fail("Cricket level must be L0-L3")
    if data.get("classification") not in {"technical-enforcement", "policy-only", "proxy"}:
        _fail("Cricket must distinguish enforcement, policy-only and proxy")
    if not isinstance(data.get("evidence"), list) or not data["evidence"]:
        _fail("Cricket observations require visible evidence")
    action = data.get("requested_action")
    if action is not None:
        normalized_action = re.sub(r"[\s-]+", "_", str(action).strip().lower())
        if normalized_action in FORBIDDEN_SOL_ACTIONS:
            _fail("Cricket observes and escalates; it does not solve project problems")
    return copy.deepcopy(data)


def synthetic_capsule(*, with_sub_chats: bool = False) -> dict[str, Any]:
    sub_chats = []
    route = ["luna-manager", "lead-gpt"]
    if with_sub_chats:
        sub_chats = [
            {
                "role": "gpt-subchat",
                "chat_id": "kgg-sub-example-1",
                "scope": "contract-reading",
                "generation": 1,
                "revision": 1,
            },
            {
                "role": "gpt-subchat",
                "chat_id": "kgg-sub-example-2",
                "scope": "contract-safety",
                "generation": 1,
                "revision": 1,
            },
        ]
        route.append("gpt-subchat")
    route.extend(
        [
            "lead-synthesis",
            "luna-relay",
            "luna-max-worker",
            "luna-relay",
            "lead-gpt",
            "ci-acceptance",
        ]
    )
    return {
        "schema": CAPSULE_SCHEMA,
        "task_id": "kgg-brain-example-001",
        "ticket": {
            "ticket_id": "kgg-ticket-example-001",
            "duplicate_checked": True,
            "source": "private-memory-gate",
        },
        "profile": "admin",
        "generation": 1,
        "revision": 1,
        "lead": {
            "role": "lead-gpt",
            "profile": "admin",
            "chat_id": "kgg-admin-lead-example",
            "generation": 1,
            "revision": 1,
        },
        "requirements": {
            "text": "Only the KGG coordination contract; no product code.",
            "sha256": "a" * 64,
        },
        "acceptance": [
            "The complete route is used for every development task.",
            "The requirements hash is unchanged in every handoff.",
        ],
        "scope": {
            "allowed": ["playbooks", "actions", "coordination", "synthetic tests"],
            "forbidden": ["patient data", "product code", "releases", "live gates"],
        },
        "sub_chats": sub_chats,
        "workers": [
            {
                "worker_id": "worker-contract",
                "role": "luna-max-worker",
                "scope": "contract implementation",
                "generation": 1,
                "revision": 1,
            },
            {
                "worker_id": "verifier-contract",
                "role": "verifier",
                "scope": "contract verification",
                "generation": 1,
                "revision": 1,
            },
        ],
        "route": route,
        "retry": {
            "luna_attempts": 0,
            "max_luna_attempts": MAX_LUNA_ATTEMPTS,
            "after_exhaustion": "lead-gpt",
            "sol_gate": "cricket-one-time",
        },
        "rotation": {
            "meaningful_events": 0,
            "prepare_at": ROTATION_PREPARE_AT,
            "hard_at": ROTATION_HARD_AT,
            "role_drift": False,
            "revision_drift": False,
            "state": "ACTIVE",
            "successor": "fresh-chat",
            "codex_successor": "fresh-chat",
            "custom_gpt_successor": "browser-new-chat",
            "fork_allowed": False,
            "old_generation": "ACTIVE",
        },
        "locks": {
            "merge": True,
            "release": True,
            "deploy": True,
            "ticket_close": True,
            "scope_expansion": True,
        },
    }


def _expect_failure(name: str, callback: Any, expected: str) -> None:
    try:
        callback()
    except ContractError as exc:
        if expected not in str(exc):
            _fail(f"self-test {name} failed with unexpected error: {exc}")
        return
    _fail(f"self-test {name} unexpectedly passed")


def self_test() -> None:
    capsule = synthetic_capsule()
    validate_task_capsule(capsule)
    validate_route(["luna-manager", "status-read"], task_kind="status")
    with_sub = synthetic_capsule(with_sub_chats=True)
    validate_task_capsule(with_sub)

    too_many_subs = copy.deepcopy(capsule)
    too_many_subs["sub_chats"] = [
        {
            "role": "gpt-subchat",
            "chat_id": f"kgg-sub-example-{index}",
            "scope": f"scope-{index}",
            "generation": 1,
            "revision": 1,
        }
        for index in range(5)
    ]
    too_many_subs["route"] = [
        "luna-manager",
        "lead-gpt",
        "gpt-subchat",
        "lead-synthesis",
        "luna-relay",
        "luna-max-worker",
        "luna-relay",
        "lead-gpt",
        "ci-acceptance",
    ]
    _expect_failure("sub-chat-limit", lambda: validate_task_capsule(too_many_subs), "at most four")

    overlap = copy.deepcopy(capsule)
    overlap["workers"][1]["scope"] = overlap["workers"][0]["scope"]
    _expect_failure("disjoint-workers", lambda: validate_task_capsule(overlap), "pairwise disjoint")

    duplicate_retry = copy.deepcopy(capsule)
    duplicate_retry["retry"] = {
        "luna_attempts": 2,
        "max_luna_attempts": 2,
        "after_exhaustion": "lead-gpt",
        "sol_gate": "cricket-one-time",
        "attempts": [
            {"attempt": 1, "approach": "A", "approach_sha256": "b" * 64},
            {"attempt": 2, "approach": "B", "approach_sha256": "b" * 64},
        ],
    }
    _expect_failure("different-retries", lambda: validate_task_capsule(duplicate_retry), "substantively different")

    handoff = {
        "schema": HANDOFF_SCHEMA,
        "event_id": "kgg-event-example-001",
        "sequence": 1,
        "event_type": "worker_result",
        "task_id": capsule["task_id"],
        "generation": 1,
        "revision": 1,
        "from_role": "luna-max-worker",
        "to_role": "luna-relay",
        "requirements_sha256": capsule["requirements"]["sha256"],
        "transport_only": True,
        "summary": "The worker returned its bounded result.",
        "evidence": [{"kind": "test", "name": "brain-relay-selftest", "status": "PASS"}],
        "append_only": True,
    }
    handoff["handoff_hash"] = handoff_hash_for(handoff)
    validate_handoff_event(handoff, capsule)
    stale = copy.deepcopy(handoff)
    stale["generation"] = 2
    stale["handoff_hash"] = handoff_hash_for(stale)
    _expect_failure("stale-generation", lambda: validate_handoff_event(stale, capsule), "stale_generation")
    changed = copy.deepcopy(handoff)
    changed["requirement_delta"] = ["changed"]
    changed["handoff_hash"] = handoff_hash_for(changed)
    _expect_failure("relay-no-mutation", lambda: validate_handoff_event(changed, capsule), "requirement delta")

    browser_capsule = synthetic_capsule(with_sub_chats=True)
    browser = {
        "schema": BROWSER_RELAY_SCHEMA,
        "task_id": browser_capsule["task_id"],
        "generation": 1,
        "revision": 1,
        "chat_ids": ["kgg-sub-example-1", "kgg-sub-example-2"],
        "dispatch_mode": "single-run",
        "wait_for_completion": True,
        "status_prompts": 0,
        "timeout_seconds": BROWSER_TIMEOUT_SECONDS,
        "fresh_retry_limit": 1,
        "retries_used": 0,
        "completion_channel": "coordination-action",
        "fallback": "browser-relay",
    }
    validate_browser_relay_batch(browser, browser_capsule)
    too_many_browser_chats = copy.deepcopy(browser)
    too_many_browser_chats["chat_ids"] = [f"kgg-sub-example-{index}" for index in range(5)]
    _expect_failure("browser-limit", lambda: validate_browser_relay_batch(too_many_browser_chats, browser_capsule), "one to four")
    no_status_prompt = copy.deepcopy(browser)
    no_status_prompt["status_prompts"] = 1
    _expect_failure("browser-no-status-prompt", lambda: validate_browser_relay_batch(no_status_prompt, browser_capsule), "without status prompts")

    ticket = {
        "role": "ticket-master",
        "operation": "create",
        "duplicate_checked": True,
        "source": "private-memory-gate",
        "program": False,
        "close": False,
        "invent": False,
    }
    validate_ticket_action(ticket)
    bad_ticket = copy.deepcopy(ticket)
    bad_ticket["close"] = True
    _expect_failure("ticket-lock", lambda: validate_ticket_action(bad_ticket), "not allowed to close")

    validate_sol_request(
        {
            "role": "sol-endboss",
            "state": "SLEEPING",
            "requested_action": "observe",
            "internal_sol_agents": False,
        }
    )
    _expect_failure(
        "sol-code-guard",
        lambda: validate_sol_request(
            {"role": "sol-endboss", "state": "SLEEPING", "requested_action": "code"}
        ),
        "may not code",
    )
    _expect_failure(
        "sol-agent-guard",
        lambda: validate_sol_request(
            {
                "role": "sol-endboss",
                "state": "SLEEPING",
                "requested_action": "observe",
                "internal_sol_agents": True,
            }
        ),
        "one-time Cricket",
    )
    validate_sol_request(
        {
            "role": "sol-endboss",
            "state": "ESCALATED",
            "requested_action": "review_l3_blocker",
            "internal_sol_agents": True,
            "cricket_escalation": {
                "approved_once": True,
                "single_use": True,
                "approval_id": "cricket-l3-example-001",
            },
        }
    )

    validate_cricket_event(
        {
            "schema": HANDOFF_SCHEMA,
            "event_id": "cricket-example-001",
            "sequence": 1,
            "event_type": "cricket_observation",
            "from_role": "cricket",
            "to_role": "luna-manager",
            "level": "L0",
            "classification": "proxy",
            "evidence": [{"kind": "visible-state", "status": "PASS"}],
        }
    )

    needs_sol = {
        "schema": RESULT_SCHEMA,
        "task_id": capsule["task_id"],
        "generation": 1,
        "revision": 1,
        "role": "lead-gpt",
        "status": "NEEDS_SOL",
        "scope": "contract decision",
        "attempt": 2,
        "requirements_sha256": capsule["requirements"]["sha256"],
        "summary": "Two different Luna approaches need an endboss decision.",
        "evidence": [{"kind": "cricket", "status": "PASS"}],
        "next_action": "coordination-escalation",
        "blocker": {
            "level": "L3",
            "code": "luna-attempts-exhausted",
            "owner": "lead-gpt",
            "next_action": "review_l3_blocker",
        },
        "luna_attempts": 2,
        "cricket_escalated": True,
    }
    validate_result(needs_sol, capsule)
    bad_result = copy.deepcopy(needs_sol)
    bad_result["generation"] = 2
    _expect_failure("result-stale-generation", lambda: validate_result(bad_result, capsule), "stale_generation")

    print(
        json.dumps(
            {
                "status": "PASS",
                "contract": CAPSULE_SCHEMA,
                "maxSubChats": MAX_SUB_CHATS,
                "maxLunaWorkers": MAX_LUNA_WORKERS,
                "maxLunaAttempts": MAX_LUNA_ATTEMPTS,
                "rotation": {"prepareAt": ROTATION_PREPARE_AT, "hardAt": ROTATION_HARD_AT},
                "browserTimeoutSeconds": BROWSER_TIMEOUT_SECONDS,
            },
            ensure_ascii=False,
        )
    )


def load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ContractError(f"cannot read JSON {path}: {exc}") from exc
    return _object(value, str(path))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true", help="run synthetic contract tests")
    parser.add_argument("--capsule", type=Path, help="validate one Task Capsule JSON")
    parser.add_argument("--handoff", type=Path, help="validate a Handoff JSON with --capsule")
    parser.add_argument("--result", type=Path, help="validate a Result JSON with --capsule")
    parser.add_argument("--browser-relay", type=Path, help="validate a Browser Relay JSON with --capsule")
    args = parser.parse_args()
    try:
        if args.self_test:
            self_test()
            return 0
        if not args.capsule:
            parser.error("one of --self-test or --capsule is required")
        capsule = validate_task_capsule(load_json(args.capsule))
        if args.handoff:
            validate_handoff_event(load_json(args.handoff), capsule)
        if args.result:
            validate_result(load_json(args.result), capsule)
        if args.browser_relay:
            validate_browser_relay_batch(load_json(args.browser_relay), capsule)
        print(json.dumps({"status": "PASS", "task_id": capsule["task_id"]}, ensure_ascii=False))
        return 0
    except ContractError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
