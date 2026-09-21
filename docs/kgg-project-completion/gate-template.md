# GXX – Gate-Titel

## 1. Ziel

Ein prüfbarer Satz, der den erforderlichen Endzustand beschreibt.

## 2. Warum dieses Gate erforderlich ist

Welche echte Produktfähigkeit oder welches Risiko dieses Gate abdeckt.

## 3. Scope und Nicht-Ziele

Erlaubte Komponenten, ausdrücklich nicht enthaltene Erweiterungen und unveränderliche Grenzen.

## 4. Abhängigkeiten

- Vorgelagerte Gates.
- Benötigte Host-/Tool-/Testfähigkeiten.
- Benötigte Consequence Gates.

## 5. Aktueller Stand

- `IMPLEMENTATION_STATUS=`
- `LIVE_EVIDENCE_STATUS=`
- `GATE_STATUS=PASS|PARTIAL|FAIL|BLOCKED|UNKNOWN|NOT_APPLICABLE`
- `EVIDENCE_LEVEL=E0|E1|E2|E3|E4`
- `LAST_VERIFIED_BASE_SHA=`
- `LAST_VERIFIED_AT=`

## 6. Bestehende Evidence

Pfade, Hashes, Runs, Screenshots oder Transkripte. Historische Evidence als historisch markieren.

## 7. Lücke und Root Cause

Nicht nur Symptom, sondern kleinste belegte Ursache. `UNKNOWN` bleibt `UNKNOWN`.

## 8. Kleinschrittiger Arbeitsplan

1. Ein einzelner beobachtbarer Schritt.
2. Nächster Schritt nur nach bestandener Kontrolle.
3. Jeder Write besitzt zugehörigen RED- und Akzeptanztest.

## 9. CONTROL_LOOP_GATE

- `GATE_ID=`
- `INPUT=`
- `PROCEDURE=`
- `PASS_CRITERIA=`
- `FAIL_CRITERIA=`
- `RETRY_RULE=`
- `FALLBACK=`
- `EVIDENCE_OUTPUT=`
- `NEXT_ON_PASS=`
- `NEXT_ON_FAIL=`
- `INVALIDATION_TRIGGERS=`

## 10. Tests

- Targeted.
- Negative/Fault.
- relevante Regression.
- Real-Host- oder Black-Box-Nachweis.
- unveränderter Replay, falls gefordert.

## 11. Safety und Datenschutz

Nur synthetische Daten, minimale Rechte, erlaubte Domains/Pfade, Sanitization und Stop-Regeln.

## 12. Brother-GPT-Eskalation

Exakte Bedingungen, Entscheidungsfrage und benötigtes Evidence-Paket. Kein rekursiver Brother-Loop.

## 13. Abschlussartefakte

Code, Dokumentation, Tests, Evidence, Statusregister und finaler Checkpoint.

## 14. Beitragsherkunft

Für extern erarbeitete Vorschläge:

```text
CONTRIBUTION_SOURCE=HUMAN|CODEX|BROTHER_GPT|CUSTOM_GPT
CONTRIBUTION_DATE=<ISO-8601>
HANDOFF_ID=<id-or-none>
REVIEW_STATUS=ACCEPTED|REVISED|REJECTED
INCORPORATED_BY=<actor>
SOURCE_SUMMARY=<bounded summary>
DECISION_SUMMARY=<bounded summary>
```
