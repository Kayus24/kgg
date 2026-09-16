#!/usr/bin/env python3
"""Contract tests for the bounded KGG UI Lab session protocol."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import unittest

import kgg_ui_lab_contract as contract


MAIN_SHA = "a" * 40
PREVIEW_SHA = "b" * 40


def valid_session() -> dict:
    return {
        "schema": contract.SESSION_SCHEMA,
        "session_id": "ui-lab-demo-001",
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
            "main_sha": MAIN_SHA,
            "preview_sha": PREVIEW_SHA,
        },
        "device_profile": "tab-s9",
        "viewport": {
            "width": 1280,
            "height": 800,
            "device_scale_factor": 1,
        },
        "quick_flow": {"name": "open-tablet-layout", "version": "1.0.0"},
        "timeout": {"timeout_ms": 120000, "cleanup_on_cancel": True},
        "artifacts": [],
    }


def event(sequence: int, request_id: str = "ui-request-001") -> dict:
    return {
        "schema": contract.EVENT_SCHEMA,
        "event_id": f"ui-event-{sequence:03d}",
        "session_id": "ui-lab-demo-001",
        "request_id": request_id,
        "sequence": sequence,
        "event_type": "state_observed",
        "actor": "custom_gpt",
        "timestamp": f"2026-09-14T08:0{sequence}:00Z",
        "status": "running",
        "summary": "Synthetic state observed.",
        "evidence": [],
    }


class KggUiLabContractTests(unittest.TestCase):
    def test_valid_session_and_capability_pass(self) -> None:
        self.assertEqual(contract.validate_session(valid_session())["session_id"], "ui-lab-demo-001")
        self.assertTrue(contract.runner_supports(valid_session()["runner"], "browser"))

    def test_invalid_actor_is_rejected(self) -> None:
        value = valid_session()
        value["active_actor"] = "unknown-agent"
        with self.assertRaisesRegex(contract.ContractError, "actor"):
            contract.validate_session(value)

    def test_expired_lease_is_rejected_at_use_time(self) -> None:
        lease = valid_session()["lease"]
        now = datetime(2026, 9, 14, 8, 31, tzinfo=timezone.utc)
        with self.assertRaisesRegex(contract.ContractError, "lease_expired"):
            contract.assert_lease_active(lease, now=now)

    def test_http_non_localhost_url_is_rejected(self) -> None:
        value = valid_session()
        value["app"]["url"] = "http://preview.example.test/admin"
        with self.assertRaisesRegex(contract.ContractError, "app_url"):
            contract.validate_session(value)

    def test_missing_runner_capability_is_rejected(self) -> None:
        value = valid_session()
        value["runner"]["capabilities"] = ["capture"]
        with self.assertRaisesRegex(contract.ContractError, "capability"):
            contract.require_capability(value, "browser")

    def test_event_chain_is_append_only_and_contiguous(self) -> None:
        events = [event(1), event(2, request_id="ui-request-002")]
        self.assertEqual(contract.validate_event_chain(events), 2)
        duplicate = [events[0], dict(events[0], event_id="ui-event-999", sequence=2)]
        with self.assertRaisesRegex(contract.ContractError, "duplicate_request"):
            contract.validate_event_chain(duplicate)
        gap = [events[0], dict(events[1], sequence=3)]
        with self.assertRaisesRegex(contract.ContractError, "event_sequence"):
            contract.validate_event_chain(gap)

    def test_replayed_request_is_rejected(self) -> None:
        accepted = dict(event(1), event_type="request_accepted")
        with self.assertRaisesRegex(contract.ContractError, "duplicate_request"):
            contract.assert_request_not_replayed([accepted], "ui-request-001")

    def test_sensitive_event_fields_are_rejected(self) -> None:
        value = event(1)
        value["evidence"] = [{"kind": "raw_qr", "value": "synthetic"}]
        with self.assertRaisesRegex(contract.ContractError, "sensitive"):
            contract.validate_event(value)

    def test_invalid_timeout_and_quick_flow_are_rejected(self) -> None:
        value = valid_session()
        value["timeout"]["timeout_ms"] = 0
        with self.assertRaisesRegex(contract.ContractError, "timeout"):
            contract.validate_session(value)
        value = valid_session()
        value["quick_flow"]["version"] = "v1"
        with self.assertRaisesRegex(contract.ContractError, "quick_flow"):
            contract.validate_session(value)


if __name__ == "__main__":
    unittest.main()
