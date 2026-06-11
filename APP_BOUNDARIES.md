# KGG App Boundaries

Diese Datei ist eine Sicherheits- und Orientierungsdatei fuer Max, Codex und spaetere Agenten.

Sie dokumentiert die Grenze zwischen Patienten-App und Therapeuten-App. Sie ist absichtlich nur Dokumentation und veraendert kein Laufzeitverhalten.

## Grundregel

Die KGG-Patienten-App und die KGG-Therapeuten-App duerfen funktional zusammenarbeiten, sollen aber gedanklich und bei Patches klar getrennt bleiben.

Gemeinsame Schnittstelle ist nur das stabile Plan-/QR-/Rueckgabe-QR-Datenformat.

## Patienten-App

### Zielgruppe

Patient:innen.

### Zweck

Die Patienten-App zeigt einen bereits erstellten Trainingsplan an, speichert Trainingswerte lokal und erzeugt Rueckgabe-Daten fuer Therapeut:innen.

### Typische Aufgaben

- Plan per QR-/Hash-Link oeffnen.
- Uebungen anzeigen.
- Trainingswerte pro Tag eintragen.
- Schmerz 0-10 dokumentieren.
- Werte lokal/offline speichern.
- Rueckgabe-QR fuer Therapeut:innen erzeugen.
- Auf dem Handy als PWA / Startbildschirm-App laufen.

### Typische Dateien in diesem Repo

- `index.html` - Patienten-Handy-App / Live-Einstieg.
- `manifest.json` - PWA-Manifest.
- `service-worker.js` - Offline-Cache und Modul-Ladeverhalten.
- `icon.svg` - App-Icon.
- `patient-*.js` - Patienten-App-Zusatzmodule.
- `collapse-cards.js` - UI-Zusatzverhalten fuer Patienten-App.

### Darf die Patienten-App nicht tun

- Keine Patientenverwaltung.
- Keine Diagnosen oder Verordnungsdaten im normalen QR-Link.
- Keine PDF-Erzeugung fuer Therapeut:innen.
- Keine Admin-/Therapeuten-UI anzeigen.
- Kein JSON/Base64 als normale Patient:innen-Ausgabe anzeigen.
- Keine API-Keys oder geheimen Daten enthalten.

## Therapeuten-App

### Zielgruppe

Therapeut:innen / Kolleg:innen.

### Zweck

Die Therapeuten-App erstellt und bearbeitet KGG-Plaene, nutzt Parser/Scanner/Uebungsbank, erzeugt PDF/QR und kann Rueckgabe-Daten aus der Patienten-App einlesen.

### Typische Aufgaben

- Trainingsplan erstellen und bearbeiten.
- Uebungen aus Datenbank/Bank/Textfeld uebernehmen.
- Textfeld-Parser verwenden.
- Plan-State pflegen.
- PDF erzeugen.
- QR/Patientenlink erzeugen.
- Rueckgabe-QR scannen/importieren.
- Android/APK/WebView-Variante bereitstellen.

### Typische Dateien ausserhalb oder neben diesem Patienten-Repo

- Admin-/Therapeuten-HTML.
- Kolleg:innen-HTML.
- Android WebView / APK-Projektdateien.
- Scanner-Modul.
- PDF-Modul.
- Textfeld-Parser.
- Uebungsbank.
- Export-/Import-Core.
- QR-Core.

### Darf die Therapeuten-App nicht nebenbei tun

- Patienten-App-Service-Worker ohne klaren Auftrag aendern.
- Patienten-App-Offline-Cache nebenbei aendern.
- QR-Datenformat ohne Source-of-Truth-Entscheidung aendern.
- Patient:innen-Ausgabe mit JSON/Base64 verwechseln.
- Layout der Patienten-App nebenbei umbauen.

## Gemeinsame Schnittstelle

Diese Bereiche muessen stabil bleiben:

- Plan-State.
- QR-/Hash-Link-Format.
- Rueckgabe-QR-Format.
- Lokale Speicherlogik der Patienten-App.
- Bedeutungen von Uebungen, Saetzen, Seiten, Gewicht, Wiederholungen und Schmerzskala.

Aenderungen an dieser Schnittstelle brauchen ausdrueckliche Freigabe von Max.

## Risiko-Kategorien fuer Patches

### Sicher anfassen

- Neue Dokumentationsdateien.
- README-Ergaenzungen ohne Aenderung technischer Aussagen.
- Repo-Map / Moduluebersicht.
- Changelog / Patch-Log.
- Kommentare in separaten Doku-Dateien.

### Nur mit Max-Freigabe anfassen

- `service-worker.js`.
- `index.html`.
- `patient-*.js`.
- `collapse-cards.js`.
- QR-/Hash-Parsing.
- Rueckgabe-QR.
- LocalStorage-Keys.
- PWA-Installationslogik.
- Offline-Cache.

### Niemals nebenbei anfassen

- QR-Datenformat.
- Patienten-Ausgabe-Regeln.
- PDF/QR/Parser/Scan-Logik.
- API-Key-Handling.
- Android/APK-Build-Konfiguration.
- Layout oder UI-Flow, wenn der Auftrag nicht genau dazu passt.

## Codex-Regel

Vor jedem Patch muss Codex zuerst einordnen:

1. Patienten-App?
2. Therapeuten-App?
3. Gemeinsame Schnittstelle?
4. Reine Dokumentation?
5. Source-of-Truth-Entscheidung noetig?

Wenn die Antwort unklar ist, darf Codex keinen Code-Patch machen.

## Aktuelle Arbeitsregel

Dieses Repo dient aktuell vor allem der Patienten-App/PWA-Bereitstellung.

Die Therapeuten-App darf hier nur dokumentiert oder angebunden werden, solange Max nicht ausdruecklich einen Code-Patch fuer diesen Bereich freigibt.
