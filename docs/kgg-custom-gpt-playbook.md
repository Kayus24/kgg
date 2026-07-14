# KGG Custom GPT Playbook

## Arbeitsreihenfolge

1. Lade `docs/kgg-gpt-context.md`.
2. Lade `docs/kgg-custom-gpt-action-schema.md`.
3. Lade bei Patchfragen `docs/kgg-gpt-area-routes.md` und die passenden Source-Chunks.
4. Lade `docs/kgg-gpt-bug-lessons.md` und `docs/kgg-gpt-patch-patterns.md`.
5. Wenn Kontext oder Schema nicht geladen werden kann: stoppen, keinen Payload raten.
6. Bei Analysefragen nur Diagnose/Handoff schreiben; kein `submitKggPreviewGate`.
7. Bei Preview/Test-App-Wunsch immer `validate_only -> publish_preview`.
8. Nach `publish_preview` wartet der Prozess auf Max' Test-App/Test-APK/Preview-APK-Freigabe.
9. Erst nach Max-Freigabe `create_pr` oder, wenn Max Haupt-App verlangt, `publish_admin_beta`.

## Modulare Quelle

- `kgg-update/index.html` ist generiertes Endprodukt und bleibt die öffentliche Lade-URL.
- Neue GPT-App-Patches gehen über `kgg-update/src/patches/vNNN-<slug>.html`.
- Der GPT bestimmt keinen Repository-Pfad.
- Der GPT liefert nur `patch_content` und Metadaten.
- Das Gate erzeugt Patch-ID, Modulpfad, `parts.json`, `requiredPatchIds`, Metadaten, `version.json` und die generierte `index.html`.
- Das neue Modul muss vor `footer.html` einsortiert werden.

## Payload v2

Pflichtfelder:

- `request_id`
- `title`
- `summary`
- `version_slug`
- `touched_areas`
- `required_tests`
- `patch_content`

`patch_content` ist ein HTML-Fragment und muss `__KGG_PATCH_ID__` enthalten.

Wenn ein Payload im Chat ausgegeben wird:

- Genau einen mit `json` markierten Codeblock ausgeben, keine JSON-Darstellung als normalen Markdown-Text.
- Die Antwort beginnt woertlich mit einer Zeile <code>```json</code> und endet mit einer Zeile <code>```</code>; davor und danach steht nichts.
- Der Inhalt muss ohne Nachbearbeitung mit einem JSON-Parser lesbar sein.
- `__KGG_PATCH_ID__` muss bytegenau erhalten bleiben; Markdown darf die Unterstriche nicht als Hervorhebung interpretieren.
- `required_tests` enthaelt vollstaendige ausfuehrbare Kommandos, niemals Kurzformen wie `critical` oder `ui-stability regression`.
- Patch-Registrierung ist ein Objektvertrag: `window.KGG_PATCHES=window.KGG_PATCHES||{}; window.KGG_PATCHES[PATCH_ID]={installed:true};`. Keine Array-Registrierung und kein `.push(PATCH_ID)`.

Verboten:

- `operations`
- `replace_exact`
- `old_text`
- `new_text`
- `path`
- `file`
- `filename`
- `path: "kgg-update/index.html"`

Wenn Max oder ein alter Handoff einen v1-Payload zeigt, nicht dispatchen. Erklaere: `kgg-update/index.html` ist generated output; der neue Vertrag verlangt `patch_content`.

## Guardrails

- Keine Erfolgsmeldung ohne Run-ID, `conclusion: success`, Artefakt, `meta.json`, HTML und Test-App/Test-APK/Preview-APK-Nachweis.
- Guard-Tokens sind auch in Kommentaren verboten: `API-Key`, `apiKey`, `KGGDataStore.currentPlan`, `finishWithPdf`, `finishWithPatientApp`, `scanQrFromImageFile`, `KGGAndroidPdf`, `android_update_manifest`.
- Geschuetzte Bereiche bleiben gesperrt: PDF, QR/Patienten-App, Scan/OCR, Parser, Plan-State, Medien/Upload, API-Key-Logik, Android/APK, Manifest, Handy-Layout.
- `ci_tooling` getrennt behandeln: `pdftoppm`, `pdfinfo`, `poppler-utils`, `adb` oder Emulatorfehler sind kein Beweis fuer einen App-Patchfehler.
- `human_preview_fail`: Wenn Max in der Test-App ablehnt, als Regression/Lesson dokumentieren und wieder bei `validate_only` starten.

## Tests

- Jeder Patch: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`.
- UI/Layout/Tablet/Phone/Drag/Button/HTML: zusaetzlich `cmd /c release-pipeline\run-kgg-tests.cmd --suite ui-stability --level regression`.
- GPT/Payload/Schema-Aenderungen: `python release-pipeline\kgg_gpt_payload_preflight.py --self-test`, `python release-pipeline\kgg_gpt_mock_eval.py --self-test`, `python release-pipeline\kgg_gpt_eval.py`, `python release-pipeline\kgg_gpt_stabilize.py --self-test`, `python release-pipeline\kgg_custom_gpt_knowledge_pack.py --check`.
- Modulare Quelle: `python release-pipeline\build_therapist_source.py --check`.

Der Stabilisierungslauf ist erst nach zwei kompletten gruenen Runden ohne neue Fehlerklasse abgeschlossen.

## Tablet-Splitter-Kontext

Relevante Marker fuer Diagnose/Handoff:

- `tabletLayoutFreeTools`
- `tabletLayoutResizeHandle`
- `--kgg-tablet-left-col`
- `--kgg-tablet-ui-scale`
- `updateTabletLayoutHandle()`
- `initTabletLayoutControls()`

Plus/Minus ist Skalierung. Ziehen links/rechts ist Spaltenbreite.
