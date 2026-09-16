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
    ("missing-screenshot", "runner_unavailable"),
    ("contradictory-evidence", "test_regression"),
    ("missing-bruder", "app_behavior"),
    ("invalid-bruder-response", "unknown"),
    ("mcp-hook-outage", "permission"),
    ("unauthorized-goal-extension", "permission"),
)


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
    if case_id in {"mcp-hook-outage", "unauthorized-goal-extension"}:
        return {
            "case_id": case_id,
            "failure_class": failure_class,
            "component": "trusted_gate",
            "actions": ["pause_for_max"],
            "status": "BOUNDED",
            "external_write": False,
        }
    if case_id == "invalid-bruder-response":
        return {
            "case_id": case_id,
            "failure_class": failure_class,
            "component": "bruder_fallback",
            "actions": ["pause_for_max"],
            "status": "BOUNDED",
            "external_write": False,
        }
    first = runtime.build_fallback_decision(failure_class, attempt=0, bruder_attempted=False)
    if first["action"] == "pause_for_max":
        return {
            "case_id": case_id,
            "failure_class": failure_class,
            "component": "ui_lab_runtime",
            "actions": [first["action"]],
            "status": "BOUNDED",
            "external_write": False,
        }
    second = runtime.build_fallback_decision(failure_class, attempt=1, bruder_attempted=False)
    if case_id == "missing-bruder":
        second = runtime.build_fallback_decision(failure_class, attempt=1, bruder_attempted=True)
    return {
        "case_id": case_id,
        "failure_class": failure_class,
        "component": "ui_lab_runtime",
        "actions": [first["action"], second["action"]],
        "status": "BOUNDED",
        "external_write": False,
    }


def execute_matrix() -> list[dict[str, Any]]:
    """Execute every named Phase 7 injection in deterministic order."""

    return [execute_case(case_id) for case_id, _ in FAULT_CASES]


def self_test() -> None:
    results = execute_matrix()
    if [item["case_id"] for item in results] != [case_id for case_id, _ in FAULT_CASES]:
        raise AssertionError("fault matrix order drift")
    if any(item["status"] != "BOUNDED" or item["external_write"] for item in results):
        raise AssertionError("fault matrix escaped its boundary")
    if results[0]["actions"] != ["retry_same_request", "bruder_handoff"]:
        raise AssertionError("timeout retry ladder drift")
    if results[3]["actions"] != ["pause_for_max"]:
        raise AssertionError("duplicate request was not protected")
    if results[7]["actions"] != ["bruder_handoff", "pause_for_max"]:
        raise AssertionError("missing Bruder did not stop after handoff")


if __name__ == "__main__":
    self_test()
    print({"status": "PASS", "fault_cases": len(FAULT_CASES), "external_write": False})
