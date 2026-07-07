# KGG Custom GPT Negative Examples

These are examples the GPT must reject before dispatch.

## Wrong operation key

Reject:

```json
{
  "operations": [
    {
      "file": "kgg-update/index.html",
      "old_text": "...",
      "new_text": "..."
    }
  ]
}
```

Reason: operations must use `path: "kgg-update/index.html"`.

## Protected token in patch comment

Reject:

```json
{
  "operations": [
    {
      "path": "kgg-update/index.html",
      "old_text": ".tabletLayoutResizeHandle{display:none}",
      "new_text": ".tabletLayoutResizeHandle{display:block} /* keine API-Key Aenderung */"
    }
  ]
}
```

Reason: protected words are forbidden in `old_text` and `new_text`, even inside comments. Put do-not-touch notes in the answer, not in the payload.

## Broken JSON from shell quoting

Reject:

```text
{request_id:kgg-v057-tablet-split-scale,operations:[{path:kgg-update/index.html}]}
```

Reason: JSON keys and string values must be quoted. Use the GitHub CLI JSON-stdin form when dispatching complex payloads.

## Red run plus missing meta

Reject this answer:

> meta.json is 404, so the manifest probably just has not updated yet.

Correct answer:

> The run is already red. The Preview is not available. Report the failed step and concrete error first.

## UI patch without UI tests

Reject any Tablet, Phone, Layout, Drag, Swipe or HTML patch that does not declare:

- `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`
- `cmd /c release-pipeline\run-kgg-tests.cmd --suite ui-stability --level regression`

## Manual version/build edit

Reject:

```json
{
  "operations": [
    {
      "path": "kgg-update/index.html",
      "old_text": "const VERSION='KGG_GITHUB_UPDATE_v056_patient_qr_root_query';",
      "new_text": "const VERSION='KGG_GITHUB_UPDATE_v058_tablet_splitter_drag_ratio';"
    }
  ]
}
```

Reason: the Preview Gate owns version and build metadata. The GPT patch payload only changes the requested app behavior.

## Success claim without verified Test-APK gate

Reject this answer:

> Preview ist fertig und kann auf main.

Correct answer:

> Noch nicht freigegeben. Erst `validate_only`, dann `publish_preview`, dann Run-ID, Artifact, `meta.json`, HTML und Test-APK-Kanal pruefen. Danach entscheidet Max in der Test-APK.

## Analysis prompt starts Preview dispatch

Reject this behavior:

> Max asks why the Tablet splitter is wrong, and the GPT immediately calls `submitKggPreviewGate`.

Reason: Ursache-/Analysefragen are not publish requests. The GPT must explain the diagnosis and tests first. It may dispatch only when Max explicitly asks for Preview, Test-HTML, Test-APK or Abschicken.
