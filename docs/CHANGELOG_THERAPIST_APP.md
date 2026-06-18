# Therapeuten-App Changelog

Dieses Changelog dokumentiert bewusst nur Änderungen an der Therapeuten-/Admin-/Kolleg:innen-App.
Patient:innen-App-Änderungen gehören in `CHANGELOG_PATIENT_APP.md`.

## 2026-06-18 – Doku-Struktur für Therapeuten-App und Bug-Debug

### Added
- Eigenes Changelog für die Therapeuten-/Admin-App angelegt.
- Verweis auf strukturierten Bug-Debug-Ordner ergänzt.

### Ziel
- Änderungen an der Therapeuten-App getrennt von Patient:innen-App-Fixes dokumentieren.
- Wiederkehrende Probleme mit Ursache, Lösung und Tests auffindbar machen.

### Dateien
- `docs/CHANGELOG_THERAPIST_APP.md`
- `docs/bug-debug/README.md`

### Safety
- Keine Änderung an HTML/CSS/JS-App-Logik.
- Keine Layout-Änderung.
- Keine Änderung an PDF, QR, Parser, Scan/OCR, Storage oder Übungsdatenbank.
- Keine API-Keys oder Secrets ergänzt.

## Arbeitsregel ab jetzt

Jeder relevante Therapeuten-App-Fix soll hier kurz eingetragen werden:

- Datum
- Version/Datei
- Problem
- Änderung
- Test/Abnahmekriterien
- Nicht angefasste Bereiche
