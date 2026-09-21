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

- `IMPLEMENTATION_STATUS=A_ACTION_CANARY_B_TRANSPORT_C_LOCAL_MCP`
- `LIVE_EVIDENCE_STATUS=A_E3_B_E3_PARTIAL_C_E2_LOCAL`
- `GATE_STATUS=PASS`
- `GATE_SCOPE=surface_classification_only`
- `EVIDENCE_LEVEL=E3_REAL_HOST_PLUS_E2_LOCAL_REAL_RUNTIME`
- `LAST_VERIFIED_BASE_SHA=1e6c6e3e28603f28bfbad3b127c688e722c823f5`
- `LAST_VERIFIED_AT=2026-09-21`
- `MATRIX=A_B_C_CAPABILITY_MATRIX_V1`

## 6. Bestehende Evidence

- A führte genau einen read-only `getKggMainCommit`-Canary aus und gab die
  aktuelle Fresh-Main-SHA korrekt zurück (`A-CANARY`, E3).
- B nutzte den bereits bewiesenen ChatGPT-App-/Tunneltransport für genau einen
  read-only `get_current_state(actor=system)`-Canary (`B-G03`, E3). Der Client
  wurde danach beendet; `main_sha=not_bound` bleibt fail-closed.
- C bestand einen lokalen stdio-MCP-Initialize- und Health-Canary
  (`C-STDIO`, E2). Das ist lokale Plugin-Evidence und kein Real-Host-Nachweis.
- Der aktuelle lokale Real-Bridge-Test `python -B -m unittest
  release-pipeline/test_kgg_real_browser_bridge.py -v` lief mit 8/8 Tests
  erfolgreich. Diese Evidence bestätigt G04/G05/G06 lokal, nicht die
  Codex- oder ChatGPT-Host-Grenze.
- `NEXT_SUBSTEP=G08_G09_LOCAL_SAFETY_PROVENANCE_HARDENING`
- Das Read-only Preflight ist in
  [`G07_HOST_BOUNDARY_PREFLIGHT_20260921.json`](G07_HOST_BOUNDARY_PREFLIGHT_20260921.json)
  gebunden: B/C besitzen im aktuellen Transport keinen aktiven
  Real-Browser-Host-Hook; der lokale Opt-in-Code ist vorhanden, aber nicht
  aktiviert. Deshalb wird kein weiterer Runtime-Key oder Tunnel-Canary
  gestartet.
- Die vollständige Zeilenmatrix steht in
  [`A_B_C_CAPABILITY_MATRIX_V1.md`](A_B_C_CAPABILITY_MATRIX_V1.md); die
  Checkpoint-Capsule ist
  [`CP_G07_SURFACE_MATRIX_20260921.json`](CP_G07_SURFACE_MATRIX_20260921.json).

## 7. Lücke und Root Cause

Die drei Hosts haben unterschiedliche Tool-/Installationsgrenzen. Die
read-only Healthpfade sind jetzt getrennt nachgewiesen, aber kein B- oder
C-Plugin-Host liefert in diesem Checkpoint einen vollständigen Screenshot-,
Aktions- und Run-Lifecycle-Nachweis. `main_sha=not_bound` darf nicht als
Fresh-Main-Bindung interpretiert werden.

## 8. Kleinschrittiger Arbeitsplan

1. ✅ Pro Surface Tool Discovery/Health und Transportstatus erfassen.
2. ✅ Capability-Zeilen aus G01 als `PASS`, `PARTIAL`, `SYNTHETIC_ONLY`,
   `NOT_TESTED` oder `NOT_SUPPORTED` klassifizieren.
3. ✅ denselben read-only Health-Canary je erreichbarer Surface ausführen.
4. Screenshot-, Action- und Quick-Flow-Canaries nur mit einem nachgewiesenen
   Host-Hook ausführen; aktuell nicht als B/C-Plugin-Parität behaupten.
5. Surface-spezifische Diagnostik getrennt halten.
6. finalen Betriebsmodus erst nach G05/G06 oder dokumentiertem
   `NOT_OBSERVABLE`/`NOT_SUPPORTED` festlegen.

## 9. CONTROL_LOOP_GATE

- `GATE_ID=G07_SURFACE_CAPABILITIES`
- `INPUT=G01-Matrix, installierte Surface-Versionen, Real-Canaries`
- `PROCEDURE=jede Surface unabhängig prüfen; keine Capability-Vererbung`
- `PASS_CRITERIA=jede Pflichtzeile besitzt pro Surface einen begründeten Status und Evidence; unterstützte Kernpfade laufen real`
- `FAIL_CRITERIA=Local-Codex-PASS wird als ChatGPT-PASS gewertet oder Action-Transport als Browserhost ausgegeben`
- `RETRY_RULE=ein frischer Hostchat bei belegtem UI-Cacheproblem`
- `FALLBACK=NOT_SUPPORTED oder PARTIAL mit explizitem Betriebsmodus`
- `EVIDENCE_OUTPUT=A_B_C_CAPABILITY_MATRIX_V1 + CP_G07_SURFACE_MATRIX_20260921`
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
