# Patient First-Load Modules

## Symptom

Ein Patient-Preview-Run konnte vollstaendig gruen sein, obwohl die erste im Browser oder in der Test-App geoeffnete `index.html` den Scanner und weitere Patient-Module noch nicht geladen hatte. Das gleiche Risiko bestand fuer den echten ersten QR-Aufruf: Die Dateien waren im Artefakt vorhanden, wurden aber erst durch `service-worker.js` in einen spaeteren, bereits kontrollierten Seitenaufruf injiziert.

## Ursache

Die Root-`index.html` lud nur ein Teilmodul direkt. Die vollstaendige Modulliste existierte nur in `service-worker.js`. Beim ersten Aufruf war noch kein Service-Worker-Controller aktiv. Dadurch konnte die Test-App oder die echte Patienten-PWA eine unvollstaendige Ansicht anzeigen, bis ein Reload oder eine weitere Navigation erfolgte.

## Fix

- Die Root-`index.html` laedt alle benoetigten Patienten-Module direkt und genau einmal.
- `service-worker.js` liefert diese HTML-Datei unveraendert aus; er ist Cache/Offline-Schicht und keine Laufzeit-Abhaengigkeit fuer den ersten Aufruf.
- Der PWA-Vertrag prueft die direkten Modul-Tags und die Cache-Liste.
- Ein Browser-Smoke startet die Root-PWA mit blockiertem Service Worker und prueft Scanner, No-Plan-Rettungsbutton sowie die direkte Modulinitialisierung.

## Dauerhafte Regel

Ein gruenes Preview, vorhandene Dateien und ein Artefakt beweisen noch keinen funktionierenden ersten Seitenaufruf. Jede neue Patienten-Modulliste muss direkt in der Root-`index.html` vollstaendig sein und den First-Load-Test ohne Service-Worker-Controller oder Reload bestehen.

## Workflow-Hindernis

Der alte Ablauf konnte nur durch einen manuellen Reload, eine zweite Navigation oder einen erneut angestossenen GPT-Zug sichtbar vollstaendig werden. Das ist kein zulaessiger Workaround: Ein GPT darf Patient:innen nicht bitten, erneut zu scannen oder die Seite neu zu laden, um fehlende Funktionen zu erhalten. Wenn der direkte First-Load-Smoke ohne Service Worker scheitert, muss der Ablauf als fehlgeschlagen dokumentiert und die Root-Ladefolge repariert werden.
