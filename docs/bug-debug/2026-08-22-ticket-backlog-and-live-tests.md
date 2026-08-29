# 2026-08-22 – KGG Ticket-Backlog und Live-Test-Merkliste

## Zweck

Diese Datei ist die dauerhafte Übergabe für noch offene Live-/Realgerät-Tests
und bekannte Ticketblöcke. Sie enthält nur synthetische Testfälle und keine
Patientendaten.

## Belegter Stand

- Kanonischer Remote-Stand: `origin/main` / `ad6433a`.
- Therapeut:innen-Quelle: v071, `1.0.71-pdf-global-exercise-numbering`.
- Veröffentlichtes Therapeut:innen-Web: r0426 / v1.0.65.
- Veröffentlichtes Android-Shell-Manifest: v401.
- Patienten-App-Quelle: v79; der reale Browser-/Pages-Stand muss pro Test notiert werden.
- Lokale Browser- und Pipeline-Smokes ersetzen keinen Realgerät- oder Live-Nachweis.

## Offene Live-/Realgerät-Tests

Statuswerte: `pending-real-device`, `blocked-remote-access`, `scope-open`,
`passed` oder `failed`. Ein Test wird erst nach dokumentiertem Gerät, Browser,
Version, Beobachtung und anonymisiertem Screenshot als `passed` markiert.

| Priorität | Test/Ticket | Gerät/Kanal | Abnahme |
|---|---|---|---|
| P0 | RD-001 / Ticket 001 | Admin-Browser | Sieben Übungen anlegen, umbenennen, löschen, umsortieren; Speichern, QR und PDF prüfen; nach Reload und in zweitem Browser gleiche Anzahl. |
| P0 | RD-002 / Ticket 002 | Neues Smartphone-Profil | QR/Link genau einmal öffnen; ohne Reload/Zweitscan Scanner, Planliste, Löschen, Kartenstatus, Satz 1–3 und Schmerztrigger prüfen. |
| P0 | RD-003 / Tickets 003–006, 009, 032 | Echtes iPhone, Safari | Lange Namen mit/ohne Bild, Kartenstatus, Schmerztrigger, Vorwert-Schimmer, vollständiger QR-Kamerarahmen und keine abgeschnittenen Inhalte prüfen. |
| P0 | RD-004 / Ticket 008 | Tatsächlich verwendetes Tablet | Portrait/Landscape, Übungspakete-Button, Touchziel, Dialog, Planname, Speichern und Rückkehr prüfen. |
| P0 | RD-005 / Ticket 032 | Mindestens Android und iPhone | QR bei normaler, schräger, kleiner, weiter und dunkler Aufnahme sowie mit mehreren Übungen/Plänen testen; Gerät, OS, Browser und Version notieren. |
| P1 | RD-006 / Ticket 007 | Echtes Patienten-Smartphone | Unbenannte und benannte Pläne importieren, umbenennen, Reload/Planwechsel/erneuten QR-Import prüfen; Werte, Status, Medien und `currentPlan` müssen erhalten bleiben. |
| P1 | RD-007 / Ticket 026 | Externer Custom-GPT-Editor | Vier kanonische Admin-/Patient-Ressourcen und Actions abgleichen; erst nach echter Prüfung `LIVE_PASS` zulassen. Kein Preview oder Dispatch während `target-pending-live-editor-sync`. |
| P2 | Ticket 012 | Papierdruck, optional | Mehrseitige PDF mit sichtbaren Nummern drucken und `EX1…EX9` prüfen. Technische Integration ist dadurch nicht blockiert. |

## Bekannte Ticketliste

| Ticket | Priorität | Status | Kurzbeschreibung / nächster Schritt |
|---|---:|---|---|
| 001 | P0 | Integriert, Live-Test offen | Mehrübungsplan darf während Eingabe nicht auf eine Übung kollabieren; RD-001 durchführen. |
| 002 | P0 | Integriert, Live-Test offen | Patienten-App muss beim ersten Öffnen vollständig und ohne Reload/Zweitscan starten; RD-002 durchführen. |
| 003 | P0 | Integriert, iPhone-Test offen | Thumbnails, lange Namen und Kartenabstände mit/ohne Bild prüfen; RD-003. |
| 004 | P0 | Integriert, Live-Test offen | Drei identische Sätze müssen ausdrücklich als `Satz 1–3` erscheinen; RD-003. |
| 005 | P0 | Integriert, Live-Test offen | Offen/Teilweise/Bearbeitet im geschlossenen Kartenzustand prüfen; RD-003. |
| 006 | P0 | Integriert, Live-Test offen | Geschlossen nur `Schmerzen?`, Tap öffnet die Skala, Schließen stellt Layout wieder her; RD-003. |
| 007 | P1 | Integriert auf origin/main, Live-Test offen | Planname/Umbenennen darf Werte, Status, Medien und zentrale Planquelle nicht verändern; RD-006. |
| 008 | P0 | Integriert, Tablet-Test offen | Bestehenden Übungspaket-Button auf echtem Tablet prüfen; RD-004. |
| 009 | P1 | Scope offen | Entscheiden: Admin-Trefferbutton, Patient-„Vorwert übernehmen“ oder beide; erst danach gezielt abnehmen oder patchen. |
| 012 | P2 | Integriert auf origin/main | PDF-Nummern laufen seitenübergreifend global; optionaler Papierdrucktest offen. |
| 026 | P1 | Lokal `TARGET_PASS`, `LIVE_PASS` offen | GPT-Lifecycle-/Ticket-Registry-Vertrag lokal geprüft; externe Editor-Synchronisierung und strikter Live-Audit fehlen. |
| 032 | P0 | Integriert auf origin/main, Geräte-Test offen | QR-/Kamera-Varianten auf echten Android-/iPhone-Geräten testen; synthetische Warnfälle nicht als bestanden werten. |
| 011, 013, 014, 020, 031 | P2 | Research offen | Im aktiven Handoff ist nur die Research-Reihe genannt; belastbare Beschreibungen fehlen. Keine Ticketdetails oder Statuswerte erfinden. |

## Was Codex jetzt noch tun kann

- Testergebnisse anhand dieses Formulars aufnehmen und als `passed`, `failed`
  oder `blocked` dokumentieren:

  ```text
  Test-ID:
  Ergebnis:
  Zeitpunkt (Europe/Berlin):
  Gerät / OS:
  Browser:
  App-Version:
  Beobachtung:
  Erwartung erfüllt:
  Screenshot/Pfad (ohne Patientendaten):
  Folge-Ticket oder Commit:
  ```

- Lokale Regressionen, Source-/Manifest-Verträge und isolierte PR-Kandidaten
  prüfen oder vorbereiten.
- Bei einem späteren KGG-Auftrag diese offene Liste zuerst vorlegen und die
  noch nicht erledigten Tests erinnern.

## Grenzen der Erinnerung

Diese Datei ist die dauerhafte Projektübergabe. Codex kann sie bei späteren
KGG-Aufträgen wieder auslesen und die offenen Tests nennen. Eine zeitgesteuerte
Benachrichtigung zu einem bestimmten Datum/Uhrzeit ist davon getrennt und
braucht einen ausdrücklich angegebenen Zeitpunkt.

## Nicht anfassen

Keine Patientendaten, keine Secrets, kein Preview-/Dispatch-/Memory-Write und
keine automatische Änderung von Ticket- oder GPT-Live-Status ohne belegten
Nachweis.
