# KGG Patienten-App – Legacy/React-Gesamtvergleich (Fortsetzung)

Stand: 2026-10-13 · Workstream `test/patient-complete-react-acceptance-20261013`.
Basis: frisches `main@f59bc55e6e22e1b04061557c710069f6cf8f0b21`.
Ziel: die **gesamte Patienten-App** mit reproduzierbaren Alt/Neu-Abläufen schrittweise
abzusichern und am Ende nur eine echte Geräte-Gesamtabnahme zu verlangen.

## Bereits erledigt – NICHT erneut bauen

- [PR #303](https://github.com/Kayus24/kgg/pull/303) ist gemergt:
  synthetische, unabhängige Legacy-/React-NumPad- und Transfer-Tests auf
  Phone/Tablet, Chromium/WebKit, mit 12 Checkpoints und Videos/Screenshots.
- Satzschmerz-E2E ist bereits separat in beiden Browser-Engines eingebunden.
- [PR #307](https://github.com/Kayus24/kgg/pull/307) zeigt, wie die
  API-freie Gemini-Web-Videoanalyse mit dem Fahrklar-MCP real funktioniert.
  Kein zweiter Upload-Mechanismus nötig. Die gemeldeten grauen Frames werden
  separat unter [Issue #308](https://github.com/Kayus24/kgg/issues/308)
  behandelt; beide Videovarianten sind betroffen, nicht nur React.
- [PR #305](https://github.com/Kayus24/kgg/pull/305) bereitet teilweise
  denselben Gemini-Webweg vor; vor dem Merge mit #307 abgleichen, damit
  nicht zwei Anbieter-/Validator-/Browserprofile konkurrierend gepflegt werden.

## Neuer Testumfang dieses Workstreams

1. Vorhandenen `kgg_patient_unit_semantics_playwright.js` minimal erweitert:
   Legacy/React in Chromium und WebKit, echter React-Mount erforderlich.
   Synthetische dynamische Units (keine/Sek., bar/Wdh, Watt/Sek.),
   inaktive Felder, Startwerte, Kartenfortschritt, Summary, Reload und History.
2. Vorhandenen `kgg_patient_continuous_days_playwright.js` erweitert:
   Tag 7→8, 12→13, Tag 100 und Pagination, Tagespersistenz,
   unabhängige Tage mehrerer Pläne, feste Plangrenze und finalen QR.
   Ebenfalls Legacy/React und Chromium/WebKit mit überprüftem React-Mount.
3. Der bereits bestehende Satzschmerz-E2E-Test liefert nach erfolgreicher
   Legacy-/React-Ausführung SHA-gebundene `pain-legacy.json`/`pain-react.json`.
   Ein auftauchender Updatehinweis wird regulär über `Später` geschlossen,
   statt Klicks zu erzwingen. Die React-Komponente wird real geprüft.
4. `kgg_patient_full_acceptance_report.mjs` aggregiert **vier Testblöcke**
   aus **synthetischen Daten mit exakter Kandidaten-SHA**, Einzel-Assertions,
   getrennten Bildbelegen und offenem Geräte-/Feature-Teststatus.
   Fehlende/alte/falsch formatierte Evidenz führt NICHT zu PASS.
5. Der bestehende Parity-Workflow bekommt diese Tests ohne zusätzliche
   Browser-Infrastruktur; Artefakt `acceptance.html` ergänzt `report.html`.

## Funktionsinventar und ehrliche Coverage-Aussage

Das aktuelle Drive-Dokument *KGG Patienten-App – Feature & Regression
Manifest* bleibt die fachliche Quelle. Stand-Snapshot im Repo:
`docs/quality/patient-react-feature-inventory-20261013.json`.
114 Manifestzeilen umfassen 111 unterschiedliche PAT-Funktions-IDs.
Mit dem ergänzten Zwischenstands-QR-/Vollbild-Test sind 32 Funktions-IDs
mindestens einem bisherigen oder neuen Alt/Neu-Testbaustein zugeordnet.
Für 79 fehlt im betrachteten Vergleich noch eine solche Zuordnung.
Dies gilt als Mapping-Fortschritt, erst nach bestandener CI als Testnachweis.
**Zuordnung ist kein PASS** und **fehlende Zuordnung kein Beweis, dass eine
Funktion generell ungetestet ist**. Weitere bestehende Tests sind in der
KGG-Testbatterie vorhanden; nicht pauschal duplizieren.

## Noch offen, priorisiert nach Patientenrisiko und Testnutzen

**Nächste automatisierte Parity-Slices, bestehende Tests zuerst sichten:**
1. Zwischenstands-QR (final=false, ohne Tagesabschluss), Vollbild und
   Schließen sind im bestehenden Trainingstag-E2E ergänzt (CI-Prüfung offen).
   Noch offen: tatsächlicher System-Clipboard-Kopiernachweis, QR-Planimport,
   Plan ersetzen/löschen, Speicherisolierung und Kamerafallback (synthetisch).
2. DB/Übungssuche, Hinzufügen, Übungseinstellungen, Progressionsvarianten,
   Medien/Lightbox und Karten-Ein-/Ausklappen bei 1/2/3/4+ Sätzen.
3. PWA-/Offline-/Update-Recovery, First Load, Installationshilfe,
   Android-/iOS-Sonderfälle, Defekt-Payload und i18n.
4. Visuelle Tablet-/Large-UI-Parität; gemeinsamer Grauframe-Fund #308 mit
   unabhängiger Recorder-/Compositorprüfung. Bestehenden Oppo-Fix schützen.

**Gesamtabnahme-Gate:** jeder fachlich verpflichtende PAT-Flow besitzt
(a) eine bestehende oder erweiterte Testquelle, (b) einen konkret
nachgewiesenen Teststatus auf dem richtigen Kandidaten, (c) keine
unaufgeklärten hohen Befunde. Keine versteckten Mocks/Phantom-PASS.
Zum Schluss eine reale End-to-End-Abnahme auf Oppo und iPhone/Safari,
mit nur noch gebündelter Rückmeldung des Nutzers. Android-/iOS-Hardware
kann nicht durch Desktop-Chromium/WebKit allein freigegeben werden.

## Arbeits- und Sicherheitsregeln

Isolierter Worktree, kein direktes main. Kein Patientendatensatz,
keine Gemini-API, kein automatischer Merge/Release. Laufzeit langer Tests
in kurzen PID-/Run-Abschnitten, keine blinden Wiederholungen.
Vor jeder Übernahme aktuelle GitHub-/Drive-Stände, CI und andere
aktive Workstreams prüfen. Dieses Dokument ist ein Snapshot, kein Lock.

## Lokaler Prüf-Checkpoint vor GitHub-CI

Kandidatenbasis: `f59bc55e6e22e1b04061557c710069f6cf8f0b21`.
Chromium und WebKit jeweils mit derselben synthetischen NumPad-,
Einheiten-/Verlaufs-, Trainingstag-/QR- und Satzschmerz-Strecke.
**Vier fachliche Blöcke pro Engine PASS**, jeweils Legacy und React
mit aktivem React-Mount-Nachweis. Parity-Recorder: 392 Einträge,
davon 352 harte PASS und 40 reine Beobachtungen; 0 Abweichungen.
20/20 lokale Vertrags-/Negativtests PASS.

Lokale Belege liegen engine-getrennt in den ignorierten
`.tmp/acceptance-chromium/patient-ui-parity` und
`.tmp/acceptance-webkit/patient-ui-parity`. Das GitHub-Artefakt entsteht
nach Push auf **dem neuen PR-Head**; die alten f59bc55-Testbelege dürfen
keinen Erfolg auf einen neueren Commit vortäuschen.
WebKit-Satzschmerz zeigte im ersten Lauf einen echten Updatehinweis;
der Browser-Test nutzt nun den sichtbaren `Später`-Button ohne
`force-click`; die überarbeitete Variante war erfolgreich.

### Full-Critical-Lauf (lokale Umweltgrenze)

Der vorgeschriebene lokale Lauf wurde tatsächlich gestartet. Module-Source-
Check und Patch-Hygiene waren PASS. Danach blieb die Release-Contract-
Unit-Testgruppe ohne weiteren Logfortschritt stehen (wie zuvor bei einem
anderen KGG-Workstream). Nur der eigene Testprozess wurde kontrolliert
gestoppt. Ergebnis des **gesamten** lokalen Critical-Gates:
`INCOMPLETE`, ausdrücklich **kein PASS**. Recovery-Notiz und Teil-Log
stehen ausschließlich im ignorierten `.tmp`-Ordner. GitHub Required Gate
des neuen Pull Requests bleibt ein separat nachzuweisendes Pflichtgate.

## Weiterer enger Test-Slice: Zwischenstands-QR (14.10.2026)

Auf dem getrennten Folgebranch des Draft-PR #309 wird der vorhandene
Trainingstag-Browser-Test erweitert; keine Produktänderung und kein neues
Testframework. Vor dem finalen T7-Abschluss wird ein **nicht-finaler QR**
mit KGGD1-Payload erzeugt und verifiziert: richtiges Datum, final=false,
kein veränderter Tages-/Done-/Wertezustand; QR-Bild öffnen, Vollbild
schließen, Kopier-Button auslösen, QR-Payload muss erhalten bleiben,
danach erst regulär Training beenden. Legacy/React und Chromium/WebKit
laufen in den bestehenden CI-Jobs. Ob die OS-Clipboard-Operation
wirklich erfolgreich war, wird NICHT behauptet – dies ist weiter offen.

Solange diese neuen CI-Jobs nicht auf dem neuen Head bestanden sind,
gilt dieser zusätzliche Scope als *Implementierung im Testbranch*,
nicht als abgenommene Funktion. Der bereits grüne PR #309 bleibt
unangetastet. Der Gesamtabnahme-Blocker ist weiterhin die vollständige
Testabdeckung und spätere reale Oppo-/iOS-Prüfung.
