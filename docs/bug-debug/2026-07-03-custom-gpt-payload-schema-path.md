# Custom GPT Payload Schema: path statt file

## Problem

Ein Custom-GPT-Preview-Dispatch kann formal plausibel aussehen, aber im Write-Gate scheitern, wenn eine Operation das Feld `file` statt `path` verwendet.
Konkreter Run: `28665968004` scheiterte im Step `Apply guarded GPT payload` mit `ERROR: v1 only allows kgg-update/index.html`.

## Ursache

`release-pipeline/kgg_gpt_write_gate.py` erlaubt in v1 nur Operationen mit:

- `path: "kgg-update/index.html"`
- `old_text`
- `new_text`

Alias-Felder wie `file`, `filename` oder `target` werden nicht akzeptiert.

## Loesung

Der GPT muss jeden Payload vor Dispatch stoppen, wenn eine Operation `file` statt `path` nutzt.
Die korrekte Operation ist:

```json
{
  "path": "kgg-update/index.html",
  "old_text": "...",
  "new_text": "..."
}
```

## Nicht anfassen

- App-Feature-Code
- PDF
- QR/Patienten-App
- Scan/OCR
- Parser
- Plan-State
- Medien/Upload
- Android/APK
- GitHub Manifest
- Handy-Layout

## Test / Abnahmekriterien

- `release-pipeline/kgg_gpt_payload_preflight.py --self-test` blockt einen Payload mit `file`.
- GPT-Eval `payload-schema-path` verlangt `path: "kgg-update/index.html"`.
- Der GPT darf bei rotem Run nicht nur `meta.json 404` melden, sondern muss den fehlgeschlagenen Step und die Gate-Meldung nennen.

## Bereiche

- debug
- preview-gate
- tablet-layout
