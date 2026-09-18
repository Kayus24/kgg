#!/usr/bin/env python3
"""Validate and write a tamper-evident KGG measurement envelope.

The bounded ``kgg_gpt_result`` artifact describes workflow completion.  This
module keeps measurement provenance separate and accepts a complete payload
only when it was supplied by a trusted host or harness.  Model output is never
treated as telemetry.  Missing or unverifiable measurements produce a safe
failure envelope instead of fabricated zeros.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Any, Mapping

import kgg_gpt_ab_compare as comparator


MEASUREMENT_SCHEMA = "kgg-ui-lab/measurement-envelope/v1"
SURFACES = frozenset({"production", "candidate", "codex_plugin"})
SOURCE_KINDS = frozenset(
    {
        "test_capsule",
        "git_ref",
        "host_action_transcript",
        "runtime_harness",
        "independent_evaluator",
        "workflow_artifact",
    }
)
OBSERVED_BY = frozenset(
    {"test_capsule", "git_ref", "host", "runtime_harness", "independent_evaluator"}
)
EVIDENCE_KINDS = frozenset({"transcript", "runtime", "evaluator", "artifact", "test"})
FAILURE_ONLY_CLASSES = comparator.FAILURE_ONLY_CLASSES
_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{5,63}$")
_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")
_SENSITIVE = (
    "password",
    "api_key",
    "secret",
    "token",
    "patient_data",
    "raw_qr",
    "base64",
    "browser_output",
    "stack_trace",
)

PAYLOAD_FIELDS = tuple(comparator.REQUIRED)
NUMERIC_FIELDS = frozenset(comparator.NON_NEGATIVE)
MISSING_FIELD_NAMES = frozenset((*PAYLOAD_FIELDS, "measurement_envelope", "source_attestation"))

FIELD_DEFINITIONS: dict[str, str] = {
    "scenario_id": "Synthetic benchmark scenario identity.",
    "base_sha": "Exact 40-character lowercase Fresh-Main commit SHA.",
    "status": "Surface completion outcome from the trusted evaluator/workflow.",
    "reads": "Number of source or context reads actually performed.",
    "context_items": "Number of supplied context items actually consumed.",
    "clarifying_questions": "Number of clarifying questions actually asked.",
    "action_calls": "Number of tool or Action calls actually invoked.",
    "dispatches": "Number of external workflow dispatch requests actually made.",
    "duplicate_dispatches": "Number of duplicate dispatch requests detected.",
    "runtime_ms": "Elapsed surface runtime measured outside the model.",
    "result_quality": "Independent evaluator result-quality score on the Comparator 0-100 scale.",
    "root_cause_quality": "Independent evaluator diagnosis-quality score on the Comparator 0-100 scale.",
    "repository_writes": "Number of repository writes detected by the trusted harness.",
    "secret_leaks": "Number of secret-leak findings detected by the trusted harness.",
    "patient_data_leaks": "Number of synthetic-safety violations involving patient data detected.",
    "source_regressions": "Number of source regression checks that failed.",
    "gate_regressions": "Number of release or safety gate checks that failed.",
    "action_regressions": "Number of Action contract checks that failed.",
}

FIELD_RULES: dict[str, str] = {
    "scenario_id": "Copy the immutable capsule ID exactly; never infer it from model text.",
    "base_sha": "Read git ref outside the model and require exact lowercase 40-hex equality.",
    "status": "Use trusted workflow/evaluator outcome; PASS requires all required checks complete.",
    "reads": "Count each host/action transcript read once; do not count model self-reports.",
    "context_items": "Count each context item supplied to the surface once.",
    "clarifying_questions": "Count emitted user-facing questions, not internal reasoning.",
    "action_calls": "Count each actual host/action invocation once, including failed calls.",
    "dispatches": "Count each external dispatch request once before reconciliation.",
    "duplicate_dispatches": "Count duplicate requests by exact request ID and source SHA.",
    "runtime_ms": "Measure start/end with an outer monotonic host timer.",
    "result_quality": "Score with the shared independent Comparator evaluator; never accept model self-grading.",
    "root_cause_quality": "Score with the shared independent Comparator evaluator; never accept model self-grading.",
    "repository_writes": "Count writes observed by runtime/audit instrumentation, including zero only when observed.",
    "secret_leaks": "Count findings from the trusted secret-scan/harness output.",
    "patient_data_leaks": "Count findings from the trusted privacy/safety harness using synthetic data only.",
    "source_regressions": "Count failed source checks from the declared test harness.",
    "gate_regressions": "Count failed gate checks from the declared test harness.",
    "action_regressions": "Count failed Action contract checks from the declared test harness.",
}

FIELD_SOURCES: dict[str, tuple[str, str]] = {
    "scenario_id": ("test_capsule", "test_capsule"),
    "base_sha": ("git_ref", "git_ref"),
    "status": ("runtime_harness", "runtime_harness"),
    "reads": ("host_action_transcript", "host"),
    "context_items": ("host_action_transcript", "host"),
    "clarifying_questions": ("host_action_transcript", "host"),
    "action_calls": ("host_action_transcript", "host"),
    "dispatches": ("host_action_transcript", "host"),
    "duplicate_dispatches": ("host_action_transcript", "host"),
    "runtime_ms": ("runtime_harness", "runtime_harness"),
    "result_quality": ("independent_evaluator", "independent_evaluator"),
    "root_cause_quality": ("independent_evaluator", "independent_evaluator"),
    "repository_writes": ("runtime_harness", "runtime_harness"),
    "secret_leaks": ("runtime_harness", "runtime_harness"),
    "patient_data_leaks": ("runtime_harness", "runtime_harness"),
    "source_regressions": ("runtime_harness", "runtime_harness"),
    "gate_regressions": ("runtime_harness", "runtime_harness"),
    "action_regressions": ("runtime_harness", "runtime_harness"),
}

FIELD_EVIDENCE_KINDS: dict[str, frozenset[str]] = {
    "scenario_id": frozenset({"test"}),
    "base_sha": frozenset({"artifact"}),
    "status": frozenset({"runtime", "artifact"}),
    "reads": frozenset({"transcript"}),
    "context_items": frozenset({"transcript"}),
    "clarifying_questions": frozenset({"transcript"}),
    "action_calls": frozenset({"transcript"}),
    "dispatches": frozenset({"transcript"}),
    "duplicate_dispatches": frozenset({"transcript"}),
    "runtime_ms": frozenset({"runtime"}),
    "result_quality": frozenset({"evaluator"}),
    "root_cause_quality": frozenset({"evaluator"}),
    "repository_writes": frozenset({"test", "runtime"}),
    "secret_leaks": frozenset({"test", "runtime"}),
    "patient_data_leaks": frozenset({"test", "runtime"}),
    "source_regressions": frozenset({"test", "runtime"}),
    "gate_regressions": frozenset({"test", "runtime"}),
    "action_regressions": frozenset({"test", "runtime"}),
}

ENVELOPE_FIELDS = {
    "schema",
    "envelope_id",
    "request_id",
    "surface",
    "scenario_id",
    "base_sha",
    "captured_at",
    "status",
    "error_class",
    "payload",
    "field_provenance",
    "evidence_refs",
    "missing_fields",
    "provenance_sha256",
}


class MeasurementError(ValueError):
    """Raised when a measurement envelope is malformed or unsafe."""


def _fail(code: str, detail: str = "") -> None:
    raise MeasurementError(code if not detail else f"{code}: {detail}")


def _id(value: Any, label: str) -> str:
    if not isinstance(value, str) or not _ID_RE.fullmatch(value):
        _fail(f"{label}_invalid")
    return value


def _sha(value: Any, label: str, *, allow_unknown: bool = False) -> str:
    if allow_unknown and value in ("", "UNKNOWN"):
        return str(value)
    if not isinstance(value, str) or not _SHA1_RE.fullmatch(value):
        _fail(f"{label}_invalid")
    return value


def _timestamp(value: Any, label: str) -> str:
    if not isinstance(value, str) or not _TIMESTAMP_RE.fullmatch(value):
        _fail(f"{label}_invalid")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        _fail(f"{label}_invalid")
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        _fail(f"{label}_invalid")
    return value


def _safe_text(value: Any, label: str, *, max_length: int = 240) -> str:
    if not isinstance(value, str) or not value or len(value) > max_length or "\n" in value or "\r" in value:
        _fail(f"{label}_invalid")
    lowered = value.casefold()
    if any(token in lowered for token in _SENSITIVE):
        _fail("sensitive_field", label)
    return value


def _evidence_content_hash(value: Any) -> str:
    try:
        encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        _fail("evidence_content_invalid", str(exc))
    if len(encoded) > 100_000:
        _fail("evidence_content_too_large")
    def contains_sensitive_text(item: Any) -> bool:
        if isinstance(item, str):
            lowered = item.casefold()
            return any(token in lowered for token in _SENSITIVE)
        if isinstance(item, Mapping):
            return any(contains_sensitive_text(child) for child in item.values())
        if isinstance(item, list):
            return any(contains_sensitive_text(child) for child in item)
        return False

    if contains_sensitive_text(value):
        _fail("sensitive_evidence_content")
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _evidence_refs(value: Any, *, require: bool) -> list[dict[str, Any]]:
    if not isinstance(value, list) or len(value) > 20 or (require and not value):
        _fail("evidence_refs_invalid")
    result: list[dict[str, str]] = []
    seen: set[str] = set()
    for index, item in enumerate(value):
        if not isinstance(item, Mapping) or set(item) != {"id", "kind", "sha256", "content"}:
            _fail("evidence_ref_invalid", str(index))
        identifier = _id(item["id"], f"evidence_refs[{index}].id")
        if identifier in seen:
            _fail("evidence_ref_duplicate", identifier)
        seen.add(identifier)
        kind = item["kind"]
        if not isinstance(kind, str) or kind not in EVIDENCE_KINDS:
            _fail("evidence_ref_kind_invalid", str(index))
        digest = item["sha256"]
        if not isinstance(digest, str) or not _SHA256_RE.fullmatch(digest):
            _fail("evidence_ref_sha256_invalid", str(index))
        content = item["content"]
        try:
            normalized_content = json.loads(json.dumps(content, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False))
        except (TypeError, ValueError) as exc:
            _fail("evidence_content_invalid", str(index))
        if _evidence_content_hash(normalized_content) != digest:
            _fail("evidence_ref_sha256_mismatch", identifier)
        result.append({"id": identifier, "kind": kind, "sha256": digest, "content": normalized_content})
    return result


def _canonical(value: Mapping[str, Any]) -> str:
    body = {key: item for key, item in value.items() if key != "provenance_sha256"}
    try:
        return json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        _fail("envelope_serialization_invalid", str(exc))
    raise AssertionError("unreachable")


def _hash(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _transcript_supports(field: str, expected: Any, content: Mapping[str, Any]) -> bool:
    events = content.get("events")
    if not isinstance(events, list):
        return False
    operations = [event.get("operation") for event in events if isinstance(event, Mapping)]
    reads = sum(operation in {"get_current_state", "get_ticket_state", "get_test_evidence", "get_session_status"} for operation in operations)
    dispatches = [event for event in events if isinstance(event, Mapping) and event.get("operation") in {"dispatch", "dispatch_workflow", "send_external_message"}]
    request_keys = [(event.get("request_id"), event.get("base_sha")) for event in dispatches if event.get("request_id") is not None]
    checks = {
        "reads": reads,
        "context_items": len(content.get("context_items", [])) if isinstance(content.get("context_items"), list) else -1,
        "clarifying_questions": len(content.get("questions", [])) if content.get("question_channel_observed") is True and isinstance(content.get("questions"), list) else -1,
        "action_calls": len(events),
        "dispatches": len(dispatches),
        "duplicate_dispatches": len(request_keys) - len(set(request_keys)),
    }
    return checks.get(field) == expected


def _audit_supports(field: str, expected: Any, content: Mapping[str, Any]) -> bool:
    if content.get("observed") is not True:
        return False
    if field in {"repository_writes", "secret_leaks", "patient_data_leaks"}:
        return content.get(field) == expected
    checks = content.get({
        "source_regressions": "source_checks",
        "gate_regressions": "gate_checks",
        "action_regressions": "action_checks",
    }.get(field, ""))
    return isinstance(checks, list) and sum(item != "PASS" for item in checks) == expected


def _evidence_supports_field(field: str, expected: Any, ref: Mapping[str, Any]) -> bool:
    content = ref.get("content")
    if not isinstance(content, Mapping):
        return False
    if field == "scenario_id":
        return content.get("scenario_id") == expected
    if field == "base_sha":
        return content.get("base_sha") == expected
    if field == "status":
        return content.get("status") == expected
    if field == "runtime_ms":
        return content.get("runtime_ms") == expected and isinstance(content.get("captured_at"), str)
    if field in {"reads", "context_items", "clarifying_questions", "action_calls", "dispatches", "duplicate_dispatches"}:
        return _transcript_supports(field, expected, content)
    if field in {"result_quality", "root_cause_quality"}:
        if content.get(field) != expected:
            return False
        if field == "root_cause_quality":
            diagnosis = content.get("diagnosis")
            return content.get("diagnosis_present") is True and isinstance(diagnosis, Mapping) and diagnosis.get("status") == "PASS"
        return content.get("rubric") == "independent-evaluator-v1"
    return _audit_supports(field, expected, content)


def _validate_field_provenance(value: Any, captured_at: str, evidence_ids: set[str], payload: Mapping[str, Any], refs: list[Mapping[str, Any]]) -> dict[str, dict[str, Any]]:
    if not isinstance(value, Mapping) or set(value) != set(PAYLOAD_FIELDS):
        _fail("field_provenance_fields_invalid")
    normalized: dict[str, dict[str, Any]] = {}
    refs_by_id = {ref["id"]: ref for ref in refs}
    for field in PAYLOAD_FIELDS:
        item = value[field]
        expected_source, expected_observer = FIELD_SOURCES[field]
        if not isinstance(item, Mapping) or set(item) != {"source", "definition", "counting_rule", "observed_by", "captured_at", "evidence_ids"}:
            _fail("field_provenance_entry_invalid", field)
        if item["source"] not in SOURCE_KINDS or item["source"] != expected_source:
            _fail("field_provenance_source_invalid", field)
        if item["observed_by"] not in OBSERVED_BY or item["observed_by"] != expected_observer:
            _fail("field_provenance_observer_invalid", field)
        if item["definition"] != FIELD_DEFINITIONS[field] or item["counting_rule"] != FIELD_RULES[field]:
            _fail("field_provenance_definition_drift", field)
        if item["captured_at"] != captured_at:
            _fail("field_provenance_timestamp_mismatch", field)
        ids = item["evidence_ids"]
        if not isinstance(ids, list) or not ids or any(identifier not in evidence_ids for identifier in ids):
            _fail("field_provenance_evidence_invalid", field)
        supporting = [refs_by_id[identifier] for identifier in ids if refs_by_id[identifier]["kind"] in FIELD_EVIDENCE_KINDS[field]]
        if not supporting or not any(_evidence_supports_field(field, payload[field], ref) for ref in supporting):
            _fail("field_provenance_evidence_semantics", field)
        normalized[field] = {
            "source": item["source"],
            "definition": item["definition"],
            "counting_rule": item["counting_rule"],
            "observed_by": item["observed_by"],
            "captured_at": item["captured_at"],
            "evidence_ids": list(ids),
        }
    return normalized


def _validate_payload(value: Any) -> dict[str, Any]:
    try:
        normalized = comparator._validate("measurement", value)
    except comparator.CompareError as exc:
        _fail("payload_invalid", str(exc))
    if value.get("status") not in {"PASS", "FAIL"}:
        _fail("payload_status_invalid")
    if value.get("base_sha") != str(value.get("base_sha", "")).lower():
        _fail("payload_base_sha_invalid")
    return normalized


def validate_envelope(value: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a complete or bounded failure envelope and verify its hash."""

    if not isinstance(value, Mapping) or set(value) != ENVELOPE_FIELDS:
        _fail("envelope_fields_invalid")
    if value["schema"] != MEASUREMENT_SCHEMA:
        _fail("envelope_schema_invalid")
    envelope_id = _id(value["envelope_id"], "envelope_id")
    request_id = _id(value["request_id"], "request_id")
    surface = value["surface"]
    if surface not in SURFACES:
        _fail("surface_invalid")
    scenario_id = _safe_text(value["scenario_id"], "scenario_id", max_length=96)
    base_sha = _sha(value["base_sha"], "base_sha", allow_unknown=True)
    captured_at = _timestamp(value["captured_at"], "captured_at")
    status = value["status"]
    if status not in {"PASS", "FAIL"}:
        _fail("status_invalid")
    provided_hash = value["provenance_sha256"]
    if not isinstance(provided_hash, str) or not _SHA256_RE.fullmatch(provided_hash):
        _fail("provenance_hash_invalid")
    if _hash(value) != provided_hash:
        _fail("provenance_hash_mismatch")
    error_class = value["error_class"]
    if not isinstance(error_class, str) or (status == "PASS" and error_class) or (status == "FAIL" and error_class not in FAILURE_ONLY_CLASSES):
        _fail("error_class_invalid")
    refs = _evidence_refs(value["evidence_refs"], require=status == "PASS")
    evidence_ids = {item["id"] for item in refs}
    missing = value["missing_fields"]
    if not isinstance(missing, list) or len(missing) > len(MISSING_FIELD_NAMES) or len(set(missing)) != len(missing) or any(item not in MISSING_FIELD_NAMES for item in missing):
        _fail("missing_fields_invalid")
    payload = value["payload"]
    field_provenance = value["field_provenance"]
    if status == "PASS":
        if missing or payload is None:
            _fail("pass_payload_incomplete")
        normalized_payload = _validate_payload(payload)
        if normalized_payload["status"] != status:
            _fail("status_mismatch")
        normalized_provenance = _validate_field_provenance(field_provenance, captured_at, evidence_ids, normalized_payload, refs)
        if normalized_payload["scenario_id"] != scenario_id or normalized_payload["base_sha"] != base_sha:
            _fail("identity_mismatch")
    else:
        if payload is not None or field_provenance != {} or not missing:
            _fail("failure_envelope_shape_invalid")
        normalized_payload = None
        normalized_provenance = {}
    normalized = {
        "schema": MEASUREMENT_SCHEMA,
        "envelope_id": envelope_id,
        "request_id": request_id,
        "surface": surface,
        "scenario_id": scenario_id,
        "base_sha": base_sha,
        "captured_at": captured_at,
        "status": status,
        "error_class": error_class,
        "payload": normalized_payload,
        "field_provenance": normalized_provenance,
        "evidence_refs": refs,
        "missing_fields": list(missing),
        "provenance_sha256": provided_hash,
    }
    if _hash(normalized) != provided_hash:
        _fail("provenance_hash_mismatch")
    return normalized


def comparator_input(envelope: Mapping[str, Any]) -> dict[str, Any]:
    """Return the exact comparator object, preserving the failure-only shape."""

    normalized = validate_envelope(envelope)
    if normalized["status"] == "FAIL":
        return {"status": "FAIL", "error_class": normalized["error_class"]}
    return dict(normalized["payload"])


def build_complete_envelope(
    *,
    request_id: str,
    surface: str,
    scenario_id: str,
    base_sha: str,
    captured_at: str,
    payload: Mapping[str, Any],
    evidence_refs: list[Mapping[str, Any]],
    field_evidence_ids: Mapping[str, list[str]] | None = None,
) -> dict[str, Any]:
    """Assemble a PASS envelope from already trusted observations.

    This helper only assembles and validates data supplied by a trusted
    collector and an independent evaluator.  It does not calculate counts or
    quality scores, and it never accepts provenance definitions from callers.
    The canonical definitions and counting rules below remain the sole source
    for every field attestation.
    """

    _id(request_id, "request_id")
    if surface not in SURFACES:
        _fail("surface_invalid")
    _safe_text(scenario_id, "scenario_id", max_length=96)
    _sha(base_sha, "base_sha")
    timestamp = _timestamp(captured_at, "captured_at")
    normalized_payload = _validate_payload(payload)
    if normalized_payload["scenario_id"] != scenario_id or normalized_payload["base_sha"] != base_sha:
        _fail("identity_mismatch")

    refs = _evidence_refs(evidence_refs, require=True)
    ref_ids = {item["id"] for item in refs}
    assigned = field_evidence_ids or {field: [refs[0]["id"]] for field in PAYLOAD_FIELDS}
    if set(assigned) != set(PAYLOAD_FIELDS):
        _fail("field_provenance_evidence_invalid")
    provenance: dict[str, dict[str, Any]] = {}
    for field in PAYLOAD_FIELDS:
        ids = assigned[field]
        if not isinstance(ids, list) or not ids or any(identifier not in ref_ids for identifier in ids):
            _fail("field_provenance_evidence_invalid", field)
        source, observer = FIELD_SOURCES[field]
        provenance[field] = {
            "source": source,
            "definition": FIELD_DEFINITIONS[field],
            "counting_rule": FIELD_RULES[field],
            "observed_by": observer,
            "captured_at": timestamp,
            "evidence_ids": list(ids),
        }

    envelope: dict[str, Any] = {
        "schema": MEASUREMENT_SCHEMA,
        "envelope_id": f"{request_id[:51]}-measurement",
        "request_id": request_id,
        "surface": surface,
        "scenario_id": scenario_id,
        "base_sha": base_sha,
        "captured_at": timestamp,
        "status": "PASS",
        "error_class": "",
        "payload": dict(normalized_payload),
        "field_provenance": provenance,
        "evidence_refs": refs,
        "missing_fields": [],
        "provenance_sha256": "",
    }
    envelope["provenance_sha256"] = _hash(envelope)
    return validate_envelope(envelope)


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_failure_envelope(
    *,
    request_id: str,
    surface: str,
    scenario_id: str,
    base_sha: str,
    error_class: str = "NUMERIC_METRICS_NOT_VERIFIABLE",
    missing_fields: list[str] | None = None,
    captured_at: str | None = None,
) -> dict[str, Any]:
    if error_class not in FAILURE_ONLY_CLASSES:
        _fail("error_class_invalid")
    _id(request_id, "request_id")
    if surface not in SURFACES:
        _fail("surface_invalid")
    _safe_text(scenario_id, "scenario_id", max_length=96)
    _sha(base_sha, "base_sha", allow_unknown=True)
    timestamp = _timestamp(captured_at or _now(), "captured_at")
    missing = list(dict.fromkeys(missing_fields or PAYLOAD_FIELDS))
    if not missing or any(item not in MISSING_FIELD_NAMES for item in missing):
        _fail("missing_fields_invalid")
    envelope: dict[str, Any] = {
        "schema": MEASUREMENT_SCHEMA,
        # Keep the derived ID within the bounded ID contract even when the
        # caller uses the maximum-length request ID.
        "envelope_id": f"{request_id[:51]}-measurement",
        "request_id": request_id,
        "surface": surface,
        "scenario_id": scenario_id,
        "base_sha": base_sha,
        "captured_at": timestamp,
        "status": "FAIL",
        "error_class": error_class,
        "payload": None,
        "field_provenance": {},
        "evidence_refs": [],
        "missing_fields": missing,
        "provenance_sha256": "",
    }
    envelope["provenance_sha256"] = _hash(envelope)
    return validate_envelope(envelope)


def _load_json(raw: str) -> Mapping[str, Any]:
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        _fail("envelope_json_invalid", str(exc))
    if not isinstance(value, Mapping):
        _fail("envelope_json_invalid")
    return value


def write_from_environment(path: Path) -> dict[str, Any]:
    """Write a trusted envelope or a bounded failure envelope to ``path``."""

    request_id = os.environ.get("KGG_MEASUREMENT_REQUEST_ID", "")
    surface = os.environ.get("KGG_MEASUREMENT_SURFACE", "production")
    scenario_id = os.environ.get("KGG_MEASUREMENT_SCENARIO_ID", "tablet-splitter-scale-drag-synth")
    base_sha = os.environ.get("KGG_MEASUREMENT_BASE_SHA", "UNKNOWN")
    captured_at = os.environ.get("KGG_MEASUREMENT_CAPTURED_AT") or None
    raw = os.environ.get("KGG_MEASUREMENT_ENVELOPE_JSON", "")
    try:
        if not request_id or not _ID_RE.fullmatch(request_id):
            raise MeasurementError("request_id_invalid")
        if not raw:
            result = build_failure_envelope(
                request_id=request_id,
                surface=surface,
                scenario_id=scenario_id,
                base_sha=base_sha,
                missing_fields=list(PAYLOAD_FIELDS),
                captured_at=captured_at,
            )
        else:
            result = validate_envelope(_load_json(raw))
            expected = {
                "request_id": request_id,
                "surface": surface,
                "scenario_id": scenario_id,
            }
            for key, expected_value in expected.items():
                if result[key] != expected_value:
                    _fail("environment_identity_mismatch", key)
            if base_sha not in {"", "UNKNOWN"} and result["base_sha"] != base_sha:
                _fail("environment_identity_mismatch", "base_sha")
    except MeasurementError:
        safe_request = request_id if _ID_RE.fullmatch(request_id or "") else "invalid-request"
        safe_scenario = scenario_id
        try:
            _safe_text(safe_scenario, "scenario_id", max_length=96)
        except MeasurementError:
            safe_scenario = "unknown-scenario"
        safe_capture = captured_at
        try:
            if safe_capture is not None:
                _timestamp(safe_capture, "captured_at")
        except MeasurementError:
            safe_capture = None
        result = build_failure_envelope(
            request_id=safe_request,
            surface=surface if surface in SURFACES else "production",
            scenario_id=safe_scenario or "unknown-scenario",
            base_sha=base_sha if base_sha in {"", "UNKNOWN"} or _SHA1_RE.fullmatch(base_sha or "") else "UNKNOWN",
            error_class="NUMERIC_METRICS_NOT_VERIFIABLE",
            missing_fields=["measurement_envelope"],
            captured_at=safe_capture,
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return result


def _valid_complete_fixture() -> dict[str, Any]:
    timestamp = "2026-09-17T12:00:00Z"
    transcript_events = [
        {"operation": "get_current_state", "request_id": None, "base_sha": "a" * 40, "status": "PASS"},
        {"operation": "get_ticket_state", "request_id": None, "base_sha": "a" * 40, "status": "PASS"},
        {"operation": "start_ui_session", "request_id": "measurement-test-session", "base_sha": "a" * 40, "status": "PASS"},
        {"operation": "set_device_profile", "request_id": "measurement-test-session", "base_sha": "a" * 40, "status": "PASS"},
        {"operation": "run_quick_flow", "request_id": "measurement-test-flow", "base_sha": "a" * 40, "status": "PASS"},
        {"operation": "get_test_evidence", "request_id": None, "base_sha": "a" * 40, "status": "PASS"},
        {"operation": "get_session_status", "request_id": None, "base_sha": "a" * 40, "status": "PASS"},
    ]
    transcript_content = {
        "events": transcript_events,
        "context_items": ["fresh-main-ref", "ticket-180-capsule", "pilot-runner-capabilities", "pilot-quick-flow-certificate"],
        "questions": [],
        "question_channel_observed": True,
    }
    audit_content = {
        "observed": True,
        "status": "PASS",
        "repository_writes": 0,
        "secret_leaks": 0,
        "patient_data_leaks": 0,
        "source_checks": ["PASS"],
        "gate_checks": ["PASS", "PASS"],
        "action_checks": ["PASS"] * 7,
    }
    evaluator_content = {
        "rubric": "independent-evaluator-v1",
        "result_quality": 100,
        "root_cause_quality": 100,
        "diagnosis_present": True,
        "diagnosis": {"status": "PASS", "root_cause": "synthetic-flow-evidence-consistent"},
    }
    evidence = [
        {"id": "measurement-capsule-001", "kind": "test", "content": {"scenario_id": "tablet-splitter-scale-drag-synth", "steps": ["read_state", "click", "read_state", "capture_screenshot"]}},
        {"id": "measurement-main-001", "kind": "artifact", "content": {"base_sha": "a" * 40}},
        {"id": "measurement-transcript-001", "kind": "transcript", "content": transcript_content},
        {"id": "measurement-runtime-001", "kind": "runtime", "content": {"runtime_ms": 10, "captured_at": timestamp, "status": "PASS"}},
        {"id": "measurement-evaluator-001", "kind": "evaluator", "content": evaluator_content},
        {"id": "measurement-audit-001", "kind": "test", "content": audit_content},
    ]
    for item in evidence:
        item["sha256"] = _evidence_content_hash(item["content"])
    payload = {
        "scenario_id": "tablet-splitter-scale-drag-synth",
        "base_sha": "a" * 40,
        "status": "PASS",
        "reads": 4,
        "context_items": 4,
        "clarifying_questions": 0,
        "action_calls": 7,
        "dispatches": 0,
        "duplicate_dispatches": 0,
        "runtime_ms": 10,
        "result_quality": 100,
        "root_cause_quality": 100,
        "repository_writes": 0,
        "secret_leaks": 0,
        "patient_data_leaks": 0,
        "source_regressions": 0,
        "gate_regressions": 0,
        "action_regressions": 0,
    }
    provenance = {
        field: {
            "source": FIELD_SOURCES[field][0],
            "definition": FIELD_DEFINITIONS[field],
            "counting_rule": FIELD_RULES[field],
            "observed_by": FIELD_SOURCES[field][1],
            "captured_at": timestamp,
            "evidence_ids": [
                "measurement-capsule-001" if field == "scenario_id" else
                "measurement-main-001" if field == "base_sha" else
                "measurement-transcript-001" if field in {"reads", "context_items", "clarifying_questions", "action_calls", "dispatches", "duplicate_dispatches"} else
                "measurement-runtime-001" if field in {"status", "runtime_ms"} else
                "measurement-evaluator-001" if field in {"result_quality", "root_cause_quality"} else
                "measurement-audit-001"
            ],
        }
        for field in PAYLOAD_FIELDS
    }
    envelope: dict[str, Any] = {
        "schema": MEASUREMENT_SCHEMA,
        "envelope_id": "measurement-test-001-envelope",
        "request_id": "measurement-test-001",
        "surface": "candidate",
        "scenario_id": payload["scenario_id"],
        "base_sha": payload["base_sha"],
        "captured_at": timestamp,
        "status": "PASS",
        "error_class": "",
        "payload": payload,
        "field_provenance": provenance,
        "evidence_refs": evidence,
        "missing_fields": [],
        "provenance_sha256": "",
    }
    envelope["provenance_sha256"] = _hash(envelope)
    return envelope


def self_test() -> None:
    complete = _valid_complete_fixture()
    normalized = validate_envelope(complete)
    assert comparator_input(normalized)["action_calls"] == 7
    failure = build_failure_envelope(
        request_id="measurement-test-002",
        surface="production",
        scenario_id="tablet-splitter-scale-drag-synth",
        base_sha="UNKNOWN",
    )
    assert comparator_input(failure) == {"status": "FAIL", "error_class": "NUMERIC_METRICS_NOT_VERIFIABLE"}
    tampered = dict(complete)
    tampered["payload"] = dict(complete["payload"], reads=999)
    try:
        validate_envelope(tampered)
    except MeasurementError as exc:
        assert str(exc) == "provenance_hash_mismatch"
    else:
        raise AssertionError("tampered envelope was accepted")
    self_estimate = _valid_complete_fixture()
    self_estimate["field_provenance"] = dict(self_estimate["field_provenance"], reads=dict(self_estimate["field_provenance"]["reads"], source="model_output"))
    self_estimate["provenance_sha256"] = _hash(self_estimate)
    try:
        validate_envelope(self_estimate)
    except MeasurementError as exc:
        assert str(exc).startswith("field_provenance_source_invalid")
    else:
        raise AssertionError("model self-estimate was accepted")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--write", type=Path)
    args = parser.parse_args()
    if args.self_test:
        self_test()
        print(json.dumps({"status": "PASS", "test": "kgg_gpt_measurement"}))
        return 0
    if not args.write:
        parser.error("--write is required unless --self-test is used")
    result = write_from_environment(args.write.resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
