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

## Repo-Navigation

Dieses Repository enthält heute sowohl die Patienten-App als auch die modulare Therapeut:innen-App, den Android-Wrapper, die Releasepipeline und unveränderliche Releaseartefakte.

| Bereich | Aktive Quelle | Bedeutung |
|---|---|---|
| Patienten-App | `index.html`, `patient-*.js`, `service-worker.js` | Editierbare Patienten-/PWA-Quelle |
| Therapeut:innen-App | `kgg-update/src/**` | Editierbare modulare Quelle |
| Therapeut:innen-Kandidat | `kgg-update/index.html`, `kgg-update/version.json` | Generiertes HTML und Kandidatenidentität |
| Live-Releases/APKs | `therapist-app/android_update_manifest.json` | Kanonischer veröffentlichter Admin-, Kolleg:innen- und Android-Stand |
| Legacy-Kompatibilität | `therapist-app/kgg_update_manifest.json` | Bestehende Kompatibilitätsansicht, nicht kanonisch |
| Android | `android-wrapper/**` | Native Wrapper-Quelle |
| Releases | `therapist-app/releases/**` | Historische, unveränderliche Artefakte |

Kandidat und Live-Stand dürfen bewusst voneinander abweichen. Deshalb immer beide Manifestdateien lesen und nie aus Dateinamen oder historischen Aliasdateien auf den Live-Stand schließen.

`therapist-app/admin.html` entspricht bytegenau dem Admin-Artefakt r0389/v389. `therapist-app/kollegen.html` entspricht dem historischen v389-Kolleg:innen-Artefakt, jedoch nicht der später abgeleiteten Datei `therapist-app/releases/web/r0389/colleague.html`. Beide Dateien sind historische Aliase und keine Patchbasis.

Normale Quellsuchen verwenden die aktiven Verzeichnisse. Für Historienprüfungen wird der ignorierte Releasepfad ausdrücklich mit `rg --no-ignore` angegeben; Beispiele stehen in `AGENTS.md`.
