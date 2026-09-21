# G07 – Integration der Surfaces A/B/C

## 1. Ziel

Custom GPT (A), normales ChatGPT mit Plugin (B) und Codex+Plugin (C) erhalten je eine ehrlich geprüfte Capability-Matrix und nutzen soweit möglich denselben Plugin-Kern.

## 2. Warum dieses Gate erforderlich ist

Fähigkeiten einer Surface dürfen nicht auf eine andere übertragen werden. Die Migration ist erst glaubwürdig, wenn jeder Host separat geprüft wurde.

## 3. Scope und Nicht-Ziele

Surface A = Custom GPT, B = normales ChatGPT+Plugin, C = Codex+Plugin. Keine Forderung nach künstlicher Vollparität bei technisch fehlenden Hostgrenzen.

## 4. Abhängigkeiten

G03 bis G06. G08/G09 gelten je Surface separat.

## 5. Aktueller Stand

- `IMPLEMENTATION_STATUS=A_ACTIONS_AND_C_LOCAL_MCP_EXIST_B_MISSING`
- `LIVE_EVIDENCE_STATUS=PARTIAL_AND_NOT_COMPARABLE`
- `GATE_STATUS=PARTIAL`
- `EVIDENCE_LEVEL=E2_LOCAL_REAL_RUNTIME`
- `LAST_VERIFIED_BASE_SHA=2b8024e359bd0f65bcc5666b5e190d78a4b4ed6f`
- `LAST_VERIFIED_AT=2026-09-21`

## 6. Bestehende Evidence

- A besitzt GitHub-/Memory-/Coordination-Actions, aber keine Browsersteuerungs-Operations.
- B fand im Live-Test kein installiertes KGG-Plugin.
- C besitzt lokalen Plugin-/MCP-Kandidaten und JSONL-/Raw-Capture-Bausteine; UI-Lab bleibt synthetisch.

## 7. Lücke und Root Cause

Die drei Hosts haben unterschiedliche Tool-/Installationsgrenzen. Eine gemeinsame Capability-Matrix und dieselben realen Kern-Canaries fehlen.

## 8. Kleinschrittiger Arbeitsplan

1. Pro Surface Tool Discovery und Plugin-/Action-Version erfassen.
2. Capability-Zeilen aus G01 als `READY`, `PARTIAL`, `NOT_SUPPORTED`, `NOT_TESTED` klassifizieren.
3. denselben read-only Health-Canary ausführen.
4. denselben Screenshot-Canary ausführen, wenn Host unterstützt.
5. denselben Click-/Quick-Flow-Canary ausführen, wenn Host unterstützt.
6. Surface-spezifische Diagnostik getrennt halten.
7. finalen Betriebsmodus pro Surface festlegen.

## 9. CONTROL_LOOP_GATE

- `GATE_ID=G07_SURFACE_CAPABILITIES`
- `INPUT=G01-Matrix, installierte Surface-Versionen, Real-Canaries`
- `PROCEDURE=jede Surface unabhängig prüfen; keine Capability-Vererbung`
- `PASS_CRITERIA=jede Pflichtzeile besitzt pro Surface finalen Status und Evidence; unterstützte Kernpfade laufen real`
- `FAIL_CRITERIA=Local-Codex-PASS wird als ChatGPT-PASS gewertet oder Action-Transport als Browserhost ausgegeben`
- `RETRY_RULE=ein frischer Hostchat bei belegtem UI-Cacheproblem`
- `FALLBACK=NOT_SUPPORTED oder PARTIAL mit explizitem Betriebsmodus`
- `EVIDENCE_OUTPUT=A_B_C_CAPABILITY_MATRIX_V1`
- `NEXT_ON_PASS=G10 und G12`
- `NEXT_ON_FAIL=betroffenes Vorgate oder G11`
- `INVALIDATION_TRIGGERS=Host-, Plugin-, Action- oder Capability-Version ändert sich`

## 10. Tests

- Tool Discovery A/B/C.
- read-only Canary A/B/C.
- Screenshot/Action/Quick-Flow je unterstützter Surface.
- Negativ: nicht vorhandenes Tool darf nicht halluziniert werden.

## 11. Safety und Datenschutz

Nur synthetische Appdaten und identische minimale Rechte. Host-spezifische zusätzliche Rechte werden separat dokumentiert.

## 12. Brother-GPT-Eskalation

Bei unerwarteter Hostabweichung erhält der Brother nur die betroffene Matrixzeile, Tool-Discovery und Fehlerevidence.

## 13. Abschlussartefakte

Capability-Matrix, Surface-Canaries, Versionen, Grenzen und finaler Nutzungsentscheid.

## 14. Beitragsherkunft

`CONTRIBUTION_SOURCE=HUMAN_AND_CODEX`, `REVIEW_STATUS=PENDING`.
