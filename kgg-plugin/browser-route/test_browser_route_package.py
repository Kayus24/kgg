from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parent


class BrowserRoutePackageTest(unittest.TestCase):
    def test_manifest_keeps_minimum_permissions(self):
        manifest = json.loads((ROOT / 'manifest.json').read_text('utf-8'))
        self.assertEqual(manifest['permissions'], ['nativeMessaging', 'alarms'])
        self.assertEqual(manifest['host_permissions'], ['https://chatgpt.com/*'])
        self.assertNotIn('content_scripts', manifest)
        serialized = json.dumps(manifest)
        for forbidden in ('tabs', 'scripting', 'cookies', 'history', 'debugger', 'storage', '<all_urls>'):
            self.assertNotIn(f'"{forbidden}"', serialized)

    def test_manifest_uses_module_service_worker(self):
        manifest = json.loads((ROOT / 'manifest.json').read_text('utf-8'))
        self.assertEqual(manifest['background']['service_worker'], 'service_worker.mjs')
        self.assertEqual(manifest['background']['type'], 'module')
    def test_native_host_template_pins_one_extension_origin(self):
        template = json.loads((ROOT / 'native_host_manifest.template.json').read_text('utf-8'))
        self.assertEqual(template['name'], 'com.kgg.project_status_route')
        self.assertEqual(template['type'], 'stdio')
        self.assertEqual(template['allowed_origins'], ['chrome-extension://__EXTENSION_ID__/'])

    def test_installer_is_user_scoped_and_id_pinned(self):
        script = (ROOT / 'install_native_host.ps1').read_text('utf-8')
        self.assertIn("ValidatePattern('^[a-p]{32}$')", script)
        self.assertIn("hpamfcbdlakklemljchpkfinmakjeada", script)
        self.assertIn("[switch]$PlanOnly", script)
        self.assertIn('HKCU:\\Software\\Google\\Chrome\\NativeMessagingHosts', script)
        self.assertIn('HKCU:\\Software\\Chromium\\NativeMessagingHosts', script)
        self.assertIn('allowed_origins = @("chrome-extension://$ExtensionId/")', script)
        self.assertNotIn('HKLM:', script)

    def test_manifest_key_pins_expected_extension_id(self):
        manifest = json.loads((ROOT / 'manifest.json').read_text('utf-8'))
        public_key = base64.b64decode(manifest['key'])
        digest = hashlib.sha256(public_key).digest()[:16]
        alphabet = 'abcdefghijklmnop'
        extension_id = ''.join(
            alphabet[byte >> 4] + alphabet[byte & 0x0F]
            for byte in digest
        )
        self.assertEqual(extension_id, 'hpamfcbdlakklemljchpkfinmakjeada')


if __name__ == '__main__':
    unittest.main()
