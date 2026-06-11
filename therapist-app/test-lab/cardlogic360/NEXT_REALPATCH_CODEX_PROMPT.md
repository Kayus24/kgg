# NEXT REALPATCH CODEX PROMPT - CardLogic360

Stand: 2026-06-11

## Ziel

Jetzt keine weiteren Frame-Overrides mehr. Erstelle eine echte v389-Testkopie im Test-Lab und integriere die Kartenlogik sauber in der echten Datei.

## Basisdatei

Quelle:

```text
therapist-app/releases/v389/web/KGG_APP_KOLLEGEN_v389_flow_stability.html
```

Ziel/Testkopie:

```text
therapist-app/test-lab/cardlogic360/v389-cardlogic360-realpatch.html
```

Wichtig:
- Haupt-App NICHT anfassen.
- v389 Release-Datei NICHT veraendern.
- Keine PDF-/QR-/Patienten-App-/Scan-/Parser-Aenderungen.
- Keine DB-Vorschlag-/Textfeld-Aenderungen in diesem Patch.
- Nur Kartenlogik im Bereich "Uebungen im Plan".

## Testergebnisse bisher

### Test 001 - isolierte Gesture-Testdatei
- Kartenbewegung besser.
- CardLogic360-Hold-Ansatz positiv.

### Test 003 - v389 Frame + CardLogic360 Capture-Override
- Drag/Drop ging bei den Karten.
- DB-Vorschlaege poppen/jittern separat.
- Swipe war ohne eigenen Override nur rot, ohne sichtbare Translation.

### Test B - Swipe isoliert
- Links/rechts Swipe hatte wieder sichtbare Animation.
- Drag/Hold war dort erwartbar nicht getestet.

### Test AB - Drag + Swipe im Frame kombiniert
- Beide Bewegungen waren prinzipiell aktiv.
- Swipe ging, loeschte aber nicht, weil Frame-Test keinen echten removeExercise/state update ausfuehrt.
- Drag war ok, aber Karte sprang nach oben und Placeholder war als graue Luecke sichtbar.
- Bewertung: Frame-Override ist am Limit. Jetzt echte v389-Testkopie patchen.

## Patch A - Drag/Hold sauber integrieren

In der echten v389-Datei gibt es bereits:
- `startAnimatedReorderPress(ev)`
- `activateAnimatedReorder(press, initialEv)`
- `fixedContainingBlockOffset(el)`
- `onAnimatedReorderMove(ev)`
- `finishAnimatedReorder(ev)`

Bitte nur `startAnimatedReorderPress(ev)` so umbauen, dass es wieder wie alte v360/v366-Logik startet:

Soll:
- Bei pointerdown am Drag-Handle NICHT sofort bei vertikaler Bewegung aktivieren.
- Stattdessen ca. 120 ms Hold-Timer.
- Wenn vor Aktivierung Bewegung > 10-12 px passiert: abbrechen.
- Wenn Hold erreicht: `activateAnimatedReorder(press, ev)` verwenden.
- `activateAnimatedReorder`, `fixedContainingBlockOffset`, `onAnimatedReorderMove`, `finishAnimatedReorder`, `cleanupAnimatedReorder` aus v389 behalten.
- Touch-Support aus v389 behalten (`startAnimatedReorderTouchPress`, touchmove/touchend/touchcancel).

Nicht machen:
- Kein eigener fixed-position-Code.
- Kein neuer grauer Placeholder.
- Nicht die vorhandene v389-Reorder-Animation ersetzen.
- Kein Layout-Umbau.

Warum:
- Frame-Test sprang nach oben, weil er die v389-Funktion `fixedContainingBlockOffset` nicht sauber benutzt hat.
- Diese vorhandene v389-Logik muss bleiben.

## Patch B - Swipe-Translation sichtbar machen

V389 hat bereits `startPlanCardSwipeDelete(ev)` und setzt:

```js
card.style.setProperty('--kgg-plan-swipe-x', swipe.dx+'px');
card.style.transform = 'translateX(var(--kgg-plan-swipe-x,0px))';
```

Problembeobachtung:
- In echter v389/AB-Test wurde teils nur rote Verfaerbung gesehen, aber keine sichtbare Kartenbewegung.
- Swipe-Test B mit direktem `translate3d(dx,0,0)` zeigte sichtbare Bewegung.

Bitte in der Testkopie pruefen und minimal anpassen:
- Waehrend aktivem Swipe `card.style.transform = 'translate3d('+swipe.dx+'px,0,0)'` oder gleichwertig setzen.
- CSS-Klassen fuer Rot/Armed beibehalten.
- Delete muss weiter ueber vorhandenes `removeExercise(id)` laufen.
- `resetPlanCardSwipe(card)` muss Transform/Opacity/Transition sauber entfernen.

Nicht machen:
- Kein neuer Delete-Mechanismus.
- Kein separater State.
- Kein DB-/Textfeld-/Layout-Fix.

## Build-Identity Hinweis

Die v389-Datei meldet intern noch:

```text
KGG App Kollegen v383 UI Flow Stability
```

Das ist verwirrend. Bitte in der Testkopie nur den `<title>` sichtbar auf Testkopie aendern, z. B.:

```text
KGG App Kollegen v389 CardLogic360 Realpatch Test
```

Die Hauptdatei nicht aendern.

## Erwartetes Testergebnis

In:

```text
therapist-app/test-lab/cardlogic360/v389-cardlogic360-realpatch.html
```

soll gelten:
- Drag-Handle kurz antippen/scrollen: kein sofortiger Drag.
- Drag-Handle bewusst halten: Karte hebt nach ca. 120 ms ab.
- Karte bleibt am Finger und springt nicht nach oben.
- Placeholder sieht wie v389 aus, keine komische graue Luecke.
- Swipe links/rechts bewegt Karte sichtbar horizontal.
- Swipe ueber Threshold loescht Karte weiterhin ueber `removeExercise(id)`.
- DB-Vorschlaege koennen weiter jittern; das ist NICHT Teil dieses Patches.

## Nicht anfassen

- `therapist-app/admin.html`
- `therapist-app/kollegen.html`
- `therapist-app/releases/v389/web/KGG_APP_KOLLEGEN_v389_flow_stability.html`
- `therapist-app/releases/v389/web/KGG_APP_ADMIN_v389_flow_stability.html`
- PDF-Core
- QR-Core
- Patienten-App
- Scan-Core
- Parser
- Textfeld/DB-Vorschlaege
