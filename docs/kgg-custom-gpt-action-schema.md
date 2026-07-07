# KGG Custom GPT Action Schema

This is the canonical payload shape for `KGG GPT Preview Gate`.
The Custom GPT must follow this shape exactly.

The combined GPT Action OpenAPI schema lives at `docs/kgg-custom-gpt-action-openapi.yaml`.
For the current split GPT editor setup, update the existing `api.github.com` Action with `docs/kgg-custom-gpt-action-api-openapi.yaml` and keep the separate `raw.githubusercontent.com` Action for read-only repo context.
Do not paste the combined schema into an editor that already has a separate `raw.githubusercontent.com` Action; ChatGPT rejects duplicate action domains.
If the GPT editor does not offer `validate_only`, the Action schema is stale and must be updated before any Preview request.

## Modes

- `validate_only`: validate JSON, exact patch matches and HTML syntax. Writes nothing.
- `publish_preview`: validate, run tests, build Preview APK, publish HTML/meta to `gpt-preview`.
- `create_pr`: only after Max accepts the matching preview. Creates a PR, never merges.
- `publish_admin_beta`: only after Max accepts the matching Preview/Test-APK. Creates an `[admin-beta]` PR, labels it `kgg-auto-merge`, waits for required checks and merges the Admin beta to `main`.

## Valid payload

```json
{
  "request_id": "kgg-v057-tablet-split-scale",
  "title": "v057 Tablet Splitter und Skalierung trennen",
  "summary": "Tablet Splitter liegt auf der Spaltengrenze; Plus/Minus bleibt reine Skalierung.",
  "version_slug": "v057-tablet-split-scale",
  "required_tests": [
    "cmd /c release-pipeline\\run-kgg-tests.cmd --level critical",
    "cmd /c release-pipeline\\run-kgg-tests.cmd --suite ui-stability --level regression"
  ],
  "operations": [
    {
      "type": "replace_exact",
      "path": "kgg-update/index.html",
      "old_text": "...",
      "new_text": "..."
    }
  ]
}
```

## Required operation fields

- `path` must be exactly `kgg-update/index.html`.
- `old_text` must be non-empty and match exactly once.
- `new_text` must be a string.
- Do not use `file`, `filename`, `target` or other aliases.
- Do not patch `const VERSION`, `KGG_BUILD_INFO`, `kgg-source-truth` or `kgg-changelog`; the Preview Gate owns version/build metadata.
- UI-like payloads must include `required_tests` with `critical` and `ui-stability regression` before any dispatch.

## Preview artifact response checklist

The GPT may say a Preview is available only after it has verified:

- GitHub run conclusion is `success`.
- `critical` completed successfully.
- `ui-stability regression` completed successfully for UI/Layout changes.
- Artifact exists and is not expired.
- `meta.json` returns HTTP 200.
- Preview HTML returns HTTP 200.
- Test-APK/Preview channel is updated when the request targets the Test-APK.
- Max accepts the Test-APK result before `create_pr` or `publish_admin_beta` is used.
- A push-test counts positive only after both `publish_preview` and `publish_admin_beta` are verified.

## Dispatch note

For complex payloads, use GitHub CLI JSON via STDIN instead of raw `-f payload_json=...`.
This preserves quotes inside `payload_json` and prevents invalid JSON such as `{request_id:...}`.

## Required GPT Action operations

- `submitKggPreviewGate` must allow `mode` values `validate_only`, `publish_preview`, `create_pr` and `publish_admin_beta`.
- `listKggPreviewGateRuns` must be available so the GPT can find the run for a `request_id`.
- `getKggPreviewGateRun` must be available so the GPT can verify `status` and `conclusion`.
- `getKggPreviewGateJobs` must be available so the GPT can report failed job/step names.
- `getKggPreviewGateArtifacts` must be available so the GPT can verify the Preview artifact exists and is not expired.
