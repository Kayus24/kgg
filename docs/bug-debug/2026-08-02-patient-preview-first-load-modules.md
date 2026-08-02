# Patient Preview First-Load Modules

## Symptom

Ein Patient-Preview-Run konnte vollstaendig gruen sein, obwohl die erste im Browser oder in der Test-App geoeffnete `index.html` den Scanner und weitere Patient-Module noch nicht geladen hatte. Die Dateien waren im Artefakt vorhanden, wurden aber erst durch `service-worker.js` in einen spaeteren, bereits kontrollierten Seitenaufruf injiziert.

## Ursache

`release-pipeline/kgg_patient_gpt_write_gate.py` kopierte die Root-`index.html` unveraendert in den isolierten Preview-Ordner. Die kanonische Modulliste existierte nur in `service-worker.js`. Beim ersten Aufruf war noch kein Service-Worker-Controller aktiv. Dadurch konnte die Test-App eine unvollstaendige Preview anzeigen, bis ein Reload oder eine weitere Navigation erfolgte.

## Fix

- Der Preview-Publisher liest die kanonische Modulinjektion aus dem mitgelieferten Service Worker.
- Er entfernt vorhandene direkte Modul-Tags und fuegt dieselbe Liste genau einmal in die Preview-`index.html` ein.
- Fehlende Dateien, doppelte Module oder eine nicht eindeutig lesbare Service-Worker-Injektion blockieren das Gate.
- Ein Browser-Smoke startet die Preview mit blockiertem Service Worker und prueft Scanner-Modul, No-Plan-Rettungsbutton, Kamera-Fallback und horizontale Geometrie.

## Dauerhafte Regel

Ein gruenes Preview, vorhandene Dateien und ein Artefakt beweisen noch keinen funktionierenden ersten Seitenaufruf. Preview-Erfolg erfordert eine direkt vollstaendige `index.html` und einen First-Load-Test ohne vorhandenen Service-Worker-Controller oder Reload.
