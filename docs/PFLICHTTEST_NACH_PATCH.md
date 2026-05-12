# Pflicht-Test nach jedem Patch

Diese Liste ist bewusst kurz. Sie soll verhindern, dass ein Patch unbemerkt wichtige Funktionen zerstört.

## 1. App-Start

- App öffnet ohne Fehlermeldung
- Hauptansicht lädt sichtbar
- Keine leere weiße Seite

## 2. Basis-Plan

- Neuen Plan erstellen oder vorhandenen Demo-Plan öffnen
- Übung hinzufügen oder vorhandene Übung anzeigen
- Werte eintragen
- Werte bleiben nach kurzer Navigation erhalten

## 3. Patienten-App

- Plan per Link/QR öffnen, falls vorhanden
- Trainingstag auswählen
- Kg/Wdh oder Werte eintragen
- Schmerzskala testen, falls vorhanden
- Rückgabe-QR erzeugen, falls vorhanden

## 4. Therapeut:innen-App

- Plan erstellen oder bearbeiten
- Übungsliste sichtbar
- Sätze/Wiederholungen/Werte plausibel
- Plan speichern oder exportieren, falls vorhanden

## 5. Kamera/Galerie/Scan

Nur testen, wenn diese Funktion im aktuellen Stand existiert:

- Kamera-Foto aufnehmen
- Galerie-Bild auswählen
- Nach Kamera und Galerie erscheint derselbe Folge-Dialog:
  - Seite anhängen
  - weiteren Plan scannen
  - fertig
- Bild wird nicht nur angezeigt, sondern wirklich dem Plan/Scan hinzugefügt

## 6. PDF und QR

Nur testen, wenn diese Funktion im aktuellen Stand existiert:

- PDF erzeugen
- QR erzeugen
- QR-Link öffnet erwartete Ansicht

## 7. Nach dem Test notieren

In `docs/VERSIONSLOG.md` eintragen:

- Versionsname
- Was wurde geändert?
- Was funktioniert?
- Was ist kaputt?
- Commit-Link oder Commit-Hash

## Abbruchregel

Wenn eine Kernfunktion kaputt ist:

1. Nicht weiter patchen
2. Letzte stabile Version suchen
3. Unterschied zwischen stabiler und kaputter Version prüfen
4. Erst danach gezielt reparieren
