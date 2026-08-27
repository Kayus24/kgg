#!/usr/bin/env python3
from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import kgg_brain_relay_worker as contract


class BrainRelayWorkerContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.capsule = contract.synthetic_capsule()

    def test_capsule_and_status_route_are_valid(self) -> None:
        self.assertEqual(self.capsule, contract.validate_task_capsule(self.capsule))
        self.assertEqual(
            ["luna-manager", "status-read"],
            contract.validate_route(["luna-manager", "status-read"], task_kind="status"),
        )

    def test_real_route_requires_lead_synthesis_and_ci(self) -> None:
        bad = copy.deepcopy(self.capsule)
        bad["route"] = ["luna-manager", "lead-gpt", "luna-relay"]
        with self.assertRaisesRegex(contract.ContractError, "complete"):
            contract.validate_task_capsule(bad)

    def test_worker_and_subchat_limits_are_enforced(self) -> None:
        too_many = copy.deepcopy(self.capsule)
        too_many["sub_chats"] = [
            {
                "role": "gpt-subchat",
                "chat_id": f"kgg-sub-{index}",
                "scope": f"scope-{index}",
                "generation": 1,
                "revision": 1,
            }
            for index in range(5)
        ]
        with self.assertRaisesRegex(contract.ContractError, "at most four"):
            contract.validate_task_capsule(too_many)

        overlap = copy.deepcopy(self.capsule)
        overlap["workers"][1]["scope"] = overlap["workers"][0]["scope"]
        with self.assertRaisesRegex(contract.ContractError, "pairwise disjoint"):
            contract.validate_task_capsule(overlap)

        sub_overlap = contract.synthetic_capsule(with_sub_chats=True)
        sub_overlap["sub_chats"].append(
            {
                "role": "gpt-subchat",
                "chat_id": "kgg-sub-test-2",
                "scope": "contract-reading",
                "generation": 1,
                "revision": 1,
            }
        )
        with self.assertRaisesRegex(contract.ContractError, "sub-chat scopes"):
            contract.validate_task_capsule(sub_overlap)

    def test_retry_attempts_must_be_different(self) -> None:
        bad = copy.deepcopy(self.capsule)
        bad["retry"] = {
            "luna_attempts": 2,
            "max_luna_attempts": 2,
            "after_exhaustion": "lead-gpt",
            "sol_gate": "cricket-one-time",
            "attempts": [
                {"attempt": 1, "approach": "A", "approach_sha256": "b" * 64},
                {"attempt": 2, "approach": "B", "approach_sha256": "b" * 64},
            ],
        }
        with self.assertRaisesRegex(contract.ContractError, "substantively different"):
            contract.validate_task_capsule(bad)

        missing_record = copy.deepcopy(self.capsule)
        missing_record["retry"]["luna_attempts"] = 1
        with self.assertRaisesRegex(contract.ContractError, "equal the number"):
            contract.validate_task_capsule(missing_record)

    def test_handoff_hash_and_stale_generation(self) -> None:
        event = {
            "schema": contract.HANDOFF_SCHEMA,
            "event_id": "kgg-event-test-001",
            "sequence": 1,
            "event_type": "worker_result",
            "task_id": self.capsule["task_id"],
            "generation": 1,
            "revision": 1,
            "from_role": "luna-max-worker",
            "to_role": "luna-relay",
            "requirements_sha256": self.capsule["requirements"]["sha256"],
            "transport_only": True,
            "summary": "bounded result",
            "evidence": [],
            "append_only": True,
        }
        event["handoff_hash"] = contract.handoff_hash_for(event)
        self.assertEqual(event, contract.validate_handoff_event(event, self.capsule))
        stale = copy.deepcopy(event)
        stale["generation"] = 2
        stale["handoff_hash"] = contract.handoff_hash_for(stale)
        with self.assertRaisesRegex(contract.ContractError, "stale_generation"):
            contract.validate_handoff_event(stale, self.capsule)

    def test_browser_relay_is_single_run_and_bounded(self) -> None:
        capsule = contract.synthetic_capsule(with_sub_chats=True)
        batch = {
            "schema": contract.BROWSER_RELAY_SCHEMA,
            "task_id": capsule["task_id"],
            "generation": 1,
            "revision": 1,
            "chat_ids": ["kgg-sub-example-1", "kgg-sub-example-2"],
            "dispatch_mode": "single-run",
            "wait_for_completion": True,
            "status_prompts": 0,
            "timeout_seconds": contract.BROWSER_TIMEOUT_SECONDS,
            "fresh_retry_limit": 1,
            "retries_used": 0,
            "completion_channel": "coordination-action",
            "fallback": "browser-relay",
        }
        self.assertEqual(batch, contract.validate_browser_relay_batch(batch, capsule))
        bad = copy.deepcopy(batch)
        bad["status_prompts"] = 1
        with self.assertRaisesRegex(contract.ContractError, "without status prompts"):
            contract.validate_browser_relay_batch(bad, capsule)

        unrelated = copy.deepcopy(batch)
        unrelated["chat_ids"] = ["kgg-unrelated-chat"]
        with self.assertRaisesRegex(contract.ContractError, "only target sub-chats"):
            contract.validate_browser_relay_batch(unrelated, capsule)

    def test_ticket_master_and_sol_guards(self) -> None:
        contract.validate_ticket_action(
            {
                "role": "ticket-master",
                "operation": "create",
                "duplicate_checked": True,
                "source": "private-memory-gate",
                "program": False,
                "close": False,
                "invent": False,
            }
        )
        with self.assertRaisesRegex(contract.ContractError, "not allowed to close"):
            contract.validate_ticket_action(
                {
                    "role": "ticket-master",
                    "operation": "create",
                    "duplicate_checked": True,
                    "source": "private-memory-gate",
                    "program": False,
                    "close": True,
                    "invent": False,
                }
            )
        contract.validate_sol_request(
            {
                "role": "sol-endboss",
                "state": "SLEEPING",
                "requested_action": "observe",
                "internal_sol_agents": False,
            }
        )
        with self.assertRaisesRegex(contract.ContractError, "may not code"):
            contract.validate_sol_request(
                {"role": "sol-endboss", "state": "SLEEPING", "requested_action": "code"}
            )
        with self.assertRaisesRegex(contract.ContractError, "may not code"):
            contract.validate_sol_request(
                {"role": "sol-endboss", "state": "SLEEPING", "requested_action": "repo-analysis"}
            )

    def test_rotation_and_cricket_classification(self) -> None:
        rotated = copy.deepcopy(self.capsule)
        rotated["rotation"].update(
            {
                "meaningful_events": 40,
                "state": "HARD_SWITCH",
                "old_generation": "RETIRED",
            }
        )
        contract.validate_task_capsule(rotated)
        contract.validate_cricket_event(
            {
                "schema": contract.HANDOFF_SCHEMA,
                "event_id": "cricket-test-001",
                "sequence": 1,
                "event_type": "cricket_observation",
                "from_role": "cricket",
                "to_role": "luna-manager",
                "level": "L1",
                "classification": "technical-enforcement",
                "evidence": [{"kind": "contract", "status": "FAIL"}],
            }
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
