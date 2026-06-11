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
- therapist-app/test-lab/cardlogic360/test-003.html

Direkter Test-Link:
- https://kayus24.github.io/kgg/therapist-app/test-lab/cardlogic360/test-003.html?v=003a

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

Ergebnis vom 2026-06-11:
- JSON: pointerDown 4, blockedV389 4, holdActivated 4, finish 4, cancelBeforeHold 0.
- verdict: override_active.
- Max: Drag-Drop ging bei den Karten.
- Max: Es gab lustigen Jitter um die Vorschlaege der Uebungsdatenbank; Vorschlaege poppen auf/zu.
- Max: Swipe links/rechts hatte keine Karten-Translation/Animation, nur rote Verfaerbung.
- Scroll maxJump sehr hoch, aber Test laeuft im Frame/Overlay und misst auch normale Spruenge durch Scrollen.

Bewertung:
- CardLogic360-Hold-Ansatz ist in echter v389-Umgebung positiv fuer Drag/Drop.
- Das Drag-Problem kann als eigener Mini-Patch vorbereitet werden.
- Swipe-Animation ist ein getrenntes Problem und darf nicht mit Drag-Hold-Patch vermischt werden.
- DB-Vorschlag-Jitter ist ebenfalls ein getrenntes UI-Flow-Problem: Vorschlagsbereich braucht vermutlich reservierte Hoehe/keine display-auf-zu-Spruenge.

## Test B - Swipe-Animation

Datei:
- therapist-app/test-lab/cardlogic360/test-b-swipe.html

Direkter Test-Link:
- https://kayus24.github.io/kgg/therapist-app/test-lab/cardlogic360/test-b-swipe.html?v=swipeb1

Ziel:
- Swipe links/rechts isoliert testen.
- Pruefen, ob eine direkte translate3d-Swipe-Bewegung im echten v389-Frame sichtbar ist.
- Nicht Drag/Hold testen.

Ergebnis vom 2026-06-11:
- JSON mode: override.
- pointerDown 6, overrideActive 6, move 85, armed 17, finish 1, cancel 5.
- verdict: override_translation_applied.
- Max: Rechts/links Swipe hatte wieder Animation.
- Max: Drag-Drop hoch/runter ging in diesem Test nicht.
- Max: leichter Jitter in der ganzen aktuellen Uebungsbox.

Bewertung:
- Swipe-Translation ist grundsaetzlich moeglich. CSS/Container blockieren transform nicht generell.
- Dass Drag-Drop in Test B nicht ging, ist erwartbar: Test B ist nur Swipe-Test und ueberschreibt keine Drag/Hold-Logik.
- Leichter Jitter in der aktuellen Uebungsbox bleibt als separates Full-Integration-Problem.
- Naechster sinnvoller kombinierter Test: echte v389-Testkopie mit zwei klar getrennten Fixes: CardLogic360 Drag-Hold + direkte Swipe-Translation, aber ohne DB-Vorschlaege anzufassen.

## Test AB - Drag + Swipe kombiniert im Frame

Datei:
- therapist-app/test-lab/cardlogic360/test-ab-combined.html

Direkter Test-Link:
- https://kayus24.github.io/kgg/therapist-app/test-lab/cardlogic360/test-ab-combined.html?v=ab1

Ergebnis vom 2026-06-11:
- JSON kind: kgg-cardlogic360-ab-combined.
- dragPointer 7, dragHold 4, dragCancel 5, dragFinish 2.
- swipePointer 11, swipeMove 239, swipeArmed 103, swipeFinish 10, swipeCancel 1.
- verdict: drag_and_swipe_active.
- Max: Links/rechts Swipe ging, loeschte aber nicht.
- Max: Drag-Drop war ok, aber die Karte sprang direkt nach oben statt am Finger zu bleiben.
- Max: graue Luecke/Placeholder war komisch sichtbar.

Bewertung:
- Frame-Override beweist nur, dass beide Bewegungen prinzipiell moeglich sind.
- Swipe loescht nicht, weil der Test-Override bewusst kein removeExercise/state update macht.
- Graue Luecke ist der Test-Placeholder; in echter Integration muss sie wie v389 reorder-placeholder aussehen und korrekt animieren.
- Das Hochspringen zeigt: Der Frame-Override berechnet fixed positioning zu grob. Die echte v389-Logik hat bereits fixedContainingBlockOffset; diese muss beibehalten werden.
- Naechster Schritt darf kein weiterer Frame-Override sein. Es braucht eine echte v389-Testkopie, die die vorhandenen v389-Funktionen sauber patcht.

## Naechste sinnvolle Tickets

Ticket A - Mini-Patch Drag/Hold:
- In v389 startAnimatedReorderPress so aendern, dass Drag erst nach 100-140 ms Hold startet.
- Bewegung vor Hold > 10-12 px bricht Drag ab.
- Touch-Support behalten.
- Wichtig: activateAnimatedReorder und fixedContainingBlockOffset aus v389 behalten, damit Karte nicht nach oben springt.
- Kein Swipe, keine Vorschlaege, kein Layout anfassen.

Ticket B - Mini-Patch Swipe-Translation:
- Swipe muss sichtbare translate3d/translateX-Bewegung bekommen.
- Rote Verfaerbung allein reicht nicht.
- Delete/state remove muss in echter Integration ueber vorhandenes removeExercise laufen.
- Separat von Drag/Hold testen oder in Testkopie klar getrennt implementieren.

Ticket C - separater DB-Vorschlag-Jitter-Test:
- Vorschlagsbereich unter Textfeld/Bank stabilisieren.
- Vermutlich Hoehe reservieren und nur Inhalt/Opacity wechseln.
- Nicht zusammen mit Kartenlogik patchen.

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
- Swipe-Test B vorhanden: ja
- Kombinierter Frame-Test AB vorhanden: ja
- Haupt-App veraendert: nein
- Naechster Mini-Patch-Kandidat: echte v389-Testkopie statt Frame-Override
