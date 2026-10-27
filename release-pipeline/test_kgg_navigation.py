"""Public navigation acceptance through MCP and the real browser boundary."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_kgg_real_browser_bridge import server, _runtime_available, _real_runtime, _session, _visual_request, local_fixture_server
from test_kgg_ui_lab_flow_persistence import flow


class NavigationTests(unittest.TestCase):
    def setUp(self):
        runtime = _runtime_available()
        if runtime is None:
            self.fail('Navigation acceptance requires provisioned Playwright')
        node, modules = runtime
        self.env = patch.dict('os.environ', {'KGG_REAL_BROWSER': '1', 'KGG_BROWSER_NODE': node, 'KGG_PLAYWRIGHT_NODE_PATH': modules})
        self.env.start()
        self.addCleanup(self.env.stop)

    def call(self, runtime, name, arguments):
        return server.handle(runtime, {'jsonrpc': '2.0', 'id': 1, 'method': 'tools/call', 'params': {'name': name, 'arguments': arguments}})['result']

    def act(self, runtime, sid, operation, expected, observation):
        return self.call(runtime, 'execute_visual_action', {
            'request': _visual_request(session_id=sid, request_id=sid + '-act', operation='execute_visual_action'),
            'decision': {'operation': operation, 'label': operation, 'expected_state_after': expected, 'observation_id': observation},
        })

    def start_observe(self, runtime, url, sid):
        self.call(runtime, 'start_ui_session', {'session': _session(url, session_id=sid, request_id=sid + '-start', capabilities=['browser', 'capture', 'visual_loop'])})
        result = self.call(runtime, 'observe_visual_state', {'request': _visual_request(session_id=sid, request_id=sid + '-observe', operation='observe_visual_state')})
        self.assertFalse(result.get('isError'), result)
        return result['structuredContent']['observation']

    def test_reload_confirms_fresh_capture_with_unchanged_state(self):
        with local_fixture_server('kgg_ui_lab_navigation_fixture.html') as url:
            runtime = _real_runtime()
            before = self.start_observe(runtime, url, 'navigation-reload-session')
            result = self.act(runtime, 'navigation-reload-session', 'reload', 'navigation-entry', before['id'])
            self.assertFalse(result.get('isError'), result)
            evidence = result['structuredContent']['evidence']
            self.assertEqual(evidence['status'], 'PASS')
            self.assertEqual(evidence['state_before'], evidence['state_after'])
            self.assertTrue(evidence['navigation_completed'])
            self.assertNotEqual(evidence['artifacts'][0]['id'], evidence['artifacts'][1]['id'])

    def test_back_returns_to_allowed_history_entry(self):
        with local_fixture_server('kgg_ui_lab_navigation_fixture.html') as url:
            runtime = _real_runtime()
            before = self.start_observe(runtime, url + '?history=1', 'navigation-back-session')
            self.assertEqual(before['state'], 'navigation-second')
            result = self.act(runtime, 'navigation-back-session', 'back', 'navigation-entry', before['id'])
            self.assertFalse(result.get('isError'), result)
            self.assertEqual(result['structuredContent']['result']['state_after'], 'navigation-entry')

    def test_back_without_allowed_history_fails_closed(self):
        with local_fixture_server('kgg_ui_lab_navigation_fixture.html') as url:
            runtime = _real_runtime()
            before = self.start_observe(runtime, url, 'navigation-no-history-session')
            result = self.act(runtime, 'navigation-no-history-session', 'back', 'navigation-entry', before['id'])
            self.assertTrue(result.get('isError'), result)
            self.assertIn('back_history_unavailable', str(result))
            self.assertNotIn('"status": "PASS"', str(result))

    def test_navigation_rejects_stale_observation_before_dispatch(self):
        with local_fixture_server('kgg_ui_lab_navigation_fixture.html') as url:
            runtime = _real_runtime()
            self.start_observe(runtime, url, 'navigation-stale-session')
            result = self.act(runtime, 'navigation-stale-session', 'reload', 'navigation-entry', '0' * 64)
            self.assertTrue(result.get('isError'), result)
            self.assertIn('visual_observation_stale', str(result))
            self.assertEqual(runtime.sessions['navigation-stale-session']['status'], 'observing')

    def test_public_catalog_and_saved_flow_accept_navigation(self):
        catalog = {tool['name']: tool for tool in server.tool_catalog()}
        enum = catalog['execute_visual_action']['inputSchema']['properties']['decision']['properties']['operation']['enum']
        self.assertTrue({'back', 'reload'}.issubset(enum))
        with tempfile.TemporaryDirectory() as directory:
            runtime = server.Runtime(flow_store_path=Path(directory) / 'flows.json')
            definition = flow()
            definition['steps'] = [
                {'sequence': 1, 'operation': 'reload', 'label': 'reload'},
                {'sequence': 2, 'operation': 'back', 'label': 'back'},
            ]
            saved = runtime.save_flow({'flow': definition})
            self.assertEqual([step['operation'] for step in saved['flow']['steps']], ['reload', 'back'])

    def test_saved_navigation_flow_replays_through_real_browser(self):
        with local_fixture_server('kgg_ui_lab_navigation_fixture.html') as url, tempfile.TemporaryDirectory() as directory:
            browser = server._load_real_browser_module()
            runtime = server.Runtime(browser_bootstrap=browser.BrowserBootstrap.from_environment(), flow_store_path=Path(directory) / 'flows.json')
            definition = flow(fingerprint='navigation-fixture-v1')
            definition['steps'] = [
                {'sequence': 1, 'operation': 'back', 'label': 'back'},
                {'sequence': 2, 'operation': 'reload', 'label': 'reload'},
                {'sequence': 3, 'operation': 'read_state', 'label': 'navigation-entry', 'expected_state': 'navigation-entry'},
                {'sequence': 4, 'operation': 'capture_screenshot', 'label': 'navigation-proof'},
            ]
            definition['toggle_states'] = {'before': {}, 'after': {}}
            definition['expected_states'] = {'intermediate': ['navigation-second'], 'final': 'navigation-entry'}
            runtime.save_flow({'flow': definition})
            sid = 'navigation-persisted-session'
            rid = sid + '-run'
            self.call(runtime, 'start_ui_session', {'session': _session(url + '?history=1', session_id=sid, request_id=rid, capabilities=['browser', 'capture', 'quick_flows'], device_profile='custom')})
            result = self.call(runtime, 'run_flow', {
                'request': _visual_request(session_id=sid, request_id=rid, operation='run_flow'),
                'flow_id': definition['flow_id'], 'project': definition['project'], 'scope': 'project',
                'version': '1.0.0', 'binding_fingerprint': 'navigation-fixture-v1', 'toggle_states': {'before': {}},
            })
            self.assertFalse(result.get('isError'), result)
            content = result['structuredContent']
            self.assertEqual(content['result']['status'], 'PASS', content['result'])
            self.assertEqual(content['result']['final_state'], 'navigation-entry')
            self.assertEqual(content['evidence']['surface'], 'real_browser')
            self.assertEqual([step['actual'] for step in content['result']['steps'][:2]], ['back completed', 'reload completed'])


if __name__ == '__main__':
    unittest.main()
