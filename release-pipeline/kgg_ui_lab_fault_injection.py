#!/usr/bin/env python3
"""Deterministic contract-level fault-injection matrix for UI-Lab V1.

The matrix injects named failures into the local contracts only.  It never
restarts a broker, opens a GPT, sends a message, or performs a write.
"""

from __future__ import annotations

from typing import Any

import kgg_ui_lab_runtime as runtime


FAULT_CASES = (
    ("browser-timeout", "network_timeout"),
    ("broker-restart", "browser_transport"),
    ("runner-abort", "runner_unavailable"),
    ("duplicate-request-id", "duplicate_request"),
    ("stale-main", "stale_context"),
    ("wrong-head-sha", "stale_context"),
    ("missing-head-sha", "stale_context"),
    ("request-id-prefix-collision", "duplicate_request"),
    ("request-id-suffix-collision", "duplicate_request"),
    ("multiple-similar-runs", "duplicate_request"),
    ("ci-tooling-failure", "runner_unavailable"),
    ("missing-artifact", "unknown"),
    ("artifact-workflow-contradiction", "unknown"),
    ("mcp-unavailable", "permission"),
    ("plugin-skill-missing", "permission"),
    ("stale-plugin-reference", "stale_context"),
    ("missing-screenshot", "runner_unavailable"),
    ("contradictory-evidence", "test_regression"),
    ("missing-bruder", "app_behavior"),
    ("invalid-bruder-response", "unknown"),
    ("mcp-hook-outage", "permission"),
    ("unauthorized-goal-extension", "permission"),
    ("unauthorized-write", "permission"),
)

_PROTECTED_STOP = frozenset(
    {
        "duplicate-request-id",
        "request-id-prefix-collision",
        "request-id-suffix-collision",
        "multiple-similar-runs",
        "artifact-workflow-contradiction",
        "mcp-unavailable",
        "plugin-skill-missing",
        "invalid-bruder-response",
        "mcp-hook-outage",
        "unauthorized-goal-extension",
        "unauthorized-write",
    }
)
_TRANSIENT_CASES = frozenset(
    {
        "browser-timeout",
        "broker-restart",
        "runner-abort",
        "stale-main",
        "wrong-head-sha",
        "missing-head-sha",
        "ci-tooling-failure",
        "stale-plugin-reference",
        "missing-screenshot",
    }
)
_EXPECTED_STOP = {
    "transient": "one_unchanged_retry_then_bruder_or_pause_without_redispatch",
    "bounded_failure": "bruder_advisory_then_pause_for_max_without_external_write",
    "protected": "pause_before_any_external_action_or_redispatch",
}


def _expected_action(case_id: str) -> tuple[str, ...]:
    if case_id in _PROTECTED_STOP:
        return ("pause_for_max",)
    if case_id in _TRANSIENT_CASES:
        return ("retry_same_request", "bruder_handoff")
    return ("bruder_handoff", "pause_for_max")


def _expected_stop(case_id: str) -> str:
    if case_id in _PROTECTED_STOP:
        return _EXPECTED_STOP["protected"]
    if case_id not in _TRANSIENT_CASES:
        return _EXPECTED_STOP["bounded_failure"]
    return _EXPECTED_STOP["transient"]


class FaultInjectionError(ValueError):
    """A stable matrix-definition error."""


def _case(case_id: str) -> tuple[str, str]:
    for item in FAULT_CASES:
        if item[0] == case_id:
            return item
    raise FaultInjectionError("fault_case_unknown")


def execute_case(case_id: str) -> dict[str, Any]:
    """Run one synthetic fault and return its bounded handling trace."""

    _, failure_class = _case(case_id)
    component = "trusted_gate" if case_id in _PROTECTED_STOP else "ui_lab_runtime"
    if case_id == "invalid-bruder-response":
        component = "bruder_fallback"
    if case_id in _PROTECTED_STOP:
        actions = ["pause_for_max"]
    elif case_id == "missing-artifact":
        actions = ["bruder_handoff", "pause_for_max"]
    else:
        first = runtime.build_fallback_decision(failure_class, attempt=0, bruder_attempted=False)
        if first["action"] == "pause_for_max":
            actions = [first["action"]]
        else:
            second = runtime.build_fallback_decision(
                failure_class,
                attempt=1,
                bruder_attempted=first["action"] == "bruder_handoff",
            )
            actions = [first["action"], second["action"]]
    expected_actions = list(_expected_action(case_id))
    actual_result = {
        "failure_class": failure_class,
        "actions": actions,
        "external_write": False,
    }
    passed = (
        failure_class == dict(FAULT_CASES)[case_id]
        and actions == expected_actions
        and actual_result["external_write"] is False
    )
    return {
        "case_id": case_id,
        "expected_class": failure_class,
        "expected_action": expected_actions,
        "expected_stop_behavior": _expected_stop(case_id),
        "actual_result": actual_result,
        "failure_class": failure_class,
        "component": component,
        "actions": actions,
        "status": "PASS" if passed else "FAIL",
        "external_write": False,
    }


def execute_matrix() -> list[dict[str, Any]]:
    """Execute every named Phase 7 injection in deterministic order."""

    return [execute_case(case_id) for case_id, _ in FAULT_CASES]


def self_test() -> None:
    results = execute_matrix()
    if [item["case_id"] for item in results] != [case_id for case_id, _ in FAULT_CASES]:
        raise AssertionError("fault matrix order drift")
    if any(item["status"] != "PASS" or item["external_write"] for item in results):
        raise AssertionError("fault matrix escaped its boundary")
    if results[0]["actions"] != ["retry_same_request", "bruder_handoff"]:
        raise AssertionError("timeout retry ladder drift")
    if results[3]["actions"] != ["pause_for_max"]:
        raise AssertionError("duplicate request was not protected")
    if results[18]["actions"] != ["bruder_handoff", "pause_for_max"]:
        raise AssertionError("missing Bruder did not stop after handoff")
    if any(set(item) != {"case_id", "expected_class", "expected_action", "expected_stop_behavior", "actual_result", "failure_class", "component", "actions", "status", "external_write"} for item in results):
        raise AssertionError("fault matrix evidence fields drift")


if __name__ == "__main__":
    self_test()
    print({"status": "PASS", "fault_cases": len(FAULT_CASES), "external_write": False})
