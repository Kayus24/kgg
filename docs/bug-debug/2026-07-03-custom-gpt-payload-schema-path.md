# Custom GPT Payload Schema: alter v1-Pfad statt modularer v2-Payload

## Problem

Ein Custom-GPT-Preview-Dispatch kann formal plausibel aussehen, aber im Write-Gate scheitern, wenn er ein altes v1-Operationsschema verwendet.
Historischer Run: `28665968004` scheiterte im Step `Apply guarded GPT payload` mit `ERROR: v1 only allows kgg-update/index.html`.
Seit der modularen Quelle ist auch `path: "kgg-update/index.html"` falsch, weil `index.html` generiertes Endprodukt ist.

## Ursache

Das alte v1-Write-Gate erlaubte nur Operationen mit:

- `path: "kgg-update/index.html"`
- `old_text`
- `new_text`

Alias-Felder wie `file`, `filename` oder `target` werden nicht akzeptiert.
Das aktuelle v2-Gate akzeptiert gar keine `operations`, `path`, `file`, `old_text` oder `new_text` mehr. Der GPT liefert nur `patch_content` und Metadaten; das Gate erzeugt den Modulpfad unter `kgg-update/src/patches/` selbst.

## Loesung

Der GPT muss jeden Payload vor Dispatch stoppen, wenn er `operations`, `path`, `file`, `filename`, `target`, `old_text` oder `new_text` nutzt.
Der korrekte v2-Payload liefert kein Repository-Ziel, sondern nur Patchinhalt und Metadaten:

```json
{
  "request_id": "kgg-vNNN-example",
  "title": "Example",
  "summary": "Small scoped app patch.",
  "version_slug": "example",
  "touched_areas": ["Admin-Web UI"],
  "required_tests": [
    "cmd /c release-pipeline\\run-kgg-tests.cmd --level critical",
    "cmd /c release-pipeline\\run-kgg-tests.cmd --suite ui-stability --level regression"
  ],
  "patch_content": "<script id=\"__KGG_PATCH_ID__\">...</script>"
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
- GPT-Eval `payload-schema-path` blockt alte `operations` gegen `kgg-update/index.html`.
- GPT-Eval `modular-payload` verlangt `patch_content` mit `__KGG_PATCH_ID__`.
- Der GPT darf bei rotem Run nicht nur `meta.json 404` melden, sondern muss den fehlgeschlagenen Step und die Gate-Meldung nennen.

## Bereiche

- debug
- preview-gate
- tablet-layout
