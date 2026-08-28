#!/usr/bin/env python3
from __future__ import annotations

import copy
import re
import sys
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import kgg_brain_relay_worker as contract


class BrainRelayWorkerContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.capsule = contract.synthetic_capsule()

    def _openapi_path_blocks(self, path: str) -> list[str]:
        blocks = []
        for filename in (
            "docs/kgg-custom-gpt-action-api-openapi.yaml",
            "docs/kgg-patient-custom-gpt-action-api-openapi.yaml",
        ):
            text = (ROOT / filename).read_text(encoding="utf-8")
            match = re.search(
                rf"^  {re.escape(path)}:\n(.*?)(?=^  \S|\Z)",
                text,
                re.MULTILINE | re.DOTALL,
            )
            self.assertIsNotNone(match, f"missing {path} in {filename}")
            blocks.append(match.group(1))
        self.assertEqual(2, len(blocks))
        return blocks

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
        event = contract.synthetic_handoff(self.capsule)
        self.assertEqual(
            "b92d3e051de1645bcd7b37690a8370954a2641ee60e4966c6d103adc05c8a910",
            contract.handoff_sha256_for(event),
        )
        self.assertEqual(event, contract.validate_handoff_event(event, self.capsule))
        stale = copy.deepcopy(event)
        stale["generation"] = 2
        stale["handoff_sha256"] = contract.handoff_sha256_for(stale)
        with self.assertRaisesRegex(contract.ContractError, "stale_generation"):
            contract.validate_handoff_event(stale, self.capsule)

        legacy = copy.deepcopy(event)
        legacy["handoff_hash"] = legacy.pop("handoff_sha256")
        self.assertEqual(legacy, contract.validate_handoff_event(legacy, self.capsule))

    def test_shared_hash_rules_use_fixed_fixture_values(self) -> None:
        self.assertEqual(
            "Use only the bounded coordination bridge; keep the full runtime local.",
            contract.canonical_requirement_text(
                "  Use only the bounded coordination bridge; keep the full runtime local.\r\n"
            ),
        )
        self.assertEqual(
            "723a3cb65ae66ecbbf147b29f31b04e2d16910bf0fea33505459d32cc68b5022",
            contract.SHARED_FIXTURE_REQUIREMENTS_SHA256,
        )
        self.assertEqual(
            contract.SHARED_FIXTURE_REQUIREMENTS_SHA256,
            contract.requirements_sha256_for("\r\n" + contract.SHARED_FIXTURE_REQUIREMENT_TEXT + "\r"),
        )
        self.assertRegex(contract.SHARED_FIXTURE_REQUIREMENTS_SHA256, r"^[0-9a-f]{64}$")
        bad_capsule = copy.deepcopy(self.capsule)
        bad_capsule["requirements"]["text"] += " changed"
        with self.assertRaisesRegex(contract.ContractError, "requirements_sha256"):
            contract.validate_task_capsule(bad_capsule)

        handoff = contract.synthetic_handoff(self.capsule)
        self.assertEqual(
            "b92d3e051de1645bcd7b37690a8370954a2641ee60e4966c6d103adc05c8a910",
            contract.SHARED_FIXTURE_HANDOFF_SHA256,
        )
        with_both_hash_fields = copy.deepcopy(handoff)
        with_both_hash_fields["handoff_hash"] = "a" * 64
        self.assertEqual(
            contract.canonical_handoff_representation(handoff),
            contract.canonical_handoff_representation(with_both_hash_fields),
        )
        self.assertEqual(
            '{"append_only":true,"event_id":"kgg-event-example-001","event_type":"worker_result",'
            '"evidence":[{"kind":"test","name":"brain-relay-selftest","status":"PASS"}],'
            '"from_role":"luna-max-worker","generation":1,"requirements_sha256":"'
            + contract.SHARED_FIXTURE_REQUIREMENTS_SHA256
            + '","revision":1,"schema":"kgg-brain-relay-worker/handoff-v2","sequence":1,'
            '"summary":"The worker returned its bounded result.","task_id":"kgg-brain-example-001",'
            '"to_role":"luna-relay","transport_only":true}',
            contract.canonical_handoff_representation(handoff),
        )
        unicode_event = copy.deepcopy(handoff)
        unicode_event["summary"] = "Ergebnis ä"
        self.assertIn("Ergebnis ä", contract.canonical_handoff_representation(unicode_event))
        self.assertNotIn("\\u00e4", contract.canonical_handoff_representation(unicode_event))
        self.assertEqual(
            contract.SHARED_FIXTURE_HANDOFF_SHA256,
            contract.handoff_sha256_for(with_both_hash_fields),
        )
        self.assertRegex(contract.SHARED_FIXTURE_HANDOFF_SHA256, r"^[0-9a-f]{64}$")

    def test_bridge_fixture_has_exact_allowlist_and_memory_states(self) -> None:
        bridge = contract.synthetic_bridge()
        handoff = contract.synthetic_handoff(self.capsule)
        self.assertEqual(list(contract.BRIDGE_FIELDS), list(bridge))
        self.assertEqual(set(contract.BRIDGE_FIELDS), set(bridge))
        self.assertEqual(contract.BRIDGE_SCHEMA_VERSION, bridge["schema_version"])
        self.assertEqual(self.capsule["task_id"], bridge["task_id"])
        self.assertEqual(contract.TASK_STATES, contract.BRIDGE_STATUSES)
        self.assertEqual(contract.TASK_STATES, contract.RESULT_STATUSES)
        self.assertTrue(contract.BRIDGE_ROLES.issuperset(contract.KNOWN_ROLES))
        for role in contract.BRIDGE_ROLES:
            candidate = copy.deepcopy(bridge)
            candidate["role"] = role
            self.assertEqual(
                candidate,
                contract.validate_bridge(
                    candidate,
                    self.capsule["requirements"]["text"],
                    handoff,
                    capsule=self.capsule,
                ),
            )
        for status in contract.TASK_STATES:
            candidate = copy.deepcopy(bridge)
            candidate["status"] = status
            contract.validate_bridge(
                candidate,
                self.capsule["requirements"]["text"],
                handoff,
                capsule=self.capsule,
            )
        self.assertEqual(
            "coordination-bridge/tasks/kgg-brain-example-001.json",
            contract.bridge_path_for(self.capsule["task_id"]),
        )
        self.assertEqual(
            contract.SHARED_FIXTURE_REQUIREMENTS_SHA256,
            bridge["requirements_sha256"],
        )
        self.assertEqual(contract.SHARED_FIXTURE_HANDOFF_SHA256, bridge["handoff_sha256"])

    def test_bridge_rejects_extra_or_sensitive_data(self) -> None:
        bridge = contract.synthetic_bridge()
        handoff = contract.synthetic_handoff(self.capsule)

        extra = copy.deepcopy(bridge)
        extra["prompt"] = "must stay local"
        with self.assertRaisesRegex(contract.ContractError, "fields must be exact"):
            contract.validate_bridge(
                extra,
                self.capsule["requirements"]["text"],
                handoff,
                capsule=self.capsule,
            )

        missing = copy.deepcopy(bridge)
        del missing["next_action"]
        with self.assertRaisesRegex(contract.ContractError, "fields must be exact"):
            contract.validate_bridge(
                missing,
                self.capsule["requirements"]["text"],
                handoff,
                capsule=self.capsule,
            )

        sensitive_action = copy.deepcopy(bridge)
        sensitive_action["next_action"] = "write patient log"
        with self.assertRaisesRegex(contract.ContractError, "runtime or sensitive data"):
            contract.validate_bridge(
                sensitive_action,
                self.capsule["requirements"]["text"],
                handoff,
                capsule=self.capsule,
            )

    def test_both_api_openapi_schemas_expose_only_the_bridge_for_v2(self) -> None:
        bridge_path = "/repos/Kayus24/kgg-project-memory/contents/coordination-bridge/tasks/{task_id}.json"
        bridge_blocks = self._openapi_path_blocks(bridge_path)
        required = "required: [schema_version, task_id, role, generation, revision, status, requirements_sha256, handoff_sha256, next_action]"
        role_enum = "enum: [luna-manager, lead-gpt, gpt-subchat, lead-synthesis, luna-relay, luna-max-worker, verifier, cricket, ticket-master, sol-endboss, ci-acceptance, status-read]"
        state_enum = "enum: [PASS, FAIL, BLOCKED, PENDING, NEEDS_LEAD, NEEDS_SOL]"
        for bridge_block in bridge_blocks:
            self.assertIn("operationId: getKggAgentCoordinationBridgeTask", bridge_block)
            self.assertIn("additionalProperties: false", bridge_block)
            self.assertIn(required, bridge_block)
            for field in contract.BRIDGE_FIELDS:
                self.assertIsNotNone(
                    re.search(rf"^\s{{18}}{re.escape(field)}:$", bridge_block, re.MULTILINE),
                    field,
                )
            self.assertIn(role_enum, bridge_block)
            self.assertIn(state_enum, bridge_block)

        for filename in (
            "docs/kgg-custom-gpt-action-api-openapi.yaml",
            "docs/kgg-patient-custom-gpt-action-api-openapi.yaml",
        ):
            text = (ROOT / filename).read_text(encoding="utf-8")
            self.assertEqual(1, text.count(bridge_path + ":"), filename)
            self.assertNotIn("coordination-v2", text, filename)
            path_lines = [line[2:].split(":", 1)[0] for line in text.splitlines() if line.startswith("  /")]
            self.assertFalse(any("handoffs" in path or "cricket" in path for path in path_lines), filename)
            self.assertEqual(
                1,
                text.count("operationId: getKggAgentCoordinationBridgeTask"),
                filename,
            )
            for operation_id in (
                "getKggAgentCoordinationIndex",
                "getKggAgentCoordinationThread",
                "submitKggAgentCoordinationEvent",
                "listKggAgentCoordinationRuns",
            ):
                self.assertEqual(1, text.count(f"operationId: {operation_id}"), filename)

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
