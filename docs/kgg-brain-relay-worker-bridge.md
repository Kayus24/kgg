# KGG-Relay-Brücke

Die vollständige Runtime bleibt lokal auf dem PC. Task Capsule, Handoff,
Worker, Verifier, Cricket und Logs werden dort verarbeitet. GitHub ist nur ein
optionaler Kurzpass für den sichtbaren Koordinationsstand.

## Erlaubter Kurzpass

Optional darf genau diese Datei gelesen oder geschrieben werden:

`coordination-bridge/tasks/<task_id>.json`

Sie enthält exakt diese neun Felder und keine weiteren:

```text
schema_version, task_id, role, generation, revision, status,
requirements_sha256, handoff_sha256, next_action
```

`schema_version` ist immer `kgg-coordination-bridge-v1`. Der Kurzpass enthält
keine Patientendaten, QR-Rohdaten, Secrets, Prompts oder Logs. Die Handoff-
Hash-Berechnung entfernt sowohl `handoff_hash` als auch `handoff_sha256` vor
der kanonischen JSON-Serialisierung (`ensure_ascii=False`, sortierte Schlüssel,
keine Leerzeichen) und hasht UTF-8. Der Requirements-Text ersetzt CRLF und CR
durch LF, wird getrimmt und ohne angehängten Zeilenumbruch als UTF-8 gehasht.

## Gemeinsame Rollen und Zustände

Die Bridge verwendet die bestehenden KGG-Rollen: `luna-manager`, `lead-gpt`,
`gpt-subchat`, `lead-synthesis`, `luna-relay`, `luna-max-worker`, `verifier`,
`cricket`, `ticket-master`, `sol-endboss`, `ci-acceptance` und `status-read`.

Die gemeinsamen `TASK_STATES` sind: `PASS`, `FAIL`, `BLOCKED`, `PENDING`,
`NEEDS_LEAD` und `NEEDS_SOL`.

Für direkte Codex-Vermittlung muss der PC mit der vollständigen lokalen Runtime
laufen. Die GitHub-Brücke ersetzt diese Runtime nicht; ein fehlender oder
veralteter Kurzpass ist kein Beleg für lokalen Abschluss.
