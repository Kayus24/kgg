#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
import json
import re
import sys

HTML_PATH = Path('kgg-update/index.html')
VERSION_PATH = Path('kgg-update/version.json')
RELEASE_PATH = Path('update-inbox/release.json')

PATCH_ID = 'kgg-v024-rollback-v023-debug-breakage'
VERSION_NAME = '1.0.24-rollback-v023-debug-breakage'
STYLE_ID = PATCH_ID + '-guard-style'

REMOVE_IDS = [
    'kgg-v023-admin-debug-visible-hotfix-style',
    'kgg-v023-admin-debug-visible-hotfix-script',
    'kgg-v022-admin-debug-menu-feedback-style',
    'kgg-v022-admin-debug-menu-feedback-script',
]

PROTECTED = [
    'PDF',
    'QR-Erzeugung',
    'Patienten-App',
    'Scan-Kamera',
    'Parser',
    'Android-Wrapper',
    'Tablet-Core-Layout',
    'Plan-State',
    'Storage',
]

ROLLBACK_CSS = r'''
/* KGG PATCH START: kgg-v024-rollback-v023-debug-breakage-guard-style */
#kggAdminDebugFab,
#kggAdminDebugBtn,
#kggAdminHubBtn,
.kggAdminDebugBtn,
.kggAdminHubBtn,
#kggDebugPanelOverlay,
.kggDebugPanelOverlay,
.kggDebugToast{
  display:none!important;
  visibility:hidden!important;
  opacity:0!important;
  pointer-events:none!important;
}
/* KGG PATCH END: kgg-v024-rollback-v023-debug-breakage-guard-style */
'''.strip()


def fail(msg: str) -> None:
    print('ERROR:', msg)
    sys.exit(1)


def read_json(path: Path, fallback: dict) -> dict:
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
        return data if isinstance(data, dict) else fallback
    except Exception:
        return fallback


def comment_spans(html: str):
    return [(m.start(), m.end()) for m in re.finditer(r'<!--.*?-->', html, re.S)]


def in_spans(pos: int, spans) -> bool:
    return any(start <= pos < end for start, end in spans)


def remove_active_tag_by_id(html: str, tag_id: str) -> str:
    spans = comment_spans(html)
    pattern = re.compile(
        r'<(?P<tag>style|script)\b(?=[^>]*\bid=["\']' + re.escape(tag_id) + r'["\'])[^>]*>.*?</(?P=tag)>\s*',
        re.I | re.S,
    )
    out = []
    last = 0
    removed = 0
    for match in pattern.finditer(html):
        if in_spans(match.start(), spans):
            continue
        out.append(html[last:match.start()])
        last = match.end()
        removed += 1
    if removed:
        out.append(html[last:])
        html = ''.join(out)
        print('Removed tag id:', tag_id, 'count:', removed)
    return html


def first_active_match(html: str, pattern: re.Pattern):
    spans = comment_spans(html)
    for match in pattern.finditer(html):
        if not in_spans(match.start(), spans):
            return match
    return None


def upsert_style(html: str, tag_id: str, css: str) -> str:
    block = '<style id="' + tag_id + '">\n' + css + '\n</style>'
    pattern = re.compile(r'<style\b(?=[^>]*\bid=["\']' + re.escape(tag_id) + r'["\'])[^>]*>.*?</style>\s*', re.I | re.S)
    match = first_active_match(html, pattern)
    if match:
        return html[:match.start()] + block + '\n' + html[match.end():]
    idx = html.lower().rfind('</head>')
    return html[:idx] + block + '\n' + html[idx:] if idx >= 0 else html + '\n' + block + '\n'


def json_pat(script_id: str) -> re.Pattern:
    return re.compile(
        r'<script\b(?=[^>]*\bid=["\']' + re.escape(script_id) + r'["\'])'
        r'(?=[^>]*\btype=["\']application/json["\'])[^>]*>\s*(.*?)\s*</script>',
        re.I | re.S,
    )


def load_active_json(html: str, script_id: str, fallback: dict) -> dict:
    match = first_active_match(html, json_pat(script_id))
    if not match:
        return fallback
    try:
        data = json.loads(match.group(1).strip())
        return data if isinstance(data, dict) else fallback
    except Exception:
        return fallback


def replace_active_json(html: str, script_id: str, data: dict, anchor: str | None = None) -> str:
    block = '<script type="application/json" id="' + script_id + '">\n' + json.dumps(data, ensure_ascii=False, indent=2) + '\n</script>'
    pattern = json_pat(script_id)
    match = first_active_match(html, pattern)
    if match:
        return html[:match.start()] + block + html[match.end():]
    if anchor and anchor in html:
        idx = html.find(anchor) + len(anchor)
        return html[:idx] + '\n' + block + html[idx:]
    idx = html.lower().find('</head>')
    return html[:idx] + block + '\n' + html[idx:] if idx >= 0 else html + '\n' + block + '\n'


def next_code(manifest: dict, version_name: str) -> int:
    try:
        cur = int(manifest.get('versionCode', 0))
    except Exception:
        cur = 0
    return cur if manifest.get('versionName') == version_name else cur + 1


def update_meta(html: str, release: dict, manifest: dict) -> str:
    version_name = release.get('versionName') or VERSION_NAME
    code = next_code(manifest, version_name)

    source = load_active_json(html, 'kgg-source-truth', {'schema': 1, 'app': 'KGG Plan', 'activeFixes': []})
    current = source.get('currentVersion') if isinstance(source.get('currentVersion'), dict) else {}
    current.update({
        'versionCode': code,
        'versionName': version_name,
        'lastPatchId': PATCH_ID,
        'updatedBy': 'update-inbox',
    })
    source['currentVersion'] = current
    source['latestPatchId'] = PATCH_ID
    fixes = source.get('activeFixes') if isinstance(source.get('activeFixes'), list) else []
    fixes = [x for x in fixes if x not in ('admin-debug-visible-hotfix', 'admin-debug-menu-feedback')]
    if 'rollback-v023-debug-breakage' not in fixes:
        fixes.append('rollback-v023-debug-breakage')
    source['activeFixes'] = fixes
    source['lastUpdateIntent'] = {
        'id': PATCH_ID,
        'summary': 'Emergency rollback: remove v023/v022 admin debug UI because it broke tablet layout.',
        'touched': ['Admin debug UI rollback', 'HTML embedded metadata', 'Source Truth', 'Changelog', 'Patch rules'],
        'notTouched': PROTECTED,
    }
    html = replace_active_json(html, 'kgg-source-truth', source, '<!-- END kgg-source-truth -->')

    changelog = load_active_json(html, 'kgg-changelog', {'schema': 1, 'entries': []})
    entries = changelog.get('entries') if isinstance(changelog.get('entries'), list) else []
    entries = [entry for entry in entries if not (isinstance(entry, dict) and entry.get('patchId') == PATCH_ID)]
    entries.insert(0, {
        'versionCode': code,
        'versionName': version_name,
        'patchId': PATCH_ID,
        'status': 'active',
        'type': 'github-web-update',
        'title': 'Rollback v023 Debug-Layout-Bruch',
        'reason': 'v023 machte den Debug-Floating-Button sichtbar, brach aber erneut das Tablet-Layout und zeigte doppelte Debug-Einstiege.',
        'whatChanged': [
            'Removes active v023 debug style/script block.',
            'Removes active v022 debug style/script block if still present.',
            'Adds a small rollback guard that hides leftover debug buttons/overlays.',
            'Leaves the workflow indexUrl fix in place.',
            'Does not change PDF, QR generation, patient app, scan camera, parser, plan state or storage.',
        ],
        'touchedAreas': ['Admin debug UI rollback', 'HTML embedded metadata', 'Source Truth', 'Changelog', 'Patch rules'],
        'notTouched': PROTECTED,
        'testStatus': {
            'tabletLayoutRestored': 'pending',
            'debugButtonsHidden': 'pending',
            'versionIndexUrl': 'pending',
        },
        'createdAt': datetime.now(timezone.utc).isoformat(),
    })
    changelog['schema'] = changelog.get('schema', 1)
    changelog['latestVersionCode'] = code
    changelog['latestVersionName'] = version_name
    changelog['entries'] = entries
    html = replace_active_json(html, 'kgg-changelog', changelog, '<!-- END kgg-changelog -->')

    rules = load_active_json(html, 'kgg-patch-rules', {'schema': 1})
    rules['adminDebugRollbackPolicy'] = {
        'patchId': PATCH_ID,
        'reason': 'v023 broke tablet layout; debug UI must not be reintroduced without isolated viewport tests.',
        'blockedUntil': ['tablet screenshot proof', 'phone screenshot proof', 'no duplicate debug entry', 'Max approval'],
    }
    html = replace_active_json(html, 'kgg-patch-rules', rules, '<!-- END kgg-patch-rules -->')
    return html


def validate(html: str) -> None:
    active_html = re.sub(r'<!--.*?-->', '', html, flags=re.S)
    for removed_id in REMOVE_IDS:
        if removed_id in active_html:
            fail('rollback failed, active id still present: ' + removed_id)
    if STYLE_ID not in active_html:
        fail('rollback guard style missing')
    if PATCH_ID not in active_html:
        fail('patch id missing from active html')
    if 'id="kgg-source-truth"' not in active_html or 'id="kgg-changelog"' not in active_html:
        fail('source-truth/changelog missing')


def main() -> None:
    if not HTML_PATH.exists():
        fail(f'missing {HTML_PATH}')
    release = read_json(RELEASE_PATH, {'versionName': VERSION_NAME})
    manifest = read_json(VERSION_PATH, {})
    html = HTML_PATH.read_text(encoding='utf-8')
    idx = html.lower().find('<!doctype html')
    if idx < 0:
        fail('doctype missing')
    html = html[idx:]
    for tag_id in REMOVE_IDS:
        html = remove_active_tag_by_id(html, tag_id)
    html = upsert_style(html, STYLE_ID, ROLLBACK_CSS)
    html = update_meta(html, release, manifest)
    validate(html)
    HTML_PATH.write_text(html, encoding='utf-8', newline='\n')
    print('Applied', PATCH_ID)
    print('Expected versionName:', release.get('versionName') or VERSION_NAME)


if __name__ == '__main__':
    main()
