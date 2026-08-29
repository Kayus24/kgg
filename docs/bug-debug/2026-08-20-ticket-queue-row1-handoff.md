# KGG Ticket-Queue Reihe 1 – Testübergabe

Stand: 2026-08-20  
Zweck: Übergabe der noch offenen Nachweise an Custom GPT + Max.  
Wichtig: Diese Datei ändert keinen Ticketstatus und schließt kein Ticket.

## Verifizierter technischer Stand

- KGG-Main: `5d0f9395e6d493f84731fd8980d363c305531553`.
- Admin-Main: v070 (`1.0.70-tablet-package-save`).
- Patient-Main/PWA: v77.
- Automatische lokale Smokes der Reihe 1: grün.
- Admin-live und Patient-live sind nicht mit Main gleichzusetzen; ein grüner Main-Smoke ist kein Realgerät-Nachweis.
- Patient-Custom-GPT: sicherer `stale_context`-Stopp wegen Knowledge-Hash-/v77-Drift; keine Ticketbewertung durch den Patient-GPT.
- Admin-Custom-GPT: Read-only-Lauf wurde nach Quellenprüfung unvollständig beendet; nur die ausdrücklich unten genannten Aussagen gelten als belegt.

## Ticket 001 – Live-Master kollabiert auf eine Übung

Status für Übergabe: IMPLEMENTIERT AUF MAIN – REAL-/LIVE-VERIFIKATION OFFEN.

Belege:

- Plan-State-Fix v067–v069 ist in Main enthalten.
- `kgg_html_logic_smoke.js` prüft strukturierte Namen und Komma-Namen.
- Textblock-Critical/Regression und UI-Stability waren grün.

Noch testen:

1. Admin-Main/Preview mit sieben Übungen und Text `Beinpresse, Dips, Abduktion Maschine, Adduktion Maschine, Latziehen`.
2. Während des Tippens darf die Struktur nicht auf eine Übung fallen.
3. Bewusstes Umbenennen, Löschen und Umsortieren muss weiterhin sofort funktionieren.
4. Speichern, QR-Erzeugung und PDF müssen alle Übungen enthalten.
5. Nach Reload und auf einem zweiten Browser die Plananzahl vergleichen.

Erwartetes Ergebnis: Textfeld und strukturierter Plan bleiben konsistent; kein Datenverlust und keine Ein-Übungs-Übertragung.

## Ticket 002 – Patient First Load

Status für Übergabe: IMPLEMENTIERT AUF MAIN – FRISCHER REALGERÄT-/LIVE-FIRST-LOAD OFFEN.

Belege:

- `kgg_patient_preview_first_load_smoke.js`: Service Worker blockiert, 22 Module direkt, genau eine Navigation, direkte Initialisierung grün.
- `kgg_patient_runtime_progress_playwright.js`: v77, frischer Lauf ohne Reload/Zweitscan grün.
- PWA-Vertrag und Update-Recovery grün.

Noch testen:

1. Neues/gelöschtes Browserprofil oder neues Gerät öffnen.
2. Einen QR-/Plan-Link genau einmal scannen/öffnen.
3. Ohne Reload und ohne zweiten Scan prüfen: Scanner, Planliste, Löschen, Kartenstatus, Satz-1–3 und Schmerztrigger.
4. Sichtbares Versionslabel und vollständige aktuelle Oberfläche dokumentieren.

## Tickets 003–006 – Patient-Funktionen

Gemeinsame Ursache prüfen: First Load/Cache/Modulstand. Nicht vier unabhängige Patches beginnen, bevor der Einzel-First-Load-Test abgeschlossen ist.

- **003 Thumbnails:** `kgg_patient_preview_first_load_smoke.js` prüft lokale Thumbnail-Geometrie, lange Titel und No-Image-Padding. Real-iPhone-Test mit langen Namen und Bild/ohne Bild offen.
- **004 Satz 1–3:** `kgg_patient_summary_smoke.js` grün. Realgerät-Test mit drei identischen Sätzen offen; Anzeige muss ausdrücklich `Satz 1–3` (oder gleichwertig) nennen.
- **005 Kartenstatus:** `kgg_patient_card_progress_smoke.js` und Runtime-Progress-Smoke grün. Realgerät-Test für Offen/Teilweise/Bearbeitet im geschlossenen Zustand offen.
- **006 Schmerztrigger:** `kgg_patient_pain_vertical_smoke.js` grün; kompakter Trigger/Modal ist auf Main. Realgerät-Test: geschlossen nur `Schmerzen?`, Tap öffnet, Schließen stellt Kartenlayout wieder her.

## Ticket 007 – Trainingspläne benennen/umbenennen

Status für Übergabe: TEILWEISE IMPLEMENTIERT.

- Mehrplan-Speicher, Auswahl, Anzeige von Titel/Default und rotes Löschen sind vorhanden.
- Ein belastbarer Patient-Flow zum späteren Umbenennen ist im aktuellen Main nicht belegt.
- Admin-Erstellung/Plan-Titel und additive QR-/Sharing-Kompatibilität müssen vor einem Patch als Datenmodell geprüft werden.

Noch testen/konzipieren:

1. Zwei Pläne ohne Titel, Defaultnamen und eindeutige Anzeige.
2. Zwei benannte Pläne über QR/Sharing übertragen.
3. Umbenennen im Patient-Flow: Persistenz nach Reload, Wechsel und erneutem Import.
4. Prüfen, dass `KGGDataStore.currentPlan` die einzige aktive Planquelle bleibt.

## Ticket 008 – Übungspakete auf Tablet

Status für Übergabe: IMPLEMENTIERT AUF MAIN – REALTABLET-VERIFIKATION OFFEN.

- v070 positioniert den bestehenden `savePackageBtn` im Tabletmodus sichtbar im Planheader.
- Tablet-Browser-Smoke für Dialog, Viewports und Rückkehr in die Handyansicht grün.
- Realgerät mit dem tatsächlich genutzten Tablet, Portrait/Landscape und Touch muss noch geprüft werden.

## Ticket 009 – „Übung übernehmen“ hervorheben

Status für Übergabe: SCOPE-KLÄRUNG NÖTIG, ADMIN-TICKET WEITER OFFEN.

- Das Registry-Ticket beschreibt den **Admin-Button** `[data-apply-hit]` („Treffer übernehmen"). Dafür ist in Main kein Schimmer belegt.
- Der vorhandene v77-Schimmer gehört ausschließlich zum **Patienten-Button** `#padLast` („Vorwert übernehmen"); dafür sind Patient-Smoke und Reduced-Motion-Prüfung grün.
- Diese beiden Funktionen nicht als dasselbe Ticket schließen.

Noch testen/entscheiden:

1. Max bestätigt, ob der gewünschte Schimmer am Admin-Treffer-Button, am Patient-„Vorwert übernehmen“-Button oder an beiden gilt.
2. Falls Admin: isolierte Admin-Preview mit ruhigem Links→Rechts-Schimmer, Reduced Motion und Tap-Verhalten.
3. Falls Patient: Realtelefon-Test des bereits vorhandenen v77-Schimmers; kein neuer Admin-Patch.

## Offene Realgerätliste für Max

- Admin: Ticket 001 Mehrübungsplan inklusive Speichern/QR/PDF.
- Patient: Ticket 002 frischer Erststart ohne Reload/Zweitscan.
- iPhone: Ticket 003 lange Namen mit/ohne Bild.
- Patient: Ticket 004 identische Sätze und explizite `Satz 1–3`-Anzeige.
- Patient: Ticket 005 geschlossene Kartenstatus.
- Patient: Ticket 006 kompakter Schmerztrigger.
- Patient: Ticket 007 Mehrplan-Titel und Umbenennen.
- Tablet: Ticket 008 Paketbutton, Portrait/Landscape, Touch.
- Je nach Scope von Ticket 009: Admin-Trefferbutton oder Patient-Vorwertbutton.

## Übergabe an Custom GPT

READ-ONLY bis alle Realtests dokumentiert sind. Keine Preview, kein Dispatch, kein Memory-Statuswechsel. Pro Test festhalten: Gerät/Browser, Main- oder Live-URL, Startzustand, genaue Schritte, sichtbares Ergebnis, Screenshot/Run-Referenz (ohne Patientendaten), PASS/FAIL und eine Next-Action.

## Nächste Reihe

## Reihe 2 – KGG-TICKET-012 (PDF-Nummerierung)

Status: OFFEN / Main reproduzierbar fehlerhaft; lokaler Kandidat vorhanden, aber noch nicht Main.

- Main `5d0f939`/v070 setzt in `normalizePdfExercise()` `exNo`, `displayLabel` und `machineLine` aus dem seitenlokalen `slotNo`; die klassische Vorlage beginnt deshalb auf jeder Folgeseite wieder mit `EX1`.
- Der separate Großdruck-Renderer nummeriert bereits global; die Korrektur darf den klassischen Slot-/EX-Vertrag nicht mit dem Layout-Slot verwechseln.
- Lokaler Kandidat `C:\src\kgg-ticket-session-1`, Commit `a136bdf`, v071. `kgg_html_logic_smoke.js` und `kgg_pdf_readability_smoke.js` grün; der Kandidat ist trotzdem noch nicht Main.
- Technische Mehrseiten-Abnahme mit sichtbaren Nummern sowie `exNo`/`machineLine` ist abgeschlossen. Offen bleibt nur der optionale physische Drucktest; er blockiert Preview/Main-Routing nicht.

Technische Abnahme am 2026-08-21 ergänzt:

- `python release-pipeline\\kgg_test_battery.py --level critical --suite pdf` grün: PDF-critical und PDF-readability-critical.
- Generierte Fälle `short-3`, `long-6`, `overflow-9` und `missing-image-3` ergaben die erwarteten 1/2/3/1 Seiten und korrekte Bildanzahlen.
- Gerenderte Mehrseiten-PDFs visuell geprüft: `EX1–EX3`, `EX4–EX6`, `EX7–EX9`, keine sichtbaren Überlagerungen oder abgeschnittenen Karten.
- `build_therapist_source.py --check` und `git diff --check` grün.
- Vollständiger Kandidatenlauf `kgg_test_battery.py --level critical` grün (117 Release-Tests, 33 Pipeline-Tests, 1 Skip); wegen fehlender Beta-Ausrichtung wurde ausschließlich `KGG_ALLOW_RELEASE_DRIFT=1` verwendet, kein Release ausgelöst.
- Der physische Drucktest ist ausdrücklich auf später verschoben und blockiert die technische Integration nicht.

Die nächsten Reihen bleiben nach Ticket 012: 026-Parität, 032/Device-Variance, danach 011/013/014/020/031-Research. Keine Reihe wird automatisch als erledigt markiert.

## Reihe 3 – Ticket 026 und Ticket 032 read-only Vorprüfung

- Ticket 026: Die GPT-Lifecycle-Gates, der Legacy-Wrapper-Schutz und die vollständige `editor-contract`-Prüfung sind im Main vorhanden. Der lokale Produktionsaudit ist mit dem aktuellen separaten Knowledge-Drift weiterhin `TARGET_PASS`, nicht `LIVE_PASS`; ein strenger Live-Nachweis bleibt bis zur externen Editor-Synchronisierung offen.
- Ticket 032/Device-Variance: Admin-Kamera-Smoke grün (BarcodeDetector, jsQR, Berechtigungsfallback, manuelles Foto). Die Patient-Scanner-Suite läuft mit 50+ synthetischen Perspektiv-/Distanz-/Rotation-/Lichtfällen, Multi-Plan-Erhalt und Track-Cleanup; mehrere extreme Klein-/Dunkel-, Trapez-, Asymmetrie- sowie starke Yaw/Pitch-Fälle melden jedoch erwartete `WARN`/keine sichere Erkennung. Die realen Android-/iPhone-Gerätevarianten sind damit nicht ersetzt; Gerätemodell, Browser und echte QR-Aufnahme fehlen weiterhin.
- Auf dem Arbeitsrechner ist `adb` nicht installiert und kein reales Android-Gerät verbunden; ein automatischer Gerätetest war daher nicht möglich.
- Der read-only Admin-GPT erhielt beide Themen nach frischem Pflichtstand. Sein abschließender Bericht kam im verfügbaren Antwortfenster nicht zurück; es wurde kein Preview, Dispatch oder Memory-Write ausgelöst. Das wird als `gpt_status_read_timeout` dokumentiert, nicht als Ticketbefund.
