#!/usr/bin/env python3
"""The exactly-three initial, semantic UI-Lab Quick-Flow certificates."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import kgg_ui_lab_contract as contract
from kgg_ui_lab_session import QuickFlowRegistry


CERTIFIED_QUICK_FLOWS: tuple[dict[str, Any], ...] = (
    {
        "name": "admin-start-baseline",
        "version": "1.0.0",
        "preconditions": ["admin-preview", "synthetic-data-only"],
        "steps": [
            {"sequence": 1, "operation": "read_state", "label": "admin-ready", "expected": "admin-ready"},
            {"sequence": 2, "operation": "capture_screenshot", "label": "baseline-screen", "expected": "baseline-visible"},
        ],
        "expected_state": "admin-ready",
        "required_artifact_kinds": ["screenshot"],
        "pass_reason": "Admin preview starts in the expected synthetic baseline.",
        "fail_reason": "Admin preview did not expose the expected baseline state.",
        "cleanup": ["close-preview-tab", "release-session-lease"],
    },
    {
        "name": "pilot-180-reproduce",
        "version": "1.0.0",
        "preconditions": ["admin-preview", "ticket-180-selected", "synthetic-data-only"],
        "steps": [
            {"sequence": 1, "operation": "read_state", "label": "pilot-area-ready", "expected": "pilot-area-ready"},
            {"sequence": 2, "operation": "click", "label": "tablet-splitter-control", "expected": "control-focused"},
            {"sequence": 3, "operation": "read_state", "label": "scale-drag-state", "expected": "scale-drag-observed"},
            {"sequence": 4, "operation": "capture_screenshot", "label": "pilot-180-evidence", "expected": "pilot-180-visible"},
        ],
        "expected_state": "scale-drag-observed",
        "required_artifact_kinds": ["screenshot"],
        "pass_reason": "Ticket #180 behavior is reproduced with a bounded semantic flow.",
        "fail_reason": "Ticket #180 behavior or its expected evidence was not reproduced.",
        "cleanup": ["return-to-pilot-root", "close-preview-tab", "release-session-lease"],
    },
    {
        "name": "synthetic-qr-preview-link",
        "version": "1.0.0",
        "preconditions": ["admin-preview", "patient-preview", "synthetic-qr-image-only"],
        "steps": [
            {"sequence": 1, "operation": "read_state", "label": "admin-preview-ready", "expected": "admin-preview-ready"},
            {"sequence": 2, "operation": "click", "label": "synthetic-qr-image", "expected": "patient-link-ready"},
            {"sequence": 3, "operation": "read_state", "label": "linked-preview-ready", "expected": "linked-preview-ready"},
            {"sequence": 4, "operation": "capture_screenshot", "label": "preview-link-evidence", "expected": "preview-link-visible"},
        ],
        "expected_state": "linked-preview-ready",
        "required_artifact_kinds": ["screenshot"],
        "pass_reason": "Admin and patient previews are linked only through a synthetic QR image.",
        "fail_reason": "The preview link or its synthetic evidence was not available.",
        "cleanup": ["close-patient-preview", "close-admin-preview", "release-session-lease"],
    },
)


def validate_certified_quick_flows() -> tuple[dict[str, Any], ...]:
    if len(CERTIFIED_QUICK_FLOWS) != 3:
        raise contract.ContractError("quick_flow_certificate_count_invalid")
    names: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for flow in CERTIFIED_QUICK_FLOWS:
        expected_keys = {"name", "version", "preconditions", "steps", "expected_state", "required_artifact_kinds", "pass_reason", "fail_reason", "cleanup"}
        if set(flow) != expected_keys:
            raise contract.ContractError("quick_flow_certificate_fields_invalid")
        name, version = flow["name"], flow["version"]
        if not isinstance(name, str) or name in names or not name.startswith(("admin-", "pilot-", "synthetic-")):
            raise contract.ContractError("quick_flow_certificate_name_invalid")
        if not isinstance(version, str) or version != "1.0.0":
            raise contract.ContractError("quick_flow_certificate_version_invalid")
        names.add(name)
        if not isinstance(flow["preconditions"], list) or not flow["preconditions"]:
            raise contract.ContractError("quick_flow_preconditions_invalid")
        if not isinstance(flow["steps"], list) or not 1 <= len(flow["steps"]) <= 20:
            raise contract.ContractError("quick_flow_certificate_steps_invalid")
        seen_sequences: set[int] = set()
        runtime_steps: list[dict[str, str]] = []
        for expected_sequence, step in enumerate(flow["steps"], start=1):
            if not isinstance(step, dict) or set(step) != {"sequence", "operation", "label", "expected"}:
                raise contract.ContractError("quick_flow_certificate_step_fields_invalid")
            if step["sequence"] != expected_sequence or step["sequence"] in seen_sequences:
                raise contract.ContractError("quick_flow_certificate_sequence_invalid")
            seen_sequences.add(step["sequence"])
            if not isinstance(step["expected"], str) or not step["expected"]:
                raise contract.ContractError("quick_flow_expected_state_invalid")
            runtime_steps.append({"operation": step["operation"], "label": step["label"]})
        if flow["required_artifact_kinds"] != ["screenshot"]:
            raise contract.ContractError("quick_flow_required_artifacts_invalid")
        for key in ("expected_state", "pass_reason", "fail_reason"):
            if not isinstance(flow[key], str) or not flow[key]:
                raise contract.ContractError("quick_flow_certificate_text_invalid")
        if not isinstance(flow["cleanup"], list) or not flow["cleanup"]:
            raise contract.ContractError("quick_flow_cleanup_invalid")
        # Validate the selector-free projection using the existing strict store.
        registry = QuickFlowRegistry()
        runtime_flow = {"name": name, "version": version, "steps": runtime_steps}
        registry.register(runtime_flow)
        normalized.append(deepcopy(flow))
    return tuple(normalized)


def runtime_flows() -> tuple[dict[str, Any], ...]:
    """Return the exact three certificate projections accepted by the runtime."""

    return tuple(
        {
            "name": flow["name"],
            "version": flow["version"],
            "steps": [{"operation": step["operation"], "label": step["label"]} for step in flow["steps"]],
        }
        for flow in validate_certified_quick_flows()
    )
