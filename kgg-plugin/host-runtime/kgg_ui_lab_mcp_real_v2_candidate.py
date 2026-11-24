"""Stable KGG UI Lab host launcher: version selection is local, not a ChatGPT plugin update."""
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import re
import runpy
import sys

RUNTIME_ROOT = Path(r'C:\src\kgg-runtime\ui-lab')
ACTIVE_FILE = RUNTIME_ROOT / 'current.json'
SCHEMA = 'kgg-ui-lab/active-runtime/v1'
APPROVED_TOOL_CONTRACT_SHA256 = frozenset(('0cc291eface08da646164bc0785b78f1800f6b201255ad0cf3d581c13973f071', '4ca861d8504daed6d2f1698306f97dab3dbe2bea0506fc39ef1eae0c816d685d'))
PREVIEW_TOOL_CONTRACT_SHA256 = '4ca861d8504daed6d2f1698306f97dab3dbe2bea0506fc39ef1eae0c816d685d'
BASE_WORKFLOW_OPERATIONS = 'submitKggReadOnlyValidation,submitKggAdminEditorSyncPreflight,submitKggPreviewAuto'
PREVIEW_WORKFLOW_OPERATIONS = BASE_WORKFLOW_OPERATIONS + ',submitKggVerifiedPatientPrPreview'
KEYS = frozenset(('schema', 'release', 'server_sha256', 'server_version', 'tool_contract_sha256'))

def select_server(config_path=ACTIVE_FILE):
    root = RUNTIME_ROOT.resolve(strict=True)
    raw = Path(config_path).read_bytes()
    if not raw or len(raw) > 4096:
        raise RuntimeError('invalid_runtime_manifest')
    data = json.loads(raw)
    if not isinstance(data, dict) or set(data) != KEYS or data['schema'] != SCHEMA:
        raise RuntimeError('invalid_runtime_manifest')
    release = data['release']
    if not isinstance(release, str) or release in ('.', '..') or not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9._-]{0,79}', release):
        raise RuntimeError('invalid_runtime_release')
    for key in ('server_sha256', 'tool_contract_sha256'):
        if not isinstance(data[key], str) or not re.fullmatch(r'[a-f0-9]{64}', data[key]):
            raise RuntimeError('invalid_runtime_hash')
    if not isinstance(data['server_version'], str) or not re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+', data['server_version']):
        raise RuntimeError('invalid_runtime_version')
    server = (root / release / 'mcp' / 'server.py').resolve(strict=True)
    if not server.is_relative_to(root) or not server.is_file():
        raise RuntimeError('invalid_runtime_path')
    if hashlib.sha256(server.read_bytes()).hexdigest() != data['server_sha256']:
        raise RuntimeError('runtime_source_changed')
    # A fixed tool contract is a prerequisite for switching server versions without
    # updating the installed ChatGPT plugin. Never silently accept a schema change.
    with contextlib.redirect_stdout(io.StringIO()) as output:
        namespace = runpy.run_path(str(server), run_name='kgg_ui_lab_contract_preflight')
        tools = namespace['tool_catalog']()
    if output.getvalue():
        raise RuntimeError('unexpected_runtime_output')
    digest = hashlib.sha256(json.dumps(tools, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf8')).hexdigest()
    if (digest != data['tool_contract_sha256'] or digest not in APPROVED_TOOL_CONTRACT_SHA256
            or namespace['SERVER_VERSION'] != data['server_version']):
        raise RuntimeError('runtime_contract_mismatch')
    if digest == PREVIEW_TOOL_CONTRACT_SHA256 and namespace['SERVER_VERSION'] != '1.5.0':
        raise RuntimeError('new_contract_requires_version_1_5_0')
    return server, digest

def workflow_operations(contract: str) -> str:
    if contract not in APPROVED_TOOL_CONTRACT_SHA256:
        raise RuntimeError('runtime_contract_mismatch')
    return PREVIEW_WORKFLOW_OPERATIONS if contract == PREVIEW_TOOL_CONTRACT_SHA256 else BASE_WORKFLOW_OPERATIONS


def main():
    # MCP stdio is UTF-8, including when Windows pipes default to CP1252.
    sys.stdin.reconfigure(encoding='utf-8')
    sys.stdout.reconfigure(encoding='utf-8')
    os.environ['KGG_REAL_BROWSER'] = '1'
    os.environ['KGG_GITHUB_READS'] = '1'
    server, contract = select_server()
    # Never enable a new operation while booting the old verified runtime.
    os.environ['KGG_GITHUB_WORKFLOW_OPERATIONS'] = workflow_operations(contract)
    # The runtime pointer is updated atomically by the trusted host, not by
    # model-supplied tool inputs. A failed validation stops before boot.
    runpy.run_path(str(server), run_name='__main__')

if __name__ == '__main__':
    main()
