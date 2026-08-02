# Patient-Kamera wirkt gezoomt und GPT stoppt an Koordinations-404

## Problem

Der mobile Live-Scanner der Patient:innen-App zeigt nur einen Ausschnitt des Kamerabilds und wirkt dadurch stark gezoomt. Der Update-GPT diagnostiziert die Ursache, startet aber keinen Patient-Preview-Write, weil der private Koordinationsindex HTTP 404 liefert.

## Ursache

`patient-start-scan.js` setzt einen breiten Kamerastream mit `object-fit: cover` in einen mobilen `3/4`-Rahmen. Das beschneidet die Seiten des Bilds. Unabhaengig davon verwiesen beide GPT-Actions bereits auf `coordination/index.json`, obwohl der vorbereitete Koordinationsbranch noch nicht in `kgg-project-memory/main` integriert war.

## Loesung/Fix

- Fuer den visuellen Scanner-Patch `object-fit: contain` verwenden und keine Kamera-Zoom-Constraints einfuehren.
- Aenderungen an `patient-start-scan.js` immer als `patient-camera` routen und die `patient-scan`-Regression ausfuehren.
- Die private Koordinationsqueue vollstaendig ausrollen.
- Queue-Ausfaelle nur bei echten Interface-/Cross-App-Aenderungen als harten Stopp behandeln. Isolierte visuelle Patient-UI-Patches duerfen mit frischem Main-/Source-Nachweis als `coordination_unavailable` weiterlaufen.

## Test / Abnahmekriterien

- Breiter Stream `1280x720` und hoher Stream `720x1280` bleiben im mobilen Kamerarahmen vollstaendig sichtbar.
- `getComputedStyle(video).objectFit` ist `contain`.
- Kein horizontaler Overflow; Schliessen und Fallbacks bleiben bedienbar.
- QR-Erkennung, Track-Cleanup, Plan und Trainingswerte bleiben unveraendert.
- Koordinationsindex liefert keinen 404 und ein leerer Index wird als keine offene Aufgabe behandelt.

## Nicht anfassen

- QR-/KGGH2-/KGGD1-Vertrag
- Parser und Plan-State
- Patientenspeicher und Trainingswerte
- Admin-App, PDF und Android-Wrapper

## Risiken

`contain` kann bei abweichendem Seitenverhaeltnis schwarze Restflaechen anzeigen. Das ist akzeptiert; ein abgeschnittenes Kamerabild ist nicht akzeptiert.
