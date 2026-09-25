#!/usr/bin/env python3
"""Bounded stdio MCP server for the KGG UI-Lab candidate.

The server is intentionally self-contained so the installed marketplace copy
does not depend on the repository checkout.  Runtime/session/evidence state is
in memory; only explicitly saved synthetic Flow definitions use the bounded,
namespaced atomic store.  Synthetic evidence remains the default and the
server exposes the same bounded operations as the repository adapter.  There
is no shell, arbitrary browser, network, editor, ticket, preview, merge, or
external-message operation.
"""

from __future__ import annotations

import base64
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import struct
import sys
import time
from typing import Any, Mapping
from urllib.parse import urlparse
import zlib


PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "kgg-ui-lab"
SERVER_VERSION = "1.0.0"
MCP_SCHEMA = "kgg-ui-lab/mcp-server/v1"
SESSION_SCHEMA = "kgg-ui-lab/session/v1"
REQUEST_SCHEMA = "kgg-ui-lab/request/v1"
ACTORS = {"codex", "custom_gpt", "max", "system"}
PROFILES = {"tab-s9", "oppo-find-x9", "custom"}
CAPABILITIES = {"browser", "capture", "android", "quick_flows", "visual_loop", "width_sweep", "qr_image", "screen_recording"}
TOOL_NAMES = (
    "get_current_state",
    "get_ticket_state",
    "start_ui_session",
    "set_device_profile",
    "run_quick_flow",
    "capture_screenshot",
    "record_screen",
    "observe_visual_state",
    "execute_visual_action",
    "compare_visual_reference",
    "run_width_sweep",
    "get_test_evidence",
    "get_session_status",
    "save_flow",
    "list_flows",
    "get_flow",
    "run_flow",
    "create_new_version",
    "deprecate_flow",
)
ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{5,63}$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
REFERENCE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{2,127}$")
VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
SENSITIVE = ("raw_qr", "base64", "password", "api_key", "secret", "patient_data", "selector", "stack_trace", "token")
MAX_REFERENCE_BYTES = 2 * 1024 * 1024
MAX_REFERENCE_PIXELS = 10_000_000
MAX_RECORDING_DURATION_MS = 10_000
MIN_RECORDING_FRAME_INTERVAL_MS = 50
MAX_RECORDING_FRAME_INTERVAL_MS = 2_000
MAX_RECORDING_FRAMES = 128


def _app_url_allowed(value: Any, bootstrap: Any) -> bool:
    parsed = urlparse(str(value))
    if parsed.username or parsed.password or parsed.fragment:
        return False
    if parsed.scheme == "http":
        return parsed.hostname in {"localhost", "127.0.0.1"} and bool(parsed.netloc)
    if parsed.scheme != "https" or not bool(parsed.netloc):
        return False
    if not bootstrap.enabled:
        # Synthetic mode keeps its historical contract fixtures; the real
        # browser boundary applies the configured project policy below.
        return True
    return bootstrap.policy.allows_url(str(value))


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
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        return module


def _load_flow_store_module():
    """Load the sibling persistent-flow module for installed and test imports."""

    try:
        import flow_store  # type: ignore
        return flow_store
    except ModuleNotFoundError:
        module_path = Path(__file__).with_name("flow_store.py")
        spec = importlib.util.spec_from_file_location("kgg_plugin_flow_store", module_path)
        if spec is None or spec.loader is None:
            _fail("flow_store_helper_missing")
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
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


def _decode_png(image_data: Any, label: str) -> tuple[int, int, bytes]:
    if not isinstance(image_data, str) or len(image_data) > MAX_REFERENCE_BYTES * 2:
        _fail(f"{label}_invalid")
    try:
        raw = base64.b64decode(image_data, validate=True)
    except (ValueError, TypeError):
        _fail(f"{label}_invalid")
    if len(raw) < 33 or len(raw) > MAX_REFERENCE_BYTES or raw[:8] != b"\x89PNG\r\n\x1a\n":
        _fail(f"{label}_invalid")
    offset = 8
    width = height = color_type = bit_depth = interlace = None
    compressed = bytearray()
    while offset + 12 <= len(raw):
        length = struct.unpack(">I", raw[offset:offset + 4])[0]
        chunk_end = offset + 12 + length
        if chunk_end > len(raw):
            _fail(f"{label}_invalid")
        chunk_type = raw[offset + 4:offset + 8]
        chunk = raw[offset + 8:offset + 8 + length]
        if chunk_type == b"IHDR":
            if length != 13:
                _fail(f"{label}_invalid")
            width, height, bit_depth, color_type, compression, filter_method, interlace = struct.unpack(">IIBBBBB", chunk)
            if compression != 0 or filter_method != 0:
                _fail(f"{label}_invalid")
        elif chunk_type == b"IDAT":
            compressed.extend(chunk)
        elif chunk_type == b"IEND":
            break
        offset = chunk_end
    if not all(isinstance(value, int) for value in (width, height, bit_depth, color_type, interlace)):
        _fail(f"{label}_invalid")
    if width < 1 or height < 1 or width * height > MAX_REFERENCE_PIXELS or bit_depth != 8 or color_type not in {2, 6} or interlace != 0:
        _fail(f"{label}_unsupported")
    channels = 4 if color_type == 6 else 3
    row_bytes = width * channels
    expected_size = height * (row_bytes + 1)
    try:
        scanlines = zlib.decompress(bytes(compressed))
    except zlib.error:
        _fail(f"{label}_invalid")
    if len(scanlines) != expected_size:
        _fail(f"{label}_invalid")

    def paeth(left: int, up: int, upper_left: int) -> int:
        estimate = left + up - upper_left
        distances = (abs(estimate - left), abs(estimate - up), abs(estimate - upper_left))
        return (left, up, upper_left)[distances.index(min(distances))]

    pixels = bytearray()
    previous = bytearray(row_bytes)
    for row_index in range(height):
        start = row_index * (row_bytes + 1)
        filter_type = scanlines[start]
        row = bytearray(scanlines[start + 1:start + 1 + row_bytes])
        for index in range(row_bytes):
            left = row[index - channels] if index >= channels else 0
            up = previous[index]
            upper_left = previous[index - channels] if index >= channels else 0
            if filter_type == 1:
                row[index] = (row[index] + left) & 0xFF
            elif filter_type == 2:
                row[index] = (row[index] + up) & 0xFF
            elif filter_type == 3:
                row[index] = (row[index] + ((left + up) // 2)) & 0xFF
            elif filter_type == 4:
                row[index] = (row[index] + paeth(left, up, upper_left)) & 0xFF
            elif filter_type != 0:
                _fail(f"{label}_unsupported")
        if channels == 4:
            pixels.extend(row)
        else:
            for index in range(0, row_bytes, 3):
                pixels.extend((row[index], row[index + 1], row[index + 2], 255))
        previous = row
    return width, height, bytes(pixels)


def _comparison_viewport(value: Any, session: Mapping[str, Any]) -> dict[str, Any]:
    viewport = _object(value, "reference_viewport")
    if set(viewport) != {"width", "height", "device_scale_factor"}:
        _fail("reference_viewport_invalid")
    expected = session["viewport"]
    if viewport["width"] != expected["width"] or viewport["height"] != expected["height"] or viewport["device_scale_factor"] != expected["device_scale_factor"]:
        _fail("reference_viewport_mismatch")
    if not all(isinstance(viewport[key], int) and not isinstance(viewport[key], bool) for key in ("width", "height")):
        _fail("reference_viewport_invalid")
    if not isinstance(viewport["device_scale_factor"], (int, float)) or isinstance(viewport["device_scale_factor"], bool):
        _fail("reference_viewport_invalid")
    return {"width": viewport["width"], "height": viewport["height"], "device_scale_factor": viewport["device_scale_factor"]}


def _comparison_threshold(value: Any) -> dict[str, Any]:
    threshold = _object(value, "reference_threshold")
    if set(threshold) != {"max_changed_pixels", "max_changed_ratio", "pixel_delta"}:
        _fail("reference_threshold_invalid")
    max_pixels = threshold["max_changed_pixels"]
    ratio = threshold["max_changed_ratio"]
    pixel_delta = threshold["pixel_delta"]
    if not isinstance(max_pixels, int) or isinstance(max_pixels, bool) or not 0 <= max_pixels <= MAX_REFERENCE_PIXELS:
        _fail("reference_threshold_invalid")
    if not isinstance(ratio, (int, float)) or isinstance(ratio, bool) or not 0 <= ratio <= 1:
        _fail("reference_threshold_invalid")
    if not isinstance(pixel_delta, int) or isinstance(pixel_delta, bool) or not 0 <= pixel_delta <= 255:
        _fail("reference_threshold_invalid")
    return {"max_changed_pixels": max_pixels, "max_changed_ratio": ratio, "pixel_delta": pixel_delta}


def _comparison_masks(value: Any, viewport: Mapping[str, Any]) -> list[dict[str, int]]:
    if value is None:
        return []
    if not isinstance(value, list) or len(value) > 10:
        _fail("reference_masks_invalid")
    masks: list[dict[str, int]] = []
    for raw in value:
        mask = _object(raw, "reference_mask")
        if set(mask) != {"x", "y", "width", "height"}:
            _fail("reference_masks_invalid")
        if not all(isinstance(mask[key], int) and not isinstance(mask[key], bool) for key in ("x", "y", "width", "height")):
            _fail("reference_masks_invalid")
        if mask["x"] < 0 or mask["y"] < 0 or mask["width"] < 1 or mask["height"] < 1 or mask["x"] + mask["width"] > viewport["width"] or mask["y"] + mask["height"] > viewport["height"]:
            _fail("reference_masks_invalid")
        masks.append({key: mask[key] for key in ("x", "y", "width", "height")})
    return masks


def _visual_reference(value: Any, session: Mapping[str, Any]) -> dict[str, Any]:
    reference = _object(value, "reference")
    allowed = {"reference_class", "reference_id", "reference_sha256", "content_type", "image_data", "approval_id", "observation_id", "viewport", "threshold", "masks"}
    required = {"reference_class", "reference_id", "reference_sha256", "viewport", "threshold"}
    if set(reference) - allowed or not required.issubset(reference):
        _fail("reference_invalid")
    reference_class = reference["reference_class"]
    if reference_class not in {"explicit_artifact", "approved_golden", "fixture_screenshot"}:
        _fail("reference_class_invalid")
    reference_id = reference["reference_id"]
    if not isinstance(reference_id, str) or not REFERENCE_ID_RE.fullmatch(reference_id):
        _fail("reference_id_invalid")
    reference_sha256 = _sha256(reference["reference_sha256"], "reference_sha256")
    viewport = _comparison_viewport(reference["viewport"], session)
    threshold = _comparison_threshold(reference["threshold"])
    masks = _comparison_masks(reference.get("masks"), viewport)
    image_data: str | None = None
    approval_id: str | None = None
    if reference_class == "fixture_screenshot":
        observation_id = _sha256(reference.get("observation_id"), "reference_observation_id")
        history = session.get("visual_observations")
        stored = history.get(observation_id) if isinstance(history, Mapping) else None
        stored_artifact = stored.get("artifact") if isinstance(stored, Mapping) else None
        if not isinstance(stored_artifact, Mapping) or stored_artifact.get("id") != reference_id:
            _fail("reference_provenance_invalid")
        artifact = stored_artifact
        image = stored.get("image")
        if not isinstance(artifact, Mapping) or artifact.get("sha256") != reference_sha256 or not isinstance(image, Mapping):
            _fail("reference_provenance_invalid")
        image_data = image.get("data_base64")
    else:
        if reference.get("content_type", "image/png") != "image/png":
            _fail("reference_content_type_invalid")
        image_data = reference.get("image_data")
        if not isinstance(image_data, str):
            _fail("reference_image_missing")
        try:
            decoded = base64.b64decode(image_data, validate=True)
        except (ValueError, TypeError):
            _fail("reference_image_invalid")
        if hashlib.sha256(decoded).hexdigest() != reference_sha256:
            _fail("reference_hash_mismatch")
        if reference_class == "approved_golden":
            approval_id = reference.get("approval_id")
            if not isinstance(approval_id, str) or not re.fullmatch(r"approved:[A-Za-z0-9._:-]{3,120}", approval_id):
                _fail("reference_approval_invalid")
    if not isinstance(image_data, str):
        _fail("reference_image_missing")
    _decode_png(image_data, "reference_image")
    return {
        "reference_class": reference_class,
        "reference_id": reference_id,
        "reference_sha256": reference_sha256,
        "image_data": image_data,
        "viewport": viewport,
        "threshold": threshold,
        "masks": masks,
        "approval_id": approval_id,
    }


def _compare_visual_images(current: Mapping[str, Any], reference: Mapping[str, Any]) -> dict[str, Any]:
    current_data = current.get("data_base64")
    if not isinstance(current_data, str):
        _fail("visual_current_image_missing")
    current_width, current_height, current_pixels = _decode_png(current_data, "current_image")
    reference_width, reference_height, reference_pixels = _decode_png(reference["image_data"], "reference_image")
    structural_issues: list[str] = []
    if (current_width, current_height) != (reference_width, reference_height):
        structural_issues.append("image_dimensions")
    masks = reference["masks"]
    expected_dynamic_pixels = 0
    changed_pixels = 0
    if not structural_issues:
        pixel_delta = reference["threshold"]["pixel_delta"]
        for index in range(current_width * current_height):
            current_pixel = current_pixels[index * 4:index * 4 + 4]
            reference_pixel = reference_pixels[index * 4:index * 4 + 4]
            difference = max(abs(current_pixel[channel] - reference_pixel[channel]) for channel in range(4))
            if difference <= pixel_delta:
                continue
            x = index % current_width
            y = index // current_width
            masked = any(mask["x"] <= x < mask["x"] + mask["width"] and mask["y"] <= y < mask["y"] + mask["height"] for mask in masks)
            if masked:
                expected_dynamic_pixels += 1
            else:
                changed_pixels += 1
    total_pixels = current_width * current_height if not structural_issues else 0
    changed_ratio = changed_pixels / total_pixels if total_pixels else 1.0
    threshold = reference["threshold"]
    visual_pass = not structural_issues and changed_pixels <= threshold["max_changed_pixels"] and changed_ratio <= threshold["max_changed_ratio"]
    classes: list[str] = []
    if structural_issues:
        classes.append("STRUCTURAL_DIFFERENCE")
    if not visual_pass and not structural_issues:
        classes.append("VISUAL_DIFFERENCE")
    if expected_dynamic_pixels:
        classes.append("EXPECTED_DYNAMIC_DIFFERENCE")
    return {
        "status": "PASS" if visual_pass else "FAIL",
        "difference_classes": classes,
        "structural": {"status": "FAIL" if structural_issues else "PASS", "issues": structural_issues},
        "visual": {"status": "PASS" if visual_pass else "FAIL", "changed_pixels": changed_pixels, "changed_ratio": changed_ratio, "threshold": deepcopy(threshold)},
        "expected_dynamic": {"status": "OBSERVED" if expected_dynamic_pixels else "NONE", "changed_pixels": expected_dynamic_pixels, "mask_count": len(masks)},
        "image_dimensions": {"current": {"width": current_width, "height": current_height}, "reference": {"width": reference_width, "height": reference_height}},
    }


def _visual_decision(value: Any) -> dict[str, Any]:
    decision = _object(value, "decision")
    allowed = {"operation", "label", "coordinates", "start", "end", "duration_ms", "text", "delta_y", "timeout_ms", "expected_state_after", "observation_id"}
    if set(decision) - allowed or not {"operation", "label", "expected_state_after", "observation_id"}.issubset(decision):
        _fail("visual_decision_invalid")
    operation = decision["operation"]
    if operation not in {"click", "tap", "type", "scroll", "wait", "swipe"}:
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
    if operation == "swipe":
        if "start" not in decision or "end" not in decision:
            _fail("visual_decision_invalid")
        points: dict[str, dict[str, int]] = {}
        for name in ("start", "end"):
            point = _object(decision[name], name)
            if set(point) != {"x", "y"} or not all(isinstance(point[key], int) and not isinstance(point[key], bool) and point[key] >= 0 for key in ("x", "y")):
                _fail("visual_decision_invalid")
            points[name] = {"x": point["x"], "y": point["y"]}
        duration = decision.get("duration_ms", 300)
        if not isinstance(duration, int) or isinstance(duration, bool) or not 50 <= duration <= 5000:
            _fail("visual_decision_invalid")
        normalized.update(points)
        normalized["duration_ms"] = duration
    return normalized


def _validate_swipe_bounds(decision: Mapping[str, Any], viewport: Mapping[str, Any]) -> None:
    if decision.get("operation") != "swipe":
        return
    start = decision["start"]
    end = decision["end"]
    width = viewport["width"]
    height = viewport["height"]
    if any(point[axis] >= limit for point in (start, end) for axis, limit in (("x", width), ("y", height))):
        _fail("swipe_bounds_invalid")
    if start == end:
        _fail("swipe_unchanged")


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


def _tool(
    name: str,
    description: str,
    properties: Mapping[str, Any],
    required: list[str],
    *,
    read_only: bool,
    destructive: bool,
    idempotent: bool,
    open_world: bool,
) -> dict[str, Any]:
    return {
        "name": name,
        "description": description,
        "inputSchema": {"type": "object", "properties": dict(properties), "required": required, "additionalProperties": False},
        "annotations": {
            "readOnlyHint": read_only,
            "destructiveHint": destructive,
            "idempotentHint": idempotent,
            "openWorldHint": open_world,
        },
    }


def tool_catalog() -> list[dict[str, Any]]:
    actor = {"type": "string", "enum": sorted(ACTORS)}
    session_id = {"type": "string", "pattern": "^[a-z0-9][a-z0-9-]{5,63}$"}
    request = {
        "type": "object",
        "description": "kgg-ui-lab/request/v1 object; no sensitive fields",
        "properties": {
            "schema": {"type": "string", "const": REQUEST_SCHEMA},
            "request_id": session_id,
            "session_id": session_id,
            "actor": actor,
            "operation": {
                "type": "string",
                "enum": ["run_quick_flow", "capture_screenshot", "record_screen", "observe_visual_state", "execute_visual_action", "compare_visual_reference", "run_flow"],
            },
            "main_sha": {"type": "string", "pattern": "^[0-9a-f]{40}$"},
            "payload_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        },
        "required": ["schema", "request_id", "session_id", "actor", "operation", "main_sha", "payload_sha256"],
        "additionalProperties": False,
    }
    session = {
        "type": "object",
        "description": "kgg-ui-lab/session/v1 object; synthetic or explicitly opt-in real-browser session",
        "properties": {
            "schema": {"type": "string", "const": SESSION_SCHEMA},
            "session_id": session_id,
            "status": {"type": "string"},
            "active_actor": actor,
            "request_id": {"type": "string", "pattern": "^[a-z0-9][a-z0-9-]{5,63}$"},
            "lease": {
                "type": "object",
                "properties": {
                    "owner": actor,
                    "issued_at": {"type": "string", "format": "date-time"},
                    "expires_at": {"type": "string", "format": "date-time"},
                },
                "required": ["owner", "issued_at", "expires_at"],
                "additionalProperties": False,
            },
            "runner": {
                "type": "object",
                "properties": {
                    "runner_id": {"type": "string", "pattern": "^[a-z0-9][a-z0-9-]{5,63}$"},
                    "version": {"type": "string", "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+$"},
                    "browser_revision": {"type": "string", "minLength": 1},
                    "capabilities": {"type": "array", "items": {"type": "string", "enum": sorted(CAPABILITIES)}, "minItems": 1, "uniqueItems": True},
                },
                "required": ["runner_id", "version", "browser_revision", "capabilities"],
                "additionalProperties": False,
            },
            "app": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "enum": ["admin", "patient"]},
                    "url": {
                        "type": "string",
                        "format": "uri",
                        "description": "Raw URI string only; do not wrap it in Markdown link syntax.",
                    },
                    "main_sha": {"type": "string", "pattern": "^[0-9a-f]{40}$"},
                    "preview_sha": {"anyOf": [{"type": "string", "pattern": "^[0-9a-f]{40}$"}, {"type": "null"}]},
                },
                "required": ["name", "url", "main_sha", "preview_sha"],
                "additionalProperties": False,
            },
            "device_profile": {"type": "string", "enum": sorted(PROFILES)},
            "viewport": {
                "type": "object",
                "properties": {
                    "width": {"type": "integer", "minimum": 240, "maximum": 10000},
                    "height": {"type": "integer", "minimum": 240, "maximum": 10000},
                    "device_scale_factor": {"type": "number", "minimum": 0.5, "maximum": 4},
                },
                "required": ["width", "height", "device_scale_factor"],
                "additionalProperties": False,
            },
            "quick_flow": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "minLength": 1},
                    "version": {"type": "string", "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+$"},
                },
                "required": ["name", "version"],
                "additionalProperties": False,
            },
            "timeout": {
                "type": "object",
                "properties": {
                    "timeout_ms": {"type": "integer", "minimum": 1000, "maximum": 1800000},
                    "cleanup_on_cancel": {"type": "boolean"},
                },
                "required": ["timeout_ms", "cleanup_on_cancel"],
                "additionalProperties": False,
            },
            "artifacts": {"type": "array", "items": {"type": "object"}},
        },
        "required": ["schema", "session_id", "status", "active_actor", "request_id", "lease", "runner", "app", "device_profile", "viewport", "quick_flow", "timeout", "artifacts"],
        "additionalProperties": False,
    }
    visual_decision = {
        "type": "object",
        "description": "One bounded agent decision derived from the previously returned screenshot; no selectors or JavaScript.",
        "properties": {
            "operation": {"type": "string", "enum": ["click", "tap", "type", "scroll", "wait", "swipe"]},
            "label": {"type": "string", "pattern": "^[A-Za-z0-9][A-Za-z0-9 ._:/-]{0,199}$"},
            "coordinates": {"type": "object", "properties": {"x": {"type": "integer", "minimum": 0}, "y": {"type": "integer", "minimum": 0}}, "required": ["x", "y"], "additionalProperties": False},
            "start": {"type": "object", "properties": {"x": {"type": "integer", "minimum": 0}, "y": {"type": "integer", "minimum": 0}}, "required": ["x", "y"], "additionalProperties": False},
            "end": {"type": "object", "properties": {"x": {"type": "integer", "minimum": 0}, "y": {"type": "integer", "minimum": 0}}, "required": ["x", "y"], "additionalProperties": False},
            "duration_ms": {"type": "integer", "minimum": 50, "maximum": 5000},
            "text": {"type": "string", "maxLength": 200},
            "delta_y": {"type": "integer", "minimum": -10000, "maximum": 10000},
            "timeout_ms": {"type": "integer", "minimum": 1, "maximum": 5000},
            "expected_state_after": {"type": "string", "pattern": "^[A-Za-z0-9][A-Za-z0-9 ._:/-]{0,199}$"},
            "observation_id": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        },
        "required": ["operation", "label", "expected_state_after", "observation_id"],
        "additionalProperties": False,
    }
    visual_reference = {
        "type": "object",
        "description": "An explicitly transferred PNG, approved golden, or earlier screenshot from the same fixture; no implicit chat upload or filesystem lookup.",
        "properties": {
            "reference_class": {"type": "string", "enum": ["explicit_artifact", "approved_golden", "fixture_screenshot"]},
            "reference_id": {"type": "string", "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{2,127}$"},
            "reference_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
            "content_type": {"type": "string", "const": "image/png"},
            "image_data": {"type": "string", "maxLength": MAX_REFERENCE_BYTES * 2},
            "approval_id": {"type": "string", "pattern": "^approved:[A-Za-z0-9._:-]{3,120}$"},
            "observation_id": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
            "viewport": {"type": "object", "properties": {"width": {"type": "integer", "minimum": 240, "maximum": 10000}, "height": {"type": "integer", "minimum": 240, "maximum": 10000}, "device_scale_factor": {"type": "number", "minimum": 0.5, "maximum": 4}}, "required": ["width", "height", "device_scale_factor"], "additionalProperties": False},
            "threshold": {"type": "object", "properties": {"max_changed_pixels": {"type": "integer", "minimum": 0, "maximum": MAX_REFERENCE_PIXELS}, "max_changed_ratio": {"type": "number", "minimum": 0, "maximum": 1}, "pixel_delta": {"type": "integer", "minimum": 0, "maximum": 255}}, "required": ["max_changed_pixels", "max_changed_ratio", "pixel_delta"], "additionalProperties": False},
            "masks": {"type": "array", "maxItems": 10, "items": {"type": "object", "properties": {"x": {"type": "integer", "minimum": 0}, "y": {"type": "integer", "minimum": 0}, "width": {"type": "integer", "minimum": 1}, "height": {"type": "integer", "minimum": 1}}, "required": ["x", "y", "width", "height"], "additionalProperties": False}},
        },
        "required": ["reference_class", "reference_id", "reference_sha256", "viewport", "threshold"],
        "additionalProperties": False,
    }
    flow_id = {"type": "string", "pattern": "^[a-z0-9][a-z0-9._:-]{2,127}$"}
    flow_ref = {
        "type": "object",
        "properties": {
            "flow_id": flow_id,
            "project": flow_id,
            "scope": {"type": "string", "enum": ["project", "user"]},
            "version": {"type": "string", "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+$"},
        },
        "required": ["flow_id", "project", "scope"],
        "additionalProperties": False,
    }
    flow_document = {
        "type": "object",
        "description": "kgg-ui-lab/flow/v1; versioned, synthetic, namespaced flow definition with stable action targets and drift binding.",
        "properties": {
            "schema": {"type": "string", "const": "kgg-ui-lab/flow/v1"},
            "flow_id": flow_id,
            "name": {"type": "string", "minLength": 1, "maxLength": 200},
            "project": flow_id,
            "scope": {"type": "string", "enum": ["project", "user"]},
            "store": {"type": "string", "enum": ["USER_SAVED_FLOWS", "BUILTIN_VERSIONED_FLOWS"]},
            "version": {"type": "string", "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+$"},
            "status": {"type": "string", "enum": ["active", "deprecated"]},
            "start_conditions": {"type": "array", "minItems": 1, "maxItems": 20, "items": {"type": "string", "maxLength": 120}},
            "steps": {"type": "array", "minItems": 1, "maxItems": 20, "items": {"type": "object"}},
            "expected_states": {"type": "object"},
            "toggle_states": {"type": "object"},
            "viewport_constraints": {"type": "object"},
            "device_constraints": {"type": "array", "items": {"type": "string", "enum": sorted(PROFILES)}},
            "binding": {"type": "object"},
            "safety_class": {"type": "string", "maxLength": 200},
            "metadata": {"type": "object"},
        },
        "required": ["schema", "flow_id", "name", "project", "scope", "store", "version", "status", "start_conditions", "steps", "expected_states", "toggle_states", "viewport_constraints", "device_constraints", "binding", "safety_class", "metadata"],
        "additionalProperties": False,
    }
    run_flow_request = {
        "type": "object",
        "properties": {
            "request": request,
            "flow_id": flow_id,
            "project": flow_id,
            "scope": {"type": "string", "enum": ["project", "user"]},
            "version": {"type": "string", "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+$"},
            "binding_fingerprint": {"type": "string", "minLength": 3, "maxLength": 200},
            "toggle_states": {"type": "object"},
            "parameters": {"type": "object"},
        },
        "required": ["request", "flow_id", "project", "scope", "version", "binding_fingerprint"],
        "additionalProperties": False,
    }
    record_screen_request = {
        "type": "object",
        "description": "Opt-in bounded viewport trace. The current host returns timestamped PNG keyframes; it does not claim a video artifact.",
        "properties": {
            "request": request,
            "duration_ms": {"type": "integer", "minimum": 100, "maximum": MAX_RECORDING_DURATION_MS},
            "frame_interval_ms": {"type": "integer", "minimum": MIN_RECORDING_FRAME_INTERVAL_MS, "maximum": MAX_RECORDING_FRAME_INTERVAL_MS},
        },
        "required": ["request", "duration_ms", "frame_interval_ms"],
        "additionalProperties": False,
    }
    return [
        _tool("get_current_state", "Read bounded synthetic UI-Lab state. Never writes or reaches a browser.", {"actor": actor}, ["actor"], read_only=True, destructive=False, idempotent=True, open_world=False),
        _tool("get_ticket_state", "Read a bounded synthetic ticket summary only. Never writes, dispatches, or reaches a ticket system.", {"actor": actor, "ticket_id": {"type": "string", "pattern": "^#?[0-9]{1,6}$"}}, ["actor", "ticket_id"], read_only=True, destructive=False, idempotent=True, open_world=False),
        _tool("start_ui_session", "Create or replace an in-memory session binding actor, lease, runner, and caller-supplied Fresh-Main SHA; it does not open a browser or write app/repository data.", {"session": session}, ["session"], read_only=False, destructive=False, idempotent=False, open_world=False),
        _tool("set_device_profile", "Change only the in-memory device profile of an active session; no app or repository write occurs.", {"session_id": session_id, "actor": actor, "profile": {"type": "string", "enum": sorted(PROFILES)}}, ["session_id", "actor", "profile"], read_only=False, destructive=False, idempotent=True, open_world=False),
        _tool("run_quick_flow", "Run the bounded synthetic Quick Flow, or allowlisted browser steps when the opt-in real-browser host is enabled; record sanitized evidence and never write the repository.", {"request": request}, ["request"], read_only=False, destructive=False, idempotent=False, open_world=True),
        _tool("capture_screenshot", "Return a deterministic synthetic screenshot, or capture from the session app URL when the opt-in real-browser host is enabled; record evidence and never write the repository.", {"request": request}, ["request"], read_only=False, destructive=False, idempotent=False, open_world=True),
        _tool("record_screen", "Opt-in, origin-allowlisted, session-bound viewport trace with a hard duration cap; return traceable timestamped PNG keyframes when video transport is unavailable, never a false video-success claim or a continuous recording.", record_screen_request["properties"], ["request", "duration_ms", "frame_interval_ms"], read_only=False, destructive=False, idempotent=False, open_world=True),
        _tool("observe_visual_state", "When the opt-in real-browser host is enabled, observe one screenshot and state from a persistent bounded browser page; store the observation and evidence for the caller's next action.", {"request": request}, ["request"], read_only=False, destructive=False, idempotent=False, open_world=True),
        _tool("execute_visual_action", "When the opt-in real-browser host is enabled, execute exactly one bounded caller-supplied action in the same page; it may change app state and returns a second screenshot plus state verification.", {"request": request, "decision": visual_decision}, ["request", "decision"], read_only=False, destructive=True, idempotent=False, open_world=True),
        _tool("compare_visual_reference", "Compare the latest observed real-browser screenshot against an explicitly transferred, approved, or same-fixture reference PNG with exact viewport, mask, threshold, hash, and pixel-diff evidence; never infer a reference from an upload or filesystem.", {"request": request, "reference": visual_reference}, ["request", "reference"], read_only=False, destructive=False, idempotent=False, open_world=True),
        _tool("run_width_sweep", "Validate a bounded viewport list and return PREVIEW_ONLY in memory; no browser run or screenshot comparison is performed.", {"session_id": session_id, "actor": actor, "viewports": {"type": "array", "maxItems": 10}}, ["session_id", "actor", "viewports"], read_only=True, destructive=False, idempotent=True, open_world=False),
        _tool("get_test_evidence", "Read sanitized in-memory evidence for a session; never writes or dispatches.", {"session_id": session_id, "actor": actor}, ["session_id", "actor"], read_only=True, destructive=False, idempotent=True, open_world=False),
        _tool("get_session_status", "Read sanitized in-memory session status and event count; never writes or dispatches.", {"session_id": session_id, "actor": actor}, ["session_id", "actor"], read_only=True, destructive=False, idempotent=True, open_world=False),
        _tool("save_flow", "Persist one new user-saved synthetic Flow atomically in its project namespace; published versions are never silently overwritten.", {"flow": flow_document}, ["flow"], read_only=False, destructive=False, idempotent=False, open_world=False),
        _tool("list_flows", "List built-in and user-saved versioned Flows by project and scope; deprecated versions are hidden unless explicitly requested.", {"project": flow_id, "scope": {"type": "string", "enum": ["project", "user"]}, "include_deprecated": {"type": "boolean"}}, ["project", "scope"], read_only=True, destructive=False, idempotent=True, open_world=False),
        _tool("get_flow", "Read one exact versioned Flow definition without opening a browser or returning stored user data.", {"flow": flow_ref}, ["flow"], read_only=True, destructive=False, idempotent=True, open_world=False),
        _tool("run_flow", "Run one exact persisted Flow only when its source fingerprint, viewport/device constraints, toggle preconditions, and stable targets match; drift fails closed.", run_flow_request["properties"], ["request", "flow_id", "project", "scope", "version", "binding_fingerprint"], read_only=False, destructive=True, idempotent=False, open_world=True),
        _tool("create_new_version", "Create a higher append-only version of an existing user Flow; it never edits a published version in place.", {"flow": flow_document}, ["flow"], read_only=False, destructive=False, idempotent=False, open_world=False),
        _tool("deprecate_flow", "Explicitly deprecate one user-saved Flow version so it is excluded from normal replay listings.", {"flow": flow_ref}, ["flow"], read_only=False, destructive=False, idempotent=False, open_world=False),
    ]


class Runtime:
    def __init__(self, *, browser_bootstrap: Any | None = None, flow_store_path: str | Path | None = None) -> None:
        self.sessions: dict[str, dict[str, Any]] = {}
        self.evidence: dict[str, list[dict[str, Any]]] = {}
        self.visual_sessions: dict[str, Any] = {}
        self.call_count = 0
        self.read_count = 0
        self.started_perf: float | None = None
        real_browser = _load_real_browser_module()
        self.browser_bootstrap = browser_bootstrap or real_browser.BrowserBootstrap.synthetic()
        self.flow_store_module = _load_flow_store_module()
        self.flow_store = self.flow_store_module.FlowStore(flow_store_path)

    def _close_visual(self, session_id: str) -> None:
        browser = self.visual_sessions.pop(session_id, None)
        if browser is not None:
            try:
                browser.close()
            except Exception:  # noqa: BLE001 - cleanup must never mask the gate result
                pass

    def _record_visual_observation(
        self,
        session: Mapping[str, Any],
        observed: Mapping[str, Any],
        *,
        evidence_status: str = "OBSERVED",
        flow_status: str | None = None,
    ) -> dict[str, Any]:
        artifacts = observed.get("artifacts")
        images = observed.get("images")
        artifact = artifacts[0] if isinstance(artifacts, list) and artifacts else None
        image = images[0] if isinstance(images, list) and images else None
        if not isinstance(artifact, Mapping) or not isinstance(image, Mapping):
            _fail("visual_observation_missing_screenshot")
        state = str(observed.get("state", "unknown"))
        observation_id = hashlib.sha256(f"{session['session_id']}|{artifact['sha256']}|{state}".encode("utf-8")).hexdigest()
        public_observation = {
            "id": observation_id,
            "state": state,
            "artifact": dict(artifact),
            "fallback": flow_status == "STALE_REQUIRES_REVIEW",
        }
        stored_observation = {**public_observation, "image": dict(image)}
        session["visual_observation"] = stored_observation
        history = session.setdefault("visual_observations", {})
        history[observation_id] = stored_observation
        while len(history) > 20:
            history.pop(next(iter(history)))
        evidence: dict[str, Any] = {
            "schema": "kgg-ui-lab/visual-evidence/v1",
            "status": evidence_status,
            "surface": "real_browser",
            "observation_id": observation_id,
            "state_before": state,
            "artifacts": [dict(artifact)],
        }
        if flow_status is not None:
            evidence["flow_status"] = flow_status
        self.evidence.setdefault(session["session_id"], []).append(evidence)
        return {"observation": public_observation, "evidence": evidence, "image": dict(image)}

    def _open_visual_fallback(self, session: Mapping[str, Any], failure: str) -> dict[str, Any] | None:
        """Open G05 only after a real, deterministic Quick-Flow drift."""

        if "visual_loop" not in session["runner"]["capabilities"] or "capture" not in session["runner"]["capabilities"]:
            return None
        real_browser = _load_real_browser_module()
        self._close_visual(session["session_id"])
        try:
            browser = real_browser.PersistentRealBrowser(
                url=session["app"]["url"],
                viewport=session["viewport"],
                run_id=f"{session['session_id']}-visual-fallback",
                timeout_ms=session["timeout"]["timeout_ms"],
                bootstrap=self.browser_bootstrap,
            )
            self.visual_sessions[session["session_id"]] = browser
            observed = browser.observe()
            record = self._record_visual_observation(
                session,
                observed,
                evidence_status="DRIFT_FALLBACK_READY",
                flow_status="STALE_REQUIRES_REVIEW",
            )
            session["flow_stale"] = True
            session["status"] = "visual_fallback"
            return {
                "status": "READY",
                "reason": failure,
                "flow_status": "STALE_REQUIRES_REVIEW",
                "observation": record["observation"],
                "evidence": record["evidence"],
                "image": record["image"],
            }
        except real_browser.RealBrowserError:
            self._close_visual(session["session_id"])
            return None

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
        if not _app_url_allowed(app["url"], self.browser_bootstrap):
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
        session["visual_observations"] = {}
        session["created_at"] = _now()
        session["main_sha"] = main_sha
        self.sessions[session_id] = session
        return {"schema": MCP_SCHEMA, "operation": "start_ui_session", "session": self._public_session(session)}

    @staticmethod
    def _public_session(session: Mapping[str, Any]) -> dict[str, Any]:
        return {key: deepcopy(value) for key, value in session.items() if key not in {"used_requests", "events", "main_sha", "visual_observation", "visual_observations"}}

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

    def _flow_store_call(self, callback: Any) -> Any:
        try:
            return callback()
        except self.flow_store_module.FlowStoreError as exc:
            _fail(exc.code)

    def save_flow(self, value: Any) -> dict[str, Any]:
        args = _object(value, "arguments")
        flow = self._flow_store_call(lambda: self.flow_store.save(args.get("flow")))
        return {"schema": MCP_SCHEMA, "operation": "save_flow", "flow": flow, "store": "USER_SAVED_FLOWS"}

    def list_flows(self, value: Any) -> dict[str, Any]:
        args = _object(value, "arguments")
        project = args.get("project")
        scope = args.get("scope")
        include_deprecated = args.get("include_deprecated", False)
        if not isinstance(include_deprecated, bool):
            _fail("include_deprecated_invalid")
        flows = self._flow_store_call(lambda: self.flow_store.list_flows(project=project, scope=scope, include_deprecated=include_deprecated))
        return {"schema": MCP_SCHEMA, "operation": "list_flows", "flows": flows}

    def get_flow(self, value: Any) -> dict[str, Any]:
        args = _object(value, "arguments")
        reference = args.get("flow", args)
        flow = self._flow_store_call(lambda: self.flow_store.get(_object(reference, "flow")))
        return {"schema": MCP_SCHEMA, "operation": "get_flow", "flow": flow}

    def create_new_version(self, value: Any) -> dict[str, Any]:
        args = _object(value, "arguments")
        flow = self._flow_store_call(lambda: self.flow_store.create_version(args.get("flow")))
        return {"schema": MCP_SCHEMA, "operation": "create_new_version", "flow": flow, "store": "USER_SAVED_FLOWS"}

    def deprecate_flow(self, value: Any) -> dict[str, Any]:
        args = _object(value, "arguments")
        reference = args.get("flow", args)
        flow = self._flow_store_call(lambda: self.flow_store.deprecate(_object(reference, "flow")))
        return {"schema": MCP_SCHEMA, "operation": "deprecate_flow", "flow": flow}

    @staticmethod
    def _flow_runtime_steps(flow: Mapping[str, Any], parameters: Any = None) -> list[dict[str, Any]]:
        if parameters is None:
            parameters = {}
        parameters = _object(parameters, "parameters")
        _scan_safe(parameters)
        steps: list[dict[str, Any]] = []
        for raw in flow["steps"]:
            step = dict(raw)
            operation = step["operation"]
            if operation == "observe":
                operation = "read_state"
            target = step.pop("target", None)
            if target is not None:
                if target["kind"] == "action_id":
                    step["label"] = target["value"]
                elif target["kind"] == "accessibility":
                    step["label"] = target["name"]
                elif target["kind"] == "coordinate_fallback":
                    step["coordinates"] = {"x": target["x"], "y": target["y"]}
            if operation == "type":
                placeholder = step["text"][2:-2]
                if placeholder not in parameters or not isinstance(parameters[placeholder], str) or len(parameters[placeholder]) > 200:
                    _fail("flow_parameter_missing")
                step["text"] = parameters[placeholder]
            step["operation"] = operation
            for key in ("sequence", "expected_state"):
                step.pop(key, None)
            steps.append(step)
        return steps

    @staticmethod
    def _check_flow_binding(flow: Mapping[str, Any], session: Mapping[str, Any], binding_fingerprint: Any, toggle_states: Any) -> dict[str, Any]:
        binding = flow["binding"]
        if binding_fingerprint != binding["source_fingerprint"]:
            _fail("flow_drift_detected")
        if "app_name" in binding and session["app"]["name"] != binding["app_name"]:
            _fail("flow_app_mismatch")
        if session["device_profile"] not in flow["device_constraints"]:
            _fail("flow_device_constraint_mismatch")
        viewport = session["viewport"]
        limits = flow["viewport_constraints"]
        if not limits["min_width"] <= viewport["width"] <= limits["max_width"] or not limits["min_height"] <= viewport["height"] <= limits["max_height"]:
            _fail("flow_viewport_constraint_mismatch")
        scale = limits["device_scale_factor"]
        if not scale[0] <= viewport["device_scale_factor"] <= scale[1]:
            _fail("flow_viewport_constraint_mismatch")
        requested = {} if toggle_states is None else _object(toggle_states, "toggle_states")
        requested_before = requested.get("before", {})
        if requested_before != flow["toggle_states"]["before"]:
            _fail("flow_toggle_precondition_mismatch")
        return {"before": deepcopy(flow["toggle_states"]["before"]), "after": deepcopy(flow["toggle_states"]["after"])}

    @staticmethod
    def _synthetic_flow_result(flow: Mapping[str, Any], toggle_states: Mapping[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        artifacts: list[dict[str, Any]] = []
        steps: list[dict[str, Any]] = []
        for raw in flow["steps"]:
            operation = raw["operation"]
            label = raw.get("label", operation)
            if operation in {"observe", "read_state"}:
                actual = raw.get("expected_state", label)
            elif operation == "capture_screenshot":
                artifact = _artifact(f"flow-shot-{raw['sequence']:03d}", "screenshot", f"synthetic://kgg-ui-lab/flows/{flow['flow_id']}/{flow['version']}/{raw['sequence']}")
                artifacts.append(artifact)
                actual = "screenshot captured"
            elif operation == "type":
                actual = "text entered"
            else:
                actual = "action completed"
            steps.append({"expected": label, "actual": actual, "status": "PASS", "artifact_refs": [artifacts[-1]["id"]] if operation == "capture_screenshot" else []})
        result = {"status": "PASS", "error_class": "", "steps": steps, "artifacts": artifacts, "final_state": flow["expected_states"]["final"], "toggle_states": dict(toggle_states)}
        return result, artifacts

    def _run_real_flow(self, session: Mapping[str, Any], operation: str, *, runtime_steps: list[Mapping[str, Any]] | None = None, flow: Mapping[str, Any] | None = None) -> dict[str, Any]:
        """Run one explicitly enabled real browser flow through the host bridge."""

        real_browser = _load_real_browser_module()
        if operation == "run_flow":
            steps = runtime_steps
            if not isinstance(steps, list) or not steps:
                _fail("flow_steps_invalid")
        elif operation == "run_quick_flow":
            flow_name = session["quick_flow"]["name"]
            try:
                builtin = self.flow_store.builtin(flow_name, session["quick_flow"]["version"])
            except self.flow_store_module.FlowStoreError:
                _fail("real_browser_flow_not_allowlisted")
            steps = self._flow_runtime_steps(builtin)
        else:
            steps = [{"operation": "capture_screenshot", "label": "manual-capture"}]
        try:
            result = real_browser.run_real_flow(
                url=session["app"]["url"],
                viewport=session["viewport"],
                steps=steps,
                run_id=f"{session['session_id']}-{session['request_id']}",
                timeout_ms=session["timeout"]["timeout_ms"],
                bootstrap=self.browser_bootstrap,
            )
            if flow is not None and result["status"] == "PASS":
                expected_observations = [step.get("expected_state") for step in flow["steps"] if step["operation"] in {"observe", "read_state"}]
                actual_observations = [step["actual"] for step, raw in zip(result["steps"], flow["steps"]) if raw["operation"] in {"observe", "read_state"}]
                if expected_observations != actual_observations:
                    result["status"] = "FAIL"
                    result["error_class"] = "flow_state_mismatch"
                elif result["final_state"] != flow["expected_states"]["final"]:
                    result["status"] = "FAIL"
                    result["error_class"] = "flow_final_state_mismatch"
            return result
        except real_browser.RealBrowserError as exc:
            _fail(exc.code)
        _fail("real_browser_failed")

    def run_browser_flow(self, value: Any, operation: str) -> dict[str, Any]:
        request = _object(value, "request")
        session_id = request.get("session_id")
        session = self._session(session_id, request.get("actor"))
        required_capability = "quick_flows" if operation == "run_quick_flow" else "capture"
        if required_capability not in session["runner"]["capabilities"]:
            _fail("capability_missing")
        checked = _request(request, operation, session)
        session["status"] = "running"
        session["used_requests"].append(checked["request_id"])
        if self.browser_bootstrap.enabled:
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
            fallback = None
            if operation == "run_quick_flow" and real["status"] == "FAIL" and real["error_class"] in {"action_target_not_found", "input_target_not_found"}:
                fallback = self._open_visual_fallback(session, real["error_class"])
                if fallback is not None:
                    session["events"].append({"event": "quick_flow_visual_fallback", "status": "READY", "at": _now()})
            result = {
                "status": real["status"],
                "error_class": real["error_class"],
                "steps": real["steps"],
                "artifacts": real["artifacts"],
                "final_state": real["final_state"],
                "runtime_ms": real["runtime_ms"],
            }
            images = list(real["images"])
            if fallback is not None:
                result["fallback"] = {
                    "status": fallback["status"],
                    "reason": fallback["reason"],
                    "flow_status": fallback["flow_status"],
                    "observation": fallback["observation"],
                    "evidence": fallback["evidence"],
                }
                images.append(fallback["image"])
            pilot_metrics = {"status": "FAIL", "error_class": "NUMERIC_METRICS_NOT_VERIFIABLE"}
            return {
                "schema": MCP_SCHEMA,
                "operation": operation,
                "result": result,
                "evidence": evidence,
                "pilot_metrics": pilot_metrics,
                "session_status": session["status"],
                "_images": images,
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

    def run_flow(self, value: Any) -> dict[str, Any]:
        args = _object(value, "arguments")
        request = _object(args.get("request"), "request")
        session = self._session(request.get("session_id"), request.get("actor"))
        if "quick_flows" not in session["runner"]["capabilities"]:
            _fail("capability_missing")
        checked = _request(request, "run_flow", session)
        flow_ref = {
            "flow_id": args.get("flow_id"),
            "project": args.get("project"),
            "scope": args.get("scope"),
            "version": args.get("version"),
        }
        flow = self._flow_store_call(lambda: self.flow_store.get(flow_ref))
        if flow["status"] != "active":
            _fail("flow_deprecated")
        toggle_states = self._check_flow_binding(flow, session, args.get("binding_fingerprint"), args.get("toggle_states"))
        runtime_steps = self._flow_runtime_steps(flow, args.get("parameters"))
        session["status"] = "running"
        session["used_requests"].append(checked["request_id"])
        if self.browser_bootstrap.enabled:
            real = self._run_real_flow(session, "run_flow", runtime_steps=runtime_steps, flow=flow)
            session["status"] = "completed" if real["status"] == "PASS" else "failed"
            result = {
                "status": real["status"],
                "error_class": real["error_class"],
                "steps": real["steps"],
                "artifacts": real["artifacts"],
                "final_state": real["final_state"],
                "runtime_ms": real["runtime_ms"],
                "flow": {key: flow[key] for key in ("flow_id", "project", "scope", "version")},
                "toggle_states": toggle_states,
            }
            evidence = {
                "schema": "kgg-ui-lab/evidence/v1",
                "status": real["status"],
                "surface": "real_browser",
                "flow": result["flow"],
                "binding_fingerprint": flow["binding"]["source_fingerprint"],
                "toggle_states": toggle_states,
                "artifacts": real["artifacts"],
                "runtime_ms": real["runtime_ms"],
                "final_state": real["final_state"],
            }
            self.evidence.setdefault(session["session_id"], []).append(evidence)
            session["events"].append({"event": "flow_completed", "status": real["status"], "flow_id": flow["flow_id"], "version": flow["version"], "at": _now()})
            return {"schema": MCP_SCHEMA, "operation": "run_flow", "result": result, "evidence": evidence, "session_status": session["status"], "_images": list(real["images"])}
        result, artifacts = self._synthetic_flow_result(flow, toggle_states)
        result["flow"] = {key: flow[key] for key in ("flow_id", "project", "scope", "version")}
        evidence = {
            "schema": "kgg-ui-lab/evidence/v1",
            "status": "PASS",
            "surface": "synthetic",
            "flow": result["flow"],
            "binding_fingerprint": flow["binding"]["source_fingerprint"],
            "toggle_states": toggle_states,
            "artifacts": artifacts,
            "final_state": result["final_state"],
        }
        session["status"] = "completed"
        session["events"].append({"event": "flow_completed", "status": "PASS", "flow_id": flow["flow_id"], "version": flow["version"], "at": _now()})
        self.evidence.setdefault(session["session_id"], []).append(evidence)
        return {"schema": MCP_SCHEMA, "operation": "run_flow", "result": result, "evidence": evidence, "session_status": session["status"]}

    @staticmethod
    def _recording_frame(observed: Mapping[str, Any], index: int, timestamp_ms: int) -> dict[str, Any]:
        artifacts = observed.get("artifacts")
        images = observed.get("images")
        if not isinstance(artifacts, list) or not artifacts or not isinstance(images, list) or not images:
            _fail("recording_frame_missing_screenshot")
        artifact = artifacts[0]
        image = images[0]
        if not isinstance(artifact, Mapping) or not isinstance(image, Mapping):
            _fail("recording_frame_invalid")
        encoded = image.get("data_base64")
        if not isinstance(encoded, str):
            _fail("recording_frame_invalid")
        try:
            size_bytes = len(base64.b64decode(encoded, validate=True))
        except (ValueError, TypeError):
            _fail("recording_frame_invalid")
        if size_bytes < 1:
            _fail("recording_frame_invalid")
        public_artifact = {
            "id": str(artifact["id"]),
            "kind": "screenshot",
            "ref": str(artifact["ref"]),
            "sha256": str(artifact["sha256"]),
            "content_type": "image/png",
            "size_bytes": size_bytes,
            "retention": "session-bound",
        }
        return {
            "index": index,
            "timestamp_ms": timestamp_ms,
            "state": str(observed.get("state", "unknown"))[:200],
            "artifact": public_artifact,
            "image": dict(image),
        }

    def record_screen(self, value: Any) -> dict[str, Any]:
        """Capture a short, opt-in viewport trace as timestamped PNG keyframes."""

        args = _object(value, "arguments")
        request = _object(args.get("request"), "request")
        session = self._session(request.get("session_id"), request.get("actor"))
        if not {"screen_recording", "capture"}.issubset(session["runner"]["capabilities"]):
            _fail("capability_missing")
        checked = _request(request, "record_screen", session)
        duration_ms = args.get("duration_ms")
        frame_interval_ms = args.get("frame_interval_ms")
        if not isinstance(duration_ms, int) or isinstance(duration_ms, bool) or not 100 <= duration_ms <= MAX_RECORDING_DURATION_MS:
            _fail("recording_duration_invalid")
        if not isinstance(frame_interval_ms, int) or isinstance(frame_interval_ms, bool) or not MIN_RECORDING_FRAME_INTERVAL_MS <= frame_interval_ms <= MAX_RECORDING_FRAME_INTERVAL_MS:
            _fail("recording_interval_invalid")
        expected_frames = ((duration_ms + frame_interval_ms - 1) // frame_interval_ms) + 1
        if expected_frames > MAX_RECORDING_FRAMES:
            _fail("recording_frame_count_invalid")
        if not self.browser_bootstrap.enabled:
            _fail("real_browser_not_enabled")

        session_id = session["session_id"]
        run_id = f"{session_id}-{checked['request_id']}-recording"
        session["status"] = "recording"
        session["used_requests"].append(checked["request_id"])
        frames: list[dict[str, Any]] = []
        real_browser = _load_real_browser_module()
        try:
            self._close_visual(session_id)
            browser = real_browser.PersistentRealBrowser(
                url=session["app"]["url"],
                viewport=session["viewport"],
                run_id=run_id,
                timeout_ms=session["timeout"]["timeout_ms"],
                bootstrap=self.browser_bootstrap,
            )
            self.visual_sessions[session_id] = browser
            started_at = _now()
            started_perf = time.perf_counter()
            frames.append(self._recording_frame(browser.observe(), 0, 0))
            deadline = started_perf + (duration_ms / 1000)
            index = 1
            while index < expected_frames:
                remaining_ms = int(max(0, (deadline - time.perf_counter()) * 1000))
                if remaining_ms <= 0:
                    break
                wait_ms = min(frame_interval_ms, remaining_ms)
                browser.act({"operation": "wait", "label": f"recording-frame-{index}", "timeout_ms": max(1, wait_ms)})
                elapsed_ms = min(duration_ms, int(max(0, (time.perf_counter() - started_perf) * 1000)))
                frames.append(self._recording_frame(browser.observe(), index, elapsed_ms))
                index += 1
        except real_browser.RealBrowserError as exc:
            session["status"] = "failed"
            _fail(exc.code)
        except ServerError:
            session["status"] = "failed"
            raise
        finally:
            self._close_visual(session_id)

        if not frames:
            session["status"] = "failed"
            _fail("recording_frame_missing_screenshot")
        stopped_at = _now()
        public_frames = [{key: frame[key] for key in ("index", "timestamp_ms", "state", "artifact")} for frame in frames]
        artifacts = [frame["artifact"] for frame in frames]
        actual_duration_ms = public_frames[-1]["timestamp_ms"]
        evidence = {
            "schema": "kgg-ui-lab/screen-recording-evidence/v1",
            "status": "PASS",
            "surface": "real_browser",
            "recording_mode": "KEYFRAME_FALLBACK",
            "session_id": session_id,
            "request_id": checked["request_id"],
            "run_id": run_id,
            "started_at": started_at,
            "stopped_at": stopped_at,
            "requested_duration_ms": duration_ms,
            "actual_duration_ms": actual_duration_ms,
            "hard_max_duration_ms": MAX_RECORDING_DURATION_MS,
            "frame_interval_ms": frame_interval_ms,
            "timeout": {
                "host_timeout_ms": session["timeout"]["timeout_ms"],
                "hard_max_duration_ms": MAX_RECORDING_DURATION_MS,
                "timed_out": False,
            },
            "content_type": "image/png",
            "retention": "session-bound",
            "video_artifact": None,
            "frames": [{key: frame[key] for key in ("index", "timestamp_ms", "state", "artifact")} for frame in public_frames],
            "artifacts": artifacts,
        }
        session["status"] = "completed"
        session["events"].append({"event": "screen_recording_completed", "status": "PASS", "recording_mode": "KEYFRAME_FALLBACK", "frame_count": len(public_frames), "at": stopped_at})
        self.evidence.setdefault(session_id, []).append(evidence)
        return {
            "schema": MCP_SCHEMA,
            "operation": "record_screen",
            "result": {
                "status": "PASS",
                "error_class": "",
                "recording_mode": "KEYFRAME_FALLBACK",
                "frames": public_frames,
                "video_artifact": None,
                "requested_duration_ms": duration_ms,
                "actual_duration_ms": actual_duration_ms,
            },
            "evidence": evidence,
            "session_status": session["status"],
            "_images": [frames[0]["image"], frames[-1]["image"]] if len(frames) > 1 else [frames[0]["image"]],
        }

    def observe_visual(self, value: Any) -> dict[str, Any]:
        if not self.browser_bootstrap.enabled:
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
            self._close_visual(session["session_id"])
            browser = real_browser.PersistentRealBrowser(
                url=session["app"]["url"],
                viewport=session["viewport"],
                run_id=f"{session['session_id']}-{checked['request_id']}",
                timeout_ms=session["timeout"]["timeout_ms"],
                bootstrap=self.browser_bootstrap,
            )
            self.visual_sessions[session["session_id"]] = browser
            observed = browser.observe()
        except real_browser.RealBrowserError as exc:
            self._close_visual(session["session_id"])
            session["status"] = "failed"
            _fail(exc.code)
        try:
            record = self._record_visual_observation(session, observed)
        except ServerError:
            self._close_visual(session["session_id"])
            session["status"] = "failed"
            raise
        return {
            "schema": MCP_SCHEMA,
            "operation": "observe_visual_state",
            "observation": record["observation"],
            "evidence": record["evidence"],
            "session_status": session["status"],
            "_images": [record["image"]],
        }

    def execute_visual_action(self, value: Any, decision_value: Any) -> dict[str, Any]:
        if not self.browser_bootstrap.enabled:
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
        _validate_swipe_bounds(decision, session["viewport"])
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
        flow_stale = bool(session.get("flow_stale"))
        session["status"] = "stale_fallback_completed" if flow_stale else "completed"
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
        if flow_stale:
            evidence["flow_status"] = "STALE_REQUIRES_REVIEW"
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
                "flow_status": "STALE_REQUIRES_REVIEW" if flow_stale else "VISUAL_LOOP",
            },
            "evidence": evidence,
            "session_status": session["status"],
            "_images": [observation["image"], after_image],
        }

    def compare_visual_reference(self, value: Any, reference_value: Any) -> dict[str, Any]:
        request = _object(value, "request")
        session = self._session(request.get("session_id"), request.get("actor"))
        if not {"capture", "visual_loop"}.issubset(session["runner"]["capabilities"]):
            _fail("capability_missing")
        checked = _request(request, "compare_visual_reference", session, sequential=True)
        observation = session.get("visual_observation")
        if not isinstance(observation, Mapping) or not isinstance(observation.get("image"), Mapping):
            _fail("visual_observation_required")
        current_image = observation["image"]
        current_data = current_image.get("data_base64")
        current_artifact = observation.get("artifact")
        if not isinstance(current_data, str) or not isinstance(current_artifact, Mapping):
            _fail("visual_current_image_missing")
        try:
            current_digest = hashlib.sha256(base64.b64decode(current_data, validate=True)).hexdigest()
        except (ValueError, TypeError):
            _fail("visual_current_image_invalid")
        if current_digest != current_artifact.get("sha256"):
            _fail("visual_current_hash_mismatch")
        reference = _visual_reference(reference_value, session)
        comparison = _compare_visual_images(current_image, reference)
        session["used_requests"].append(checked["request_id"])
        session["events"].append({"event": "visual_reference_compared", "status": comparison["status"], "at": _now()})
        evidence = {
            "schema": "kgg-ui-lab/visual-reference-evidence/v1",
            "status": comparison["status"],
            "reference_class": reference["reference_class"],
            "reference_id": reference["reference_id"],
            "reference_sha256": reference["reference_sha256"],
            "current_id": current_artifact["id"],
            "current_sha256": current_artifact["sha256"],
            "viewport": reference["viewport"],
            "masks": reference["masks"],
            "comparison": comparison,
        }
        if reference.get("approval_id") is not None:
            evidence["approval_id"] = reference["approval_id"]
        self.evidence.setdefault(session["session_id"], []).append(evidence)
        return {
            "schema": MCP_SCHEMA,
            "operation": "compare_visual_reference",
            "result": {
                "status": comparison["status"],
                "reference_id": reference["reference_id"],
                "reference_sha256": reference["reference_sha256"],
                "current_id": current_artifact["id"],
                "current_sha256": current_artifact["sha256"],
                "comparison": comparison,
            },
            "evidence": evidence,
            "session_status": session["status"],
            "_images": [dict(current_image)],
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
            return self.run_browser_flow(args.get("request"), name)
        if name == "record_screen":
            return self.record_screen(args)
        if name == "observe_visual_state":
            return self.observe_visual(args.get("request"))
        if name == "execute_visual_action":
            return self.execute_visual_action(args.get("request"), args.get("decision"))
        if name == "compare_visual_reference":
            return self.compare_visual_reference(args.get("request"), args.get("reference"))
        if name == "run_width_sweep":
            return self.sweep(args.get("session_id"), args.get("actor"), args.get("viewports"))
        if name == "get_test_evidence":
            return self.evidence_read(args.get("session_id"), args.get("actor"))
        if name == "get_session_status":
            return self.status_read(args.get("session_id"), args.get("actor"))
        if name == "save_flow":
            return self.save_flow(args)
        if name == "list_flows":
            return self.list_flows(args)
        if name == "get_flow":
            return self.get_flow(args)
        if name == "run_flow":
            return self.run_flow(args)
        if name == "create_new_version":
            return self.create_new_version(args)
        if name == "deprecate_flow":
            return self.deprecate_flow(args)
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
    # The stdio host is the only launcher boundary that reads activation
    # variables; unit tests and embedded callers remain synthetic by default.
    runtime = Runtime(browser_bootstrap=_load_real_browser_module().BrowserBootstrap.from_environment())
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
