#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
NATIVE_HOST = ROOT / 'kgg-plugin' / 'browser-route' / 'native_host.py'
PROJECT_STATUS = ROOT / 'kgg-plugin' / 'mcp' / 'project_status.py'

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

native_host = load_module('kgg_browser_route_native_host', NATIVE_HOST)
project_status = load_module('kgg_browser_route_project_status', PROJECT_STATUS)
class BrowserRouteCheckpointE2E(unittest.TestCase):
    def test_verified_native_state_becomes_verified_route_without_session_ref(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / 'route.json'
            payload = {
                'schema': 'kgg-chatgpt-browser-route/v1',
                'state': 'verified',
                'canonical_url': 'https://chatgpt.com/c/e2e-route',
                'observed_at': int(time.time() * 1000),
            }
            native_host.handle_raw(json.dumps(payload).encode(), state_path)
            old = os.environ.get('KGG_CHATGPT_ROUTE_STATE')
            os.environ['KGG_CHATGPT_ROUTE_STATE'] = str(state_path)
            try:
                result = project_status.build_checkpoint_intent(
                    {
                        'project_id': 'project-status-widget',
                        'project_name': 'Project Status Widget',
                        'state': 'running',
                        'step': 'Browser route e2e',
                    },
                    session_ref='opaque-should-not-persist',
                )
            finally:
                if old is None: os.environ.pop('KGG_CHATGPT_ROUTE_STATE', None)
                else: os.environ['KGG_CHATGPT_ROUTE_STATE'] = old
            route = result['chatgpt_route']
            self.assertTrue(route['publish'])
            self.assertEqual(route['route_state'], 'verified')
            self.assertIn('open_url: https://chatgpt.com/c/e2e-route', route['body'])
            self.assertNotIn('session_ref:', route['body'])

    def test_unavailable_native_state_falls_back_to_correlation_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / 'route.json'
            payload = {
                'schema': 'kgg-chatgpt-browser-route/v1',
                'state': 'unavailable',
                'canonical_url': None,
                'observed_at': int(time.time() * 1000),
            }
            native_host.handle_raw(json.dumps(payload).encode(), state_path)
            old = os.environ.get('KGG_CHATGPT_ROUTE_STATE')
            os.environ['KGG_CHATGPT_ROUTE_STATE'] = str(state_path)
            try:
                result = project_status.build_checkpoint_intent(
                    {
                        'project_id': 'project-status-widget',
                        'project_name': 'Project Status Widget',
                        'state': 'running',
                        'step': 'Browser route unavailable',
                    },
                    session_ref='fallback-session',
                )
            finally:
                if old is None: os.environ.pop('KGG_CHATGPT_ROUTE_STATE', None)
                else: os.environ['KGG_CHATGPT_ROUTE_STATE'] = old
            self.assertEqual(result['chatgpt_route']['route_state'], 'correlation_only')
            self.assertIn('session_ref: fallback-session', result['chatgpt_route']['body'])

if __name__ == '__main__':
    unittest.main()
