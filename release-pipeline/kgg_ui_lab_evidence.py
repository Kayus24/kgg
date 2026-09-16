#!/usr/bin/env python3
"""Canonical, synthetic and tamper-evident UI Lab evidence artifacts."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import re
from typing import Any, Mapping

import kgg_ui_lab_contract as contract
import kgg_ui_lab_runtime as runtime


EVIDENCE_SCHEMA = "kgg-ui-lab/evidence/v1"
_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{5,63}$")
_REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_./-]{0,511}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_LABEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._:/-]{0,199}$")
_STEP_STATUSES = frozenset({"pass", "fail", "blocked"})
_RESULT_STATUSES = frozenset({"PASS", "FAIL", "BLOCKED"})
_SAFE_ARTIFACT_KINDS = frozenset({"screenshot", "capture", "result", "metadata", "dom-snapshot"})
_SENSITIVE = ("raw_qr", "base64", "password", "api_key", "secret", "patient_data", "selector", "stack_trace", "browser_output")


class ContractError(ValueError):
    """Raised when an evidence artifact is malformed or unsafe."""


def _fail(code: str, detail: str = "") -> None:
    raise ContractError(code if not detail else f"{code}: {detail}")


def _id(value: Any, label: str) -> str:
    if not isinstance(value, str) or not _ID_RE.fullmatch(value):
        _fail(f"{label}_invalid")
    return value


def _text(value: Any, label: str, *, max_length: int = 200) -> str:
    if not isinstance(value, str) or not value or len(value) > max_length or not _LABEL_RE.fullmatch(value):
        _fail(f"{label}_invalid")
    lowered = value.casefold()
    if any(token in lowered for token in _SENSITIVE) or re.search(r"\btoken\b", lowered):
        _fail("sensitive_field", label)
    return value


def _timestamp(value: Any, label: str) -> datetime:
    if not isinstance(value, str) or not value:
        _fail(f"{label}_invalid")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        _fail(f"{label}_invalid")
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        _fail(f"{label}_invalid")
    return parsed.astimezone(timezone.utc)


def _artifact(value: Any) -> dict[str, str]:
    if not isinstance(value, Mapping) or set(value) != {"id", "kind", "ref", "sha256"}:
        _fail("artifact_invalid")
    artifact_id = _id(value["id"], "artifact_id")
    kind = value["kind"]
    if not isinstance(kind, str) or kind not in _SAFE_ARTIFACT_KINDS:
        if isinstance(kind, str) and any(token in kind.casefold() for token in _SENSITIVE):
            _fail("sensitive_field", "artifact.kind")
        _fail("artifact_kind_invalid")
    ref = value["ref"]
    if not isinstance(ref, str) or not _REF_RE.fullmatch(ref) or any(token in ref.casefold() for token in _SENSITIVE):
        _fail("sensitive_field", "artifact.ref")
    digest = value["sha256"]
    if not isinstance(digest, str) or not _SHA256_RE.fullmatch(digest):
        _fail("artifact_sha256_invalid")
    return {"id": artifact_id, "kind": kind, "ref": ref, "sha256": digest}


def _step(value: Any, expected_sequence: int) -> dict[str, Any]:
    if not isinstance(value, Mapping) or set(value) != {"sequence", "label", "expected", "actual", "status", "artifact_refs"}:
        _fail("step_invalid")
    if value["sequence"] != expected_sequence:
        _fail("step_sequence_invalid")
    label = _text(value["label"], "step_label")
    expected = _text(value["expected"], "step_expected")
    actual = _text(value["actual"], "step_actual")
    status = value["status"]
    if status not in _STEP_STATUSES:
        _fail("step_status_invalid")
    refs = value["artifact_refs"]
    if not isinstance(refs, list) or len(refs) > 10 or any(not isinstance(ref, str) or not _ID_RE.fullmatch(ref) for ref in refs):
        _fail("step_artifact_refs_invalid")
    if status == "pass" and expected != actual:
        _fail("evidence_conflict", label)
    return {
        "sequence": expected_sequence,
        "label": label,
        "expected": expected,
        "actual": actual,
        "status": status,
        "artifact_refs": list(refs),
    }


def _canonical(value: Mapping[str, Any]) -> str:
    body = {key: item for key, item in value.items() if key != "provenance_sha256"}
    try:
        return json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        _fail("evidence_serialization_invalid", str(exc))
    raise AssertionError("unreachable")


def _provenance_hash(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _validated_core(value: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        _fail("evidence_invalid")
    expected_keys = {
        "schema",
        "evidence_id",
        "session_id",
        "request_id",
        "flow_name",
        "flow_version",
        "app_name",
        "main_sha",
        "preview_sha",
        "device_profile",
        "viewport",
        "runner_id",
        "runner_version",
        "started_at",
        "ended_at",
        "status",
        "error_class",
        "steps",
        "artifacts",
        "provenance_sha256",
    }
    if set(value) != expected_keys:
        _fail("evidence_fields_invalid")
    if value["schema"] != EVIDENCE_SCHEMA:
        _fail("evidence_schema_invalid")
    for key in ("evidence_id", "session_id", "request_id", "runner_id"):
        _id(value[key], key)
    _text(value["flow_name"], "flow_name", max_length=64)
    if not isinstance(value["flow_version"], str) or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", value["flow_version"]):
        _fail("flow_version_invalid")
    if value["app_name"] not in {"admin", "patient"}:
        _fail("app_name_invalid")
    if not isinstance(value["main_sha"], str) or not re.fullmatch(r"[0-9a-f]{40}", value["main_sha"]):
        _fail("main_sha_invalid")
    if value["preview_sha"] is not None and (not isinstance(value["preview_sha"], str) or not re.fullmatch(r"[0-9a-f]{40}", value["preview_sha"])):
        _fail("preview_sha_invalid")
    if value["device_profile"] not in contract.DEVICE_PROFILES:
        _fail("device_profile_invalid")
    viewport = value["viewport"]
    if not isinstance(viewport, Mapping) or set(viewport) != {"width", "height", "device_scale_factor"}:
        _fail("viewport_invalid")
    if not isinstance(viewport["width"], int) or not isinstance(viewport["height"], int):
        _fail("viewport_invalid")
    if not 240 <= viewport["width"] <= 10000 or not 240 <= viewport["height"] <= 10000:
        _fail("viewport_invalid")
    if not isinstance(viewport["device_scale_factor"], (int, float)) or isinstance(viewport["device_scale_factor"], bool):
        _fail("viewport_invalid")
    if not 0.5 <= viewport["device_scale_factor"] <= 4:
        _fail("viewport_invalid")
    _text(value["runner_version"], "runner_version", max_length=32)
    started = _timestamp(value["started_at"], "started_at")
    ended = _timestamp(value["ended_at"], "ended_at")
    if ended <= started:
        _fail("evidence_time_invalid")
    if value["status"] not in _RESULT_STATUSES:
        _fail("evidence_status_invalid")
    error_class = value["error_class"]
    if not isinstance(error_class, str) or (value["status"] == "PASS" and error_class) or (value["status"] != "PASS" and error_class not in runtime.FAILURE_CLASSES):
        _fail("error_class_invalid")
    provided_hash = value["provenance_sha256"]
    if not isinstance(provided_hash, str) or not _SHA256_RE.fullmatch(provided_hash):
        _fail("evidence_hash_invalid")
    # Check provenance before interpreting step semantics.  This makes a
    # post-run mutation observable as tampering rather than as a new result.
    if _provenance_hash(value) != provided_hash:
        _fail("evidence_hash_mismatch")
    steps = value["steps"]
    if not isinstance(steps, list) or not 1 <= len(steps) <= 50:
        _fail("steps_invalid")
    normalized_steps = [_step(item, index) for index, item in enumerate(steps, start=1)]
    artifacts = value["artifacts"]
    if not isinstance(artifacts, list) or len(artifacts) > 100:
        _fail("artifacts_invalid")
    normalized_artifacts = [_artifact(item) for item in artifacts]
    ids = [item["id"] for item in normalized_artifacts]
    if len(ids) != len(set(ids)):
        _fail("artifact_duplicate")
    valid_ids = set(ids)
    for step in normalized_steps:
        if any(ref not in valid_ids for ref in step["artifact_refs"]):
            _fail("artifact_missing")
    if value["status"] == "PASS" and any(step["status"] != "pass" for step in normalized_steps):
        _fail("evidence_conflict", "PASS requires all steps to pass")
    normalized = dict(value)
    normalized["viewport"] = dict(viewport)
    normalized["steps"] = normalized_steps
    normalized["artifacts"] = normalized_artifacts
    if _provenance_hash(normalized) != provided_hash:
        _fail("evidence_hash_mismatch")
    return normalized


def build_evidence(
    *,
    session: Mapping[str, Any],
    started_at: str,
    ended_at: str,
    status: str,
    error_class: str,
    steps: list[Mapping[str, Any]],
    artifacts: list[Mapping[str, Any]],
    required_artifact_kinds: set[str] | None = None,
) -> dict[str, Any]:
    session_value = contract.validate_session(session)
    normalized_artifacts = [_artifact(item) for item in artifacts]
    required = required_artifact_kinds or set()
    kinds = {item["kind"] for item in normalized_artifacts}
    missing = required - kinds
    if missing:
        _fail("evidence_missing", ", ".join(sorted(missing)))
    evidence: dict[str, Any] = {
        "schema": EVIDENCE_SCHEMA,
        "evidence_id": f"{session_value['session_id']}-evidence-001",
        "session_id": session_value["session_id"],
        "request_id": session_value["request_id"],
        "flow_name": session_value["quick_flow"]["name"],
        "flow_version": session_value["quick_flow"]["version"],
        "app_name": session_value["app"]["name"],
        "main_sha": session_value["app"]["main_sha"],
        "preview_sha": session_value["app"]["preview_sha"],
        "device_profile": session_value["device_profile"],
        "viewport": dict(session_value["viewport"]),
        "runner_id": session_value["runner"]["runner_id"],
        "runner_version": session_value["runner"]["version"],
        "started_at": started_at,
        "ended_at": ended_at,
        "status": status,
        "error_class": error_class,
        "steps": [dict(item) for item in steps],
        "artifacts": normalized_artifacts,
    }
    # Derive the immutable hash only after all semantic fields are assembled.
    # _validated_core then performs the full validation and verifies this hash.
    evidence["provenance_sha256"] = _provenance_hash(evidence)
    return _validated_core(evidence)


def validate_evidence(value: Mapping[str, Any]) -> dict[str, Any]:
    return _validated_core(value)
