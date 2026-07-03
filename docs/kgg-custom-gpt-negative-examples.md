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
