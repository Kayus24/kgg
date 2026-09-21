#!/usr/bin/env python3
"""Bounded stdio MCP server for the KGG UI-Lab candidate.

The server is intentionally self-contained so the installed marketplace copy
does not depend on the repository checkout.  It keeps all state in memory,
uses synthetic evidence by default, and exposes the same bounded operations as the
repository adapter.  There is no shell, filesystem, network, editor, ticket,
preview, merge, or external-message operation.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
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
CAPABILITIES = {"browser", "capture", "android", "quick_flows", "visual_loop", "width_sweep", "qr_image"}
TOOL_NAMES = (
    "get_current_state",
    "get_ticket_state",
    "start_ui_session",
    "set_device_profile",
    "run_quick_flow",
    "capture_screenshot",
    "observe_visual_state",
    "execute_visual_action",
    "run_width_sweep",
    "get_test_evidence",
    "get_session_status",
)
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{5,63}$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
SENSITIVE = ("raw_qr", "base64", "password", "api_key", "secret", "patient_data", "selector", "stack_trace", "token")


def _real_browser_enabled() -> bool:
    return os.environ.get("KGG_REAL_BROWSER", "").casefold() in {"1", "true", "yes"}


def _load_real_browser_module():
    """Load the optional sibling bridge even when this file is imported in tests."""

    try:
        import real_browser  # type: ignore
        return real_browser
    except ModuleNotFoundError:
        module_path = Path(__file__).with_name("real_browser.py")
        spec = importlib.util.spec_from_file_location("kgg_plugin_real_browser", module_path)
        if spec is None or spec.loader is None:
            _fail("real_browser_helper_missing")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module


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


def _visual_decision(value: Any) -> dict[str, Any]:
    decision = _object(value, "decision")
    allowed = {"operation", "label", "coordinates", "text", "delta_y", "timeout_ms", "expected_state_after", "observation_id"}
    if set(decision) - allowed or not {"operation", "label", "expected_state_after", "observation_id"}.issubset(decision):
        _fail("visual_decision_invalid")
    operation = decision["operation"]
    if operation not in {"click", "tap", "type", "scroll", "wait"}:
        _fail("visual_decision_invalid")
    label = decision["label"]
    if not isinstance(label, str) or not 1 <= len(label) <= 200 or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 ._:/-]{0,199}", label):
        _fail("visual_decision_invalid")
    expected = decision["expected_state_after"]
    if not isinstance(expected, str) or not 1 <= len(expected) <= 200 or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 ._:/-]{0,199}", expected):
        _fail("visual_decision_invalid")
    observation_id = decision["observation_id"]
    if not isinstance(observation_id, str) or not SHA256_RE.fullmatch(observation_id):
        _fail("visual_decision_invalid")
    normalized: dict[str, Any] = {"operation": operation, "label": label, "expected_state_after": expected, "observation_id": observation_id}
    if "coordinates" in decision:
        coordinates = _object(decision["coordinates"], "coordinates")
        if set(coordinates) != {"x", "y"} or not all(isinstance(coordinates[key], int) and not isinstance(coordinates[key], bool) and coordinates[key] >= 0 for key in ("x", "y")):
            _fail("visual_decision_invalid")
        normalized["coordinates"] = {"x": coordinates["x"], "y": coordinates["y"]}
    if operation == "type":
        if not isinstance(decision.get("text"), str) or len(decision["text"]) > 200:
            _fail("visual_decision_invalid")
        normalized["text"] = decision["text"]
    if operation == "scroll":
        delta = decision.get("delta_y", 500)
        if not isinstance(delta, int) or isinstance(delta, bool) or not -10000 <= delta <= 10000:
            _fail("visual_decision_invalid")
        normalized["delta_y"] = delta
    if operation == "wait":
        timeout = decision.get("timeout_ms", 1000)
        if not isinstance(timeout, int) or isinstance(timeout, bool) or not 1 <= timeout <= 5000:
            _fail("visual_decision_invalid")
        normalized["timeout_ms"] = timeout
    return normalized


def _actor(value: Any) -> str:
    if value not in ACTORS:
        _fail("mcp_auth_denied")
    return str(value)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _artifact(identifier: str, kind: str, ref: str) -> dict[str, str]:
    digest = hashlib.sha256(ref.encode("utf-8")).hexdigest()
    return {"id": identifier, "kind": kind, "ref": ref, "sha256": digest}


def _request(value: Any, operation: str, session: Mapping[str, Any], *, sequential: bool = False) -> Mapping[str, Any]:
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
    if not sequential and request["request_id"] != session["request_id"]:
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
    visual_decision = {
        "type": "object",
        "description": "One bounded agent decision derived from the previously returned screenshot; no selectors or JavaScript.",
        "properties": {
            "operation": {"type": "string", "enum": ["click", "tap", "type", "scroll", "wait"]},
            "label": {"type": "string", "pattern": "^[A-Za-z0-9][A-Za-z0-9 ._:/-]{0,199}$"},
            "coordinates": {"type": "object", "properties": {"x": {"type": "integer", "minimum": 0}, "y": {"type": "integer", "minimum": 0}}, "required": ["x", "y"], "additionalProperties": False},
            "text": {"type": "string", "maxLength": 200},
            "delta_y": {"type": "integer", "minimum": -10000, "maximum": 10000},
            "timeout_ms": {"type": "integer", "minimum": 1, "maximum": 5000},
            "expected_state_after": {"type": "string", "pattern": "^[A-Za-z0-9][A-Za-z0-9 ._:/-]{0,199}$"},
            "observation_id": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        },
        "required": ["operation", "label", "expected_state_after", "observation_id"],
        "additionalProperties": False,
    }
    return [
        _tool("get_current_state", "Read bounded synthetic UI-Lab state. Never writes.", {"actor": actor}, ["actor"]),
        _tool("get_ticket_state", "Read a synthetic ticket summary only. Never writes or dispatches.", {"actor": actor, "ticket_id": {"type": "string", "pattern": "^#?[0-9]{1,6}$"}}, ["actor", "ticket_id"]),
        _tool("start_ui_session", "Bind a synthetic session, actor, lease, runner, and caller-supplied Fresh-Main SHA in memory.", {"session": {"type": "object", "description": "kgg-ui-lab/session/v1 object"}}, ["session"]),
        _tool("set_device_profile", "Change only the in-memory device profile of an active session.", {"session_id": session_id, "actor": actor, "profile": {"type": "string", "enum": sorted(PROFILES)}}, ["session_id", "actor", "profile"]),
        _tool("run_quick_flow", "Run the bounded synthetic Quick Flow and return sanitized evidence; no browser or repository write.", {"request": request}, ["request"]),
        _tool("capture_screenshot", "Return a deterministic synthetic screenshot artifact, or a real screenshot only when the opt-in real host is enabled.", {"request": request}, ["request"]),
        _tool("observe_visual_state", "Observe one real screenshot and state from a persistent bounded browser page; the caller must decide the next action.", {"request": request}, ["request"]),
        _tool("execute_visual_action", "Execute exactly one caller-supplied bounded action in the same page and return a second screenshot plus state verification.", {"request": request, "decision": visual_decision}, ["request", "decision"]),
        _tool("run_width_sweep", "Validate a bounded viewport list and return PREVIEW_ONLY in memory.", {"session_id": session_id, "actor": actor, "viewports": {"type": "array", "maxItems": 10}}, ["session_id", "actor", "viewports"]),
        _tool("get_test_evidence", "Read sanitized in-memory evidence for a session.", {"session_id": session_id, "actor": actor}, ["session_id", "actor"]),
        _tool("get_session_status", "Read sanitized in-memory session status and event count.", {"session_id": session_id, "actor": actor}, ["session_id", "actor"]),
    ]


class Runtime:
    def __init__(self) -> None:
        self.sessions: dict[str, dict[str, Any]] = {}
        self.evidence: dict[str, list[dict[str, Any]]] = {}
        self.visual_sessions: dict[str, Any] = {}
        self.call_count = 0
        self.read_count = 0
        self.started_perf: float | None = None

    def _close_visual(self, session_id: str) -> None:
        browser = self.visual_sessions.pop(session_id, None)
        if browser is not None:
            try:
                browser.close()
            except Exception:  # noqa: BLE001 - cleanup must never mask the gate result
                pass

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

    def _run_real_flow(self, session: Mapping[str, Any], operation: str) -> dict[str, Any]:
        """Run one explicitly enabled real browser flow through the host bridge."""

        real_browser = _load_real_browser_module()
        if operation == "run_quick_flow":
            flow_name = session["quick_flow"]["name"]
            real_flows = {
                "admin-start-baseline": [
                    {"operation": "read_state", "label": "admin-ready"},
                    {"operation": "capture_screenshot", "label": "baseline-screen"},
                ],
                "pilot-180-reproduce": [
                    {"operation": "read_state", "label": "pilot-area-ready"},
                    {"operation": "capture_screenshot", "label": "baseline-screen"},
                    {"operation": "click", "label": "tablet-splitter-control"},
                    {"operation": "read_state", "label": "scale-drag-state"},
                    {"operation": "capture_screenshot", "label": "pilot-180-evidence"},
                ],
                "synthetic-qr-preview-link": [
                    {"operation": "read_state", "label": "admin-preview-ready"},
                    {"operation": "capture_screenshot", "label": "baseline-screen"},
                    {"operation": "click", "label": "synthetic-qr-image"},
                    {"operation": "read_state", "label": "linked-preview-ready"},
                    {"operation": "capture_screenshot", "label": "preview-link-evidence"},
                ],
            }
            steps = real_flows.get(flow_name)
            if steps is None:
                _fail("real_browser_flow_not_allowlisted")
        else:
            steps = [{"operation": "capture_screenshot", "label": "manual-capture"}]
        try:
            return real_browser.run_real_flow(
                url=session["app"]["url"],
                viewport=session["viewport"],
                steps=steps,
                run_id=f"{session['session_id']}-{session['request_id']}",
                timeout_ms=session["timeout"]["timeout_ms"],
            )
        except real_browser.RealBrowserError as exc:
            _fail(exc.code)
        _fail("real_browser_failed")

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
        if _real_browser_enabled():
            real = self._run_real_flow(session, operation)
            session["status"] = "completed" if real["status"] == "PASS" else "failed"
            event = {"event": "real_browser_run_completed", "status": real["status"], "at": _now()}
            session["events"].append(event)
            evidence = {
                "schema": "kgg-ui-lab/evidence/v1",
                "status": real["status"],
                "surface": "real_browser",
                "artifacts": real["artifacts"],
                "runtime_ms": real["runtime_ms"],
                "final_state": real["final_state"],
            }
            self.evidence.setdefault(session["session_id"], []).append(evidence)
            result = {
                "status": real["status"],
                "error_class": real["error_class"],
                "steps": real["steps"],
                "artifacts": real["artifacts"],
                "final_state": real["final_state"],
                "runtime_ms": real["runtime_ms"],
            }
            pilot_metrics = {"status": "FAIL", "error_class": "NUMERIC_METRICS_NOT_VERIFIABLE"}
            return {
                "schema": MCP_SCHEMA,
                "operation": operation,
                "result": result,
                "evidence": evidence,
                "pilot_metrics": pilot_metrics,
                "session_status": session["status"],
                "_images": real["images"],
            }
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

    def observe_visual(self, value: Any) -> dict[str, Any]:
        if not _real_browser_enabled():
            _fail("real_browser_not_enabled")
        request = _object(value, "request")
        session = self._session(request.get("session_id"), request.get("actor"))
        if "visual_loop" not in session["runner"]["capabilities"] or "capture" not in session["runner"]["capabilities"]:
            _fail("capability_missing")
        checked = _request(request, "observe_visual_state", session, sequential=True)
        session["status"] = "observing"
        session["used_requests"].append(checked["request_id"])
        real_browser = _load_real_browser_module()
        try:
            browser = real_browser.PersistentRealBrowser(
                url=session["app"]["url"],
                viewport=session["viewport"],
                run_id=f"{session['session_id']}-{checked['request_id']}",
                timeout_ms=session["timeout"]["timeout_ms"],
            )
            self._close_visual(session["session_id"])
            self.visual_sessions[session["session_id"]] = browser
            observed = browser.observe()
        except real_browser.RealBrowserError as exc:
            self._close_visual(session["session_id"])
            session["status"] = "failed"
            _fail(exc.code)
        artifact = observed["artifacts"][0] if observed["artifacts"] else None
        image = observed["images"][0] if observed["images"] else None
        if artifact is None or image is None:
            self._close_visual(session["session_id"])
            session["status"] = "failed"
            _fail("visual_observation_missing_screenshot")
        observation_id = hashlib.sha256(f"{session['session_id']}|{artifact['sha256']}|{observed['state']}".encode("utf-8")).hexdigest()
        session["visual_observation"] = {
            "id": observation_id,
            "state": observed["state"],
            "artifact": artifact,
            "image": image,
        }
        evidence = {
            "schema": "kgg-ui-lab/visual-evidence/v1",
            "status": "OBSERVED",
            "surface": "real_browser",
            "observation_id": observation_id,
            "state_before": observed["state"],
            "artifacts": [artifact],
        }
        self.evidence.setdefault(session["session_id"], []).append(evidence)
        return {
            "schema": MCP_SCHEMA,
            "operation": "observe_visual_state",
            "observation": {"id": observation_id, "state": observed["state"], "artifact": artifact},
            "evidence": evidence,
            "session_status": session["status"],
            "_images": [image],
        }

    def execute_visual_action(self, value: Any, decision_value: Any) -> dict[str, Any]:
        if not _real_browser_enabled():
            _fail("real_browser_not_enabled")
        request = _object(value, "request")
        session = self._session(request.get("session_id"), request.get("actor"))
        if "visual_loop" not in session["runner"]["capabilities"]:
            _fail("capability_missing")
        checked = _request(request, "execute_visual_action", session, sequential=True)
        observation = session.get("visual_observation")
        if not isinstance(observation, Mapping):
            _fail("visual_observation_required")
        decision = _visual_decision(decision_value)
        if decision["observation_id"] != observation["id"]:
            _fail("visual_observation_stale")
        session["status"] = "acting"
        session["used_requests"].append(checked["request_id"])
        browser = self.visual_sessions.get(session["session_id"])
        if browser is None:
            session["status"] = "failed"
            _fail("visual_session_not_initialized")
        real_browser = _load_real_browser_module()
        try:
            action_result = browser.act(decision)
            action = action_result.get("action")
            if not isinstance(action, Mapping) or action.get("before_state") != observation["state"]:
                _fail("visual_state_changed_before_action")
            verified = browser.observe()
            after_state = verified["state"]
            if after_state != decision["expected_state_after"]:
                _fail("visual_expected_state_not_reached")
            if after_state == observation["state"]:
                _fail("visual_state_unchanged")
        except real_browser.RealBrowserError as exc:
            self._close_visual(session["session_id"])
            session["status"] = "failed"
            _fail(exc.code)
        except ServerError:
            self._close_visual(session["session_id"])
            session["status"] = "failed"
            raise
        finally:
            self._close_visual(session["session_id"])
        before_artifact = observation["artifact"]
        after_artifact = verified["artifacts"][0] if verified["artifacts"] else None
        after_image = verified["images"][0] if verified["images"] else None
        if after_artifact is None or after_image is None:
            session["status"] = "failed"
            _fail("visual_verification_missing_screenshot")
        session["status"] = "completed"
        evidence = {
            "schema": "kgg-ui-lab/visual-evidence/v1",
            "status": "PASS",
            "surface": "real_browser",
            "observation_id": observation["id"],
            "decision": {key: value for key, value in decision.items() if key != "text"},
            "state_before": observation["state"],
            "state_after": after_state,
            "artifacts": [before_artifact, after_artifact],
        }
        self.evidence.setdefault(session["session_id"], []).append(evidence)
        return {
            "schema": MCP_SCHEMA,
            "operation": "execute_visual_action",
            "result": {
                "status": "PASS",
                "action": {key: action[key] for key in ("expected", "actual", "status", "before_state", "after_state")},
                "state_before": observation["state"],
                "state_after": after_state,
                "artifacts": [before_artifact, after_artifact],
            },
            "evidence": evidence,
            "session_status": session["status"],
            "_images": [observation["image"], after_image],
        }

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
        if name == "observe_visual_state":
            return self.observe_visual(args.get("request"))
        if name == "execute_visual_action":
            return self.execute_visual_action(args.get("request"), args.get("decision"))
        if name == "run_width_sweep":
            return self.sweep(args.get("session_id"), args.get("actor"), args.get("viewports"))
        if name == "get_test_evidence":
            return self.evidence_read(args.get("session_id"), args.get("actor"))
        if name == "get_session_status":
            return self.status_read(args.get("session_id"), args.get("actor"))
        _fail("tool_not_found")


def _result_content(value: Mapping[str, Any]) -> dict[str, Any]:
    public = deepcopy(dict(value))
    images = public.pop("_images", [])
    encoded = json.dumps(public, ensure_ascii=False, separators=(",", ":"))
    content: list[dict[str, Any]] = [{"type": "text", "text": encoded}]
    if isinstance(images, list):
        for image in images[:2]:
            if isinstance(image, Mapping) and image.get("mime_type") == "image/png" and isinstance(image.get("data_base64"), str):
                content.append({"type": "image", "data": image["data_base64"], "mimeType": "image/png"})
    return {"content": content, "structuredContent": public}


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
