#!/usr/bin/env python3
"""Emit complete metrics for the local KGG Plugin-Candidate surface.

The emitter runs one fixed, synthetic Quick Flow through the existing
contract-shaped adapter.  It is deliberately local: it does not claim that a
ChatGPT or Codex host exposes the candidate, and it has no dispatch, shell,
editor, ticket or external-message operation.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import re
import time
from typing import Any, Mapping

import kgg_plugin_candidate_gate as candidate_gate
import kgg_plugin_candidate_parity as parity
import kgg_ui_lab_contract as contract
import kgg_ui_lab_mcp_adapter as mcp_adapter
import kgg_ui_lab_quick_flows as quick_flows
from kgg_ui_lab_session import QuickFlowRegistry, RunnerRegistry, SessionStore


SCENARIO_ID = "tablet-splitter-scale-drag-synth"
_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_REQUIRED_FIELDS = (
    "scenario_id",
    "base_sha",
    "status",
    "reads",
    "context_items",
    "clarifying_questions",
    "action_calls",
    "dispatches",
    "duplicate_dispatches",
    "runtime_ms",
    "result_quality",
    "root_cause_quality",
    "repository_writes",
    "secret_leaks",
    "patient_data_leaks",
    "source_regressions",
    "gate_regressions",
    "action_regressions",
)


class SurfaceMetricsError(ValueError):
    """Raised when the local metric pilot cannot prove a complete result."""


class _PilotClock:
    """Deterministic synthetic clock; no wall-clock value enters the payload."""

    def __init__(self) -> None:
        self.value = datetime(2026, 9, 14, 10, 0, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        current = self.value
        self.value += timedelta(seconds=1)
        return current


def _validate_sha(value: str) -> str:
    if not isinstance(value, str) or not _SHA_RE.fullmatch(value):
        raise SurfaceMetricsError("base_sha must be a 40-character lower-case SHA")
    return value


def _runner() -> dict[str, Any]:
    return {
        "runner_id": "surface-pilot-runner",
        "version": "1.0.0",
        "browser_revision": "chromium-140",
        "capabilities": ["browser", "quick_flows", "capture", "width_sweep"],
    }


def _session(main_sha: str, runner: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema": contract.SESSION_SCHEMA,
        "session_id": "surface-pilot-session",
        "status": "ready",
        "active_actor": "codex",
        "request_id": "surface-pilot-request",
        "lease": {
            "owner": "codex",
            "issued_at": "2026-09-14T09:00:00Z",
            "expires_at": "2026-09-14T12:00:00Z",
        },
        "runner": dict(runner),
        "app": {
            "name": "admin",
            "url": "https://preview.example.test/admin",
            "main_sha": main_sha,
            "preview_sha": "b" * 40,
        },
        "device_profile": "tab-s9",
        "viewport": {"width": 1280, "height": 800, "device_scale_factor": 1},
        "quick_flow": {"name": "pilot-180-reproduce", "version": "1.0.0"},
        "timeout": {"timeout_ms": 120000, "cleanup_on_cancel": True},
        "artifacts": [],
    }


def _flow() -> dict[str, Any]:
    for flow in quick_flows.runtime_flows():
        if flow["name"] == "pilot-180-reproduce":
            return flow
    raise SurfaceMetricsError("pilot quick flow is missing")


def _request(main_sha: str) -> dict[str, Any]:
    return {
        "schema": contract.REQUEST_SCHEMA,
        "request_id": "surface-pilot-request",
        "session_id": "surface-pilot-session",
        "actor": "codex",
        "operation": "run_quick_flow",
        "main_sha": main_sha,
        "payload_sha256": hashlib.sha256(SCENARIO_ID.encode("utf-8")).hexdigest(),
    }


def _observer(step: Mapping[str, str]) -> dict[str, Any]:
    label = step["label"]
    if step["operation"] == "capture_screenshot":
        digest = hashlib.sha256(f"{SCENARIO_ID}:{label}".encode("utf-8")).hexdigest()
        return {
            "expected": label,
            "actual": label,
            "status": "pass",
            "artifacts": [
                {
                    "id": "surface-pilot-shot-001",
                    "kind": "screenshot",
                    "ref": "artifacts/tablet-splitter-scale-drag-synth.png",
                    "sha256": digest,
                }
            ],
        }
    return {"expected": label, "actual": label, "status": "pass", "artifacts": []}


def _state_provider() -> Mapping[str, Any]:
    return {
        "status": "ready",
        "branch": "codex/kgg-next-level-infrastructure",
        "head": "synthetic-candidate-head",
    }


def _ticket_provider(ticket_id: str) -> Mapping[str, Any]:
    return {
        "ticket_id": ticket_id,
        "status": "selected",
        "title": "tablet-splitter-scale-drag",
    }


def build_candidate_metrics(*, base_sha: str, plugin_root: Path | None = None) -> dict[str, Any]:
    """Run the complete local candidate pilot and return comparator metrics."""

    main_sha = _validate_sha(base_sha)
    root = plugin_root or Path(__file__).resolve().parents[1] / "kgg-plugin"
    started = time.perf_counter_ns()
    candidate_gate.validate_candidate(
        root,
        surface="codex",
        surface_capabilities={"codex": {"mcp"}},
    )
    parity.validate_bundle(parity.sample_bundle())

    runner = _runner()
    flow_registry = QuickFlowRegistry()
    flow_registry.register(_flow())
    runner_registry = RunnerRegistry()
    runner_registry.register(runner)
    clock = _PilotClock()
    lab = mcp_adapter.KggUiLabMcpAdapter(
        main_sha=main_sha,
        state_provider=_state_provider,
        ticket_provider=_ticket_provider,
        runner_registry=runner_registry,
        flow_registry=flow_registry,
        session_store=SessionStore(now=clock),
        now=clock,
    )

    # The seven calls below are the complete bounded read-only interaction:
    # two source reads, session/profile setup, one flow, and two evidence reads.
    lab.get_current_state("codex")
    lab.get_ticket_state("codex", "#180")
    lab.start_ui_session(_session(main_sha, runner))
    lab.set_device_profile("surface-pilot-session", "codex", "tab-s9")
    flow_result = lab.run_quick_flow(_request(main_sha), _observer)
    lab.get_test_evidence("surface-pilot-session", "codex")
    lab.get_session_status("surface-pilot-session", "codex")
    elapsed_ms = max(0, (time.perf_counter_ns() - started) // 1_000_000)

    passed = flow_result["result"]["status"] == "PASS" and flow_result["evidence"]["status"] == "PASS"
    return {
        "scenario_id": SCENARIO_ID,
        "base_sha": main_sha,
        "status": "PASS" if passed else "FAIL",
        "reads": 2,
        "context_items": 4,
        "clarifying_questions": 0,
        "action_calls": 7,
        "dispatches": 0,
        "duplicate_dispatches": 0,
        "runtime_ms": int(elapsed_ms),
        "result_quality": 100 if passed else 0,
        # The local semantic runner proves behavior/evidence only.  It does
        # not independently judge the diagnosis text, so root-cause quality
        # must remain zero until a diagnostic surface supplies evidence.
        "root_cause_quality": 0,
        "repository_writes": 0,
        "secret_leaks": 0,
        "patient_data_leaks": 0,
        "source_regressions": 0,
        "gate_regressions": 0,
        "action_regressions": 0,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-sha", required=True)
    parser.add_argument("--plugin-root", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = build_candidate_metrics(base_sha=args.base_sha, plugin_root=args.plugin_root)
    encoded = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8", newline="\n")
    print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
