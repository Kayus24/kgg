#!/usr/bin/env python3
"""Strict, dependency-free contracts for the bounded KGG UI Lab.

The UI Lab is deliberately represented as data contracts first.  Keeping the
validation here small and deterministic lets the browser/Android runners be
replaced without weakening leases, source pinning, or the append-only audit
trail.
"""

from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import Any, Mapping
from urllib.parse import urlparse


SESSION_SCHEMA = "kgg-ui-lab/session/v1"
REQUEST_SCHEMA = "kgg-ui-lab/request/v1"
EVENT_SCHEMA = "kgg-ui-lab/event/v1"

_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{5,63}$")
_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{2,63}$")
_EVENT_TYPE_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{2,63}$")

ACTORS = frozenset({"codex", "custom_gpt", "max", "system"})
EVENT_ACTORS = ACTORS | {"runner"}
SESSION_STATUSES = frozenset(
    {"created", "ready", "running", "waiting", "failed", "completed", "expired", "cancelled"}
)
CAPABILITIES = frozenset({"browser", "capture", "android", "quick_flows", "width_sweep", "qr_image"})
DEVICE_PROFILES = frozenset({"tab-s9", "oppo-find-x9", "custom"})
# A wait is a semantic runner step, never an unbounded sleep.  Adapters may
# choose a shorter default, but the contract must reject a caller-provided
# duration above this hard ceiling.
MAX_WAIT_MS = 5000
OPERATIONS = frozenset(
    {
        "start_session",
        "open_preview",
        "read_state",
        "click",
        "tap",
        "type",
        "scroll",
        "reload",
        "back",
        "wait",
        "run_quick_flow",
        "capture_screenshot",
        "cancel_session",
        "cleanup",
        "register_runner",
    }
)

_SENSITIVE_TOKENS = (
    "raw_qr",
    "base64",
    "password",
    "api_key",
    "secret",
    "patient_data",
    "selector",
    "stack_trace",
    "browser_output",
)


class ContractError(ValueError):
    """A safe, stable contract failure.

    Callers can branch on the prefix (for example ``lease_expired``) without
    exposing runner internals or browser output to a Custom GPT.
    """


def _fail(code: str, detail: str = "") -> None:
    message = code if not detail else f"{code}: {detail}"
    raise ContractError(message)


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        _fail(f"{label}_invalid", "expected an object")
    return value


def _exact_keys(value: Mapping[str, Any], expected: set[str], label: str) -> None:
    missing = expected - set(value)
    unknown = set(value) - expected
    if missing:
        _fail(f"{label}_missing", ", ".join(sorted(missing)))
    if unknown:
        _fail(f"{label}_unknown", ", ".join(sorted(unknown)))


def _string(value: Any, label: str, *, max_length: int = 256) -> str:
    if not isinstance(value, str) or not value or len(value) > max_length:
        _fail(f"{label}_invalid")
    if any(ord(char) < 32 for char in value):
        _fail(f"{label}_invalid", "control characters are not allowed")
    return value


def _id(value: Any, label: str) -> str:
    text = _string(value, label, max_length=64)
    if not _ID_RE.fullmatch(text):
        _fail(f"{label}_invalid", "must be a lower-case slug")
    return text


def _version(value: Any, label: str) -> str:
    text = _string(value, label, max_length=32)
    if not _VERSION_RE.fullmatch(text):
        _fail(f"{label}_invalid", "expected x.y.z")
    return text


def _timestamp(value: Any, label: str) -> datetime:
    text = _string(value, label, max_length=40)
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        _fail(f"{label}_invalid", "expected RFC3339")
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        _fail(f"{label}_invalid", "timezone is required")
    return parsed.astimezone(timezone.utc)


def _sha(value: Any, label: str, *, nullable: bool = False) -> str | None:
    if value is None and nullable:
        return None
    text = _string(value, label, max_length=64)
    if not _SHA_RE.fullmatch(text):
        _fail(f"{label}_invalid", "expected a 40-character lower-case SHA")
    return text


def _sha256(value: Any, label: str) -> str:
    text = _string(value, label, max_length=64)
    if not _SHA256_RE.fullmatch(text):
        _fail(f"{label}_invalid", "expected a 64-character lower-case SHA-256")
    return text


def _scan_sensitive(value: Any, path: str = "event") -> None:
    """Reject fields which could leak credentials, patient data, or raw UI internals."""

    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key).casefold()
            if any(token in key_text for token in _SENSITIVE_TOKENS) or re.search(r"\btoken\b", key_text):
                _fail("sensitive_field", path + "." + str(key))
            _scan_sensitive(child, path + "." + str(key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _scan_sensitive(child, f"{path}[{index}]")
    elif isinstance(value, str):
        lowered = value.casefold()
        if any(token in lowered for token in _SENSITIVE_TOKENS) or re.search(r"\btoken\b", lowered):
            _fail("sensitive_field", path)


def _validate_url(value: Any) -> str:
    url = _string(value, "app_url", max_length=2048)
    parsed = urlparse(url)
    if parsed.scheme == "https" and parsed.netloc:
        return url
    if parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1"} and parsed.netloc:
        return url
    _fail("app_url_invalid", "only HTTPS or local HTTP is allowed")


def assert_lease_active(lease: Mapping[str, Any], *, now: datetime | None = None) -> None:
    """Fail closed when a session lease is missing, malformed, or expired."""

    value = _mapping(lease, "lease")
    _exact_keys(value, {"owner", "issued_at", "expires_at"}, "lease")
    owner = _string(value["owner"], "lease_owner", max_length=32)
    if owner not in ACTORS:
        _fail("lease_owner_invalid")
    issued = _timestamp(value["issued_at"], "lease_issued_at")
    expires = _timestamp(value["expires_at"], "lease_expires_at")
    if expires <= issued:
        _fail("lease_invalid", "expires_at must be after issued_at")
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None or current.utcoffset() is None:
        _fail("lease_now_invalid")
    if current.astimezone(timezone.utc) >= expires:
        _fail("lease_expired")


def runner_supports(runner: Mapping[str, Any], capability: str) -> bool:
    value = _mapping(runner, "runner")
    capabilities = value.get("capabilities")
    return isinstance(capabilities, list) and capability in capabilities


def require_capability(session: Mapping[str, Any], capability: str) -> None:
    if capability not in CAPABILITIES:
        _fail("capability_invalid", capability)
    value = _mapping(session, "session")
    if not runner_supports(_mapping(value.get("runner"), "runner"), capability):
        _fail("capability_missing", capability)


def validate_runner(value: Mapping[str, Any]) -> Mapping[str, Any]:
    runner = _mapping(value, "runner")
    _exact_keys(runner, {"runner_id", "version", "browser_revision", "capabilities"}, "runner")
    _id(runner["runner_id"], "runner_id")
    _version(runner["version"], "runner_version")
    _string(runner["browser_revision"], "browser_revision", max_length=128)
    capabilities = runner["capabilities"]
    if not isinstance(capabilities, list) or not capabilities or any(not isinstance(item, str) for item in capabilities):
        _fail("runner_capabilities_invalid")
    if len(set(capabilities)) != len(capabilities) or any(item not in CAPABILITIES for item in capabilities):
        _fail("runner_capabilities_invalid")
    return runner


def validate_session(value: Mapping[str, Any]) -> Mapping[str, Any]:
    session = _mapping(value, "session")
    _exact_keys(
        session,
        {
            "schema",
            "session_id",
            "status",
            "active_actor",
            "request_id",
            "lease",
            "runner",
            "app",
            "device_profile",
            "viewport",
            "quick_flow",
            "timeout",
            "artifacts",
        },
        "session",
    )
    if session["schema"] != SESSION_SCHEMA:
        _fail("session_schema_invalid")
    session_id = _id(session["session_id"], "session_id")
    if session["status"] not in SESSION_STATUSES:
        _fail("session_status_invalid")
    if session["active_actor"] not in ACTORS:
        _fail("actor_invalid")
    _id(session["request_id"], "request_id")

    lease = _mapping(session["lease"], "lease")
    _exact_keys(lease, {"owner", "issued_at", "expires_at"}, "lease")
    if lease["owner"] != session["active_actor"]:
        _fail("lease_owner_invalid", "owner must match active_actor")
    assert_lease_active(lease, now=_timestamp(lease["issued_at"], "lease_issued_at"))
    # The previous call intentionally uses the issue time only to validate the
    # shape; expiry is checked again at every operation by assert_lease_active.

    runner = validate_runner(session["runner"])

    app = _mapping(session["app"], "app")
    _exact_keys(app, {"name", "url", "main_sha", "preview_sha"}, "app")
    if app["name"] not in {"admin", "patient"}:
        _fail("app_name_invalid")
    _validate_url(app["url"])
    _sha(app["main_sha"], "main_sha")
    _sha(app["preview_sha"], "preview_sha", nullable=True)

    if session["device_profile"] not in DEVICE_PROFILES:
        _fail("device_profile_invalid")
    viewport = _mapping(session["viewport"], "viewport")
    _exact_keys(viewport, {"width", "height", "device_scale_factor"}, "viewport")
    for key in ("width", "height"):
        number = viewport[key]
        if not isinstance(number, int) or isinstance(number, bool) or not 240 <= number <= 10000:
            _fail("viewport_invalid", key)
    scale = viewport["device_scale_factor"]
    if not isinstance(scale, (int, float)) or isinstance(scale, bool) or not 0.5 <= scale <= 4:
        _fail("viewport_invalid", "device_scale_factor")

    quick_flow = _mapping(session["quick_flow"], "quick_flow")
    _exact_keys(quick_flow, {"name", "version"}, "quick_flow")
    name = _string(quick_flow["name"], "quick_flow_name", max_length=64)
    if not _SLUG_RE.fullmatch(name):
        _fail("quick_flow_invalid", "name")
    _version(quick_flow["version"], "quick_flow_version")

    timeout = _mapping(session["timeout"], "timeout")
    _exact_keys(timeout, {"timeout_ms", "cleanup_on_cancel"}, "timeout")
    timeout_ms = timeout["timeout_ms"]
    if not isinstance(timeout_ms, int) or isinstance(timeout_ms, bool) or not 1000 <= timeout_ms <= 1_800_000:
        _fail("timeout_invalid")
    if not isinstance(timeout["cleanup_on_cancel"], bool):
        _fail("timeout_invalid", "cleanup_on_cancel")

    artifacts = session["artifacts"]
    if not isinstance(artifacts, list) or len(artifacts) > 100:
        _fail("artifacts_invalid")
    for artifact in artifacts:
        _validate_artifact(artifact)
    return session


def validate_request(value: Mapping[str, Any]) -> Mapping[str, Any]:
    request = _mapping(value, "request")
    _exact_keys(request, {"schema", "request_id", "session_id", "actor", "operation", "main_sha", "payload_sha256"}, "request")
    if request["schema"] != REQUEST_SCHEMA:
        _fail("request_schema_invalid")
    _id(request["request_id"], "request_id")
    _id(request["session_id"], "session_id")
    if request["actor"] not in ACTORS:
        _fail("actor_invalid")
    if request["operation"] not in OPERATIONS:
        _fail("operation_invalid")
    _sha(request["main_sha"], "main_sha")
    _sha256(request["payload_sha256"], "payload_sha256")
    return request


def _validate_artifact(value: Any) -> None:
    artifact = _mapping(value, "artifact")
    _exact_keys(artifact, {"kind", "ref", "sha256"}, "artifact")
    kind = _string(artifact["kind"], "artifact_kind", max_length=48)
    if not _SLUG_RE.fullmatch(kind):
        _fail("artifacts_invalid", "kind")
    _string(artifact["ref"], "artifact_ref", max_length=512)
    _sha256(artifact["sha256"], "artifact_sha256")


def validate_event(value: Mapping[str, Any]) -> Mapping[str, Any]:
    event = _mapping(value, "event")
    _exact_keys(
        event,
        {"schema", "event_id", "session_id", "request_id", "sequence", "event_type", "actor", "timestamp", "status", "summary", "evidence"},
        "event",
    )
    _scan_sensitive(event)
    if event["schema"] != EVENT_SCHEMA:
        _fail("event_schema_invalid")
    _id(event["event_id"], "event_id")
    _id(event["session_id"], "session_id")
    _id(event["request_id"], "request_id")
    sequence = event["sequence"]
    if not isinstance(sequence, int) or isinstance(sequence, bool) or not 1 <= sequence <= 100_000:
        _fail("event_sequence_invalid")
    event_type = _string(event["event_type"], "event_type", max_length=64)
    if not _EVENT_TYPE_RE.fullmatch(event_type):
        _fail("event_type_invalid")
    if event["actor"] not in EVENT_ACTORS:
        _fail("actor_invalid")
    _timestamp(event["timestamp"], "event_timestamp")
    if event["status"] not in SESSION_STATUSES:
        _fail("event_status_invalid")
    _string(event["summary"], "event_summary", max_length=500)
    evidence = event["evidence"]
    if not isinstance(evidence, list) or len(evidence) > 20:
        _fail("evidence_invalid")
    for item in evidence:
        _validate_artifact(item)
    return event


def validate_event_chain(events: list[Mapping[str, Any]]) -> int:
    if not isinstance(events, list):
        _fail("event_chain_invalid")
    seen_ids: set[str] = set()
    seen_pairs: set[tuple[str, str]] = set()
    session_id: str | None = None
    for expected_sequence, item in enumerate(events, start=1):
        event = validate_event(item)
        if event["sequence"] != expected_sequence:
            _fail("event_sequence_invalid", f"expected {expected_sequence}")
        if session_id is None:
            session_id = event["session_id"]
        elif event["session_id"] != session_id:
            _fail("event_chain_invalid", "session_id changed")
        if event["event_id"] in seen_ids:
            _fail("event_id_duplicate")
        seen_ids.add(event["event_id"])
        pair = (event["request_id"], event["event_type"])
        if pair in seen_pairs:
            _fail("duplicate_request", event["request_id"])
        seen_pairs.add(pair)
    return len(events)


def assert_request_not_replayed(events: list[Mapping[str, Any]], request_id: str) -> None:
    _id(request_id, "request_id")
    for item in events:
        event = validate_event(item)
        if event["request_id"] == request_id and event["event_type"] == "request_accepted":
            _fail("duplicate_request", request_id)
