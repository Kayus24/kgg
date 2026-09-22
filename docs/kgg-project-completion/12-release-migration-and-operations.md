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

- `IMPLEMENTATION_STATUS=PARTIAL_COMPLETE_WITH_TECHNICAL_LIMITS`
- `LIVE_EVIDENCE_STATUS=MERGED_REQUIRED_CHECKS_PASS_POST_MERGE_CANARY_NOT_RUN`
- `GATE_STATUS=PARTIAL`
- `EVIDENCE_LEVEL=E3_REAL_HOST`
- `LAST_VERIFIED_BASE_SHA=01fc1077b153840fbef37c79f6152084268932c4`
- `LAST_VERIFIED_AT=2026-09-21T20:08:00+02:00`
- `MERGED_PR=247`
- `MERGED_SHA=01fc1077b153840fbef37c79f6152084268932c4`

## 6. Bestehende Evidence

Repo besitzt Branch-/PR-/Required-Gate-/Preview-Prozesse. Frühere PRs härteten Measurement und Raw Capture, aber der echte ChatGPT-/Browserpfad ist noch nicht fertig.

## 7. Lücke und Root Cause

G05/G06, G08 und G09 enthalten weiterhin ausdrücklich technische Grenzen
(fehlende externe Host-Parität bzw. Envelope-Reconciliation). Ein finaler
Migrationsclaim wäre daher verfrüht; ein PR kann höchstens den geprüften
Dokument-/Candidate-Stand transportieren. Der vollständige Abschlussbericht
steht in
[`CP_G12_FINAL_ACCEPTANCE_20260921.json`](CP_G12_FINAL_ACCEPTANCE_20260921.json)
und klassifiziert den Zustand als `PARTIAL_COMPLETE_WITH_TECHNICAL_LIMITS`.

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

`CONTRIBUTION_SOURCE=BROTHER_GPT`
`CONTRIBUTION_DATE=2026-09-22`
`HANDOFF_ID=POST_MERGE_RECONCILIATION_20260922`
`REVIEW_STATUS=ACCEPTED`
`INCORPORATED_BY=KGG_LEAD`
`SOURCE_SUMMARY=Nach-Merge-Reconciliation auf Baseline- versus beobachteten Main-SHA geprüft.`
`DECISION_SUMMARY=Generation-Baseline historisch belassen; PR #261 als nachfolgend beobachteten Merge dokumentieren; keine Statuspromotion.`

## 15. Aktuelle Reconciliation (2026-09-22)

- `RECONCILIATION_BASELINE=3f9225b6de45e4c46c7deedb86a3e8a2899ecdb1`
- `OBSERVED_MAIN_AFTER_PR_261=818d57415ece7e438410ce6da0ae41c2abadf71a`
- PR #256 (Browser-Runtime-Modulauflösung), PR #257 (Reconciliation der
  G07-Evidence), PR #258 (operative G07-Dokumentation), PR #259 (lokale
  Browser-Verifikation) und PR #260 (Trennung von sichtbarem Host und
  Codex-Bereitschaft) sind auf Main gemergt; PR #261 (Aktualisierung des
  Abschlussstatus) wurde anschließend mit `818d574…` gemergt.
- Der Codex-Ausführungskontext meldet den nativen Bridge als `ready`; das ist
  nicht gleichbedeutend mit einer vorbereiteten kanonischen sichtbaren
  Windows-Hostumgebung.
- In der sichtbaren PowerShell des kanonischen Hosts waren `tunnel-client` und
  die erwartete Profil-Datei nicht auflösbar. Keine Codex-/PTY-Evidence darf
  diesen Hostbefund ersetzen.
- Der eine autorisierte B-Real-Host-Canary startete, lief aber vor der visuellen
  Beobachtung in `real_browser_timeout`; Screenshot, Klick und Seiteneffekt
  wurden nicht erzeugt.
- Die statische Modulauflösung und die relevanten Contract-Tests sind grün.
- Der aktuelle Shell-Read findet Node, die Helper, Playwright und eine
  Chromium-Executable statisch; die Codex-Runtime verwendet dabei Playwright
  `1.62.1`, das Repository-Testmodul `1.61.1`. Die Bindung dieses Shell-/Codex-
  Kontexts an den nativen B-Canary ist nicht bewiesen; es wurde kein Browser
  gestartet.
- Der einzige B-Canary basierte auf Main `17c8e2a…` und lief vor dem Merge des
  Playwright-Auflösungsfixes PR #256 (`c414446…`). Sein Timeout ist daher
  historische Pre-Fix-Evidence und kein Gegenbeweis gegen den aktuellen Bridge-
  Code. Ein Post-Fix-Canary bleibt ohne neues Run-Budget nicht autorisiert.
- Der native `tunnel-mcp`-Bundle ist im sichtbaren Host nicht als lesbarer
  `real_browser.py`-/Helper-Bestand auffindbar; deshalb bleibt die Bindung des
  installierten B-Pfads an den Post-#256-Code `NOT_PROVEN`.
- `PRODUCTION_CONTROL=PILOT_INCOMPLETE`, `A_B=NOT_COMPARABLE` und
  `replacement_eligible=false` bleiben unverändert.
- Nächster zulässiger Schritt: read-only Timeout-/Child-Process-/Localhost-
  Diagnose beziehungsweise — falls der sichtbare Host weiter unvorbereitet
  bleibt — ein separat zu genehmigendes Installations-/Profil-Gate. Ein weiterer
  Real-Canary benötigt ein neues, separat gebundenes Run-Budget.
- Vor einer solchen Vorbereitung muss die offizielle Upstream-Version und ihre
  bekannten ChatGPT-Discovery-Risiken frisch geprüft werden. Der frische
  Read-only-Check von Issue #57 bestätigt einen offenen Discovery-Grenzfall
  nach erfolgreichem `main/server/discover`, aber keinen verifizierten Fix.
  Das hebt keinen Gate-Status an.
- PR #262 ist ungemergt und wegen eines bestehenden CI-/Browser-Layout-Timeouts
  blockiert; seine Release-Freshness-Felder sind keine kanonische Main-Evidence.
