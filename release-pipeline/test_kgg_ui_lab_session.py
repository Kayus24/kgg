#!/usr/bin/env python3
"""Contract tests for the local UI Lab runner/session/quick-flow stores."""

from __future__ import annotations

from datetime import datetime, timezone
import unittest

import kgg_ui_lab_contract as contract
import kgg_ui_lab_session as session_runtime


def valid_session() -> dict:
    return {
        "schema": contract.SESSION_SCHEMA,
        "session_id": "ui-lab-session-001",
        "status": "ready",
        "active_actor": "custom_gpt",
        "request_id": "ui-request-001",
        "lease": {
            "owner": "custom_gpt",
            "issued_at": "2026-09-14T08:00:00Z",
            "expires_at": "2026-09-14T08:30:00Z",
        },
        "runner": {
            "runner_id": "runner-local-001",
            "version": "1.0.0",
            "browser_revision": "chromium-140",
            "capabilities": ["browser", "quick_flows", "capture"],
        },
        "app": {
            "name": "admin",
            "url": "https://preview.example.test/admin",
            "main_sha": "a" * 40,
            "preview_sha": "b" * 40,
        },
        "device_profile": "tab-s9",
        "viewport": {"width": 1280, "height": 800, "device_scale_factor": 1},
        "quick_flow": {"name": "open-tablet-layout", "version": "1.0.0"},
        "timeout": {"timeout_ms": 120000, "cleanup_on_cancel": True},
        "artifacts": [],
    }


def event(sequence: int, event_type: str = "state_observed") -> dict:
    return {
        "schema": contract.EVENT_SCHEMA,
        "event_id": f"ui-event-{sequence:03d}",
        "session_id": "ui-lab-session-001",
        "request_id": "ui-request-001",
        "sequence": sequence,
        "event_type": event_type,
        "actor": "runner",
        "timestamp": f"2026-09-14T08:0{sequence}:00Z",
        "status": "running",
        "summary": "Synthetic state observed.",
        "evidence": [],
    }


class KggUiLabSessionTests(unittest.TestCase):
    def test_runner_registry_is_deterministic_and_rejects_duplicates(self) -> None:
        registry = session_runtime.RunnerRegistry()
        runner = valid_session()["runner"]
        registry.register(runner)
        self.assertEqual(registry.select("browser")["runner_id"], "runner-local-001")
        with self.assertRaisesRegex(session_runtime.ContractError, "duplicate"):
            registry.register(runner)
        with self.assertRaisesRegex(session_runtime.ContractError, "capability"):
            registry.select("android")

    def test_session_store_enforces_transitions_and_append_only_events(self) -> None:
        clock = lambda: datetime(2026, 9, 14, 8, 5, tzinfo=timezone.utc)
        store = session_runtime.SessionStore(now=clock)
        store.create(valid_session())
        store.transition("ui-lab-session-001", "running")
        self.assertEqual(store.append_event(event(1)), 1)
        self.assertEqual(store.append_event(event(2, "action_completed")), 2)
        with self.assertRaisesRegex(session_runtime.ContractError, "duplicate_request"):
            store.append_event(event(3))
        store.transition("ui-lab-session-001", "completed")
        with self.assertRaisesRegex(session_runtime.ContractError, "transition"):
            store.transition("ui-lab-session-001", "running")

    def test_expired_session_cannot_be_created_or_used(self) -> None:
        expired_clock = lambda: datetime(2026, 9, 14, 8, 31, tzinfo=timezone.utc)
        store = session_runtime.SessionStore(now=expired_clock)
        with self.assertRaisesRegex(session_runtime.ContractError, "lease_expired"):
            store.create(valid_session())

    def test_quick_flow_uses_semantic_targets_not_selectors(self) -> None:
        registry = session_runtime.QuickFlowRegistry()
        flow = {
            "name": "open-tablet-layout",
            "version": "1.0.0",
            "steps": [
                {"operation": "read_state", "label": "layout"},
                {"operation": "click", "label": "tablet-layout"},
            ],
        }
        registry.register(flow)
        self.assertEqual(len(registry.get("open-tablet-layout", "1.0.0")["steps"]), 2)
        with self.assertRaisesRegex(session_runtime.ContractError, "duplicate"):
            registry.register(flow)
        unsafe = dict(flow, name="unsafe-flow", steps=[{"operation": "click", "selector": "#secret"}])
        with self.assertRaisesRegex(session_runtime.ContractError, "selector"):
            registry.register(unsafe)

    def test_tap_and_bounded_wait_steps_are_supported(self) -> None:
        registry = session_runtime.QuickFlowRegistry()
        flow = {
            "name": "tap-and-wait",
            "version": "1.0.0",
            "steps": [
                {"operation": "tap", "label": "tablet-control"},
                {"operation": "wait", "label": "wait-short", "timeout_ms": 1500},
            ],
        }
        normalized = registry.register(flow)
        self.assertEqual(normalized["steps"][0]["operation"], "tap")
        self.assertEqual(normalized["steps"][1]["timeout_ms"], 1500)
        with self.assertRaisesRegex(session_runtime.ContractError, "wait_timeout"):
            registry.register(
                {
                    "name": "wait-too-long",
                    "version": "1.0.0",
                    "steps": [{"operation": "wait", "label": "wait-long", "timeout_ms": 5001}],
                }
            )


if __name__ == "__main__":
    unittest.main()
