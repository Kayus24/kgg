# KGG Custom GPT Action Schema

This is the canonical payload shape for `KGG GPT Preview Gate`.
The Custom GPT must follow this shape exactly.

## Modes

- `validate_only`: validate JSON, exact patch matches and HTML syntax. Writes nothing.
- `publish_preview`: validate, run tests, build Preview APK, publish HTML/meta to `gpt-preview`.
- `create_pr`: only after Max accepts the matching preview. Creates a PR, never merges.

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

## Preview artifact response checklist

The GPT may say a Preview is available only after it has verified:

- GitHub run conclusion is `success`.
- `critical` completed successfully.
- `ui-stability regression` completed successfully for UI/Layout changes.
- Artifact exists and is not expired.
- `meta.json` returns HTTP 200.
- Preview HTML returns HTTP 200.

## Dispatch note

For complex payloads, use GitHub CLI JSON via STDIN instead of raw `-f payload_json=...`.
This preserves quotes inside `payload_json` and prevents invalid JSON such as `{request_id:...}`.
