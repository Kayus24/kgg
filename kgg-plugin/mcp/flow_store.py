#!/usr/bin/env python3
"""Versioned, namespaced Quick-Flow storage for the portable UI-Lab plugin.

The store deliberately keeps built-in KGG certificates in reviewable plugin
source and persists only user-saved, synthetic flow definitions.  It never
stores screenshots, credentials, patient data, or live page contents.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
from typing import Any, Mapping


FLOW_SCHEMA = "kgg-ui-lab/flow/v1"
STORE_SCHEMA = "kgg-ui-lab/flow-store/v1"
BUILTIN_STORE = "BUILTIN_VERSIONED_FLOWS"
USER_STORE = "USER_SAVED_FLOWS"
FLOW_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._:-]{2,127}$")
VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
SAFE_TEXT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._:/-]{0,199}$")
FINGERPRINT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{2,199}$")
PLACEHOLDER_RE = re.compile(r"^\{\{[a-z][a-z0-9_.-]{0,63}\}\}$")
PROFILE_NAMES = {"tab-s9", "oppo-find-x9", "custom"}
OPERATIONS = {"click", "tap", "type", "scroll", "swipe", "wait", "observe", "read_state", "capture_screenshot"}
INTERACTIVE_OPERATIONS = {"click", "tap", "type", "swipe"}
TARGET_KINDS = {"action_id", "accessibility", "coordinate_fallback"}
SENSITIVE_TOKENS = (
    "raw_qr",
    "base64",
    "password",
    "api_key",
    "secret",
    "patient_data",
    "selector",
    "javascript",
    "css",
    "stack_trace",
    "token",
)


class FlowStoreError(ValueError):
    """Stable, safe flow-store error returned at the MCP boundary."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _fail(code: str) -> None:
    raise FlowStoreError(code)


def _object(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        _fail(f"{label}_invalid")
    return value


def _version(value: Any, label: str = "version") -> str:
    if not isinstance(value, str) or not VERSION_RE.fullmatch(value):
        _fail(f"{label}_invalid")
    return value


def _version_tuple(value: str) -> tuple[int, int, int]:
    return tuple(int(part) for part in value.split("."))  # type: ignore[return-value]


def _flow_id(value: Any, label: str = "flow_id") -> str:
    if not isinstance(value, str) or not FLOW_ID_RE.fullmatch(value):
        _fail(f"{label}_invalid")
    return value


def _safe_scan(value: Any) -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            lowered_key = str(key).casefold()
            if any(token in lowered_key for token in SENSITIVE_TOKENS):
                _fail("sensitive_field")
            _safe_scan(child)
    elif isinstance(value, list):
        for child in value:
            _safe_scan(child)
    elif isinstance(value, str):
        lowered = value.casefold()
        if any(token in lowered for token in SENSITIVE_TOKENS):
            _fail("sensitive_field")


def _safe_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not SAFE_TEXT_RE.fullmatch(value):
        _fail(f"{label}_invalid")
    return value


def _target(value: Any) -> dict[str, Any]:
    target = _object(value, "target")
    kind = target.get("kind")
    if kind not in TARGET_KINDS:
        _fail("target_kind_invalid")
    if kind == "action_id":
        if set(target) != {"kind", "value"}:
            _fail("target_invalid")
        _flow_id(target["value"], "target_value")
        return {"kind": kind, "value": target["value"]}
    if kind == "accessibility":
        if set(target) != {"kind", "role", "name"}:
            _fail("target_invalid")
        if target["role"] not in {"button", "link", "checkbox", "switch", "textbox"}:
            _fail("target_role_invalid")
        _safe_text(target["name"], "target_name")
        return {"kind": kind, "role": target["role"], "name": target["name"]}
    if set(target) != {"kind", "x", "y", "rationale"}:
        _fail("target_invalid")
    for coordinate in ("x", "y"):
        if not isinstance(target[coordinate], int) or isinstance(target[coordinate], bool) or target[coordinate] < 0:
            _fail("target_coordinate_invalid")
    rationale = target["rationale"]
    if not isinstance(rationale, str) or not rationale.strip() or len(rationale) > 200:
        _fail("target_fallback_rationale_invalid")
    return {"kind": kind, "x": target["x"], "y": target["y"], "rationale": rationale}


def _normalize_step(value: Any, expected_sequence: int) -> dict[str, Any]:
    raw = _object(value, "step")
    allowed = {"sequence", "operation", "label", "target", "expected_state", "text", "delta_y", "start", "end", "duration_ms", "timeout_ms"}
    if set(raw) - allowed:
        _fail("step_fields_invalid")
    if raw.get("sequence") != expected_sequence:
        _fail("step_sequence_invalid")
    operation = raw.get("operation")
    if operation not in OPERATIONS:
        _fail("step_operation_invalid")
    normalized: dict[str, Any] = {"sequence": expected_sequence, "operation": operation}
    normalized_target: dict[str, Any] | None = None
    if operation in INTERACTIVE_OPERATIONS:
        if "target" not in raw:
            _fail("target_required")
        normalized_target = _target(raw["target"])
    if "label" in raw:
        normalized["label"] = _safe_text(raw["label"], "step_label")
    elif operation in INTERACTIVE_OPERATIONS:
        if normalized_target["kind"] == "action_id":
            normalized["label"] = normalized_target["value"]
        elif normalized_target["kind"] == "accessibility":
            normalized["label"] = normalized_target["name"]
        else:
            normalized["label"] = operation
    if "expected_state" in raw:
        normalized["expected_state"] = _safe_text(raw["expected_state"], "expected_state")
    if operation in INTERACTIVE_OPERATIONS:
        normalized["target"] = normalized_target
    if operation == "type":
        text = raw.get("text")
        if not isinstance(text, str) or not PLACEHOLDER_RE.fullmatch(text):
            _fail("type_placeholder_required")
        normalized["text"] = text
    if operation == "scroll":
        delta = raw.get("delta_y", 500)
        if not isinstance(delta, int) or isinstance(delta, bool) or not -10000 <= delta <= 10000:
            _fail("scroll_delta_invalid")
        normalized["delta_y"] = delta
    if operation == "swipe":
        if "start" not in raw or "end" not in raw:
            _fail("swipe_points_required")
        points: dict[str, dict[str, int]] = {}
        for name in ("start", "end"):
            point = _object(raw[name], f"swipe_{name}")
            if set(point) != {"x", "y"} or any(not isinstance(point[key], int) or isinstance(point[key], bool) or point[key] < 0 for key in ("x", "y")):
                _fail("swipe_point_invalid")
            points[name] = {"x": point["x"], "y": point["y"]}
        if points["start"] == points["end"]:
            _fail("swipe_unchanged")
        duration = raw.get("duration_ms", 300)
        if not isinstance(duration, int) or isinstance(duration, bool) or not 50 <= duration <= 5000:
            _fail("swipe_duration_invalid")
        normalized.update(points, duration_ms=duration)
    if operation == "wait":
        timeout = raw.get("timeout_ms", 1000)
        if not isinstance(timeout, int) or isinstance(timeout, bool) or not 1 <= timeout <= 5000:
            _fail("wait_timeout_invalid")
        normalized["timeout_ms"] = timeout
    return normalized


def validate_flow(value: Any, *, expected_store: str | None = None) -> dict[str, Any]:
    raw = _object(value, "flow")
    required = {
        "schema", "flow_id", "name", "project", "scope", "store", "version", "status",
        "start_conditions", "steps", "expected_states", "toggle_states", "viewport_constraints",
        "device_constraints", "binding", "safety_class", "metadata",
    }
    if set(raw) != required:
        _fail("flow_schema_invalid")
    if raw["schema"] != FLOW_SCHEMA:
        _fail("flow_schema_invalid")
    _safe_scan(raw)
    flow_id = _flow_id(raw["flow_id"])
    name = _safe_text(raw["name"], "flow_name")
    project = _flow_id(raw["project"], "project")
    if raw["scope"] not in {"project", "user"}:
        _fail("flow_scope_invalid")
    if raw["store"] not in {BUILTIN_STORE, USER_STORE} or (expected_store and raw["store"] != expected_store):
        _fail("flow_store_invalid")
    version = _version(raw["version"])
    if raw["status"] not in {"active", "deprecated"}:
        _fail("flow_status_invalid")
    conditions = raw["start_conditions"]
    if not isinstance(conditions, list) or not 1 <= len(conditions) <= 20 or any(not isinstance(item, str) or not item or len(item) > 120 for item in conditions):
        _fail("start_conditions_invalid")
    steps = raw["steps"]
    if not isinstance(steps, list) or not 1 <= len(steps) <= 20:
        _fail("flow_steps_invalid")
    normalized_steps = [_normalize_step(item, index) for index, item in enumerate(steps, start=1)]
    expected_states = _object(raw["expected_states"], "expected_states")
    if set(expected_states) != {"intermediate", "final"} or not isinstance(expected_states["intermediate"], list) or any(not isinstance(item, str) or not item for item in expected_states["intermediate"]):
        _fail("expected_states_invalid")
    final_state = _safe_text(expected_states["final"], "final_state")
    toggle_states = _object(raw["toggle_states"], "toggle_states")
    if set(toggle_states) != {"before", "after"}:
        _fail("toggle_states_invalid")
    for phase in ("before", "after"):
        state = _object(toggle_states[phase], f"toggle_{phase}")
        if len(state) > 20 or any(not isinstance(key, str) or not isinstance(item, str) or not SAFE_TEXT_RE.fullmatch(key) or not SAFE_TEXT_RE.fullmatch(item) for key, item in state.items()):
            _fail("toggle_states_invalid")
    viewport = _object(raw["viewport_constraints"], "viewport_constraints")
    expected_viewport_keys = {"min_width", "max_width", "min_height", "max_height", "device_scale_factor"}
    if set(viewport) != expected_viewport_keys:
        _fail("viewport_constraints_invalid")
    for key in ("min_width", "max_width", "min_height", "max_height"):
        if not isinstance(viewport[key], int) or isinstance(viewport[key], bool) or not 240 <= viewport[key] <= 10000:
            _fail("viewport_constraints_invalid")
    if viewport["min_width"] > viewport["max_width"] or viewport["min_height"] > viewport["max_height"]:
        _fail("viewport_constraints_invalid")
    scale = viewport["device_scale_factor"]
    if not isinstance(scale, list) or len(scale) != 2 or any(not isinstance(item, (int, float)) or isinstance(item, bool) or not 0.5 <= item <= 4 for item in scale) or scale[0] > scale[1]:
        _fail("viewport_constraints_invalid")
    devices = raw["device_constraints"]
    if not isinstance(devices, list) or not devices or any(item not in PROFILE_NAMES for item in devices):
        _fail("device_constraints_invalid")
    binding = _object(raw["binding"], "binding")
    if set(binding) - {"source_fingerprint", "app_name"} or not isinstance(binding.get("source_fingerprint"), str) or not FINGERPRINT_RE.fullmatch(binding["source_fingerprint"]):
        _fail("flow_binding_invalid")
    if "app_name" in binding and binding["app_name"] not in {"admin", "patient"}:
        _fail("flow_binding_invalid")
    safety_class = _safe_text(raw["safety_class"], "safety_class")
    metadata = _object(raw["metadata"], "metadata")
    if metadata.get("synthetic") is not True or len(metadata) > 12:
        _fail("flow_metadata_invalid")
    return {
        "schema": FLOW_SCHEMA,
        "flow_id": flow_id,
        "name": name,
        "project": project,
        "scope": raw["scope"],
        "store": raw["store"],
        "version": version,
        "status": raw["status"],
        "start_conditions": list(conditions),
        "steps": normalized_steps,
        "expected_states": {"intermediate": list(expected_states["intermediate"]), "final": final_state},
        "toggle_states": {"before": dict(toggle_states["before"]), "after": dict(toggle_states["after"])},
        "viewport_constraints": deepcopy(dict(viewport)),
        "device_constraints": list(devices),
        "binding": deepcopy(dict(binding)),
        "safety_class": safety_class,
        "metadata": deepcopy(dict(metadata)),
    }


def _step(operation: str, sequence: int, label: str, *, expected_state: str | None = None, target: Mapping[str, Any] | None = None, **extra: Any) -> dict[str, Any]:
    value: dict[str, Any] = {"sequence": sequence, "operation": operation, "label": label}
    if expected_state is not None:
        value["expected_state"] = expected_state
    if target is not None:
        value["target"] = dict(target)
    value.update(extra)
    return value


def _builtin_flow(flow_id: str, name: str, app_name: str, steps: list[dict[str, Any]], intermediate: list[str], final: str) -> dict[str, Any]:
    return {
        "schema": FLOW_SCHEMA,
        "flow_id": flow_id,
        "name": name,
        "project": "kgg-ui-lab",
        "scope": "project",
        "store": BUILTIN_STORE,
        "version": "1.0.0",
        "status": "active",
        "start_conditions": ["synthetic-data-only", f"{app_name}-preview"],
        "steps": steps,
        "expected_states": {"intermediate": intermediate, "final": final},
        "toggle_states": {"before": {}, "after": {}},
        "viewport_constraints": {"min_width": 240, "max_width": 10000, "min_height": 240, "max_height": 10000, "device_scale_factor": [0.5, 4]},
        "device_constraints": ["tab-s9", "oppo-find-x9", "custom"],
        "binding": {"source_fingerprint": "kgg-ui-lab-real-fixture-v1", "app_name": app_name},
        "safety_class": "synthetic-bounded",
        "metadata": {"source": "release-pipeline/kgg_ui_lab_quick_flows.py", "synthetic": True},
    }


BUILTIN_VERSIONED_FLOWS: tuple[dict[str, Any], ...] = (
    _builtin_flow(
        "admin-start-baseline",
        "Admin start baseline",
        "admin",
        [_step("observe", 1, "admin-ready", expected_state="admin-ready"), _step("capture_screenshot", 2, "baseline-screen")],
        ["admin-ready"],
        "admin-ready",
    ),
    _builtin_flow(
        "pilot-180-reproduce",
        "Pilot 180 reproduce",
        "admin",
        [
            _step("observe", 1, "pilot-area-ready", expected_state="pilot-area-ready"),
            _step("capture_screenshot", 2, "baseline-screen"),
            _step("click", 3, "tablet-splitter-control", target={"kind": "action_id", "value": "tablet-splitter-control"}, expected_state="scale-drag-state"),
            _step("observe", 4, "scale-drag-state", expected_state="scale-drag-state"),
            _step("capture_screenshot", 5, "pilot-180-evidence"),
        ],
        ["pilot-area-ready", "scale-drag-state"],
        "scale-drag-state",
    ),
    _builtin_flow(
        "synthetic-qr-preview-link",
        "Synthetic QR preview link",
        "admin",
        [
            _step("observe", 1, "admin-preview-ready", expected_state="admin-preview-ready"),
            _step("capture_screenshot", 2, "baseline-screen"),
            _step("click", 3, "synthetic-qr-image", target={"kind": "action_id", "value": "synthetic-qr-image"}, expected_state="linked-preview-ready"),
            _step("observe", 4, "linked-preview-ready", expected_state="linked-preview-ready"),
            _step("capture_screenshot", 5, "preview-link-evidence"),
        ],
        ["admin-preview-ready", "linked-preview-ready"],
        "linked-preview-ready",
    ),
)


class FlowStore:
    """Atomic user-flow store over one plugin/project-namespaced JSON file."""

    def __init__(self, storage_path: str | Path | None = None) -> None:
        self.path = Path(storage_path) if storage_path is not None else self.default_path()
        self._user_flows = self._load()

    @staticmethod
    def default_path() -> Path:
        local_app_data = os.environ.get("LOCALAPPDATA")
        base = Path(local_app_data) if local_app_data else Path.home() / ".local" / "share"
        return base / "Codex" / "kgg-ui-lab" / "flows-v1.json"

    def _load(self) -> list[dict[str, Any]]:
        if not self.path.exists():
            return []
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            _fail("flow_store_corrupt")
        root = _object(raw, "flow_store")
        if set(root) != {"schema", "plugin", "flows"} or root["schema"] != STORE_SCHEMA or root["plugin"] != "kgg-ui-lab" or not isinstance(root["flows"], list):
            _fail("flow_store_corrupt")
        return [validate_flow(item, expected_store=USER_STORE) for item in root["flows"]]

    def _write(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_name(f".{self.path.name}.{os.getpid()}.tmp")
        payload = {"schema": STORE_SCHEMA, "plugin": "kgg-ui-lab", "flows": self._user_flows}
        try:
            temporary.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
            os.replace(temporary, self.path)
        finally:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass

    @staticmethod
    def _all_builtins() -> list[dict[str, Any]]:
        return [validate_flow(item, expected_store=BUILTIN_STORE) for item in BUILTIN_VERSIONED_FLOWS]

    @staticmethod
    def _matches(flow: Mapping[str, Any], ref: Mapping[str, Any]) -> bool:
        for key in ("flow_id", "project", "scope", "version"):
            if key in ref and ref[key] is not None and flow.get(key) != ref[key]:
                return False
        return True

    def list_flows(self, *, project: str | None = None, scope: str | None = None, include_deprecated: bool = False) -> list[dict[str, Any]]:
        if project is not None:
            _flow_id(project, "project")
        if scope is not None and scope not in {"project", "user"}:
            _fail("flow_scope_invalid")
        combined = self._all_builtins() + [deepcopy(item) for item in self._user_flows]
        return [
            deepcopy(item)
            for item in combined
            if (project is None or item["project"] == project)
            and (scope is None or item["scope"] == scope)
            and (include_deprecated or item["status"] == "active")
        ]

    def get(self, ref: Mapping[str, Any]) -> dict[str, Any]:
        flow_id = _flow_id(ref.get("flow_id"))
        project = _flow_id(ref.get("project"), "project")
        scope = ref.get("scope")
        if scope not in {"project", "user"}:
            _fail("flow_scope_invalid")
        version = ref.get("version")
        if version is not None:
            _version(version)
        candidates = [item for item in self.list_flows(project=project, scope=scope, include_deprecated=True) if item["flow_id"] == flow_id and (version is None or item["version"] == version)]
        if not candidates:
            _fail("flow_not_found")
        candidates.sort(key=lambda item: _version_tuple(item["version"]), reverse=True)
        return deepcopy(candidates[0])

    def save(self, flow: Any) -> dict[str, Any]:
        normalized = validate_flow(flow, expected_store=USER_STORE)
        ref = {key: normalized[key] for key in ("flow_id", "project", "scope", "version")}
        if any(self._matches(item, ref) for item in self._user_flows):
            _fail("flow_version_exists")
        self._user_flows.append(normalized)
        self._write()
        return deepcopy(normalized)

    def create_version(self, flow: Any) -> dict[str, Any]:
        normalized = validate_flow(flow, expected_store=USER_STORE)
        prior = [item for item in self._user_flows if item["flow_id"] == normalized["flow_id"] and item["project"] == normalized["project"] and item["scope"] == normalized["scope"]]
        if not prior:
            _fail("flow_not_found")
        if any(item["version"] == normalized["version"] for item in prior):
            _fail("flow_version_exists")
        highest = max(_version_tuple(item["version"]) for item in prior)
        if _version_tuple(normalized["version"]) <= highest:
            _fail("flow_version_must_increase")
        self._user_flows.append(normalized)
        self._write()
        return deepcopy(normalized)

    def deprecate(self, ref: Mapping[str, Any]) -> dict[str, Any]:
        flow = self.get(ref)
        if flow["store"] != USER_STORE:
            _fail("builtin_flow_immutable")
        for item in self._user_flows:
            if all(item[key] == flow[key] for key in ("flow_id", "project", "scope", "version")):
                item["status"] = "deprecated"
                self._write()
                return deepcopy(item)
        _fail("flow_not_found")

    def builtin(self, flow_id: str, version: str) -> dict[str, Any]:
        return self.get({"flow_id": flow_id, "project": "kgg-ui-lab", "scope": "project", "version": version})


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
