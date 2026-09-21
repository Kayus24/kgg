# G11 – Brother-GPT-Eskalation und Dokument-Governance

## 1. Ziel

Ein neuer, dokumentseitig ungelöster Blocker wird einmal strukturiert an den Brother/Custom GPT übergeben, dessen Lösung wird in einem zweiten Pass kritisch geprüft und erst nach Lead-Validierung mit Herkunftsnotiz in die Projektdokumente übernommen.

## 2. Warum dieses Gate erforderlich ist

Es verhindert Stillstand, Mikrofragen und wiederholte Denkfehler, ohne dem externen Berater Schreib-, Freigabe- oder Erfolgsautorität zu geben.

## 3. Scope und Nicht-Ziele

Advisory Analyse, Architektur- und Lösungsplanung. Kein Repo-Write, Test, Dispatch, PR, Merge oder Permission Grant durch den Brother.

## 4. Abhängigkeiten

G00 und ein konkreter neuer Blocker-Fingerprint. Der Benutzer hat den Brother als wiederkehrenden Architektur-/Kontrollkanal vorgesehen.

## 5. Aktueller Stand

- `IMPLEMENTATION_STATUS=ESCALATION_SKILL_PRESENT_PROCESS_PROVEN_ON_G03_BLOCKER`
- `LIVE_EVIDENCE_STATUS=HANDOFF_SELF_REVIEW_LEAD_REVIEW_AND_PROVENANCE_BOUND`
- `GATE_STATUS=PASS`
- `EVIDENCE_LEVEL=E1_SYNTHETIC`
- `CHECKPOINT=CP_G11_BROTHER_CYCLE_20260921.json`
- `HANDOFF_ID=G03_CHATGPT_DISCOVERY_20260921_01`
- `LAST_VERIFIED_BASE_SHA=1e6c6e3e28603f28bfbad3b127c688e722c823f5`
- `LAST_VERIFIED_AT=2026-09-21T19:52:00+02:00`

## 6. Bestehende Evidence

`kgg-escalation` existiert. Für den G03-Blocker ist ein vollständiger, einmaliger
Zyklus mit stabiler Herkunfts-, Fingerprint- und Self-Review-Regel im
Checkpoint und im betroffenen Zieldokument gebunden. Weitere Reviews desselben
unveränderten Fingerprints sind ausdrücklich ausgeschlossen.

Der aktuelle Lead-Review bestätigt, dass der G03-Fingerprint gelöst ist und
keine neue Brother-Schleife erforderlich ist. Die verbleibenden technischen
Grenzen (fehlende B/C-Host-Parität, externe Safety-/Envelope-Evidence und
fehlender Merge-/Canary-Nachweis) sind in den aktiven G08/G09/G10/G12-
Dokumenten gebunden.

## 7. Lücke und Root Cause

Es fehlte ein verpflichtender, dokumentierter Ablauf vom Blocker über doppelte Prüfung bis zur nachvollziehbaren Übernahme.

## 8. Kleinschrittiger Arbeitsplan

1. Blocker-Fingerprint aus Baseline, Gate, Fehlerklasse und Evidence-Hashes bilden.
2. prüfen, ob derselbe Fingerprint bereits reviewed wurde.
3. genau ein `BROTHER_HANDOFF_PACKAGE` erstellen.
4. Brother um Diagnose, Reuse-Option, Minimalplan, Tests, Risiken und Fallback bitten.
5. im selben Brother-Chat einen zweiten Prompt zur Selbstkritik/Korrektur senden.
6. Lead prüft Antwort gegen Fresh Main, Safety und Gate-Scope.
7. nur akzeptierte/revidierte Teile in das betroffene Detaildokument übernehmen.
8. Herkunftsblock und Changelog-Eintrag ergänzen.
9. Statusregister und Checkpoint aktualisieren.

## 9. CONTROL_LOOP_GATE

- `GATE_ID=G11_BROTHER_ADVISORY`
- `INPUT=neuer Blocker-Fingerprint und bounded Evidence-Paket`
- `PROCEDURE=Erstanalyse → Brother-Self-Review → Lead-Review → Dokumentpatch → Konsistenzprüfung`
- `PASS_CRITERIA=Lösung ist geprüft, in-scope, testbar, dokumentiert und eindeutig als Brother-Beitrag markiert`
- `FAIL_CRITERIA=ungeprüfte Übernahme, Scope-/Gate-Abschwächung, Secrets/Patientendaten oder rekursive Brother-Kette`
- `RETRY_RULE=kein erneuter Review bei identischem Fingerprint und unveränderter Evidence`
- `FALLBACK=BLOCKED_WITH_FINAL_TECHNICAL_CONCLUSION oder genau ein Human Gate`
- `EVIDENCE_OUTPUT=BROTHER_ADVISORY_RECORD_V1`
- `NEXT_ON_PASS=zum blockierten Gate zurückkehren`
- `NEXT_ON_FAIL=WAITING_HUMAN_GATE oder finaler technischer Grenzstatus`
- `INVALIDATION_TRIGGERS=neue Evidence oder veränderter Blocker-Fingerprint`

## 10. Tests

- Trockenlauf mit synthetischem Blocker.
- Duplicate-Fingerprint wird nicht erneut gesendet.
- Brother-Lösung mit Gate-Abschwächung wird abgelehnt.
- akzeptierter Vorschlag erhält vollständigen Herkunftsblock.
- Resume liest den neuen Dokumentschritt korrekt.

## 11. Safety und Datenschutz

Handoff enthält keine Tokens, Patientendaten, vollständigen Chats oder unnötigen Browserrohbilder. Nur minimale technische Evidence.

## 12. Brother-GPT-Eskalation

### BROTHER_HANDOFF_PACKAGE

```text
HANDOFF_ID=
BLOCKER_FINGERPRINT=
BASE_SHA=
ACTIVE_GATE=
OBJECTIVE=
OBSERVED=
EXPECTED=
EVIDENCE_REFS=
ATTEMPTS=
CONSTRAINTS=
REUSABLE_COMPONENTS_CHECKED=
ONE_DECISION_QUESTION=
```
Pflichtantwort des Brother:

```text
DIAGNOSIS=
ASSUMPTIONS=
ROOT_CAUSE=
REUSE_OPTIONS=
PROPOSED_SOLUTION=
SMALL_STEPS=
TEST_PLAN=
FALLBACK=
RISKS=
REQUIRED_DOC_CHANGES=
SELF_REVIEW=
FINAL_RECOMMENDATION=
```

Der zweite Prompt lautet sinngemäß: „Prüfe deinen Vorschlag jetzt gegen Evidence, Scope, Safety, unnötigen Eigenbau und mögliche Gegenbeispiele. Gib eine korrigierte Endfassung aus.“

## 13. Abschlussartefakte

Handoff, Erstfassung, Self-Review, Lead-Entscheidung, Dokumentpatch und Herkunftsblock.

## 14. Beitragsherkunft

Jede Übernahme nutzt exakt:

```text
CONTRIBUTION_SOURCE=BROTHER_GPT
CONTRIBUTION_DATE=<ISO-8601>
HANDOFF_ID=<stable-id>
REVIEW_STATUS=ACCEPTED|REVISED|REJECTED
INCORPORATED_BY=KGG_LEAD
SOURCE_SUMMARY=<what the Brother contributed>
DECISION_SUMMARY=<what was incorporated and why>
```
