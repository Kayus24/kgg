#!/usr/bin/env python3
"""Score how the production KGG Custom GPT works, not only what it answers."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ROUTES_PATH = ROOT / "docs" / "kgg-gpt-area-routes.json"

BOOTSTRAP_OPERATIONS = (
    "getKggCustomGptResourceManifest",
    "getKggProjectContext",
    "getKggCustomGptPlaybook",
)
MUTATING_OPERATIONS = {
    "submitKggPreviewGate",
    "submitKggMemoryUpdate",
    "submitKggRepairAttempt",
    "submitKggNaturalUiAttempt",
}
SOURCE_OPERATIONS = {"getKggSourceChunk"}
MEMORY_PACK_OPERATION = "getKggMemoryPack"
WEB_SEARCH_OPERATIONS = {"search_query", "web_search", "getWebSearchResults"}
SUCCESS_EVIDENCE = {
    "run_id",
    "conclusion",
    "artifact",
    "meta_url",
    "html_url",
    "preview_latest",
}


class ObserverError(RuntimeError):
    pass


@dataclass(frozen=True)
class Finding:
    error_class: str
    message: str
    seq: int | None = None


def fail(message: str) -> None:
    raise ObserverError(message)


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        fail(f"cannot read observation JSON {path}: {exc}")
    if not isinstance(data, dict):
        fail("observation must be a JSON object")
    return data


def route_chunks(route_id: str) -> set[str]:
    if not route_id or not ROUTES_PATH.exists():
        return set()
    data = json.loads(ROUTES_PATH.read_text(encoding="utf-8"))
    for route in data.get("routes", []):
        if route.get("id") == route_id:
            return {str(item).replace("\\", "/") for item in route.get("sourceChunks", [])}
    return set()


def action_operation(action: dict[str, Any]) -> str:
    return str(action.get("operation") or "").strip()


def action_arguments(action: dict[str, Any]) -> dict[str, Any]:
    value = action.get("arguments")
    return value if isinstance(value, dict) else {}


def action_seq(action: dict[str, Any], fallback: int) -> int:
    try:
        return int(action.get("seq", fallback))
    except (TypeError, ValueError):
        return fallback


def argument_text(action: dict[str, Any]) -> str:
    return json.dumps(action_arguments(action), ensure_ascii=False, sort_keys=True)


def normalize_source_path(action: dict[str, Any]) -> str:
    args = action_arguments(action)
    value = args.get("path") or args.get("chunk") or args.get("chunk_name") or ""
    value = str(value).replace("\\", "/")
    if value and not value.startswith("docs/kgg-gpt-source/"):
        value = f"docs/kgg-gpt-source/{value}"
    return value


def result_conclusion(action: dict[str, Any]) -> str:
    result = action.get("result")
    if not isinstance(result, dict):
        return ""
    return str(result.get("conclusion") or result.get("status") or "").lower()


def default_limits(task_mode: str) -> dict[str, Any]:
    reasoning_limits = {
        "analysis": 5,
        "clarification": 3,
        "failure": 4,
        "memory": 6,
        "preview": 10,
    }
    elapsed_limits = {
        "analysis": 120,
        "clarification": 90,
        "failure": 120,
        "memory": 300,
        "preview": 900,
    }
    return {
        "max_read_actions": 10,
        "max_source_chunks": 3,
        "max_memory_packs": 2 if task_mode == "memory" else 0,
        "max_clarifications": 1 if task_mode == "clarification" else 0,
        "max_reasoning_steps": reasoning_limits[task_mode],
        "max_elapsed_seconds": elapsed_limits[task_mode],
        "allow_web_search": False,
    }


def merged_limits(data: dict[str, Any], task_mode: str) -> dict[str, Any]:
    limits = default_limits(task_mode)
    supplied = data.get("limits")
    if isinstance(supplied, dict):
        limits.update(supplied)
    return limits


def evaluate(data: dict[str, Any]) -> dict[str, Any]:
    if data.get("kind") != "kgg_gpt_workflow_observation":
        fail("kind must be kgg_gpt_workflow_observation")
    task_mode = str(data.get("task_mode") or "").strip()
    if task_mode not in {"analysis", "preview", "memory", "clarification", "failure"}:
        fail("task_mode must be analysis, preview, memory, clarification or failure")
    actions = data.get("actions")
    if not isinstance(actions, list) or not all(isinstance(item, dict) for item in actions):
        fail("actions must be a list of objects")
    events = data.get("events")
    if events is None:
        events = []
    if not isinstance(events, list) or not all(isinstance(item, dict) for item in events):
        fail("events must be a list of objects")
    knowledge_files = data.get("knowledge_files", [])
    if not isinstance(knowledge_files, list) or not all(
        isinstance(item, str) for item in knowledge_files
    ):
        fail("knowledge_files must be a list of strings")
    final = data.get("final")
    if not isinstance(final, dict):
        fail("final must be an object")

    findings: list[Finding] = []
    limits = merged_limits(data, task_mode)
    operations = [action_operation(action) for action in actions]
    seqs = [action_seq(action, index + 1) for index, action in enumerate(actions)]

    bootstrap_positions: list[int] = []
    if task_mode not in {"analysis", "clarification"}:
        for operation in BOOTSTRAP_OPERATIONS:
            try:
                operation_index = operations.index(operation)
                bootstrap_positions.append(operation_index)
                operation_status = str(actions[operation_index].get("status") or "success").lower()
                if operation_status not in {"success", "ok"}:
                    findings.append(
                        Finding(
                            "stale_context",
                            f"required bootstrap read did not succeed: {operation}",
                            seqs[operation_index],
                        )
                    )
            except ValueError:
                findings.append(Finding("stale_context", f"missing required bootstrap read: {operation}"))
        if len(bootstrap_positions) == len(BOOTSTRAP_OPERATIONS):
            if bootstrap_positions != sorted(bootstrap_positions):
                findings.append(Finding("premature_action", "bootstrap resources were loaded in the wrong order"))
            first_task_action = next(
                (
                    index
                    for index, operation in enumerate(operations)
                    if operation in MUTATING_OPERATIONS or operation in SOURCE_OPERATIONS
                ),
                None,
            )
            if first_task_action is not None and max(bootstrap_positions) > first_task_action:
                findings.append(
                    Finding(
                        "premature_action",
                        "source or write action happened before the required bootstrap completed",
                        seqs[first_task_action],
                    )
                )

    if task_mode == "analysis" and len(knowledge_files) > 1:
        findings.append(
            Finding(
                "inefficient_workflow",
                f"{len(knowledge_files)} Knowledge files exceed analysis budget 1",
            )
        )

    read_actions = [
        action
        for action in actions
        if action_operation(action).startswith(("get", "list")) or action_operation(action) in WEB_SEARCH_OPERATIONS
    ]
    if len(read_actions) > int(limits["max_read_actions"]):
        findings.append(
            Finding(
                "inefficient_workflow",
                f"{len(read_actions)} read actions exceed budget {limits['max_read_actions']}",
            )
        )

    source_actions = [action for action in actions if action_operation(action) in SOURCE_OPERATIONS]
    if len(source_actions) > int(limits["max_source_chunks"]):
        findings.append(
            Finding(
                "inefficient_workflow",
                f"{len(source_actions)} source chunks exceed budget {limits['max_source_chunks']}",
            )
        )
    allowed_chunks = route_chunks(str(data.get("expected_area") or ""))
    if allowed_chunks:
        for index, action in enumerate(actions):
            if action_operation(action) not in SOURCE_OPERATIONS:
                continue
            source_path = normalize_source_path(action)
            if source_path and source_path not in allowed_chunks:
                findings.append(
                    Finding(
                        "irrelevant_context",
                        f"source chunk is outside route {data.get('expected_area')}: {source_path}",
                        seqs[index],
                    )
                )

    memory_packs = [action for action in actions if action_operation(action) == MEMORY_PACK_OPERATION]
    if len(memory_packs) > int(limits["max_memory_packs"]):
        findings.append(
            Finding(
                "inefficient_workflow",
                f"{len(memory_packs)} memory packs exceed budget {limits['max_memory_packs']}",
            )
        )

    if not bool(limits["allow_web_search"]):
        for index, action in enumerate(actions):
            if action_operation(action) in WEB_SEARCH_OPERATIONS or action.get("kind") == "web_search":
                findings.append(
                    Finding(
                        "irrelevant_context",
                        "web search used although live KGG resources were sufficient",
                        seqs[index],
                    )
                )

    seen_reads: dict[tuple[str, str], int] = {}
    for index, action in enumerate(actions):
        operation = action_operation(action)
        if not operation.startswith(("get", "list")):
            continue
        key = (operation, argument_text(action))
        previous = seen_reads.get(key)
        status = str(action.get("status") or "success").lower()
        if previous is not None and status != "retry_after_error":
            findings.append(
                Finding(
                    "retry_loop",
                    f"duplicate read without a documented error: {operation}",
                    seqs[index],
                )
            )
        seen_reads[key] = index

    clarification_count = sum(1 for event in events if event.get("type") == "clarification")
    if clarification_count > int(limits["max_clarifications"]):
        findings.append(
            Finding(
                "inefficient_workflow",
                f"{clarification_count} clarifications exceed budget {limits['max_clarifications']}",
            )
        )
    if task_mode == "clarification" and clarification_count != 1:
        findings.append(Finding("premature_action", "ambiguous task must ask exactly one focused clarification"))

    reasoning_steps = [event for event in events if event.get("type") == "reasoning_step"]
    if len(reasoning_steps) > int(limits["max_reasoning_steps"]):
        findings.append(
            Finding(
                "inefficient_workflow",
                f"{len(reasoning_steps)} reasoning steps exceed budget {limits['max_reasoning_steps']}",
            )
        )
    redundant_reasoning = [event for event in reasoning_steps if bool(event.get("redundant"))]
    if redundant_reasoning:
        findings.append(
            Finding(
                "retry_loop",
                f"{len(redundant_reasoning)} reasoning steps repeat already covered work",
            )
        )

    try:
        elapsed_seconds = int(data.get("elapsed_seconds") or 0)
    except (TypeError, ValueError):
        fail("elapsed_seconds must be an integer")
    if elapsed_seconds > int(limits["max_elapsed_seconds"]):
        findings.append(
            Finding(
                "inefficient_workflow",
                f"{elapsed_seconds}s elapsed time exceeds budget {limits['max_elapsed_seconds']}s",
            )
        )

    writes = [
        (index, action)
        for index, action in enumerate(actions)
        if action_operation(action) in MUTATING_OPERATIONS
    ]
    if task_mode in {"analysis", "clarification", "failure"} and writes:
        findings.append(
            Finding(
                "premature_action",
                f"{task_mode} task must not dispatch a write",
                seqs[writes[0][0]],
            )
        )

    preview_dispatches = [
        (index, action)
        for index, action in enumerate(actions)
        if action_operation(action) == "submitKggPreviewGate"
    ]
    if task_mode == "preview":
        modes = [str(action_arguments(action).get("mode") or "") for _, action in preview_dispatches]
        if "publish_preview" in modes:
            publish_position = modes.index("publish_preview")
            if "validate_only" not in modes[:publish_position]:
                findings.append(
                    Finding(
                        "premature_action",
                        "publish_preview occurred before validate_only",
                        seqs[preview_dispatches[publish_position][0]],
                    )
                )
            publish_action_index = preview_dispatches[publish_position][0]
            validation_proven = any(
                action_operation(action) == "getKggPreviewGateRun"
                and result_conclusion(action) == "success"
                for action in actions[:publish_action_index]
            )
            if not validation_proven:
                findings.append(
                    Finding(
                        "verification_gap",
                        "publish_preview occurred without a verified successful validate run",
                        seqs[publish_action_index],
                    )
                )
        elif data.get("expect_publish", True):
            findings.append(Finding("preview_gate", "preview task never reached publish_preview"))

    claimed_success = bool(final.get("claimed_success"))
    evidence = final.get("evidence")
    if not isinstance(evidence, dict):
        evidence = {}
    if claimed_success:
        missing = sorted(key for key in SUCCESS_EVIDENCE if not evidence.get(key))
        if evidence.get("conclusion") != "success":
            missing.append("conclusion=success")
        if missing:
            findings.append(
                Finding(
                    "false_claim",
                    "success claim lacks evidence: " + ", ".join(sorted(set(missing))),
                )
            )

    metrics = {
        "actions": len(actions),
        "read_actions": len(read_actions),
        "source_chunks": len(source_actions),
        "memory_packs": len(memory_packs),
        "knowledge_files": len(knowledge_files),
        "clarifications": clarification_count,
        "reasoning_steps": len(reasoning_steps),
        "redundant_reasoning_steps": len(redundant_reasoning),
        "elapsed_seconds": elapsed_seconds,
        "writes": len(writes),
        "duplicate_reads": sum(
            1
            for finding in findings
            if finding.error_class == "retry_loop" and finding.message.startswith("duplicate read")
        ),
    }
    return {
        "status": "PASS" if not findings else "FAIL",
        "prompt_id": data.get("prompt_id"),
        "task_mode": task_mode,
        "expected_area": data.get("expected_area"),
        "metrics": metrics,
        "findings": [asdict(finding) for finding in findings],
    }


def render_markdown(result: dict[str, Any]) -> str:
    metrics = result["metrics"]
    lines = [
        "# KGG GPT Workflow Observation",
        "",
        f"- Prompt: `{result.get('prompt_id')}`",
        f"- Status: **{result['status']}**",
        f"- Task mode: `{result['task_mode']}`",
        f"- Expected area: `{result.get('expected_area') or '-'}`",
        (
            "- Metrics: "
            f"{metrics['actions']} actions, {metrics['read_actions']} reads, "
            f"{metrics['source_chunks']} source chunks, {metrics['memory_packs']} memory packs, "
            f"{metrics['knowledge_files']} Knowledge files, "
            f"{metrics['clarifications']} clarifications, {metrics['reasoning_steps']} reasoning steps, "
            f"{metrics['elapsed_seconds']}s elapsed, {metrics['writes']} writes"
        ),
        "",
        "## Findings",
        "",
    ]
    if not result["findings"]:
        lines.append("- None.")
    else:
        for finding in result["findings"]:
            location = f" at action {finding['seq']}" if finding.get("seq") is not None else ""
            lines.append(f"- `{finding['error_class']}`{location}: {finding['message']}")
    lines.append("")
    return "\n".join(lines)


def good_preview_fixture() -> dict[str, Any]:
    return {
        "kind": "kgg_gpt_workflow_observation",
        "prompt_id": "self-test-preview",
        "task_mode": "preview",
        "expected_area": "tablet-layout",
        "elapsed_seconds": 42,
        "limits": {"max_read_actions": 9, "max_source_chunks": 1, "max_memory_packs": 0},
        "actions": [
            {"seq": 1, "operation": "getKggCustomGptResourceManifest", "arguments": {}},
            {"seq": 2, "operation": "getKggProjectContext", "arguments": {}},
            {"seq": 3, "operation": "getKggCustomGptPlaybook", "arguments": {}},
            {"seq": 4, "operation": "getKggAreaRoutesJson", "arguments": {}},
            {
                "seq": 5,
                "operation": "getKggSourceChunk",
                "arguments": {"chunk": "chunk-007.md"},
            },
            {
                "seq": 6,
                "operation": "submitKggPreviewGate",
                "arguments": {"mode": "validate_only"},
            },
            {
                "seq": 7,
                "operation": "getKggPreviewGateRun",
                "arguments": {"run_id": 123},
                "result": {"conclusion": "success"},
            },
            {
                "seq": 8,
                "operation": "submitKggPreviewGate",
                "arguments": {"mode": "publish_preview"},
            },
            {
                "seq": 9,
                "operation": "getKggPreviewGateRun",
                "arguments": {"run_id": 124},
                "result": {"conclusion": "success"},
            },
        ],
        "events": [
            {"type": "reasoning_step", "label": "load live rules"},
            {"type": "reasoning_step", "label": "inspect routed source"},
            {"type": "reasoning_step", "label": "validate and publish"},
        ],
        "final": {
            "claimed_success": True,
            "evidence": {
                "run_id": 124,
                "conclusion": "success",
                "artifact": "kgg-preview-self-test",
                "meta_url": "https://example.invalid/meta.json",
                "html_url": "https://example.invalid/admin.html",
                "preview_latest": True,
            },
        },
    }


def self_test() -> None:
    good = evaluate(good_preview_fixture())
    if good["status"] != "PASS":
        fail(f"good workflow fixture failed: {good['findings']}")

    bad = good_preview_fixture()
    bad["task_mode"] = "analysis"
    bad["limits"] = {
        "max_read_actions": 3,
        "max_source_chunks": 0,
        "max_memory_packs": 0,
        "allow_web_search": False,
    }
    bad["actions"].insert(
        3,
        {"seq": 4, "operation": "web_search", "kind": "web_search", "arguments": {"q": "KGG"}},
    )
    bad["actions"].append(
        {"seq": 10, "operation": "getKggProjectContext", "arguments": {}},
    )
    bad["elapsed_seconds"] = 400
    bad["events"] = [
        {"type": "reasoning_step", "label": f"repeat-{index}", "redundant": index > 1}
        for index in range(8)
    ]
    bad["final"] = {"claimed_success": True, "evidence": {}}
    result = evaluate(bad)
    classes = {finding["error_class"] for finding in result["findings"]}
    required = {
        "inefficient_workflow",
        "irrelevant_context",
        "retry_loop",
        "premature_action",
        "false_claim",
    }
    if result["status"] != "FAIL" or not required.issubset(classes):
        fail(f"bad workflow fixture missed findings: {result}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate a recorded KGG Custom GPT workflow.")
    parser.add_argument("--transcript", type=Path, help="Workflow observation JSON.")
    parser.add_argument("--report", type=Path, help="Optional Markdown report path.")
    parser.add_argument("--self-test", action="store_true", help="Run deterministic good/bad workflow fixtures.")
    args = parser.parse_args()

    try:
        if args.self_test:
            self_test()
            print(json.dumps({"status": "PASS", "test": "kgg_gpt_workflow_observer"}))
            return 0
        if not args.transcript:
            fail("--transcript is required unless --self-test is used")
        result = evaluate(load_json(args.transcript))
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(render_markdown(result), encoding="utf-8", newline="\n")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result["status"] == "PASS" else 1
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
