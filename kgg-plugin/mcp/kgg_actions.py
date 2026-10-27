"""Fixed KGG Action routes over the existing GitHub CLI keyring login.

Reads and explicitly host-enabled workflow dispatches have separate entrypoints.
There is no caller-selected command, host, repository, method or credential.
"""
from copy import deepcopy
import json
import hashlib
from pathlib import Path
import re
import shutil
import subprocess
from threading import Lock
from urllib.parse import urlencode


MAX_WORKFLOW_BODY_BYTES = 256_000
MAX_PAYLOAD_JSON_BYTES = 120_000
MAX_TRACKED_DISPATCHES = 256
PROTECTED_WORKFLOWS = frozenset({"submitKggMainGate", "submitKggAdminEditorSyncSnapshotPr"})
MEMORY_WORKFLOW = "submitKggMemoryUpdate"


class ActionError(ValueError):
    pass


def _catalog_actions():
    try:
        catalog = json.loads(Path(__file__).with_name('kgg_action_routes.json').read_text(encoding='utf-8'))
        return {action['operation']: action for action in catalog['actions']}
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise ActionError('kgg_action_catalog_invalid') from exc


def _validate_workflow_schema(value, schema):
    if schema.get('type') == 'object':
        if not isinstance(value, dict):
            raise ActionError('workflow_payload_invalid')
        fields = schema.get('properties', {})
        if set(value) - set(fields) or not set(schema.get('required', ())).issubset(value):
            raise ActionError('workflow_payload_invalid')
        for name, child in value.items():
            _validate_workflow_schema(child, fields[name])
    elif schema.get('type') == 'string':
        if not isinstance(value, str) or len(value) > schema.get('maxLength', MAX_PAYLOAD_JSON_BYTES):
            raise ActionError('workflow_payload_invalid')
        if 'enum' in schema and value not in schema['enum']:
            raise ActionError('workflow_payload_invalid')
        if 'pattern' in schema and not re.fullmatch(schema['pattern'], value):
            raise ActionError('workflow_payload_invalid')
    else:
        raise ActionError('workflow_schema_unsupported')


def _unique_json_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ActionError('workflow_payload_invalid')
        result[key] = value
    return result


def _invalid_json_constant(_value):
    raise ActionError('workflow_payload_invalid')


def _check_json_tree(value, *, memory=False, depth=0):
    if depth > 20:
        raise ActionError('workflow_payload_invalid')
    if isinstance(value, dict):
        for key, child in value.items():
            if memory and key.casefold() in {'supersedes', 'approved_by', 'approval_quote'} and child:
                # Model-supplied names and quotations are never human consent.
                raise ActionError('external_gate_required')
            _check_json_tree(child, memory=memory, depth=depth + 1)
    elif isinstance(value, list):
        for child in value:
            _check_json_tree(child, memory=memory, depth=depth + 1)


def _workflow_body(action, payload):
    if action['operation'] in PROTECTED_WORKFLOWS:
        raise ActionError('external_gate_required')
    schema = action.get('request_schema')
    if not isinstance(schema, dict):
        raise ActionError('workflow_schema_missing')
    _validate_workflow_schema(payload, schema)
    if payload.get('ref') != 'main':
        raise ActionError('workflow_payload_invalid')
    inputs = payload['inputs']
    if action['operation'] == MEMORY_WORKFLOW and inputs.get('mode') != 'validate_only':
        raise ActionError('external_gate_required')
    if 'payload_json' in inputs:
        raw = inputs['payload_json']
        byte_limit = 60_000 if action['operation'] == 'submitKggPatientPreviewFromAdmin' else MAX_PAYLOAD_JSON_BYTES
        try:
            if len(raw.encode('utf-8')) > byte_limit:
                raise ActionError('workflow_payload_invalid')
            document = json.loads(raw, object_pairs_hook=_unique_json_object, parse_constant=_invalid_json_constant)
            if not isinstance(document, dict) or document.get('request_id') != inputs['request_id']:
                raise ActionError('workflow_payload_invalid')
            _check_json_tree(document, memory=action['operation'] == MEMORY_WORKFLOW)
        except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
            raise ActionError('workflow_payload_invalid') from exc
    try:
        encoded = json.dumps(payload, sort_keys=True, ensure_ascii=True, allow_nan=False, separators=(',', ':'))
        if len(encoded.encode('utf-8')) > MAX_WORKFLOW_BODY_BYTES:
            raise ActionError('workflow_payload_invalid')
    except (TypeError, ValueError, UnicodeError) as exc:
        if isinstance(exc, ActionError):
            raise
        raise ActionError('workflow_payload_invalid') from exc
    return deepcopy(payload), encoded


def github_dispatch(route, payload):
    """One fixed-route POST; an accepted dispatch is never a workflow PASS."""
    action = next((a for a in _catalog_actions().values() if a['method'] == 'POST' and a['path'] == route), None)
    if action is None:
        raise ActionError('workflow_route_invalid')
    _body, encoded = _workflow_body(action, payload)
    executable = shutil.which('gh')
    if not executable:
        raise ActionError('kgg_github_cli_unavailable')
    try:
        result = subprocess.run(
            [executable, 'api', '--hostname', 'github.com', '--method', 'POST',
             '--header', 'Accept: application/vnd.github+json', '--include', '--input', '-', route],
            input=encoded, capture_output=True, text=True, encoding='utf-8', errors='replace',
            timeout=30, check=False, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ActionError('dispatch_unknown') from exc
    if not isinstance(result.stdout, str) or len(result.stdout.encode('utf-8')) > 64_000:
        raise ActionError('dispatch_unknown')
    matched = re.match(r'^HTTP/\S+\s+([0-9]{3})(?:\s|$)', result.stdout)
    status = int(matched[1]) if matched else None
    if result.returncode == 0 and status == 204:
        return {'status': 'dispatch_accepted', 'http_status': 204}
    if status is not None and 400 <= status < 500:
        raise ActionError('dispatch_rejected')
    raise ActionError('dispatch_unknown')


def github_read(route, accept):
    executable = shutil.which('gh')
    if not executable:
        raise ActionError('kgg_github_cli_unavailable')
    try:
        result = subprocess.run([executable, 'api', '--hostname', 'github.com', '--method', 'GET', '--header', 'Accept: ' + accept, route], capture_output=True, timeout=30, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ActionError('kgg_github_read_failed') from exc
    if result.returncode:
        raise ActionError('kgg_github_read_failed')
    if len(result.stdout) > 2 * 1024 * 1024:
        raise ActionError('kgg_github_response_too_large')
    try:
        text = result.stdout.decode('utf-8')
        return text if accept == 'application/vnd.github.raw+json' and route.split('?')[0].endswith(('.md', '.yaml')) else json.loads(text)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ActionError('kgg_github_response_invalid') from exc


class KggActions:
    """Callable adapter compatible with KggCompatibilityShim.action_adapter."""
    def __init__(self, *, transport=None, dispatch_transport=None, allowed_workflow_operations=()):
        self.transport = transport or github_read
        self.actions = _catalog_actions()
        if not isinstance(allowed_workflow_operations, (tuple, list, set, frozenset)) or any(
            not isinstance(name, str) or name not in self.actions or self.actions[name]['method'] != 'POST'
            for name in allowed_workflow_operations
        ):
            raise ActionError('workflow_allowlist_invalid')
        self.allowed_workflow_operations = frozenset(allowed_workflow_operations)
        self.dispatch_transport = dispatch_transport or github_dispatch
        self._dispatches = {}
        self._dispatch_lock = Lock()

    def capabilities(self):
        return {'schema': 'kgg-ui-lab/kgg-action-capabilities/v1', 'surface': 'GITHUB_KEYRING', 'actions': [
            {'operation': action['operation'], 'method': action['method'], 'consequential': action['consequential'], 'status': 'BOUND_READ' if action['method'] == 'GET' else 'EXTERNAL_GATE_REQUIRED'}
            for action in self.actions.values()]}

    def __call__(self, operation, payload):
        result = self.run(operation, payload)
        return result if isinstance(result, dict) else {'content': result}

    def workflow_capabilities(self):
        """Host authorization and actual acceptance limits, without a human-proof claim."""
        prerequisites = {
            'submitKggReadOnlyValidation': ['exact_current_main_source_sha', 'allowlisted_validation_profile'],
            'submitKggPreviewAuto': ['live_synced_admin_editor', 'guarded_payload', 'identical_validate_then_preview'],
            'submitKggDeviceTest': ['separate_host_device_test_authorization', 'exact_current_main_source_sha', 'authorized_physical_devices'],
            'submitKggAdminEditorSyncPreflight': ['separate_host_editor_attestation', 'published_editor_checked', 'TARGET_PASS'],
            'submitKggPatientPreviewFromAdmin': ['synthetic_only_guarded_payload', 'both_editors_live_synced_before_publish'],
            'submitKggAgentCoordinationEvent': ['non_sensitive_v1_event', 'validate_then_identical_apply'],
            MEMORY_WORKFLOW: ['validate_only', 'no_model_approval_metadata', 'apply_requires_external_validated_payload_binding'],
        }
        actions = []
        for operation, action in self.actions.items():
            if action['method'] != 'POST':
                continue
            protected = operation in PROTECTED_WORKFLOWS
            enabled = operation in self.allowed_workflow_operations and not protected
            modes = action['request_schema']['properties']['inputs']['properties'].get('mode', {}).get('enum', [])
            actions.append({
                'operation': operation, 'method': 'POST', 'consequential': action['consequential'],
                'status': 'EXTERNAL_GATE_REQUIRED' if protected else ('AVAILABLE' if enabled else 'HOST_DISABLED'),
                'allowed_modes': ([] if protected else (['validate_only'] if operation == MEMORY_WORKFLOW else list(modes))) if enabled else [],
                'external_gate_modes': ['apply'] if operation == MEMORY_WORKFLOW else (list(modes) if protected else []),
                'prerequisites': prerequisites.get(operation, ['verified_external_human_authorization']),
            })
        return {
            'schema': 'kgg-ui-lab/kgg-workflow-capabilities/v1', 'actions': actions,
            'automatic_retry': False, 'human_approval_verified': False,
            'dispatch_result': 'dispatch_accepted_only', 'workflow_acceptance': 'reconcile_exact_request_source_and_result_artifact',
            'deduplication_scope': 'per_phase_with_immutable_request_payload; process_lifetime; reconcile durable GitHub state after restart',
            'limits': {'body_bytes': MAX_WORKFLOW_BODY_BYTES, 'payload_json_bytes': MAX_PAYLOAD_JSON_BYTES,
                       'patient_payload_json_bytes': 60_000, 'json_depth': 20,
                       'tracked_requests_per_process': MAX_TRACKED_DISPATCHES, 'transport_timeout_seconds': 30},
        }

    def dispatch(self, operation, payload):
        """Dispatch each explicit phase once, keeping the request's other inputs immutable."""
        action = self.actions.get(operation) if isinstance(operation, str) else None
        if action is None or action['method'] != 'POST':
            raise ActionError('workflow_operation_invalid')
        if operation in PROTECTED_WORKFLOWS:
            raise ActionError('external_gate_required')
        checked, encoded = _workflow_body(action, payload)
        if operation not in self.allowed_workflow_operations:
            raise ActionError('workflow_host_disabled')
        request_id = checked['inputs']['request_id']
        digest = hashlib.sha256(encoded.encode('utf-8')).hexdigest()
        phase = checked['inputs'].get('mode')
        bound_body = deepcopy(checked)
        bound_body['inputs'].pop('mode', None)
        bound_encoded = json.dumps(bound_body, sort_keys=True, ensure_ascii=True, allow_nan=False, separators=(',', ':'))
        bound_digest = hashlib.sha256(bound_encoded.encode('utf-8')).hexdigest()
        key = (operation, request_id)
        with self._dispatch_lock:
            prior = self._dispatches.get(key)
            if prior is not None:
                if prior['digest'] != bound_digest:
                    raise ActionError('workflow_request_reused')
            else:
                if len(self._dispatches) >= MAX_TRACKED_DISPATCHES:
                    raise ActionError('workflow_history_full_reconcile_required')
                prior = {'digest': bound_digest, 'phases': {}}
                self._dispatches[key] = prior
            phases = prior['phases']
            existing = phases.get(phase)
            if existing is not None:
                if 'result' in existing:
                    return deepcopy(existing['result'])
                raise ActionError(existing['error'])
            if any('result' not in item and item['error'] == 'dispatch_unknown' for item in phases.values()):
                # A different phase must not hide an unresolved/in-flight POST.
                raise ActionError('dispatch_unknown')
            entry = {'digest': digest, 'error': 'dispatch_unknown'}
            phases[phase] = entry
        try:
            accepted = self.dispatch_transport(action['path'], checked)
            if not isinstance(accepted, dict) or accepted.get('status') != 'dispatch_accepted' or type(accepted.get('http_status')) is not int or accepted['http_status'] != 204:
                raise ActionError('dispatch_unknown')
        except Exception as exc:
            code = str(exc) if isinstance(exc, ActionError) and str(exc) in {'dispatch_rejected', 'kgg_github_cli_unavailable', 'external_gate_required'} else 'dispatch_unknown'
            with self._dispatch_lock:
                entry['error'] = code
            raise ActionError(code) from None
        result = {
            'operation': operation, 'status': 'dispatch_accepted', 'http_status': 204,
            'request_id': request_id, 'payload_sha256': digest,
            'reconciliation_required': True, 'workflow_result': 'NOT_OBSERVED',
        }
        if 'source_sha' in checked['inputs']:
            result['source_sha'] = checked['inputs']['source_sha']
        with self._dispatch_lock:
            entry['result'] = result
        return deepcopy(result)

    def ticket(self, ticket_id):
        if not isinstance(ticket_id, str) or not re.fullmatch(r'#?[0-9]{1,6}', ticket_id) or int(ticket_id.lstrip('#')) < 1:
            raise ActionError('ticket_id_invalid')
        issue = self.transport('/repos/Kayus24/kgg/issues/' + str(int(ticket_id.lstrip('#'))), 'application/vnd.github+json')
        if not isinstance(issue, dict) or issue.get('number') != int(ticket_id.lstrip('#')) or 'pull_request' in issue:
            raise ActionError('ticket_state_invalid')
        return {'ticket_id': ticket_id, 'status': issue.get('state'), 'title': issue.get('title'), 'updated_at': issue.get('updated_at'), 'source': 'github_issue', 'url': issue.get('html_url')}

    def resource(self, name):
        resources = {'resource-manifest': 'docs/kgg-custom-gpt-resource-manifest.json', 'source-version': 'kgg-update/version.json'}
        for profile, prefix in [('admin', 'kgg-custom-gpt'), ('patient', 'kgg-patient-custom-gpt')]:
            resources[profile + '-bootstrap'] = 'docs/' + prefix + '-editor-bootstrap.md'
            for topic in ['architecture', 'operations', 'safety', 'testing']:
                resources[profile + '-' + topic] = 'docs/' + prefix + '-knowledge-' + topic + '.md'
        if name not in resources:
            raise ActionError('kgg_resource_invalid')
        path = resources[name]
        content = self.transport('/repos/Kayus24/kgg/contents/' + path + '?ref=main', 'application/vnd.github.raw+json')
        raw = content if isinstance(content, str) else json.dumps(content, sort_keys=True, separators=(',', ':'))
        return {'resource': name, 'path': path, 'ref': 'main', 'content': content, 'content_sha256': hashlib.sha256(raw.encode('utf-8')).hexdigest(), 'hash_scope': 'returned_content', 'source': 'github_live'}

    def run(self, operation, payload):
        if not isinstance(operation, str) or operation not in self.actions:
            raise ActionError('kgg_action_operation_invalid')
        action = self.actions[operation]
        if action['method'] != 'GET':
            raise ActionError('external_gate_required')
        if not isinstance(payload, dict):
            raise ActionError('kgg_action_payload_invalid')
        parameters = {parameter['name']: parameter for parameter in action['parameters']}
        if set(payload) - set(parameters):
            raise ActionError('kgg_action_payload_invalid')
        route = action['path']
        query = {}
        accept = 'application/vnd.github+json'
        for name, parameter in parameters.items():
            schema = parameter['schema']
            value = payload.get(name, schema.get('default'))
            if value is None:
                if parameter.get('required'):
                    raise ActionError('kgg_action_parameter_missing')
                continue
            if schema.get('type') == 'integer':
                if type(value) is not int or value < schema.get('minimum', 1) or value > schema.get('maximum', 2**63-1):
                    raise ActionError('kgg_action_parameter_invalid')
            elif not isinstance(value, str) or len(value) > 128:
                raise ActionError('kgg_action_parameter_invalid')
            if 'enum' in schema and value not in schema['enum']:
                raise ActionError('kgg_action_parameter_invalid')
            if 'pattern' in schema and not re.fullmatch(schema['pattern'], str(value)):
                raise ActionError('kgg_action_parameter_invalid')
            if parameter['in'] == 'path':
                if not re.fullmatch(r'[a-z0-9][a-z0-9.-]{0,127}', str(value)) or '..' in str(value):
                    raise ActionError('kgg_action_parameter_invalid')
                route = route.replace('{' + name + '}', str(value))
            elif parameter['in'] == 'query':
                query[name] = value
            elif parameter['in'] == 'header':
                if name != 'Accept' or value != 'application/vnd.github.raw+json':
                    raise ActionError('kgg_action_parameter_invalid')
                accept = value
        if '{' in route or not route.startswith(('/repos/Kayus24/kgg/', '/repos/Kayus24/kgg-project-memory/')):
            raise ActionError('kgg_action_route_invalid')
        if query:
            route += '?' + urlencode(query)
        return deepcopy(self.transport(route, accept))
