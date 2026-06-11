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
- Die Kartenbewegung selbst war in der separaten CardLogic360-Testdatei besser. Der neue Restfehler sitzt daher vermutlich im Textfeld-/Live-Render-Flow.

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
- Noch offen. Max soll beide Modi auf dem Android-Geraet testen und Rueckmeldung geben.

## Erfolgskriterium

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
