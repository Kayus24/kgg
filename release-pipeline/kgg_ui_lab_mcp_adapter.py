#!/usr/bin/env python3
"""Local preview-safe MCP-shaped adapter over the UI-Lab contracts.

This is an adapter contract, not a network server. It exposes a fixed tool
catalog and delegates all mutations to the bounded in-memory stores. No shell,
editor, live, merge, or external-message operation is represented here.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import re
from typing import Any, Callable, Mapping

import kgg_ui_lab_contract as contract
import kgg_ui_lab_evidence as evidence
import kgg_ui_lab_runtime as runtime
from kgg_ui_lab_browser import SemanticBrowserRunner
from kgg_ui_lab_session import QuickFlowRegistry, RunnerRegistry, SessionStore


MCP_SCHEMA = "kgg-ui-lab/mcp-adapter/v1"
TOOL_CATALOG = (
    "get_current_state",
    "get_ticket_state",
    "start_ui_session",
    "set_device_profile",
    "run_quick_flow",
    "capture_screenshot",
    "run_width_sweep",
    "get_test_evidence",
    "get_session_status",
)
_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{5,63}$")
_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class McpAdapterError(ValueError):
    """A stable, non-sensitive adapter error code."""


def _fail(code: str, detail: str = "") -> None:
    raise McpAdapterError(code if not detail else f"{code}: {detail}")


class KggUiLabMcpAdapter:
    """Expose only contract-shaped local operations."""

    def __init__(
        self,
        *,
        main_sha: str,
        now: Callable[[], datetime] | None = None,
        state_provider: Callable[[], Mapping[str, Any]] | None = None,
        ticket_provider: Callable[[str], Mapping[str, Any]] | None = None,
        runner_registry: RunnerRegistry | None = None,
        flow_registry: QuickFlowRegistry | None = None,
        session_store: SessionStore | None = None,
    ) -> None:
        if not isinstance(main_sha, str) or not _SHA_RE.fullmatch(main_sha):
            _fail("mcp_stale_main", "main_sha_invalid")
        self.main_sha = main_sha
        self.now = now or (lambda: datetime.now(timezone.utc))
        self.state_provider = state_provider or (lambda: {"status": "ready"})
        self.ticket_provider = ticket_provider or (lambda ticket_id: {"ticket_id": ticket_id, "status": "unknown"})
        self.runners = runner_registry or RunnerRegistry()
        self.flows = flow_registry or QuickFlowRegistry()
        self.sessions = session_store or SessionStore(now=self.now)
        self._evidence: dict[str, list[dict[str, Any]]] = {}

    @staticmethod
    def tool_catalog() -> tuple[str, ...]:
        return TOOL_CATALOG

    def _actor(self, actor: str) -> str:
        if actor not in contract.ACTORS:
            _fail("mcp_auth_denied", "actor_invalid")
        return actor

    def _get_session(self, session_id: str, actor: str, *, lease: bool = True) -> Mapping[str, Any]:
        if not isinstance(session_id, str) or not _ID_RE.fullmatch(session_id):
            _fail("session_id_invalid")
        actor = self._actor(actor)
        session = self.sessions.get(session_id)
        if session["active_actor"] != actor:
            _fail("mcp_auth_denied", "actor_not_bound")
        if lease:
            try:
                contract.assert_lease_active(session["lease"], now=self.now())
            except contract.ContractError as exc:
                raise McpAdapterError(str(exc)) from exc
        return session

    def get_current_state(self, actor: str) -> dict[str, Any]:
        actor = self._actor(actor)
        state = self.state_provider()
        if not isinstance(state, Mapping):
            _fail("state_invalid")
        safe = {str(key): deepcopy(value) for key, value in state.items() if str(key) in {"status", "ticket_id", "branch", "head"}}
        safe.update({"schema": MCP_SCHEMA, "operation": "get_current_state", "actor": actor, "main_sha": self.main_sha})
        return safe

    def get_ticket_state(self, actor: str, ticket_id: str) -> dict[str, Any]:
        actor = self._actor(actor)
        if not isinstance(ticket_id, str) or not re.fullmatch(r"#?[0-9]{1,6}", ticket_id):
            _fail("ticket_id_invalid")
        state = self.ticket_provider(ticket_id)
        if not isinstance(state, Mapping):
            _fail("ticket_state_invalid")
        safe = {str(key): deepcopy(value) for key, value in state.items() if str(key) in {"ticket_id", "status", "title", "updated_at", "main_sha"}}
        safe.update({"schema": MCP_SCHEMA, "operation": "get_ticket_state", "actor": actor, "main_sha": self.main_sha})
        return safe

    def start_ui_session(self, session: Mapping[str, Any]) -> dict[str, Any]:
        value = contract.validate_session(session)
        self._actor(value["active_actor"])
        if value["app"]["main_sha"] != self.main_sha:
            _fail("mcp_stale_main")
        created = self.sessions.create(value)
        return {"schema": MCP_SCHEMA, "operation": "start_ui_session", "session": created}

    def set_device_profile(self, session_id: str, actor: str, profile: str) -> dict[str, Any]:
        self._get_session(session_id, actor)
        try:
            value = self.sessions.set_device_profile(session_id, actor, profile)
        except contract.ContractError as exc:
            raise McpAdapterError(str(exc)) from exc
        return {"schema": MCP_SCHEMA, "operation": "set_device_profile", "session": value}

    def _validate_request(self, request: Mapping[str, Any], operation: str) -> tuple[Mapping[str, Any], Mapping[str, Any]]:
        try:
            value = contract.validate_request(request)
        except contract.ContractError as exc:
            raise McpAdapterError(str(exc)) from exc
        if value["operation"] != operation:
            _fail("operation_invalid", operation)
        session = self._get_session(value["session_id"], value["actor"])
        if value["request_id"] != session["request_id"]:
            _fail("request_binding_invalid")
        if value["main_sha"] != self.main_sha or value["main_sha"] != session["app"]["main_sha"]:
            _fail("mcp_stale_main")
        try:
            contract.assert_request_not_replayed(self.sessions.events(value["session_id"]), value["request_id"])
        except contract.ContractError as exc:
            raise McpAdapterError(str(exc)) from exc
        return value, session

    @staticmethod
    def _event_id(session_id: str, request_id: str, sequence: int, event_type: str) -> str:
        digest = hashlib.sha256(f"{session_id}:{request_id}:{sequence}:{event_type}".encode("utf-8")).hexdigest()[:24]
        return f"adapter-{digest}"

    def _append_event(
        self,
        session: Mapping[str, Any],
        request_id: str,
        event_type: str,
        actor: str,
        status: str,
        summary: str,
        artifacts: list[Mapping[str, Any]],
    ) -> None:
        sequence = len(self.sessions.events(session["session_id"])) + 1
        evidence_refs = [{"kind": item["kind"], "ref": item["ref"], "sha256": item["sha256"]} for item in artifacts]
        event = {
            "schema": contract.EVENT_SCHEMA,
            "event_id": self._event_id(session["session_id"], request_id, sequence, event_type),
            "session_id": session["session_id"],
            "request_id": request_id,
            "sequence": sequence,
            "event_type": event_type,
            "actor": actor,
            "timestamp": self.now().astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
            "status": status,
            "summary": summary,
            "evidence": evidence_refs,
        }
        try:
            self.sessions.append_event(event)
        except contract.ContractError as exc:
            raise McpAdapterError(str(exc)) from exc

    def run_quick_flow(
        self,
        request: Mapping[str, Any],
        observer: Callable[[Mapping[str, str]], Mapping[str, Any]],
    ) -> dict[str, Any]:
        value, session = self._validate_request(request, "run_quick_flow")
        if session["status"] not in {"ready", "waiting"}:
            _fail("session_not_runnable")
        try:
            flow = self.flows.get(session["quick_flow"]["name"], session["quick_flow"]["version"])
        except contract.ContractError as exc:
            raise McpAdapterError(str(exc)) from exc
        self._append_event(session, value["request_id"], "request_accepted", value["actor"], "running", "Quick Flow request accepted.", [])
        runner = SemanticBrowserRunner(session["runner"], observer, now=self.now)
        result = runner.run(flow)
        terminal = "completed" if result["status"] == "PASS" else "failed"
        for index, step in enumerate(result["steps"], start=1):
            status = terminal if index == len(result["steps"]) else "running"
            self._append_event(session, value["request_id"], f"quick_flow_step_{index}", "runner", status, "Semantic Quick Flow step completed.", [result["artifacts"][result["artifacts"].index(next(item for item in result["artifacts"] if item["id"] == ref))] for ref in step["artifact_refs"]])
        session_after = self.sessions.get(session["session_id"])
        evidence_status = result["status"]
        error_class = result["error_class"]
        ev = evidence.build_evidence(
            session=session_after,
            started_at=result["started_at"],
            ended_at=result["ended_at"],
            status=evidence_status,
            error_class=error_class,
            steps=result["steps"],
            artifacts=result["artifacts"],
        )
        self._evidence.setdefault(session["session_id"], []).append(ev)
        return {"schema": MCP_SCHEMA, "operation": "run_quick_flow", "result": result, "evidence": ev, "session_status": session_after["status"]}

    def capture_screenshot(
        self,
        request: Mapping[str, Any],
        observer: Callable[[Mapping[str, str]], Mapping[str, Any]],
    ) -> dict[str, Any]:
        value, session = self._validate_request(request, "capture_screenshot")
        try:
            contract.require_capability(session, "capture")
        except contract.ContractError as exc:
            raise McpAdapterError(str(exc)) from exc
        if not callable(observer):
            _fail("observer_invalid")
        try:
            observation = observer({"operation": "capture_screenshot", "label": "manual-capture"})
        except Exception as exc:  # noqa: BLE001 - do not expose runner internals
            raise McpAdapterError(runtime.classify_failure("capture", exc.__class__.__name__)) from exc
        if not isinstance(observation, Mapping) or set(observation) != {"expected", "actual", "status", "artifacts"}:
            _fail("observation_invalid")
        artifacts = observation["artifacts"]
        if not isinstance(artifacts, list) or not artifacts:
            _fail("evidence_missing", "screenshot")
        return {"schema": MCP_SCHEMA, "operation": "capture_screenshot", "session_id": session["session_id"], "request_id": value["request_id"], "artifacts": deepcopy(artifacts)}

    def run_width_sweep(self, session_id: str, actor: str, viewports: list[Mapping[str, Any]]) -> dict[str, Any]:
        session = self._get_session(session_id, actor)
        try:
            contract.require_capability(session, "width_sweep")
        except contract.ContractError as exc:
            raise McpAdapterError(str(exc)) from exc
        if not isinstance(viewports, list) or not 1 <= len(viewports) <= 10:
            _fail("viewport_sweep_invalid")
        normalized: list[dict[str, Any]] = []
        for viewport in viewports:
            if not isinstance(viewport, Mapping) or set(viewport) != {"width", "height", "device_scale_factor"}:
                _fail("viewport_invalid")
            width, height, scale = viewport["width"], viewport["height"], viewport["device_scale_factor"]
            if not isinstance(width, int) or not isinstance(height, int) or not 240 <= width <= 10000 or not 240 <= height <= 10000:
                _fail("viewport_invalid")
            if not isinstance(scale, (int, float)) or isinstance(scale, bool) or not 0.5 <= scale <= 4:
                _fail("viewport_invalid")
            normalized.append({"width": width, "height": height, "device_scale_factor": scale})
        return {"schema": MCP_SCHEMA, "operation": "run_width_sweep", "session_id": session_id, "viewports": normalized, "status": "PREVIEW_ONLY"}

    def get_test_evidence(self, session_id: str, actor: str) -> dict[str, Any]:
        self._get_session(session_id, actor, lease=False)
        return {"schema": MCP_SCHEMA, "operation": "get_test_evidence", "session_id": session_id, "evidence": deepcopy(self._evidence.get(session_id, []))}

    def get_session_status(self, session_id: str, actor: str) -> dict[str, Any]:
        session = self._get_session(session_id, actor, lease=False)
        return {"schema": MCP_SCHEMA, "operation": "get_session_status", "session_id": session_id, "status": session["status"], "event_count": len(self.sessions.events(session_id)), "runner_id": session["runner"]["runner_id"], "main_sha": session["app"]["main_sha"]}
