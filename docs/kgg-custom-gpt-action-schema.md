# KGG Custom GPT Action Schema

This is the canonical payload shape for `KGG GPT Preview Gate` and `KGG Project Memory Gate`.
The Custom GPT must follow this shape exactly.

The public app still loads `kgg-update/index.html`, but that file is generated output.
The GPT must patch the modular source through the gate; it must not request direct edits to `kgg-update/index.html`.

## Modes

- `validate_only`: validate JSON, scaffold the modular patch in memory, verify build invariants. Writes nothing.
- `publish_preview`: validate, create a module under `kgg-update/src/patches/`, rebuild generated HTML, run tests, build Preview APK, publish HTML/meta to `gpt-preview`.
- `create_pr`: only after Max accepts the matching Test-App/Test-APK/Preview-APK. Creates a PR, never merges.
- `publish_admin_beta`: only after Max accepts the matching Test-App/Test-APK/Preview-APK and asks for Haupt-App/Admin-Beta. Creates an `[admin-beta]` PR, labels it `kgg-auto-merge`, waits for required checks and merges the Admin beta to `main`.

## Valid modular payload

```json
{
  "request_id": "kgg-v061-tablet-split-scale",
  "title": "Tablet Splitter und Skalierung trennen",
  "summary": "Tablet Splitter liegt auf der Spaltengrenze; Plus/Minus bleibt reine Skalierung.",
  "version_slug": "tablet-split-scale",
  "touched_areas": ["Tablet-Layout"],
  "required_tests": [
    "cmd /c release-pipeline\\run-kgg-tests.cmd --level critical",
    "cmd /c release-pipeline\\run-kgg-tests.cmd --suite ui-stability --level regression"
  ],
  "patch_content": "<style id=\"__KGG_PATCH_ID__-style\">...</style>\n<script id=\"__KGG_PATCH_ID__\">...</script>\n"
}
```

## Required payload fields

- `request_id`: stable lowercase id matching `[a-z0-9][a-z0-9-]{5,63}`.
- `title`, `summary`, `version_slug`: non-empty; `version_slug` uses lowercase words separated by single hyphens.
- `touched_areas`: non-empty list. Protected areas are rejected unless Max explicitly authorizes a separate guarded path.
- `required_tests`: non-empty list. UI-like payloads must include `critical` and `ui-stability regression`.
- `patch_content`: HTML fragment only. It must include `__KGG_PATCH_ID__`; the gate replaces it with the generated Patch-ID.

## Forbidden payload fields

- Do not send `operations`, `replace_exact`, `old_text`, `new_text`, `path`, `file`, `filename` or `target`.
- Do not send `path: "kgg-update/index.html"`. That is generated output and is rejected.
- Do not patch `const VERSION`, `KGG_BUILD_INFO`, `kgg-source-truth`, `kgg-changelog`, `base-app.html`, `base-head.html` or existing modules.
- Do not include protected tokens such as `API-Key`, `KGGDataStore.currentPlan`, `finishWithPdf`, `finishWithPatientApp`, `scanQrFromImageFile`, `KGGAndroidPdf` or `android_update_manifest`.

## Gate-owned outputs

The gate creates all of these:

- next `versionCode` and `versionName`
- `patchId`
- `kgg-update/src/patches/vNNN-<slug>.html`
- `kgg-update/src/parts.json` entry before `footer.html`
- `requiredPatchIds`
- source-truth/changelog metadata
- generated `kgg-update/index.html`
- `kgg-update/version.json` hash

## Preview artifact response checklist

The GPT may say a Preview is available only after it has verified:

- GitHub run conclusion is `success`.
- `critical` completed successfully.
- `ui-stability regression` completed successfully for UI/Layout changes.
- Artifact exists and is not expired.
- `meta.json` returns HTTP 200 and contains `patchFile`.
- Preview HTML returns HTTP 200.
- Test-App/Test-APK/Preview-APK channel is updated.
- Max accepts the Test-APK result before Admin-Beta/Main is allowed.
- Max accepts the Test-App result before `create_pr` or `publish_admin_beta` is used.
- A Haupt-App push counts positive only after `publish_admin_beta` is verified on `main`.

## Required GPT Action operations

- `submitKggPreviewGate` must allow `mode` values `validate_only`, `publish_preview`, `create_pr` and `publish_admin_beta`.
- `listKggPreviewGateRuns` must be available so the GPT can find the run for a `request_id`.
- `getKggPreviewGateRun` must be available so the GPT can verify `status` and `conclusion`.
- `getKggPreviewGateJobs` must be available so the GPT can report failed job/step names.
- `getKggPreviewGateArtifacts` must be available so the GPT can verify the Preview artifact exists and is not expired.

## Custom GPT Editor Domains

- Use the API-only Action schema for `api.github.com`.
- Do not create duplicate action domains for `raw.githubusercontent.com`; raw URLs are verified through the GitHub run/artifact/meta checks.
- If the editor reports duplicate action domains, stop and fix the Action schema before dispatching.

## KGG Project Memory Gate

The private repository `Kayus24/kgg-project-memory` stores curated durable decisions. It does not store app code, patient data, secrets or full chat transcripts.

Read in this order:

1. `getKggMemoryIndex`.
2. Only the smallest matching file via `getKggMemoryPack` (normally one or two packs).
3. `getKggMemoryRecord` or `getKggMemoryHistory` only for rationale, history or conflicts.

Valid memory payload:

```json
{
  "request_id": "memory-example-001",
  "record": {
    "kind": "decision",
    "key": "example.stable-key",
    "topic": "project",
    "title": "Short title",
    "summary": "Compact routing summary.",
    "value": "The durable instruction or fact.",
    "source_refs": ["user:2026-07-20"],
    "supersedes": []
  }
}
```

- Use `submitKggMemoryUpdate` with `mode=validate_only` first.
- Continue with `mode=apply` only for `would_apply`, using the identical `request_id` and payload.
- `no_change` is terminal and must not create another request.
- `needs_approval` means the active old value and candidate value must be shown to Max; write nothing until he explicitly approves.
- After approval, append a new record with `supersedes`, `approved_by: "Max"` and `approval_quote`. Never edit or delete the old record.
- `rejected` must be reported and never bypassed.
- The GPT must semantically compare the candidate with the matching active pack before dispatch. The workflow also blocks same-key value changes mechanically.

Required memory operations:

- `getKggMemoryIndex`
- `getKggMemoryPack`
- `getKggMemoryRecord`
- `getKggMemoryHistory`
- `submitKggMemoryUpdate`
- `listKggMemoryUpdateRuns`
- `getKggMemoryUpdateRun`
- `getKggMemoryUpdateStatus`
- `getKggMemoryUpdateArtifacts`
