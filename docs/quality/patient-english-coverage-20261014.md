# Patienten-App: vollständiger Englischmodus – Inventur und Abnahme

Stand: 2026-10-14. Verantwortlicher Produkt-/Test-Worker: `patient_english_implementation`.
Auftrag: alle Patienten-Bedienelemente auf Englisch anzeigen und englische
Übungsanzeigenamen verwenden, während kanonische gespeicherte und über QR
übertragene Namen unverändert bleiben. Dies ist die einzige Inventur-/Planablage
dieses Workstreams; Browser- und Katalogbefunde werden hier ergänzt.

## Basis und Grenzen

- Worktree: `C:/src/kgg-worktrees/patient-english-complete-20261014`.
- Branch: `fix/patient-english-complete-20261014`.
- Fresh `origin/main`, Base SHA: `f59bc55e6e22e1b04061557c710069f6cf8f0b21`.
- Patienten-Quellversion: v90 (`patient-version-label.js`, `service-worker.js`).
- Vorläufig reservierte Zielversion: v93; vor Umsetzung nochmals abgleichen.
- Native Worktree-Erstellung scheiterte mit `Not a git repository`; anschließend
  autorisierten Git-Worktree-Fallback erstellt. Hook Guard install/check: PASS.
- Ausführung: PC, CLI und isolierte synthetische Daten. Der Worker verwendet kein
  CUA und keinen gemeinsam genutzten Browser. Gesamt-Abnahme bleibt beim Lead.
- Patienten-Anzeige, entsprechende Tests und Versions-/Cachemarker sind erlaubt.
  Keine Layout-, Parser-, QR-Version-, Plan-State-Refactor- oder Androidänderung.
  Autorisiert ist das kleinste Englischfeld im Therapeuteneditor samt Bankpersistenz
  und optionaler Anzeige-Metadata im bestehenden Plancontainer. React-Scope umfasst ausschließlich notwendige Texte in
  `patient-ui/src/legacy-numpad/LegacyNumpadHeader.tsx` und den erforderlichen Build
  nach `patient-react-dist`.
- Phase 1 abgeschlossen. GO für Patienten-UI/Standardkatalog und React nach Cloud-Planrevision2;
  GO für explizites Therapeuten-Englischfeld/Metadata nach Cloud-Planrevision3 (PASS).
  Patienten-Kandidat v93, Therapeuten-Sourcekandidat v96; kein Merge/Release autorisiert.

Parallel geprüft: PR #306 verändert `patient-pain-vertical-scale.js`, index/SW und
Schmerztests; #309/#311 erweitern Legacy/React-Abnahme; #214 Vorwert-Schimmer.
Separater Importwerte-Worker hat inzwischen PR #321 als Draft mit v92, normaler
FullRegression-Zertifizierung PASS und noch separat zu prüfender Remote-CI. Seine
Produktänderungen sind hier nicht integriert. Nur die unabhängig geprüfte
Testharness-Revision aed8d33 wurde als eigener Commit 01e9c4e wiederverwendet.
Keine Scanneränderung übernommen; spätere Produktintegration bleibt beim Lead.

## Search-first / vorhandene Lösungen

Die aktive Quelle, vorhandene Tests und genaue Kataloge wurden zuerst geprüft.
Wiederverwendung: Sprache in `kggPatientLang`, vorhandene DE/EN-Textpaare und
Einheitenübersetzung, Legacy-DOM-Verträge und die vorhandenen Playwright-Tests.
Es gibt keine öffentliche gemeinsame i18n-API; Module lesen denselben Sprachkey
über lokale Helper. Kein neuer Framework-/Übersetzungsdienst oder Dependency.

Übungsquellen sind die 18 Einträge in
`kgg-update/src/runtime/app-core.html` und die identische feste Cockpit-Registry
in `kgg-update/src/patches/v082-therapy-cockpit.html`. Die Patientendaten führen
den Übungsnamen unter KGGH2/3 `e[0]`, später `p.ex[].n`. KGGH2 überträgt keine
Bank-ID; `exObj()` übernimmt weder eine stabile ID noch ein explizites EN-Feld.
`patient-exercise-media-sources.js` besitzt zehn genau benannte Medienfamilien
mit vorhandenen EN-Aliasnamen. Diese Namen werden als Orientierung wiederverwendet;
Medienzuordnung und Lizenz-/Attributionsdaten bleiben unverändert.

Nutzerentscheidung bestätigt: englische Bezeichnung freier/eigener Übungen wird
in der Therapeuten-App bei der Übung gepflegt. Umsetzung: optionales `nameEn`
im bestehenden Editor/Bankpfad; optionaler exakter Name→EN-Map unter
`m.exerciseNamesEn`. Kein neues QR-Präfix/Version/Schema und kein Eingriff in
`e[0]` oder belegte Tuple-Slots11–13. Leere Übersetzungen bleiben ausdrücklich
unvollständige Abdeckung. Widersprüchliche EN-Bezeichnungen derselben exakten
DE-Identität blockieren den Export verständlich.
Keine unscharfe Zuordnung eigener Namen zu ähnlich klingenden Bankübungen.
Patienten-/Therapeutennotizen und frei vergebene Plantitel bleiben Quellinhalt.

Die fachlich kritische Identität `deadlift`/Cockpit `0H` bedeutet im konkreten
Repo **Wadenheben**, daher EN **Calf Raise**, nicht Deadlift. Übersetzungen werden
gegen konkrete kanonische Namen und geprüfte exakte Aliase festgelegt.

## Ursachen und i18n-Flächen

Sprachwechsel in `collapse-cards.js` aktualisiert nur dessen lokale Flächen.
Die meisten anderen Module übersetzen erst bei ihrem eigenen Render-/apply-
Aufruf. `patient-card-settings.i18n()` übersetzt Metadaten, Units, Set- und
Seitenlabels, aber keinen Karten-Übungsnamen. Sein `patchText()` erzeugt erneut
deutsche Summarytexte. `rows()` exportiert direkt `e.n`; dieser Datenpfad bleibt
von Anzeigeübersetzung getrennt und unverändert.

| Quelle / vorhandener Ansatz | Flächen und notwendige Abdeckung |
| --- | --- |
| `index.html`, `dayPlanMeta()` | Start, Laden/Wiederherstellen/Speichern/Fehler, Titel-Fallback, Tage/Verlängerung, Karten, NumPad, QR-/Copy-Texte, Abschluss, Summary, Installbox |
| `collapse-cards.js`, `la()/tr()` | Sprachschalter, Chrome, Collapse-/Progresslabels, Sprachwechsel-Veröffentlichung |
| `patient-card-settings.js`, `en()/T()/unit()` | Kartenanzeigename/-metadaten, Sätze/Seiten, Einheiten, offene Einstellungen samt Optionen/Aktionen; Summary nur Anzeige |
| `patient-day-history.js`, `en()/T()` | Taghub, offene Historie, Übungsnamen darin, Planwahl und aktuelle/offene/fertige Zustände |
| `patient-start-scan.js`, `lang()/tr()` | Empty-/Rescue-Start, Update/Ersetzen, Kamera-/Foto-/Paste-Dialog, Scanner-/Permission-/Validierungsfehler und ARIA; Import bleibt gleich |
| `patient-multiplan-db.js`, `isEn()/t()` | Datenbankknopf/-Dialog, genaue Übungsnamen, Planaktionen/FAB/-Bubbles, weitere Pläne |
| `patient-plan-link-choice.js` | Eingang eines zweiten Plans: hinzufügen/ersetzen/abbrechen, Vergleichskarten und Fallbacks |
| `patient-plan-delete.js`, `isEn()` | Plan löschen/umbenennen, Auswahl/-Warnungen, Bestätigung und Status |
| `patient-plan-replace-slot-fix.js`, `isEnglish()` | Nummerierte Planhinzufügung, Scan-Bubble/Status; bestehende Slots gleich |
| `patient-install-guide.js`, `patient-install-prompt.js` | Install-Angebot/-Hinweis, Plattformhinweise und installierte Zustände |
| `patient-version-label.js` | Versions-ARIA, Updatebanner, später/jetzt, Eingabegate, aktivieren/Retry/Fehler |
| `patient-start-values-day1.js` | Vorbefüllungsstatus; Werte gleich |
| `patient-last-value-hints.js` | Vorwert übernehmen/kein Vorwert, Units; Draft und Transfer gleich |
| `patient-set-compact-view.js`, `en()` | Compact-/Classic-Labels, Neu-Badge, Pair-/Transferlabels und ARIA |
| `patient-ui-micro-polish.js` | NumPad-, Unit-/Pain-Labels; bestehende Geometrie gleich |
| `patient-pain-vertical-scale.js` | Übungs-/Satzschmerz, offene Skala, Endpunkte und ARIA |
| `patient-set-summary-groups.js` | Set-Range, Progressions-/Info-Systemlabels; Notizen und Progressionsdaten gleich |
| `patient-extra-info-display.js` | Info-Systemprefix; freie Notizen unverändert |
| `patient-media-retry-cache_v2.js` | Bild-/Video-Systemlabels und ARIA; Medien-/Uploadlogik gleich |
| `patient-qr-fullscreen.js` | Vollbild-/Schließen-/QR-ARIA; Payload gleich |
| React `LegacyNumpadHeader.tsx` | Hardcoded Neu, Werteingabe, Aktives Wertefeld und Fallback Wert; Pair/Transfer beziehen bereits Legacy-DOM-Labels |

## Kleinster geplanter Patch

1. Einen kleinen gemeinsamen display-only Helper in `patient-i18n.js` aus den
   vorhandenen Textpaaren und geprüften Namensquellen bereitstellen. Kein Write
   auf `p.ex[].n`, keine Displaywerte als Inputs für Speicher/QR/Identity.
2. Genau die direkten Patienten-Textquellen auf diesen Helper anwenden. Beim
   vorhandenen Sprachwechsel ein gemeinsames Ereignis veröffentlichen. Offene
   Flächen aktualisieren, ohne Dialogzustände/Eingabedrafts neu aufzubauen oder
   bestehende Hooks zu entfernen. Geprüfte Namen zentral bei Anzeige anwenden.
3. Notwendige React-Texte am Quellort übersetzen und mit unverändertem Build
   exportieren. Keine Layout-/Controlleränderung.
4. Neue Zielversion/Modulmarker und Service-Worker-Asset-Liste konsistent setzen,
   damit vorheriger Cache und Offline-Nutzung die Anzeige erhalten.
5. Vor Änderungen reale RED-Reproduktion und danach fokussierte GREEN-Flows,
   Pflichtgates und unabhängige Lead-Browserabnahme.

## Eingefrorene Abnahmekriterien

| ID | Nachweis / PASS-Bedingung |
| --- | --- |
| EN-01 | Strukturabgleich mit der gesamten aktiven 18er-Bank; jeder kanonische Name und jeder explizit geprüfte Alias besitzt passenden englischen Anzeigenamen. Zusätzliche Medienfamilien separat genau abgedeckt. |
| EN-02 | Keine deutschen Systemtexte/ARIA/Title/Placeholder in English UI in echten Start-, Karte-, NumPad-, Pain-, History-, Summary-, Settings-, DB-, Install-, Update-, Info-, Planaktionen-, Scan- und Return-QR-Flows. |
| EN-03 | DE→EN→DE ohne Reload, auch für bereits offene Dialoge und dynamische Status/Fehler; Draft, aktive Eingabe, aktueller Tag und Dialogzustand gleich. |
| EN-04 | Legacy und React Opt-in getrennt durch reale Bedienung geprüft; Übersetzungslabels der Pair-/Transfersteuerung und React-ARIA stimmen. |
| EN-05 | Snapshot vor/nach Sprache/Reload: Plan/Übungsidentität und relevanter Speicher bytegleich, wo Format stabil ist, sonst semantisch gleich; nur Sprachpreferenz darf sich ändern. Keine englischen Anzeigenamen in kanonischen Namen. |
| EN-06 | Zwischen- und Abschluss-KGGD1 behalten deutsche kanonische Namen; Payload vor/nach Sprachwechsel identisch bei gleichen Werten/Tag. Summary zeigt Englisch ausschließlich als Anzeige. |
| EN-07 | KGGH2 und KGGH3 importieren dieselbe vollständige synthetische Struktur unverändert; Medien, zusätzliche Felder, Werte, Sets/Seiten/Units, Progression und Plan-Slots bleiben erhalten. |
| EN-08 | Reload hält English UI und kanonische Daten; offline cold reload nach Cacheaufbau ebenso. Separater alter Cache→neue Version-Aufbau beweist Updatepfad und neue Textressourcen. |
| EN-09 | Pflichtgates: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical` und `cmd /c release-pipeline\run-kgg-tests.cmd --suite ui-stability --level regression`. Benannte unabhängige Baselinefehler offen reporten. |
| EN-10 | Freie/benutzerdefinierte Übungsnamen nicht als fertig zählen, bis Nutzerentscheidung und tatsächliche englische Anzeige nachgewiesen sind. |

Fokussierte vorhandene Tests: `kgg_patient_summary_smoke.js`,
`kgg_patient_card_progress_smoke.js`, `kgg_patient_set_view_adaptive_smoke.js`,
`kgg_patient_unit_semantics_playwright.js`, `kgg_patient_continuous_days_playwright.js`,
`kgg_patient_per_set_pain_playwright.js`, `kgg_patient_react_numpad_header_playwright.js`,
`kgg_patient_plan_link_choice_smoke.js`, `kgg_patient_scan_format_smoke.js`,
`kgg_patient_install_capability_playwright.js`, `kgg_pwa_contract_smoke.py`.
Neue Abnahmetests prüfen reales Verhalten und Katalogvollständigkeit, keine reine
Stringliste. Vor Produktpatch relevante RED-Nachweise festhalten.

## Phase-1-Evidenz und Vorschau

Preview: `http://127.0.0.1:8873/`, eigener Python-HTTP-Server, nur Loopback.
Synthetischer Plan: ID `english-coverage-synthetic-20261014`, Titel
`English coverage test`, sechs Tage, Kniebeuge (B,3,kg/Wdh,15/12), Rudern
(LR,3,kg/Wdh,20/10), Beinpresse (B,3,kg/Wdh,40/12), Plank
(B,1,keine/Sek.,30 sec). Keine Patientendaten.

Bedienstart: den vom Lead geteilten KGGH2-Link in frischem Kontext öffnen,
`DE ▸ EN` klicken, Karte am Titel öffnen, Werte/Tag2/History prüfen. Opt-in:
`&kggReactPad=1`, Legacy: `&kggReactPad=0`.

Headless Chromium Baseline: Sprachschalter geklickt, vier Kartenüberschriften
weiter deutsch/Plank; `Startwerte übernommen.` blieb deutsch. Root-lang/meta
blieben ebenfalls deutsch. Planstate und `kggCurrentPlanV1` waren beim Wechsel
bytegleich; keine pageerrors. Diese reproduzierbaren Lücken sind RED,
keine Abschlussabnahme.

Critical-Baseline wurde vor Produktarbeit kontrolliert unterbrochen (Exit1);
unvollständiger Lauf und kein Produkt-PASS/FAIL. Finalpflichtgates stehen nach
Aux-DONE und vollständigem Kandidaten aus. Vollständige separate Browserinventur und geprüfte
Katalogtabelle und gesamte Browserinventur sind im Arbeitsstand erfasst.
Produktänderungen sind nach den bestätigten GOs in Umsetzung.


### Verifizierte Hash-Importlinks (ohne Prompt)

- [normal](http://127.0.0.1:8873/?kggReactPad=0#KGGH2:eyJpIjoiZW5nbGlzaC1jb3ZlcmFnZS1zeW50aGV0aWMtMjAyNjEwMTQiLCJ0IjoiRW5nbGlzaCBjb3ZlcmFnZSB0ZXN0IiwidiI6MSwiZCI6NiwiZSI6W1siS25pZWJldWdlIiwzLCJCIiwia2ciLCJXZGgiLCIxNSIsIjEyIl0sWyJSdWRlcm4iLDMsIkxSIiwia2ciLCJXZGgiLCIyMCIsIjEwIl0sWyJCZWlucHJlc3NlIiwzLCJCIiwia2ciLCJXZGgiLCI0MCIsIjEyIl0sWyJQbGFuayIsMSwiQiIsImtlaW5lIiwiU2VrLiIsIiIsIjMwIl1dfQ)
- [second](http://127.0.0.1:8873/?kggReactPad=0#KGGH2:eyJpIjoiZW5nbGlzaC1zZWNvbmQtc3ludGhldGljIiwidCI6IlNlY29uZCBzeW50aGV0aWMgcGxhbiIsInYiOjEsImQiOjYsImUiOltbIkVpZ2VuZSBUZXN0dWVidW5nIiwxLCJCIiwia2ciLCJXZGgiLCIiLCIiLFtdLCIiLCIiLCJleGVyY2lzZSIsIlVudmVyYWVuZGVydGUgZGV1dHNjaGUgQmVudXR6ZXJub3RpeiJdXX0)
- [progression](http://127.0.0.1:8873/?kggReactPad=0#KGGH2:eyJpIjoiZW5nbGlzaC1wcm9ncmVzc2lvbnMtc3ludGhldGljIiwidCI6IlN5bnRoZXRpYyBwcm9ncmVzc2lvbiIsInYiOjEsImQiOjYsImUiOltbIktuaWViZXVnZSIsMiwiQiIsImtnIiwiV2RoIiwiIiwiIixbXSwiIiwiIiwiZXhlcmNpc2UiLHsiZyI6InN5bnRoZXRpYy1ncm91cCIsImEiOiJiYXNlIiwidiI6W3siaSI6ImVhc3kiLCJuIjoiTGVpY2h0ZXIiLCJvIjowLCJzIjoiIiwibSI6W3siaWQiOiJlYXN5LW1lZGlhIiwidHlwZSI6ImltYWdlIiwic3JjIjoiZGF0YTppbWFnZS9zdmcreG1sLCUzQ3N2ZyUyMHhtbG5zJTNEJTIyaHR0cCUzQSUyRiUyRnd3dy53My5vcmclMkYyMDAwJTJGc3ZnJTIyJTIwd2lkdGglM0QlMjIxMjAlMjIlMjBoZWlnaHQlM0QlMjI4MCUyMiUzRSUzQ3JlY3QlMjB3aWR0aCUzRCUyMjEyMCUyMiUyMGhlaWdodCUzRCUyMjgwJTIyJTIwZmlsbCUzRCUyMiUyM2RiZWFmZSUyMiUyRiUzRSUzQ2NpcmNsZSUyMGN4JTNEJTIyNjAlMjIlMjBjeSUzRCUyMjQwJTIyJTIwciUzRCUyMjIyJTIyJTIwZmlsbCUzRCUyMiUyMzI1NjNlYiUyMiUyRiUzRSUzQyUyRnN2ZyUzRSJ9XX0seyJpIjoiYmFzZSIsIm4iOiJCYXNpcyIsIm8iOjEsInMiOiIiLCJtIjpbeyJpZCI6ImJhc2UtbWVkaWEiLCJ0eXBlIjoiaW1hZ2UiLCJzcmMiOiJkYXRhOmltYWdlL3N2Zyt4bWwsJTNDc3ZnJTIweG1sbnMlM0QlMjJodHRwJTNBJTJGJTJGd3d3LnczLm9yZyUyRjIwMDAlMkZzdmclMjIlMjB3aWR0aCUzRCUyMjEyMCUyMiUyMGhlaWdodCUzRCUyMjgwJTIyJTNFJTNDcmVjdCUyMHdpZHRoJTNEJTIyMTIwJTIyJTIwaGVpZ2h0JTNEJTIyODAlMjIlMjBmaWxsJTNEJTIyJTIzZGJlYWZlJTIyJTJGJTNFJTNDY2lyY2xlJTIwY3glM0QlMjI2MCUyMiUyMGN5JTNEJTIyNDAlMjIlMjByJTNEJTIyMjIlMjIlMjBmaWxsJTNEJTIyJTIzMjU2M2ViJTIyJTJGJTNFJTNDJTJGc3ZnJTNFIn1dfSx7ImkiOiJoYXJkIiwibiI6IlNjaHdlcmVyIiwibyI6MiwicyI6IiIsIm0iOlt7ImlkIjoiaGFyZC1tZWRpYSIsInR5cGUiOiJpbWFnZSIsInNyYyI6ImRhdGE6aW1hZ2Uvc3ZnK3htbCwlM0NzdmclMjB4bWxucyUzRCUyMmh0dHAlM0ElMkYlMkZ3d3cudzMub3JnJTJGMjAwMCUyRnN2ZyUyMiUyMHdpZHRoJTNEJTIyMTIwJTIyJTIwaGVpZ2h0JTNEJTIyODAlMjIlM0UlM0NyZWN0JTIwd2lkdGglM0QlMjIxMjAlMjIlMjBoZWlnaHQlM0QlMjI4MCUyMiUyMGZpbGwlM0QlMjIlMjNkYmVhZmUlMjIlMkYlM0UlM0NjaXJjbGUlMjBjeCUzRCUyMjYwJTIyJTIwY3klM0QlMjI0MCUyMiUyMHIlM0QlMjIyMiUyMiUyMGZpbGwlM0QlMjIlMjMyNTYzZWIlMjIlMkYlM0UlM0MlMkZzdmclM0UifV19XX0sIlVudmVyYWVuZGVydGUgUHJvZ3Jlc3Npb25zbm90aXoiXV19)

CLI Headless: [{"fixture":"normal","names":["Kniebeuge","Rudern","Beinpresse","Plank"],"rawExact":true},{"fixture":"second","names":["Eigene Testuebung"],"rawExact":true},{"fixture":"progression","names":["Kniebeuge"],"rawExact":true}]

Alte Patienten-App mit optionalem `m.exerciseNamesEn`: {"rawExact":true,"metadata":{"source":"kgg-therapist-app","schema":"KGGH2","media":{"expected":false,"count":0,"ready":0,"status":"none"},"exerciseNamesEn":{"Eigene Testuebung":"My Test Exercise"}},"qrName":"Eigene Testuebung","cardName":"Eigene Testuebung"}


### Baseline optional EN-Metadata compatibility

{"status":"PASS","stages":["import","saveCurrentSlot","reload","planSwitchAwayAndBack"],"metadataByteEqual":true,"canonicalName":"Eigene Testuebung","noteUnchanged":true,"outboundQrNames":["Eigene Testuebung"]}


## Wiederanlauf-Checkpoint

Runtime-Unterbrechung: Teilpatch erhalten; Vorschauprozess nicht mehr vorhanden,
Port8873 geprüft frei und eigener Hidden-HTTP-Server erneut gestartet. Keine
Doppelvergabe/Modelländerung. Helper/Core/Karten/Summary/Compact/Versionsmarker
sind Teiländerungen; Therapie-Englischfeld, React-Build, vollständige Directstrings
und Finalgates sind noch offen. Sechs Aux-Dateien bleiben ausschließlich beim
separaten Writer: day-history, plan-delete, plan-link-choice, install-guide,
install-prompt und qr-fullscreen. Nächste Aktion: gezielter Katalog-GREEN, danach
Therapie-Editor/Metadata RED→GREEN und React-Lokalisierung.

Metadata-Basispfade: `app-core.html` compactTuple4531, buildKggH2Payload4545
(m4562), H3Wrap4576; `patient-qr-format.js` validatePlan44/m54;
`patient-multiplan-db.js` rawFromRuntime43 klont base inkl m, saveCurrentSlot51
und switchTo54. Slot11 Progression in patient-set-summary-groups166/198;
ExtraInfo-Strings11–13 in patient-extra-info-display11 bleiben erhalten.


## Candidate Freeze 1

Product source candidates: Patient v93 / Therapist v96. Existing builds completed;
no-release scope uses the documented KGG_ALLOW_RELEASE_DRIFT=1 and future PR
label kgg-no-release. This does not authorize merge/release and skips no other
test/hook. Fresh main remains f59bc55.

Aux work accepted: five localized files; install-prompt unchanged. Scoped
existing plan-delete/install-prompt/link-choice/continuous-days smokes and Aux
open-dialog/history/install/fullscreen contract evidence PASS, independently
reported by Lead. No Aux writer remains.

Own GREEN: complete active bank18+additional12 Legacy/React catalog and immutable
plan/raw/values/day snapshots; real settings/NumPad/commit/QR/summary/reload flow;
open-settings language trigger is scripted onclick because existing backdrop
blocks physical access, not a new layout path. React build, therapist build, PWA
contract, summary smoke, exact EN metadata/conflicting export smoke PASS.
Editor full export flow, author-content negative test, cache/offline transitions
and required gates remain INCOMPLETE at this freeze.

Frozen product SHA256 records:

```json
[
  {
    "file": "collapse-cards.js",
    "sha256": "ac8afec81349ecb3ae8d9b5dd9fd9a39c476d4dedc7148907939ebd4fae8aafc"
  },
  {
    "file": "index.html",
    "sha256": "6088380652ce6cd99471b533680b2a5abf11ff245d394bcdab842c170548ca71"
  },
  {
    "file": "kgg-update/index.html",
    "sha256": "d9f23c7f95442e67dd0523a88646af1092116edc301cf8d636c1fbe40256ad56"
  },
  {
    "file": "kgg-update/src/document/body-shell.html",
    "sha256": "52fc54134ed60677b787d798a1caf21f86215f17f467bad532e52f2e9236cc80"
  },
  {
    "file": "kgg-update/src/document/head-ui.html",
    "sha256": "c74cca199993b498cbb9d50de132c1fa5dd5a0f89b1e468165b54e7cc18fd9bb"
  },
  {
    "file": "kgg-update/src/patches/v085-ticket-015-progressions.html",
    "sha256": "5ed33aea25819a0d85247a68fa36bf262864dd07015337c4c4a801cf3dfcc480"
  },
  {
    "file": "kgg-update/src/runtime/app-core.html",
    "sha256": "9f0d9ba575d2bc30ff721c3d06b97f1bffda9e1bd68dde8e1df750c99dbdb601"
  },
  {
    "file": "kgg-update/version.json",
    "sha256": "e423cdd80e631b76c1af2f14514b8ff9973167d2405544633539aff02675a027"
  },
  {
    "file": "patient-card-settings.js",
    "sha256": "1956801d44b1d1c4470187ebc66474df92cc456bf1e6d2ea9bda92c026fa7901"
  },
  {
    "file": "patient-day-history.js",
    "sha256": "2e904b1b6578aef5a7fccc5128bc633c5367c966b4eb5dd484e79a98bdf7661e"
  },
  {
    "file": "patient-install-guide.js",
    "sha256": "11d2fb9edd3f290a4f75bd7a1526daee53faa55bccbe041129f3f04fdf729e86"
  },
  {
    "file": "patient-last-value-hints.js",
    "sha256": "879131abf73d0e66234abe33670c43e9eb963a1371527262db617ee1a817d685"
  },
  {
    "file": "patient-media-retry-cache_v2.js",
    "sha256": "1ae19634aa7973dbe1546333b7d2e6d0138e04e175290ce2e11310092a4651ca"
  },
  {
    "file": "patient-multiplan-db.js",
    "sha256": "509b74e641eb5159a6ba3b0ff1e23f45ff1932088901e76b533cc4ded5b78122"
  },
  {
    "file": "patient-plan-delete.js",
    "sha256": "2b37629bfbabb202e04c04cec8f6a883c173343411a4c57814771b9fb5b43ad7"
  },
  {
    "file": "patient-plan-link-choice.js",
    "sha256": "19e7edb65e02717b8e36f0062e6422b0bffb3b4e9987e4b31638fb7cea2d0917"
  },
  {
    "file": "patient-qr-fullscreen.js",
    "sha256": "a9245be9a5bbc7d1582b42a587b7de72d4261b9f6946dd196edb74992b3e23dc"
  },
  {
    "file": "patient-react-dist/kgg-patient-ui.js",
    "sha256": "57d37fa3dacfddcd1050b7507436ba5f3499d8eaa678cedcce87f8054161c9f8"
  },
  {
    "file": "patient-set-compact-view.js",
    "sha256": "b9a7218388913774d7d151cced14a29522ebcc6f95dd8bad50b96f2d50a4e533"
  },
  {
    "file": "patient-set-summary-groups.js",
    "sha256": "44d9c793c4967940604f486270bec970409b9625fc93a642f5e9166eaeaf8c5b"
  },
  {
    "file": "patient-ui-micro-polish.js",
    "sha256": "5bce46af62a0b793da0a850121429c704ac8294150aea0c1fcd148e3eda767a2"
  },
  {
    "file": "patient-ui/src/legacy-numpad/LegacyNumpadHeader.tsx",
    "sha256": "16c2b4870d35d165dd7ec2f6d8fe74ca6e8dbd087a37afd4b99fb62b49bfae78"
  },
  {
    "file": "patient-version-label.js",
    "sha256": "8aacac7fc3e25380200e5bef46d7055b421cfe6189a8af8116bc759b540187b3"
  },
  {
    "file": "service-worker.js",
    "sha256": "e7c4c785995340d7be2eebce8bae924c00deb7756d01231338d15f76a9cf9469"
  },
  {
    "file": "update-recovery.html",
    "sha256": "6f57568a48f65daaf63492d4c7098a76171dbe55bb8ca9b51a2fde6e3fcb11e3"
  },
  {
    "file": "patient-i18n.js",
    "sha256": "c0b5a81dc8d7245389960ecdd2bac894ae328982a39c2c92ec272f97966cf935"
  }
]
```


### Aktueller Checkpoint nach unabhängigem Review (Freeze1 zurückgewiesen)

Freeze1 wurde vom unabhängigen Code-Review über Start-/Endhashes 26/26 unverändert geprüft: 0 Critical, 6 Important, 1 Minor. Zusätzlich zwei echte Browserbefunde (Dokumenttitel, offenes Replace-Menü). Freeze1 ist **REJECTED / keine Gesamtfreigabe**. Important: Installbox DE; Shared-Bank explizite EN-Leerung verloren; tatsächliche numerische Statusformen; frei benannte Basis/Leichter/Schwerer im allgemeinen Katalog; authored EN-Summaryname nachlaufend verändert; EN-DB-Suche. Minor: Pad-Unit bei EN→DE. Receiving-code-review angewandt; alle Befunde am tatsächlichen Code geprüft.

Der vollständige Critical-Versuch auf Freeze1 endete **FAIL**, 141 Release-Unittests, 3 Failures/4 Errors/1 Skip: VERSION marker vs kgg-source-truth, embedded changelog vs version.json, patientProduction Knowledge digest während noch unvollständigem Ressourcenrefresh. Kein nachfolgender Funktionsgate dieses Laufs als PASS ausgegeben. Notwendige v96 Source-/Changelog-Nachweise werden über bestehende Quellen/Generatoren korrigiert; Manifest/live release bleibt unverändert. No-Release-Drift ausschließlich dokumentiertes KGG_ALLOW_RELEASE_DRIFT=1, keine anderen Gate-Skips.

Reparaturen laufen nach Root-GO. Targeted Review-Playwright reproduzierte neun rote Verhaltenstests und wurde danach GREEN für Installbox/Titel/offenes Replace-Menü/freie Hauptübungsnamen/authored Summarynamen/numerische Statusformen/EN-Suche/Pad-Rückwechsel. SharedBank Sender→Empfänger VM RED→GREEN: absent Legacy erhält Label, explizit leer clears; deutsche Namen/Einheiten unverändert.

Neuer read-only Detailreview identifizierte aktive Overrides: v090 Gallery ersetzt den v085-Editor-Draft/DOM; v093 besitzt separate Cockpit-Variantenfelder; v082 entfernt Haupt-/Varianten-nameEn in cleaner/updateSlot, bezieht ganze progressionVariants in contentKey ein, und dispatchPlanHook übernimmt EN nicht. v085-only Variantentest war RED (aktiver Button existiert nicht), anschließend korrekte aktive Pfade freigegeben. Das einfache echte Editor Save→Reload→Bank→Plan→Patientlink→EN→DE ReturnQR war vorher PASS; Varianten/Umordnung/Mainwechsel/Cockpit noch INCOMPLETE.

Cloud-Erweiterungsplan für Variantenpflege und optionale Cockpit-x-Extras: PASS / Root GO. Bestehende x.ne für Haupt-nameEn und pv.nameEn für Varianten sind nur optional; Prefix/Schema/Checksum/Limits bleiben. Immutable alter v082-Reader aus HEAD liest hypothetische zusätzliche x.ne/pv.nameEn ohne Fehler, Namen Deutsch, zusätzliche Labels ignoriert: VM PASS. State-VM RED→GREEN: EN-Änderung/Löschung, syncSlot, Trainingswerte und EN-freier contentKey. Noch offen: new→new Wire Create/Edit/Clear, old→new Retain, echte active Gallery/Cockpit-Bedienung sowie finaler stabiler Critical/UI-Gate.

Basis/Leichter/Schwerer sind im tatsächlichen Varianteneditor frei authored Namen ohne Provenance; ohne explizites nameEn bleiben sie unverändert. Nur feste UI-Badges/Stufe N werden übersetzt. Bereits vorhandene '<Übung> – Stufe N' ohne sichere Provenance werden ebenfalls über ausdrücklich gepflegtes nameEn gelöst; keine globale Wortheuristik. Bekannte Bank, gepflegte Custom/Varianten und noch unübersetzte fremde Custom/Altvarianten werden in der Abnahme getrennt ausgewiesen.

Der eigene Varianten-Browserlauf wurde auf Root-Anweisung während der zeitkritischen QR-Ladder des Importfix-Chats sauber abgebrochen und ist kein PASS. CPU-Reservierung danach ausdrücklich freigegeben. Vorhandene geprüfte Testharness-Revision aed8d336795eac530622f86f780d47319861c6ce wird vor eigener Pflicht-Ladder getrennt wiederverwendet; keine neue Scannerdiagnose/CPU-Friständerung.

**Next actual action:** aktive Gallery-/Cockpit-Editorpfade und optionales Wire fertigstellen und gezielt prüfen; alle Generatoren danach aktualisieren; Freeze2 mit kompletten Hashes melden; erst stabilen Kandidaten vollständig zertifizieren. Keine Merge-/Releasefreigabe.


### Freeze2 — Produktstand zur unabhängigen Abnahme

Alle Produktdateien dieser Hashliste sind ab diesem Checkpoint eingefroren. Worker nimmt vor neuen Produktreparaturen den konkreten Pfad beim Lead zurück; kein laufender Aux-Writer. Base bleibt f59bc55e6e22e1b04061557c710069f6cf8f0b21. Separater wiederverwendeter Testcommit HEAD: 01e9c4e4c316752e90efb538c6fbb20adc856951. Patienten-App v93, Therapeuten-Source v96, released Manifest v95 unverändert, kein Release-Inbox/APK/Android.

**Focused PASS am Kandidaten:**
- `kgg_patient_english_playwright.js`: komplette tatsächliche 18er Bank + zusätzliche 12 Displaynamen, Legacy und React, canonical/raw/storage/values/day unverändert, Settings/NumPad/QR/Summary/Reload.
- `kgg_patient_english_review_playwright.js`: echte Installbox über kontrolliertes Browser-capability Event, Titel, offenes Replace, numerische Statusformen beide Richtungen, freie Haupt-/Stufennamen, authored EN-Summarysegment, englische DB-Suche, Pad-Unit-Rückwechsel. Backdrop-blockierter Sprachknopf in geöffnetem Modal ist als programmatischer Toggle-Contract gekennzeichnet; echte EN-Bedienung erfolgte nach normalem sichtbarem Toggle.
- `kgg_english_editor_playwright.js`: tatsächliches Bank-Gear und active v090 Gallery; EN anlegen/speichern/reload/explizit leeren/erneut pflegen, verknüpfte Bank-EN; reale Bank→Plan→Finish→KGGH3; deutsche g/a/v IDs und separate ENmap. Physischer Patient-Stage-next→NumPad2/OK→EN-Badge/dominante Überschrift/Summary→deutscher ReturnQR einschließlich Varianten-ID. Synthetisches verschlüsseltes SVG via bestehender IndexedDB-/Bundle-/Uploadadapter-Testgrenze, lokaler HTTP-Adapter; keine Produktmediaänderung. Öffentliche shareable Fixture-URL `.example` wird nicht besucht: erzeugte exakte Querybytes lokal importiert.
- `kgg_english_cockpit_playwright.js`: tatsächlicher v093 Editor, Haupt-/Stufen-EN ändern/leeren/reopen; linked A mit EN→B ohne EN löscht A-Label, eigenes Label bleibt; syncSlot→currentPlan; anderer Slot, Werte/contentKey unverändert.
- `kgg_english_metadata_smoke.js`: exakte DE Mapkeys; gültige ENlabels/Conflictstop; shared explicit Clear vs legacy absent; frischer Coretuple-Companion nutzt vorhandene wireVariants, noVariants bytegleich zur immutable Baseline, tuple0..10 gleich, DE g/a/v und gültiger Main-ID-Fallback.
- `kgg_english_cockpit_smoke.js`: fehlende EN-Properties erhalten baseline kodierte Bytes, new→new und immutable new→old inkl Checksum, Stringleerung, old→new Retain, 200-Zeichen-Grenze fail closed; beide EN-Felder vom contentKey ausgeschlossen.
- `kgg_patient_english_compatibility_playwright.js`: freie Notiz `Neu`/Credit `Wert eingeben` unverändert; Planswitch und DB-Copy active ENmap; realer no-camera/paste/error/recovery; tatsächlicher Serviceworker v90→v93 Update und offline cold reload.
- Bestehender Cockpit-Codec-Smoke, Summary-Range-Smoke, PWA-/Recovery-Contract, Encoding-/Hook Guard und scoped diffcheck PASS.

**Companion-Provenienz:** Immutable f59 reale Gallery→Bank→Plan vor Finish hat Varianten und echte wireVariants-Ausgabe, Patientlink enthielt slot11 nicht; globale Serializerbindungen fehlen wegen Core-IIFE. Ausgabeschluss leert currentPlan absichtlich via archiveAndCloseCurrentPlan; kein State-/Parserfehler. Enger Adapter-GO nach Cloud PASS und unabhängiger read-only Gegenprüfung: nur neu erzeugtes Coretuple um bestehende wireVariants plus gültiges a ergänzen. Kein alter Notizslot überschrieben/verschoben, keine Decoderänderung. Früherer künstlicher window-Serializer-Smoke ist kein Nachweis für den realen Pfad; das neue echte E2E schließt die Lücke.

**Generator-/CI-Freshness:** bestehende Therapist source build/check + changelog archive/check PASS. gpt_context, bug_knowledge, gpt_source_context, custom_gpt_knowledge_pack, patient_gpt_resources `--check` PASS; resource_audit TARGET_PASS. Nur Knowledge-Digests der bereits pending Editor-Targets aktualisiert, model/capabilities unverändert, kein Live-Sync behauptet. React-Build bleibt projektlokal mit vorhandenen pinned Dependencies/Lockfiles; generated JS, keine CSSänderung. KGG_ALLOW_RELEASE_DRIFT=1 genau im dokumentierten No-Release-Preview-Scope; Hygiene PASS.

**Offene Abnahme:** Root führt volle 14 Browser-Akzeptanzeinheiten inkl Legacy/React und unabhängigen affected Code-/Cloudreview aus. Danach erst normaler kompletter Commit-Hook (Critical plus UI regression) und ggf. autorisierte DraftPR mit kgg-no-release. Keine zweite volle Batterie vor demselben Hook ohne neuen Befund. Freeze1 FAIL bleibt oben historische Evidenz. Unübersetzte fremde frei benannte Custom/Altvarianten ohne gepflegtes nameEn bleiben absichtlich original und sind kein 'alle Übungen fertig'-Beleg. Bereits existierende freie Defaulttexte ohne sichere Provenance werden ausschließlich über explizite EN-Pflege gelöst.

Freeze2 ProductHashes (SHA256 tatsächlicher Arbeitsdateien):

```json
[
  {
    "file": "collapse-cards.js",
    "sha256": "ac8afec81349ecb3ae8d9b5dd9fd9a39c476d4dedc7148907939ebd4fae8aafc"
  },
  {
    "file": "index.html",
    "sha256": "6088380652ce6cd99471b533680b2a5abf11ff245d394bcdab842c170548ca71"
  },
  {
    "file": "kgg-update/index.html",
    "sha256": "d9e4edcda8afd4cdfc821b4e9d155483a726cec4e9c4603e4eeee4b94a0bf2d3"
  },
  {
    "file": "kgg-update/src/document/body-shell.html",
    "sha256": "52fc54134ed60677b787d798a1caf21f86215f17f467bad532e52f2e9236cc80"
  },
  {
    "file": "kgg-update/src/document/head-ui.html",
    "sha256": "c74cca199993b498cbb9d50de132c1fa5dd5a0f89b1e468165b54e7cc18fd9bb"
  },
  {
    "file": "kgg-update/src/metadata/changelog.html",
    "sha256": "a919cbbe18ba7d8015b561699e5a1e44cc153452c8583b9188bc5d0c26a17f27"
  },
  {
    "file": "kgg-update/src/metadata/source-truth.html",
    "sha256": "7fed7106b40c946e0f113edd221dc76c17f532ab5dc93a4b19a25624718b3a2d"
  },
  {
    "file": "kgg-update/src/patches/v082-therapy-cockpit.html",
    "sha256": "94564723f8d292cf9cf23a88da3076c7cf6393e47880a6c50b06bdc7836ac673"
  },
  {
    "file": "kgg-update/src/patches/v085-ticket-015-progressions.html",
    "sha256": "43ed681276dac3f5394d3e05880fca683c1d3cc6dd44f00c5c50a4f9be599975"
  },
  {
    "file": "kgg-update/src/patches/v090-ticket-015-admin-stage-gallery-drag-motion.html",
    "sha256": "bbae05b6d45927c7f14b19dcfe8b193cd0fcf1414b27adced0105e43e06ad1e6"
  },
  {
    "file": "kgg-update/src/patches/v093-cockpit-shared-editor.html",
    "sha256": "76da5d4c09e1b941127b0cb1b0ea7873c4ae7436708ed3c5779b8e362f2de42b"
  },
  {
    "file": "kgg-update/src/runtime/app-core.html",
    "sha256": "80548924281b10af79c1d2645a60956b42728a905ac934e5c0b8e3d09447149f"
  },
  {
    "file": "kgg-update/version.json",
    "sha256": "44407021580e051dd1719882c921a0aa477ccf59660f7966bec8171a36ad237f"
  },
  {
    "file": "patient-card-settings.js",
    "sha256": "1956801d44b1d1c4470187ebc66474df92cc456bf1e6d2ea9bda92c026fa7901"
  },
  {
    "file": "patient-day-history.js",
    "sha256": "2e904b1b6578aef5a7fccc5128bc633c5367c966b4eb5dd484e79a98bdf7661e"
  },
  {
    "file": "patient-i18n.js",
    "sha256": "c2a86d7ad498933f7b4338f1957ff9b6df6b9a4020aa45b90449dd528afa8827"
  },
  {
    "file": "patient-install-guide.js",
    "sha256": "11d2fb9edd3f290a4f75bd7a1526daee53faa55bccbe041129f3f04fdf729e86"
  },
  {
    "file": "patient-last-value-hints.js",
    "sha256": "879131abf73d0e66234abe33670c43e9eb963a1371527262db617ee1a817d685"
  },
  {
    "file": "patient-media-retry-cache_v2.js",
    "sha256": "1ae19634aa7973dbe1546333b7d2e6d0138e04e175290ce2e11310092a4651ca"
  },
  {
    "file": "patient-multiplan-db.js",
    "sha256": "40946ffbc7200254f9f813dc0a6048437171256e7f2f2de9470c78d4338528eb"
  },
  {
    "file": "patient-plan-delete.js",
    "sha256": "2b37629bfbabb202e04c04cec8f6a883c173343411a4c57814771b9fb5b43ad7"
  },
  {
    "file": "patient-plan-link-choice.js",
    "sha256": "19e7edb65e02717b8e36f0062e6422b0bffb3b4e9987e4b31638fb7cea2d0917"
  },
  {
    "file": "patient-qr-fullscreen.js",
    "sha256": "a9245be9a5bbc7d1582b42a587b7de72d4261b9f6946dd196edb74992b3e23dc"
  },
  {
    "file": "patient-react-dist/kgg-patient-ui.js",
    "sha256": "57d37fa3dacfddcd1050b7507436ba5f3499d8eaa678cedcce87f8054161c9f8"
  },
  {
    "file": "patient-set-compact-view.js",
    "sha256": "b9a7218388913774d7d151cced14a29522ebcc6f95dd8bad50b96f2d50a4e533"
  },
  {
    "file": "patient-set-summary-groups.js",
    "sha256": "6102607a3621da16e6f063d4c392123d8fc3f81f75e3e616471daa39118963a8"
  },
  {
    "file": "patient-ui-micro-polish.js",
    "sha256": "5bce46af62a0b793da0a850121429c704ac8294150aea0c1fcd148e3eda767a2"
  },
  {
    "file": "patient-ui/src/legacy-numpad/LegacyNumpadHeader.tsx",
    "sha256": "16c2b4870d35d165dd7ec2f6d8fe74ca6e8dbd087a37afd4b99fb62b49bfae78"
  },
  {
    "file": "patient-version-label.js",
    "sha256": "8aacac7fc3e25380200e5bef46d7055b421cfe6189a8af8116bc759b540187b3"
  },
  {
    "file": "service-worker.js",
    "sha256": "e7c4c785995340d7be2eebce8bae924c00deb7756d01231338d15f76a9cf9469"
  },
  {
    "file": "update-recovery.html",
    "sha256": "6f57568a48f65daaf63492d4c7098a76171dbe55bb8ca9b51a2fde6e3fcb11e3"
  }
]
```


### Historische unabhängige Freeze2-Abnahme — REJECTED

[Browserbericht Freeze2](/C:/src/kgg-worktrees/patient-english-complete-20261014/output/playwright/patient-english-review/freeze2-review.json): 14 Akzeptanzeinheiten, **12 PASS / 2 FAIL**, Start-/Endhashes beide 31/31 gleich; status REJECTED_TWO_IMPORTANT_FINDINGS. [Separator-Summarybefund](/C:/src/kgg-worktrees/patient-english-complete-20261014/output/playwright/patient-english-review/freeze2-authored-separator-fail-summary.png), [Merge-Statusbefund](/C:/src/kgg-worktrees/patient-english-complete-20261014/output/playwright/patient-english-review/freeze2-merge-status-fail.png), [Therapeuten-Summarybeleg](/C:/src/kgg-worktrees/patient-english-complete-20261014/output/playwright/patient-english-review/freeze2-teacher-export-summary.png). Diese lokalen Artefakte bleiben außerhalb des Commitumfangs; der 114-MB-Traceordner wird nicht gestagt.

Codebericht ausschließlich nativer Finalbericht des bounded Workers `/root/patient_english_code_review` im Parent-Chat; keine externe URL oder zweite Reportdatei. Quelle: Freeze2 affectedCodeReview, HEAD01e9c4e4c316752e90efb538c6fbb20adc856951, start/end31/31, **2 Important / 0 Critical / 0 Minor**, files_changed=[]. Befund 1: helper verlangt terminalen Punkt, tatsächlicher patient-start-scan.js mergeStatus38 endet direkt mit added ohne Punkt. Befund 2: prefix/colon-Heuristik verändert authored Separatornamen: `Basis — Tag 1` wird als `Basis` erkannt; Source/Target wie `Eigene Übung: Satz: A → Tag 2` werden durch nachlaufende Systemregex verändert. Sichere Producer: patient-card-settings rows(day)149, set-summary-groups notesFor363 über exIndex und beide variantIDs. Andere frühere 6+1/Browser2-Fixes, aktive Gallery/Cockpit/Metadata/Coreadapter angenommen; VM/sourceBuild/PWA/changelog PASS. Keine CI-/FullHook-/Gesamtfreigabe.

### Freeze3 — enger Status-/Summaryfix, 15.10.2026

Cloud-Fixplan PASS, Root-Fixfenster erst nach Ende beider gebundenen Audits. Genau vier Produktpfade geändert: index.html, patient-i18n.js, patient-card-settings.js, patient-set-summary-groups.js. **27 andere Produkte und sämtliche v96/Gallery/Cockpit/Companion/SW-Versionen bytegleich zu Freeze2.** Kein Parser-, QR-, State-, Decoder-, Layout-, Versions- oder Cache-Refactor.

Statusvorlage erkennt den tatsächlichen MergeStatus mit/ohne terminalen Punkt und erhält die vorhandene Interpunktion im Sprachroundtrip. Summary-Anzeige wird am Producer strukturiert erfasst: QR-Tag, konkrete Zeilenwerte, Übungsindex/Varianten-ID aufgelöste vollständige Namen, aktuelle explizite EN-Map und aufgelöste Übergangssegmente. Das ephemere Modell hängt nur am Summary-DOM-Knoten. Systembeschriftungen/erkannte Units werden beim Rendern separat übersetzt. Der alte helper.summaryText-Parser über fertige Strings ist entfernt. Der kanonische text()-Producer, rows()-Payload und deutscher QR bleiben unverändert. Fehlende Varianten-ID/Übungsindex/Tag werden ausgelassen; keine Namen- oder Reihenfolgeninferenz. Capture vor Tagesfortschaltung hält den dargestellten QR-Tag bei offenen Current-/Final-Ausgaben stabil.

**Focused frische Evidenz:**
- Neuer `kgg_patient_english_summary_playwright.js`: tatsächliche Source-Statusanweisung aus patient-start-scan gelesen und in VM ausgeführt, keine künstliche 'actual' Ersatzform. RED für echte unpunktierte Form und tatsächlichen Prefix-Stage-Header; GREEN nach Patch. Frische getrennte Legacy-/React-Contexts, Serviceworker block/no-store, vier tatsächlich servierte Ressourcenkörper an SHA256 gebunden. 52 Assertions PASS: beide Statusformen DE↔EN; authored DE- und EN-Namen mit Tag1/Colon/Dash/Arrow; Transition Source/Target exakt; identische Namen per Index und separate Werte; Tage1/2, Current/Final-QR, acht vollständige Summary-Sprachroundtrips mit p/v/currentPlan/echter kggProgressionHistoryV1/rows/text/QR/day bytegleich.
- Physisch: normaler Sprachknopf, Stage-next, Legacy-/React-NumPad3/4/OK, Current-/Final-QR. Zusätzliche identische Indexwerte/komplette Day2-Werte über ausdrücklich gekennzeichnete reale put-Contractcalls; der bestehende Tap-Proxy einer adversarial Notizfixture blockierte den Pointer. Keine Layoutumgehung als Produktänderung und keine körperliche Bedienung dieses Sonderfalls behauptet.
- Neuer `kgg_patient_english_summary_smoke.js`: echter registerSummaryDisplay-Callback + tatsächlicher variantById. Unterschiedliche ID-Paare bei identischem Namen bleiben ihrem exIndex zugeordnet; fehlende IDs/Index bzw. falscher Tag werden ausgelassen. Exakte authored DE/EN-Namen und unveränderte raw Daten PASS.
- Bestehende English18+12 Legacy/React und gezielte Review-Playwright-Suite PASS; Reviewer-Summaryprobe nutzt jetzt die strukturierte Display-API, alte numerische Ersatzformen korrekt als Fixtures bezeichnet. Bestehender Summary-range-Smoke, Syntax, PWA/Recovery, Encoding, Hook Guard und scoped Diffcheck PASS.
- Alle bestehenden source/changelog/context/bug/sourceContext/knowledgePack/patientResources Freshnesschecks PASS; resource_audit TARGET_PASS ausschließlich erneut notwendige Patient-Knowledge-Digests, model/capabilities unverändert und Live-Sync weiterhin pending. Keine erneute volle Batterie vor dem vorgesehenen vollständigen Commit-Hook.

**Next actual action:** Writer pausiert Produkt-/Test-/Docänderungen ab Freeze3. Root führt independent affected Code-/Browserrecheck und getrennte Cockpit-/v90-offline-Gegenprobe durch. Danach erst normaler vollständiger Commit-Hook und autorisierte DraftPR kgg-no-release. FullHook, CI, Merge/Release und Gesamtprojektabschluss weiterhin offen.

Freeze3 ProductHashes (31 tatsächliche Arbeitsdateien):

```json
[
  {
    "file": "collapse-cards.js",
    "sha256": "ac8afec81349ecb3ae8d9b5dd9fd9a39c476d4dedc7148907939ebd4fae8aafc"
  },
  {
    "file": "index.html",
    "sha256": "2630a9cacaad3b5cd83ff7df44b47c3585456c7d95a0e079ea67b5612ab2f6ce"
  },
  {
    "file": "kgg-update/index.html",
    "sha256": "d9e4edcda8afd4cdfc821b4e9d155483a726cec4e9c4603e4eeee4b94a0bf2d3"
  },
  {
    "file": "kgg-update/src/document/body-shell.html",
    "sha256": "52fc54134ed60677b787d798a1caf21f86215f17f467bad532e52f2e9236cc80"
  },
  {
    "file": "kgg-update/src/document/head-ui.html",
    "sha256": "c74cca199993b498cbb9d50de132c1fa5dd5a0f89b1e468165b54e7cc18fd9bb"
  },
  {
    "file": "kgg-update/src/metadata/changelog.html",
    "sha256": "a919cbbe18ba7d8015b561699e5a1e44cc153452c8583b9188bc5d0c26a17f27"
  },
  {
    "file": "kgg-update/src/metadata/source-truth.html",
    "sha256": "7fed7106b40c946e0f113edd221dc76c17f532ab5dc93a4b19a25624718b3a2d"
  },
  {
    "file": "kgg-update/src/patches/v082-therapy-cockpit.html",
    "sha256": "94564723f8d292cf9cf23a88da3076c7cf6393e47880a6c50b06bdc7836ac673"
  },
  {
    "file": "kgg-update/src/patches/v085-ticket-015-progressions.html",
    "sha256": "43ed681276dac3f5394d3e05880fca683c1d3cc6dd44f00c5c50a4f9be599975"
  },
  {
    "file": "kgg-update/src/patches/v090-ticket-015-admin-stage-gallery-drag-motion.html",
    "sha256": "bbae05b6d45927c7f14b19dcfe8b193cd0fcf1414b27adced0105e43e06ad1e6"
  },
  {
    "file": "kgg-update/src/patches/v093-cockpit-shared-editor.html",
    "sha256": "76da5d4c09e1b941127b0cb1b0ea7873c4ae7436708ed3c5779b8e362f2de42b"
  },
  {
    "file": "kgg-update/src/runtime/app-core.html",
    "sha256": "80548924281b10af79c1d2645a60956b42728a905ac934e5c0b8e3d09447149f"
  },
  {
    "file": "kgg-update/version.json",
    "sha256": "44407021580e051dd1719882c921a0aa477ccf59660f7966bec8171a36ad237f"
  },
  {
    "file": "patient-card-settings.js",
    "sha256": "8add0ea203d90b87a76dcc423f5f0bac36e687212b999df81c9c48981a4dcfb7"
  },
  {
    "file": "patient-day-history.js",
    "sha256": "2e904b1b6578aef5a7fccc5128bc633c5367c966b4eb5dd484e79a98bdf7661e"
  },
  {
    "file": "patient-i18n.js",
    "sha256": "efc1a0b7fbc9bce500951b36d35a21d9b615d4294efa7a5f91faf1e06cbaf898"
  },
  {
    "file": "patient-install-guide.js",
    "sha256": "11d2fb9edd3f290a4f75bd7a1526daee53faa55bccbe041129f3f04fdf729e86"
  },
  {
    "file": "patient-last-value-hints.js",
    "sha256": "879131abf73d0e66234abe33670c43e9eb963a1371527262db617ee1a817d685"
  },
  {
    "file": "patient-media-retry-cache_v2.js",
    "sha256": "1ae19634aa7973dbe1546333b7d2e6d0138e04e175290ce2e11310092a4651ca"
  },
  {
    "file": "patient-multiplan-db.js",
    "sha256": "40946ffbc7200254f9f813dc0a6048437171256e7f2f2de9470c78d4338528eb"
  },
  {
    "file": "patient-plan-delete.js",
    "sha256": "2b37629bfbabb202e04c04cec8f6a883c173343411a4c57814771b9fb5b43ad7"
  },
  {
    "file": "patient-plan-link-choice.js",
    "sha256": "19e7edb65e02717b8e36f0062e6422b0bffb3b4e9987e4b31638fb7cea2d0917"
  },
  {
    "file": "patient-qr-fullscreen.js",
    "sha256": "a9245be9a5bbc7d1582b42a587b7de72d4261b9f6946dd196edb74992b3e23dc"
  },
  {
    "file": "patient-react-dist/kgg-patient-ui.js",
    "sha256": "57d37fa3dacfddcd1050b7507436ba5f3499d8eaa678cedcce87f8054161c9f8"
  },
  {
    "file": "patient-set-compact-view.js",
    "sha256": "b9a7218388913774d7d151cced14a29522ebcc6f95dd8bad50b96f2d50a4e533"
  },
  {
    "file": "patient-set-summary-groups.js",
    "sha256": "505c5aab315c2d4d955c75c17f6514be04b88f24d81289376008e6f2a066974c"
  },
  {
    "file": "patient-ui-micro-polish.js",
    "sha256": "5bce46af62a0b793da0a850121429c704ac8294150aea0c1fcd148e3eda767a2"
  },
  {
    "file": "patient-ui/src/legacy-numpad/LegacyNumpadHeader.tsx",
    "sha256": "16c2b4870d35d165dd7ec2f6d8fe74ca6e8dbd087a37afd4b99fb62b49bfae78"
  },
  {
    "file": "patient-version-label.js",
    "sha256": "8aacac7fc3e25380200e5bef46d7055b421cfe6189a8af8116bc759b540187b3"
  },
  {
    "file": "service-worker.js",
    "sha256": "e7c4c785995340d7be2eebce8bae924c00deb7756d01231338d15f76a9cf9469"
  },
  {
    "file": "update-recovery.html",
    "sha256": "6f57568a48f65daaf63492d4c7098a76171dbe55bb8ca9b51a2fde6e3fcb11e3"
  }
]
```


### Historische Freeze3-Abnahme — REJECTED (13 PASS / 1 FAIL)

[Browserbericht Freeze3](/C:/src/kgg-worktrees/patient-english-complete-20261014/output/playwright/patient-english-review/freeze3-review.json): effektive 14er-Matrix **13 PASS / 1 FAIL**, 31 Endhashes unverändert. Die beiden alten Status-/Summarytexte bestanden; unabhängige Cockpit-, Cache-/v90-offline- und Summary-Runner bestanden laut Lead-Abnahme. Neuer reproduzierter Laufzeitbefund: Sprachroundtrip setzt die Karten-H3 auf Basis, während gewählte Stufe und QR-Summary Ziel bleiben; Daten/QR unverändert. Native read-only Gegenprüfung bestätigte echte Writer-Reihenfolge: set-summary Sprachlistener schreibt zuerst Variante, später registrierter card-settings i18n-Writer überschreibt mit exerciseName(e.n). helper.refresh schreibt keine H3. Kein weiterer Produktscope aus nicht stabil reproduzierter Medienbeobachtung.

### Freeze4 — vorhandener H3-Writer nutzt vorhandenen Resolver

Nach Ende beider gebundenen Audits Root-GO, Cloud-Gegenprüfung PASS. **Genau ein Produkt geändert: patient-card-settings.js; die anderen 30 Produkte bytegleich zu Freeze3.** Der vorhandene H3-Schreibvorgang in i18n() ruft für den aktuellen Übungsindex den bereits vorhandenen KGGPatientSummaryDisplay.nameForExercise auf und lokalisiert dessen rohe kanonische Bezeichnung genau einmal via exerciseName. Ohne Provider bleibt der bisherige e.n-Fallback. Kein Namenscache, keine DOM-/Namensinferenz, kein neuer Auswahl-/State-/QR-Write, zusätzlicher Observer oder Medien-/Layoutfix.

Frische focused Evidenz `kgg_patient_english_title_playwright.js`: zwei echte REDs auf den gebundenen Freeze3-Ressourcen (EN-H3 nach DE→EN, Legacy und React); Badge/Summary/kanonische Daten bestanden bereits. Nach Ein-Writer-Adapter **30/30 Assertions PASS** im frischen Legacy-/React-Kontext: physischer Stage-next→NumPad4/OK→CurrentQR→DE↔EN, H3/Badge/Summary konsistent; bestehender render()/scheduled-Card-Apply Contract; p/v/currentPlan/rows/text/echte History/QR/day bytegleich. Gewöhnliches Wadenheben→Calf Raise, zweiter Plan mit gleicher deutscher Bezeichnung aber eigenem EN-Label, DE/EN-Roundtrip und Fallback ohne Provider PASS. Planwechsel und fehlender Provider sind als direkte vorhandene API-Contracts gekennzeichnet; keine künstliche Auswahlregel. Vier tatsächlich servierte Ressourcenkörper an SHA256 gebunden, no-store und Serviceworker block; kein Zugriff auf echte Nutzerprofile.

Notwendige Generatoren aktualisiert; source/changelog/context/bug/sourceContext/knowledgePack/patientResources Freshnesschecks PASS. resource_audit TARGET_PASS nur notwendige pending Patient-Knowledge-Digests, kein Modell-/Capabilities-/Live-Sync-Wechsel. Syntax, bestehender Summary-Range-Smoke, Summary-Producer-VM, Encoding und scoped Diffcheck PASS. UI-Stability-Registry enthält den neuen reproduzierbaren Titel-Roundtriptest. Keine zusätzliche volle Batterie vor dem regulären vollständigen Commit-Hook.

**Next actual action:** Freeze4 unabhängig abgenommen; regulärer FullHook und autorisierte DraftPR kgg-no-release. Vollständiger Hook und aktuelle Remote-CI noch offen, kein Merge/Release. Lokale Trace-/Browserartefakte werden nicht gestagt.

Freeze4 ProductHashes (31 tatsächliche Arbeitsdateien):

```json
[
  {
    "file": "collapse-cards.js",
    "sha256": "ac8afec81349ecb3ae8d9b5dd9fd9a39c476d4dedc7148907939ebd4fae8aafc"
  },
  {
    "file": "index.html",
    "sha256": "2630a9cacaad3b5cd83ff7df44b47c3585456c7d95a0e079ea67b5612ab2f6ce"
  },
  {
    "file": "kgg-update/index.html",
    "sha256": "d9e4edcda8afd4cdfc821b4e9d155483a726cec4e9c4603e4eeee4b94a0bf2d3"
  },
  {
    "file": "kgg-update/src/document/body-shell.html",
    "sha256": "52fc54134ed60677b787d798a1caf21f86215f17f467bad532e52f2e9236cc80"
  },
  {
    "file": "kgg-update/src/document/head-ui.html",
    "sha256": "c74cca199993b498cbb9d50de132c1fa5dd5a0f89b1e468165b54e7cc18fd9bb"
  },
  {
    "file": "kgg-update/src/metadata/changelog.html",
    "sha256": "a919cbbe18ba7d8015b561699e5a1e44cc153452c8583b9188bc5d0c26a17f27"
  },
  {
    "file": "kgg-update/src/metadata/source-truth.html",
    "sha256": "7fed7106b40c946e0f113edd221dc76c17f532ab5dc93a4b19a25624718b3a2d"
  },
  {
    "file": "kgg-update/src/patches/v082-therapy-cockpit.html",
    "sha256": "94564723f8d292cf9cf23a88da3076c7cf6393e47880a6c50b06bdc7836ac673"
  },
  {
    "file": "kgg-update/src/patches/v085-ticket-015-progressions.html",
    "sha256": "43ed681276dac3f5394d3e05880fca683c1d3cc6dd44f00c5c50a4f9be599975"
  },
  {
    "file": "kgg-update/src/patches/v090-ticket-015-admin-stage-gallery-drag-motion.html",
    "sha256": "bbae05b6d45927c7f14b19dcfe8b193cd0fcf1414b27adced0105e43e06ad1e6"
  },
  {
    "file": "kgg-update/src/patches/v093-cockpit-shared-editor.html",
    "sha256": "76da5d4c09e1b941127b0cb1b0ea7873c4ae7436708ed3c5779b8e362f2de42b"
  },
  {
    "file": "kgg-update/src/runtime/app-core.html",
    "sha256": "80548924281b10af79c1d2645a60956b42728a905ac934e5c0b8e3d09447149f"
  },
  {
    "file": "kgg-update/version.json",
    "sha256": "44407021580e051dd1719882c921a0aa477ccf59660f7966bec8171a36ad237f"
  },
  {
    "file": "patient-card-settings.js",
    "sha256": "06c04bcb84d6eec3bad892f48c1434f6aab7060e0601bfe2a01eb417405ee045"
  },
  {
    "file": "patient-day-history.js",
    "sha256": "2e904b1b6578aef5a7fccc5128bc633c5367c966b4eb5dd484e79a98bdf7661e"
  },
  {
    "file": "patient-i18n.js",
    "sha256": "efc1a0b7fbc9bce500951b36d35a21d9b615d4294efa7a5f91faf1e06cbaf898"
  },
  {
    "file": "patient-install-guide.js",
    "sha256": "11d2fb9edd3f290a4f75bd7a1526daee53faa55bccbe041129f3f04fdf729e86"
  },
  {
    "file": "patient-last-value-hints.js",
    "sha256": "879131abf73d0e66234abe33670c43e9eb963a1371527262db617ee1a817d685"
  },
  {
    "file": "patient-media-retry-cache_v2.js",
    "sha256": "1ae19634aa7973dbe1546333b7d2e6d0138e04e175290ce2e11310092a4651ca"
  },
  {
    "file": "patient-multiplan-db.js",
    "sha256": "40946ffbc7200254f9f813dc0a6048437171256e7f2f2de9470c78d4338528eb"
  },
  {
    "file": "patient-plan-delete.js",
    "sha256": "2b37629bfbabb202e04c04cec8f6a883c173343411a4c57814771b9fb5b43ad7"
  },
  {
    "file": "patient-plan-link-choice.js",
    "sha256": "19e7edb65e02717b8e36f0062e6422b0bffb3b4e9987e4b31638fb7cea2d0917"
  },
  {
    "file": "patient-qr-fullscreen.js",
    "sha256": "a9245be9a5bbc7d1582b42a587b7de72d4261b9f6946dd196edb74992b3e23dc"
  },
  {
    "file": "patient-react-dist/kgg-patient-ui.js",
    "sha256": "57d37fa3dacfddcd1050b7507436ba5f3499d8eaa678cedcce87f8054161c9f8"
  },
  {
    "file": "patient-set-compact-view.js",
    "sha256": "b9a7218388913774d7d151cced14a29522ebcc6f95dd8bad50b96f2d50a4e533"
  },
  {
    "file": "patient-set-summary-groups.js",
    "sha256": "505c5aab315c2d4d955c75c17f6514be04b88f24d81289376008e6f2a066974c"
  },
  {
    "file": "patient-ui-micro-polish.js",
    "sha256": "5bce46af62a0b793da0a850121429c704ac8294150aea0c1fcd148e3eda767a2"
  },
  {
    "file": "patient-ui/src/legacy-numpad/LegacyNumpadHeader.tsx",
    "sha256": "16c2b4870d35d165dd7ec2f6d8fe74ca6e8dbd087a37afd4b99fb62b49bfae78"
  },
  {
    "file": "patient-version-label.js",
    "sha256": "8aacac7fc3e25380200e5bef46d7055b421cfe6189a8af8116bc759b540187b3"
  },
  {
    "file": "service-worker.js",
    "sha256": "e7c4c785995340d7be2eebce8bae924c00deb7756d01231338d15f76a9cf9469"
  },
  {
    "file": "update-recovery.html",
    "sha256": "6f57568a48f65daaf63492d4c7098a76171dbe55bb8ca9b51a2fde6e3fcb11e3"
  }
]
```

### Unabhängige Freeze4-Abnahme — CODE PASS / Browser 14 PASS

Lead-Abnahme 15.10.2026: native finale Codeprüfung PASS (Bericht ausschließlich im Prüfer-Chat, keine Reportdatei); [Browserbericht Freeze4](/C:/src/kgg-worktrees/patient-english-complete-20261014/output/playwright/patient-english-review/freeze4-review.json) effektive Matrix **14 PASS / 0 FAIL / 0 NOT_TESTED**. Beide Prüfer bestätigten Start-/Endhashes 31/31 unverändert; vier tatsächlich geladene Ressourcen stimmten 4/4 überein. Physischer Stufen-Kartentitel in Legacy/React, bestehender Render-/CardApply-Pfad sowie Daten-/QR-Snapshots PASS. Unveränderte Dependencies: unabhängige Cockpit-, immutable v90→v93/offline- und Summary-Runner aus Freeze3 PASS mit dortiger Provenienz und Grenzen. Alle Auditor-Kontexte/Chromium geschlossen; CPU für regulären Hook freigegeben.

Autorisiert: passende Produkt-, Test- und notwendige generierte Nachweise explizit stagen; normaler vollständiger Commit-Hook ohne zusätzliche identische Vorab-Vollbatterie. Ausschließlich dokumentiertes `KGG_ALLOW_RELEASE_DRIFT=1` für v96 No-Release-Kandidat; alle weiteren Guards/Gates aktiv. Danach normaler Branchpush, DraftPR `kgg-no-release` und aktuelle Required Checks abwarten. Kein Merge/Release, keine Android-/APK-/Manifeständerung. Hardware-/echte Kamera-/Prüf-APK-Abnahme nicht durchgeführt; synthetische Browser-/VM-Gates decken diese Grenze nicht ab. Separate Import-PR321 und spätere Versions-/Overlap-Integration verbleiben bei Lead. Output-/Traceartefakte bleiben lokal und ungestagt.

### Regulärer FullHook Versuch 1 — FAIL, historische Evidenz

[Fehlerzertifikat](/C:/src/kgg-worktrees/patient-english-complete-20261014/tmp/kgg-selftest/runs/20261014T223654Z-22164/report.json), `fullRegression=true`: Secret-Scan, Modulbuild und Patchhygiene PASS; Release-Contract-Unittests **141 Tests / 2 FAIL / 1 ERROR / 1 SKIP**, Abbruch vor Browser-/QR-Gates. Ursache ausschließlich stale v95-Testfixture in `test_kgg_changelog_archive.py`: erwartet 36 Einträge/8 Snapshots statt v96 mit 37/9; Recovery-Fall verwendet v94 statt tatsächlichem v95-Vorgänger. Bestehender Generator und Archivvalidierung korrekt; keine Produktreparatur. Selftest `restoredLastGreen=true`, alle tatsächlichen Freeze4-Produkthashes danach 31/31 unverändert.

Minimaler Testfixture-Nachtrag: feste v96-Zahlen/letzte Version/prüfbarer Snapshot-Hash `49767017066c2fbecb49bdec329c3c0c18231747883aa9d2fe3e662ca7c1a9cd`, v95-Recoverybasis und 37 rekonstruierte Einträge; keine Assertion entfernt/gelockert, keine Gate- oder Hookänderung. Gezielte sechs Changelogtests **6/6 PASS** (0.449s), scoped Diffcheck PASS; regulärer neuer Hook noch offen.

Unabhängiger Testdiff-Review (native Lead-Finalmeldung) **PASS**: sechs Tests und 14 Assertions erhalten, fester Hash/Version/v95-Vorgänger sowie negative Recovery-Grenze bestätigt. Root-GO für einen regulären erneuten FullHook; Produktdateien weiter Freeze4. Zusätzliche tatsächliche CI-Freshnesschecks context/bug/sourceContext/knowledgePack/PatientResources46 PASS, resource audit TARGET_PASS. FeatureTestMap self-test PASS/structure VALID; changed-file-Ergebnis bewusst advisory REVIEW_REQUIRED, Tests NOT_RUN, kein Runtime-PASS aus Metadaten abgeleitet.
