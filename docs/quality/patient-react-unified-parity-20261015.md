# KGG Patienten-App – gemeinsame Legacy/P7/P8-Scope-Abnahme (15.10.2026)

> **Status:** Test-only Integrationskandidat; keine Freigabe für `main` oder Live. Gültigkeit ausschließlich für den in GitHub Actions geprüften PR-Head und die dort veröffentlichten Artefakte.

## Warum ein gemeinsamer Lauf?

Die opt-in Produktimplementierung P8 liegt separat als Draft [#322](https://github.com/Kayus24/kgg/pull/322). Vier voneinander unabhängige, bereits auf ihren jeweiligen SHAs vollständig CI-grüne **Test-only** Draft-PRs [#324](https://github.com/Kayus24/kgg/pull/324), [#325](https://github.com/Kayus24/kgg/pull/325), [#326](https://github.com/Kayus24/kgg/pull/326) und [#327](https://github.com/Kayus24/kgg/pull/327) decken weitere spezifische Funktionen ab. Einzelne grüne Läufe beweisen aber nicht, dass alle Testwerkzeuge auf **demselben** Kandidatenstand kompatibel sind.

Dieser Integrationszweig übernimmt nur die fünf vorhandenen, getesteten JS-Testdateien aus den Kind-PRs (Git-Blob-Wiederverwendung). Ein neuer, streng prüfender Aggregator führt exakt dieselben Tests zusammen; die vier separaten Workflow-Dateien werden **nicht** dupliziert. Es gibt **keinen Produktcode-Patch** gegenüber P8 #322.

## Umfang der zehn verpflichtenden Browser-Suite-Nachweise

| Suite | Vorhandene Testquelle | Drei Modi je Browser | Manifest (nur Teilabdeckung) |
|---|---|---|---|
| Settings / Seitenwerte | `kgg_patient_settings_side_parity_playwright.js` (#324) | Legacy / P7 / P8 | PAT-SETTINGS-001, 002; PAT-UNIT-007 |
| Progressionsstufen | `kgg_ticket_015_browser_smoke.js` (#325) | Legacy / P7 / P8 | PAT-PROGRESSION-001, 002 |
| Scanner-Fallbacks | `kgg_patient_scan_fallback_parity_playwright.js` (#326) | Legacy / P7 / P8 | PAT-SCAN-001, 003, 004 |
| PWA First-Load & Bilder | `kgg_patient_preview_first_load_smoke.js` (#327) | Legacy / P7 / P8 | PAT-PWA-002, PAT-THUMB-001, PAT-MEDIA-009 |
| NumPad / Pixel / Video | `kgg_patient_ui_parity_capture.js` (#322) | Legacy / P7 / P8 (Phone + Tablet) | P8-UI-Gegenkontrolle, keine zusätzliche Feature-ID |

Für jede der fünf Suiten laufen Chromium und WebKit: **10 unabhängige, SHA-gebundene Ergebnissätze**. Alle benötigten Modi, vereinbarten Feldprüfungen, Dateinachweise, Pixelvergleiche, Quell-SHAs und Browserzuordnungen sind Pflicht. Ein fehlender, übersprungener, falscher oder veralteter Nachweis führt **nicht** zu PASS. `release-pipeline/kgg_patient_react_combined_gate.mjs` prüft auch selbst negative Fälle (falsche SHA, Fehlstatus, fehlende Datei).

Das GitHub-Workflow-Artefakt `combined-acceptance.json` wird nur nach Bestehen aller Prüfungen erstellt. Sein Status `AUTOMATED_SCOPE_PASS_DEVICE_PENDING` bedeutet **ausschließlich** den beschriebenen synthetischen Teilumfang. Das Gate setzt ausdrücklich `manualAcceptancePending=true`, `all111FeaturesAccepted=false` und `realDeviceAccepted=false`.

## Bewusste Grenzen

- **Kein echter Kamera-/Foto-/QR-Betrieb** auf iPhone/iOS-Chrome, Safari oder Oppo/Android-Chrome. Die Scanner-Teststrecke simuliert verweigerte Kameraberechtigung und Planlinks.
- Keine reale PWA-Offline-, Cache-Update-, Service-Worker-Recovery- oder Installationsabnahme.
- Keine gesicherte Flackerfreiheit auf physischen Geräten. Issue [#308](https://github.com/Kayus24/kgg/issues/308) zur Video-Grauframe-Frage bleibt offen.
- Nicht sämtliche 111 Patientenfunktionen. **Elf IDs** erhalten hier nur einen direkt testgestützten, teils unvollständigen Vergleich. Das ältere Manifest-Inventar (52/111 teilweise zugeordnet) ist weiterhin auf der anderen, ungemergten QA-Kette #319/#320 und darf nicht ungeprüft additiv als vollständiges PASS ausgegeben werden.
- Keine Konfliktauflösung oder Zusammenführung der älteren #309–#320-Testkette, keine Hauptbranch-/Release-Aktion.

## Sicherer Review- und Wiederaufnahmepunkt

1. Aktuelle SHAs von `main`, P8 #322 und diesem Test-Integrationszweig lesen.
2. Das GitHub-Gate **`Unified automatic scope gate (device approval pending)`** sowie Browser- und Build-/Required-Gates auf exakt dem PR-Head prüfen.
3. Aus `combined-acceptance.json` zehn Belege, SHA, 11 scoped IDs und explizit ausstehende Realgeräteabnahme kontrollieren. Videos aus den kurzlebigen Chromium-/WebKit-Artefakten gegenüberstellen.
4. Bei einem roten Job **nur den konkreten Fehler** untersuchen; nie eine alte grüne SHA auf einen neuen Commit übertragen oder Tests blind wiederholen.
5. Draft belassen, bis eine ausdrückliche Entscheidung über reales Gerätegate und gesamte Produktmigration vorliegt.
