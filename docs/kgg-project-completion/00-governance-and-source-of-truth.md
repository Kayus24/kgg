# G00 – Source of Truth, Status und Checkpoints

## 1. Ziel

Jeder Arbeitszyklus startet aus einem eindeutig gebundenen Fresh State und setzt am nächsten unerfüllten Gate fort, ohne alte Phasen blind zu wiederholen.

## 2. Warum dieses Gate erforderlich ist

Das Projekt ist mehrfach zwischen UI-Lab, Plugin, Measurement und Produktionskontrolle gedriftet. Ein einziger Abschlussindex verhindert, dass Telemetriearbeiten das Produktziel ersetzen.

## 3. Scope und Nicht-Ziele

Dieses Gate verwaltet Quellen, Status und Checkpoints. Es ändert keine Produkt-, Safety-, Comparator- oder Release-Regel.

## 4. Abhängigkeiten

Keine. Fresh Git, die kanonischen KGG-Dokumente und ein lesbarer Worktree sind erforderlich.

## 5. Aktueller Stand

- `IMPLEMENTATION_STATUS=MASTER_AND_REGISTRY_CREATED_LOCALLY`
- `LIVE_EVIDENCE_STATUS=NOT_MERGED`
- `GATE_STATUS=PARTIAL`
- `EVIDENCE_LEVEL=E0_DOCUMENTED`
- `LAST_VERIFIED_BASE_SHA=2b8024e359bd0f65bcc5666b5e190d78a4b4ed6f`
- `LAST_VERIFIED_AT=2026-09-21`

## 6. Bestehende Evidence

- `docs/kgg-project-completion/README.md`
- `docs/kgg-project-completion/gate-status.json`
- kanonische Goals, Manifest, Bootstrap und Measurement-Dokumente im Repository.

## 7. Lücke und Root Cause

Der neue Abschlussindex ist noch ein lokaler Kandidat. Eine mechanische Konsistenzprüfung und Aufnahme in Main fehlen.

## 8. Kleinschrittiger Arbeitsplan

1. Alle internen Links und JSON-Syntax prüfen.
2. Masterstatus gegen Fresh Main und tatsächliche Dateien prüfen.
3. Dokumente reviewen und mergen.
4. Pro Zyklus `active_gate`, Evidence und `next_action` aktualisieren.
5. Einen Resume-Test durchführen: neuer Chat liest nur Master, Register und aktives Detaildokument und nennt korrekt den nächsten Schritt.

## 9. CONTROL_LOOP_GATE

- `GATE_ID=G00_SOURCE_OF_TRUTH`
- `INPUT=Fresh Main, HEAD, Worktree, Master, gate-status.json`
- `PROCEDURE=Hashes lesen; JSON und Links prüfen; aktives Gate mit Master abgleichen; Resume simulieren`
- `PASS_CRITERIA=Eine eindeutige Baseline, genau ein aktives Gate und reproduzierbarer nächster Schritt`
- `FAIL_CRITERIA=Widersprüchliche Statuswerte, fehlender Detailpfad oder Rückfall auf Chatgedächtnis`
- `RETRY_RULE=Ein identischer Read der widersprüchlichen autoritativen Quelle`
- `FALLBACK=UNKNOWN plus Blocker-Paket`
- `EVIDENCE_OUTPUT=BASELINE_CHECKPOINT und Link-/Schema-Prüfung`
- `NEXT_ON_PASS=G01`
- `NEXT_ON_FAIL=G11 oder WAITING_HUMAN_GATE bei echter Quellenkollision`
- `INVALIDATION_TRIGGERS=Goal-, Master-, Register- oder kanonische Vertragsänderung`

## 10. Tests

- JSON parse von `gate-status.json`.
- Link-/Dateiexistenzprüfung.
- Fresh-Main-/HEAD-/Worktree-Read.
- Resume-Prompt nennt ohne Vollanalyse das aktive Gate.

## 11. Safety und Datenschutz

Checkpoints enthalten nur technische Metadaten, Hashes und synthetische Evidence-Referenzen; keine Chats, Tokens oder Patientendaten.

## 12. Brother-GPT-Eskalation

Nur bei echter Quellenkollision oder unklarer Gate-Priorität. Brother erhält die kollidierenden Textstellen und entscheidet advisory; der Lead validiert.

## 13. Abschlussartefakte

Gemergter Master, valides Register, reproduzierbarer Resume-Test und erster aktualisierter Checkpoint.

## 14. Beitragsherkunft

`CONTRIBUTION_SOURCE=HUMAN_AND_CODEX`, `REVIEW_STATUS=PENDING`.

