# G09 – Evidence und Provenance

## 1. Ziel

Jeder behauptete Real-Run und jeder gemessene Wert lässt sich auf unveränderliche, run-gebundene Raw Evidence zurückführen; nicht verfügbare Werte bleiben `NOT_MEASURED`.

## 2. Warum dieses Gate erforderlich ist

Der bisherige Measurement-Ausbau war sinnvoll, wurde aber zeitweise mit Produktfunktion verwechselt. Dieses Gate schützt die Beweisqualität, ohne die Browserimplementierung zu ersetzen.

## 3. Scope und Nicht-Ziele

In Scope: Run-/Session-ID, Base SHA, Plugin-/Runner-Version, Raw-Screenshot-Hashes, Eventfolge, Final State, Evidence Refs und Retention. Nicht in Scope: zweiter Validator, zweite Datenbank oder geschätzte Modellmetriken.

## 4. Abhängigkeiten

G04 und bestehende Measurement-/Raw-Capture-Komponenten.

## 5. Aktueller Stand

- `IMPLEMENTATION_STATUS=MEASUREMENT_AND_CODEX_RAW_CAPTURE_PRESENT`
- `LIVE_EVIDENCE_STATUS=BROWSER_EVIDENCE_MISSING`
- `GATE_STATUS=PARTIAL`
- `EVIDENCE_LEVEL=E2_LOCAL_REAL_RUNTIME`
- `LAST_VERIFIED_BASE_SHA=2b8024e359bd0f65bcc5666b5e190d78a4b4ed6f`
- `LAST_VERIFIED_AT=2026-09-21`

## 6. Bestehende Evidence

- `release-pipeline/kgg_gpt_measurement.py`
- `release-pipeline/kgg_codex_jsonl_host_adapter.py`
- `release-pipeline/kgg_codex_raw_capture.py`
- bestehende Tamper-/Fail-closed-Tests.

## 7. Lücke und Root Cause

Real-Browser-Screenshots und Aktionen werden noch nicht vom Plugin-Run retained und an die vorhandene Evidence-/Field-Provenance-Grenze gebunden.

## 8. Kleinschrittiger Arbeitsplan

1. Minimalfelder pro Browserrun definieren: IDs, SHA, Versionen, Viewport, Timestamps, Eventorder, Screenshot-/Output-Hashes.
2. Raw Evidence vor Normalisierung retainen.
3. normalisierte Events direkt in bestehende `evidence_refs`/`field_provenance` überführen.
4. Content Hash unabhängig nachrechnen.
5. fehlende Coverage als `NOT_MEASURED`, nicht als `0`, führen.
6. Evidence-Retention zeitlich und datenschutzgerecht begrenzen.

## 9. CONTROL_LOOP_GATE

- `GATE_ID=G09_REAL_RUN_PROVENANCE`
- `INPUT=ein G04-Real-Run mit Raw Screenshots und Events`
- `PROCEDURE=Evidence erneut hashen/parsen; IDs/Versionen abgleichen; Werte zu Quellen zurückverfolgen`
- `PASS_CRITERIA=jede positive Behauptung besitzt akzeptierte Raw-Quelle; Manipulation wird erkannt`
- `FAIL_CRITERIA=Self-Report, synthetic URI als Realbeweis, fehlender Hash oder erfundener Nullwert`
- `RETRY_RULE=eine unabhängige Re-Hash/Re-Parse-Prüfung derselben Bytes`
- `FALLBACK=betroffenes Feld NOT_MEASURED; Funktionsergebnis separat berichten`
- `EVIDENCE_OUTPUT=REAL_RUN_PROVENANCE_INDEX_V1`
- `NEXT_ON_PASS=G10`
- `NEXT_ON_FAIL=G04-Fix oder G11`
- `INVALIDATION_TRIGGERS=Evidence-, Event-, Screenshot- oder Measurement-Vertrag ändert sich`

## 10. Tests

- tampered screenshot/event/hash.
- falsche Run-/Surface-/SHA-Bindung.
- fehlende Raw Bytes.
- unabhängiger Golden Hash ohne Producer-Helper.
- kein `OBSERVED_ZERO` ohne vollständige Coverage.

## 11. Safety und Datenschutz

Nur synthetische Inhalte, begrenzte Retention, keine CoT, Tokens oder unnötigen Browserrohlogs.

## 12. Brother-GPT-Eskalation

Bei unklarer Messquelle erhält der Brother Felddefinition, Raw-Evidence-Typ und Contract; er darf keine Ersatzmetrik erfinden.

## 13. Abschlussartefakte

Evidence-Index, Hash-/Retention-Regeln, Browser-Adapter-Mapping und Manipulationstests.

## 14. Beitragsherkunft

`CONTRIBUTION_SOURCE=HUMAN_AND_CODEX`, `REVIEW_STATUS=PENDING`.

