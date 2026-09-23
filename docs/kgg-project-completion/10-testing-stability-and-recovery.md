# G10 – Tests, Stabilität und Recovery

## 1. Ziel

Der reale Plugin-/Browserpfad besteht reproduzierbar Targeted-, Negative-, Regression-, Full-Gate- und unveränderte Replay-Prüfungen; bekannte Fehler führen zu deterministischen Fallbacks.

## 2. Warum dieses Gate erforderlich ist

Das Repo besitzt viele gute UI- und Release-Tests sowie jetzt einen Black-Box-Test der lokalen Plugin→Browser→Evidence-Kette. Der vollständige Agent→Plugin→Browser→Evidence-Regelkreis auf einer Real-Host-Surface fehlt noch.

## 3. Scope und Nicht-Ziele

Risikobasierte Tests der geänderten Komponenten. Keine pauschale Neuinstallation oder Vollbattery nach jedem kleinen Schritt.

## 4. Abhängigkeiten

G04, G06, G08 und G09. Befehle werden aus `release-pipeline/kgg_test_battery.py` und vorhandenen Tests gelesen, nicht erfunden.

## 5. Aktueller Stand

- `IMPLEMENTATION_STATUS=REAL_BRIDGE_BLACK_BOX_NEGATIVE_REPLAY_SUITE_PRESENT`
- `LIVE_EVIDENCE_STATUS=TARGETED_NEGATIVE_REPLAY_CRITICAL_AND_UI_REGRESSION_PASS; E3_PENDING`
- `GATE_STATUS=PASS`
- `GATE_SCOPE=local_candidate_stability_only`
- `EVIDENCE_LEVEL=E2_LOCAL_REAL_RUNTIME`
- `LAST_VERIFIED_BASE_SHA=715f2f1de4ee07676450acdf20f005d5407475d2`
- `LAST_VERIFIED_AT=2026-09-23T12:41:06+02:00`

## 6. Bestehende Evidence

Critical/Regression-Battery, Playwright-UI-Smokes, GPT-Evals, Measurement-Tests, Fault Injection, Hook Guard und eine unabhängige Real-Bridge-Black-Box-Suite existieren. Browserdependencies können Downloads auslösen und müssen vorab klassifiziert werden.

Die lokale Regression verwendet seit dem Candidate `715f2f1` zuerst das bereits
vorhandene `release-pipeline/node_modules/playwright`. Dadurch löst ein normaler
UI-/Browserlauf keinen unnötigen `npm exec --yes`-Download aus. Nur wenn kein
lokales Modul vorhanden ist, bleibt der dokumentierte Installationspfad als
Umgebungs-Gate bestehen. Die neue Evidence ist in
[`CP_G10_UI_REGRESSION_20260923.json`](CP_G10_UI_REGRESSION_20260923.json)
gebunden.

## 7. Lücke und Root Cause

Die lokale Producer-/Real-Browser-Brücke ist jetzt in einer unabhängigen Black-Box-Kette mit Drift-, Origin-, Zustands-, Hash- und Replay-Fällen getestet. E3-Agent-Host-Replay fehlt weiterhin.

Die Critical-Battery und genau ein unveränderter Replay sind in
[`CP_G10_STABILITY_REPLAY_20260921.json`](CP_G10_STABILITY_REPLAY_20260921.json)
mit Exit 0 gebunden. `PASS` gilt nur für die lokale Candidate-Stabilität, nicht
für E3-Host-Parität oder Release.

## 8. Kleinschrittiger Arbeitsplan

1. pro Gate einen RED-Akzeptanztest definieren.
2. unabhängigen Golden-Test ohne Producer-/Validator-Helper bauen.
3. Negative Matrix für Lifecycle, Auth, Safety, Evidence und UI-Drift umsetzen.
4. betroffene bestehende Tests anhand Diff auswählen.
5. Critical Gate ausführen; Regression nur für betroffene Bereiche.
6. Candidate-Fingerprint binden.
7. genau einen unveränderten Replay ausführen.
8. Recovery/Disable-/Rollbackpfad testen.

## 9. CONTROL_LOOP_GATE

- `GATE_ID=G10_FULL_STABILITY`
- `INPUT=stabiler Candidate-Fingerprint, Testmatrix, vorbereitete Dependencies`
- `PROCEDURE=Targeted → Negative → relevante Regression → Critical/Full Gate → unveränderter Replay`
- `PASS_CRITERIA=alle Pflichtprüfungen grün; Replay unverändert; kein Test wurde abgeschwächt`
- `FAIL_CRITERIA=deterministischer Fehler, instabiler Fingerprint, fehlende Evidence oder gemeinsamer Helper maskiert Fehler`
- `RETRY_RULE=nur ein identischer Retry bei belegtem transientem Harnessproblem`
- `FALLBACK=Root Cause und Minimalfix; maximal drei materielle Iterationen`
- `EVIDENCE_OUTPUT=TEST_EVIDENCE_INDEX_V1`
- `NEXT_ON_PASS=G11 Final Review und G12`
- `NEXT_ON_FAIL=Minimalfix oder G11`
- `INVALIDATION_TRIGGERS=Candidate-, Test-, Harness-, Contract- oder Expected-Result-Hash ändert sich`

## 10. Tests

- Targeted/Black-Box/Golden.
- vollständige Negativmatrix aus G04, G08 und G09.
- `python release-pipeline/kgg_hook_guard.py --check` vor Commit/Push.
- `cmd /c release-pipeline\run-kgg-tests.cmd --level critical` für Codeänderungen.
- UI-Regression bei UI-/Browseränderung gemäß AGENTS.md.
- unveränderter Replay.

Für den aktuellen Candidate zusätzlich grün:

- `python release-pipeline/kgg_test_battery.py --level regression` im Commit-Hook;
- Ticket-015-Progressions- und Admin-Browser-Smokes ohne `npm exec`;
- UI-Contract, Preview-Marker und alle registrierten UI-Stabilitätsfälle;
- `python release-pipeline/kgg_patch_hygiene.py` nach dem Fresh-Main-Merge.

## 11. Safety und Datenschutz

Testdaten bleiben synthetisch. Keine Dependency-/Browserinstallation ohne vorbereitete und erlaubte Umgebung.

## 12. Brother-GPT-Eskalation

Nur neuer deterministischer Blocker nach Root-Cause-Arbeit oder unerklärte Instabilität. Evidence statt voller Rohlogs senden.

## 13. Abschlussartefakte

Testmatrix, Ergebnisse, Fingerprint, Replay-Evidence, bekannte Grenzen und Recovery-Nachweis.

## 14. Beitragsherkunft

`CONTRIBUTION_SOURCE=HUMAN_AND_CODEX`, `REVIEW_STATUS=PARTIAL`, `NOTE=Local real bridge, negative matrix and unchanged replay are green; external host replay remains pending.`
