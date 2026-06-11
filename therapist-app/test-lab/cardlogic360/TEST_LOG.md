# CardLogic360 Test-Log

Stand: 2026-06-11

## Ziel

Die Kartenbewegung im Bereich "Uebungen im Plan" testen, ohne die Haupt-App oder aktuelle Release-Dateien zu veraendern.

## Ausgangslage

Aktuelle Hauptbasis:
- therapist-app/releases/v389/web/KGG_APP_KOLLEGEN_v389_flow_stability.html

Referenz fuer Kartenverhalten:
- KGG_APP_KOLLEGEN_v360_sync_bundle_qr (1).html
- Hinweis: Datei traegt intern v366 Mobile Floating History Packages.

Problembeobachtung von Max:
- Bewegungsanimationen der aktuellen Uebungskarten sind kaum noch sichtbar.
- Ein frueherer Fix gegen Jitter der aktuellen Uebungsbox hat das Verhalten verschlimmert.
- Drag/Reorder fuehlt sich zu aggressiv oder jitterig an.

## Technischer Verdacht

In v389 startet Drag/Reorder zu schnell bei vertikaler Bewegung am Drag-Handle.
Die alte v360/v366-Referenz wirkte ruhiger, weil Drag erst nach kurzem Halten startet.

## Test 001 - isolierter Gesture-Test

Datei:
- therapist-app/releases/v389/web/KGG_CARDLOGIC360_GESTURE_TEST.html

Direkter Test-Link:
- https://kayus24.github.io/kgg/therapist-app/releases/v389/web/KGG_CARDLOGIC360_GESTURE_TEST.html

Geaendert/isoliert getestet:
- v389-aehnliche Kartenoptik
- Drag startet erst nach kurzem Hold
- Bewegung vor Hold bricht Drag ab
- Links/Rechts-Swipe bleibt testbar

Nicht getestet in dieser Datei:
- komplette v389-App
- PDF
- QR
- Patienten-App
- Scan
- Parser
- echte Plan-State-Synchronisierung

Ergebnis:
- Noch offen: Max muss im Browser/Tablet testen, ob sich Drag/Swipe besser anfuehlt.

Bewertung:
- Wenn Test 001 gut ist, soll daraus eine volle v389-Testkopie im Test-Lab entstehen.
- Wenn Test 001 schlecht ist, muss zuerst nur Gesture-Schwelle/Hold-Zeit angepasst werden.

## Naechster geplanter Test

Test 002:
- volle v389-Testkopie im Ordner therapist-app/test-lab/cardlogic360/
- Dateiname: KGG_APP_KOLLEGEN_v389_cardlogic360_TEST.html
- Nur startAnimatedReorderPress / Karten-Gesture-Logik anpassen
- Haupt-App unveraendert lassen

## Schutzregeln

Nicht anfassen ohne ausdrueckliche Freigabe:
- therapist-app/admin.html
- therapist-app/kollegen.html
- therapist-app/releases/v389/web/KGG_APP_KOLLEGEN_v389_flow_stability.html
- therapist-app/releases/v389/web/KGG_APP_ADMIN_v389_flow_stability.html
- PDF-Core
- QR-Core
- Patienten-App
- Scan-Core
- Parser

## Ergebnisstatus

- Test-Lab-Ordner angelegt: ja
- CardLogic360-Unterordner angelegt: ja
- Test-Log angelegt: ja
- Isolierte Gesture-Testdatei vorhanden: ja, aber aktuell noch im v389 Release-Ordner
- Volle v389-Testkopie im Test-Lab: nein
- Haupt-App veraendert: nein
