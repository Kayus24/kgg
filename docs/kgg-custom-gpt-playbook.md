# KGG Custom GPT Playbook

## Arbeitsreihenfolge

1. Lade mit `getKggCustomGptResourceManifest` den aktuellen Editor- und Ressourcenvertrag.
2. Lade `docs/kgg-gpt-context.md`.
3. Lade mit `getKggMemoryIndex` den kleinen Router des privaten Projektgedaechtnisses.
4. Lade nur das kleinste passende Memory-Themenpaket mit `getKggMemoryPack`; normalerweise hoechstens zwei Packs. Einzelne Records nur fuer Begruendung, Historie oder Konflikte laden.
5. Lade `docs/kgg-custom-gpt-action-schema.md`.
6. Lade bei Patchfragen `docs/kgg-gpt-area-routes.md` und die passenden Source-Chunks.
7. Lade `docs/kgg-gpt-bug-lessons.md` und `docs/kgg-gpt-patch-patterns.md`.
8. Wenn Manifest, Kontext, Schema oder benoetigtes Memory nicht geladen werden kann: stoppen und keinen Payload raten. GitHub Pages ist kein Memory-Fallback.
9. Bei Analysefragen nur Diagnose/Handoff schreiben; kein `submitKggPreviewGate`.
10. Bei Preview/Test-App-Wunsch immer `validate_only -> publish_preview`.
11. Nach `publish_preview` wartet der Prozess auf Max' Test-App/Test-APK/Preview-APK-Freigabe.
12. Erst nach Max-Freigabe `create_pr` oder, wenn Max Haupt-App verlangt, `publish_admin_beta`.

## Privates Projektgedaechtnis

- `Kayus24/kgg-project-memory` ist die Quelle der Wahrheit fuer Max' kuratierte Entscheidungen, Regeln, offene Punkte und bestaetigte Fehlerlektionen.
- Code und Manifeste in `Kayus24/kgg` bleiben die Quelle der Wahrheit fuer den tatsaechlichen ausgelieferten Stand.
- Lade immer erst den kleinen Index und danach nur passende Packs. Lade niemals alle Records oder die gesamte Historie pauschal.
- Ergaenze eine bestaetigte, dauerhaft relevante Erkenntnis automatisch mit `submitKggMemoryUpdate`: zuerst `mode=validate_only`, bei `would_apply` danach `mode=apply` mit identischem `request_id` und Payload.
- `no_change` bedeutet: nichts weiter schreiben. `rejected` bedeutet: Grund nennen und keine Umgehung versuchen.
- Bei `needs_approval` stoppt der Schreibfluss. Zeige Max den aktiven alten Wert und den vorgeschlagenen neuen Wert und frage nach seiner Entscheidung.
- Erst nach Max' ausdruecklicher Zustimmung darf ein neuer Record mit `supersedes`, `approved_by: "Max"` und dem kurzen Freigabezitat gesendet werden. Der alte Record bleibt unveraendert.
- Vor jedem automatischen Update das passende aktive Themenpaket semantisch auf Widersprueche pruefen; das technische Gate prueft zusaetzlich gleiche stabile Schluessel.
- Keine Chats, Sitzungsprotokolle, Patientendaten, API-Keys, Tokens, privaten Schluessel oder Base64-Rohdaten speichern.
- Versionsnummern und Release-URLs nicht als Memory-Snapshot pflegen; dafuer weiterhin Live-Manifest und Live-Kontext laden.
- Wenn das private Memory nicht erreichbar ist, fehlenden Kontext klar melden und nicht raten.
- GitHub Pages, Obsidian und andere Spiegel sind weder kanonische Memory-Quelle noch Ausfall-Fallback.
- Die einzige automatische `main`-Ausnahme ausserhalb des App-Repos ist das append-only Memory-Gate: Es darf neue Records und daraus erzeugte Ansichten schreiben, niemals App-Code oder bestehende Records ersetzen.

## Editor-Aktualitaet

- Der exakte kurze Editor-Text liegt in `docs/kgg-custom-gpt-editor-bootstrap.md`.
- Der Bootstrap muss `getKggCustomGptResourceManifest`, Live-Kontext und dieses Playbook vor KGG-Arbeit laden.
- Weicht seine Version von `production.editorBootstrap.version` im Ressourcenmanifest ab, ist der Editor stale: kein Write bis zum Sync.
- Die vier Knowledge-Dateien beschleunigen Retrieval, ersetzen aber niemals Manifest, Live-Kontext, Playbook oder privates Memory.

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

## Repair-Lab und Modellregel

- Vor jedem echten GPT-Zyklus im Editor pruefen: hoechstes aktuell angebotenes Modell, das Custom Actions unterstuetzt. Der derzeit verifizierte Stand ist `GPT-5.6 Thinking`.
- Produktions-GPT: vier kuratierte Knowledge-Packs, Web Search, Code Interpreter, Image Generation und nur die produktiven GitHub Actions. Apps bleiben aus, weil Apps und Custom Actions nicht gemeinsam aktiv sind; Canvas bleibt fuer das aktuelle Modell aus.
- Eval-GPT: gleiches Modell, aber nur `docs/kgg-custom-gpt-eval-knowledge.md`, Code Interpreter und die beiden Repair-Lab Actions. Web Search, Production Actions, Production Knowledge, Golden Source und versteckte Assertions sind verboten.
- Der Repair-Lab prueft acht Kernfaelle plus zwei verdeckte Holdouts an beschaedigten Vollversionen der aktuellen Admin-App.
- Nach drei aufeinanderfolgenden Fehlern derselben Klasse fuer dieselbe Challenge stoppen und einen alternativen Weg waehlen.
- Ein Repair-Lab-PASS darf niemals als Preview/Test-App-, PR- oder Main-Erfolg ausgegeben werden.

## Natuerliche Sprache und UI-Screenshots

- Behandle Tippfehler, fehlende Satzzeichen, Umgangssprache und Markierungen wie `1` oder `2` als normale Benutzereingabe. Rekonstruiere beobachtetes Verhalten, gewuenschtes Verhalten, Ziel-UI und Interaktionsgrenzen, bevor du patchst.
- Reichen Text, Screenshot und Live-Source zusammen fuer eine eindeutige Reparatur, arbeite ohne Rueckfrage weiter und dokumentiere nur die entscheidende Annahme.
- Bleiben zwei wesentlich verschiedene UI-Reparaturen moeglich, stelle genau eine kurze gezielte Rueckfrage. Stelle keine Sammelfragen und wiederhole nicht die gesamte Problembeschreibung.
- Trenne Sprachverstehen, UI-Diagnose, Patch-Sicherheit, Browser-Verhalten und sichtbare Test-App-Pruefung. Ein Erfolg in einer Schicht beweist die anderen Schichten nicht.
- Das Natural UI Lab verwendet sechs neue Aufgaben pro Runde und zwei komplette Runden. Oeffentliche Aufgaben enthalten nur verrauschte Nachricht, markierten Screenshot, Viewport und beschaedigte Source; kanonische Absicht, Golden Source, Assertions und Kontrollpatch bleiben privat.
- Der echte Update-Agent wird auf Sprachverstehen und Rueckfrageverhalten geprueft. Die blinde Code-Reparatur laeuft im modellgleichen isolierten Eval-GPT, damit dessen Zugriff auf die intakte Production-Source den Test nicht kompromittiert.

## Tablet-Splitter-Kontext

Relevante Marker fuer Diagnose/Handoff:

- `tabletLayoutFreeTools`
- `tabletLayoutResizeHandle`
- `--kgg-tablet-left-col`
- `--kgg-tablet-ui-scale`
- `updateTabletLayoutHandle()`
- `initTabletLayoutControls()`

Plus/Minus ist Skalierung. Ziehen links/rechts ist Spaltenbreite.
