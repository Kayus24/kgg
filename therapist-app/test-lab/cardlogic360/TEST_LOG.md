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
- Rueckmeldung Max: Kartenbewegung besser als in aktueller v389.

Bewertung:
- CardLogic360-Hold-Ansatz ist positiv.
- Muss in echter v389-Umgebung getestet werden.

## Test 002 - echte v389 ohne CardLogic360 im Textfield-Jitter-Test

Datei:
- therapist-app/test-lab/textfield-jitter/KGG_APP_KOLLEGEN_v389_textfield_jitter_INSTRUMENTED.html

Ergebnis aus JSON:
- Kein grosser Textfeld-Jump: maxJumpPx 0.
- Leichte Scroll/PageTop-Spruenge.
- Kartenbewegung wieder schlecht, weil echte v389-Kartenlogik aktiv war.

Bewertung:
- Textfeld ist nicht Hauptproblem.
- Die Karten-Gesture-Logik bleibt der zentrale Kandidat.

## Test 003 - v389 Frame + CardLogic360 Capture-Override

Datei:
- therapist-app/test-lab/cardlogic360/KGG_V389_CARDLOGIC360_OVERRIDE_TEST.html

Direkter Test-Link:
- https://kayus24.github.io/kgg/therapist-app/test-lab/cardlogic360/KGG_V389_CARDLOGIC360_OVERRIDE_TEST.html

Ziel:
- Echte v389-App im Frame laden.
- Haupt-App nicht veraendern.
- Drag-Handle-Events im Capture-Modus abfangen.
- v389-aggressive Drag-Logik blockieren.
- Testweise CardLogic360-Hold-Verhalten darueberlegen.

Soll-Verhalten:
- Kurzes Scrollen/Antippen am Drag-Handle startet keinen Drag.
- Karte hebt erst nach ca. 120 ms Halten ab.
- Bewegung vor Hold > ca. 12 px bricht Drag ab.
- Overlay zeigt pointerDown, blockedV389, holdActivated, cancelBeforeHold, finish.
- JSON kann kopiert werden.

Wichtig:
- Der Override ist nur visuell/diagnostisch.
- Er ist noch kein echter Plan-State-Reorder-Patch.
- Erst wenn sich das Verhalten gut anfuehlt, soll Codex die Logik sauber in v389 implementieren.

Ergebnis:
- Noch offen. Max soll Test 003 auf Android testen und JSON/Beobachtung melden.

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
- Isolierte Gesture-Testdatei vorhanden: ja
- v389 CardLogic360 Override-Test vorhanden: ja
- Volle v389-Testkopie im Test-Lab: nein
- Haupt-App veraendert: nein
