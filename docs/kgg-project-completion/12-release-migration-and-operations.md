# G12 – Release, Migration und Betrieb

## 1. Ziel

Der geprüfte Plugin-/UI-Lab-Kandidat wird kontrolliert gemergt, in den Zielhosts installiert, per Post-Merge-Canary geprüft und mit Rollback sowie finaler Einsatzentscheidung betrieben.

## 2. Warum dieses Gate erforderlich ist

Lokaler Code und gemergter PR beweisen keine nutzbare ChatGPT-/Browserfunktion. Der operative Abschluss benötigt Installation und Real-Host-Evidence.

## 3. Scope und Nicht-Ziele

PR, Merge, Paketinstallation, genau ein bounded Post-Merge-Canary, Betriebsdokumentation und Migration. Kein automatisches Abschalten des Custom GPT ohne erfüllte Paritäts- und Stabilitätskriterien.

## 4. Abhängigkeiten

Alle G00–G11 müssen finale Dispositionen besitzen. Push, PR, Merge, Deployment/Installation und Real-Host-Canary sind getrennte Consequence Gates.

## 5. Aktueller Stand

- `IMPLEMENTATION_STATUS=NOT_READY_FOR_FINAL_RELEASE`
- `LIVE_EVIDENCE_STATUS=CORE_BROWSER_AND_CHATGPT_GATES_OPEN`
- `GATE_STATUS=BLOCKED`
- `EVIDENCE_LEVEL=E0_DOCUMENTED`
- `LAST_VERIFIED_BASE_SHA=2b8024e359bd0f65bcc5666b5e190d78a4b4ed6f`
- `LAST_VERIFIED_AT=2026-09-21`

## 6. Bestehende Evidence

Repo besitzt Branch-/PR-/Required-Gate-/Preview-Prozesse. Frühere PRs härteten Measurement und Raw Capture, aber der echte ChatGPT-/Browserpfad ist noch nicht fertig.

## 7. Lücke und Root Cause

G03–G06 sind offen. Daher wäre ein finaler Migrationsclaim verfrüht.

## 8. Kleinschrittiger Arbeitsplan

1. Completion Inventory: jedes Gate final klassifizieren.
2. finalen Diff und Evidence Index durch Lead und Brother reviewen.
3. Hook Guard und erforderliche Tests prüfen.
4. nur eigene allowlistete Änderungen committen und PR erstellen.
5. Required Checks und Reviewbefunde abarbeiten.
6. mit Merge-Gate mergen und Fresh Main binden.
7. Plugin aus gemergtem Stand installieren/deployen.
8. genau einen Post-Merge-Canary pro autorisierter Surface ausführen.
9. Canary-Evidence reconciliieren.
10. Betriebsmodus entscheiden: Custom GPT primär/fallback, Plugin primär/partial, Codex für Entwicklung.
11. Rollback/Disable tatsächlich prüfen.

## 9. CONTROL_LOOP_GATE

- `GATE_ID=G12_FINAL_OPERATIONAL_ACCEPTANCE`
- `INPUT=gemergter SHA, installierte Paketversion, finale Gate-Matrix, autorisierte Canaries`
- `PROCEDURE=Fresh Main → Installation → Tool Discovery → realer Screenshot-/Action-/Quick-Flow-Canary → Evidence-Reconciliation → Rollbackprobe`
- `PASS_CRITERIA=alle realistisch erreichbaren Pflichtfähigkeiten laufen im Zielhost; Grenzen und Betriebsmodus sind dokumentiert`
- `FAIL_CRITERIA=Merge ohne Real-Canary, falsche Version, nicht retrievable Evidence oder Migration trotz fehlender Parität`
- `RETRY_RULE=kein neuer Real-Run ohne neues Run-Budget; read-only Reconciliation ist erlaubt`
- `FALLBACK=PARTIAL_COMPLETE mit Custom GPT als Fallback und klarer Restgrenze`
- `EVIDENCE_OUTPUT=FINAL_ACCEPTANCE_REPORT_V1`
- `NEXT_ON_PASS=PROJECT_COMPLETE`
- `NEXT_ON_FAIL=Rollback, betroffenes Gate oder finaler technischer Grenzstatus`
- `INVALIDATION_TRIGGERS=neuer Main-SHA, Paketversion, Hostpolicy oder Canary-Contract`

## 10. Tests

- Required Checks und relevante Full Battery.
- installierter Versions-/Capability-Check.
- Real-Host-Screenshot-/Action-/Quick-Flow-Canary.
- unveränderter Post-Merge-Replay nur wenn Run-Budget dies erlaubt.
- Disable/Deinstall/Rollback.

## 11. Safety und Datenschutz

Canaries nur mit synthetischer KGG-Testseite. Keine Patient-, Main-App- oder Releasewrites außer explizit erlaubtem Scope.

## 12. Brother-GPT-Eskalation

Ein finaler Brother-Review prüft Gegenbeweise, falsche Erfolgsclaims und verbleibende Grenzen; er kann keine Merge- oder Releasefreigabe erzeugen.

## 13. Abschlussartefakte

Merged SHA, Paketversion, Installationsnachweis, Canary-Evidence, Rollbacknachweis, finale Capability-Matrix und Betriebsentscheidung.

## 14. Beitragsherkunft

`CONTRIBUTION_SOURCE=HUMAN_AND_CODEX`, `REVIEW_STATUS=PENDING`.
