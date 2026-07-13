# Patienten-QR Kamera-Testbericht (`patient-scan-camera-v3-live-lossless`)

- Zeitpunkt: 13.07.2026
- Basis: `e96b259` (`origin/main`)
- Produktionsziel: `start-scan-v7-live-lossless-update`, Service Worker `kgg-handyplan-v51-live-lossless-update`
- Umgebung: Windows 10.0.22631, Node v25.8.0, Playwright-Chromium
- Automatisiert: 43 bestanden, 15 dokumentierte Erkennungsgrenzen, 0 Fehler
- Android: ADB nicht verfügbar; echter Kamera-Nachtest bleibt erforderlich

## Ergebnis des Fixes

Die Patienten-PWA öffnet jetzt einen Live-Scanner und prüft fortlaufend Kameraframes. Sie löst automatisch aus, sobald BarcodeDetector oder die lokal gepinnte jsQR-Version einen gültigen KGGH2-/Plan-Link liefert. Die Frames werden nur im Arbeitsspeicher verarbeitet und weder gespeichert noch zu einem Bild zusammengerechnet. Bei fehlender oder verweigerter Live-Kamera bleiben Fotoaufnahme/-auswahl und manuelle Linkeingabe verfügbar.

Der bisherige Decoderfehler ist geschlossen: Wirft `BarcodeDetector` eine Exception, wird jsQR sowohl beim Foto als auch im Live-Stream weiter ausgeführt. Der Fotomodus prüft zusätzlich Vollbild, zwei Zentralausschnitte und Kontrastvarianten. Dadurch werden mehrere zuvor gescheiterte kleine oder vertikal verzerrte Bilder erkannt.

## Automatisierte Kameraergebnisse

- Acht echte Live-Codepfade mit test-only Canvas-`MediaStream` bestanden.
- Abstand, Unschärfe, Bewegung, Dunkelheit, Überbelichtung, Perspektive und Kontrast/Rauschen wurden jeweils beim dritten verbesserten Frame automatisch erkannt.
- `BarcodeDetector`-Exception → jsQR wurde im Live-Stream beim ersten klaren Frame erkannt.
- Kameratracks wurden nach Erfolg und `pagehide` beendet; das Overlay wurde geschlossen.
- Verweigerte Kameraberechtigung zeigt den Foto-/Link-/Wiederholen-Fallback und verändert keinen Patientenzustand.
- Erkennung und Parserübergabe stimmen in allen Erfolgsfällen bytegenau mit dem KGGH2-/URL-Payload überein.

## Perspektiv- und Fotobefunde

| Bedingung | Ergebnis nach Mehrfachdekodierung |
|---|---|
| horizontale/vertikale Neigung ±10° | erkannt |
| kombiniert ±10° | erkannt |
| horizontal −20°/−30° | erkannt |
| vertikal ±20° | erkannt |
| vertikal +30° | erkannt |
| horizontal +20°, QR 25/55/70 % | alle erkannt |
| Trapez 10 % und asymmetrische Ecke 8 % | nicht erkannt |
| horizontal +20°/+30° bei mittlerer Größe | nicht erkannt |
| horizontal ±40° | nicht erkannt |
| horizontal +30° bei 1080p und QR 40/70 % | nicht erkannt |
| stärkere Trapez-/Eckverzerrungen | nicht erkannt |
| extrem klein, dunkel und verrauscht | nicht erkannt |

Alle 31 Einzelbilder bleiben unter `patient-scan-fixtures/perspective/` reproduzierbar. Nicht erkannte Bilder sind Messgrenzen und verändern den Patientenzustand nicht.

## Verlustfreies Planupdate

Bestanden:

- Trainingswerte, erledigte Tage und aktiver Tag bleiben erhalten.
- Bestehende Übungsbilder, Video-URL, Video-Label und Schmerzmodus bleiben erhalten, wenn der neue Plan dort keinen Wert liefert.
- Unbekannte zusätzliche Übungsfelder und unbekannte Top-Level-Felder bleiben erhalten.
- Ein anderer Multi-Plan-Slot und zusätzliche Multi-Plan-Metadaten bleiben unverändert.
- Explizite neue Medien-, Video-, Schmerzmodus- und Zusatzfeldwerte ersetzen die alten Werte.
- Im Update nicht enthaltene bestehende Übungen behalten Reihenfolge und Medien; neue Übungen werden angehängt.

## Physischer Android-Chrome-Test

Der ursprüngliche reale Kamerafehler wurde vom Nutzer bestätigt. Nach Bereitstellung des Fixes müssen Chrome und die installierte PWA mit der echten Rückkamera erneut geprüft werden:

1. Scanner-Version `start-scan-v7-live-lossless-update` kontrollieren und Kameraberechtigung erteilen.
2. QR mit 15/30/60 cm Abstand, frontal und schräg sowie bei normalem, schwachem und starkem Licht testen.
3. Automatisches Schließen, Planupdate und Kamerastopp prüfen.
4. Foto-Fallback nach verweigerter Berechtigung testen.
5. Vorhandene Werte, Tage, Bilder, Videos, Zusatzfelder und zweiten Plan-Slot vergleichen.
