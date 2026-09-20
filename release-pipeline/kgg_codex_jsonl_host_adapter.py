#!/usr/bin/env python3
"""Normalize trusted ``codex exec --json`` events for the KGG contract.
This module is deliberately a collector, not a comparator or a second
validator.  It accepts only the documented JSONL lifecycle, binds identity
outside the model stream, and exposes partial observations explicitly.  A
partial observation is converted to the existing KGG failure envelope; no
missing value is represented by a fabricated zero.
"""
from __future__ import annotations
import hashlib
import json
from typing import Any, Iterable, Mapping
import kgg_gpt_measurement as measurement
EVENT_TYPES = frozenset(
    {
        "thread.started",
        "turn.started",
        "turn.completed",
        "turn.failed",
        "item.started",
        "item.updated",
        "item.completed",
        "error",
    }
)
MEASURED_ITEM_TYPES = frozenset({"agent_message", "command_execution", "file_change", "mcp_tool_call"})
# These are valid codex exec --json items, but KGG has no authoritative
# comparator field for their contents.  They must pass through the lifecycle
# without becoming actions, reads, quality, or safety evidence.
RECOGNIZED_UNMEASURED_ITEM_TYPES = frozenset({"reasoning", "web_search", "todo_list", "error"})
ITEM_TYPES = MEASURED_ITEM_TYPES | RECOGNIZED_UNMEASURED_ITEM_TYPES
COMPLETION_ONLY_ITEM_TYPES = frozenset({"agent_message", "reasoning", "error", "mcp_tool_call", "command_execution", "file_change", "web_search", "todo_list"})
_READ_OPERATIONS = frozenset({"get_current_state", "get_ticket_state", "get_test_evidence", "get_session_status"})
class AdapterError(ValueError):
    """Raised for malformed or unverifiable host evidence."""
def _text(value: Any, label: str, *, allow_empty: bool = False, allow_newline: bool = False) -> str:
    if not isinstance(value, str) or (not value and not allow_empty) or (not allow_newline and ("\n" in value or "\r" in value)):
        raise AdapterError(f"{label}_invalid")
    return value
def _object(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise AdapterError(f"{label}_invalid")
    return value
def _item(event: Mapping[str, Any], index: int) -> Mapping[str, Any]:
    item = _object(event.get("item"), f"event[{index}].item")
    _text(item.get("id"), f"event[{index}].item.id")
    item_type = _text(item.get("type"), f"event[{index}].item.type")
    if item_type not in ITEM_TYPES:
        raise AdapterError(f"unsupported_item_type:{item_type}")
    if item_type == "agent_message":
        _text(item.get("text", ""), f"event[{index}].item.text", allow_empty=True, allow_newline=True)
    elif item_type == "command_execution":
        _text(item.get("command", ""), f"event[{index}].item.command", allow_empty=True)
        if "exit_code" in item and item["exit_code"] is not None and not isinstance(item["exit_code"], int):
            raise AdapterError(f"event[{index}].item.exit_code_invalid")
    elif item_type == "file_change":
        changes = item.get("changes")
        if not isinstance(changes, list):
            raise AdapterError(f"event[{index}].item.changes_invalid")
        for change in changes:
            change_obj = _object(change, f"event[{index}].item.change")
            _text(change_obj.get("path"), f"event[{index}].item.change.path")
            _text(change_obj.get("kind"), f"event[{index}].item.change.kind")
    elif item_type == "mcp_tool_call":
        _text(item.get("server"), f"event[{index}].item.server")
        _text(item.get("tool"), f"event[{index}].item.tool")
    return item
def _json_lines(source: str | Iterable[str]) -> list[Mapping[str, Any]]:
    lines = source.splitlines() if isinstance(source, str) else list(source)
    events: list[Mapping[str, Any]] = []
    for index, line in enumerate(lines):
        if not isinstance(line, str) or not line.strip():
            continue
        try:
            decoded = json.loads(line)
        except json.JSONDecodeError as exc:
            raise AdapterError(f"malformed_jsonl:{index}") from exc
        event = _object(decoded, f"event[{index}]")
        event_type = _text(event.get("type"), f"event[{index}].type")
        if event_type not in EVENT_TYPES:
            raise AdapterError(f"unsupported_event_type:{event_type}")
        events.append(event)
    if not events:
        raise AdapterError("empty_jsonl")
    return events
def parse_jsonl(
    source: str | Iterable[str],
    *,
    expected_thread_id: str | None = None,
    scenario_id: str | None = None,
    base_sha: str | None = None,
    surface: str = "codex_plugin",
    runtime_ms: int | None = None,
) -> dict[str, Any]:
    """Parse one parent-host JSONL stream into bounded observations.
    ``scenario_id`` and ``base_sha`` are external bindings and are never
    inferred from model output.  ``runtime_ms`` is accepted only from an
    outer parent timer, never from usage metadata in the stream.
    """
    if scenario_id is not None:
        _text(scenario_id, "scenario_id")
    if base_sha is not None:
        if not isinstance(base_sha, str) or len(base_sha) != 40 or any(c not in "0123456789abcdef" for c in base_sha):
            raise AdapterError("base_sha_invalid")
    if surface not in {"production", "candidate", "codex_plugin"}:
        raise AdapterError("surface_invalid")
    if runtime_ms is not None and (isinstance(runtime_ms, bool) or not isinstance(runtime_ms, int) or runtime_ms < 0):
        raise AdapterError("runtime_ms_invalid")
    events = _json_lines(source)
    thread_id: str | None = None
    turn_id: str | None = None
    turn_started = False
    terminal: str | None = None
    stream_error_seen = False
    lifecycle: list[dict[str, Any]] = []
    items: dict[str, dict[str, Any]] = {}
    completed_items: set[str] = set()
    action_events: list[dict[str, Any]] = []
    commands: list[dict[str, Any]] = []
    file_changes: list[dict[str, Any]] = []
    messages: list[str] = []
    for index, event in enumerate(events):
        event_type = event["type"]
        if terminal is not None:
            raise AdapterError("event_after_terminal")
        if event_type == "thread.started":
            if thread_id is not None:
                raise AdapterError("duplicate_thread_started")
            thread_id = _text(event.get("thread_id"), f"event[{index}].thread_id")
            if expected_thread_id is not None and thread_id != expected_thread_id:
                raise AdapterError("thread_identity_mismatch")
            lifecycle.append({"operation": "thread_started", "thread_id": thread_id})
            continue
        if thread_id is None:
            raise AdapterError("thread_started_missing")
        if event_type == "turn.started":
            if turn_started:
                raise AdapterError("duplicate_turn_started")
            turn_started = True
            if event.get("turn_id") is not None:
                turn_id = _text(event.get("turn_id"), f"event[{index}].turn_id")
            lifecycle.append({"operation": "turn_started", "turn_id": turn_id})
            continue
        if not turn_started:
            raise AdapterError("turn_started_missing")
        if event_type in {"item.started", "item.updated", "item.completed"}:
            item = _item(event, index)
            item_id = item["id"]
            if event_type == "item.started":
                if item_id in items:
                    raise AdapterError("duplicate_item_started")
                items[item_id] = dict(item)
            elif item_id not in items:
                if event_type != "item.completed" or item["type"] not in COMPLETION_ONLY_ITEM_TYPES:
                    raise AdapterError("item_update_before_start")
                if item_id in completed_items:
                    raise AdapterError("duplicate_item_completed")
            elif item_id in completed_items:
                raise AdapterError("item_update_after_complete")
            else:
                if item["type"] != items[item_id]["type"]:
                    raise AdapterError("item_type_changed")
                items[item_id] = dict(item)
            if event_type == "item.completed":
                completed_items.add(item_id)
                item_type = item["type"]
                if item_type == "agent_message" and item.get("text"):
                    messages.append(item["text"])
                elif item_type == "command_execution":
                    commands.append(dict(item))
                elif item_type == "file_change":
                    file_changes.extend(dict(change) for change in item["changes"])
                elif item_type == "mcp_tool_call":
                    action_events.append({
                        "operation": item["tool"],
                        "server": item["server"],
                        "item_id": item_id,
                        "status": item.get("status", "UNKNOWN"),
                    })
            continue
        if event_type == "turn.completed":
            if terminal is not None:
                raise AdapterError("duplicate_turn_terminal")
            if stream_error_seen:
                raise AdapterError("turn_completed_after_stream_error")
            if event.get("turn_id") not in {None, turn_id}:
                raise AdapterError("turn_identity_mismatch")
            terminal = "PASS"
            lifecycle.append({"operation": "turn_completed", "turn_id": turn_id})
            continue
        if event_type == "error":
            if stream_error_seen:
                raise AdapterError("duplicate_stream_error")
            stream_error_seen = True
            lifecycle.append({"operation": "stream_error"})
            continue
        if event_type == "turn.failed":
            terminal = "FAIL"
            lifecycle.append({"operation": "turn_failed", "turn_id": turn_id})
            continue
        raise AdapterError(f"unsupported_event_type:{event_type}")
    if thread_id is None:
        raise AdapterError("thread_started_missing")
    if not turn_started:
        raise AdapterError("turn_started_missing")
    if terminal is None:
        raise AdapterError("turn_terminal_missing")
    if any(item_id not in completed_items for item_id in items):
        raise AdapterError("item_completion_missing")
    normalized_actions = list(action_events)
    observed_fields = {
        "status": True,
        "action_calls": bool(action_events),
        "runtime_ms": runtime_ms is not None,
        "repository_writes": bool(file_changes),
        "result_output": bool(messages),
        "reads": bool([event for event in normalized_actions if event["operation"] in _READ_OPERATIONS]),
    }
    missing_fields = [
        "context_items",
        "clarifying_questions",
        "dispatches",
        "duplicate_dispatches",
        "result_quality",
        "root_cause_quality",
        "secret_leaks",
        "patient_data_leaks",
        "source_regressions",
        "gate_regressions",
        "action_regressions",
    ]
    if not any(event["operation"] in _READ_OPERATIONS for event in normalized_actions):
        missing_fields.insert(0, "reads")
    if not action_events:
        missing_fields.append("action_calls")
    if runtime_ms is None:
        missing_fields.append("runtime_ms")
    if not file_changes:
        missing_fields.append("repository_writes")
    return {
        "thread_id": thread_id,
        "turn_id": turn_id,
        "surface": surface,
        "scenario_id": scenario_id,
        "base_sha": base_sha,
        "status": terminal,
        "runtime_ms": runtime_ms,
        "lifecycle_events": lifecycle,
        "action_events": normalized_actions,
        "command_executions": commands,
        "file_changes": file_changes,
        "final_output": messages[-1] if messages else None,
        "final_output_sha256": hashlib.sha256(messages[-1].encode("utf-8")).hexdigest() if messages else None,
        "observed_fields": observed_fields,
        "missing_fields": list(dict.fromkeys(missing_fields)),
    }
def build_measurement_envelope(
    observation: Mapping[str, Any],
    *,
    request_id: str,
    scenario_id: str,
    base_sha: str,
    captured_at: str | None = None,
    trusted_payload: Mapping[str, Any] | None = None,
    evidence_refs: list[Mapping[str, Any]] | None = None,
    field_evidence_ids: Mapping[str, list[str]] | None = None,
) -> dict[str, Any]:
    """Reuse the KGG builder; incomplete observations remain FAIL-only.
    A PASS is possible only when a caller supplies the complete payload and
    independent evidence refs.  The JSONL parser itself never scores quality
    or synthesizes absent fields.
    """
    if not isinstance(observation, Mapping):
        raise AdapterError("observation_invalid")
    missing = list(dict.fromkeys(observation.get("missing_fields", [])))
    surface = observation.get("surface", "codex_plugin")
    if trusted_payload is None or evidence_refs is None or missing:
        return measurement.build_failure_envelope(
            request_id=request_id,
            surface=surface,
            scenario_id=scenario_id,
            base_sha=base_sha,
            missing_fields=missing or list(measurement.PAYLOAD_FIELDS),
            captured_at=captured_at,
        )
    return measurement.build_complete_envelope(
        request_id=request_id,
        surface=surface,
        scenario_id=scenario_id,
        base_sha=base_sha,
        captured_at=captured_at or measurement._now(),
        payload=trusted_payload,
        evidence_refs=evidence_refs,
        field_evidence_ids=field_evidence_ids,
    )
