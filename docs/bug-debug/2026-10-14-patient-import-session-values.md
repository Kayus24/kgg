# Planimport und Werte der letzten Trainingseinheit

Auftrag: Bei Aktualisieren/Ergänzen und Plan ersetzen prüfen, ob die letzte
Trainingseinheit automatisch als neue Trainingseingabe übernommen wird.

Basis: `origin/main` `f59bc55e6e22e1b04061557c710069f6cf8f0b21`, Patienten-App v90.
Branch: `fix/patient-import-session-values-20261014`, Kandidat v92.
Verantwortlicher Schreibbereich: Patienten-Scanner, notwendige Versionsverweise,
zugehörige Regression und generierte Patienten-GPT-Quellnachweise.
Offener PR #306 überschneidet sich mit den Versionsmarkern in `index.html` und
`service-worker.js`; bei Integration Versionsverweise abgleichen.

## Search-first und Ursache

Vorhandene Plan-Slot-, Plan-Link-, Scanner- und Einheiten-Tests sowie die aktive
Quelle geprüft. Die bestehende `transferPreview`-Logik sammelte pro passender
Übung/Satz/Seite/Einheit die letzten gespeicherten Werte und schrieb sie beim
Ersetzen als Tag-1-Werte in den neuen Plan. Wiederverwendet werden die vorhandenen
Importwege und die bereits im Projekt gepinnten Playwright-Abhängigkeiten; keine
neue Bibliothek oder Produktabhängigkeit erforderlich.

## Reproduktion im Codex-In-App-Browser

Nur synthetische Pläne und lokal eingegebene Werte verwendet.

1. Beinpresse, ein Satz, 52 kg und 12 Wdh eintragen; Training T1 abschließen.
2. Anderen Planlink mit derselben Übung öffnen und „Aktiven Plan ersetzen“ wählen.
3. v90: 52 und 12 stehen als tatsächliche Eingabewerte im Ersatzplan, die Karte
   wird „Bearbeitet“. DOM-Prüfung bestätigt `input.value`, nicht nur Placeholder.
4. Aktualisieren/Ergänzen in offener T2 über den QR-Text-Fallback testen: Werte
   bleiben leer, 52/12 erscheinen nur als Hinweise; neu ergänztes Rudern bleibt
   leer. Die lokale Testfixture simuliert ausschließlich eine nicht verfügbare
   Kamera und einen festen synthetischen Prompttext. Kein Nachweis echter Kamera.
5. v92 nach Aktivieren des lokalen Updates: denselben Ersatzfall wiederholen.
   Status „Keine bisherigen Trainingswerte übernommen“, Tag 1 offen, leere
   Eingaben und Karte „Offen“. Screenshot lokal unter
   `tmp/patient-import-session-values/iab-v92-fixed.png`.

## Patch und Nachweis

Automatische Übernahme der letzten Session beim Ersetzen entfernt. Bestehende
Sessions bleiben unter ihren bisherigen Speicherkeys erhalten. Aktualisieren
behält bereits erfasste Werte und Historie; es erstellt keine neuen Werte aus
Vorwert-Hinweisen. Explizite Therapie-Startwerte im importierten Plan behalten
ihre bisherige Tag-1-Semantik.

Der neue Browser-Regressionstest prüft Aktualisieren, zusätzlichen Plan,
Ersetzen über Scanner-Fallback und Ersetzen über Planlink, einschließlich
Neuladen, leerer aktueller Zusammenfassung und unveränderter alter Speicherung.
Vor dem Patch scheitert er beim Ersetzen mit den tatsächlichen Werten
52/12 und 47/10; nach dem Patch bestehen alle vier Fälle.

Weitere geprüfte Bereiche: Plan-Slot/Plan-Link-Smokes, aktive und inaktive
Einheiten/Therapie-Startwerte samt Reload/Historie, KGGH2/KGGH3-Import,
verlustfreier Medien-Update-Pfad, PWA-Vertrag, GPT-Ressourcenfrische und Evals.
Die UI-Stability-Regressionsbatterie besteht vollständig.

Der erste Critical-Lauf scheiterte nach 141 erfolgreichen Unit-Tests (ein Skip)
am alten Scanner-Scripttag im Test-Paketgenerator (`Scanner-Einfügepunkt fehlt`).
Die beiden bestehenden Scanner-Versionsverweise der Prüfwerkzeuge wurden
angepasst; der betroffene 14-Test-Vertrag besteht danach.
Der abschließende vollständige Lauf `run-kgg-tests.cmd --level critical`
besteht vollständig (`KGG test battery OK`). Auch
`run-kgg-tests.cmd --suite ui-stability --level regression` besteht vollständig.

## Früherer Zwischenstand: Commit-Hook blockiert

Der unveränderte `.githooks/pre-commit` startet wegen der Registrierung des neuen
Tests in `kgg_test_battery.py` eine vollständige Regressionszertifizierung.
Diese scheitert an `patient-qr-v81-device-ladder-regression`: `medium-20` und
`weak-7`, jeweils `recognition`. Report:
`tmp/kgg-selftest/runs/20261014T163213Z-46804/report.md`.
Der vollständige Scanner-Test davor meldet 45 `pass`, 15 erwartete
`observed-limit`, keinen `fail`.

Gegenprüfung: Die beiden unveränderten Profildefinitionen mit ihren unveränderten
Fristen wurden separat gegen `C:/src/kgg` ausgeführt. `index.html` und
`patient-start-scan.js` dort sind nach Zeilenendennormalisierung bytegleich mit
`origin/main` f59bc55. Beide Profile scheitern auch ohne den Patch an
`recognition`. Die eigene temporäre Vergleichsfixture verwendet den originalen
Ladder-Code, nur absolute Root-/Output-Pfade und Auswahl dieser zwei Fälle.
Resultat: `tmp/patient-import-session-values/baseline-ladder/results.json`.

Der Hook wurde nicht verändert oder umgangen. Kein Commit/PR entstand.
Der getestete Kandidat und ein vollständiger staged Patch bleiben zur Prüfung
liegen. Dies ist keine erfolgreiche vollständige Regressionszertifizierung und
keine Live-Freigabe. Die bereits separat ausgeführten Critical- und
UI-Stability-Batterien bestehen vollständig.

## Früherer Zwischenstand: erneute Prüfung vor Push (14.10.2026)

Auf Max' erneuten Prüf-/Pushauftrag den unveränderten staged Kandidaten frisch
geprüft. `origin/main` bleibt f59bc55. Unabhängiges read-only Code Review:
keine blockierenden Findings. Die Prüfung bestätigt getrennte Plan-Speicherkeys,
`safeSave()` vor dem Wechsel, unveränderten Abbruch-/Update-/Add-Pfad und keine
Decoder-, Layout- oder zusätzliche Löschänderung. Grenzen des neuen Tests:
keine Therapie-Startwerte in seiner Fixture, kein direkter Vergleich alter
Done-/Meta-Keys; dafür bleiben die bestehenden separaten Nachweise relevant.

Frischer Importtest: update/add/replace/replace-link einschließlich Reload,
leerer Eingaben/Zusammenfassung und erhaltener alter Speicherung PASS.
Patienten-GPT-Quellressourcen `--check` PASS; Resource-Audit TARGET_PASS;
`git diff --cached --check` PASS.

Unveränderte vollständige QR-Ladder erneut ausgeführt: FAIL bei `medium-20`,
`old-7`, `weak-7`, jeweils `recognition`. Log:
`tmp/patient-import-session-values/ladder-recheck.log`.
Der bereits dokumentierte Baselinevergleich belegt `medium-20` und `weak-7`
auch ohne den Patch; `old-7` wurde dort nicht separat gegengeprüft.
Kein weiterer Commitversuch auf Basis eines bekannten roten Gate-Ergebnisses,
kein Hook-Bypass, kein Push und kein PR. Der angefragte Push bleibt blockiert.

## Ursache der QR-Testblockade geklärt

Die unveränderten Geräteprofile öffneten den gedrosselten Scanner mit einem
bereits gestarteten grauen Canvas-Stream. Erst nach den UI-Wartebedingungen
wurde das QR-Bild eingespeist. Dadurch prüfte jsQR zunächst graue/cached Frames,
während die Gerätefrist bereits lief. Instrumentiert beobachtet: mehrere leere
Decoderaufrufe; unter CPU-Drosselung kann ein späterer Aufruf zusätzlich stark
verzögern. Ein bloßes Zeichnen vor Scanneröffnung, aber nach captureStream,
beseitigte den gecachten ersten grauen Frame nicht zuverlässig.

Korrektur ausschließlich im Testharness: initiales QR-PNG laden und in den
Canvas zeichnen, bevor captureStream startet. Die UI-Wartebedingung akzeptiert
auch eine bereits abgeschlossene echte Erkennung mit geschlossenem Overlay.
Eine zusätzliche Assertion verlangt den exakten QR-Inhalt beim ersten echten
jsQR-Aufruf. Fristen, CPU-Faktoren, Auflösungen, Decoder und App-Quellen wurden
für diese Korrektur nicht geändert. Leere Kamera, Abbruch und verweigerte
Berechtigung bleiben im getrennten Extrem-/Lifecycle-Fall unverändert geprüft.

Unabhängiges read-only Review: keine blockierenden Findings, Gate nicht
abgeschwächt. Vollständige Ladder mit Kandidat v92 und separat mit unverändertem
Ausgangscode: alle zehn Format-/Geräteprofile PASS, einschließlich medium-20,
old-7 und weak-7. Foto- und Lifecycle-Fallbacks PASS; drei vorhandene absichtlich
schwierige Decoderbedingungen bleiben observed-limit, keine neuen FAILs.
Nachweise: tmp/patient-import-session-values/ladder-fixed.log und
baseline-ladder-fixed/results.json. Testkorrektur separat als Commit aed8d33.
Der vollständige Commit-Hook wird für den anschließenden Import-Fix erneut
ungekürzt ausgeführt.

## Grenzen

Lokaler Kandidat, kein Merge und keine Live-Veröffentlichung. Bereits früher
kopierte Trainingswerte werden nicht nachträglich gelöscht, da sie nicht sicher
von manuell erfassten Werten zu unterscheiden sind. Das automatische Schreiben
alter Werte ließ sich für Aktualisieren in diesem Szenario nicht reproduzieren.
