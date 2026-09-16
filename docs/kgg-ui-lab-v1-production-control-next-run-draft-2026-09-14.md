# KGG UI Lab V1 – Production-Control Next-Run-Entwurf

Status: `NOT_SENT / PENDING_USER_CONFIRMATION`

Aktueller Blocker: `BLOCKED_BY_FRESH_MAIN_WORKFLOW` – der referenzierte
Workflow ist auf Fresh Main noch nicht enthalten.

Dieser Entwurf korrigiert ausschließlich den Metrikvertrag für einen möglichen
späteren, separat zu bestätigenden read-only Lauf. Er ersetzt nicht die
historische Dokumentation der bereits gesendeten Läufe und wurde nicht an ein
GPT, den Editor oder eine Action übertragen. Ein weiterer Lauf ist aktuell
gesperrt, weil der interne Browser bestätigt, dass der referenzierte Workflow
auf Fresh Main nicht vorhanden ist.

## Sicherheitsgrenze

- Nur das synthetische Szenario `tablet-splitter-scale-drag-synth` verwenden.
- Vor jeder Diagnose Fresh-Main-SHA, Manifest, Playbook und Context lesen.
- Keine Preview-, Dispatch-, Editor-, Ticket-, Main-, Live-, Patient-, Memory-
  oder Coordination-Writes; keine Uploads, Handoffs oder echten Daten.
- Bei fehlendem Pflicht-Read, stale SHA, nicht beobachtbarer Metrik oder
  verifizierbarem Abschluss sofort fail-closed stoppen.
- Vor dem Versand den lokalen Preflight
  `release-pipeline/kgg_production_control_preflight.py` mit dem Vertrag
  `docs/kgg-ui-lab-v1-production-control-readonly-contract.json` ausführen.
  Für diesen Entwurf ist ausschließlich das Profil
  `baseline_no_dispatch` zulässig. Das Profil
  `read_only_validation_runner` darf nur in einem neuen, separat bestätigten
  Lauf verwendet werden; es erlaubt genau den registrierten Read-only-Runner
  und keine Preview-, Main- oder Editor-Action.
- Die datierte Editorbeobachtung ist eine externe UI-Vorbedingung und muss als
  strukturierte Attestation vorliegen (aktuell
  `docs/kgg-ui-lab-v1-editor-live-observation-2026-09-15.json`). Sie darf nicht
  durch einen statischen Editor-Snapshot oder eine GPT-Action-Antwort ersetzt
  werden; fehlt sie oder ist sie veraltet/unstrukturiert, bleibt der Lauf vor
  dem Modellstart blockiert.

## Korrigierter Ergebnisvertrag

Bei einem vollständig beobachteten erfolgreichen Lauf muss der letzte Block ein
JSON-Objekt mit genau diesen Feldern enthalten. Gegenüber dem früheren Entwurf
ist `root_cause_quality` ausdrücklich ergänzt:

```json
{
  "scenario_id": "tablet-splitter-scale-drag-synth",
  "base_sha": "<genau 40 hexadezimale Zeichen>",
  "status": "PASS",
  "reads": 0,
  "context_items": 0,
  "clarifying_questions": 0,
  "action_calls": 0,
  "dispatches": 0,
  "duplicate_dispatches": 0,
  "runtime_ms": 0,
  "result_quality": 0,
  "root_cause_quality": 0,
  "repository_writes": 0,
  "secret_leaks": 0,
  "patient_data_leaks": 0,
  "source_regressions": 0,
  "gate_regressions": 0,
  "action_regressions": 0
}
```

Alle numerischen Felder müssen tatsächlich beobachtete, nicht-negative
Ganzzahlen sein. `NOT_MEASURABLE`, Schätzungen, fehlende Felder, ein nicht
40-stelliger SHA oder zusätzliche Felder sind kein vollständiger Payload.
`root_cause_quality` ist wie `result_quality` eine Zahl von 0 bis 100.

Wenn der vollständige Payload nicht belegbar ist, darf kein Teil-Payload als
PASS ausgegeben werden. Stattdessen ist ausschließlich ein begrenzter
Fehlerblock zulässig, zum Beispiel:

```json
{"status": "FAIL", "error_class": "NUMERIC_METRICS_NOT_VERIFIABLE"}
```

Zulässige Fehlerklassen sind nur die im Comparator registrierten Klassen
`NUMERIC_METRICS_NOT_VERIFIABLE`, `REQUIRED_READ_NOT_VERIFIABLE`,
`FRESH_SHA_NOT_VERIFIABLE` und `VERIFIABLE_COMPLETION_MISSING`. Ein solcher
Fehlerblock ist ein sicherer negativer Nachweis, aber kein A/B- oder
Migrationsnachweis.

## Versandgrenze

Dieser Entwurf wird erst nach einer neuen unmittelbaren Bestätigung und erst
nach einer verifizierten Aufnahme des Workflows in Fresh Main verwendet. Bis
dahin bleiben der bestehende Production-Nachweis, der Comparator und die
Migration-Gates unverändert `NOT_COMPARABLE` beziehungsweise `NOT_ELIGIBLE`.
