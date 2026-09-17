#!/usr/bin/env python3
"""Bounded stdio MCP server for the KGG UI-Lab candidate.

The server is intentionally self-contained so the installed marketplace copy
does not depend on the repository checkout.  It keeps all state in memory,
uses synthetic evidence only, and exposes the same nine operations as the
repository adapter.  There is no shell, filesystem, network, editor, ticket,
preview, merge, or external-message operation.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
import re
import sys
import time
from typing import Any, Mapping
from urllib.parse import urlparse


PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "kgg-ui-lab"
SERVER_VERSION = "1.0.0"
MCP_SCHEMA = "kgg-ui-lab/mcp-server/v1"
SESSION_SCHEMA = "kgg-ui-lab/session/v1"
REQUEST_SCHEMA = "kgg-ui-lab/request/v1"
ACTORS = {"codex", "custom_gpt", "max", "system"}
PROFILES = {"tab-s9", "oppo-find-x9", "custom"}
CAPABILITIES = {"browser", "capture", "android", "quick_flows", "width_sweep", "qr_image"}
TOOL_NAMES = (
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
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{5,63}$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
SENSITIVE = ("raw_qr", "base64", "password", "api_key", "secret", "patient_data", "selector", "stack_trace", "token")


class ServerError(ValueError):
    """Stable safe error returned to the MCP caller."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _fail(code: str) -> None:
    raise ServerError(code)


def _scan_safe(value: Any, path: str = "input") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key).casefold()
            if any(token in key_text for token in SENSITIVE):
                _fail("sensitive_field")
            _scan_safe(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _scan_safe(child, f"{path}[{index}]")
    elif isinstance(value, str):
        lowered = value.casefold()
        if any(token in lowered for token in SENSITIVE):
            _fail("sensitive_field")


def _object(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        _fail(f"{label}_invalid")
    return value


def _slug(value: Any, label: str) -> str:
    if not isinstance(value, str) or not ID_RE.fullmatch(value):
        _fail(f"{label}_invalid")
    return value


def _sha(value: Any, label: str) -> str:
    if not isinstance(value, str) or not SHA_RE.fullmatch(value):
        _fail(f"{label}_invalid")
    return value


def _sha256(value: Any, label: str) -> str:
    if not isinstance(value, str) or not SHA256_RE.fullmatch(value):
        _fail(f"{label}_invalid")
    return value


def _actor(value: Any) -> str:
    if value not in ACTORS:
        _fail("mcp_auth_denied")
    return str(value)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _artifact(identifier: str, kind: str, ref: str) -> dict[str, str]:
    digest = hashlib.sha256(ref.encode("utf-8")).hexdigest()
    return {"id": identifier, "kind": kind, "ref": ref, "sha256": digest}


def _request(value: Any, operation: str, session: Mapping[str, Any]) -> Mapping[str, Any]:
    request = _object(value, "request")
    expected = {"schema", "request_id", "session_id", "actor", "operation", "main_sha", "payload_sha256"}
    if set(request) != expected:
        _fail("request_schema_invalid")
    if request["schema"] != REQUEST_SCHEMA:
        _fail("request_schema_invalid")
    _slug(request["request_id"], "request_id")
    _slug(request["session_id"], "session_id")
    actor = _actor(request["actor"])
    if request["operation"] != operation:
        _fail("operation_invalid")
    _sha(request["main_sha"], "main_sha")
    _sha256(request["payload_sha256"], "payload_sha256")
    if request["session_id"] != session["session_id"] or actor != session["active_actor"]:
        _fail("mcp_auth_denied")
    if request["main_sha"] != session["app"]["main_sha"]:
        _fail("mcp_stale_main")
    if request["request_id"] != session["request_id"]:
        _fail("request_binding_invalid")
    if request["request_id"] in session["used_requests"]:
        _fail("duplicate_request")
    return request


def _tool(name: str, description: str, properties: Mapping[str, Any], required: list[str]) -> dict[str, Any]:
    return {
        "name": name,
        "description": description,
        "inputSchema": {"type": "object", "properties": dict(properties), "required": required, "additionalProperties": False},
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": False, "openWorldHint": False},
    }


def tool_catalog() -> list[dict[str, Any]]:
    actor = {"type": "string", "enum": sorted(ACTORS)}
    session_id = {"type": "string", "pattern": "^[a-z0-9][a-z0-9-]{5,63}$"}
    request = {"type": "object", "description": "kgg-ui-lab/request/v1 object; no sensitive fields"}
    return [
        _tool("get_current_state", "Read bounded synthetic UI-Lab state. Never writes.", {"actor": actor}, ["actor"]),
        _tool("get_ticket_state", "Read a synthetic ticket summary only. Never writes or dispatches.", {"actor": actor, "ticket_id": {"type": "string", "pattern": "^#?[0-9]{1,6}$"}}, ["actor", "ticket_id"]),
        _tool("start_ui_session", "Bind a synthetic session, actor, lease, runner, and caller-supplied Fresh-Main SHA in memory.", {"session": {"type": "object", "description": "kgg-ui-lab/session/v1 object"}}, ["session"]),
        _tool("set_device_profile", "Change only the in-memory device profile of an active session.", {"session_id": session_id, "actor": actor, "profile": {"type": "string", "enum": sorted(PROFILES)}}, ["session_id", "actor", "profile"]),
        _tool("run_quick_flow", "Run the bounded synthetic Quick Flow and return sanitized evidence; no browser or repository write.", {"request": request}, ["request"]),
        _tool("capture_screenshot", "Return a deterministic synthetic screenshot artifact; no real screen capture.", {"request": request}, ["request"]),
        _tool("run_width_sweep", "Validate a bounded viewport list and return PREVIEW_ONLY in memory.", {"session_id": session_id, "actor": actor, "viewports": {"type": "array", "maxItems": 10}}, ["session_id", "actor", "viewports"]),
        _tool("get_test_evidence", "Read sanitized in-memory evidence for a session.", {"session_id": session_id, "actor": actor}, ["session_id", "actor"]),
        _tool("get_session_status", "Read sanitized in-memory session status and event count.", {"session_id": session_id, "actor": actor}, ["session_id", "actor"]),
    ]


class Runtime:
    def __init__(self) -> None:
        self.sessions: dict[str, dict[str, Any]] = {}
        self.evidence: dict[str, list[dict[str, Any]]] = {}
        self.call_count = 0
        self.read_count = 0
        self.started_perf: float | None = None

    def _session(self, session_id: Any, actor: Any, *, lease: bool = True) -> dict[str, Any]:
        session_key = _slug(session_id, "session_id")
        actor_value = _actor(actor)
        session = self.sessions.get(session_key)
        if session is None or session["active_actor"] != actor_value:
            _fail("mcp_auth_denied")
        if lease:
            if session["status"] in {"expired", "cancelled"}:
                _fail("lease_expired")
            lease_data = session.get("lease")
            if not isinstance(lease_data, Mapping):
                _fail("lease_invalid")
            try:
                expires = datetime.fromisoformat(str(lease_data["expires_at"]).replace("Z", "+00:00"))
            except (KeyError, TypeError, ValueError):
                _fail("lease_invalid")
            if expires.tzinfo is None or expires <= datetime.now(timezone.utc):
                session["status"] = "expired"
                _fail("lease_expired")
        return session

    def start(self, value: Any) -> dict[str, Any]:
        if self.started_perf is None:
            self.started_perf = time.perf_counter()
        supplied = _object(value, "session")
        required = {"schema", "session_id", "status", "active_actor", "request_id", "lease", "runner", "app", "device_profile", "viewport", "quick_flow", "timeout", "artifacts"}
        if set(supplied) != required or supplied["schema"] != SESSION_SCHEMA:
            _fail("session_schema_invalid")
        session_id = _slug(supplied["session_id"], "session_id")
        if session_id in self.sessions:
            _fail("session_exists")
        active_actor = _actor(supplied["active_actor"])
        _slug(supplied["request_id"], "request_id")
        lease = _object(supplied["lease"], "lease")
        if set(lease) != {"owner", "issued_at", "expires_at"} or lease["owner"] != active_actor:
            _fail("lease_invalid")
        try:
            issued = datetime.fromisoformat(str(lease["issued_at"]).replace("Z", "+00:00"))
            expires = datetime.fromisoformat(str(lease["expires_at"]).replace("Z", "+00:00"))
        except ValueError:
            _fail("lease_invalid")
        if issued.tzinfo is None or expires.tzinfo is None or expires <= datetime.now(timezone.utc):
            _fail("lease_expired")
        runner = _object(supplied["runner"], "runner")
        if set(runner) != {"runner_id", "version", "browser_revision", "capabilities"}:
            _fail("runner_schema_invalid")
        _slug(runner["runner_id"], "runner_id")
        if not isinstance(runner["version"], str) or not VERSION_RE.fullmatch(runner["version"]):
            _fail("runner_version_invalid")
        if not isinstance(runner["browser_revision"], str) or not runner["browser_revision"]:
            _fail("browser_revision_invalid")
        capabilities = runner["capabilities"]
        if not isinstance(capabilities, list) or not capabilities or len(set(capabilities)) != len(capabilities) or not set(capabilities).issubset(CAPABILITIES):
            _fail("runner_capabilities_invalid")
        app = _object(supplied["app"], "app")
        if set(app) != {"name", "url", "main_sha", "preview_sha"} or app["name"] not in {"admin", "patient"}:
            _fail("app_invalid")
        main_sha = _sha(app["main_sha"], "main_sha")
        preview_sha = app["preview_sha"]
        if preview_sha is not None:
            _sha(preview_sha, "preview_sha")
        parsed_url = urlparse(str(app["url"]))
        if not (
            (parsed_url.scheme == "https" and bool(parsed_url.netloc))
            or (parsed_url.scheme == "http" and parsed_url.hostname in {"localhost", "127.0.0.1"} and bool(parsed_url.netloc))
        ):
            _fail("app_url_invalid")
        if supplied["device_profile"] not in PROFILES:
            _fail("device_profile_invalid")
        viewport = _object(supplied["viewport"], "viewport")
        if set(viewport) != {"width", "height", "device_scale_factor"}:
            _fail("viewport_invalid")
        if not all(isinstance(viewport[key], int) and not isinstance(viewport[key], bool) and 240 <= viewport[key] <= 10000 for key in ("width", "height")):
            _fail("viewport_invalid")
        if not isinstance(viewport["device_scale_factor"], (int, float)) or isinstance(viewport["device_scale_factor"], bool) or not 0.5 <= viewport["device_scale_factor"] <= 4:
            _fail("viewport_invalid")
        timeout = _object(supplied["timeout"], "timeout")
        if set(timeout) != {"timeout_ms", "cleanup_on_cancel"}:
            _fail("timeout_invalid")
        timeout_ms = timeout["timeout_ms"]
        if not isinstance(timeout_ms, int) or isinstance(timeout_ms, bool) or not 1000 <= timeout_ms <= 1_800_000:
            _fail("timeout_invalid")
        if not isinstance(timeout["cleanup_on_cancel"], bool):
            _fail("timeout_invalid")
        _scan_safe(supplied)
        session = deepcopy(dict(supplied))
        session["status"] = "ready"
        session["app"] = deepcopy(dict(app))
        session["used_requests"] = []
        session["events"] = []
        session["created_at"] = _now()
        session["main_sha"] = main_sha
        self.sessions[session_id] = session
        return {"schema": MCP_SCHEMA, "operation": "start_ui_session", "session": self._public_session(session)}

    @staticmethod
    def _public_session(session: Mapping[str, Any]) -> dict[str, Any]:
        return {key: deepcopy(value) for key, value in session.items() if key not in {"used_requests", "events", "main_sha"}}

    def current(self, actor: Any) -> dict[str, Any]:
        actor_value = _actor(actor)
        sessions = [s for s in self.sessions.values() if s["active_actor"] == actor_value]
        main_sha = sessions[-1]["app"]["main_sha"] if sessions else "not_bound"
        return {"schema": MCP_SCHEMA, "operation": "get_current_state", "actor": actor_value, "status": "ready", "main_sha": main_sha}

    def ticket(self, actor: Any, ticket_id: Any) -> dict[str, Any]:
        actor_value = _actor(actor)
        if not isinstance(ticket_id, str) or not re.fullmatch(r"#?[0-9]{1,6}", ticket_id):
            _fail("ticket_id_invalid")
        return {"schema": MCP_SCHEMA, "operation": "get_ticket_state", "actor": actor_value, "ticket_id": ticket_id, "status": "synthetic-read-only"}

    def set_profile(self, session_id: Any, actor: Any, profile: Any) -> dict[str, Any]:
        session = self._session(session_id, actor)
        if profile not in PROFILES:
            _fail("device_profile_invalid")
        session["device_profile"] = profile
        return {"schema": MCP_SCHEMA, "operation": "set_device_profile", "session": self._public_session(session)}

    def run_flow(self, value: Any, operation: str) -> dict[str, Any]:
        request = _object(value, "request")
        session_id = request.get("session_id")
        session = self._session(session_id, request.get("actor"))
        required_capability = "quick_flows" if operation == "run_quick_flow" else "capture"
        if required_capability not in session["runner"]["capabilities"]:
            _fail("capability_missing")
        checked = _request(request, operation, session)
        session["status"] = "running"
        session["used_requests"].append(checked["request_id"])
        screenshot = _artifact("kgg-shot-001", "screenshot", "synthetic://kgg-ui-lab/tablet-splitter-scale-drag-synth/baseline")
        if operation == "run_quick_flow":
            result = {
                "status": "PASS",
                "error_class": "",
                "steps": [
                    {"operation": "read_state", "label": "pilot-area-ready", "status": "PASS", "artifact_refs": []},
                    {"operation": "click", "label": "tablet-splitter-control", "status": "PASS", "artifact_refs": []},
                    {"operation": "read_state", "label": "scale-drag-state", "status": "PASS", "artifact_refs": []},
                    {"operation": "capture_screenshot", "label": "pilot-180-evidence", "status": "PASS", "artifact_refs": [screenshot["id"]]},
                ],
                "artifacts": [screenshot],
            }
            session["status"] = "completed"
            event = {"event": "quick_flow_completed", "status": "PASS", "at": _now()}
        else:
            result = {"status": "PASS", "artifacts": [screenshot]}
            event = {"event": "screenshot_captured", "status": "PASS", "at": _now()}
        session["events"].append(event)
        evidence = {"schema": "kgg-ui-lab/evidence/v1", "status": "PASS", "artifacts": [screenshot]}
        self.evidence.setdefault(session["session_id"], []).append(evidence)
        # This installed, self-contained server has no trusted host transcript
        # or independent evaluator.  Returning numbers here would turn local
        # implementation claims into counterfeit comparator telemetry.  The
        # trusted release-pipeline collector may replace this with a complete
        # measurement envelope after external reconciliation.
        pilot_metrics = {"status": "FAIL", "error_class": "NUMERIC_METRICS_NOT_VERIFIABLE"}
        return {"schema": MCP_SCHEMA, "operation": operation, "result": result, "evidence": evidence, "pilot_metrics": pilot_metrics, "session_status": session["status"]}

    def sweep(self, session_id: Any, actor: Any, viewports: Any) -> dict[str, Any]:
        session = self._session(session_id, actor)
        if "width_sweep" not in session["runner"]["capabilities"]:
            _fail("capability_missing")
        if not isinstance(viewports, list) or not 1 <= len(viewports) <= 10:
            _fail("viewport_sweep_invalid")
        for viewport in viewports:
            item = _object(viewport, "viewport")
            if set(item) != {"width", "height", "device_scale_factor"}:
                _fail("viewport_invalid")
            if not all(isinstance(item[key], int) and not isinstance(item[key], bool) and 240 <= item[key] <= 10000 for key in ("width", "height")):
                _fail("viewport_invalid")
            if not isinstance(item["device_scale_factor"], (int, float)) or isinstance(item["device_scale_factor"], bool) or not 0.5 <= item["device_scale_factor"] <= 4:
                _fail("viewport_invalid")
        return {"schema": MCP_SCHEMA, "operation": "run_width_sweep", "session_id": session_id, "viewports": deepcopy(viewports), "status": "PREVIEW_ONLY"}

    def evidence_read(self, session_id: Any, actor: Any) -> dict[str, Any]:
        self._session(session_id, actor, lease=False)
        return {"schema": MCP_SCHEMA, "operation": "get_test_evidence", "session_id": session_id, "evidence": deepcopy(self.evidence.get(session_id, []))}

    def status_read(self, session_id: Any, actor: Any) -> dict[str, Any]:
        session = self._session(session_id, actor, lease=False)
        return {"schema": MCP_SCHEMA, "operation": "get_session_status", "session_id": session_id, "status": session["status"], "event_count": len(session["events"]), "main_sha": session["app"]["main_sha"]}

    def call(self, name: str, arguments: Any) -> dict[str, Any]:
        args = _object(arguments or {}, "arguments")
        _scan_safe(args)
        if name not in TOOL_NAMES:
            _fail("tool_not_found")
        self.call_count += 1
        if name in {"get_current_state", "get_ticket_state", "get_test_evidence", "get_session_status"}:
            self.read_count += 1
        if name == "get_current_state":
            return self.current(args.get("actor"))
        if name == "get_ticket_state":
            return self.ticket(args.get("actor"), args.get("ticket_id"))
        if name == "start_ui_session":
            return self.start(args.get("session"))
        if name == "set_device_profile":
            return self.set_profile(args.get("session_id"), args.get("actor"), args.get("profile"))
        if name in {"run_quick_flow", "capture_screenshot"}:
            return self.run_flow(args.get("request"), name)
        if name == "run_width_sweep":
            return self.sweep(args.get("session_id"), args.get("actor"), args.get("viewports"))
        if name == "get_test_evidence":
            return self.evidence_read(args.get("session_id"), args.get("actor"))
        if name == "get_session_status":
            return self.status_read(args.get("session_id"), args.get("actor"))
        _fail("tool_not_found")


def _result_content(value: Mapping[str, Any]) -> dict[str, Any]:
    encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return {"content": [{"type": "text", "text": encoded}], "structuredContent": deepcopy(dict(value))}


def handle(runtime: Runtime, message: Mapping[str, Any]) -> dict[str, Any] | None:
    method = message.get("method")
    identifier = message.get("id")
    if method == "notifications/initialized":
        return None
    if method == "initialize":
        return {"jsonrpc": "2.0", "id": identifier, "result": {"protocolVersion": PROTOCOL_VERSION, "capabilities": {"tools": {"listChanged": False}}, "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION}}}
    if method == "ping":
        return {"jsonrpc": "2.0", "id": identifier, "result": {}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": identifier, "result": {"tools": tool_catalog()}}
    if method == "tools/call":
        try:
            params = _object(message.get("params"), "params")
            name = params.get("name")
            if name not in TOOL_NAMES:
                _fail("tool_not_found")
            value = runtime.call(str(name), params.get("arguments", {}))
            return {"jsonrpc": "2.0", "id": identifier, "result": _result_content(value)}
        except ServerError as exc:
            return {"jsonrpc": "2.0", "id": identifier, "result": {"isError": True, "content": [{"type": "text", "text": json.dumps({"status": "FAIL", "error_class": exc.code}, separators=(",", ":"))}]}}
    if identifier is None:
        return None
    return {"jsonrpc": "2.0", "id": identifier, "error": {"code": -32601, "message": "method_not_found"}}


def main() -> int:
    runtime = Runtime()
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            message = json.loads(line)
            if not isinstance(message, Mapping):
                raise ValueError
            response = handle(runtime, message)
        except (ValueError, json.JSONDecodeError):
            response = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "invalid_request"}}
        except Exception:
            response = {"jsonrpc": "2.0", "id": None, "error": {"code": -32603, "message": "internal_error"}}
        if response is not None:
            sys.stdout.write(json.dumps(response, ensure_ascii=False, separators=(",", ":")) + "\n")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
