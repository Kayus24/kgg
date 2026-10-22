"""Device-first cockpit checks, complete battery, then unchanged replay.

Only synthetic fixtures are used. Browser interactions never force hit testing.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--device-only', action='store_true', help='Diagnostic subset; not a complete acceptance run')
    args = parser.parse_args()
    node = os.environ.get('KGG_NODE') or shutil.which('node')
    if not node:
        parser.error('Node is required')
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    folder = ROOT / 'tmp/cockpit-layout-loop' / run_id
    folder.mkdir(parents=True, exist_ok=False)
    output = ROOT / 'kgg-update/index.html'
    fingerprint = lambda: hashlib.sha256(output.read_bytes()).hexdigest()
    initial_hash = fingerprint()
    device_checks = [
        ('device', 'kgg_cockpit_device_canaries.js'),
        ('main-phone', 'kgg_cockpit_main_phone_flow.js'),
        ('readability', 'kgg_cockpit_narrow_readability.js'),
        ('phone-values', 'kgg_cockpit_phone_value_grid.js'),
        ('seam', 'kgg_cockpit_seam_gesture.js'),
        ('reorder', 'kgg_cockpit_reorder_parity.js'),
        ('reported', 'kgg_cockpit_reported_scenarios.js'),
    ]
    steps = [(name + '-first', [node, 'release-pipeline/' + script])
             for name, script in device_checks]
    if not args.device_only:
        steps.extend([
            ('full-regression', [sys.executable, 'release-pipeline/kgg_selftest_build.py', '--certify']),
            ('live-edit-replay', [node, 'release-pipeline/kgg_therapy_cockpit_live_edit_smoke.js']),
        ])
    steps.extend((name + '-unchanged-replay', [node, 'release-pipeline/' + script])
                 for name, script in device_checks)
    report = {'schema': 1, 'runId': run_id, 'sha256': initial_hash,
              'scope': 'device-only' if args.device_only else 'complete', 'steps': [], 'status': 'RUNNING'}
    report_path = folder / 'report.json'
    for name, command in steps:
        env = os.environ.copy()
        env['PYTHONIOENCODING'] = 'utf-8'
        env['KGG_SMOKE_SCREENSHOT_DIR'] = str(folder / name)
        env['KGG_ALLOW_RELEASE_DRIFT'] = '1'
        log = folder / (name + '.log')
        print(f'{name}: starting; {log}', flush=True)
        with log.open('w', encoding='utf-8') as stream:
            result = subprocess.run(command, cwd=ROOT, env=env, stdout=stream, stderr=subprocess.STDOUT)
        same = fingerprint() == initial_hash
        status = 'PASS' if result.returncode == 0 and same else 'FAIL'
        report['steps'].append({'name': name, 'status': status, 'exitCode': result.returncode,
                                'unchangedHtml': same, 'log': str(log)})
        report['status'] = 'FAIL' if status == 'FAIL' else 'RUNNING'
        report_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        print(f'{name}: {status}', flush=True)
        if status == 'FAIL':
            print(f'Stopped at the first failure. Evidence: {report_path}', flush=True)
            return 1
    report['status'] = 'PASS'
    report_path.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(f'PASS ({report["scope"]}); evidence: {report_path}', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
