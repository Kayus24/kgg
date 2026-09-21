# G05 – Visueller Screenshot-Aktions-Regelkreis

## 1. Ziel

Ein Agent kann aus einem echten Screenshot den nächsten sicheren UI-Schritt ableiten, ihn ausführen lassen und anhand eines zweiten Screenshots plus Zustandsbeobachtung verifizieren.

## 2. Warum dieses Gate erforderlich ist

Koordinatensteuerung ohne Rückkopplung ist blind und instabil. Der Loop macht aus einzelnen Browsertools eine echte agentische UI-Testfähigkeit.

## 3. Scope und Nicht-Ziele

In Scope: synthetische KGG-Testdaten, begrenzte App-Workflows und sichtbare Bedienung. Nicht in Scope: Chain-of-Thought-Speicherung, CAPTCHA-Umgehung oder unbegrenzte autonome Webnavigation.

## 4. Abhängigkeiten

G04, G08 und G09.

## 5. Aktueller Stand

- `IMPLEMENTATION_STATUS=DESCRIBED_NOT_CONNECTED`
- `LIVE_EVIDENCE_STATUS=NONE`
- `GATE_STATUS=BLOCKED`
- `EVIDENCE_LEVEL=E1_SYNTHETIC`
- `LAST_VERIFIED_BASE_SHA=2b8024e359bd0f65bcc5666b5e190d78a4b4ed6f`
- `LAST_VERIFIED_AT=2026-09-21`

## 6. Bestehende Evidence

Playwright-Smokes können klicken und Screenshots erzeugen. Es fehlt der MCP/ChatGPT-Regelkreis, der Screenshot, Entscheidung, echte Aktion und Nachprüfung verbindet.

## 7. Lücke und Root Cause

G04 fehlt. Zusätzlich fehlt ein expliziter „observe → decide → act → verify → recover“-Vertrag.

## 8. Kleinschrittiger Arbeitsplan

1. Screenshot-Metadaten und Viewport-Koordinatensystem festlegen.
2. Aktionsrequest mit Ziel, Koordinaten, Konfidenz, erwarteter Änderung und Safety-Klasse definieren.
3. Vorher-Screenshot und Zustandsfingerprint speichern.
4. genau eine Aktion ausführen.
5. Nachher-Screenshot und Zustand erfassen.
6. erwartete Änderung unabhängig prüfen.
7. bei Nichtänderung einmal semantisches Ziel oder frischen Screenshot nutzen; nicht blind wiederklicken.
8. Abschluss/Fehler mit Evidence ausgeben.

## 9. CONTROL_LOOP_GATE

- `GATE_ID=G05_VISUAL_LOOP`
- `INPUT=echte Session, Screenshot A, bounded Aufgabe`
- `PROCEDURE=Ziel bestimmen; eine Aktion; Screenshot B; Zustandsassertion; gegebenenfalls ein kontrollierter Fallback`
- `PASS_CRITERIA=beabsichtigte sichtbare Zustandsänderung mit gebundener Vorher-/Nachher-Evidence`
- `FAIL_CRITERIA=keine Änderung, falsches Ziel, wiederholter Blindklick oder ausschließlich modellgemeldeter Erfolg`
- `RETRY_RULE=maximal ein neuer Observe-Schritt bei plausibel veraltetem Screenshot`
- `FALLBACK=Quick Flow falls passend; sonst fail-closed`
- `EVIDENCE_OUTPUT=VISUAL_LOOP_RUN_V1`
- `NEXT_ON_PASS=G06 und G07`
- `NEXT_ON_FAIL=Root Cause oder G11`
- `INVALIDATION_TRIGGERS=Viewport-, Screenshot-, Aktions- oder Zustandsvertrag ändert sich`

## 10. Tests

- Zielbutton an variierenden Positionen.
- DPI/Viewport-Skalierung.
- Overlay, Scroll, verzögertes Rendering und nicht anklickbares Ziel.
- Negativ: Screenshot veraltet, Aktion außerhalb Bounds, Zustand unverändert.
- zwei unveränderte reale Durchläufe.

## 11. Safety und Datenschutz

Keine echten Patientenscreenshots. Destruktive oder externe Aktionen benötigen eigene Toolklassifikation und gegebenenfalls Human Gate.

## 12. Brother-GPT-Eskalation

Bei stabil wiederholtem Wahrnehmungs-/Aktionsfehler erhält der Brother anonymisierte Screenshots, Metadaten und Events; nie Secrets oder Patientendaten.

## 13. Abschlussartefakte

Loop-Vertrag, Referenzimplementierung, Evidence-Beispiel und robuste Black-Box-Tests.

## 14. Beitragsherkunft

`CONTRIBUTION_SOURCE=HUMAN_AND_CODEX`, `REVIEW_STATUS=PENDING`.

