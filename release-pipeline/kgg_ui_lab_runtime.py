#!/usr/bin/env python3
"""Fail-closed retry and Bruder-GPT escalation primitives for the UI Lab.

This module does not open a browser or send a chat message.  It produces a
small local queue record that a separately authorised adapter may deliver to
the Bruder GPT after the contract and user-confirmation checks pass.
"""

from __future__ import annotations

import re
from typing import Any, Mapping

import kgg_brain_relay_worker as brain_relay


BRUDER_HANDOFF_SCHEMA = "kgg-ui-lab/bruder-fallback/v1"
BRUDER_RESPONSE_SCHEMA = "kgg-ui-lab/bruder-response/v1"
FAILURE_CLASSES = frozenset(
    {
        "stale_context",
        "payload_schema",
        "test_regression",
        "app_behavior",
        "browser_transport",
        "runner_unavailable",
        "permission",
        "network_timeout",
        "editor_drift",
        "duplicate_request",
        "unknown",
    }
)
_TRANSIENT = frozenset({"browser_transport", "runner_unavailable", "network_timeout", "stale_context"})
_MAX_ONLY = frozenset({"permission", "editor_drift", "duplicate_request"})
_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{5,63}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{2,63}$")
_SENSITIVE = ("raw_qr", "base64", "password", "api_key", "secret", "patient_data", "selector", "stack_trace", "browser_output")
_TACTICAL_PATCH_KEYS = frozenset({"retry_budget", "timeout_ms", "step_order", "evidence_fields", "quick_flow"})


class ContractError(ValueError):
    """A safe, user-visible fallback contract error."""


def _fail(code: str, detail: str = "") -> None:
    raise ContractError(code if not detail else f"{code}: {detail}")


def _safe_text(value: Any, label: str, max_length: int = 800) -> str:
    if not isinstance(value, str) or not value or len(value) > max_length or any(ord(char) < 32 for char in value):
        _fail(f"{label}_invalid")
    lowered = value.casefold()
    if any(token in lowered for token in _SENSITIVE) or re.search(r"\btoken\b", lowered):
        _fail("sensitive_field", label)
    return value


def _id(value: Any, label: str) -> str:
    if not isinstance(value, str) or not _ID_RE.fullmatch(value):
        _fail(f"{label}_invalid")
    return value


def classify_failure(step: str, detail: str = "") -> str:
    """Map internal symptoms to the bounded public failure classes."""

    text = f"{step} {detail}".casefold()
    if any(token in text for token in ("payload", "schema", "required field")):
        return "payload_schema"
    if any(token in text for token in ("duplicate", "replay", "idempotency")):
        return "duplicate_request"
    if any(token in text for token in ("permission", "forbidden", "access denied", "gate")):
        return "permission"
    if any(token in text for token in ("editor drift", "editor sync", "live editor")):
        return "editor_drift"
    if any(token in text for token in ("websocket", "browser transport", "connection reset")):
        return "browser_transport"
    if any(token in text for token in ("runner unavailable", "runner offline", "capability missing")):
        return "runner_unavailable"
    if any(token in text for token in ("timeout", "timed out", "network", "deadline")):
        return "network_timeout"
    if any(token in text for token in ("regression", "assertion", "test failed", "baseline")):
        return "test_regression"
    if any(token in text for token in ("stale", "context drift", "source sha")):
        return "stale_context"
    if any(token in text for token in ("ui", "quick flow", "state", "click", "layout")):
        return "app_behavior"
    return "unknown"


def build_fallback_decision(failure_class: str, *, attempt: int, bruder_attempted: bool) -> dict[str, Any]:
    if failure_class not in FAILURE_CLASSES:
        _fail("failure_class_invalid")
    if not isinstance(attempt, int) or isinstance(attempt, bool) or attempt < 0:
        _fail("attempt_invalid")
    if not isinstance(bruder_attempted, bool):
        _fail("bruder_attempted_invalid")
    if failure_class in _MAX_ONLY:
        return {
            "action": "pause_for_max",
            "failure_class": failure_class,
            "reason": "Protected permission, editor, replay, or gate state requires Max review.",
        }
    if failure_class in _TRANSIENT and attempt < 1:
        return {
            "action": "retry_same_request",
            "failure_class": failure_class,
            "reason": "One fresh, unchanged retry is allowed before escalation.",
        }
    if not bruder_attempted:
        return {
            "action": "bruder_handoff",
            "failure_class": failure_class,
            "reason": "The bounded retry budget is exhausted; queue a Bruder plan request.",
        }
    return {
        "action": "pause_for_max",
        "failure_class": failure_class,
        "reason": "Bruder fallback was already attempted; stop and request Max review.",
    }


def _validate_evidence(evidence: Any) -> list[dict[str, str]]:
    if not isinstance(evidence, list) or len(evidence) > 20:
        _fail("evidence_invalid")
    validated: list[dict[str, str]] = []
    for item in evidence:
        if not isinstance(item, Mapping) or set(item) != {"kind", "ref", "sha256"}:
            _fail("evidence_invalid")
        kind = item["kind"]
        ref = item["ref"]
        digest = item["sha256"]
        if not isinstance(kind, str) or not _SLUG_RE.fullmatch(kind):
            _fail("evidence_invalid", "kind")
        if not isinstance(ref, str) or not ref or len(ref) > 512 or any(token in ref.casefold() for token in _SENSITIVE):
            _fail("sensitive_field", "evidence.ref")
        if not isinstance(digest, str) or not _SHA256_RE.fullmatch(digest):
            _fail("evidence_invalid", "sha256")
        validated.append({"kind": kind, "ref": ref, "sha256": digest})
    return validated


def build_bruder_handoff(
    *,
    task_id: str,
    session_id: str,
    request_id: str,
    failure_class: str,
    problem_summary: str,
    evidence: list[Mapping[str, Any]],
) -> dict[str, Any]:
    """Create a local-only handoff; no external GPT communication happens here."""

    _id(task_id, "task_id")
    _id(session_id, "session_id")
    _id(request_id, "request_id")
    if failure_class not in FAILURE_CLASSES:
        _fail("failure_class_invalid")
    summary = _safe_text(problem_summary, "problem_summary")
    validated_evidence = _validate_evidence(evidence)
    return {
        "schema": BRUDER_HANDOFF_SCHEMA,
        "transport_schema": brain_relay.HANDOFF_SCHEMA,
        "task_id": task_id,
        "session_id": session_id,
        "request_id": request_id,
        "failure_class": failure_class,
        "problem_summary": summary,
        "observed_evidence": validated_evidence,
        "requested_response": "small_fix_plan_or_tactical_goal_patch",
        "constraints": [
            "Do not change objective, scope, safety gates, hashes, permissions, or release state.",
            "Do not send secrets, patient data, raw browser output, or raw QR payload.",
            "Return a bounded plan with evidence and explicit blockers.",
        ],
        "delivery": "local_queue_only",
        "status": "PENDING_USER_CONFIRMATION",
    }


def accept_bruder_response(value: Mapping[str, Any]) -> dict[str, Any]:
    """Accept only a bounded tactical proposal; protected changes stop at Max."""

    if not isinstance(value, Mapping) or set(value) != {"schema", "decision", "plan", "goal_patch", "requires_max"}:
        _fail("bruder_response_invalid")
    if value["schema"] != BRUDER_RESPONSE_SCHEMA:
        _fail("bruder_response_schema_invalid")
    if value["decision"] not in {"tactical_plan", "goal_change_proposal", "blocked"}:
        _fail("bruder_response_invalid", "decision")
    plan = value["plan"]
    if not isinstance(plan, list) or not 1 <= len(plan) <= 8 or any(not isinstance(item, str) or not item for item in plan):
        _fail("bruder_plan_invalid")
    patch = value["goal_patch"]
    if not isinstance(patch, Mapping):
        _fail("goal_patch_invalid")
    unknown = set(patch) - _TACTICAL_PATCH_KEYS
    if unknown:
        _fail("goal_patch_protected", ", ".join(sorted(unknown)))
    if "retry_budget" in patch and (not isinstance(patch["retry_budget"], int) or not 0 <= patch["retry_budget"] <= 1):
        _fail("goal_patch_invalid", "retry_budget")
    if "timeout_ms" in patch and (not isinstance(patch["timeout_ms"], int) or not 1000 <= patch["timeout_ms"] <= 1_800_000):
        _fail("goal_patch_invalid", "timeout_ms")
    for key in ("step_order", "evidence_fields"):
        if key in patch and (not isinstance(patch[key], list) or any(not isinstance(item, str) for item in patch[key])):
            _fail("goal_patch_invalid", key)
    if "quick_flow" in patch and (not isinstance(patch["quick_flow"], str) or not _SLUG_RE.fullmatch(patch["quick_flow"])):
        _fail("goal_patch_invalid", "quick_flow")
    if not isinstance(value["requires_max"], bool):
        _fail("bruder_response_invalid", "requires_max")
    if value["decision"] != "tactical_plan" or value["requires_max"]:
        return {"status": "MAX_REQUIRED", "plan": list(plan), "goal_patch": dict(patch)}
    return {"status": "TACTICAL_ACCEPTED", "plan": list(plan), "goal_patch": dict(patch)}

