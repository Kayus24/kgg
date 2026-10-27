"""Bounded real GitHub binding: no arbitrary routes or remote writes."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]

class ActionBindingTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('kgg_actions_test', ROOT / 'kgg-plugin/mcp/kgg_actions.py')
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)
        self.transport = Mock(return_value={'object': {'sha': 'a' * 40}})
        self.binding = self.module.KggActions(transport=self.transport)

    def test_all_thirty_canonical_operations_are_declared(self):
        self.assertEqual(len(self.binding.capabilities()['actions']), 30)

    def test_public_runtime_binds_real_main_and_gates_actions(self):
        spec = importlib.util.spec_from_file_location('action_server_test', ROOT / 'kgg-plugin/mcp/server.py')
        server = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(server)
        runtime = server.Runtime(kgg_actions=self.binding)
        self.assertEqual(runtime.current('codex')['main_sha'], 'a' * 40)
        catalog = {tool['name'] for tool in server.tool_catalog()}
        self.assertTrue({'get_kgg_action_capabilities', 'run_kgg_action'}.issubset(catalog))
        result = runtime.call('run_kgg_action', {'actor': 'codex', 'operation': 'getKggMainCommit', 'payload': {}})
        self.assertEqual(result['result']['object']['sha'], 'a' * 40)
        with self.assertRaisesRegex(server.ServerError, 'external_gate_required'):
            runtime.call('run_kgg_action', {'actor': 'codex', 'operation': 'submitKggMainGate', 'payload': {}})

    def test_canonical_route_snapshot_has_exact_source_hash(self):
        import hashlib, json, re
        source = ROOT / 'docs/kgg-custom-gpt-action-api-openapi.yaml'
        snapshot = json.loads((ROOT / 'kgg-plugin/mcp/kgg_action_routes.json').read_text(encoding='utf-8'))
        self.assertEqual(snapshot['source_sha256'], hashlib.sha256(source.read_bytes()).hexdigest())
        operations = set(re.findall(r'^\s+operationId:\s*([A-Za-z][A-Za-z0-9_]*)\s*$', source.read_text(encoding='utf-8'), re.MULTILINE))
        self.assertEqual(len(operations), 30)
        self.assertEqual(set(self.binding.actions), operations)

    def test_existing_compatibility_shim_accepts_live_adapter_contract(self):
        import sys
        sys.path.insert(0, str(ROOT / 'release-pipeline'))
        from kgg_ui_lab_mcp_adapter import KggCompatibilityShim, KGG_ACTION_OPERATIONALS
        self.assertEqual({name for name, _ in KGG_ACTION_OPERATIONALS}, set(self.binding.actions))
        shim = KggCompatibilityShim(main_sha='a' * 40, action_adapter=self.binding)
        self.transport.return_value = 'Synthetic bounded topic text'
        result = shim.run_kgg_action('getKggMemoryPack', {'pack_name': 'workflow-01.md'})
        self.assertEqual(result['result']['content'], 'Synthetic bounded topic text')

    def test_compatibility_workflow_entry_point_preserves_dispatch_status(self):
        import sys
        sys.path.insert(0, str(ROOT / 'release-pipeline'))
        from kgg_ui_lab_mcp_adapter import KggCompatibilityShim
        dispatch = Mock(return_value={'status': 'dispatch_accepted', 'http_status': 204})
        binding = self.module.KggActions(transport=self.transport, dispatch_transport=dispatch,
                                        allowed_workflow_operations=('submitKggReadOnlyValidation',))
        shim = KggCompatibilityShim(main_sha='a' * 40, action_adapter=binding)
        self.assertTrue(callable(getattr(shim, 'dispatch_kgg_workflow', None)))
        result = shim.dispatch_kgg_workflow('submitKggReadOnlyValidation', {
            'ref': 'main', 'inputs': {'request_id': 'shim-workflow-001', 'source_sha': 'a' * 40, 'validation_profile': 'gpt-contracts'},
        })
        self.assertEqual(result['status'], 'dispatch_accepted')
        self.assertTrue(result['reconciliation_required'])
        self.transport.assert_not_called()
        self.assertEqual(dispatch.call_count, 1)

    def test_fixed_resource_and_issue_identity_never_fetch_arbitrary_paths(self):
        with self.assertRaisesRegex(self.module.ActionError, 'kgg_resource_invalid'):
            self.binding.resource('../secret')
        with self.assertRaisesRegex(self.module.ActionError, 'ticket_id_invalid'):
            self.binding.ticket('../29')
        self.transport.assert_not_called()
        self.transport.return_value = {'number': 29, 'state': 'open', 'title': 'Synthetic issue', 'body': 'excluded'}
        summary = self.binding.ticket('#29')
        self.assertEqual(summary['source'], 'github_issue')
        self.assertNotIn('body', summary)
        self.transport.return_value['pull_request'] = {}
        with self.assertRaisesRegex(self.module.ActionError, 'ticket_state_invalid'):
            self.binding.ticket('#29')

    def test_cli_errors_hide_stderr_and_never_invoke_a_shell(self):
        from unittest.mock import patch
        result = Mock(returncode=1, stdout=b'', stderr=b'sensitive synthetic stderr')
        with patch.object(self.module.shutil, 'which', return_value='gh.exe'), patch.object(self.module.subprocess, 'run', return_value=result) as invoked:
            with self.assertRaisesRegex(self.module.ActionError, '^kgg_github_read_failed$'):
                self.module.github_read('/repos/Kayus24/kgg/git/ref/heads/main', 'application/vnd.github+json')
            self.assertNotIn('shell', invoked.call_args.kwargs)
            self.assertIn('GET', invoked.call_args.args[0])

    def test_main_read_uses_fixed_route(self):
        self.binding.run('getKggMainCommit', {})
        self.transport.assert_called_once_with('/repos/Kayus24/kgg/git/ref/heads/main', 'application/vnd.github+json')

    def test_path_traversal_unknown_and_query_injection_are_denied(self):
        for operation, payload in [('getKggMemoryPack', {'pack_name': '../workflow.md'}), ('getKggMemoryPack', {'pack_name': '--help'}), ('getKggMainCommit', {'url': 'https://example.org'}), ('getKggMainCommit', {'ref': 'other'}), ('arbitrary', {})]:
            with self.subTest(operation=operation, payload=payload), self.assertRaises(self.module.ActionError):
                self.binding.run(operation, payload)
        self.transport.assert_not_called()

    def test_every_remote_write_requires_existing_external_gate(self):
        for action in self.binding.capabilities()['actions']:
            if action['method'] == 'POST':
                with self.assertRaisesRegex(self.module.ActionError, 'external_gate_required'):
                    self.binding.run(action['operation'], {})
        self.transport.assert_not_called()

    def test_integer_and_query_bounds_fail_closed(self):
        for operation, payload in [('getKggPreviewGateRun', {'run_id': True}), ('getKggPreviewGateRun', {'run_id': -1}), ('listKggReadOnlyValidationRuns', {'per_page': 1000}), ('getKggMemoryIndex', {'ref': 'other'})]:
            with self.assertRaises(self.module.ActionError):
                self.binding.run(operation, payload)
        self.transport.assert_not_called()

    def test_raw_memory_pack_and_run_parameters_are_bounded(self):
        self.binding.run('getKggMemoryPack', {'pack_name': 'workflow-01.md'})
        self.transport.assert_called_with('/repos/Kayus24/kgg-project-memory/contents/memory/packs/workflow-01.md?ref=main', 'application/vnd.github.raw+json')
        self.binding.run('getKggPreviewGateRun', {'run_id': 123})
        self.transport.assert_called_with('/repos/Kayus24/kgg/actions/runs/123', 'application/vnd.github+json')

if __name__ == '__main__':
    unittest.main()
