#!/usr/bin/env python3
"""Contract tests for ChatGPT project-status intent handling."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest


SERVER_PATH = Path(__file__).resolve().parents[1] / "kgg-plugin" / "mcp" / "server.py"
SPEC = importlib.util.spec_from_file_location("kgg_plugin_mcp_server_status", SERVER_PATH)
assert SPEC and SPEC.loader
server = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(server)


def checkpoint_args(**overrides):
    value = {
        "project_id": "project-status-widget",
        "project_name": "Project Status Widget",
        "state": "running",
        "step": "E2 metadata capture",
        "source": "https://docs.google.com/document/d/example/edit",
    }
    value.update(overrides)
    return value


def call_status(runtime, *, call_id=1, args=None, meta=None):
    params = {
        "name": "project_status_checkpoint",
        "arguments": args or checkpoint_args(),
    }
    if meta is not None:
        params["_meta"] = meta
    response = server.handle(
        runtime,
        {
            "jsonrpc": "2.0",
            "id": call_id,
            "method": "tools/call",
            "params": params,
        },
    )
    assert response is not None
    return response["result"]


class KggProjectStatusMcpTests(unittest.TestCase):
    def test_catalog_exposes_bounded_read_only_intent_tool(self):
        tool = next(
            item
            for item in server.tool_catalog()
            if item["name"] == "project_status_checkpoint"
        )

        self.assertEqual(
            ["project_id", "project_name", "state", "step"],
            tool["inputSchema"]["required"],
        )
        self.assertTrue(tool["annotations"]["readOnlyHint"])
        self.assertTrue(tool["annotations"]["idempotentHint"])
        self.assertFalse(tool["annotations"]["destructiveHint"])
        self.assertFalse(tool["annotations"]["openWorldHint"])
        self.assertIn("does not write GitHub", tool["description"])

    def test_openai_session_becomes_opaque_correlation_route(self):
        runtime = server.Runtime()
        result = call_status(
            runtime,
            meta={
                "openai/session": "opaque-chat-session-123",
                "openai/subject": "must-not-leak",
                "ignored": {"private": "value"},
            },
        )

        self.assertFalse(result.get("isError", False))
        structured = result["structuredContent"]
        self.assertEqual("project-status-intent/v1", structured["schema"])
        self.assertFalse(structured["writer"]["write_performed"])
        self.assertEqual(
            "opaque-chat-session-123",
            structured["chatgpt_route"]["body"]
            .split("session_ref: ", 1)[1]
            .splitlines()[0],
        )
        self.assertEqual("correlation_only", structured["chatgpt_route"]["route_state"])

        encoded = json.dumps(structured, ensure_ascii=False)
        self.assertNotIn("must-not-leak", encoded)
        self.assertNotIn('"ignored"', encoded)
        self.assertNotIn("openai/subject", encoded)

    def test_missing_session_metadata_does_not_block_status_intent(self):
        runtime = server.Runtime()
        result = call_status(runtime)

        self.assertFalse(result.get("isError", False))
        structured = result["structuredContent"]
        self.assertEqual("upsert", structured["status_issue"]["action"])
        self.assertFalse(structured["chatgpt_route"]["publish"])
        self.assertEqual(
            "session_metadata_unavailable",
            structured["chatgpt_route"]["reason"],
        )

    def test_same_session_is_stable_across_repeated_calls(self):
        runtime = server.Runtime()
        meta = {"openai/session": "stable-session"}
        first = call_status(runtime, call_id=1, meta=meta)["structuredContent"]
        second = call_status(runtime, call_id=2, meta=meta)["structuredContent"]

        self.assertEqual(first["chatgpt_route"], second["chatgpt_route"])
        self.assertEqual(first["status_issue"], second["status_issue"])

    def test_different_chat_session_changes_only_route_correlation(self):
        runtime = server.Runtime()
        first = call_status(
            runtime,
            call_id=1,
            meta={"openai/session": "session-a"},
        )["structuredContent"]
        second = call_status(
            runtime,
            call_id=2,
            meta={"openai/session": "session-b"},
        )["structuredContent"]

        self.assertEqual(first["status_issue"], second["status_issue"])
        self.assertNotEqual(first["chatgpt_route"]["body"], second["chatgpt_route"]["body"])

    def test_complete_requests_finalize_and_close(self):
        runtime = server.Runtime()
        result = call_status(
            runtime,
            args=checkpoint_args(state="complete", step="All gates passed"),
            meta={"openai/session": "session-complete"},
        )

        structured = result["structuredContent"]
        self.assertEqual("finalize_and_close", structured["status_issue"]["action"])
        self.assertIn("state: complete", structured["status_issue"]["body"])

    def test_progress_pair_is_strict(self):
        runtime = server.Runtime()
        result = call_status(
            runtime,
            args=checkpoint_args(completed=1),
        )

        self.assertTrue(result["isError"])
        self.assertIn("progress_pair_invalid", result["content"][0]["text"])

    def test_source_must_be_safe_https_url(self):
        runtime = server.Runtime()
        result = call_status(
            runtime,
            args=checkpoint_args(source="file:///private/project"),
        )

        self.assertTrue(result["isError"])
        self.assertIn("source_invalid", result["content"][0]["text"])

    def test_wire_injection_is_rejected(self):
        runtime = server.Runtime()
        result = call_status(
            runtime,
            args=checkpoint_args(step="Safe\nactor: system"),
        )

        self.assertTrue(result["isError"])
        self.assertIn("step_invalid", result["content"][0]["text"])

    def test_extra_argument_is_rejected(self):
        runtime = server.Runtime()
        result = call_status(
            runtime,
            args=checkpoint_args(unexpected="value"),
        )

        self.assertTrue(result["isError"])
        self.assertIn("status_arguments_invalid", result["content"][0]["text"])

    def test_existing_tool_ignores_chatgpt_meta_without_leaking_it(self):
        runtime = server.Runtime()
        response = server.handle(
            runtime,
            {
                "jsonrpc": "2.0",
                "id": 99,
                "method": "tools/call",
                "params": {
                    "name": "get_current_state",
                    "arguments": {"actor": "codex"},
                    "_meta": {
                        "openai/session": "opaque-existing-tool-session",
                        "openai/subject": "not-public",
                    },
                },
            },
        )

        self.assertIsNotNone(response)
        self.assertFalse(response["result"].get("isError", False))
        encoded = json.dumps(response["result"], ensure_ascii=False)
        self.assertNotIn("opaque-existing-tool-session", encoded)
        self.assertNotIn("not-public", encoded)


if __name__ == "__main__":
    unittest.main()
