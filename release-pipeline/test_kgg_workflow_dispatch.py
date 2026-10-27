"""Default-closed workflow dispatch; the existing read tool never gains writes."""
from copy import deepcopy
import importlib.util
import hashlib
import json
from pathlib import Path
import re
import subprocess
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
SIX = (
    "submitKggReadOnlyValidation", "submitKggPreviewAuto", "submitKggDeviceTest",
    "submitKggAdminEditorSyncPreflight", "submitKggPatientPreviewFromAdmin",
    "submitKggAgentCoordinationEvent",
)
PROTECTED = ("submitKggMainGate", "submitKggAdminEditorSyncSnapshotPr")


def body(operation, request_id="dispatch-probe-001"):
    inputs = {"request_id": request_id}
    if operation in {"submitKggReadOnlyValidation", "submitKggDeviceTest"}:
        inputs["source_sha"] = "a" * 40
    if operation == "submitKggReadOnlyValidation":
        inputs["validation_profile"] = "gpt-contracts"
    if operation in {"submitKggPreviewAuto", "submitKggPatientPreviewFromAdmin", "submitKggAgentCoordinationEvent", "submitKggMemoryUpdate"}:
        inputs["payload_json"] = json.dumps({"request_id": request_id, "summary": "Synthetic schema probe"})
    if operation in {"submitKggPatientPreviewFromAdmin", "submitKggAgentCoordinationEvent", "submitKggMemoryUpdate"}:
        inputs["mode"] = "validate_only"
    return {"ref": "main", "inputs": inputs}


class WorkflowDispatchTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location("kgg_workflow_dispatch_test", ROOT / "kgg-plugin/mcp/kgg_actions.py")
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.read = Mock()
        self.post = Mock(return_value={"status": "dispatch_accepted", "http_status": 204})

    def binding(self, allowed=SIX):
        return self.module.KggActions(transport=self.read, dispatch_transport=self.post, allowed_workflow_operations=allowed)

    def test_dispatch_api_is_separate_and_default_closed(self):
        binding = self.module.KggActions(transport=self.read)
        self.assertTrue(hasattr(binding, "dispatch"), "separate default-closed dispatch API is missing")
        with self.assertRaisesRegex(self.module.ActionError, "workflow_host_disabled"):
            binding.dispatch(SIX[0], body(SIX[0]))
        self.read.assert_not_called()

    def test_explicit_six_operation_allowlist_routes_only_canonical_workflows(self):
        binding = self.binding()
        for operation in SIX:
            with self.subTest(operation=operation):
                payload = body(operation)
                result = binding.dispatch(operation, payload)
                self.assertEqual(result["status"], "dispatch_accepted")
                self.assertTrue(result["reconciliation_required"])
                self.assertEqual(result["request_id"], payload["inputs"]["request_id"])
                self.assertNotIn("PASS", json.dumps(result))
                self.assertEqual(self.post.call_args.args, (binding.actions[operation]["path"], payload))
        self.assertEqual(self.post.call_count, 6)
        self.read.assert_not_called()

    def test_allowlist_is_not_a_wildcard_or_an_untrusted_payload_field(self):
        for allowed in ["*", ("*",), ("getKggMainCommit",), ("unknown",), (True,)]:
            with self.subTest(allowed=allowed), self.assertRaisesRegex(self.module.ActionError, "workflow_allowlist_invalid"):
                self.binding(allowed)
        binding = self.binding((SIX[0],))
        for operation in SIX[1:]:
            with self.assertRaisesRegex(self.module.ActionError, "workflow_host_disabled"):
                binding.dispatch(operation, body(operation))
        self.post.assert_not_called()

    def test_get_only_run_never_uses_post_transport_even_when_enabled(self):
        binding = self.binding((*SIX, *PROTECTED, "submitKggMemoryUpdate"))
        for operation in (*SIX, *PROTECTED, "submitKggMemoryUpdate"):
            with self.subTest(operation=operation), self.assertRaisesRegex(self.module.ActionError, "external_gate_required"):
                binding.run(operation, body(operation))
        self.post.assert_not_called()
        self.read.assert_not_called()

    def test_model_phrases_cannot_enable_main_or_snapshot(self):
        binding = self.binding((*SIX, *PROTECTED))
        for operation in PROTECTED:
            payload = body(operation)
            payload["inputs"].update(approval_phrase="Gut für Main", mode="create_pr")
            with self.subTest(operation=operation), self.assertRaisesRegex(self.module.ActionError, "external_gate_required"):
                binding.dispatch(operation, payload)
        self.post.assert_not_called()

    def test_memory_validation_is_host_bound_but_apply_stays_external(self):
        operation = "submitKggMemoryUpdate"
        binding = self.binding((operation,))
        self.assertEqual(binding.dispatch(operation, body(operation))["status"], "dispatch_accepted")
        payload = body(operation, "dispatch-memory-apply")
        payload["inputs"]["mode"] = "apply"
        with self.assertRaisesRegex(self.module.ActionError, "external_gate_required"):
            binding.dispatch(operation, payload)
        self.assertEqual(self.post.call_count, 1)

    def test_memory_model_approval_and_supersedes_are_never_human_proof(self):
        operation = "submitKggMemoryUpdate"
        binding = self.binding((operation,))
        for key, value in [("approved_by", "max"), ("approval_quote", "Approved by me"), ("supersedes", ["existing-record"])]:
            payload = body(operation)
            payload["inputs"]["payload_json"] = json.dumps({"request_id": payload["inputs"]["request_id"], "record": {key: value}})
            with self.subTest(key=key), self.assertRaisesRegex(self.module.ActionError, "external_gate_required"):
                binding.dispatch(operation, payload)
        self.post.assert_not_called()

    def test_schema_ref_request_id_unknown_fields_and_enum_fail_before_transport(self):
        operation = SIX[0]
        valid = body(operation)
        bad = []
        for key, value in [("ref", "other"), ("ref", "main\n"), ("extra", True)]:
            payload = deepcopy(valid); payload[key] = value; bad.append(payload)
        for key, value in [("request_id", "../bad"), ("request_id", "bad id"), ("request_id", "UPPERCASE"), ("source_sha", "a" * 39), ("source_sha", True), ("validation_profile", "arbitrary"), ("extra", "unknown")]:
            payload = deepcopy(valid); payload["inputs"][key] = value; bad.append(payload)
        bad.extend([{}, {"ref": "main"}, {"ref": "main", "inputs": []}, {"ref": "main", "inputs": {"request_id": "missing-profile"}}])
        binding = self.binding()
        for payload in bad:
            with self.subTest(payload=payload), self.assertRaises(self.module.ActionError):
                binding.dispatch(operation, payload)
        self.post.assert_not_called()

    def test_json_payload_must_be_bounded_unique_object_with_matching_request_id(self):
        operation = "submitKggPreviewAuto"
        binding = self.binding()
        invalid = ["{", "[]", "null", '{"request_id":"other-request"}', '{"request_id":"dispatch-probe-001","request_id":"other-request"}', '{"request_id":"dispatch-probe-001","value":NaN}', json.dumps({"request_id": "dispatch-probe-001", "value": "x" * 120001})]
        for raw in invalid:
            payload = body(operation); payload["inputs"]["payload_json"] = raw
            with self.subTest(raw=raw[:75]), self.assertRaises(self.module.ActionError):
                binding.dispatch(operation, payload)
        self.post.assert_not_called()

    def test_patient_and_memory_mode_widening_is_rejected(self):
        binding = self.binding((*SIX, "submitKggMemoryUpdate"))
        for operation, mode in [("submitKggPatientPreviewFromAdmin", "publish_live"), ("submitKggMemoryUpdate", "batch_apply")]:
            payload = body(operation); payload["inputs"]["mode"] = mode
            with self.subTest(operation=operation), self.assertRaises(self.module.ActionError):
                binding.dispatch(operation, payload)
        payload = body("submitKggPatientPreviewFromAdmin")
        payload["inputs"]["payload_json"] = json.dumps({"request_id": "dispatch-probe-001", "value": "x" * 60001})
        with self.assertRaises(self.module.ActionError):
            binding.dispatch("submitKggPatientPreviewFromAdmin", payload)
        self.post.assert_not_called()

    def test_identical_accepted_request_is_not_dispatched_twice(self):
        binding = self.binding(); payload = body(SIX[0])
        first = binding.dispatch(SIX[0], payload)
        self.assertEqual(binding.dispatch(SIX[0], deepcopy(payload)), first)
        self.post.assert_called_once()
        changed = deepcopy(payload); changed["inputs"]["source_sha"] = "b" * 40
        with self.assertRaisesRegex(self.module.ActionError, "workflow_request_reused"):
            binding.dispatch(SIX[0], changed)

    def test_two_phase_workflows_keep_payload_binding_and_deduplicate_each_phase(self):
        for operation, final_mode in [("submitKggPatientPreviewFromAdmin", "publish_preview"), ("submitKggAgentCoordinationEvent", "apply")]:
            with self.subTest(operation=operation):
                binding = self.binding(); self.post.reset_mock()
                validation = body(operation)
                first = binding.dispatch(operation, validation)
                self.assertEqual(self.post.call_count, 1, "dispatch must not advance the workflow automatically")
                publication = deepcopy(validation); publication["inputs"]["mode"] = final_mode
                second = binding.dispatch(operation, publication)
                self.assertEqual(second["status"], "dispatch_accepted")
                self.assertNotEqual(first["payload_sha256"], second["payload_sha256"])
                self.assertEqual(self.post.call_count, 2)
                self.assertEqual(binding.dispatch(operation, deepcopy(validation)), first)
                self.assertEqual(binding.dispatch(operation, deepcopy(publication)), second)
                self.assertEqual(self.post.call_count, 2)

    def test_two_phase_workflows_reject_changed_json_payload_under_same_request(self):
        for operation, final_mode in [("submitKggPatientPreviewFromAdmin", "publish_preview"), ("submitKggAgentCoordinationEvent", "apply")]:
            with self.subTest(operation=operation):
                binding = self.binding(); self.post.reset_mock()
                validation = body(operation)
                binding.dispatch(operation, validation)
                changed = deepcopy(validation); changed["inputs"]["mode"] = final_mode
                document = json.loads(changed["inputs"]["payload_json"])
                document["summary"] = "Changed after validation"
                changed["inputs"]["payload_json"] = json.dumps(document)
                with self.assertRaisesRegex(self.module.ActionError, "workflow_request_reused"):
                    binding.dispatch(operation, changed)
                self.assertEqual(self.post.call_count, 1)

    def test_unknown_validation_blocks_following_write_phase_without_another_post(self):
        for operation, final_mode in [("submitKggPatientPreviewFromAdmin", "publish_preview"), ("submitKggAgentCoordinationEvent", "apply")]:
            with self.subTest(operation=operation):
                binding = self.binding(); self.post.reset_mock()
                self.post.side_effect = subprocess.TimeoutExpired("synthetic", 30)
                validation = body(operation)
                with self.assertRaisesRegex(self.module.ActionError, "dispatch_unknown"):
                    binding.dispatch(operation, validation)
                self.post.side_effect = None
                publication = deepcopy(validation); publication["inputs"]["mode"] = final_mode
                for payload in [validation, publication]:
                    with self.assertRaisesRegex(self.module.ActionError, "dispatch_unknown"):
                        binding.dispatch(operation, payload)
                self.assertEqual(self.post.call_count, 1)

    def test_unknown_write_phase_is_not_reposted_after_validation(self):
        for operation, final_mode in [("submitKggPatientPreviewFromAdmin", "publish_preview"), ("submitKggAgentCoordinationEvent", "apply")]:
            with self.subTest(operation=operation):
                binding = self.binding(); self.post.reset_mock(); self.post.side_effect = None
                validation = body(operation)
                first = binding.dispatch(operation, validation)
                publication = deepcopy(validation); publication["inputs"]["mode"] = final_mode
                self.post.side_effect = subprocess.TimeoutExpired("synthetic", 30)
                with self.assertRaisesRegex(self.module.ActionError, "dispatch_unknown"):
                    binding.dispatch(operation, publication)
                self.post.side_effect = None
                with self.assertRaisesRegex(self.module.ActionError, "dispatch_unknown"):
                    binding.dispatch(operation, deepcopy(publication))
                self.assertEqual(binding.dispatch(operation, deepcopy(validation)), first)
                self.assertEqual(self.post.call_count, 2)

    def test_unknown_dispatch_is_latched_and_never_retried(self):
        binding = self.binding(); self.post.side_effect = subprocess.TimeoutExpired("synthetic", 30)
        for _ in range(2):
            with self.assertRaisesRegex(self.module.ActionError, "dispatch_unknown"):
                binding.dispatch(SIX[0], body(SIX[0]))
        self.post.assert_called_once()

    def test_transport_result_other_than_explicit_204_is_unknown(self):
        for result in [None, {}, {"status": "PASS"}, {"http_status": 200}, {"status": "dispatch_accepted", "http_status": True}]:
            binding = self.binding(); self.post.return_value = result
            with self.subTest(result=result), self.assertRaisesRegex(self.module.ActionError, "dispatch_unknown"):
                binding.dispatch(SIX[0], body(SIX[0]))

    def test_capabilities_distinguish_host_disabled_external_and_mode_limits(self):
        binding = self.binding((SIX[0], "submitKggMemoryUpdate"))
        result = binding.workflow_capabilities()
        actions = {a["operation"]: a for a in result["actions"]}
        self.assertEqual(len(actions), 9)
        self.assertEqual(actions[SIX[0]]["status"], "AVAILABLE")
        self.assertEqual(actions["submitKggDeviceTest"]["status"], "HOST_DISABLED")
        self.assertEqual(actions[PROTECTED[0]]["status"], "EXTERNAL_GATE_REQUIRED")
        self.assertEqual(actions["submitKggMemoryUpdate"]["allowed_modes"], ["validate_only"])
        self.assertIn("apply", actions["submitKggMemoryUpdate"]["external_gate_modes"])
        self.assertIn("device", json.dumps(actions["submitKggDeviceTest"]).lower())
        self.assertIn("attestation", json.dumps(actions["submitKggAdminEditorSyncPreflight"]).lower())
        self.assertFalse(result["automatic_retry"])

    def test_snapshot_schemas_are_bound_to_exact_canonical_source(self):
        source = ROOT / "docs/kgg-custom-gpt-action-api-openapi.yaml"
        snapshot = json.loads((ROOT / "kgg-plugin/mcp/kgg_action_routes.json").read_text(encoding="utf-8"))
        self.assertEqual(snapshot["source_sha256"], hashlib.sha256(source.read_bytes()).hexdigest())
        operations = set(re.findall(r"^\s+operationId:\s*(submit[A-Za-z0-9_]*)\s*$", source.read_text(encoding="utf-8"), re.MULTILINE))
        binding = self.module.KggActions()
        posts = {name: action for name, action in binding.actions.items() if action["method"] == "POST"}
        self.assertEqual(set(posts), operations)
        self.assertEqual(len(posts), 9)
        for name, action in posts.items():
            with self.subTest(operation=name):
                schema = action["request_schema"]
                self.assertEqual(schema["required"], ["ref", "inputs"])
                self.assertEqual(set(schema["properties"]), {"ref", "inputs"})
                self.assertEqual(schema["properties"]["ref"]["enum"], ["main"])
                self.assertIn("request_id", schema["properties"]["inputs"]["required"])

    def test_native_transport_posts_json_stdin_once_and_204_is_only_acceptance(self):
        route = "/repos/Kayus24/kgg/actions/workflows/kgg-gpt-readonly-validation.yml/dispatches"
        payload = body(SIX[0])
        process = Mock(returncode=0, stdout="HTTP/2.0 204 No Content\r\n\r\n", stderr="")
        with patch.object(self.module.shutil, "which", return_value="gh.exe"), patch.object(self.module.subprocess, "run", return_value=process) as run:
            result = self.module.github_dispatch(route, payload)
        self.assertEqual(result, {"status": "dispatch_accepted", "http_status": 204})
        run.assert_called_once()
        argv = run.call_args.args[0]
        self.assertEqual(argv[argv.index("--method") + 1], "POST")
        self.assertEqual(argv[argv.index("--input") + 1], "-")
        self.assertEqual(json.loads(run.call_args.kwargs["input"]), payload)
        self.assertNotIn("shell", run.call_args.kwargs)
        self.assertNotIn("payload_json", " ".join(argv))

    def test_native_transport_never_posts_unknown_route(self):
        with patch.object(self.module.subprocess, "run") as run:
            for route in ["https://example.invalid/", "/repos/other/repo/actions/workflows/x.yml/dispatches", "/repos/Kayus24/kgg/actions/workflows/arbitrary.yml/dispatches"]:
                with self.subTest(route=route), self.assertRaises(self.module.ActionError):
                    self.module.github_dispatch(route, body(SIX[0]))
        run.assert_not_called()

    def test_native_transport_cannot_bypass_protected_workflows(self):
        binding = self.binding()
        with patch.object(self.module.subprocess, "run") as run:
            for operation in PROTECTED:
                with self.subTest(operation=operation), self.assertRaisesRegex(self.module.ActionError, "external_gate_required"):
                    self.module.github_dispatch(binding.actions[operation]["path"], body(operation))
            payload = body("submitKggMemoryUpdate"); payload["inputs"]["mode"] = "apply"
            with self.assertRaisesRegex(self.module.ActionError, "external_gate_required"):
                self.module.github_dispatch(binding.actions["submitKggMemoryUpdate"]["path"], payload)
        run.assert_not_called()

    def test_native_explicit_http_rejection_is_not_acceptance_or_retried(self):
        route = "/repos/Kayus24/kgg/actions/workflows/kgg-gpt-readonly-validation.yml/dispatches"
        process = Mock(returncode=1, stdout="HTTP/2.0 403 Forbidden\r\n\r\n", stderr="synthetic private detail")
        with patch.object(self.module.shutil, "which", return_value="gh.exe"), patch.object(self.module.subprocess, "run", return_value=process) as run:
            with self.assertRaisesRegex(self.module.ActionError, "^dispatch_rejected$"):
                self.module.github_dispatch(route, body(SIX[0]))
        run.assert_called_once()

    def test_native_timeout_or_unclear_response_never_retries_or_leaks_stderr(self):
        route = "/repos/Kayus24/kgg/actions/workflows/kgg-gpt-readonly-validation.yml/dispatches"
        for problem in [subprocess.TimeoutExpired("synthetic", 30), OSError("synthetic private detail"), Mock(returncode=1, stdout="HTTP/2.0 503 Unavailable\n", stderr="synthetic private detail"), Mock(returncode=0, stdout="", stderr="synthetic private detail")]:
            with patch.object(self.module.shutil, "which", return_value="gh.exe"), patch.object(self.module.subprocess, "run") as run:
                if isinstance(problem, BaseException): run.side_effect = problem
                else: run.return_value = problem
                with self.subTest(problem=type(problem).__name__), self.assertRaisesRegex(self.module.ActionError, "^dispatch_unknown$"):
                    self.module.github_dispatch(route, body(SIX[0]))
                run.assert_called_once()


if __name__ == "__main__":
    unittest.main()
