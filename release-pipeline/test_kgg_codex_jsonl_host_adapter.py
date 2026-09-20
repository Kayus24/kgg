#!/usr/bin/env python3
"""Independent contract tests for the parent-side Codex JSONL adapter."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys
import unittest
ROOT = Path(__file__).resolve().parents[1]
PIPELINE = ROOT / "release-pipeline"
if str(PIPELINE) not in sys.path:
    sys.path.insert(0, str(PIPELINE))
import kgg_codex_jsonl_host_adapter as adapter
THREAD = "thread-abc123"
TURN = "turn-abc123"
BASE = "a" * 40
SCENARIO = "codex-jsonl-fixture"
def event_stream(*, tool: str = "get_current_state", final_text: str = "done") -> str:
    events = [
        {"type": "thread.started", "thread_id": THREAD},
        {"type": "turn.started"},
        {"type": "item.started", "item": {"id": "msg-abc123", "type": "agent_message", "text": final_text}},
        {"type": "item.completed", "item": {"id": "msg-abc123", "type": "agent_message", "text": final_text}},
        {"type": "item.started", "item": {"id": "mcp-abc123", "type": "mcp_tool_call", "server": "kgg", "tool": tool}},
        {"type": "item.completed", "item": {"id": "mcp-abc123", "type": "mcp_tool_call", "server": "kgg", "tool": tool, "status": "completed"}},
        {"type": "item.started", "item": {"id": "cmd-abc123", "type": "command_execution", "command": "git status"}},
        {"type": "item.completed", "item": {"id": "cmd-abc123", "type": "command_execution", "command": "git status", "exit_code": 0, "status": "completed"}},
        {"type": "item.started", "item": {"id": "file-abc123", "type": "file_change", "changes": [{"path": "release-pipeline/example.py", "kind": "update"}]}},
        {"type": "item.completed", "item": {"id": "file-abc123", "type": "file_change", "changes": [{"path": "release-pipeline/example.py", "kind": "update"}]}},
        {"type": "turn.completed", "usage": {"input_tokens": 1, "output_tokens": 1}},
    ]
    return "\n".join(json.dumps(item, sort_keys=True) for item in events)
def stream_with_unmeasured_item(item_type: str) -> str:
    lines = event_stream().splitlines()
    unmeasured = [
        {"type": "item.started", "item": {"id": f"{item_type}-abc123", "type": item_type}},
        {"type": "item.updated", "item": {"id": f"{item_type}-abc123", "type": item_type}},
        {"type": "item.completed", "item": {"id": f"{item_type}-abc123", "type": item_type}},
    ]
    lines[-1:-1] = [json.dumps(item, sort_keys=True) for item in unmeasured]
    return "\n".join(lines)
def stream_with_completion_only_item(item_type: str) -> str:
    item = {"id": f"{item_type}-only", "type": item_type, **({"text": "final output"} if item_type == "agent_message" else {"server": "kgg", "tool": "get_current_state"} if item_type == "mcp_tool_call" else {})}
    events = [{"type": "thread.started", "thread_id": THREAD}, {"type": "turn.started"}, {"type": "item.completed", "item": item}, {"type": "turn.completed", "usage": {"input_tokens": 1, "output_tokens": 1}}]
    return "\n".join(json.dumps(event, sort_keys=True) for event in events)
class CodexJsonlAdapterTests(unittest.TestCase):
    def test_independent_golden_mapping_is_bounded(self) -> None:
        result = adapter.parse_jsonl(
            event_stream(final_text="reads=999; this is output, not telemetry"),
            expected_thread_id=THREAD,
            scenario_id=SCENARIO,
            base_sha=BASE,
            runtime_ms=37,
        )
        self.assertEqual(result["thread_id"], THREAD)
        self.assertIsNone(result["turn_id"])
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["runtime_ms"], 37)
        self.assertEqual(len(result["action_events"]), 1)
        self.assertEqual(result["action_events"][0]["operation"], "get_current_state")
        self.assertEqual(len(result["command_executions"]), 1)
        self.assertEqual(len(result["file_changes"]), 1)
        self.assertTrue(result["final_output_present"])
        self.assertEqual(result["final_output_bytes"], len("reads=999; this is output, not telemetry".encode("utf-8")))
        self.assertNotIn("final_output", result)
        self.assertNotIn("reads", result)
        self.assertEqual(
            result["final_output_sha256"],
            hashlib.sha256(b"reads=999; this is output, not telemetry").hexdigest(),
        )
        self.assertNotIn("reads", result["missing_fields"])
        self.assertIn("context_items", result["missing_fields"])
    def test_failure_envelope_reuses_existing_builder_and_has_no_payload(self) -> None:
        observation = adapter.parse_jsonl(
            event_stream(tool="unknown_tool"),
            expected_thread_id=THREAD,
            scenario_id=SCENARIO,
            base_sha=BASE,
        )
        envelope = adapter.build_measurement_envelope(
            observation,
            request_id="codex-adapter-001",
            scenario_id=SCENARIO,
            base_sha=BASE,
            captured_at="2026-09-19T12:00:00Z",
        )
        self.assertEqual(envelope["status"], "FAIL")
        self.assertIsNone(envelope["payload"])
        self.assertIn("context_items", envelope["missing_fields"])
        self.assertIn("result_quality", envelope["missing_fields"])
        self.assertEqual(envelope["field_provenance"], {})
    def test_malformed_identity_and_lifecycle_inputs_fail_closed(self) -> None:
        cases = {
            "malformed": "not-json",
            "wrong_identity": event_stream().replace(THREAD, "thread-other"),
            "missing_terminal": "\n".join(event_stream().splitlines()[:-1]),
            "item_before_start": "\n".join([
                json.dumps({"type": "thread.started", "thread_id": THREAD}),
                json.dumps({"type": "turn.started", "turn_id": TURN}),
                json.dumps({"type": "item.updated", "item": {"id": "x-abc123", "type": "agent_message", "text": "x"}}),
            ]),
            "unknown_event": json.dumps({"type": "model.self_report", "value": 0}),
        }
        for label, source in cases.items():
            with self.subTest(label=label):
                with self.assertRaises(adapter.AdapterError):
                    adapter.parse_jsonl(source, expected_thread_id=THREAD, scenario_id=SCENARIO, base_sha=BASE)
    def test_no_fabricated_zero_for_missing_host_observations(self) -> None:
        result = adapter.parse_jsonl(
            event_stream(tool="not_a_read"),
            expected_thread_id=THREAD,
            scenario_id=SCENARIO,
            base_sha=BASE,
        )
        self.assertIn("reads", result["missing_fields"])
        self.assertIn("dispatches", result["missing_fields"])
        self.assertNotIn("reads", result)
        self.assertNotIn("dispatches", result)
    def test_documented_unmeasured_items_are_lifecycle_safe_but_not_metrics(self) -> None:
        for item_type in ("reasoning", "web_search", "todo_list"):
            with self.subTest(item_type=item_type):
                result = adapter.parse_jsonl(
                    stream_with_unmeasured_item(item_type),
                    expected_thread_id=THREAD,
                    scenario_id=SCENARIO,
                    base_sha=BASE,
                )
                self.assertEqual(result["status"], "PASS")
                self.assertEqual(len(result["action_events"]), 1)
                self.assertEqual(len(result["command_executions"]), 1)
                self.assertEqual(len(result["file_changes"]), 1)
                envelope = adapter.build_measurement_envelope(
                    result,
                    request_id=f"unmeasured-{item_type.replace('_', '-')}",
                    scenario_id=SCENARIO,
                    base_sha=BASE,
                )
                self.assertEqual(envelope["status"], "FAIL")
                self.assertIsNone(envelope["payload"])
    def test_item_type_mutation_fails_closed(self) -> None:
        events = [json.loads(line) for line in event_stream().splitlines()]
        for event in events:
            if event["type"] == "item.completed" and event["item"]["id"] == "mcp-abc123":
                event["item"]["type"] = "reasoning"
                break
        else:
            self.fail("mcp completion fixture missing")
        with self.assertRaisesRegex(adapter.AdapterError, "item_type_changed"):
            adapter.parse_jsonl(
                "\n".join(json.dumps(event, sort_keys=True) for event in events),
                expected_thread_id=THREAD,
                scenario_id=SCENARIO,
                base_sha=BASE,
            )

    def test_multiline_command_is_retained_as_bounded_host_evidence(self) -> None:
        events = [json.loads(line) for line in event_stream().splitlines()]
        multiline = "python - <<'PY'\nprint('ok')\nPY"
        for event in events:
            if event["type"] in {"item.started", "item.completed"} and event["item"]["type"] == "command_execution":
                event["item"]["command"] = multiline
        source = "\n".join(json.dumps(event, sort_keys=True) for event in events)
        result = adapter.parse_jsonl(
            source,
            expected_thread_id=THREAD,
            scenario_id=SCENARIO,
            base_sha=BASE,
        )
        self.assertEqual(result["command_executions"][0]["command"], multiline)

    def test_completion_only_item_cannot_start_after_completion(self) -> None:
        events = stream_with_completion_only_item("mcp_tool_call").splitlines()
        events.insert(3, json.dumps({
            "type": "item.started",
            "item": {"id": "mcp_tool_call-only", "type": "mcp_tool_call", "server": "kgg", "tool": "get_current_state"},
        }, sort_keys=True))
        with self.assertRaisesRegex(adapter.AdapterError, "duplicate_item_started"):
            adapter.parse_jsonl("\n".join(events), expected_thread_id=THREAD, scenario_id=SCENARIO, base_sha=BASE)

    def test_complete_envelope_requires_observation_identity_and_pass_status(self) -> None:
        observation = adapter.parse_jsonl(
            event_stream(),
            expected_thread_id=THREAD,
            scenario_id=SCENARIO,
            base_sha=BASE,
        )
        with self.assertRaisesRegex(adapter.AdapterError, "observation_scenario_mismatch"):
            adapter.build_measurement_envelope(
                observation,
                request_id="identity-check-001",
                scenario_id="other-scenario",
                base_sha=BASE,
                trusted_payload={},
                evidence_refs=[],
            )
        failed = dict(observation, status="FAIL", missing_fields=[])
        envelope = adapter.build_measurement_envelope(
            failed,
            request_id="identity-check-002",
            scenario_id=SCENARIO,
            base_sha=BASE,
            trusted_payload={},
            evidence_refs=[],
        )
        self.assertEqual(envelope["status"], "FAIL")
        self.assertIsNone(envelope["payload"])
    def test_exec_completion_only_items_and_missing_turn_id_are_supported(self) -> None:
        for item_type in ("agent_message", "reasoning", "error", "mcp_tool_call"):
            with self.subTest(item_type=item_type):
                result = adapter.parse_jsonl(stream_with_completion_only_item(item_type), expected_thread_id=THREAD, scenario_id=SCENARIO, base_sha=BASE)
                self.assertIsNone(result["turn_id"])
                self.assertEqual(result["status"], "PASS")
                self.assertEqual(len(result["action_events"]), 1 if item_type == "mcp_tool_call" else 0)
                envelope = adapter.build_measurement_envelope(result, request_id=f"completion-{item_type.replace('_', '-')}", scenario_id=SCENARIO, base_sha=BASE)
                self.assertEqual((envelope["status"], envelope["payload"]), ("FAIL", None))
    def test_completion_only_stateful_items_are_exactly_once_and_type_safe(self) -> None:
        events = stream_with_completion_only_item("mcp_tool_call").splitlines()
        events.insert(-1, events[2])
        with self.assertRaisesRegex(adapter.AdapterError, "duplicate_item_completed"):
            adapter.parse_jsonl("\n".join(events), expected_thread_id=THREAD, scenario_id=SCENARIO, base_sha=BASE)
        conflict = [json.loads(line) for line in stream_with_completion_only_item("mcp_tool_call").splitlines()]
        conflict.insert(2, {"type": "item.started", "item": {"id": "mcp_tool_call-only", "type": "reasoning"}})
        with self.assertRaisesRegex(adapter.AdapterError, "item_type_changed"):
            adapter.parse_jsonl("\n".join(json.dumps(event, sort_keys=True) for event in conflict), expected_thread_id=THREAD, scenario_id=SCENARIO, base_sha=BASE)
    def test_top_level_error_waits_for_authoritative_terminal(self) -> None:
        events = [json.loads(line) for line in event_stream().splitlines()]
        events.insert(-1, {"type": "error", "message": "transient warning"})
        events[-1] = {"type": "turn.failed", "error": {"message": "failed"}}
        self.assertEqual(adapter.parse_jsonl("\n".join(json.dumps(event, sort_keys=True) for event in events), expected_thread_id=THREAD, scenario_id=SCENARIO, base_sha=BASE)["status"], "FAIL")
        events[-1] = {"type": "turn.completed", "usage": {}}
        with self.assertRaisesRegex(adapter.AdapterError, "turn_completed_after_stream_error"):
            adapter.parse_jsonl("\n".join(json.dumps(event, sort_keys=True) for event in events), expected_thread_id=THREAD, scenario_id=SCENARIO, base_sha=BASE)
if __name__ == "__main__":
    unittest.main()
