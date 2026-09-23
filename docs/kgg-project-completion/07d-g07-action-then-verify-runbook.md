# G07d – ACTION_THEN_VERIFY für Surface B

## Zweck und Grenze

Dieses Runbook bereitet den einzigen funktionalen Folgeschritt nach der
query-gebundenen V3-Observation vor. Es ist **nicht aktiviert** und erzeugt
kein Run-, Key-, Installations- oder Kostenbudget. Die maschinenlesbare Vorlage
ist [`G07_ACTION_THEN_VERIFY_20260923.json`](G07_ACTION_THEN_VERIFY_20260923.json).

Der Test soll genau einen kausalen UI-Schritt beweisen:

```text
fresh meta.url + plan query
→ start_ui_session
→ observe_visual_state
→ eine sichere reversible Aktion
→ execute_visual_action mit interner Verify-Observation
```

Eine zusätzliche identische Observation oder ein Blind-Reclick ist verboten.

## CONTROL_LOOP_GATE

`GATE_ID=G05_ACTION_THEN_VERIFY_B`

### Preflight

- Fresh Main und `meta.url` erneut read-only binden.
- Surface B und das bestehende Plugin-Toolset bestätigen.
- Keine neue Runtime-Key-, Tunnel-, Package- oder Browser-Installation.
- Einen aktuellen synthetischen, reversiblen UI-Zielpunkt bestimmen.
- Save/Delete/Submit/QR-/Patienten-/Produktionsziele verwerfen.

### Ausführung

1. Session mit exakt `session/v1` einmal starten.
2. Auf derselben Session exakt einmal `observe_visual_state` aufrufen.
3. Aus der aktuellen Observation einen sicheren Zielpunkt und erwarteten
   Nachzustand ableiten.
4. Exakt einmal `execute_visual_action` aufrufen. Die vom Server erzeugte
   zweite Observation ist die einzige Verify-Evidence.
5. Nur bei gebundener Vorher-/Nachher-Evidence und tatsächlicher sichtbarer
   Zustandsänderung `ACTION_THEN_VERIFY=PASS` setzen.

### Fail-closed

Bei `UNKNOWN`, fehlenden Bounds, stale Observation, Timeout, Permission,
fehlendem Kanal, unverändertem Zustand oder unvollständiger Evidence:

```text
ACTION_THEN_VERIFY=NOT_OBSERVABLE|FAIL
NO_RETRY=true
```

Der externe Lauf darf erst nach einem separat bestätigten Run-/Kosten-Gate
stattfinden. Ohne dieses Gate bleibt der Status
`PREPARED_NOT_EXECUTED`; das ist kein Produkt-PASS.

## Statuswirkung

Ein PASS würde nur `G05` für Surface B weiter qualifizieren. Er würde weder
G06 automatisch auf PASS setzen noch A/B-Parität, Produktionsreife oder
`replacement_eligible=true` begründen. G06 benötigt weiterhin eigene
Quick-Flow-Evidence und unveränderten Replay.

`CONTRIBUTION_SOURCE=CODEX_PLUS_BROTHER_GPT`
`CONTRIBUTION_DATE=2026-09-23`
`REVIEW_STATUS=PREPARED_NOT_EXECUTED`
