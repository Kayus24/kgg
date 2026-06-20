#!/usr/bin/env python3
from pathlib import Path
from datetime import datetime, timezone
import json
import re
import sys

HTML_PATH = Path("kgg-update/index.html")
VERSION_PATH = Path("kgg-update/version.json")

VERSION_NAME = "1.0.7-patch-retention-changelog-guard"
UPDATE_ID = "web-v009-patch-retention-changelog-guard"

SOURCE_TRUTH_ID = "kgg-source-truth"
CHANGELOG_ID = "kgg-changelog"
PATCH_RULES_ID = "kgg-patch-rules"
SIZE_GUARD_ID = "kgg-changelog-size-guard"

PROTECTED_AREAS = [
    "PDF",
    "QR-Erzeugung",
    "Patienten-App",
    "Scan-Kamera",
    "Parser",
    "Android-Wrapper",
    "Tablet-Layout",
    "Plan-State",
    "Storage",
]

CHANGELOG_WARN_AT_ENTRIES = 18
CHANGELOG_MAX_EMBEDDED_ENTRIES = 30
CHANGELOG_WARN_AT_BYTES = 35000
CHANGELOG_MAX_EMBEDDED_BYTES = 55000

def fail(message: str) -> None:
    print("ERROR:", message)
    sys.exit(1)

def normalize_doctype(html: str) -> str:
    low = html.lower()
    if low.startswith("<!doctype html>"):
        return html
    idx = low.find("<!doctype html>")
    if idx < 0:
        fail("<!doctype html> not found")
    print(f"Normalizing doctype: removed {idx} leading characters before <!doctype html>")
    return html[idx:]

def load_next_version_code() -> int:
    try:
        manifest = json.loads(VERSION_PATH.read_text(encoding="utf-8"))
        return int(manifest.get("versionCode", 0)) + 1
    except Exception as err:
        print(f"WARN: could not read {VERSION_PATH}: {err}; using versionCode 1")
        return 1

def script_pattern(script_id: str) -> re.Pattern:
    return re.compile(
        r'\s*(?:<!--\s*BEGIN\s+' + re.escape(script_id) + r'.*?-->\s*)?'
        r'<script\b(?=[^>]*\bid=["\']' + re.escape(script_id) + r'["\'])[^>]*>.*?</script>'
        r'\s*(?:<!--\s*END\s+' + re.escape(script_id) + r'\s*-->\s*)?',
        re.I | re.S
    )

def extract_json_script(html: str, script_id: str) -> dict:
    m = re.search(
        r'<script\b(?=[^>]*\bid=["\']' + re.escape(script_id) + r'["\'])[^>]*>(.*?)</script>',
        html,
        re.I | re.S
    )
    if not m:
        return {}
    raw = m.group(1).strip()
    try:
        return json.loads(raw)
    except Exception as err:
        print(f"WARN: could not parse embedded {script_id}: {err}")
        return {}

def remove_script(html: str, script_id: str) -> str:
    return script_pattern(script_id).sub("\n", html)

def remove_meta_markers(html: str) -> str:
    for name in ["kgg-source-truth", "kgg-changelog", "kgg-patch-rules"]:
        html = re.sub(
            r'\s*<meta\b(?=[^>]*\bname=["\']' + re.escape(name) + r'["\'])[^>]*>\s*',
            "\n",
            html,
            flags=re.I
        )
    return html

def remove_read_first_header(html: str) -> str:
    return re.sub(
        r'\s*<!--\s*KGG INTERNAL SOURCE TRUTH — READ THIS FIRST\s*.*?END KGG INTERNAL SOURCE TRUTH READ FIRST\s*-->\s*',
        "\n",
        html,
        flags=re.I | re.S
    )

def json_script(script_id: str, data: dict, label: str) -> str:
    body = json.dumps(data, ensure_ascii=False, indent=2)
    return (
        f'\n<!-- BEGIN {script_id}: {label}; READ THIS BEFORE PATCHING -->\n'
        f'<script type="application/json" id="{script_id}">\n'
        f'{body}\n'
        f'</script>\n'
        f'<!-- END {script_id} -->\n'
    )

def build_read_first_header() -> str:
    return '''
<!--
KGG INTERNAL SOURCE TRUTH — READ THIS FIRST

Machine-readable app state, patch rules, and changelog are embedded near the top of this HTML.
Before editing this app, any LLM/agent/human should read these blocks:
1. <script type="application/json" id="kgg-source-truth">
2. <script type="application/json" id="kgg-changelog">
3. <script type="application/json" id="kgg-patch-rules">

Do not remove or rename these blocks.
Do not silently delete the last patch for a feature/function.
If a patch must be replaced, document supersedes/supersededBy/removalReason/rollbackNote in kgg-changelog.
If the embedded changelog exceeds its warning size/entry threshold, warn Max before adding more history.

END KGG INTERNAL SOURCE TRUTH READ FIRST
-->
'''

def build_size_guard_script() -> str:
    return f'''
<!-- BEGIN {SIZE_GUARD_ID}: console/helper warning when embedded changelog grows too large -->
<script id="{SIZE_GUARD_ID}">
(function(){{
  "use strict";
  var FALLBACK_POLICY = {{
    warnAtEntries: {CHANGELOG_WARN_AT_ENTRIES},
    maxEmbeddedEntries: {CHANGELOG_MAX_EMBEDDED_ENTRIES},
    warnAtBytes: {CHANGELOG_WARN_AT_BYTES},
    maxEmbeddedBytes: {CHANGELOG_MAX_EMBEDDED_BYTES}
  }};
  function readJsonBlock(id){{
    var el = document.getElementById(id);
    if(!el) return null;
    try{{ return JSON.parse((el.textContent||"").trim()); }}
    catch(err){{ return {{__parseError:String(err)}}; }}
  }}
  function changelogSizeReport(){{
    var el = document.getElementById("{CHANGELOG_ID}");
    var rules = readJsonBlock("{PATCH_RULES_ID}") || {{}};
    var policy = (rules && rules.changelogSizePolicy) || FALLBACK_POLICY;
    var text = el ? (el.textContent || "") : "";
    var entries = 0;
    var parseError = "";
    try{{
      var data = text ? JSON.parse(text) : {{}};
      entries = Array.isArray(data.entries) ? data.entries.length : 0;
    }}catch(err){{
      parseError = String(err);
    }}
    var bytes = 0;
    try{{ bytes = new TextEncoder().encode(text).length; }}
    catch(err){{ bytes = text.length; }}
    var warnings = [];
    if(!el) warnings.push("kgg-changelog block missing");
    if(parseError) warnings.push("kgg-changelog parse error: " + parseError);
    if(entries >= Number(policy.warnAtEntries || FALLBACK_POLICY.warnAtEntries)){{
      warnings.push("embedded changelog entries approaching limit: " + entries + "/" + (policy.maxEmbeddedEntries || FALLBACK_POLICY.maxEmbeddedEntries));
    }}
    if(bytes >= Number(policy.warnAtBytes || FALLBACK_POLICY.warnAtBytes)){{
      warnings.push("embedded changelog bytes approaching limit: " + bytes + "/" + (policy.maxEmbeddedBytes || FALLBACK_POLICY.maxEmbeddedBytes));
    }}
    return {{
      entries: entries,
      bytes: bytes,
      policy: policy,
      warnings: warnings,
      shouldWarn: warnings.length > 0
    }};
  }}
  window.KGG_PATCH_GUARD = window.KGG_PATCH_GUARD || {{}};
  window.KGG_PATCH_GUARD.readSourceTruth = function(){{ return readJsonBlock("{SOURCE_TRUTH_ID}"); }};
  window.KGG_PATCH_GUARD.readChangelog = function(){{ return readJsonBlock("{CHANGELOG_ID}"); }};
  window.KGG_PATCH_GUARD.readPatchRules = function(){{ return readJsonBlock("{PATCH_RULES_ID}"); }};
  window.KGG_PATCH_GUARD.checkChangelogSize = changelogSizeReport;
  var report = changelogSizeReport();
  window.KGG_PATCH_GUARD.lastChangelogSizeReport = report;
  if(report.shouldWarn && console && console.warn){{
    console.warn("KGG changelog/source-truth warning:", report);
  }}
}})();
</script>
<!-- END {SIZE_GUARD_ID} -->
'''

def ensure_head_insert(html: str, block: str) -> str:
    m = re.search(r'<head\b[^>]*>', html, flags=re.I)
    if not m:
        fail("<head> not found")
    return html[:m.end()] + block + html[m.end():]

def unique_append(items, value):
    if value not in items:
        items.append(value)

def update_metadata(html: str, version_code: int, version_name: str) -> str:
    released_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    source_truth = extract_json_script(html, SOURCE_TRUTH_ID) or {}
    changelog = extract_json_script(html, CHANGELOG_ID) or {}
    patch_rules = extract_json_script(html, PATCH_RULES_ID) or {}

    source_truth.update({
        "schema": int(source_truth.get("schema") or 1),
        "app": "KGG Plan",
        "purpose": "Machine-readable Source Truth for local LLMs, Codex agents and future patch automation.",
        "currentWebVersion": {
            "versionCode": version_code,
            "versionName": version_name,
            "channel": "github-pages-main",
            "updateUrl": "https://kayus24.github.io/kgg/kgg-update/version.json",
            "sha256": "see kgg-update/version.json",
            "releasedAt": released_at,
        },
        "protectedAreas": PROTECTED_AREAS,
        "lastUpdateIntent": {
            "id": UPDATE_ID,
            "summary": "Adds a patch-retention policy, LLM-readable patch rules, and changelog size warning thresholds directly inside the app HTML.",
            "notTouched": PROTECTED_AREAS,
        },
        "patchRetentionPolicy": {
            "rule": "Never delete the latest patch for a function silently.",
            "why": "The last patch for a feature is often what fixed or stabilized the bug; removing it without tracking can reintroduce old bugs.",
            "defaultBehavior": "Preserve previous patch code and patch history unless Max explicitly approves removal.",
            "whenReplacingPatch": [
                "Mark old changelog entry as superseded, not deleted.",
                "Add supersededBy on the old entry when practical.",
                "Add supersedes on the new entry.",
                "Record whySuperseded/removalReason/testEvidence/rollbackNote."
            ],
            "requiredWhenRemovingPatch": [
                "supersededBy",
                "removalReason",
                "testEvidence",
                "rollbackNote",
                "explicitMaxApproval"
            ],
            "pipelineExpectation": "If patch markers or active fixes disappear without changelog documentation, stop and ask Max."
        },
        "changelogSizePolicy": {
            "scope": "embedded kgg-changelog in index.html",
            "warnAtEntries": CHANGELOG_WARN_AT_ENTRIES,
            "maxEmbeddedEntries": CHANGELOG_MAX_EMBEDDED_ENTRIES,
            "warnAtBytes": CHANGELOG_WARN_AT_BYTES,
            "maxEmbeddedBytes": CHANGELOG_MAX_EMBEDDED_BYTES,
            "actionWhenWarningThresholdReached": "Warn Max before adding more large entries; propose compact summaries or external archival.",
            "actionWhenMaxExceeded": "Stop non-critical updates until Max approves compaction/archive strategy.",
            "doNotAutoDeleteHistory": True
        }
    })

    fixes = list(source_truth.get("activeFixes") or [])
    for item in [
        "patch-retention-policy",
        "changelog-size-warning",
        "llm-readable-patch-rules",
        "embedded-source-truth",
        "embedded-changelog"
    ]:
        unique_append(fixes, item)
    source_truth["activeFixes"] = fixes

    rules = list(source_truth.get("rulesForFutureAgents") or [])
    for rule in [
        "READ kgg-source-truth, kgg-changelog and kgg-patch-rules before changing code.",
        "Do not touch protectedAreas without explicit Max approval.",
        "If a user request conflicts with Source Truth, stop and ask Max before changing code.",
        "Every update must add or update a changelog entry.",
        "Never silently remove the latest patch for a function; preserve or supersede it with documentation.",
        "If the embedded changelog exceeds warning thresholds, warn Max before continuing.",
        "Do not put API keys, patient data, admin-safe codes, secrets or private links in embedded JSON.",
        "The HTML file must start exactly with <!doctype html>.",
    ]:
        unique_append(rules, rule)
    source_truth["rulesForFutureAgents"] = rules

    patch_rules.update({
        "schema": int(patch_rules.get("schema") or 1),
        "id": "kgg-patch-rules",
        "readFirst": [
            "#kgg-source-truth",
            "#kgg-changelog",
            "#kgg-patch-rules"
        ],
        "mustUpdateOnEveryPatch": [
            "kgg-source-truth.currentWebVersion",
            "kgg-source-truth.lastUpdateIntent",
            "kgg-changelog.entries",
            "kgg-update/version.json.versionCode",
            "kgg-update/version.json.versionName",
            "kgg-update/version.json.sha256"
        ],
        "protectedAreas": PROTECTED_AREAS,
        "patchRetentionPolicy": source_truth["patchRetentionPolicy"],
        "changelogSizePolicy": source_truth["changelogSizePolicy"],
        "blockPatchIfMissing": [
            "kgg-source-truth",
            "kgg-changelog",
            "kgg-patch-rules"
        ],
        "requiredOnPatchRemoval": [
            "supersededBy or replacementPatchId",
            "removalReason",
            "testEvidence",
            "rollbackNote",
            "explicitMaxApproval"
        ],
        "llmInstruction": "If changelog size exceeds policy thresholds or a patch-removal is not documented, warn Max and ask before changing code."
    })

    entries = list(changelog.get("entries") or [])
    entries = [
        e for e in entries
        if not (isinstance(e, dict) and (e.get("patchId") == UPDATE_ID or e.get("versionName") == version_name))
    ]
    new_entry = {
        "versionCode": version_code,
        "versionName": version_name,
        "patchId": UPDATE_ID,
        "status": "active",
        "type": "github-web-update",
        "title": "Patch-Retention und Changelog-Größenwarnung",
        "reason": "Max will verhindern, dass spätere LLMs den letzten funktionalen Patch einer Funktion versehentlich löschen, und möchte gewarnt werden, wenn der interne Changelog zu groß wird.",
        "whatChanged": [
            "Patch-Retention-Policy direkt in kgg-source-truth eingebettet.",
            "kgg-patch-rules als eigener maschinenlesbarer JSON-Block ergänzt.",
            "Changelog-Größenpolicy mit Entry- und Byte-Warnschwellen ergänzt.",
            "Kleiner KGG_PATCH_GUARD im Browser ergänzt, der Source Truth/Changelog/Patch Rules auslesen und Changelog-Größe prüfen kann.",
            "LLM-Regeln erweitert: Patches nicht still löschen; bei Konflikten oder Größenwarnungen Max fragen."
        ],
        "touchedAreas": [
            "HTML embedded metadata",
            "Source Truth",
            "Changelog",
            "Patch rules",
            "Non-UI helper script"
        ],
        "notTouched": PROTECTED_AREAS,
        "supersedes": [],
        "removalPolicy": {
            "doNotDeleteReason": "Dieser Eintrag definiert die neue Regel, dass alte Fix-Patches nicht still entfernt werden dürfen.",
            "requiresExplicitMaxApprovalToRemove": True
        },
        "testStatus": {
            "githubPages": "pending",
            "androidApp": "pending",
            "llmReadability": "pending"
        }
    }
    entries.insert(0, new_entry)

    changelog.update({
        "schema": int(changelog.get("schema") or 1),
        "latestVersionCode": version_code,
        "latestVersionName": version_name,
        "entries": entries
    })

    serialized_changelog = json.dumps(changelog, ensure_ascii=False, indent=2)
    changelog_size = len(serialized_changelog.encode("utf-8"))
    if len(entries) >= CHANGELOG_WARN_AT_ENTRIES or changelog_size >= CHANGELOG_WARN_AT_BYTES:
        changelog["sizeWarning"] = {
            "triggeredAtVersionCode": version_code,
            "entries": len(entries),
            "bytes": changelog_size,
            "message": "Embedded changelog is approaching policy threshold. Warn Max before adding much more history; do not auto-delete entries."
        }
        print("WARN: embedded changelog is approaching size policy threshold:", changelog["sizeWarning"])

    html = remove_read_first_header(html)
    html = remove_script(html, SOURCE_TRUTH_ID)
    html = remove_script(html, CHANGELOG_ID)
    html = remove_script(html, PATCH_RULES_ID)
    html = remove_script(html, SIZE_GUARD_ID)
    html = remove_meta_markers(html)

    meta = '''
<meta name="kgg-source-truth" content="#kgg-source-truth">
<meta name="kgg-changelog" content="#kgg-changelog">
<meta name="kgg-patch-rules" content="#kgg-patch-rules">
'''
    blocks = (
        build_read_first_header()
        + meta
        + json_script(SOURCE_TRUTH_ID, source_truth, "embedded Source Truth")
        + json_script(CHANGELOG_ID, changelog, "embedded Changelog")
        + json_script(PATCH_RULES_ID, patch_rules, "embedded Patch Rules")
        + build_size_guard_script()
    )
    html = ensure_head_insert(html, blocks)
    return html

def validate(html: str) -> None:
    if not html.lower().startswith("<!doctype html>"):
        fail("HTML does not start exactly with <!doctype html>")
    for marker in [
        'id="kgg-source-truth"',
        'id="kgg-changelog"',
        'id="kgg-patch-rules"',
        'KGG INTERNAL SOURCE TRUTH — READ THIS FIRST',
        'id="kgg-changelog-size-guard"',
        'window.KGG_PATCH_GUARD',
        'patchRetentionPolicy',
        'changelogSizePolicy',
        'Never delete the latest patch for a function silently'
    ]:
        if marker not in html:
            fail(f"required marker missing after patch: {marker}")

def main() -> None:
    if not HTML_PATH.exists():
        fail(f"{HTML_PATH} not found")
    html = HTML_PATH.read_text(encoding="utf-8")
    html = normalize_doctype(html)

    next_code = load_next_version_code()
    html = update_metadata(html, next_code, VERSION_NAME)
    html = normalize_doctype(html)
    validate(html)

    HTML_PATH.write_text(html, encoding="utf-8")
    print(f"Patched {HTML_PATH}")
    print(f"Expected next versionName: {VERSION_NAME}")
    print(f"Embedded metadata versionCode: {next_code}")
    print("This patch is non-destructive: existing changelog entries are preserved, not truncated.")

if __name__ == "__main__":
    main()
