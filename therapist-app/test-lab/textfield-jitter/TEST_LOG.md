# Textfield Jitter Test-Log

Stand: 2026-06-11

## Anlass

Max meldet nach positivem CardLogic360-Gesture-Test weiterhin starken Jitter beim Bedienen des Uebungs-Textfeldes.

Video:
- 54168.mp4

## Beobachtung aus Videoanalyse

- Jitter tritt beim fokussierten Textfeld mit geoeffneter Android-Tastatur auf.
- Beim Tippen veraendern sich gleichzeitig:
  - Textfeld-Inhalt
  - Live-Vorschau/Live-Draft im aktuellen Plan
  - DB-Vorschlag/Top-Treffer unter dem Textfeld
  - ggf. Keyboard-/Sticky-/Scroll-Korrektur
- Die Kartenbewegung selbst war in der separaten CardLogic360-Testdatei besser. Der neue Restfehler sitzt daher vermutlich im Textfeld-/Full-App-Render-/Keyboard-Flow.

## Hypothesen

H1: AutoResize des Textfeldes
- Textfeldhoehe wird bei jedem Input neu berechnet.
- Das verschiebt Elemente darunter und rechts daneben.

H2: Live-Draft-Karte im Plan
- Beim Tippen wird eine gelbe/Live-Karte im aktuellen Plan neu erzeugt/aktualisiert.
- Dadurch springt die Planliste oder der aktuelle Planblock.

H3: DB-Vorschlag/BankPreview
- Top-Treffer/Bank-Vorschlag erscheint und verschwindet bzw. aendert Hoehe bei jedem Buchstaben.
- Der Bereich unter dem Textfeld hat keinen stabil reservierten Platz.

H4: Keyboard-Sticky-Logik
- phoneTextFocus/Keyboard-Inset versucht das Textfeld sichtbar zu halten.
- Gleichzeitig triggert Render/Resize Layoutaenderungen, was Scroll-Korrekturen erzeugt.

H5: Zu grober render()
- Bei jedem Buchstaben wird zu viel neu gerendert: Plan, Bank, Suggestion, Keyboard-Inset.
- Dadurch entstehen sichtbare Reflows.

H6: Full-App-Kontext statt isolierter Ursache
- Isolierter Mock mit AutoResize, LiveDraft und Preview jittert nicht.
- Der echte Fehler entsteht wahrscheinlich erst durch Zusammenspiel mit echter v389-Struktur: Sticky-Actions, Side-Sheets, Plan-Store-Sync, Scroll-Container, VisualViewport/Keyboard oder komplette render()-Kette.

## Test 001 - isolierter Textfield-Jitter-Test

Testdatei:
- therapist-app/test-lab/textfield-jitter/KGG_TEXTFIELD_JITTER_TEST.html

Direkter Link:
- https://kayus24.github.io/kgg/therapist-app/test-lab/textfield-jitter/KGG_TEXTFIELD_JITTER_TEST.html

Testvarianten:
- Modus A: v389-aehnlich aggressiv
  - AutoResize aktiv
  - LiveDraft aktiv
  - DB-Preview sofort
  - Render sofort bei jedem Input
- Modus B: stabilisiert
  - Textfeldhoehe waehrend Fokus fixiert
  - Render gedrosselt/debounced
  - Preview-Platz reserviert
  - Planliste nicht komplett neu aufbauen bei jedem Zeichen

Ergebnis:
- Rueckmeldung Max: Keines jittert.
- Bewertung: Test 001 reproduziert den Fehler nicht.
- Schlussfolgerung: AutoResize + LiveDraft + Preview allein reichen nicht aus. Der Fehler muss im echten v389-App-Kontext gesucht werden.

## Test 002 - v389 Frame-Instrumentierung mit Mess-Overlay + JSON Export

Testdatei:
- therapist-app/test-lab/textfield-jitter/KGG_APP_KOLLEGEN_v389_textfield_jitter_INSTRUMENTED.html

Direkter Link:
- https://kayus24.github.io/kgg/therapist-app/test-lab/textfield-jitter/KGG_APP_KOLLEGEN_v389_textfield_jitter_INSTRUMENTED.html

Wichtig:
- Diese Datei veraendert die Haupt-App nicht.
- Sie laedt v389 in einem same-origin Test-Frame.
- Sie misst echte v389-DOM-Positionen und visualViewport-Werte.
- Sie gibt einen kopierbaren JSON-Diagnoseblock aus.
- Es ist bewusst noch kein Fix enthalten.

Messpunkte im Overlay und JSON:
- Textfeld top/height
- Planliste top/height
- Aktuelle Planbox top/height
- Sticky-/Bottom-Actions top
- Vorschlagsbereich top/height
- visualViewport height/offsetTop/pageTop
- input-event-Zaehler
- requestAnimationFrame-Zaehler als Render-/Layout-Aktivitaetsindikator
- letzter Layout-Sprung in px
- maximaler Layout-Sprung in px
- Samples und Jump-Historie
- User-Agent und Test-URL
- verdict: no_large_jump_yet oder layout_jump_detected

Bedienung:
- Testseite oeffnen.
- In der v389-App tippen, bis Jitter sichtbar ist.
- Button JSON anzeigen pruefen.
- Button JSON kopieren nutzen und Ergebnis an Chat/Codex geben.

Ergebnis:
- Noch offen. Max muss im echten Android-Kontext testen und den JSON-Block liefern.

Erfolgskriterium:
- Jitter muss in v389 sichtbar oder im JSON messbar werden.
- Wenn maxJumpPx deutlich steigt, naechsten Fix an genau diesem Bereich planen.
- Wenn kein Jitter sichtbar/messbar wird, muss eine echte Kopie statt Frame gebaut werden.

## Erfolgskriterium fuer spaeteren Fix

Gut:
- Beim Tippen bleibt Textfeld/Planbereich ruhig.
- Keine sichtbaren vertikalen Spruenge.
- Vorschlag darf sich aendern, aber nicht die komplette Box bewegen.

Schlecht:
- Aktueller Plan springt weiter.
- Textfeld rutscht bei jedem Buchstaben.
- Untere Buttons/Fertig wandern sichtbar.

## Nicht anfassen

- Haupt-App
- v389 Release-Dateien
- PDF
- QR
- Patienten-App
- Scan-Core
- Parser
