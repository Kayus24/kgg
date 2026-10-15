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

### Regulärer FullHook Versuch 2 — PASS / Produktcommit

[Zertifikat](/C:/src/kgg-worktrees/patient-english-complete-20261014/tmp/kgg-selftest/runs/20261014T224359Z-12616/report.json): `mode=certify`, `status=passed`, `fullRegression=true`, vollständige Regression Exit0 **681.95s**, gestartet 2026-10-14T22:43:59Z, beendet 22:55:21Z. 72 ausgeführte Batterieblöcke einschließlich aller Critical-, English-Editor/Compatibility/Summary/Title/Cockpit-, UI-Stability-, Kamera-/QR- und Native-Sync-Regressionsprüfungen. Release-Unittests 141 Tests OK (ein vorhandener Skip). QR-Ladder alle zehn Pflichtfälle PASS (einschließlich medium20, old7/12, weak7); ergänzende optische Belastungsfälle enthalten vier bestehende WARNs: angle7, motion/noise/low-light7, distance20, angle20. Diese WARNs sind kein Hardware-PASS und werden nicht verborgen. Normale Secret-/Hookguards aktiv, kein zusätzlicher Skip.

Produktcommit `1f70fd8f8bd88839cfd9b8a0413009dd3e0d87a9`, separater wiederverwendeter Testharness-Commit `01e9c4e4c316752e90efb538c6fbb20adc856951`; Base weiter f59bc55. Kandidat v96 SHA256 `d9e4edcda8afd4cdfc821b4e9d155483a726cec4e9c4603e4eeee4b94a0bf2d3`, sämtliche Freeze4-Produktdateien nach Hook **31/31 bytegleich**. Trackeds sauber, ausschließlich lokale output/-Artefakte untracked. Abschlussnachtrag nur Doku mit normalem Secret-Hook; keine zweite identische Fullbatterie.

Cloud-Abschlussgegenprüfung laut Lead **PASS für gebundenen lokalen Code-/Browserstand auf mitgeteilter Evidenz**, kein eigener Cloud-Repo-/Runtime-Test. Grenzen erhalten: unbekannte eigene Namen/Altvarianten benötigen gepflegtes nameEn; Sprache in backdrop-blockierten Modals ist als Handler-Vertrag gekennzeichnet; Hardwarekamera, OS-Installation und Android/Prüf-APK ungeprüft. Keine zusätzliche Batterie/Produktänderung aus der Cloudberatung. **Next actual action:** autorisierter Branchpush, DraftPR `kgg-no-release`, aktuelle Remote-Required-Checks verfolgen; kein Merge/Release.

### DraftPR / Remote-CI Versuch 1 — FAIL, erforderliche Nachträge

[DraftPR323](https://github.com/Kayus24/kgg/pull/323) erstellt und am Task angehängt, `kgg-no-release`, Head `ae6e1edae320d7f971b5e5850e1cac112ca63d6a`. [Aktueller RequiredGate-Lauf](https://github.com/Kayus24/kgg/actions/runs/38651024668) tatsächlich **FAIL**; erster öffnungsgetriggerter Lauf38651023873 durch Labelkonkurrenz abgelöst, nicht als Freigabe gezählt. Echte Fehlstellen: core Cockpit-VM17 erwartet Altreader-nameEn undefined, tatsächliches My exercise; patient-browser beim Prepare isolated Patient GPT browser fixture: exact direct first-load module list verletzt. Lokaler FullHook-PASS bleibt historische Evidenz am damals unveröffentlichten Kandidaten, keine Remote-CI-Freigabe.

Test-Provenienzkorrektur nach Root-GO ausschließlich `kgg_english_cockpit_smoke.js` und `kgg_patient_english_compatibility_playwright.js`: alle drei git-show-HEAD-Stellen an ursprünglichen vollständigen f59-SHA gebunden. Vor Commit war HEAD01e9 identisch zum f59-Produktstand, nach Commit Kandidat. Reale Kandidat-HEAD-REDs: Cockpit-VM17 My exercise statt undefined und Compatibility32 30000ms Timeout auf v90-Cache; danach beide gezielte echte Tests Exit0 PASS, inklusive immutable oldreader/Checksum/CreateClearRetain/contentKey und tatsächlichem v90→v93-SWupdate/offline cold reload. Unabhängiger Zwei-Datei-Diffreview PASS: gesamte übrige Assertions/Fristen/Fehlerpfade bytegleich, f59 vollständiger Vorfahr und ehemalige01e9-Baselinebytes identisch; RequiredGate fetch-depth0 unverändert. Testhashes `1f99bd139bf1bf6dc1c4f064f5d8160ce4b213c80ade02b0371cfe9e96cc0595` / `a6db2b9d66c702e04121b5c2b1e989bc8b408a19ec59f2e5d2d7bd3132655dc3`.

Konkreter weiterer lokaler Preview-RED bestätigt. Erste Interpretation (fehlender Storage-Tag in Produktindex) war falsch und wurde vor jedem Produktwrite gegenüber Lead korrigiert: Immutable f59-Produktindex hat 27 direkte Module ohne Storage-Tag; Kandidat ergänzt i18n korrekt zu28. `write_preview()` injiziert ausschließlich im isolierten Preview `patient-storage-scope.js` (write_gate567–573), daher erzeugtes Kandidatenpreview29 statt alter fester Preview-Sollliste28. Kein Produkt-/Loader-/Storagefix erforderlich oder ausgeführt. Kleinster Nachtrag nur bestehende feste Previewcontract-Modulliste um i18n nach injiziertem Storage-Script ergänzen, zugehörigen vorhandenen Firstload-Smoke prüfen; sämtliche order/missing/duplicate/isolation Guards erhalten. **Next actual action:** bounded Previewcontract-GO, betroffene echte Preview-Firstload/Storage-Isolation-Gates und unabhängiger Testdiff-Recheck; kein blinder CI-Neustart, Produkte weiterhin Freeze4.

### Vier Test-/Preview-Vertragsnachträge — unabhängig PASS

Root/Cloud-GO und native unabhängige Codeprüfung **PASS** für exakt vier Testdateien, keine Produktänderung: zwei feste f59-Altbasisbindungen wie oben; zusätzlich ausschließlich je eine Pflichtlisten-Zeile `patient-i18n.js` nach Preview-Storage in write_gate und Firstload-Smoke. Alle anderen Reihenfolgen, Existenz-/Duplikat-/missing-/version-/negative Guards, Assertions und Fristen bytegleich; Preview-only Injektion unverändert. Neue Frozen-Testhashes write_gate `db621e231bfea72dd2addaca3b3db942b3a26e084f6aefef2a44eda81c349cd1`, Firstload `37db546492635a4f27d51320d9cc46e6dfa72c00b264c07a670a61a61c9ad6a4`; zwei Altbasis-Testhashes oben unverändert. Prüfer Start/End und eigener finaler Hashcheck **31/31 Produkte Freeze4**.

Tatsächliche Gates: write_gate self-test mit isoliertem output/-Preview **PASS**, Firstload-Browser **PASS** (27 Pflichtmodule, freshRoot ohne Reload, scanner einmal, Eingabefortschritt/redX/lokale Thumbnail-Geometrie), Storage-Isolation **PASS** (Live-Plan, Preview-Reload und zwei requestbezogene Namespaces). Erster Isolation-Aufruf hatte irrtümlich nur einen Rootparameter und scheiterte expectedTitle; korrekt bestehendem CLIvertrag `. previewRoot patient-gate-self-test` Exit0 PASS, keinerlei Isolationharness-/Produktänderung daraus. Stale `knowledge-testing.md` über vorhandenen PatientResources-Generator aufgefrischt, ausschließlich zugehöriger Knowledge-Digest in Manifest/pending patientProduction-Snapshot aktualisiert; keine Modell-/Capabilities-/Syncstatus-/Liveänderung. PatientResources46 PASS, resource audit TARGET_PASS; context/bug/sourceContext/knowledgePack PASS. Vier-Testdateien-Nachtrag unabhängig angenommen. **Next actual action:** normaler Hook/Test-/Nachweiscommit, Branchpush und neue aktuelle Head-CI; keine zusätzliche identische Vorab-Vollbatterie.


### Main-Abgleich — Revision2 / kombinierter Freeze1

Verifiziert 2026-10-15T07:03:48Z. Normale Main-Merge mit `--no-ff --no-commit` auf dem vorhandenen Englishbranch; noch kein Commit/Push. Gebundene Parents unten. Patient93/Therapeutsource96 bleiben erhalten. Von den bisherigen 31 Freeze4-Produkten sind 29 tatsächliche Arbeitsdateihashes exakt erhalten; index/SW ändern ausschließlich den Main-Scannerref. Der zusätzliche 32. Produktpfad patient-start-scan.js ist exakt der festgepinnte Main-Gitblob. `sha256` bindet tatsächliche Arbeitsbytes; `lfSha256` trennt Git-/Parentinhalt von den fünf bereits vorher vorhandenen Aux-JS-CRLF-Checkouts. Kein funktionaler EOL-Patch aus diesen fünf Unterschieden.

Vier Produktkonflikte wie genehmigt aufgelöst, Generated-Konflikte über bestehende Generatoren abgeleitet. Notwendiger zweiter Scannerchunk035 ausdrücklich angenommen. Die drei Manifest-/Editor-Snapshot-JSONs stimmen rekursiv außerhalb der Knowledge-Digests mit beiden Parents überein; Modell/Capabilities/Identity/Pending unverändert. Sourcebuild/Changelog und sechs Freshnesschecks PASS; resource audit TARGET_PASS. Metadata-/SharedBank-/Companion-, Cockpit-Altreader/Wire/State- und Summary-Producer-VM PASS.

Cloud/Root-GO Revision2: DualDevice ROOT_FILES ergänzt genau einmal den vorhandenen i18n-Helper; vorhandene Kopier-/Storageisolation wird weiterverwendet. Bestehender Compatibilitytest behält default f59/v90 und wählt ausschließlich mit `--cache-from-v92` den festgepinnten Main4bbe/v92. Alle bisherigen Assertions/Fristen/Profile erhalten; zusätzliche GET_APP_VERSION-Antworten belegen die aktive Baseline sowie Ziel93 vor/nach Offline-Reload. Fehlende Altressourcen bleiben404, kein Arbeitsdateifallback. Diese Testergänzungen ändern kein Produkt.

Gezielte kombinierte Paket-/Import-/English-/beide Cache-/Preview-Storage-Gates und unabhängiger Candidate-Review jetzt offen. Alle laufen gegen genau diesen Freeze; alte8CI/Hooks bleiben historische Evidenz. Normaler FullHook/aktuelle Head-CI, Merge/Release/Manifest/APK weiterhin offen. Output/Traces bleiben lokal ungestagt.

```json
{
  "id": "main-alignment-r2-freeze1",
  "task_id": "patient-english-main-alignment-20261015",
  "generation": 2,
  "revision": 2,
  "englishParent": "d34e90f6ef4890e345c1559e75e2a5c22df4d27a",
  "mainParent": "4bbe3905126741c042e21331d7485067470b6640",
  "products": [
    {
      "file": "collapse-cards.js",
      "sha256": "ac8afec81349ecb3ae8d9b5dd9fd9a39c476d4dedc7148907939ebd4fae8aafc",
      "lfSha256": "ac8afec81349ecb3ae8d9b5dd9fd9a39c476d4dedc7148907939ebd4fae8aafc",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "index.html",
      "sha256": "12f4d469d042909d6e7b0b835b16616a0a6a35602fac18b6ada7fc6753c56b76",
      "lfSha256": "12f4d469d042909d6e7b0b835b16616a0a6a35602fac18b6ada7fc6753c56b76",
      "parent": "English-scanner-ref-only"
    },
    {
      "file": "kgg-update/index.html",
      "sha256": "d9e4edcda8afd4cdfc821b4e9d155483a726cec4e9c4603e4eeee4b94a0bf2d3",
      "lfSha256": "d9e4edcda8afd4cdfc821b4e9d155483a726cec4e9c4603e4eeee4b94a0bf2d3",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "kgg-update/src/document/body-shell.html",
      "sha256": "52fc54134ed60677b787d798a1caf21f86215f17f467bad532e52f2e9236cc80",
      "lfSha256": "52fc54134ed60677b787d798a1caf21f86215f17f467bad532e52f2e9236cc80",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "kgg-update/src/document/head-ui.html",
      "sha256": "c74cca199993b498cbb9d50de132c1fa5dd5a0f89b1e468165b54e7cc18fd9bb",
      "lfSha256": "c74cca199993b498cbb9d50de132c1fa5dd5a0f89b1e468165b54e7cc18fd9bb",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "kgg-update/src/metadata/changelog.html",
      "sha256": "a919cbbe18ba7d8015b561699e5a1e44cc153452c8583b9188bc5d0c26a17f27",
      "lfSha256": "a919cbbe18ba7d8015b561699e5a1e44cc153452c8583b9188bc5d0c26a17f27",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "kgg-update/src/metadata/source-truth.html",
      "sha256": "7fed7106b40c946e0f113edd221dc76c17f532ab5dc93a4b19a25624718b3a2d",
      "lfSha256": "7fed7106b40c946e0f113edd221dc76c17f532ab5dc93a4b19a25624718b3a2d",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "kgg-update/src/patches/v082-therapy-cockpit.html",
      "sha256": "94564723f8d292cf9cf23a88da3076c7cf6393e47880a6c50b06bdc7836ac673",
      "lfSha256": "94564723f8d292cf9cf23a88da3076c7cf6393e47880a6c50b06bdc7836ac673",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "kgg-update/src/patches/v085-ticket-015-progressions.html",
      "sha256": "43ed681276dac3f5394d3e05880fca683c1d3cc6dd44f00c5c50a4f9be599975",
      "lfSha256": "43ed681276dac3f5394d3e05880fca683c1d3cc6dd44f00c5c50a4f9be599975",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "kgg-update/src/patches/v090-ticket-015-admin-stage-gallery-drag-motion.html",
      "sha256": "bbae05b6d45927c7f14b19dcfe8b193cd0fcf1414b27adced0105e43e06ad1e6",
      "lfSha256": "bbae05b6d45927c7f14b19dcfe8b193cd0fcf1414b27adced0105e43e06ad1e6",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "kgg-update/src/patches/v093-cockpit-shared-editor.html",
      "sha256": "76da5d4c09e1b941127b0cb1b0ea7873c4ae7436708ed3c5779b8e362f2de42b",
      "lfSha256": "76da5d4c09e1b941127b0cb1b0ea7873c4ae7436708ed3c5779b8e362f2de42b",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "kgg-update/src/runtime/app-core.html",
      "sha256": "80548924281b10af79c1d2645a60956b42728a905ac934e5c0b8e3d09447149f",
      "lfSha256": "80548924281b10af79c1d2645a60956b42728a905ac934e5c0b8e3d09447149f",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "kgg-update/version.json",
      "sha256": "44407021580e051dd1719882c921a0aa477ccf59660f7966bec8171a36ad237f",
      "lfSha256": "44407021580e051dd1719882c921a0aa477ccf59660f7966bec8171a36ad237f",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-card-settings.js",
      "sha256": "06c04bcb84d6eec3bad892f48c1434f6aab7060e0601bfe2a01eb417405ee045",
      "lfSha256": "06c04bcb84d6eec3bad892f48c1434f6aab7060e0601bfe2a01eb417405ee045",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-day-history.js",
      "sha256": "2e904b1b6578aef5a7fccc5128bc633c5367c966b4eb5dd484e79a98bdf7661e",
      "lfSha256": "c8664dff338e682fbf2df380d05aeee8daeecce5b7afa1beb812fe8d5d5414c0",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-i18n.js",
      "sha256": "efc1a0b7fbc9bce500951b36d35a21d9b615d4294efa7a5f91faf1e06cbaf898",
      "lfSha256": "efc1a0b7fbc9bce500951b36d35a21d9b615d4294efa7a5f91faf1e06cbaf898",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-install-guide.js",
      "sha256": "11d2fb9edd3f290a4f75bd7a1526daee53faa55bccbe041129f3f04fdf729e86",
      "lfSha256": "0ff8e9e3c7802f2891873762e66770d3c8e38230011cacee0eed4e6a390e8643",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-last-value-hints.js",
      "sha256": "879131abf73d0e66234abe33670c43e9eb963a1371527262db617ee1a817d685",
      "lfSha256": "879131abf73d0e66234abe33670c43e9eb963a1371527262db617ee1a817d685",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-media-retry-cache_v2.js",
      "sha256": "1ae19634aa7973dbe1546333b7d2e6d0138e04e175290ce2e11310092a4651ca",
      "lfSha256": "1ae19634aa7973dbe1546333b7d2e6d0138e04e175290ce2e11310092a4651ca",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-multiplan-db.js",
      "sha256": "40946ffbc7200254f9f813dc0a6048437171256e7f2f2de9470c78d4338528eb",
      "lfSha256": "40946ffbc7200254f9f813dc0a6048437171256e7f2f2de9470c78d4338528eb",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-plan-delete.js",
      "sha256": "2b37629bfbabb202e04c04cec8f6a883c173343411a4c57814771b9fb5b43ad7",
      "lfSha256": "273f3c1a9e8d76161e924e4c03d55afd1e0266502215531daf09c2ed01903073",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-plan-link-choice.js",
      "sha256": "19e7edb65e02717b8e36f0062e6422b0bffb3b4e9987e4b31638fb7cea2d0917",
      "lfSha256": "786a6663c4eb5ab5fcd8681a940401aa92b4450f1f2f11c0b5f00b9310adee16",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-qr-fullscreen.js",
      "sha256": "a9245be9a5bbc7d1582b42a587b7de72d4261b9f6946dd196edb74992b3e23dc",
      "lfSha256": "0485f687e98c3e03a45414f0459ac1b8958dfab9ad795fd07f76409e07160c07",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-react-dist/kgg-patient-ui.js",
      "sha256": "57d37fa3dacfddcd1050b7507436ba5f3499d8eaa678cedcce87f8054161c9f8",
      "lfSha256": "57d37fa3dacfddcd1050b7507436ba5f3499d8eaa678cedcce87f8054161c9f8",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-set-compact-view.js",
      "sha256": "b9a7218388913774d7d151cced14a29522ebcc6f95dd8bad50b96f2d50a4e533",
      "lfSha256": "b9a7218388913774d7d151cced14a29522ebcc6f95dd8bad50b96f2d50a4e533",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-set-summary-groups.js",
      "sha256": "505c5aab315c2d4d955c75c17f6514be04b88f24d81289376008e6f2a066974c",
      "lfSha256": "505c5aab315c2d4d955c75c17f6514be04b88f24d81289376008e6f2a066974c",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-ui-micro-polish.js",
      "sha256": "5bce46af62a0b793da0a850121429c704ac8294150aea0c1fcd148e3eda767a2",
      "lfSha256": "5bce46af62a0b793da0a850121429c704ac8294150aea0c1fcd148e3eda767a2",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-ui/src/legacy-numpad/LegacyNumpadHeader.tsx",
      "sha256": "16c2b4870d35d165dd7ec2f6d8fe74ca6e8dbd087a37afd4b99fb62b49bfae78",
      "lfSha256": "16c2b4870d35d165dd7ec2f6d8fe74ca6e8dbd087a37afd4b99fb62b49bfae78",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-version-label.js",
      "sha256": "8aacac7fc3e25380200e5bef46d7055b421cfe6189a8af8116bc759b540187b3",
      "lfSha256": "8aacac7fc3e25380200e5bef46d7055b421cfe6189a8af8116bc759b540187b3",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "service-worker.js",
      "sha256": "025613ed790cb2796f64c41fc9720c1b5a5d8495968503a725e49f88a3c3e6cc",
      "lfSha256": "025613ed790cb2796f64c41fc9720c1b5a5d8495968503a725e49f88a3c3e6cc",
      "parent": "English-scanner-ref-only"
    },
    {
      "file": "update-recovery.html",
      "sha256": "6f57568a48f65daaf63492d4c7098a76171dbe55bb8ca9b51a2fde6e3fcb11e3",
      "lfSha256": "6f57568a48f65daaf63492d4c7098a76171dbe55bb8ca9b51a2fde6e3fcb11e3",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-start-scan.js",
      "sha256": "f458b586572fc381195057be9ba56e86b0a29b70809bb1177a892abb6deb00ec",
      "lfSha256": "f458b586572fc381195057be9ba56e86b0a29b70809bb1177a892abb6deb00ec",
      "parent": "Main-exact"
    }
  ],
  "tests": [
    {
      "file": "release-pipeline/kgg_english_progression_baseline_playwright.js",
      "sha256": "e865fdc5e8ed2b3d9388f18c1e1394097f665344c8ccacded228cd155d4c05f3"
    },
    {
      "file": "release-pipeline/kgg_english_metadata_smoke.js",
      "sha256": "a6490412d1d2a835158a32176d80132a7a398d61ee8d5c507cf4a4fbcc7cdeb2"
    },
    {
      "file": "release-pipeline/kgg_english_editor_playwright.js",
      "sha256": "515933e9f591fb7ca624256b169cbe07752c6bcd851ef56082e21074f0775fd6"
    },
    {
      "file": "release-pipeline/kgg_english_cockpit_smoke.js",
      "sha256": "1f99bd139bf1bf6dc1c4f064f5d8160ce4b213c80ade02b0371cfe9e96cc0595"
    },
    {
      "file": "release-pipeline/kgg_english_cockpit_playwright.js",
      "sha256": "4fe7eda0ab021996600fb0e45085a4019290cfdfef80bf4ffbdd242403e00f67"
    },
    {
      "file": "release-pipeline/kgg_dual_device_package.js",
      "sha256": "0b5c79fa0b7324cecf2768b397b6e1a4d88e27eecdfbbcce053e39578a7e4047"
    },
    {
      "file": "release-pipeline/kgg_patient_english_title_playwright.js",
      "sha256": "a961c1f1f3069993475832855cee09fd5159dad48dd40340055382ea6bc3e757"
    },
    {
      "file": "release-pipeline/kgg_patient_english_summary_smoke.js",
      "sha256": "6549062a8af1064189af604b07a55c7ac82039a4d357bd8ae835574c484c8994"
    },
    {
      "file": "release-pipeline/kgg_patient_english_summary_playwright.js",
      "sha256": "9a3a1042f93e050cbd515e6b464675d5fc6355bfccb8d69d47cd6ed602805b99"
    },
    {
      "file": "release-pipeline/kgg_patient_english_review_playwright.js",
      "sha256": "40e04374b14d3ec0c2221be54069f499406fa114aa9f76d5e3ecbd52983d5c9c"
    },
    {
      "file": "release-pipeline/kgg_patient_english_playwright.js",
      "sha256": "28b9d3b0153570b040491ca2241660b30a0cddb708b97dbdd4825c054cecd0af"
    },
    {
      "file": "release-pipeline/kgg_patient_english_compatibility_playwright.js",
      "sha256": "0fbda81a25fd236d4af0cca5f872309e6ba1fd9656870d2790bb51fb19802f03"
    },
    {
      "file": "release-pipeline/kgg_patient_import_session_values_playwright.js",
      "sha256": "e426348734f1e01571321dd49459606de26af747f6c60c30c6731eff1d091aed"
    },
    {
      "file": "release-pipeline/kgg_patient_gpt_write_gate.py",
      "sha256": "db621e231bfea72dd2addaca3b3db942b3a26e084f6aefef2a44eda81c349cd1"
    },
    {
      "file": "release-pipeline/kgg_patient_preview_first_load_smoke.js",
      "sha256": "37db546492635a4f27d51320d9cc46e6dfa72c00b264c07a670a61a61c9ad6a4"
    },
    {
      "file": "release-pipeline/kgg_patient_qr_v81_device_ladder.js",
      "sha256": "52b9b9c6eac8bb11e4529b507a6c4a94e46bbb5f8acdc28d177a2e27af1883e9"
    },
    {
      "file": "release-pipeline/kgg_patient_preview_storage_isolation_smoke.js",
      "sha256": "a0485ad60ca432c254ffd78a8155d9aea22f87a1781fc60f22c908fe26bbf40b"
    },
    {
      "file": "release-pipeline/kgg_pwa_contract_smoke.py",
      "sha256": "74d973ebae4dcb4e8be42fdaa0bbcfe90dead17e7dd57ae00dbf93d9b15b5e94"
    },
    {
      "file": "release-pipeline/kgg_test_battery.py",
      "sha256": "7dff67422c62e77f3dd5f88b64ce632d8759b796bd0e37f6b09346f0651446ac"
    }
  ],
  "manifestSha256": "aed26db8b869690c1eed07322203b795b08e57fe99a6a5dc5b4d78f0507d00ee"
}
```


### Main-Abgleich — Revision2 / kombinierter Freeze2

2026-10-15T07:08:27Z: unabhängige Freeze1-Leserunde beendet, 32/32 Produkte und19/19Tests unverändert. Genau ein Important: bestehender PWA-Smoke verlangte den neuen Helper weder im Index noch im Worker. Enger, von Root angenommener Contractnachtrag ergänzt ausschließlich dessen Referenz in beide bestehenden Pflichtlisten; Scanner-v92-Eintrag und alle bisherigen Guards bleiben. Vorher akzeptierten reine Leseshims jeweils fehlenden Index-/Workerhelper (reproduzierte Guardlücke), danach werden beide spezifisch abgewiesen; unveränderter realer PWA-Contract PASS. Keine Produktdatei geändert.

Nur bestehende PatientResources-/PatientProduction-Digestableitungen erneut erzeugt: 46 Resources --check PASS, audit TARGET_PASS. Freeze2 bindet dieselben32Produkte, die19aktuellenTests und die erforderlichen generierten Nachweise. Freeze1 samt damaligem PWA-Testhash bleibt oben historisch. Targeted Runtime-Gates und unabhängiger Recheck jetzt offen; keine neue Hook-/CI-Freigabe behauptet.

```json
{
  "id": "main-alignment-r2-freeze2",
  "task_id": "patient-english-main-alignment-20261015",
  "generation": 2,
  "revision": 2,
  "englishParent": "d34e90f6ef4890e345c1559e75e2a5c22df4d27a",
  "mainParent": "4bbe3905126741c042e21331d7485067470b6640",
  "products": [
    {
      "file": "collapse-cards.js",
      "sha256": "ac8afec81349ecb3ae8d9b5dd9fd9a39c476d4dedc7148907939ebd4fae8aafc",
      "lfSha256": "ac8afec81349ecb3ae8d9b5dd9fd9a39c476d4dedc7148907939ebd4fae8aafc",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "index.html",
      "sha256": "12f4d469d042909d6e7b0b835b16616a0a6a35602fac18b6ada7fc6753c56b76",
      "lfSha256": "12f4d469d042909d6e7b0b835b16616a0a6a35602fac18b6ada7fc6753c56b76",
      "parent": "English-scanner-ref-only"
    },
    {
      "file": "kgg-update/index.html",
      "sha256": "d9e4edcda8afd4cdfc821b4e9d155483a726cec4e9c4603e4eeee4b94a0bf2d3",
      "lfSha256": "d9e4edcda8afd4cdfc821b4e9d155483a726cec4e9c4603e4eeee4b94a0bf2d3",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "kgg-update/src/document/body-shell.html",
      "sha256": "52fc54134ed60677b787d798a1caf21f86215f17f467bad532e52f2e9236cc80",
      "lfSha256": "52fc54134ed60677b787d798a1caf21f86215f17f467bad532e52f2e9236cc80",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "kgg-update/src/document/head-ui.html",
      "sha256": "c74cca199993b498cbb9d50de132c1fa5dd5a0f89b1e468165b54e7cc18fd9bb",
      "lfSha256": "c74cca199993b498cbb9d50de132c1fa5dd5a0f89b1e468165b54e7cc18fd9bb",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "kgg-update/src/metadata/changelog.html",
      "sha256": "a919cbbe18ba7d8015b561699e5a1e44cc153452c8583b9188bc5d0c26a17f27",
      "lfSha256": "a919cbbe18ba7d8015b561699e5a1e44cc153452c8583b9188bc5d0c26a17f27",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "kgg-update/src/metadata/source-truth.html",
      "sha256": "7fed7106b40c946e0f113edd221dc76c17f532ab5dc93a4b19a25624718b3a2d",
      "lfSha256": "7fed7106b40c946e0f113edd221dc76c17f532ab5dc93a4b19a25624718b3a2d",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "kgg-update/src/patches/v082-therapy-cockpit.html",
      "sha256": "94564723f8d292cf9cf23a88da3076c7cf6393e47880a6c50b06bdc7836ac673",
      "lfSha256": "94564723f8d292cf9cf23a88da3076c7cf6393e47880a6c50b06bdc7836ac673",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "kgg-update/src/patches/v085-ticket-015-progressions.html",
      "sha256": "43ed681276dac3f5394d3e05880fca683c1d3cc6dd44f00c5c50a4f9be599975",
      "lfSha256": "43ed681276dac3f5394d3e05880fca683c1d3cc6dd44f00c5c50a4f9be599975",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "kgg-update/src/patches/v090-ticket-015-admin-stage-gallery-drag-motion.html",
      "sha256": "bbae05b6d45927c7f14b19dcfe8b193cd0fcf1414b27adced0105e43e06ad1e6",
      "lfSha256": "bbae05b6d45927c7f14b19dcfe8b193cd0fcf1414b27adced0105e43e06ad1e6",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "kgg-update/src/patches/v093-cockpit-shared-editor.html",
      "sha256": "76da5d4c09e1b941127b0cb1b0ea7873c4ae7436708ed3c5779b8e362f2de42b",
      "lfSha256": "76da5d4c09e1b941127b0cb1b0ea7873c4ae7436708ed3c5779b8e362f2de42b",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "kgg-update/src/runtime/app-core.html",
      "sha256": "80548924281b10af79c1d2645a60956b42728a905ac934e5c0b8e3d09447149f",
      "lfSha256": "80548924281b10af79c1d2645a60956b42728a905ac934e5c0b8e3d09447149f",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "kgg-update/version.json",
      "sha256": "44407021580e051dd1719882c921a0aa477ccf59660f7966bec8171a36ad237f",
      "lfSha256": "44407021580e051dd1719882c921a0aa477ccf59660f7966bec8171a36ad237f",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-card-settings.js",
      "sha256": "06c04bcb84d6eec3bad892f48c1434f6aab7060e0601bfe2a01eb417405ee045",
      "lfSha256": "06c04bcb84d6eec3bad892f48c1434f6aab7060e0601bfe2a01eb417405ee045",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-day-history.js",
      "sha256": "2e904b1b6578aef5a7fccc5128bc633c5367c966b4eb5dd484e79a98bdf7661e",
      "lfSha256": "c8664dff338e682fbf2df380d05aeee8daeecce5b7afa1beb812fe8d5d5414c0",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-i18n.js",
      "sha256": "efc1a0b7fbc9bce500951b36d35a21d9b615d4294efa7a5f91faf1e06cbaf898",
      "lfSha256": "efc1a0b7fbc9bce500951b36d35a21d9b615d4294efa7a5f91faf1e06cbaf898",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-install-guide.js",
      "sha256": "11d2fb9edd3f290a4f75bd7a1526daee53faa55bccbe041129f3f04fdf729e86",
      "lfSha256": "0ff8e9e3c7802f2891873762e66770d3c8e38230011cacee0eed4e6a390e8643",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-last-value-hints.js",
      "sha256": "879131abf73d0e66234abe33670c43e9eb963a1371527262db617ee1a817d685",
      "lfSha256": "879131abf73d0e66234abe33670c43e9eb963a1371527262db617ee1a817d685",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-media-retry-cache_v2.js",
      "sha256": "1ae19634aa7973dbe1546333b7d2e6d0138e04e175290ce2e11310092a4651ca",
      "lfSha256": "1ae19634aa7973dbe1546333b7d2e6d0138e04e175290ce2e11310092a4651ca",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-multiplan-db.js",
      "sha256": "40946ffbc7200254f9f813dc0a6048437171256e7f2f2de9470c78d4338528eb",
      "lfSha256": "40946ffbc7200254f9f813dc0a6048437171256e7f2f2de9470c78d4338528eb",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-plan-delete.js",
      "sha256": "2b37629bfbabb202e04c04cec8f6a883c173343411a4c57814771b9fb5b43ad7",
      "lfSha256": "273f3c1a9e8d76161e924e4c03d55afd1e0266502215531daf09c2ed01903073",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-plan-link-choice.js",
      "sha256": "19e7edb65e02717b8e36f0062e6422b0bffb3b4e9987e4b31638fb7cea2d0917",
      "lfSha256": "786a6663c4eb5ab5fcd8681a940401aa92b4450f1f2f11c0b5f00b9310adee16",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-qr-fullscreen.js",
      "sha256": "a9245be9a5bbc7d1582b42a587b7de72d4261b9f6946dd196edb74992b3e23dc",
      "lfSha256": "0485f687e98c3e03a45414f0459ac1b8958dfab9ad795fd07f76409e07160c07",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-react-dist/kgg-patient-ui.js",
      "sha256": "57d37fa3dacfddcd1050b7507436ba5f3499d8eaa678cedcce87f8054161c9f8",
      "lfSha256": "57d37fa3dacfddcd1050b7507436ba5f3499d8eaa678cedcce87f8054161c9f8",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-set-compact-view.js",
      "sha256": "b9a7218388913774d7d151cced14a29522ebcc6f95dd8bad50b96f2d50a4e533",
      "lfSha256": "b9a7218388913774d7d151cced14a29522ebcc6f95dd8bad50b96f2d50a4e533",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-set-summary-groups.js",
      "sha256": "505c5aab315c2d4d955c75c17f6514be04b88f24d81289376008e6f2a066974c",
      "lfSha256": "505c5aab315c2d4d955c75c17f6514be04b88f24d81289376008e6f2a066974c",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-ui-micro-polish.js",
      "sha256": "5bce46af62a0b793da0a850121429c704ac8294150aea0c1fcd148e3eda767a2",
      "lfSha256": "5bce46af62a0b793da0a850121429c704ac8294150aea0c1fcd148e3eda767a2",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-ui/src/legacy-numpad/LegacyNumpadHeader.tsx",
      "sha256": "16c2b4870d35d165dd7ec2f6d8fe74ca6e8dbd087a37afd4b99fb62b49bfae78",
      "lfSha256": "16c2b4870d35d165dd7ec2f6d8fe74ca6e8dbd087a37afd4b99fb62b49bfae78",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-version-label.js",
      "sha256": "8aacac7fc3e25380200e5bef46d7055b421cfe6189a8af8116bc759b540187b3",
      "lfSha256": "8aacac7fc3e25380200e5bef46d7055b421cfe6189a8af8116bc759b540187b3",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "service-worker.js",
      "sha256": "025613ed790cb2796f64c41fc9720c1b5a5d8495968503a725e49f88a3c3e6cc",
      "lfSha256": "025613ed790cb2796f64c41fc9720c1b5a5d8495968503a725e49f88a3c3e6cc",
      "parent": "English-scanner-ref-only"
    },
    {
      "file": "update-recovery.html",
      "sha256": "6f57568a48f65daaf63492d4c7098a76171dbe55bb8ca9b51a2fde6e3fcb11e3",
      "lfSha256": "6f57568a48f65daaf63492d4c7098a76171dbe55bb8ca9b51a2fde6e3fcb11e3",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-start-scan.js",
      "sha256": "f458b586572fc381195057be9ba56e86b0a29b70809bb1177a892abb6deb00ec",
      "lfSha256": "f458b586572fc381195057be9ba56e86b0a29b70809bb1177a892abb6deb00ec",
      "parent": "Main-exact"
    }
  ],
  "tests": [
    {
      "file": "release-pipeline/kgg_english_progression_baseline_playwright.js",
      "sha256": "e865fdc5e8ed2b3d9388f18c1e1394097f665344c8ccacded228cd155d4c05f3"
    },
    {
      "file": "release-pipeline/kgg_english_metadata_smoke.js",
      "sha256": "a6490412d1d2a835158a32176d80132a7a398d61ee8d5c507cf4a4fbcc7cdeb2"
    },
    {
      "file": "release-pipeline/kgg_english_editor_playwright.js",
      "sha256": "515933e9f591fb7ca624256b169cbe07752c6bcd851ef56082e21074f0775fd6"
    },
    {
      "file": "release-pipeline/kgg_english_cockpit_smoke.js",
      "sha256": "1f99bd139bf1bf6dc1c4f064f5d8160ce4b213c80ade02b0371cfe9e96cc0595"
    },
    {
      "file": "release-pipeline/kgg_english_cockpit_playwright.js",
      "sha256": "4fe7eda0ab021996600fb0e45085a4019290cfdfef80bf4ffbdd242403e00f67"
    },
    {
      "file": "release-pipeline/kgg_dual_device_package.js",
      "sha256": "0b5c79fa0b7324cecf2768b397b6e1a4d88e27eecdfbbcce053e39578a7e4047"
    },
    {
      "file": "release-pipeline/kgg_patient_english_title_playwright.js",
      "sha256": "a961c1f1f3069993475832855cee09fd5159dad48dd40340055382ea6bc3e757"
    },
    {
      "file": "release-pipeline/kgg_patient_english_summary_smoke.js",
      "sha256": "6549062a8af1064189af604b07a55c7ac82039a4d357bd8ae835574c484c8994"
    },
    {
      "file": "release-pipeline/kgg_patient_english_summary_playwright.js",
      "sha256": "9a3a1042f93e050cbd515e6b464675d5fc6355bfccb8d69d47cd6ed602805b99"
    },
    {
      "file": "release-pipeline/kgg_patient_english_review_playwright.js",
      "sha256": "40e04374b14d3ec0c2221be54069f499406fa114aa9f76d5e3ecbd52983d5c9c"
    },
    {
      "file": "release-pipeline/kgg_patient_english_playwright.js",
      "sha256": "28b9d3b0153570b040491ca2241660b30a0cddb708b97dbdd4825c054cecd0af"
    },
    {
      "file": "release-pipeline/kgg_patient_english_compatibility_playwright.js",
      "sha256": "0fbda81a25fd236d4af0cca5f872309e6ba1fd9656870d2790bb51fb19802f03"
    },
    {
      "file": "release-pipeline/kgg_patient_import_session_values_playwright.js",
      "sha256": "e426348734f1e01571321dd49459606de26af747f6c60c30c6731eff1d091aed"
    },
    {
      "file": "release-pipeline/kgg_patient_gpt_write_gate.py",
      "sha256": "db621e231bfea72dd2addaca3b3db942b3a26e084f6aefef2a44eda81c349cd1"
    },
    {
      "file": "release-pipeline/kgg_patient_preview_first_load_smoke.js",
      "sha256": "37db546492635a4f27d51320d9cc46e6dfa72c00b264c07a670a61a61c9ad6a4"
    },
    {
      "file": "release-pipeline/kgg_patient_qr_v81_device_ladder.js",
      "sha256": "52b9b9c6eac8bb11e4529b507a6c4a94e46bbb5f8acdc28d177a2e27af1883e9"
    },
    {
      "file": "release-pipeline/kgg_patient_preview_storage_isolation_smoke.js",
      "sha256": "a0485ad60ca432c254ffd78a8155d9aea22f87a1781fc60f22c908fe26bbf40b"
    },
    {
      "file": "release-pipeline/kgg_pwa_contract_smoke.py",
      "sha256": "ad7a8448bd6cf2a305bb4cbf75def1022ed75470d5897304a9ebc2a2f5046b27"
    },
    {
      "file": "release-pipeline/kgg_test_battery.py",
      "sha256": "7dff67422c62e77f3dd5f88b64ce632d8759b796bd0e37f6b09346f0651446ac"
    }
  ],
  "previousFreezeManifestSha256": "aed26db8b869690c1eed07322203b795b08e57fe99a6a5dc5b4d78f0507d00ee",
  "previousPwaContractSha256": "74d973ebae4dcb4e8be42fdaa0bbcfe90dead17e7dd57ae00dbf93d9b15b5e94",
  "generatedEvidence": [
    {
      "file": "docs/kgg-custom-gpt-editor-snapshot.json",
      "sha256": "a8d5191975add6c81713c3b803205130c3e08342f6a6e9f552498709323f87f2"
    },
    {
      "file": "docs/kgg-custom-gpt-knowledge-pack.md",
      "sha256": "a23f0929f9a8711e527f4359a84cdc0723879f91e66c049195f86eec8890efa5"
    },
    {
      "file": "docs/kgg-custom-gpt-knowledge-safety.md",
      "sha256": "9c7b48617c50be2581ed6223011a45c0e5f75c4d3d766452a4b05f87d5d8c9ee"
    },
    {
      "file": "docs/kgg-custom-gpt-resource-manifest.json",
      "sha256": "cedcc131e5d66b62ec05eadb84552fbc6f588fb24e57435e7aee5a0e4225e0ad"
    },
    {
      "file": "docs/kgg-gpt-bug-index.json",
      "sha256": "d3c7001351d03a722ad50a8f6e79ee0f0d0d533f1eeb96da6735b55ffa2310c1"
    },
    {
      "file": "docs/kgg-gpt-bug-lessons.md",
      "sha256": "6155e1b3501ffba0aef79a1fb05eb85ba15f573198a6d5c6202a0c7006098e33"
    },
    {
      "file": "docs/kgg-patient-custom-gpt-editor-snapshot.json",
      "sha256": "d31c86bdb68c26a9878eb1efa5cb05a953f7ef8b94b8eacd697dfb5b2feb05dc"
    },
    {
      "file": "docs/kgg-patient-custom-gpt-knowledge-safety.md",
      "sha256": "1622b825d6b3c0a24c6c322f51b18c43d1a8c3a293f44d7740deeb9f05790277"
    },
    {
      "file": "docs/kgg-patient-custom-gpt-knowledge-testing.md",
      "sha256": "04e1c2f5e1644777cd37cd1a91155e3c4830af91d6882f535920f81845c9b35e"
    },
    {
      "file": "docs/kgg-patient-gpt-source-index.json",
      "sha256": "b2f676798f1bdc7e824ab9556cd8a726514c4d7284c513ecbd07bed3d5ee2fe2"
    },
    {
      "file": "docs/kgg-patient-gpt-source/chunk-001.md",
      "sha256": "e561bab5a9dd148ef2cec684f2e2e837a9443c0bae956642eb121ed4652addc8"
    },
    {
      "file": "docs/kgg-patient-gpt-source/chunk-002.md",
      "sha256": "0d7ca5e77f92d1c883195aa7d1bc75ea7c426ed318131d339b63640e94850c51"
    },
    {
      "file": "docs/kgg-patient-gpt-source/chunk-003.md",
      "sha256": "e8a04e0c222effc3df0d62b121d3d3d40139c234da522bc09c09c78dcc83b210"
    },
    {
      "file": "docs/kgg-patient-gpt-source/chunk-034.md",
      "sha256": "14abffef2ee4dbc74ab67e5f4076fd796a80d34f5361ca93ba95726601753150"
    },
    {
      "file": "docs/kgg-patient-gpt-source/chunk-035.md",
      "sha256": "52a169096884ccdab28cd7f57932351895e233db901880995291b83b982018e8"
    }
  ],
  "manifestSha256": "296b09d6a243b618c8de16e12a7435a6c5ceeefd455695387dd35f5136e1cddb"
}
```


### Main-Abgleich — gezielte Kombigates / Freeze2

2026-10-15T07:14:38Z: unabhängiger enger Code-/Generated-Recheck PASS, keine offenen Findings; Start/End32Produkte+19Tests+15GeneratedEvidence=66/66 stabil. Alle nachfolgenden Writer-Gates binden Freeze2 `296b09d6a243b618c8de16e12a7435a6c5ceeefd455695387dd35f5136e1cddb`; keine Produkt-/Teständerung während der Läufe.

Bestehender DualDevice-self-test PASS. Zusätzlich tatsächlich gebautes synthetisches Paket geprüft: Helperbytes exakt aus vorhandener Storage-Isolationstransformation, genau eine auflösbare Indexreferenz; tatsächlich kopierter Storageadapter und Helper im VM-Kontext ausgeführt. Isolierte Locale-/authored-EN-Map gelesen, native Locale-/Planbytes unverändert. Paketmetadaten nennen als synthetischen sourceSha den damaligen Parent-HEAD, nicht einen noch nicht existierenden Mergecommit; Kandidatennachweis sind die separat gebundenen tatsächlichen Freeze-/Paketbytes. [Paketprotokoll](/C:/src/kgg-worktrees/patient-english-complete-20261014/output/patient-english-main-alignment-20261015-r2-freeze2/package.log).

Neun seriell ausgeführte projektinterne Headlessgates Exit0 PASS (zusammen 144.23s): Import update/add/replace/replace-link inkl. Reload/leerer echter Inputs/leerer Summary/alter Storagebytes; vollständige EnglishBank/UI Legacy+React; echter Editor→Bankreload→Plan→KGGH3→deutscherReturnQR; strukturierte Summary; H3-Sprachroundtrip; echter Cockpit-Editor; authored-content/Install/Status/DB-Review; zwei frische Cacheläufe f59/v90→v93 und fest4bbe/v92→v93. Beide beweisen aktive Altworker-Version per GET_APP_VERSION, Ziel93 vor und nach echtem Offline-Coldreload sowie erhaltene rohe Daten/EN-Metadaten. Summary-/Titelrunner binden die tatsächlich servierten vier Ressourcenkörper. Vor/nach jedem Gate32/19/15Hashes unverändert. [Ergebnisliste](/C:/src/kgg-worktrees/patient-english-complete-20261014/output/patient-english-main-alignment-20261015-r2-freeze2/targeted-results.json); Einzelprotokolle im selben Verzeichnis.

Zusätzlich kleine CLI-Gates: Preview-write_gate-Selbsttest, PlanSlot, Planlink, QRwire und Recovery PASS. Normal erzeugtes isoliertes Previewfixture v94 aus dem Quellkandidaten93; keine Produktversionserhöhung. Runtime `output/patient-english-main-alignment-20261015-r2-freeze2/preview-fixture/previews/patient-gate-self-test`, RequestId `patient-gate-self-test`. Korrekter bestehender Storage-Isolationvertrag: liveRoot, previewRuntime, requestId.

Alle Writer-Browser/Contexts und lokalen Server via finally geschlossen, Lease an den von Root koordinierten unabhängigen Browserauditor abgegeben. Dessen betroffene UI-/Preview-Firstload-/Storage-Isolationsabnahme, regulärer vollständiger Hook, Commit/Push und aktuelle Head-CI noch offen. Keine Vorab-Vollbatterie, kein Merge nach Main/Release/Manifest/APK.


### Main-Abgleich — Revision3 / Finishdialog-Freeze1

2026-10-15T07:40:14Z: unabhängige Freeze2-IAB-/Headlessabnahme beendet, einzig neuer Important: der bisher nicht übersetzte Ticket034-Finishdialog zeigte nach Stage/Wert→CurrentQR→Back→Reload in beiden Padmodes deutsche ARIA/Message/Buttons über englischem Hintergrund. Root-/Cloud-Minimalplan angenommen; Revision3 nur ein zusätzlicher Produktpfad patient-card-progress.js. Alle32bisherigen Produkt-Arbeitsdateien bleiben exakt Freeze2. Ziel93/Therapeutsource96 weiter unveröffentlicht.

Kleinster Producerfix: bestehendes language() und vorhandenes exerciseName(rawName) für reine Finish-Copy; aktueller offener Kandidat weiterhin ausschließlich über bestehenden ersten Pending-Index. Vorhandene Nodes/ARIA/Text nur bei tatsächlicher Abweichung aktualisieren; vorhandenes updateAll/List-Observer-Sprachschreibersignal wiederverwendet. Keine zusätzlichen Listener/Observer, Namenscache, Kandidatenauswahl, Counter-/Pending-/Confirm-/Cancel-/Storage-/QR-/Fokus-/Stylingänderung.

Drei bestehende Tests eng ergänzt. Auf unverändertem Producer (SHA unten) zwei RED-Protokolle: Copy-Vertrag fehlt; echter Titelrunner Legacy+React reproduziert EN-ARIA/Message/Buttons und authored/unknown-Roundtrips. Der erste neue Testentwurf enthielt zusätzlich zu strikte Datenannahmen: bestehender summary-wrapShowQr finalisiert/speichert Dominanz bereits vor dem Modal und ergänzt QR-Progressionsslots; Confirm führt den normalen Tages-/Historywechsel aus. Root verifizierte den bestehenden Pfad. Ausschließlich neue Assertions fachlich korrigiert: Sprach-/Cancel-Statebaseline direkt nach tatsächlichem Modalöffnen; Confirm-Rows aus dem echten vorherigen CurrentQR statt kurzer rows()-Form; Werte sowie vorhandene Day/Done/Counter-Outcomes statt unzulässiger History-Stillstandsannahme. Keine bestehende Assertion entfernt, kein Businesscode umgeordnet. Historische REDs bleiben offen einsehbar.

Danach CardProgress-VM GREEN (realer Helper, DE-Original, CalfRaise, exakte authored Interpunktion, unknown/noProvider-Rawfallback). Echter Titelrunner **144/144 Assertions PASS** in Legacy+React, fünf tatsächlich servierte Ressourcen gebunden: Stage/Wert→CurrentQR→Back→Reload→Finish, offener EN→DE→EN-Handlervertrag mit unveränderten Modalnodes/Confirmfokus; tatsächlicher Cancel mit Fokusrestore und unverändertem State ab Modalöffnung; erneutes Öffnen/Confirm mit kanonischen echten QR-Rows, einmaligem Counter, Day2/Done1 und unveränderten Trainingswerten; zusätzliche authored/unknown-Namen mit Doppelpunkten, Gedankenstrich und Pfeil. Der Header ist durch Backdrop für Pointer blockiert; der offene Sprachroundtrip ist ausdrücklich bestehender Handlervertrag via DOMclick, kein physischer Pointer-Nachweis.

Bestehender PatientResources-Generator aktualisierte genau source-index.json und source/chunk-009.md (Producer17926Bytes, unter24k); keine weiteren Quellchunks/Digests/Profilfelder geändert. Sechs Freshnesschecks PASS, audit TARGET_PASS. Dokumentierter RED-/GREEN-Logpfad im Manifest. Beide v90/v92→93+Offline-Modalgates und bestehender ContinuousDays-Schutz sowie unabhängiger betroffener Code/UI-Recheck jetzt offen; noch kein regulärer FullHook/Commit/Push/neueCI. Keine erneute volle9Batterie.

```json
{
  "id": "main-alignment-r3-finish-freeze1",
  "task_id": "patient-english-main-alignment-20261015",
  "generation": 2,
  "revision": 3,
  "englishParent": "d34e90f6ef4890e345c1559e75e2a5c22df4d27a",
  "mainParent": "4bbe3905126741c042e21331d7485067470b6640",
  "products": [
    {
      "file": "collapse-cards.js",
      "sha256": "ac8afec81349ecb3ae8d9b5dd9fd9a39c476d4dedc7148907939ebd4fae8aafc",
      "lfSha256": "ac8afec81349ecb3ae8d9b5dd9fd9a39c476d4dedc7148907939ebd4fae8aafc",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "index.html",
      "sha256": "12f4d469d042909d6e7b0b835b16616a0a6a35602fac18b6ada7fc6753c56b76",
      "lfSha256": "12f4d469d042909d6e7b0b835b16616a0a6a35602fac18b6ada7fc6753c56b76",
      "parent": "English-scanner-ref-only"
    },
    {
      "file": "kgg-update/index.html",
      "sha256": "d9e4edcda8afd4cdfc821b4e9d155483a726cec4e9c4603e4eeee4b94a0bf2d3",
      "lfSha256": "d9e4edcda8afd4cdfc821b4e9d155483a726cec4e9c4603e4eeee4b94a0bf2d3",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "kgg-update/src/document/body-shell.html",
      "sha256": "52fc54134ed60677b787d798a1caf21f86215f17f467bad532e52f2e9236cc80",
      "lfSha256": "52fc54134ed60677b787d798a1caf21f86215f17f467bad532e52f2e9236cc80",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "kgg-update/src/document/head-ui.html",
      "sha256": "c74cca199993b498cbb9d50de132c1fa5dd5a0f89b1e468165b54e7cc18fd9bb",
      "lfSha256": "c74cca199993b498cbb9d50de132c1fa5dd5a0f89b1e468165b54e7cc18fd9bb",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "kgg-update/src/metadata/changelog.html",
      "sha256": "a919cbbe18ba7d8015b561699e5a1e44cc153452c8583b9188bc5d0c26a17f27",
      "lfSha256": "a919cbbe18ba7d8015b561699e5a1e44cc153452c8583b9188bc5d0c26a17f27",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "kgg-update/src/metadata/source-truth.html",
      "sha256": "7fed7106b40c946e0f113edd221dc76c17f532ab5dc93a4b19a25624718b3a2d",
      "lfSha256": "7fed7106b40c946e0f113edd221dc76c17f532ab5dc93a4b19a25624718b3a2d",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "kgg-update/src/patches/v082-therapy-cockpit.html",
      "sha256": "94564723f8d292cf9cf23a88da3076c7cf6393e47880a6c50b06bdc7836ac673",
      "lfSha256": "94564723f8d292cf9cf23a88da3076c7cf6393e47880a6c50b06bdc7836ac673",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "kgg-update/src/patches/v085-ticket-015-progressions.html",
      "sha256": "43ed681276dac3f5394d3e05880fca683c1d3cc6dd44f00c5c50a4f9be599975",
      "lfSha256": "43ed681276dac3f5394d3e05880fca683c1d3cc6dd44f00c5c50a4f9be599975",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "kgg-update/src/patches/v090-ticket-015-admin-stage-gallery-drag-motion.html",
      "sha256": "bbae05b6d45927c7f14b19dcfe8b193cd0fcf1414b27adced0105e43e06ad1e6",
      "lfSha256": "bbae05b6d45927c7f14b19dcfe8b193cd0fcf1414b27adced0105e43e06ad1e6",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "kgg-update/src/patches/v093-cockpit-shared-editor.html",
      "sha256": "76da5d4c09e1b941127b0cb1b0ea7873c4ae7436708ed3c5779b8e362f2de42b",
      "lfSha256": "76da5d4c09e1b941127b0cb1b0ea7873c4ae7436708ed3c5779b8e362f2de42b",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "kgg-update/src/runtime/app-core.html",
      "sha256": "80548924281b10af79c1d2645a60956b42728a905ac934e5c0b8e3d09447149f",
      "lfSha256": "80548924281b10af79c1d2645a60956b42728a905ac934e5c0b8e3d09447149f",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "kgg-update/version.json",
      "sha256": "44407021580e051dd1719882c921a0aa477ccf59660f7966bec8171a36ad237f",
      "lfSha256": "44407021580e051dd1719882c921a0aa477ccf59660f7966bec8171a36ad237f",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-card-settings.js",
      "sha256": "06c04bcb84d6eec3bad892f48c1434f6aab7060e0601bfe2a01eb417405ee045",
      "lfSha256": "06c04bcb84d6eec3bad892f48c1434f6aab7060e0601bfe2a01eb417405ee045",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-day-history.js",
      "sha256": "2e904b1b6578aef5a7fccc5128bc633c5367c966b4eb5dd484e79a98bdf7661e",
      "lfSha256": "c8664dff338e682fbf2df380d05aeee8daeecce5b7afa1beb812fe8d5d5414c0",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-i18n.js",
      "sha256": "efc1a0b7fbc9bce500951b36d35a21d9b615d4294efa7a5f91faf1e06cbaf898",
      "lfSha256": "efc1a0b7fbc9bce500951b36d35a21d9b615d4294efa7a5f91faf1e06cbaf898",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-install-guide.js",
      "sha256": "11d2fb9edd3f290a4f75bd7a1526daee53faa55bccbe041129f3f04fdf729e86",
      "lfSha256": "0ff8e9e3c7802f2891873762e66770d3c8e38230011cacee0eed4e6a390e8643",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-last-value-hints.js",
      "sha256": "879131abf73d0e66234abe33670c43e9eb963a1371527262db617ee1a817d685",
      "lfSha256": "879131abf73d0e66234abe33670c43e9eb963a1371527262db617ee1a817d685",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-media-retry-cache_v2.js",
      "sha256": "1ae19634aa7973dbe1546333b7d2e6d0138e04e175290ce2e11310092a4651ca",
      "lfSha256": "1ae19634aa7973dbe1546333b7d2e6d0138e04e175290ce2e11310092a4651ca",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-multiplan-db.js",
      "sha256": "40946ffbc7200254f9f813dc0a6048437171256e7f2f2de9470c78d4338528eb",
      "lfSha256": "40946ffbc7200254f9f813dc0a6048437171256e7f2f2de9470c78d4338528eb",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-plan-delete.js",
      "sha256": "2b37629bfbabb202e04c04cec8f6a883c173343411a4c57814771b9fb5b43ad7",
      "lfSha256": "273f3c1a9e8d76161e924e4c03d55afd1e0266502215531daf09c2ed01903073",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-plan-link-choice.js",
      "sha256": "19e7edb65e02717b8e36f0062e6422b0bffb3b4e9987e4b31638fb7cea2d0917",
      "lfSha256": "786a6663c4eb5ab5fcd8681a940401aa92b4450f1f2f11c0b5f00b9310adee16",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-qr-fullscreen.js",
      "sha256": "a9245be9a5bbc7d1582b42a587b7de72d4261b9f6946dd196edb74992b3e23dc",
      "lfSha256": "0485f687e98c3e03a45414f0459ac1b8958dfab9ad795fd07f76409e07160c07",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-react-dist/kgg-patient-ui.js",
      "sha256": "57d37fa3dacfddcd1050b7507436ba5f3499d8eaa678cedcce87f8054161c9f8",
      "lfSha256": "57d37fa3dacfddcd1050b7507436ba5f3499d8eaa678cedcce87f8054161c9f8",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-set-compact-view.js",
      "sha256": "b9a7218388913774d7d151cced14a29522ebcc6f95dd8bad50b96f2d50a4e533",
      "lfSha256": "b9a7218388913774d7d151cced14a29522ebcc6f95dd8bad50b96f2d50a4e533",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-set-summary-groups.js",
      "sha256": "505c5aab315c2d4d955c75c17f6514be04b88f24d81289376008e6f2a066974c",
      "lfSha256": "505c5aab315c2d4d955c75c17f6514be04b88f24d81289376008e6f2a066974c",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-ui-micro-polish.js",
      "sha256": "5bce46af62a0b793da0a850121429c704ac8294150aea0c1fcd148e3eda767a2",
      "lfSha256": "5bce46af62a0b793da0a850121429c704ac8294150aea0c1fcd148e3eda767a2",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-ui/src/legacy-numpad/LegacyNumpadHeader.tsx",
      "sha256": "16c2b4870d35d165dd7ec2f6d8fe74ca6e8dbd087a37afd4b99fb62b49bfae78",
      "lfSha256": "16c2b4870d35d165dd7ec2f6d8fe74ca6e8dbd087a37afd4b99fb62b49bfae78",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-version-label.js",
      "sha256": "8aacac7fc3e25380200e5bef46d7055b421cfe6189a8af8116bc759b540187b3",
      "lfSha256": "8aacac7fc3e25380200e5bef46d7055b421cfe6189a8af8116bc759b540187b3",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "service-worker.js",
      "sha256": "025613ed790cb2796f64c41fc9720c1b5a5d8495968503a725e49f88a3c3e6cc",
      "lfSha256": "025613ed790cb2796f64c41fc9720c1b5a5d8495968503a725e49f88a3c3e6cc",
      "parent": "English-scanner-ref-only"
    },
    {
      "file": "update-recovery.html",
      "sha256": "6f57568a48f65daaf63492d4c7098a76171dbe55bb8ca9b51a2fde6e3fcb11e3",
      "lfSha256": "6f57568a48f65daaf63492d4c7098a76171dbe55bb8ca9b51a2fde6e3fcb11e3",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-start-scan.js",
      "sha256": "f458b586572fc381195057be9ba56e86b0a29b70809bb1177a892abb6deb00ec",
      "lfSha256": "f458b586572fc381195057be9ba56e86b0a29b70809bb1177a892abb6deb00ec",
      "parent": "Main-exact"
    },
    {
      "file": "patient-card-progress.js",
      "sha256": "5151406061f51bd6cd90e979874237e90f87e1972a9d31ee3fac698ad769cf8f",
      "lfSha256": "cc6179f83d1a7327f90adc5d12e4cedb47b26edfd6c1d07cf069dc5d48fee557",
      "parent": "English-additional-finish-copy-only"
    }
  ],
  "tests": [
    {
      "file": "release-pipeline/kgg_english_progression_baseline_playwright.js",
      "sha256": "e865fdc5e8ed2b3d9388f18c1e1394097f665344c8ccacded228cd155d4c05f3"
    },
    {
      "file": "release-pipeline/kgg_english_metadata_smoke.js",
      "sha256": "a6490412d1d2a835158a32176d80132a7a398d61ee8d5c507cf4a4fbcc7cdeb2"
    },
    {
      "file": "release-pipeline/kgg_english_editor_playwright.js",
      "sha256": "515933e9f591fb7ca624256b169cbe07752c6bcd851ef56082e21074f0775fd6"
    },
    {
      "file": "release-pipeline/kgg_english_cockpit_smoke.js",
      "sha256": "1f99bd139bf1bf6dc1c4f064f5d8160ce4b213c80ade02b0371cfe9e96cc0595"
    },
    {
      "file": "release-pipeline/kgg_english_cockpit_playwright.js",
      "sha256": "4fe7eda0ab021996600fb0e45085a4019290cfdfef80bf4ffbdd242403e00f67"
    },
    {
      "file": "release-pipeline/kgg_dual_device_package.js",
      "sha256": "0b5c79fa0b7324cecf2768b397b6e1a4d88e27eecdfbbcce053e39578a7e4047"
    },
    {
      "file": "release-pipeline/kgg_patient_english_title_playwright.js",
      "sha256": "dd0d3291b55102bdabba84e7db02d5fcf824d60c0d319e1b9dc62c82319c92ee"
    },
    {
      "file": "release-pipeline/kgg_patient_english_summary_smoke.js",
      "sha256": "6549062a8af1064189af604b07a55c7ac82039a4d357bd8ae835574c484c8994"
    },
    {
      "file": "release-pipeline/kgg_patient_english_summary_playwright.js",
      "sha256": "9a3a1042f93e050cbd515e6b464675d5fc6355bfccb8d69d47cd6ed602805b99"
    },
    {
      "file": "release-pipeline/kgg_patient_english_review_playwright.js",
      "sha256": "40e04374b14d3ec0c2221be54069f499406fa114aa9f76d5e3ecbd52983d5c9c"
    },
    {
      "file": "release-pipeline/kgg_patient_english_playwright.js",
      "sha256": "28b9d3b0153570b040491ca2241660b30a0cddb708b97dbdd4825c054cecd0af"
    },
    {
      "file": "release-pipeline/kgg_patient_english_compatibility_playwright.js",
      "sha256": "eae06368c3521f91cff58b01fe80cc4272213ff539a5df0dc4a82b463317cecb"
    },
    {
      "file": "release-pipeline/kgg_patient_import_session_values_playwright.js",
      "sha256": "e426348734f1e01571321dd49459606de26af747f6c60c30c6731eff1d091aed"
    },
    {
      "file": "release-pipeline/kgg_patient_gpt_write_gate.py",
      "sha256": "db621e231bfea72dd2addaca3b3db942b3a26e084f6aefef2a44eda81c349cd1"
    },
    {
      "file": "release-pipeline/kgg_patient_preview_first_load_smoke.js",
      "sha256": "37db546492635a4f27d51320d9cc46e6dfa72c00b264c07a670a61a61c9ad6a4"
    },
    {
      "file": "release-pipeline/kgg_patient_qr_v81_device_ladder.js",
      "sha256": "52b9b9c6eac8bb11e4529b507a6c4a94e46bbb5f8acdc28d177a2e27af1883e9"
    },
    {
      "file": "release-pipeline/kgg_patient_preview_storage_isolation_smoke.js",
      "sha256": "a0485ad60ca432c254ffd78a8155d9aea22f87a1781fc60f22c908fe26bbf40b"
    },
    {
      "file": "release-pipeline/kgg_pwa_contract_smoke.py",
      "sha256": "ad7a8448bd6cf2a305bb4cbf75def1022ed75470d5897304a9ebc2a2f5046b27"
    },
    {
      "file": "release-pipeline/kgg_test_battery.py",
      "sha256": "7dff67422c62e77f3dd5f88b64ce632d8759b796bd0e37f6b09346f0651446ac"
    },
    {
      "file": "release-pipeline/kgg_patient_card_progress_smoke.js",
      "sha256": "aaf4a40d881884aec5bee71cab688a020763bdc2c60ee6d125f1af906f1b94b9"
    },
    {
      "file": "release-pipeline/kgg_patient_continuous_days_playwright.js",
      "sha256": "f4897ee618712948aaefe83cdc78f694282fea535100a3f09175a618783cd699"
    }
  ],
  "previousFreezeManifestSha256": "296b09d6a243b618c8de16e12a7435a6c5ceeefd455695387dd35f5136e1cddb",
  "previousPwaContractSha256": "74d973ebae4dcb4e8be42fdaa0bbcfe90dead17e7dd57ae00dbf93d9b15b5e94",
  "generatedEvidence": [
    {
      "file": "docs/kgg-custom-gpt-editor-snapshot.json",
      "sha256": "a8d5191975add6c81713c3b803205130c3e08342f6a6e9f552498709323f87f2"
    },
    {
      "file": "docs/kgg-custom-gpt-knowledge-pack.md",
      "sha256": "a23f0929f9a8711e527f4359a84cdc0723879f91e66c049195f86eec8890efa5"
    },
    {
      "file": "docs/kgg-custom-gpt-knowledge-safety.md",
      "sha256": "9c7b48617c50be2581ed6223011a45c0e5f75c4d3d766452a4b05f87d5d8c9ee"
    },
    {
      "file": "docs/kgg-custom-gpt-resource-manifest.json",
      "sha256": "cedcc131e5d66b62ec05eadb84552fbc6f588fb24e57435e7aee5a0e4225e0ad"
    },
    {
      "file": "docs/kgg-gpt-bug-index.json",
      "sha256": "d3c7001351d03a722ad50a8f6e79ee0f0d0d533f1eeb96da6735b55ffa2310c1"
    },
    {
      "file": "docs/kgg-gpt-bug-lessons.md",
      "sha256": "6155e1b3501ffba0aef79a1fb05eb85ba15f573198a6d5c6202a0c7006098e33"
    },
    {
      "file": "docs/kgg-patient-custom-gpt-editor-snapshot.json",
      "sha256": "d31c86bdb68c26a9878eb1efa5cb05a953f7ef8b94b8eacd697dfb5b2feb05dc"
    },
    {
      "file": "docs/kgg-patient-custom-gpt-knowledge-safety.md",
      "sha256": "1622b825d6b3c0a24c6c322f51b18c43d1a8c3a293f44d7740deeb9f05790277"
    },
    {
      "file": "docs/kgg-patient-custom-gpt-knowledge-testing.md",
      "sha256": "04e1c2f5e1644777cd37cd1a91155e3c4830af91d6882f535920f81845c9b35e"
    },
    {
      "file": "docs/kgg-patient-gpt-source-index.json",
      "sha256": "dcc0e22582bfe8247216e2383bb8d91c51b5eaa087fb37f035a317a4fc4ba802"
    },
    {
      "file": "docs/kgg-patient-gpt-source/chunk-001.md",
      "sha256": "e561bab5a9dd148ef2cec684f2e2e837a9443c0bae956642eb121ed4652addc8"
    },
    {
      "file": "docs/kgg-patient-gpt-source/chunk-002.md",
      "sha256": "0d7ca5e77f92d1c883195aa7d1bc75ea7c426ed318131d339b63640e94850c51"
    },
    {
      "file": "docs/kgg-patient-gpt-source/chunk-003.md",
      "sha256": "e8a04e0c222effc3df0d62b121d3d3d40139c234da522bc09c09c78dcc83b210"
    },
    {
      "file": "docs/kgg-patient-gpt-source/chunk-009.md",
      "sha256": "e1f7dcae94cb45d1679807fac69a8b96d11d6eab930a237274e945a5839645ed"
    },
    {
      "file": "docs/kgg-patient-gpt-source/chunk-034.md",
      "sha256": "14abffef2ee4dbc74ab67e5f4076fd796a80d34f5361ca93ba95726601753150"
    },
    {
      "file": "docs/kgg-patient-gpt-source/chunk-035.md",
      "sha256": "52a169096884ccdab28cd7f57932351895e233db901880995291b83b982018e8"
    }
  ],
  "redProducerSha256": "b5b3737577c21d482365e19cf41b4ddea9270ba22c30230ad5f2833e12fa5da9",
  "redGreenEvidence": [
    {
      "file": "output/patient-english-main-alignment-20261015-r3/card-progress-red.log",
      "sha256": "d14753cbecd7a8bbd81541630b9855253a03684687c765cac4265a629a459fb6"
    },
    {
      "file": "output/patient-english-main-alignment-20261015-r3/finish-title-red.log",
      "sha256": "7b70208af402ca9d9c1e2555549640e954e40a1dead4d160708efa07d1c665ce"
    },
    {
      "file": "output/patient-english-main-alignment-20261015-r3/card-progress-green.log",
      "sha256": "c4f237559f22e0aef60010218df101c354f3c9a05286f80fd7ff720f7be6baab"
    },
    {
      "file": "output/patient-english-main-alignment-20261015-r3/finish-title-green.log",
      "sha256": "d9b1447f77a36c65896bc334e8f0e4ee467da4dc8b0f12089a262f22f06c429d"
    }
  ],
  "manifestSha256": "88c3eb46935f99f157d4e727358b2cff165fa9c2cb22171a088f691265adbb92"
}
```


### Main-Abgleich — Revision3 gezielte GREEN-Abnahme

2026-10-15T07:42:38Z: gegen unveränderten 33er-Freeze `88c3eb46935f99f157d4e727358b2cff165fa9c2cb22171a088f691265adbb92` alle eng betroffenen Writer-Gates Exit0 PASS. CardProgress-VM und Titel144/144 wie oben; zusätzlich beide festgepinnten realen v90/v92→v93-Serviceworker-Upgrades mit anschließender echter Offline-Coldreload und tatsächlich geöffnetem/canceltem korrigiertem Dialog. EN-ARIA/Message/Buttons und exakter authored Anzeigename aus bestehender Map sowie volle Statebytes ab Modalöffnung erhalten. No-store allein wurde nicht als Offlinebeweis verwendet. [Ergebnisliste](/C:/src/kgg-worktrees/patient-english-complete-20261014/output/patient-english-main-alignment-20261015-r3/finish-targeted-results.json), [v90-Dialog](/C:/src/kgg-worktrees/patient-english-complete-20261014/output/patient-english-main-alignment-20261015-r3/offline-modal-v90.log), [v92-Dialog](/C:/src/kgg-worktrees/patient-english-complete-20261014/output/patient-english-main-alignment-20261015-r3/offline-modal-v92.log).

Bestehender ContinuousDays-Schutz mit realem Finish PASS: T7→8, T12→13 plus Reload, T99→100/paginierteHistory, historischer Abschluss erhält die Front, unabhängige Tage in mehreren Plänen und begrenzter fixer Plan. [Protokoll](/C:/src/kgg-worktrees/patient-english-complete-20261014/output/patient-english-main-alignment-20261015-r3/continuous-days.log). Keine neue Geschäftslogik und keine erneute neunfache Gesamtprüfung.

Vor/nach jedem dieser Läufe33/21/16Produkt-/Test-/GeneratedHashes sowie alle vier RED-/GREEN-Loghashes unverändert. Alle Writer-Browser/Contexts/Server via finally geschlossen; CPU-/Browserlease an Root zur unabhängigen betroffenen33er-Abnahme freigegeben. Noch keine unabhängige finale Revision3-Abnahme/FullHook/Commit/Push/aktuelleCI, kein Merge nach Main/Release. Root übernimmt die endgültige PR323-Beschreibung; kein konkurrierender PRbodywrite.


### Main-Abgleich — finale unabhängige Revision3-Abnahme

2026-10-15T07:50:00Z: Root nimmt unabhängigen finalen Code-/Test-/Generatedreview PASS (0 Findings,70/70Freeze-Dateien plus4RED/GREEN-Logs stabil) und den tatsächlich gelesenen [Browserbericht](/C:/src/kgg-worktrees/patient-english-complete-20261014/output/playwright/patient-english-main-alignment-review/r3-finish/acceptance-report.json) an. Sechs betroffene Legacy-/React-UI-Fälle sowie realer festgepinnt4bbe/v92→93-Offline-Dialog PASS,33Start-/Endprodukthashes gleich;360tatsächliche Ressourcenkörper gebunden. Root hat den aktuellen englischen Belegscreenshot selbst visuell geprüft.

Aktuelles IAB war in der tatsächlichen CUA-Inventur nicht verfügbar und der reale Öffnungsversuch schlug fehl; kein neuer IAB-PASS behauptet. Autorisierter projektinterner Playwright1.61.1-Fallback mit frischen isolierten Chromiumkontexten, keine privaten Profile. Tatsächliche Pointer-/Tastaturhandlungen für Stage/NumPad/QR/Reload/Open/Cancel/Confirm; offener Dialogsprachwechsel bleibt wegen Backdrop als bestehender DOMclick-Handlervertrag benannt. Cancel-Statebezug beginnt ab Modalöffnung, kein Rückrollen der bestehenden vorgezogenen Historyfinalisierung behauptet. Alle Auditor-/Writerkontexte und Server laut finaler Leadannahme geschlossen, Lease für normalen Hook freigegeben.

Tatsächlich erneute Cloud-Abschlussplanprüfung PASS laut Root, Thread `6acfb2a8-c608-83eb-88f2-ba42f7e3de42`, Turn `8f8c6619-8a70-4a5a-9735-9d532022653c`; keine zusätzliche Planlücke. Das ist die gebundene Cloud-Gegenprüfung der mitgeteilten lokalen Code-/Laufzeitnachweise, kein eigener Cloud-Repo-/Runtime-PASS. Main unmittelbar vor Abschluss weiterhin4bbe390.

Autorisiert jetzt: explizites Source/Test/Generated/Doc-Staging ohne Output/Traces, genau ein regulärer vollständiger Commit-Hook und normaler Mergecommit, danach normaler Branchpush in bestehenden DraftPR323. Ausschließlich dokumentiertes KGG_ALLOW_RELEASE_DRIFT=1 für No-Release96; keine Guards/Fristen umgehen. Produkt-/Testfreeze unverändert. Kein Merge nach Main, Release, Manifest oder APK. Root besitzt endgültige PRbeschreibung/aktuelle Head-CI-Abschlussprüfung.


### Main-Abgleich — Revision4 / Pending-Main-Merge-Guard

2026-10-15T08:04:39Z: erster normaler Mergecommit-Hook unverändert gestartet, SecretScan/Modulsource PASS, dann tatsächlicher FAIL im FreshMain-Hygieneguard (Zertifikat20261015T075025Z-54564, fullRegression=true,2.469s, restoredLastGreen=true). Der alte Guard verlangte Main als HEAD-Vorfahren, obwohl beim normalen noch nicht abgeschlossenen Merge HEAD weiterE und MERGE_HEAD=M bleibt. Kein Commit/Push, kein Stale-/Hookbypass. Nach Transaktionsrollback alle33Produkte/21Tests/16GeneratedEvidence und4RED/GREEN-Logs unverändert. [Historisches Fehlerzertifikat](/C:/src/kgg-worktrees/patient-english-complete-20261014/tmp/kgg-selftest/runs/20261015T075025Z-54564/report.json).

Search-first: vorhandenen Guard, native Tests/README und vorhandenes sanitized_git_environment geprüft; kein PendingMergepfad vorhanden. Vorhandene GitCLI-/Helper-/Teststruktur wiederverwendet, keine Dependency/Installation und kein übernommener Fremdcode. Offizielle Git-[True-Merge-Dokumentation](https://git-scm.com/docs/git-merge#_true_merge) und [rev-parse-Dokumentation](https://git-scm.com/docs/git-rev-parse) dienten laut Leadprüfung zur Orientierung. Unabhängiger enger Planreview PASS; tatsächliche Cloud-Präzisierung PASS Turn `7bb7e2b4-fd6c-4f8a-977a-9747d7aee968` (ersetzt allgemeinePlanreferenz f0e9acc1-0f6e-430f-b4cf-2337e0eead8c); kein Cloud-Runtime-PASS behauptet.

Revision4 nur Guard/Begleittest/1README-Satz: ursprünglicher HEAD-Vorfahrpfad und alle anderen Hygiene-/Releaseguards erhalten. Separater Pendingpfad liest ausschließlich erfolgreiches Git-rev-parse --git-path MERGE_HEAD (LinkedWorktree korrekt), akzeptiert ausschließlich exakte kanonische volle Main-Commitbytes optional1LF/CRLF, bestätigt Committyp ohne Tagpeeling, echte gemeinsame Mergebase und vollständig leeren erfolgreich gelesenen Unmergedindex. Fehlende/falsche/mehrfache/abgekürzte/Whitespace-OIDs, Refnamefallback, Nichtcommits, andererParent, Main-Descendant, unrelatedHistories, Konflikte und technische Read-/Gitfehler bleiben gesperrt. Kein neuer Flag, kein Graph-/Index-/Reftrick.

Echte frische TempGit-RED-Reproduktion auf unverändertem alten Guard: gültiger aufgelöster Mainmerge wird als stale abgewiesen. Danach11gezielte neue Tests mit echten Gitcommits/normalen Merges/LinkedWorktree und Negativsubfällen PASS (23.984s),7bestehende Release-/Hygieneschutztests PASS; native Hygiene auf tatsächlichem gebundenen E/M-Merge mit ausschließlich erlaubtem KGG_ALLOW_RELEASE_DRIFT=1 PASS. Sämtliche Tempfixture-Gitprozesse verwenden vorhandenes sanitized_git_environment; Parent-Hook-GIT_DIR/INDEX werden nicht in Fixtures geerbt. Registry/Hook unverändert. Protokolle unten separat gebunden.

Freezeprodukte33 und alle bisherigen21Tests/16GeneratedEvidence exakt gleichRevision3; keine erneute Browserabnahme nötig. Neue Guard-/Selftest-/READMEhashes bilden Revision4. Tatsächlicher unabhängiger Guard-/Testdiffreview FINAL PASS ohne Findings: Start/End73/73Dateihashes, StageLF und8/8Loghashes stabil; Root hat diese Hashes, den tatsächlichen Diff und11+7Exit0-Testausgänge selbst geprüft und Revision4 angenommen. Erneuter normaler vollständiger Hook/Commit/Push freigegeben, Ergebnis noch offen. Main vor neuem Hook einmal frisch gegen gebundenesM prüfen; bei echtem Delta melden. Keine breite Vorab-Vollbatterie, kein Merge nach Main/Release/Manifest/APK.

Zweiter normaler Hook `20261015T081128Z-42108` tatsächlich FAILED: äußerer cp1252-Logwrapper scheiterte am Pfeilzeichen und verursachte beim gepufferten Hookdruck BrokenPipe; Zertifikat bestätigt Rollback, kein Commit/Push. Separat enthält der frische vollständige Scanreport einen echten PflichtFAIL `contrast-noise-to-clean` (5000ms Feedtimeout). [Originalreport](/C:/src/kgg-worktrees/patient-english-complete-20261014/output/patient-english-main-alignment-20261015-r4/original-hook-scan-failure/scan-results.json), SHA256 `bed9add2e0f49a7b53d66d08b51f67c38373d048718cf6dfb4973d7a5eb212dc`, Markdown, tatsächlich erfasster Hooklog und Fehlerzertifikat separat unverändert gesichert. Alle73Dateien+8Logs unverändert. Unveränderter Einzelcase einmal Exit0/Frame1; dies erklärt den ursprünglichen FAIL nicht.

Anschließend genau ein vollständiger Kamera-Diagnoselauf mit gleicher60erFallfolge/Stimuli/Fristen und ausschließlich passiver Output-Telemetrie: Exit0,45PASS/15observed-limit, alle34PflichtfällePASS;60eindeutige frische Kontexte/Baselines und neuer Import im betroffenen Context59 belegt (08:40:28.145Z,2→5Übungen,12Erhaltungschecks,Trackstop1/Overlayfalse). Kein Catch/kein bereits dekodierter Feedbaseline; Race unbewiesen, Ursache offen. [Ergebnis](/C:/src/kgg-worktrees/patient-english-complete-20261014/output/patient-english-main-alignment-20261015-r4/scan-camera-telemetry-full/results.json) SHA256 `3b8cda2615d512df9272a5f8045ff647125facdc70577c2408ee7b5d81ca4892`; Telemetrie `6edec61f41e0100bb35a2ed9ee2a6de8b01cc5865cdc1373d08f04679867f31f`, vollständiger Kameralog `092be9e8d987cc06b83923a1d197dcbfb55edc0ac2b23ef37fd9489e0fd265d5`. Original-ROOT/Modulpfade erhalten, Source/Harness/Fixture unverändert;86/86StartEndbindungen stabil. Unabhängige tatsächliche Delta- und Ergebnisreviews FINAL PASS, Root selbst geprüft; tatsächlicher Cloudcheck Turn `3d3d8303-f37e-4354-a4fb-800e766e63db` bestätigt den nächsten normalen FullHook, keinen Ursachen-PASS/Cloud-Runtime behauptet.

Logtransport separat mit Unicode-stdout/stderr Exit0 und exakten42Bytes validiert (ProbeSHA256 `ee89cf2e167c24d4c09d45d9a7dd5b214be23f35567bb64a96a7d06b494161bf`): Gitstdout+stderr direkt in binäre Datei, Kind-PYTHONIOENCODING=utf-8; Wrapper ausschließlich ASCII-JSON mit tatsächlichem Gitexitcode. Ein neuer normaler Commit-Hook freigegeben, kein separater Fulltest/Retryloop; bei PflichtFAIL stoppen und Nachweise sichern.

```json
{
  "id": "main-alignment-r4-pending-merge-freeze1",
  "task_id": "patient-english-main-alignment-20261015",
  "generation": 2,
  "revision": 4,
  "englishParent": "d34e90f6ef4890e345c1559e75e2a5c22df4d27a",
  "mainParent": "4bbe3905126741c042e21331d7485067470b6640",
  "products": [
    {
      "file": "collapse-cards.js",
      "sha256": "ac8afec81349ecb3ae8d9b5dd9fd9a39c476d4dedc7148907939ebd4fae8aafc",
      "lfSha256": "ac8afec81349ecb3ae8d9b5dd9fd9a39c476d4dedc7148907939ebd4fae8aafc",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "index.html",
      "sha256": "12f4d469d042909d6e7b0b835b16616a0a6a35602fac18b6ada7fc6753c56b76",
      "lfSha256": "12f4d469d042909d6e7b0b835b16616a0a6a35602fac18b6ada7fc6753c56b76",
      "parent": "English-scanner-ref-only"
    },
    {
      "file": "kgg-update/index.html",
      "sha256": "d9e4edcda8afd4cdfc821b4e9d155483a726cec4e9c4603e4eeee4b94a0bf2d3",
      "lfSha256": "d9e4edcda8afd4cdfc821b4e9d155483a726cec4e9c4603e4eeee4b94a0bf2d3",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "kgg-update/src/document/body-shell.html",
      "sha256": "52fc54134ed60677b787d798a1caf21f86215f17f467bad532e52f2e9236cc80",
      "lfSha256": "52fc54134ed60677b787d798a1caf21f86215f17f467bad532e52f2e9236cc80",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "kgg-update/src/document/head-ui.html",
      "sha256": "c74cca199993b498cbb9d50de132c1fa5dd5a0f89b1e468165b54e7cc18fd9bb",
      "lfSha256": "c74cca199993b498cbb9d50de132c1fa5dd5a0f89b1e468165b54e7cc18fd9bb",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "kgg-update/src/metadata/changelog.html",
      "sha256": "a919cbbe18ba7d8015b561699e5a1e44cc153452c8583b9188bc5d0c26a17f27",
      "lfSha256": "a919cbbe18ba7d8015b561699e5a1e44cc153452c8583b9188bc5d0c26a17f27",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "kgg-update/src/metadata/source-truth.html",
      "sha256": "7fed7106b40c946e0f113edd221dc76c17f532ab5dc93a4b19a25624718b3a2d",
      "lfSha256": "7fed7106b40c946e0f113edd221dc76c17f532ab5dc93a4b19a25624718b3a2d",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "kgg-update/src/patches/v082-therapy-cockpit.html",
      "sha256": "94564723f8d292cf9cf23a88da3076c7cf6393e47880a6c50b06bdc7836ac673",
      "lfSha256": "94564723f8d292cf9cf23a88da3076c7cf6393e47880a6c50b06bdc7836ac673",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "kgg-update/src/patches/v085-ticket-015-progressions.html",
      "sha256": "43ed681276dac3f5394d3e05880fca683c1d3cc6dd44f00c5c50a4f9be599975",
      "lfSha256": "43ed681276dac3f5394d3e05880fca683c1d3cc6dd44f00c5c50a4f9be599975",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "kgg-update/src/patches/v090-ticket-015-admin-stage-gallery-drag-motion.html",
      "sha256": "bbae05b6d45927c7f14b19dcfe8b193cd0fcf1414b27adced0105e43e06ad1e6",
      "lfSha256": "bbae05b6d45927c7f14b19dcfe8b193cd0fcf1414b27adced0105e43e06ad1e6",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "kgg-update/src/patches/v093-cockpit-shared-editor.html",
      "sha256": "76da5d4c09e1b941127b0cb1b0ea7873c4ae7436708ed3c5779b8e362f2de42b",
      "lfSha256": "76da5d4c09e1b941127b0cb1b0ea7873c4ae7436708ed3c5779b8e362f2de42b",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "kgg-update/src/runtime/app-core.html",
      "sha256": "80548924281b10af79c1d2645a60956b42728a905ac934e5c0b8e3d09447149f",
      "lfSha256": "80548924281b10af79c1d2645a60956b42728a905ac934e5c0b8e3d09447149f",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "kgg-update/version.json",
      "sha256": "44407021580e051dd1719882c921a0aa477ccf59660f7966bec8171a36ad237f",
      "lfSha256": "44407021580e051dd1719882c921a0aa477ccf59660f7966bec8171a36ad237f",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-card-settings.js",
      "sha256": "06c04bcb84d6eec3bad892f48c1434f6aab7060e0601bfe2a01eb417405ee045",
      "lfSha256": "06c04bcb84d6eec3bad892f48c1434f6aab7060e0601bfe2a01eb417405ee045",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-day-history.js",
      "sha256": "2e904b1b6578aef5a7fccc5128bc633c5367c966b4eb5dd484e79a98bdf7661e",
      "lfSha256": "c8664dff338e682fbf2df380d05aeee8daeecce5b7afa1beb812fe8d5d5414c0",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-i18n.js",
      "sha256": "efc1a0b7fbc9bce500951b36d35a21d9b615d4294efa7a5f91faf1e06cbaf898",
      "lfSha256": "efc1a0b7fbc9bce500951b36d35a21d9b615d4294efa7a5f91faf1e06cbaf898",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-install-guide.js",
      "sha256": "11d2fb9edd3f290a4f75bd7a1526daee53faa55bccbe041129f3f04fdf729e86",
      "lfSha256": "0ff8e9e3c7802f2891873762e66770d3c8e38230011cacee0eed4e6a390e8643",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-last-value-hints.js",
      "sha256": "879131abf73d0e66234abe33670c43e9eb963a1371527262db617ee1a817d685",
      "lfSha256": "879131abf73d0e66234abe33670c43e9eb963a1371527262db617ee1a817d685",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-media-retry-cache_v2.js",
      "sha256": "1ae19634aa7973dbe1546333b7d2e6d0138e04e175290ce2e11310092a4651ca",
      "lfSha256": "1ae19634aa7973dbe1546333b7d2e6d0138e04e175290ce2e11310092a4651ca",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-multiplan-db.js",
      "sha256": "40946ffbc7200254f9f813dc0a6048437171256e7f2f2de9470c78d4338528eb",
      "lfSha256": "40946ffbc7200254f9f813dc0a6048437171256e7f2f2de9470c78d4338528eb",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-plan-delete.js",
      "sha256": "2b37629bfbabb202e04c04cec8f6a883c173343411a4c57814771b9fb5b43ad7",
      "lfSha256": "273f3c1a9e8d76161e924e4c03d55afd1e0266502215531daf09c2ed01903073",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-plan-link-choice.js",
      "sha256": "19e7edb65e02717b8e36f0062e6422b0bffb3b4e9987e4b31638fb7cea2d0917",
      "lfSha256": "786a6663c4eb5ab5fcd8681a940401aa92b4450f1f2f11c0b5f00b9310adee16",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-qr-fullscreen.js",
      "sha256": "a9245be9a5bbc7d1582b42a587b7de72d4261b9f6946dd196edb74992b3e23dc",
      "lfSha256": "0485f687e98c3e03a45414f0459ac1b8958dfab9ad795fd07f76409e07160c07",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-react-dist/kgg-patient-ui.js",
      "sha256": "57d37fa3dacfddcd1050b7507436ba5f3499d8eaa678cedcce87f8054161c9f8",
      "lfSha256": "57d37fa3dacfddcd1050b7507436ba5f3499d8eaa678cedcce87f8054161c9f8",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-set-compact-view.js",
      "sha256": "b9a7218388913774d7d151cced14a29522ebcc6f95dd8bad50b96f2d50a4e533",
      "lfSha256": "b9a7218388913774d7d151cced14a29522ebcc6f95dd8bad50b96f2d50a4e533",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-set-summary-groups.js",
      "sha256": "505c5aab315c2d4d955c75c17f6514be04b88f24d81289376008e6f2a066974c",
      "lfSha256": "505c5aab315c2d4d955c75c17f6514be04b88f24d81289376008e6f2a066974c",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-ui-micro-polish.js",
      "sha256": "5bce46af62a0b793da0a850121429c704ac8294150aea0c1fcd148e3eda767a2",
      "lfSha256": "5bce46af62a0b793da0a850121429c704ac8294150aea0c1fcd148e3eda767a2",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-ui/src/legacy-numpad/LegacyNumpadHeader.tsx",
      "sha256": "16c2b4870d35d165dd7ec2f6d8fe74ca6e8dbd087a37afd4b99fb62b49bfae78",
      "lfSha256": "16c2b4870d35d165dd7ec2f6d8fe74ca6e8dbd087a37afd4b99fb62b49bfae78",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-version-label.js",
      "sha256": "8aacac7fc3e25380200e5bef46d7055b421cfe6189a8af8116bc759b540187b3",
      "lfSha256": "8aacac7fc3e25380200e5bef46d7055b421cfe6189a8af8116bc759b540187b3",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "service-worker.js",
      "sha256": "025613ed790cb2796f64c41fc9720c1b5a5d8495968503a725e49f88a3c3e6cc",
      "lfSha256": "025613ed790cb2796f64c41fc9720c1b5a5d8495968503a725e49f88a3c3e6cc",
      "parent": "English-scanner-ref-only"
    },
    {
      "file": "update-recovery.html",
      "sha256": "6f57568a48f65daaf63492d4c7098a76171dbe55bb8ca9b51a2fde6e3fcb11e3",
      "lfSha256": "6f57568a48f65daaf63492d4c7098a76171dbe55bb8ca9b51a2fde6e3fcb11e3",
      "parent": "English-raw-unchanged"
    },
    {
      "file": "patient-start-scan.js",
      "sha256": "f458b586572fc381195057be9ba56e86b0a29b70809bb1177a892abb6deb00ec",
      "lfSha256": "f458b586572fc381195057be9ba56e86b0a29b70809bb1177a892abb6deb00ec",
      "parent": "Main-exact"
    },
    {
      "file": "patient-card-progress.js",
      "sha256": "5151406061f51bd6cd90e979874237e90f87e1972a9d31ee3fac698ad769cf8f",
      "lfSha256": "cc6179f83d1a7327f90adc5d12e4cedb47b26edfd6c1d07cf069dc5d48fee557",
      "parent": "English-additional-finish-copy-only"
    }
  ],
  "tests": [
    {
      "file": "release-pipeline/kgg_english_progression_baseline_playwright.js",
      "sha256": "e865fdc5e8ed2b3d9388f18c1e1394097f665344c8ccacded228cd155d4c05f3"
    },
    {
      "file": "release-pipeline/kgg_english_metadata_smoke.js",
      "sha256": "a6490412d1d2a835158a32176d80132a7a398d61ee8d5c507cf4a4fbcc7cdeb2"
    },
    {
      "file": "release-pipeline/kgg_english_editor_playwright.js",
      "sha256": "515933e9f591fb7ca624256b169cbe07752c6bcd851ef56082e21074f0775fd6"
    },
    {
      "file": "release-pipeline/kgg_english_cockpit_smoke.js",
      "sha256": "1f99bd139bf1bf6dc1c4f064f5d8160ce4b213c80ade02b0371cfe9e96cc0595"
    },
    {
      "file": "release-pipeline/kgg_english_cockpit_playwright.js",
      "sha256": "4fe7eda0ab021996600fb0e45085a4019290cfdfef80bf4ffbdd242403e00f67"
    },
    {
      "file": "release-pipeline/kgg_dual_device_package.js",
      "sha256": "0b5c79fa0b7324cecf2768b397b6e1a4d88e27eecdfbbcce053e39578a7e4047"
    },
    {
      "file": "release-pipeline/kgg_patient_english_title_playwright.js",
      "sha256": "dd0d3291b55102bdabba84e7db02d5fcf824d60c0d319e1b9dc62c82319c92ee"
    },
    {
      "file": "release-pipeline/kgg_patient_english_summary_smoke.js",
      "sha256": "6549062a8af1064189af604b07a55c7ac82039a4d357bd8ae835574c484c8994"
    },
    {
      "file": "release-pipeline/kgg_patient_english_summary_playwright.js",
      "sha256": "9a3a1042f93e050cbd515e6b464675d5fc6355bfccb8d69d47cd6ed602805b99"
    },
    {
      "file": "release-pipeline/kgg_patient_english_review_playwright.js",
      "sha256": "40e04374b14d3ec0c2221be54069f499406fa114aa9f76d5e3ecbd52983d5c9c"
    },
    {
      "file": "release-pipeline/kgg_patient_english_playwright.js",
      "sha256": "28b9d3b0153570b040491ca2241660b30a0cddb708b97dbdd4825c054cecd0af"
    },
    {
      "file": "release-pipeline/kgg_patient_english_compatibility_playwright.js",
      "sha256": "eae06368c3521f91cff58b01fe80cc4272213ff539a5df0dc4a82b463317cecb"
    },
    {
      "file": "release-pipeline/kgg_patient_import_session_values_playwright.js",
      "sha256": "e426348734f1e01571321dd49459606de26af747f6c60c30c6731eff1d091aed"
    },
    {
      "file": "release-pipeline/kgg_patient_gpt_write_gate.py",
      "sha256": "db621e231bfea72dd2addaca3b3db942b3a26e084f6aefef2a44eda81c349cd1"
    },
    {
      "file": "release-pipeline/kgg_patient_preview_first_load_smoke.js",
      "sha256": "37db546492635a4f27d51320d9cc46e6dfa72c00b264c07a670a61a61c9ad6a4"
    },
    {
      "file": "release-pipeline/kgg_patient_qr_v81_device_ladder.js",
      "sha256": "52b9b9c6eac8bb11e4529b507a6c4a94e46bbb5f8acdc28d177a2e27af1883e9"
    },
    {
      "file": "release-pipeline/kgg_patient_preview_storage_isolation_smoke.js",
      "sha256": "a0485ad60ca432c254ffd78a8155d9aea22f87a1781fc60f22c908fe26bbf40b"
    },
    {
      "file": "release-pipeline/kgg_pwa_contract_smoke.py",
      "sha256": "ad7a8448bd6cf2a305bb4cbf75def1022ed75470d5897304a9ebc2a2f5046b27"
    },
    {
      "file": "release-pipeline/kgg_test_battery.py",
      "sha256": "7dff67422c62e77f3dd5f88b64ce632d8759b796bd0e37f6b09346f0651446ac"
    },
    {
      "file": "release-pipeline/kgg_patient_card_progress_smoke.js",
      "sha256": "aaf4a40d881884aec5bee71cab688a020763bdc2c60ee6d125f1af906f1b94b9"
    },
    {
      "file": "release-pipeline/kgg_patient_continuous_days_playwright.js",
      "sha256": "f4897ee618712948aaefe83cdc78f694282fea535100a3f09175a618783cd699"
    },
    {
      "file": "release-pipeline/test_kgg_selftest_build.py",
      "sha256": "966485778ba940756fb6390c86cdc6549834e393df4b2c71d8fb2e68e4e932d3"
    }
  ],
  "previousFreezeManifestSha256": "88c3eb46935f99f157d4e727358b2cff165fa9c2cb22171a088f691265adbb92",
  "previousPwaContractSha256": "74d973ebae4dcb4e8be42fdaa0bbcfe90dead17e7dd57ae00dbf93d9b15b5e94",
  "generatedEvidence": [
    {
      "file": "docs/kgg-custom-gpt-editor-snapshot.json",
      "sha256": "a8d5191975add6c81713c3b803205130c3e08342f6a6e9f552498709323f87f2"
    },
    {
      "file": "docs/kgg-custom-gpt-knowledge-pack.md",
      "sha256": "a23f0929f9a8711e527f4359a84cdc0723879f91e66c049195f86eec8890efa5"
    },
    {
      "file": "docs/kgg-custom-gpt-knowledge-safety.md",
      "sha256": "9c7b48617c50be2581ed6223011a45c0e5f75c4d3d766452a4b05f87d5d8c9ee"
    },
    {
      "file": "docs/kgg-custom-gpt-resource-manifest.json",
      "sha256": "cedcc131e5d66b62ec05eadb84552fbc6f588fb24e57435e7aee5a0e4225e0ad"
    },
    {
      "file": "docs/kgg-gpt-bug-index.json",
      "sha256": "d3c7001351d03a722ad50a8f6e79ee0f0d0d533f1eeb96da6735b55ffa2310c1"
    },
    {
      "file": "docs/kgg-gpt-bug-lessons.md",
      "sha256": "6155e1b3501ffba0aef79a1fb05eb85ba15f573198a6d5c6202a0c7006098e33"
    },
    {
      "file": "docs/kgg-patient-custom-gpt-editor-snapshot.json",
      "sha256": "d31c86bdb68c26a9878eb1efa5cb05a953f7ef8b94b8eacd697dfb5b2feb05dc"
    },
    {
      "file": "docs/kgg-patient-custom-gpt-knowledge-safety.md",
      "sha256": "1622b825d6b3c0a24c6c322f51b18c43d1a8c3a293f44d7740deeb9f05790277"
    },
    {
      "file": "docs/kgg-patient-custom-gpt-knowledge-testing.md",
      "sha256": "04e1c2f5e1644777cd37cd1a91155e3c4830af91d6882f535920f81845c9b35e"
    },
    {
      "file": "docs/kgg-patient-gpt-source-index.json",
      "sha256": "dcc0e22582bfe8247216e2383bb8d91c51b5eaa087fb37f035a317a4fc4ba802"
    },
    {
      "file": "docs/kgg-patient-gpt-source/chunk-001.md",
      "sha256": "e561bab5a9dd148ef2cec684f2e2e837a9443c0bae956642eb121ed4652addc8"
    },
    {
      "file": "docs/kgg-patient-gpt-source/chunk-002.md",
      "sha256": "0d7ca5e77f92d1c883195aa7d1bc75ea7c426ed318131d339b63640e94850c51"
    },
    {
      "file": "docs/kgg-patient-gpt-source/chunk-003.md",
      "sha256": "e8a04e0c222effc3df0d62b121d3d3d40139c234da522bc09c09c78dcc83b210"
    },
    {
      "file": "docs/kgg-patient-gpt-source/chunk-009.md",
      "sha256": "e1f7dcae94cb45d1679807fac69a8b96d11d6eab930a237274e945a5839645ed"
    },
    {
      "file": "docs/kgg-patient-gpt-source/chunk-034.md",
      "sha256": "14abffef2ee4dbc74ab67e5f4076fd796a80d34f5361ca93ba95726601753150"
    },
    {
      "file": "docs/kgg-patient-gpt-source/chunk-035.md",
      "sha256": "52a169096884ccdab28cd7f57932351895e233db901880995291b83b982018e8"
    }
  ],
  "redProducerSha256": "b5b3737577c21d482365e19cf41b4ddea9270ba22c30230ad5f2833e12fa5da9",
  "redGreenEvidence": [
    {
      "file": "output/patient-english-main-alignment-20261015-r3/card-progress-red.log",
      "sha256": "d14753cbecd7a8bbd81541630b9855253a03684687c765cac4265a629a459fb6"
    },
    {
      "file": "output/patient-english-main-alignment-20261015-r3/finish-title-red.log",
      "sha256": "7b70208af402ca9d9c1e2555549640e954e40a1dead4d160708efa07d1c665ce"
    },
    {
      "file": "output/patient-english-main-alignment-20261015-r3/card-progress-green.log",
      "sha256": "c4f237559f22e0aef60010218df101c354f3c9a05286f80fd7ff720f7be6baab"
    },
    {
      "file": "output/patient-english-main-alignment-20261015-r3/finish-title-green.log",
      "sha256": "d9b1447f77a36c65896bc334e8f0e4ee467da4dc8b0f12089a262f22f06c429d"
    }
  ],
  "toolingEvidence": [
    {
      "file": "release-pipeline/kgg_patch_hygiene.py",
      "sha256": "13527c6ca2aeac3b18dd94b85030275d16512ecb50125789877e62912e87438c"
    },
    {
      "file": "release-pipeline/README.md",
      "sha256": "66762aaacee11d5983d622b4a9dfcd5d3efe67c0f383a2d94f380d1743dcb80a"
    }
  ],
  "guardEvidence": [
    {
      "file": "output/patient-english-main-alignment-20261015-r4/pending-merge-red.log",
      "sha256": "5192c4cb7036f6a622f54b6ef037176b033bbd72b4a6f297ce2e061e80e0dacc"
    },
    {
      "file": "output/patient-english-main-alignment-20261015-r4/pending-merge-green.log",
      "sha256": "957a1aea1996dbe5cba04b71b9711c06735cb33103c1ae99ece20f4bd1baccf6"
    },
    {
      "file": "output/patient-english-main-alignment-20261015-r4/existing-release-guards.log",
      "sha256": "f97a41b8582424b43e54d58d595a3d61d7b8bd13206a6ccca0e69f2315da6a1a"
    },
    {
      "file": "output/patient-english-main-alignment-20261015-r4/actual-pending-hygiene.log",
      "sha256": "cc61333e21319494f981de6b335139196abfc7923be92b5daeaf70d9809fca13"
    }
  ],
  "firstMergeHookFailure": {
    "runId": "20261015T075025Z-54564",
    "status": "failed",
    "fullRegression": true,
    "restoredLastGreen": true,
    "report": "tmp/kgg-selftest/runs/20261015T075025Z-54564/report.json"
  },
  "manifestSha256": "fbc72f17518d44e53ee711ef15c6e3c7c8b2523fa92515d2aa3205e4243c951f"
}
```
