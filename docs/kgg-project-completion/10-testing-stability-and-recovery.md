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

- `IMPLEMENTATION_STATUS=BROAD_EXISTING_TESTS_REAL_BRIDGE_SUITE_MISSING`
- `LIVE_EVIDENCE_STATUS=PARTIAL`
- `GATE_STATUS=PARTIAL`
- `EVIDENCE_LEVEL=E2_LOCAL_REAL_RUNTIME`
- `LAST_VERIFIED_BASE_SHA=2b8024e359bd0f65bcc5666b5e190d78a4b4ed6f`
- `LAST_VERIFIED_AT=2026-09-21`

## 6. Bestehende Evidence

Critical/Regression-Battery, Playwright-UI-Smokes, GPT-Evals, Measurement-Tests, Fault Injection und Hook Guard existieren. Browserdependencies können Downloads auslösen und müssen vorab klassifiziert werden.

## 7. Lücke und Root Cause

Producer und Real-Browser-Brücke sind nicht in einer unabhängigen Black-Box-Kette getestet. Synthetic-Tests decken gemeinsame Denkfehler nicht ab.

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

## 11. Safety und Datenschutz

Testdaten bleiben synthetisch. Keine Dependency-/Browserinstallation ohne vorbereitete und erlaubte Umgebung.

## 12. Brother-GPT-Eskalation

Nur neuer deterministischer Blocker nach Root-Cause-Arbeit oder unerklärte Instabilität. Evidence statt voller Rohlogs senden.

## 13. Abschlussartefakte

Testmatrix, Ergebnisse, Fingerprint, Replay-Evidence, bekannte Grenzen und Recovery-Nachweis.

## 14. Beitragsherkunft

`CONTRIBUTION_SOURCE=HUMAN_AND_CODEX`, `REVIEW_STATUS=PENDING`.
