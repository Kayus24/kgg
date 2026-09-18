# KGG UI Lab V1 – Measurement Envelope

Dieses Dokument ist der kanonische Vertrag für autoritative Mess-Provenance.
Das bestehende `kgg_gpt_result`-Artefakt beschreibt ausschließlich den
Workflow-Abschluss. Die Measurement-Hülle bleibt davon getrennt und darf nur
Werte aus einem vertrauenswürdigen Host-/Action-Transcript, Runtime-Harness,
Git-Ref, Test-Capsule oder unabhängigen Evaluator übernehmen.

## Schema und Identität

Das Artefakt verwendet `kgg-ui-lab/measurement-envelope/v1` und enthält exakt:

```json
{
  "schema": "kgg-ui-lab/measurement-envelope/v1",
  "envelope_id": "<bounded-id>",
  "request_id": "<bounded-id>",
  "surface": "production|candidate|codex_plugin",
  "scenario_id": "<synthetic-capsule-id>",
  "base_sha": "<40 lowercase hex>|UNKNOWN",
  "captured_at": "<RFC3339 UTC>",
  "status": "PASS|FAIL",
  "error_class": "",
  "payload": {},
  "field_provenance": {},
  "evidence_refs": [],
  "missing_fields": [],
  "provenance_sha256": "<64 lowercase hex>"
}
```

Ein `PASS` enthält den unveränderten, exakt geschlossenen 18-Felder-Payload des
Comparators; sein äußerer und innerer `status` müssen beide `PASS` sein.
`base_sha` und `scenario_id` müssen in Außenhülle und Payload identisch sein.
Jede Payload-Property besitzt genau eine Provenance-Angabe mit
`source`, `definition`, `counting_rule`, `observed_by`, `captured_at` und
`evidence_ids`. Jede Evidence-Referenz enthält zusätzlich ihren typisierten
`content`-Snapshot; dessen kanonischer SHA-256 muss exakt mit `sha256`
übereinstimmen. Die Definitionen und Zählregeln sind im Validator kanonisch
festgelegt und dürfen nicht vom getesteten Modell überschrieben werden.

Ein `FAIL` enthält keinen Teil-Payload (`payload: null`) und keine teilweise
ausgefüllte Provenance. Er verwendet ausschließlich eine Comparator-Fehlerklasse
und listet die nicht messbaren Felder in `missing_fields`. Der Comparator erhält
aus einer solchen Hülle nur den geschlossenen Zwei-Felder-Block:

```json
{"status":"FAIL","error_class":"NUMERIC_METRICS_NOT_VERIFIABLE"}
```

Zulässige Fehlerklassen sind `NUMERIC_METRICS_NOT_VERIFIABLE`,
`REQUIRED_READ_NOT_VERIFIABLE`, `FRESH_SHA_NOT_VERIFIABLE` und
`VERIFIABLE_COMPLETION_MISSING`.

## Autoritative Feldquellen

| Felder | Quelle | Zähl-/Bewertungsregel |
| --- | --- | --- |
| `scenario_id` | unveränderliche Test-Capsule | exakt übernehmen |
| `base_sha` | außerhalb des Modells gelesene Git-Ref | 40-stellige Kleinschreibung, bytegenau |
| `status` | Runtime-Harness/Workflow | PASS nur bei vollständig grünem Lauf |
| Reads, Kontext, Rückfragen, Actions, Dispatches, Duplikate | Host-/Action-Transcript | tatsächliche Aufrufe einmal zählen |
| `runtime_ms` | äußerer monotoner Host-Timer | Start und Ende außerhalb des Modells |
| Ergebnis-/Root-Cause-Qualität | unabhängiger Evaluator | Comparator-Skala 0–100; keine Selbsteinschätzung |
| Writes, Leaks, Regressionen | Runtime-/Gate-/Test-Harness | jeder Verstoß blockiert Replacement |

Die zusätzlichen Goal-Felder (`tool_calls`, `failure_classes`,
`evidence_quality`, `source_fidelity`, `stale_state_errors`,
`safety_violations`, `unauthorized_writes`, `unnecessary_context`,
`unnecessary_reads`, `unnecessary_tool_calls`) bleiben separate Evaluator-
Felder, bis ein eigener expliziter Vertrag sie ergänzt. Sie werden niemals
durch Comparator-Felder ersetzt.

## Integrität und Reconciliation

`provenance_sha256` ist der SHA-256-Hash der kanonisch sortierten Hülle ohne
das Hash-Feld selbst. Alle Artefakt-Referenzen sind typisiert, nicht sensibel
und enthalten ihren inhaltlich verifizierten SHA-256 sowie den unveränderten
Content-Snapshot. Vor dem Comparator müssen `request_id`,
`source_sha`, Run-Status, Artefaktname, Artefaktstatus und Hash exakt
reconciliiert werden. Fehlender, doppelter, abgelaufener oder widersprüchlicher
Nachweis ist `PILOT_INCOMPLETE`/`NOT_COMPARABLE`.

Das Modell darf weder diese Hülle erzeugen noch Laufzeit, Zähler oder Qualität
selbst attestieren. Fehlt die externe Hülle, schreibt der Runner nur einen
Failure-Envelope und beendet den UI-Produktionslauf rot. Es gibt keine
Ersatzwerte `0`, `false`, Schätzungen oder historischen Werte.

## Testpflichten

Der Validator benötigt positive und negative Tests für geschlossene Felder,
Hash-Tampering, fehlende Quellen, Modell-Selbstauskunft, stale SHA, doppelte
Runs, fehlende Artefakte, Status-/Artefakt-Widersprüche und Safety-Zähler.
Nach jeder Implementierung folgen TARGETED, relevante Regression, Full Gate
und ein unveränderter Replay. Ein grüner Candidate ersetzt keinen fehlenden
Production-Nachweis.
