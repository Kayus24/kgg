# KGG UI Lab V1 – lokaler Candidate-Surface-Lauf

Stand: 14. September 2026. Dieser Nachweis betrifft ausschließlich den
lokalen KGG Plugin-Candidate und eine synthetische, read-only Adapter-Fixture.
Er autorisiert keinen Write. Der separate installierte Codex+Plugin-Transport
ist im eigenen Run-Nachweis dokumentiert.

## Contract und Quelle

- `scenario_id`: `tablet-splitter-scale-drag-synth`
- Fresh-Main-SHA, vor den Läufen frisch gelesen:
  `444fa925dfa989cfe360442f506da9acd9fc55a4`
- Candidate-Gate: `PASS`; Parity-Bundle (`current_state`, `ticket_plan`,
  `safe_canary`): `PASS`
- Adapter: sieben begrenzte Operationen, zwei Source-Reads, ein synthetischer
  `pilot-180-reproduce`-Flow, Evidence- und Session-Abschluss-Reads.

## Unveränderte Replays

Zwischen den Läufen gab es keine Änderung an Code, Skill, Knowledge, Schema,
Test, Expected Result, Seed, Budget oder Capability.

| Feld | Replay 1 | Replay 2 |
| --- | ---: | ---: |
| `status` | `PASS` | `PASS` |
| `reads` | `2` | `2` |
| `context_items` | `4` | `4` |
| `clarifying_questions` | `0` | `0` |
| `action_calls` | `7` | `7` |
| `runtime_ms` | `12` | `11` |
| `root_cause_quality` | `0` | `0` |
| `result_quality` | `100` | `100` |
| `dispatches` / Duplikate | `0` / `0` | `0` / `0` |
| Writes / Leaks | `0` / `0` | `0` / `0` |
| Source-/Gate-/Action-Regressionen | `0` / `0` / `0` | `0` / `0` / `0` |

`result_quality=100` bedeutet hier, dass alle synthetischen Flow-, Gate- und
Evidence-Erwartungen erfüllt wurden. `root_cause_quality=0` ist absichtlich
konservativ: Dieser Runner prüft keine diagnostische Begründung und ersetzt
keine unabhängige Bewertung der Root-Cause-Formulierung.

Der vollständige Replay-2-Payload liegt in
`docs/kgg-ui-lab-v1-candidate-metrics-2026-09-14.json`. Die Laufzeit ist die
vom lokalen Prozess gemessene Ausführungszeit; sie wurde nicht geschätzt.

## Einstufung

Der Candidate ist für diese lokale synthetische Fixture als
`PROVEN_LOCAL` belegt. Das ist ein B-Nachweis innerhalb der gemeinsamen
Runtime. Die installierte Codex+Plugin-Oberfläche ist separat technisch
verifiziert, erreicht aber nur `root_cause_quality: 0`; die Production-Control-
Oberfläche bleibt wegen ihres fehlenden vollständigen Metrik-Payloads
`NOT_COMPARABLE`. Ein Cross-Surface- oder Migrationsurteil ist daher weiterhin
nicht zulässig.
