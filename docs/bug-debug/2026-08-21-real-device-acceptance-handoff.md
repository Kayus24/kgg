# KGG Realgeräte-Abnahme – Ticket-Session 1

**Status:** `pending-real-device`
**Erstellt:** 2026-08-21
**Lokaler Stand:** `codex/ticket-session-1` / `d898b423ee324a8f8f4f4115a8dd015e2ed34afc`
**Bereich:** Admin-/Patient-App, QR, PWA, Tablet, Planverwaltung

Diese Übergabe enthält nur Tests, die lokale Browser-, Parser- und PDF-Prüfungen nicht vollständig ersetzen können. Es werden keine Patientendaten benötigt. Screenshots dürfen nur synthetische Pläne und anonymisierte Testdaten zeigen.

## Ergebnisregeln

- `pending-real-device`: noch nicht auf einem echten Gerät durchgeführt.
- `pass`: nur nach dokumentierter Durchführung auf dem genannten Gerät.
- `fail`: reproduzierbarer Fehler mit Beleg.
- `blocked`: Durchführung wegen Gerät, Zugriff oder Verbindung nicht möglich.
- Lokale Tests oder ein grüner Preview-Test allein dürfen keinen Realgeräte-Test auf `pass` setzen.
- Der Custom GPT darf keine Ergebnisse erfinden und keine Ticket-/Memory-Statusänderung selbstständig durchführen.

## Abnahmefälle

### RD-001 – Admin-Mehrübungsplan / Live-Master

**Gerät:** Max’ tatsächlich verwendeter Admin-Browser
**Status:** `pending-real-device`

1. Einen synthetischen Plan mit mindestens sieben Übungen anlegen, darunter Beinpresse, Dips, Abduktion Maschine, Adduktion Maschine und Latziehen.
2. Während des Schreibens die Textquelle und die strukturierte Anzahl beobachten.
3. Eine Übung bewusst umbenennen, eine löschen und eine umsortieren.
4. Speichern, QR und PDF erzeugen.
5. Nach Reload und in einem zweiten Browser die Übungsanzahl vergleichen.

**Erwartung:** Kein Zwischenzustand fällt auf „1 Übung“ zurück. Textfeld, strukturierter Plan, QR und PDF enthalten dieselben Übungen. Bewusste Änderungen bleiben möglich.

### RD-002 – Patienten-App First Load

**Gerät:** neues/gelöschtes Browserprofil auf einem echten Smartphone
**Status:** `pending-real-device`

1. Den Plan-Link oder QR-Code genau einmal öffnen.
2. Keinen Reload und keinen Zweitscan durchführen.
3. Planliste, rotes X, Kartenstatus, Satz-1–3-Ausgabe und Schmerztrigger prüfen.
4. Das sichtbare Versionslabel notieren.

**Erwartung:** Der aktuelle vollständige Stand erscheint beim ersten Öffnen. Erwartete Version des lokalen Kandidaten: `v79`.

### RD-003 – iPhone-Karten und QR-Kamerarahmen

**Gerät:** echtes iPhone, Safari
**Status:** `pending-real-device`

Mit langen Übungsnamen und einem synthetischen Plan mit und ohne Bilder prüfen:

- Bild verdeckt weder Übungsname noch Satzdaten, Gewicht, Wiederholungen oder T1-Werte.
- Karten ohne Bild haben keinen unnötigen Leerraum.
- Die geschlossene Karte zeigt ihren Bearbeitungsstatus.
- „Schmerzen?“ öffnet die Skala erst nach Antippen.
- „Vorwert übernehmen“ ist antippbar und schimmert ruhig von links nach rechts.
- Das sichtbare QR-Livebild zeigt den vollständigen Kamerarahmen; schwarze Letterbox-Flächen sind zulässig.

### RD-004 – Echtes Tablet / Übungspaket

**Gerät:** das tatsächlich verwendete Tablet
**Status:** `pending-real-device`

In Portrait und Landscape prüfen:

- Übungspakete-Button ist sichtbar und erreichbar.
- Touchziel lässt sich zuverlässig antippen.
- Bestehender Speichern-Dialog öffnet sich.
- Planname ist fokussiert.
- Speichern und Rückkehr in die normale Ansicht funktionieren.

### RD-005 – QR-Gerätevarianz

**Geräte:** mindestens ein Android- und ein iPhone-Gerät
**Status:** `pending-real-device`

Je Gerät testen:

- normaler QR,
- Plan mit mehreren Übungen,
- mehrere Pläne,
- leicht schräger QR,
- schwaches Licht,
- unterschiedliche Abstände.

Pro Durchlauf dokumentieren: Gerät, OS, Browser, sichtbare App-Version, Ergebnis und anonymisierten Screenshot.

### RD-006 – Planname / Umbenennen / Erhalt der Werte

**Gerät:** echtes Patienten-Smartphone
**Status:** `pending-real-device`

1. Zwei unbenannte Pläne und zwei benannte Pläne importieren.
2. Prüfen, dass deterministische Fallbacknamen unterscheidbar sind.
3. Einen Plan über die bestehende Planverwaltung umbenennen.
4. Reload, Planwechsel und erneuten QR-Import durchführen.
5. Vorher eingetragene Werte und Kartenstatus kontrollieren.

**Erwartung:** Titel bleibt erhalten; Werte, Status, Medien und zentrale Planquelle bleiben unverändert; das rote X löscht weiterhin erst nach Bestätigung.

### RD-007 – Externer Patient-GPT-Sync

**Voraussetzung:** Remote-/Editorzugriff funktioniert wieder.
**Status:** `blocked-remote-access`

1. Die vier kanonischen Patient-Knowledge-Dateien und die Actions im externen Editor abgleichen.
2. Nur Pflicht-Reads ausführen; kein Dispatch und kein Release.
3. Erst nach echter Editorprüfung den Snapshot auf `live-synced` setzen.
4. Danach den strikten lokalen Audit mit `--require-live-synced` ausführen.

Bis dahin muss der Snapshot `target-pending-live-editor-sync` bleiben.

## Bekannter separater Automatikbefund

`tablet-splitter-scale-drag` schlägt in der breiten UI-Regression bereits auf dem unveränderten Main-Bestand fehl. Dieser Befund ist kein Realgeräte-Test und gehört nicht in die Abnahme der obigen Produktfunktionen.

## Ergebnisformular

Für jeden Testfall nur diesen Block ergänzen:

```text
Test-ID: RD-___
Ergebnis: pass | fail | blocked
Zeitpunkt (Europe/Berlin):
Gerät / OS:
Browser:
App-Version:
Beobachtung:
Erwartung erfüllt: ja | nein
Screenshot/Pfad (ohne Patientendaten):
Folge-Ticket oder Commit:
```

Der Custom GPT darf dieses Formular aus einer ausdrücklichen Nachricht von Max vorbereiten oder ausfüllen, aber nur mit den tatsächlich genannten Beobachtungen. Bei `fail` zuerst reproduzierbaren Befund und Beleg dokumentieren, dann Codex für Analyse/Patch einplanen.
