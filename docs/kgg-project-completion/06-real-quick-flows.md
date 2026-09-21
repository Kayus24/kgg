# G06 – Reale Quick Flows

## 1. Ziel

Bekannte KGG-Navigationsfolgen laufen als versionierte, kontrollierte Makros auf der echten Browser-Brücke und wechseln bei Drift automatisch in die visuelle Rückfallebene.

## 2. Warum dieses Gate erforderlich ist

Stabile Abläufe sollen nicht bei jedem Schritt einen teuren Screenshot brauchen. Quick Flows liefern Effizienz, dürfen aber bei UI-Drift nicht blind klicken.

## 3. Scope und Nicht-Ziele

Zunächst drei risikoarme Flows aus dem ursprünglichen UI-Lab-Ziel. Keine Produktionswrites, kein Patientendatensatz und keine unbegrenzten Makros.

## 4. Abhängigkeiten

G04; für den visuellen Fallback G05; Safety aus G08.

## 5. Aktueller Stand

- `IMPLEMENTATION_STATUS=SYNTHETIC_FLOW_CONTRACT_PLUS_ONE_REAL_BRIDGE_PATH`
- `LIVE_EVIDENCE_STATUS=THREE_CANONICAL_FLOWS_LOCAL_REAL; VISUAL_DRIFT_FALLBACK_PENDING`
- `GATE_STATUS=PARTIAL`
- `EVIDENCE_LEVEL=E2_LOCAL_REAL_RUNTIME`
- `LAST_VERIFIED_BASE_SHA=1e6c6e3e28603f28bfbad3b127c688e722c823f5`
- `LAST_VERIFIED_AT=2026-09-21T13:42:46+02:00`

## 6. Bestehende Evidence

UI-Lab-Goal und MCP-Kandidat enthalten Quick-Flow-Begriffe und synthetische Schritte. Die drei kanonischen Flows laufen jetzt jeweils lokal real über dieselbe Brücke; der kontrollierte visuelle Drift-Fallback ist noch nicht gebunden.

## 7. Lücke und Root Cause

Die drei Flow-Zertifikate sind an den echten Runner gebunden. Es fehlen noch versionierte Real-Run-Fingerprints und der G05-Fallback bei UI-Drift.

## 8. Kleinschrittiger Arbeitsplan

1. Drei erste Flows mit Startzustand, Schritten, Endzustand und Version definieren.
2. Semantische Locator bevorzugen; Koordinaten nur mit gebundenem Viewport nutzen.
3. Vor jedem Schritt Vorbedingung prüfen.
4. nach jedem Schritt minimale Zustandsassertion ausführen.
5. bei unerwartetem Zustand stoppen und G05-Screenshot-Fallback verwenden.
6. Step Evidence, Laufzeit, Fehlerklasse und finalen Zustand ausgeben.
7. Flow-Version an UI-/Source-Fingerprint binden.

## 9. CONTROL_LOOP_GATE

- `GATE_ID=G06_REAL_QUICK_FLOWS`
- `INPUT=echte Browser-Session, versionierter Flow, definierter Startzustand`
- `PROCEDURE=drei Flows jeweils aus definiertem Startzustand ausführen; Schritte und Endzustand prüfen`
- `PASS_CRITERIA=alle drei Flows real erfolgreich; Driftfall stoppt und wechselt kontrolliert zum visuellen Loop`
- `FAIL_CRITERIA=synthetische Events, Blindklick, übersprungene Assertion oder Erfolg trotz falschem Endzustand`
- `RETRY_RULE=kein identischer Retry bei deterministischem UI-Drift`
- `FALLBACK=G05 mit frischem Screenshot; Flow danach als stale markieren`
- `EVIDENCE_OUTPUT=QUICK_FLOW_RUNS_V1`
- `NEXT_ON_PASS=G07 und G10`
- `NEXT_ON_FAIL=Flow fixen oder G11 bei Architekturproblem`
- `INVALIDATION_TRIGGERS=UI-Fingerprint, Locator, Viewportprofil oder Flow-Version ändert sich`

## 10. Tests

- Happy Path pro Flow.
- veränderter Viewport.
- fehlender/verschobener Button.
- Overlay/Modal.
- stale Flow-Fingerprint.
- unveränderter Replay pro Flow.
- `python -m unittest release-pipeline/test_kgg_real_browser_bridge.py -v`: drei zertifizierte Flows real PASS; der Test prüft weiterhin nur den Realpfad, nicht den visuellen Fallback.

## 11. Safety und Datenschutz

Flows sind allowlistet, schrittbegrenzt und auf synthetische Testdaten beschränkt. Destruktive Schritte sind standardmäßig verboten.

## 12. Brother-GPT-Eskalation

Nur wenn ein Flow weder semantisch noch visuell robust modellierbar ist. Brother soll Vereinfachung oder Aufteilung vorschlagen.

## 13. Abschlussartefakte

Drei Flow-Spezifikationen, Runnerbindung, Step-Evidence, Drift-Fallback und Tests.

## 14. Beitragsherkunft

`CONTRIBUTION_SOURCE=HUMAN_AND_CODEX`, `REVIEW_STATUS=PARTIAL`, `NOTE=Three canonical flows run locally through G04; G05 visual drift fallback remains.`
