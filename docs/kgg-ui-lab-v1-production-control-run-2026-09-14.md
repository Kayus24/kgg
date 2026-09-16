# KGG UI Lab V1 – Production-Control-Run

Stand: 14. September 2026. Dieser Bericht dokumentiert die zwei ausdrücklich
autorisierten, synthetischen read-only Läufe im bestehenden Production-Control-
Custom-GPT. Es wurden keine Preview-, Dispatch-, Editor-, Ticket-, Main-,
Live-, Patient- oder Repository-Writes ausgeführt.

## Beobachtete grobe Metriken

| Feld | Wert |
| --- | ---: |
| `scenario_id` | `tablet-splitter-scale-drag-synth` |
| `base_sha` | `NOT_REPORTED` |
| GPT-Status | `COMPARABLE` (vom GPT selbst) |
| `reads` | `17` |
| `context_items` | `17` |
| `clarifying_questions` | `0` |
| `action_calls` | `17` |
| `dispatches` | `0` |
| `duplicate_dispatches` | `0` |
| `runtime_ms` | `NOT_MEASURABLE` |
| `result_quality` | `NOT_MEASURABLE` |
| `repository_writes` | `0` |
| `secret_leaks` | `0` |
| `patient_data_leaks` | `0` |
| `source_regressions` | `NOT_MEASURABLE` |
| `gate_regressions` | `NOT_MEASURABLE` |
| `action_regressions` | `NOT_MEASURABLE` |

Die sichtbare Antwort enthielt keine Action mit Schreibwirkung. Die 17
`action_calls` sind daher als vom GPT gemeldete Lese-/Kontextaktionen erfasst,
nicht als Beleg für einen vollständigen A/B-Payload.

## Inhaltlicher Befund

Das GPT schlug als wahrscheinlichste Ursache eine verschachtelte
`tabletSplitScaleControl`-Steuerung im Splitter vor und empfahl, diese UI-
Steuerung zu entfernen. Dieser Vorschlag wird nicht automatisch übernommen:

- Der Fresh-Main-Control reproduziert den eigentlichen #180-Fehler mit
  `handleBoundaryDelta=230`.
- Der lokale Candidate behebt diesen Fehler durch die lokale
  Koordinatenberechnung in `updateTabletLayoutHandle()`; derselbe Lauf besteht
  zweimal unverändert.
- Die verschachtelte Splitter-Steuerung existiert im aktuellen Candidate als
  bewusst geschützte UI-/Pointer-Interaktion (`.tabletSplitScaleControl` wird
  beim Drag separat abgefangen). Eine Entfernung wäre ein neuer, nicht
  beauftragter UI-Patch und braucht einen eigenen roten Test.

Damit ist der externe GPT-Vorschlag ein **sekundärer Prüfhinweis**, aber kein
freigegebener Fix und kein Paritätsnachweis.

Als Reaktion auf die Contract-Lücke wurde im Request-Dokument ein strengerer
Folgeprompt vorbereitet und nach ausdrücklicher Freigabe genau einmal gesendet.

## Zweiter Lauf mit korrigiertem Payload-Vertrag

Der Folgeprompt verlangte zuerst die Fresh-Main-/Manifest-/Playbook-/Context-
Reads, den tatsächlich gelesenen 40-stelligen SHA sowie einen letzten JSON-Block
mit einem geschlossenen Feldsatz. Der GPT meldete Fresh-Main
`444fa925dfa989cfe360442f506da9acd9fc55a4`, 17 gelesene Kontextaktionen und
keine Dispatches oder Writes. Die inhaltliche Diagnose blieb beim bereits
beobachteten sekundären Hinweis (`tabletSplitScaleControl`), ohne einen Patch
auszuführen.

Der Lauf endete fail-closed mit:

```json
{
  "status": "FAIL",
  "error_class": "NUMERIC_METRICS_NOT_VERIFIABLE"
}
```

Damit wurde der gewünschte PASS-/Metrikvertrag trotz der Korrektur nicht
erfüllt: `runtime_ms`, `source_regressions`, `gate_regressions` und
`action_regressions` wurden nicht als nicht-negative Ganzzahlen belegt. Der
lokale Comparator klassifiziert den Lauf deshalb als
`NOT_COMPARABLE / pilot_incomplete` (kein A/B-/Migrationsurteil). Der Lauf ist
als sicherer negativer Vertragsnachweis wertvoll, ersetzt aber keinen
vollständigen Production-Control-Surface-Nachweis.

Für die Fallback-Leiter wurde daraus nur lokal ein sanitisiertes
Bruder-Handoff-Paket erstellt:
`docs/kgg-ui-lab-v1-production-metrics-bruder-handoff-2026-09-14.json`.
Es bleibt `local_queue_only` mit `PENDING_USER_CONFIRMATION`; es gab keinen
Bruder-Versand und keine weitere externe Aktion.

## Comparator-Einstufung

Der lokale Comparator lehnt beide GPT-Antworten als `NOT_COMPARABLE` ab: Sein
Vertrag verlangt `scenario_id`, einen gemeldeten
40-stelligen `base_sha`, `status` `PASS` oder `FAIL` sowie nicht-negative
Ganzzahlen für sämtliche Metrikfelder. Im ersten Lauf fehlten `base_sha` und
der geschlossene Status-/Zahlenvertrag. Im zweiten Lauf wurde zwar der SHA
genannt und `FAIL` verwendet, aber nur ein verkürztes Fehlerobjekt statt des
verbindlichen Feldsatzes geliefert. Der Comparator klassifiziert diesen
kontrollierten Fehlerblock nun als `pilot_incomplete` (statt als bloßen
Schemafehler); es wurde weiterhin kein Replacement- oder Migrationsurteil
erzeugt.
