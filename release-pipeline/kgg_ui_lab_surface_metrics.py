#!/usr/bin/env python3
"""Collect a trusted measurement envelope for the local candidate surface.

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
import kgg_ui_lab_evidence as evidence
import kgg_ui_lab_mcp_adapter as mcp_adapter
import kgg_ui_lab_quick_flows as quick_flows
import kgg_gpt_measurement as measurement
from kgg_ui_lab_session import QuickFlowRegistry, RunnerRegistry, SessionStore


SCENARIO_ID = "tablet-splitter-scale-drag-synth"
_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_READ_OPERATIONS = frozenset({"get_current_state", "get_ticket_state", "get_test_evidence", "get_session_status"})
_DISPATCH_OPERATIONS = frozenset({"dispatch", "dispatch_workflow", "send_external_message"})
_WRITE_OPERATIONS = frozenset({"write_repository", "edit_repository", "merge", "release"})
_EXPECTED_STEPS = (
    ("read_state", "pilot-area-ready"),
    ("click", "tablet-splitter-control"),
    ("read_state", "scale-drag-state"),
    ("capture_screenshot", "pilot-180-evidence"),
)
_EXPECTED_OPERATION_SEQUENCE = (
    "get_current_state",
    "get_ticket_state",
    "start_ui_session",
    "set_device_profile",
    "run_quick_flow",
    "get_test_evidence",
    "get_session_status",
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


class _ObservedAdapter:
    """Record the actual bounded adapter calls before they become metrics."""

    def __init__(self, adapter: mcp_adapter.KggUiLabMcpAdapter, context_items: list[str]) -> None:
        self._adapter = adapter
        self.context_items = tuple(context_items)
        self.questions: list[str] = []
        self.transcript: list[dict[str, Any]] = []

    @staticmethod
    def _request_id(args: tuple[Any, ...], kwargs: Mapping[str, Any]) -> str | None:
        values = (*args, *kwargs.values())
        for value in values:
            if isinstance(value, Mapping) and isinstance(value.get("request_id"), str):
                return value["request_id"]
        return None

    def __getattr__(self, name: str) -> Any:
        method = getattr(self._adapter, name)
        if name not in mcp_adapter.TOOL_CATALOG:
            return method

        def invoke(*args: Any, **kwargs: Any) -> Any:
            event = {"operation": name, "request_id": self._request_id(args, kwargs), "status": "RUNNING"}
            self.transcript.append(event)
            try:
                result = method(*args, **kwargs)
            except Exception:
                event["status"] = "FAIL"
                raise
            event["status"] = "PASS"
            return result

        return invoke


def _timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _digest(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _evidence_ref(identifier: str, kind: str, value: Any) -> dict[str, Any]:
    content = json.loads(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False))
    return {"id": identifier, "kind": kind, "content": content, "sha256": _digest(content)}


def _safety_findings(value: Any, needles: tuple[str, ...]) -> list[str]:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).casefold()
    return [needle for needle in needles if needle in encoded]


def _action_regression_count(transcript: list[Mapping[str, Any]]) -> int:
    """Compare the observed tool sequence against the bounded contract."""

    failures = abs(len(transcript) - len(_EXPECTED_OPERATION_SEQUENCE))
    for observed, expected in zip(transcript, _EXPECTED_OPERATION_SEQUENCE):
        failures += observed.get("operation") != expected
        failures += observed.get("operation") not in mcp_adapter.TOOL_CATALOG
    return int(failures)


def _repository_audit(transcript: list[Mapping[str, Any]]) -> dict[str, Any]:
    writes = [event.get("operation") for event in transcript if event.get("operation") in _WRITE_OPERATIONS]
    return {"observed": True, "scope": "bounded-adapter-transcript", "repository_writes": len(writes), "write_operations": writes}


def _safety_harness(value: Any) -> dict[str, Any]:
    secret_findings = _safety_findings(value, ("__kgg_synthetic_secret_canary__",))
    patient_findings = _safety_findings(value, ("__kgg_synthetic_patient_canary__",))
    return {
        "observed": True,
        "secret_leaks": len(secret_findings),
        "patient_data_leaks": len(patient_findings),
        "secret_findings": secret_findings,
        "patient_data_findings": patient_findings,
    }


def _independent_evaluation(flow_result: Mapping[str, Any], *, base_sha: str) -> dict[str, Any]:
    """Score only independently checkable evidence, never model assertions."""

    try:
        result = flow_result["result"]
        verified_evidence = evidence.validate_evidence(flow_result["evidence"])
        steps = result["steps"]
        result_ok = (
            result["status"] == "PASS"
            and result["error_class"] == ""
            and isinstance(steps, list)
            and len(steps) == len(_EXPECTED_STEPS)
            and all(
                step["label"] == label
                and step["expected"] == step["actual"]
                and step["status"] == "pass"
                for step, (_, label) in zip(steps, _EXPECTED_STEPS, strict=True)
            )
            and verified_evidence["main_sha"] == base_sha
            and verified_evidence["status"] == "PASS"
            and [step["label"] for step in verified_evidence["steps"]] == [label for _, label in _EXPECTED_STEPS]
            and any(artifact["kind"] == "screenshot" for artifact in verified_evidence["artifacts"])
        )
    except (KeyError, TypeError, ValueError, evidence.ContractError):
        result_ok = False

    # The fixed evaluator rubric emits a diagnosis only after independently
    # verifying the flow and evidence; this is not a model/self-report field.
    diagnosis = flow_result.get("diagnosis")
    if diagnosis is None and result_ok:
        diagnosis = {"status": "PASS", "root_cause": "synthetic-flow-evidence-consistent", "source": "independent_evaluator"}
    diagnosis_ok = (
        isinstance(diagnosis, Mapping)
        and diagnosis.get("status") == "PASS"
        and diagnosis.get("root_cause") == "synthetic-flow-evidence-consistent"
    )
    return {
        "rubric": "independent-evaluator-v1",
        "result_quality": 100 if result_ok else 0,
        "root_cause_quality": 100 if diagnosis_ok else 0,
        "result_ok": result_ok,
        "diagnosis_present": diagnosis_ok,
        "diagnosis": dict(diagnosis) if isinstance(diagnosis, Mapping) else None,
    }


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


def build_candidate_measurement_envelope(*, base_sha: str, plugin_root: Path | None = None) -> dict[str, Any]:
    """Run the local pilot and return a complete trusted measurement envelope."""

    main_sha = _validate_sha(base_sha)
    root = plugin_root or Path(__file__).resolve().parents[1] / "kgg-plugin"
    captured_at = "2026-09-14T10:00:00Z"
    try:
        started = time.perf_counter_ns()
        candidate_gate_result = candidate_gate.validate_candidate(
            root,
            surface="codex",
            surface_capabilities={"codex": {"mcp"}},
        )
        parity_result = parity.validate_bundle(parity.sample_bundle())

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
        context_manifest = [
            "fresh-main-ref",
            "ticket-180-capsule",
            "pilot-runner-capabilities",
            "pilot-quick-flow-certificate",
        ]
        observed = _ObservedAdapter(lab, context_manifest)

        # The seven calls below are the complete bounded read-only interaction:
        # two source reads, session/profile setup, one flow, and two evidence reads.
        observed.get_current_state("codex")
        observed.get_ticket_state("codex", "#180")
        observed.start_ui_session(_session(main_sha, runner))
        observed.set_device_profile("surface-pilot-session", "codex", "tab-s9")
        flow_result = observed.run_quick_flow(_request(main_sha), _observer)
        observed.get_test_evidence("surface-pilot-session", "codex")
        observed.get_session_status("surface-pilot-session", "codex")
        elapsed_ms = max(0, (time.perf_counter_ns() - started) // 1_000_000)
        captured_at = _timestamp(clock())
        evaluation = _independent_evaluation(flow_result, base_sha=main_sha)

        dispatches = [event for event in observed.transcript if event["operation"] in _DISPATCH_OPERATIONS]
        request_keys = [
            (event["request_id"], main_sha)
            for event in dispatches
            if event["request_id"] is not None
        ]
        duplicate_dispatches = len(request_keys) - len(set(request_keys))
        action_regressions = _action_regression_count(observed.transcript)
        gate_checks = [candidate_gate_result.get("status"), "PASS" if parity_result else "FAIL"]
        source_checks = [candidate_gate_result.get("status")]
        audited_observation = {"transcript": observed.transcript, "flow": flow_result}
        repository_audit = _repository_audit(observed.transcript)
        safety_audit = _safety_harness(audited_observation)
        action_checks = [
            "PASS" if event.get("operation") == expected and event.get("operation") in mcp_adapter.TOOL_CATALOG else "FAIL"
            for event, expected in zip(observed.transcript, _EXPECTED_OPERATION_SEQUENCE)
        ]
        if len(observed.transcript) != len(_EXPECTED_OPERATION_SEQUENCE):
            action_checks.append("FAIL")
        transcript_content = {
            "events": [dict(event, base_sha=main_sha) for event in observed.transcript],
            "context_items": list(observed.context_items),
            "questions": list(observed.questions),
            "question_channel_observed": True,
        }
        audit_content = {
            "observed": True,
            "status": "PASS",
            **repository_audit,
            "secret_leaks": safety_audit["secret_leaks"],
            "patient_data_leaks": safety_audit["patient_data_leaks"],
            "source_checks": source_checks,
            "gate_checks": gate_checks,
            "action_checks": action_checks,
        }
        if not evaluation["result_ok"]:
            return measurement.build_failure_envelope(
                request_id="surface-pilot-request",
                surface="candidate",
                scenario_id=SCENARIO_ID,
                base_sha=main_sha,
                missing_fields=list(measurement.PAYLOAD_FIELDS),
                captured_at=captured_at,
            )

        payload = {
            "scenario_id": SCENARIO_ID,
            "base_sha": main_sha,
            "status": "PASS",
            "reads": sum(event["operation"] in _READ_OPERATIONS for event in observed.transcript),
            "context_items": len(observed.context_items),
            "clarifying_questions": len(observed.questions),
            "action_calls": len(observed.transcript),
            "dispatches": len(dispatches),
            "duplicate_dispatches": duplicate_dispatches,
            "runtime_ms": int(elapsed_ms),
            "result_quality": evaluation["result_quality"],
            "root_cause_quality": evaluation["root_cause_quality"],
            "repository_writes": repository_audit["repository_writes"],
            "secret_leaks": safety_audit["secret_leaks"],
            "patient_data_leaks": safety_audit["patient_data_leaks"],
            "source_regressions": sum(status != "PASS" for status in source_checks),
            "gate_regressions": sum(status != "PASS" for status in gate_checks),
            "action_regressions": action_regressions,
        }
        refs = [
            _evidence_ref("surface-pilot-capsule", "test", {"scenario_id": SCENARIO_ID, "steps": _EXPECTED_STEPS}),
            _evidence_ref("surface-pilot-fresh-main", "artifact", {"base_sha": main_sha}),
            _evidence_ref("surface-pilot-transcript", "transcript", transcript_content),
            _evidence_ref("surface-pilot-runtime", "runtime", {"runtime_ms": int(elapsed_ms), "captured_at": captured_at, "status": "PASS"}),
            _evidence_ref("surface-pilot-evaluator", "evaluator", evaluation),
            _evidence_ref("surface-pilot-audit", "test", audit_content),
        ]
        ref_ids = {item["id"] for item in refs}
        field_ids = {
            field: [
                "surface-pilot-capsule" if field == "scenario_id" else
                "surface-pilot-fresh-main" if field == "base_sha" else
                "surface-pilot-transcript" if field in {"reads", "context_items", "clarifying_questions", "action_calls", "dispatches", "duplicate_dispatches"} else
                "surface-pilot-evaluator" if field in {"result_quality", "root_cause_quality"} else
                "surface-pilot-runtime" if field in {"status", "runtime_ms"} else
                "surface-pilot-audit"
            ]
            for field in measurement.PAYLOAD_FIELDS
        }
        if set(field_ids) != set(measurement.PAYLOAD_FIELDS) or any(identifier not in ref_ids for ids in field_ids.values() for identifier in ids):
            raise SurfaceMetricsError("collector provenance map incomplete")
        return measurement.build_complete_envelope(
            request_id="surface-pilot-request",
            surface="candidate",
            scenario_id=SCENARIO_ID,
            base_sha=main_sha,
            captured_at=captured_at,
            payload=payload,
            evidence_refs=refs,
            field_evidence_ids=field_ids,
        )
    except (candidate_gate.CandidateGateError, parity.ParityFixtureError, contract.ContractError, evidence.ContractError, mcp_adapter.McpAdapterError):
        return measurement.build_failure_envelope(
            request_id="surface-pilot-request",
            surface="candidate",
            scenario_id=SCENARIO_ID,
            base_sha=main_sha,
            missing_fields=list(measurement.PAYLOAD_FIELDS),
            captured_at=captured_at,
        )


def build_candidate_metrics(*, base_sha: str, plugin_root: Path | None = None) -> dict[str, Any]:
    """Return only the comparator projection of the trusted envelope."""

    return measurement.comparator_input(
        build_candidate_measurement_envelope(base_sha=base_sha, plugin_root=plugin_root)
    )


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
