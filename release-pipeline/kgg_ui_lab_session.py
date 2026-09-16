#!/usr/bin/env python3
"""Local runner, lease, event and semantic Quick-Flow stores.

The stores are intentionally in-memory and side-effect free.  Persistence and
browser adapters can be added later behind these contracts without changing
the safety rules.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import re
from typing import Any, Callable, Mapping

import kgg_ui_lab_contract as contract


ContractError = contract.ContractError
_FLOW_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{2,63}$")
_SAFE_TEXT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._-]{0,79}$")
_FLOW_OPERATIONS = frozenset({"read_state", "click", "tap", "type", "scroll", "reload", "back", "wait", "capture_screenshot"})
_TERMINAL = frozenset({"completed", "failed", "expired", "cancelled"})
_ALLOWED_TRANSITIONS = {
    "created": frozenset({"ready", "failed", "cancelled"}),
    "ready": frozenset({"running", "failed", "cancelled", "expired"}),
    "running": frozenset({"waiting", "completed", "failed", "cancelled", "expired"}),
    "waiting": frozenset({"running", "completed", "failed", "cancelled", "expired"}),
    "failed": frozenset(),
    "completed": frozenset(),
    "expired": frozenset(),
    "cancelled": frozenset(),
}


class RunnerRegistry:
    """Register immutable runner descriptors and select them deterministically."""

    def __init__(self) -> None:
        self._runners: dict[str, dict[str, Any]] = {}

    def register(self, runner: Mapping[str, Any]) -> Mapping[str, Any]:
        value = contract.validate_runner(runner)
        runner_id = str(value["runner_id"])
        if runner_id in self._runners:
            raise ContractError(f"runner_duplicate: {runner_id}")
        self._runners[runner_id] = deepcopy(dict(value))
        return deepcopy(self._runners[runner_id])

    def select(self, capability: str, *, browser_revision: str | None = None) -> Mapping[str, Any]:
        if capability not in contract.CAPABILITIES:
            raise ContractError(f"capability_invalid: {capability}")
        candidates = [
            runner
            for runner in self._runners.values()
            if contract.runner_supports(runner, capability)
            and (browser_revision is None or runner["browser_revision"] == browser_revision)
        ]
        if not candidates:
            raise ContractError(f"capability_missing: {capability}")
        candidates.sort(key=lambda item: (str(item["version"]), str(item["runner_id"])))
        return deepcopy(candidates[0])

    def snapshot(self) -> list[Mapping[str, Any]]:
        return [deepcopy(self._runners[key]) for key in sorted(self._runners)]


class SessionStore:
    """Keep session state and its append-only event chain in one local boundary."""

    def __init__(self, *, now: Callable[[], datetime] | None = None) -> None:
        self._now = now or (lambda: datetime.now(timezone.utc))
        self._sessions: dict[str, dict[str, Any]] = {}
        self._events: dict[str, list[dict[str, Any]]] = {}

    def create(self, session: Mapping[str, Any]) -> Mapping[str, Any]:
        value = contract.validate_session(session)
        session_id = str(value["session_id"])
        if session_id in self._sessions:
            raise ContractError(f"session_duplicate: {session_id}")
        contract.assert_lease_active(value["lease"], now=self._now())
        self._sessions[session_id] = deepcopy(dict(value))
        self._events[session_id] = []
        return deepcopy(self._sessions[session_id])

    def get(self, session_id: str) -> Mapping[str, Any]:
        if session_id not in self._sessions:
            raise ContractError(f"session_not_found: {session_id}")
        return deepcopy(self._sessions[session_id])

    def events(self, session_id: str) -> list[Mapping[str, Any]]:
        if session_id not in self._events:
            raise ContractError(f"session_not_found: {session_id}")
        return deepcopy(self._events[session_id])

    def transition(self, session_id: str, status: str) -> Mapping[str, Any]:
        if session_id not in self._sessions:
            raise ContractError(f"session_not_found: {session_id}")
        session = self._sessions[session_id]
        current = str(session["status"])
        if status not in contract.SESSION_STATUSES:
            raise ContractError("session_status_invalid")
        if status not in _ALLOWED_TRANSITIONS.get(current, frozenset()):
            raise ContractError(f"transition_invalid: {current} -> {status}")
        if current not in _TERMINAL:
            contract.assert_lease_active(session["lease"], now=self._now())
        session["status"] = status
        return deepcopy(session)

    def set_device_profile(self, session_id: str, actor: str, profile: str) -> Mapping[str, Any]:
        """Change the profile only before a run and only for the bound actor."""

        if session_id not in self._sessions:
            raise ContractError(f"session_not_found: {session_id}")
        if profile not in contract.DEVICE_PROFILES:
            raise ContractError("device_profile_invalid")
        session = self._sessions[session_id]
        if actor != session["active_actor"]:
            raise ContractError("actor_invalid: device profile actor is not bound")
        if session["status"] not in {"created", "ready"}:
            raise ContractError("device_profile_locked")
        contract.assert_lease_active(session["lease"], now=self._now())
        session["device_profile"] = profile
        return deepcopy(session)

    def append_event(self, event: Mapping[str, Any]) -> int:
        value = contract.validate_event(event)
        session_id = str(value["session_id"])
        if session_id not in self._sessions:
            raise ContractError(f"session_not_found: {session_id}")
        session = self._sessions[session_id]
        if session["status"] in _TERMINAL:
            raise ContractError("event_after_terminal")
        contract.assert_lease_active(session["lease"], now=self._now())
        if value["actor"] not in {session["active_actor"], "runner", "system"}:
            raise ContractError("actor_invalid: event actor is not bound to session")
        chain = self._events[session_id] + [dict(value)]
        count = contract.validate_event_chain(chain)
        next_status = str(value["status"])
        if next_status != session["status"]:
            if next_status not in _ALLOWED_TRANSITIONS.get(str(session["status"]), frozenset()):
                raise ContractError(f"transition_invalid: {session['status']} -> {next_status}")
            session["status"] = next_status
        self._events[session_id].append(deepcopy(dict(value)))
        return count


class QuickFlowRegistry:
    """Version semantic, selector-free Quick Flows before adapter execution."""

    def __init__(self) -> None:
        self._flows: dict[tuple[str, str], dict[str, Any]] = {}

    def register(self, flow: Mapping[str, Any]) -> Mapping[str, Any]:
        if not isinstance(flow, Mapping) or set(flow) != {"name", "version", "steps"}:
            raise ContractError("quick_flow_invalid")
        name = flow["name"]
        version = flow["version"]
        if not isinstance(name, str) or not _FLOW_NAME_RE.fullmatch(name):
            raise ContractError("quick_flow_invalid: name")
        if not isinstance(version, str) or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", version):
            raise ContractError("quick_flow_invalid: version")
        steps = flow["steps"]
        if not isinstance(steps, list) or not 1 <= len(steps) <= 20:
            raise ContractError("quick_flow_invalid: steps")
        normalized: list[dict[str, str]] = []
        for step in steps:
            if not isinstance(step, Mapping) or not {"operation", "label"}.issubset(set(step)):
                unknown = next(iter(set(step) - {"operation", "label"}), "step") if isinstance(step, Mapping) else "step"
                raise ContractError(f"quick_flow_step_invalid: {unknown}")
            operation, label = step["operation"], step["label"]
            if operation not in _FLOW_OPERATIONS:
                raise ContractError("quick_flow_step_invalid: operation")
            allowed_keys = {"operation", "label", "timeout_ms"} if operation == "wait" else {"operation", "label"}
            if set(step) - allowed_keys:
                raise ContractError("quick_flow_step_invalid: fields")
            if not isinstance(label, str) or not _SAFE_TEXT_RE.fullmatch(label):
                raise ContractError("quick_flow_step_invalid: label")
            if any(token in label.casefold() for token in ("token", "secret", "patient", "raw_qr")):
                raise ContractError("sensitive_field: quick_flow label")
            normalized_step = {"operation": str(operation), "label": label}
            if operation == "wait" and "timeout_ms" in step:
                timeout_ms = step["timeout_ms"]
                if (
                    not isinstance(timeout_ms, int)
                    or isinstance(timeout_ms, bool)
                    or not 1 <= timeout_ms <= contract.MAX_WAIT_MS
                ):
                    raise ContractError("quick_flow_step_invalid: wait_timeout")
                normalized_step["timeout_ms"] = timeout_ms
            normalized.append(normalized_step)
        key = (name, version)
        if key in self._flows:
            raise ContractError(f"quick_flow_duplicate: {name}@{version}")
        self._flows[key] = {"name": name, "version": version, "steps": normalized}
        return deepcopy(self._flows[key])

    def get(self, name: str, version: str) -> Mapping[str, Any]:
        try:
            return deepcopy(self._flows[(name, version)])
        except KeyError as exc:
            raise ContractError(f"quick_flow_not_found: {name}@{version}") from exc

    def snapshot(self) -> list[Mapping[str, Any]]:
        return [deepcopy(self._flows[key]) for key in sorted(self._flows)]
