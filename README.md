# KGG Handyplan

Lokale Patienten-App für KGG-Trainingspläne.

## Zweck

- Plan per QR-/Hash-Link öffnen
- Werte pro Trainingstag eintragen
- Schmerz 0–10 dokumentieren
- Rückgabe-QR für Therapeut:innen erzeugen
- Daten lokal im Browser speichern

## Datenschutz-Regel

QR-Links sollen keine Patientennamen, Diagnosen oder Verordnungsdaten enthalten. Empfohlen sind nur Plan-ID, Übungen, Einheiten, Sätze und Trainingswerte.

## Dateien

- `index.html` – Patienten-Handy-App
- `manifest.json` – PWA-Manifest
- `service-worker.js` – Offline-Cache
- `icon.svg` – App-Icon

## Aktueller Fokus

Die Therapeut:innen-App bleibt zunächst lokal. Dieses Repo dient vorerst der Patienten-App und Offline-/PWA-Bereitstellung.
