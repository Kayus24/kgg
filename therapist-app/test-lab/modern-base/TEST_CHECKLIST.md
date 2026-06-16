# KGG Modern Base Candidates - Test Checklist

## Ziel

Pruefen, ob die alte v360/v366-Kollegenbasis als stabilere neue Arbeitsbasis taugt, bevor v389 weiter repariert wird. v383 bleibt als zweite Vergleichsbasis erhalten.

## Testdateien

- Empfehlung zuerst: `KGG_APP_KOLLEGEN_v390_v360_v366_modern_base_candidate.html`
- Basis: `therapist-app/releases/v360/web/KGG_APP_KOLLEGEN_v360_sync_bundle_qr.html`
- Vergleich danach: `KGG_APP_KOLLEGEN_v390_modern_base_candidate.html`
- Vergleichsbasis: `therapist-app/releases/v383/web/KGG_APP_KOLLEGEN_v383_ui_flow_stability.html`
- Keine Funktionslogik geaendert, nur Test-Lab-Identity.

## Kern-UI testen

- Plan erstellen.
- Uebungen eingeben und hinzufuegen.
- Uebungskarten anzeigen lassen.
- Drag am Handle: startet erst nach kurzem Halten.
- Drag am Handle: Karte bleibt sichtbar am Finger.
- Drag am Handle: kein Chaos-/Lueckenfeld.
- Scrollen im Planbereich startet keinen Drag.
- Swipe links/rechts loescht weiterhin echt.
- Textfeld sitzt sichtbar unter den Karten.
- Vorschlaege/Bank springen nicht auf falsche Hoehe.

## Funktions-Smoke

- Plan-State bleibt nach Bearbeitung erhalten.
- PDF-Button oeffnet/erzeugt Ausgabe.
- Patienten-App/QR-Button oeffnet Ausgabe.
- Scan-/Foto-Datei-Flow startet.
- Keine Roh-JSON/Base64-Debugdaten fuer Patient:innen sichtbar.

## Entscheidung

- Wenn v360/v366-Kern-UI stabiler als v389 ist: diese Basis modernisieren.
- Wenn v360/v366 gut ist, aber ein Modul fehlt: Modul spaeter separat nachziehen.
- Wenn v360/v366 schlechter ist, v383 als Zwischenbasis pruefen.
- Wenn QR/PDF/Scan/Plan-State schlechter sind: v389 nur als frische Testkopie reparieren oder Hybrid pruefen.
- Wenn ein spaeteres Modul neue UI-Fehler erzeugt: Modul zurueckstellen, nicht weiterflicken.
