# KGG Project Completion – Master-Gates

Stand dieses Kandidaten: 2026-09-21

Fresh Remote Main beim Abschluss der Planungsnachbereitung: `12b13767cc1667f97d428e1f7f7b7978fe2e4ac4`

Letzter verifizierter Realpfad-Code-Checkpoint: `dafa352164d1a14e2c5036aac90b27459e79a0fe`

Letzter Dokumentations-/Safety-Checkpoint: `211d6a2677926839fa79ba69eb09ed1389e2aa3b`

Dieses Verzeichnis ist die Arbeits- und Abschlusssteuerung für das KGG-Agentenprojekt. Es ersetzt keine Fach-, Safety-, Measurement- oder Release-Verträge. Bei Widerspruch gilt die jeweils fachlich kanonische Quelle; der Widerspruch wird als Gate-Blocker erfasst und nicht stillschweigend aufgelöst.

Die kompakte Kriterienübersicht für „läuft“ versus „vollständig abgeschlossen“
und die vorbereitete Arbeitsgrundlage für kleinere Modelle stehen in
[project-readiness.md](project-readiness.md). Dort ist jeder Pflichtpunkt mit
Gate-Kriterium, Erfüllungsstand, Evidence-Lücke, nächstem Schritt und
Detaildokument erfasst. `gate-status.json` bleibt die einzige maschinenlesbare
Statusquelle; der Goal-Prompt ist
[kgg-project-completion-goal-prompt.md](kgg-project-completion-goal-prompt.md).

## 1. Unveränderliches Oberziel

Das Projekt besitzt zwei gleichrangige Produktziele:

1. Die benötigten Funktionen der KGG Custom GPTs werden in ein universell nutzbares KGG-Plugin überführt, das im normalen ChatGPT und – soweit die Host-Fähigkeiten reichen – in Codex verwendet werden kann.
2. Dieses Plugin stellt einen echten UI-Lab-Kanal für die KGG-HTML-App bereit:
   - visueller Regelkreis: Screenshot → GPT-Auswertung → Maus-/Touch-Aktion → neuer Screenshot → Zustandsprüfung;
   - Quick Flows: vorgefertigte, versionierte Navigations- und Bedienfolgen mit visueller Rückfallebene.

Measurement, Provenance und Telemetrie sichern diese Funktionen ab. Sie sind kein Ersatz für eine funktionierende Browser-Brücke.

## 2. Was „fertig“ bedeutet

`PROJECT_COMPLETE` ist nur zulässig, wenn alle Pflicht-Gates `PASS` oder ein ausdrücklich erlaubter finaler Grenzstatus sind, keine ungeklärten Pflichtpunkte verbleiben und der reale End-to-End-Pfad nachgewiesen ist.

Mindestens muss nachgewiesen sein:

- Ein normales ChatGPT kann das installierte KGG-Plugin erkennen und mindestens ein read-only KGG-Tool ausführen.
- Ein autorisierter KGG-Agent kann eine echte KGG-Testseite öffnen, einen echten Screenshot erhalten, eine echte Aktion ausführen und den veränderten Zustand mit einem zweiten Screenshot prüfen.
- Mindestens drei kanonische Quick Flows laufen auf der echten Testseite mit Schritt-Evidence und visueller Rückfallebene.
- Custom GPT, normales ChatGPT mit Plugin und Codex+Plugin sind je Surface ehrlich als `READY`, `PARTIAL` oder `NOT_SUPPORTED` klassifiziert.
- Safety, Datenschutz, Raw-Evidence, Tests, Installation, Rollback und Betriebsdokumentation sind abgeschlossen.

Nicht zugängliche Host-Interna dürfen als `NOT_OBSERVABLE` abgeschlossen werden. Eine fehlende Kernfunktion wie echte Screenshots oder echte Browseraktionen darf dagegen nicht als „nur nicht beobachtbar“ umetikettiert werden.

## 3. Status- und Evidence-Regeln

Erlaubte Gate-Statuswerte:

- `PASS`: Abnahmekriterium mit der geforderten Evidence-Stufe erfüllt.
- `PARTIAL`: verwertbare Teile vorhanden, mindestens ein Pflichtkriterium fehlt.
- `FAIL`: vorhandene Implementierung widerspricht dem Kriterium.
- `BLOCKED`: nächster erlaubter Schritt benötigt eine echte externe Voraussetzung oder ein Consequence Gate.
- `UNKNOWN`: autoritative Prüfung fehlt; niemals als Erfolg behandeln.
- `NOT_APPLICABLE`: nachgewiesen nicht relevant; Begründung erforderlich.

Evidence-Stufen:

1. `E0_DOCUMENTED`: Behauptung oder Spezifikation.
2. `E1_SYNTHETIC`: Fixture/Mock/Unit-Test.
3. `E2_LOCAL_REAL_RUNTIME`: reale lokale Browser-/MCP-Ausführung.
4. `E3_REAL_HOST`: echte Ausführung in ChatGPT, Custom GPT oder Codex.
5. `E4_REPEATED_STABLE`: unveränderter Real-Host-Replay mit gebundener Evidence.

Ein Gate darf nur mit der in seinem Detaildokument verlangten Stufe auf `PASS` gesetzt werden. `E1_SYNTHETIC` beweist niemals eine echte Host-Funktion.

## 4. Abschlussmatrix

| Gate | Pflichtpunkt | Aktueller Status | Aktuelle Evidence | Für PASS erforderlich | Detail |
| --- | --- | --- | --- | --- | --- |
| G00 | Source of Truth, Statusregister, Checkpoints | `PASS` | Dokumentensatz in PR #239 gemergt; Required Gate grün; Resume-Regel getestet | Fresh-Main-gebundener Dokumentensatz und eindeutiger nächster Gate-Schritt | [G00](00-governance-and-source-of-truth.md) |
| G01 | Vollständige Custom-GPT-Funktionsinventur und Migration | `PASS` | 30 operationIds, fünf Skills, Manifest und kanonische Quellen abgebildet; Self-Tests grün; PR #241 auf Main `fe62c8b` | Jede benötigte Fähigkeit besitzt Zielkomponente, Test und Disposition; Live-Parität bleibt nachgelagert | [G01](01-custom-gpt-capability-migration.md) |
| G02 | Universelles Plugin-Paket | `PARTIAL` | Portable Root-Manifest, repo-lokale Marketplace-Registrierung und frische lokale Codex-Installation grün; ChatGPT-Discovery noch nicht live bewiesen | Paket in Codex und ChatGPT installierbar, versioniert und ohne lokale Pfadannahmen | [G02](02-universal-plugin-package.md) |
| G03 | Normales ChatGPT erkennt und nutzt das Plugin | `PASS` | Private Tunnelressource, offizieller Client, verbundene ChatGPT-App und genau ein read-only `get_current_state`-Canary mit `status=ready`; Client danach gestoppt; Secret nie in Evidence gespeichert | Für G07 den proven Transport verwenden; keinen zweiten G03-Canary ausführen | [G03](03-chatgpt-plugin-connection.md) |
| G04 | Echte Browser-/UI-Brücke | `PASS` | Lokaler realer Chromium-Lauf: zwei unterschiedliche Screenshot-Hashes, Zustandswechsel und fail-closed Hostfehler; E2 | Echte Session, Screenshot, Koordinaten-/Semantik-Aktionen und Zustandsbeobachtung | [G04](04-real-browser-bridge.md) |
| G05 | Visueller Screenshot-Aktions-Regelkreis | `PARTIAL` | lokaler persistenter Observe/Decide/Act/Verify-Loop mit E2-Evidence; Host-Parität fehlt | Autorisierten Agent-Host anbinden und E3 nachweisen | [G05](05-visual-interaction-loop.md) |
| G06 | Reale Quick Flows | `PARTIAL` | Drei kanonische Flows, echter Locator-Drift-Fallback und unveränderter Replay lokal nachgewiesen; E3-Host-Parität fehlt | Mindestens drei reale, versionierte Flows mit Fallback, Step Evidence und unverändertem Replay | [G06](06-real-quick-flows.md) |
| G07 | Surface-Integration A/B/C | `PASS` (Klassifikation; B Real-UI-Audit `PARTIAL`) | A bleibt aus dem aktuellen Repo nicht beobachtbar; B genau ein Real-Host-Canary fail-closed mit `real_browser_timeout`; C lokaler Bridge-/Provenance-Pfad mit statischer Playwright-Auflösung; [G07-Evidence](G07_REAL_B_HOST_CANARY_20260922.json) | ehrliche, live geprüfte Capability-Matrix und begründete NOT_TESTED/SYNTHETIC_ONLY/NOT_OBSERVABLE-Zeilen; keine Capability-Vererbung; keine Aussage über vollständige UI-Parität | [G07](07-surface-integration.md) |
| G08 | Safety, Datenschutz und Autorisierung | `PARTIAL` | lokale Realpfad-Origin-/Pfad-Allowlist und 57/57 Negativ-/Safety-Tests grün; externe Host-Safety fehlt | Domain-Allowlist, Lease, Limits, Sanitization und Negativtests am Realpfad; E3 bleibt offen | [G08](08-security-privacy-and-authorization.md) |
| G09 | Evidence und Provenance | `PARTIAL` | lokale Screenshot-/Action-/Measurement-Evidence und 57/57 Rehash-/Tamper-Tests grün; externe Envelope-Reconciliation fehlt | Browser-Evidence retained, gehasht, run-gebunden; keine erfundenen Nullwerte; E3 bleibt offen | [G09](09-evidence-and-provenance.md) |
| G10 | Test-, Fault- und Stabilitätsloops | `PASS` (lokale Candidate-Stabilität) | Black-Box, Drift, Origin, Replay, Critical und UI-Regression grün; genau ein unveränderter Critical-Replay; E3-Replay fehlt | Black-Box-Realpfad, Negative, Regression, Full Gate, unveränderter Replay; E3 bleibt technische Grenze | [G10](10-testing-stability-and-recovery.md) |
| G11 | Brother-GPT-Eskalation und Dokumentpflege | `PASS` | G03-Blocker mit Handoff, Self-Review, Lead-Review und Herkunftsblock in `CP_G11_BROTHER_CYCLE_20260921.json` gebunden | Bei neuem Fingerprint denselben geprüften Ablauf wiederverwenden; unveränderte Fingerprints nicht erneut senden | [G11](11-brother-gpt-escalation.md) |
| G12 | Release, Migration und Betrieb | `PARTIAL_COMPLETE_WITH_TECHNICAL_LIMITS` | Reconciliation-Baseline `3f9225b6de45e4c46c7deedb86a3e8a2899ecdb1`; PR #261 danach mit Main-SHA `818d57415ece7e438410ce6da0ae41c2abadf71a` gemergt; Required Gates grün; kein zweiter B-Canary und kein Post-Merge-Canary ausgeführt | Custom GPT bleibt Fallback; keine Migration oder Ersetzbarkeit behaupten; nächster Schritt ist ausschließlich ein separat freizugebender Runtime-Diagnoselauf | [G12](12-release-migration-and-operations.md) |

## 5. Kritischer Pfad

Die Ausführung folgt grundsätzlich dieser Reihenfolge:

`G00 → G01 → G02 → G03 → G04 → G05 → G06 → G07 → G08/G09 → G10 → G11 → G12`

G08 und G09 werden bei jedem Implementierungsschritt mitgeführt. Sie dürfen die Kernfunktion nicht durch endlose Metaaudits verdrängen.

Der aktuelle Projektendzustand ist
`PARTIAL_COMPLETE_WITH_TECHNICAL_LIMITS`. Der historische Abschlusscheckpoint
`CP_G12_FINAL_ACCEPTANCE_20260921` bleibt unverändert; die aktuelle G07-
Reconciliation steht in `G07_REAL_B_HOST_CANARY_20260922.json`. Die nachfolgende
Runtime-Diagnose öffnet die Klassifikation nicht erneut und ändert keinen
Gate-Status.

Der einzige vorbereitete Folgepfad ist ein später separat autorisierter,
synthetischer A/B-Host-Audit:

`Fresh Bindung → Execution-Envelope instanziieren → A separat prüfen → B separat prüfen → G08/G09 reconciliieren → Statusänderungen nur vorschlagen.`

Die ausführbare Reihenfolge steht in
[`07a-dual-surface-ui-audit-runbook.md`](07a-dual-surface-ui-audit-runbook.md),
die deaktivierte maschinenlesbare Vorlage in
[`G07_DUAL_SURFACE_EXECUTION_ENVELOPE_TEMPLATE_20260921.json`](G07_DUAL_SURFACE_EXECUTION_ENVELOPE_TEMPLATE_20260921.json).
Beide Dateien sind reine Planung: Sie erzeugen weder Run-, Key-, Tunnel- noch
Write-Budget und ändern `gate-status.json` nicht.

Für den aktuellen B-Timeout gilt zusätzlich: zuerst read-only die Timeout-
Schicht, den Child-Process-/Playwright-Kontext und die Localhost-Bindung
diagnostizieren. Ein weiterer Real-Canary ist erst nach einem neuen, separat
gebundenen Run-Budget zulässig.

## 6. Globale Control-Loop-Regel

Für jeden Gate-Schritt:

1. `ORIENT`: Master, Statusregister und genau ein aktives Detaildokument lesen.
2. `FRESH`: Main, HEAD, Worktree und betroffene Vertrags-Hashes prüfen.
3. `PREFLIGHT`: Abhängigkeiten, Berechtigungen, Testumgebung und Host-Grenze vor dem Write prüfen.
4. `RED`: kleinstes scheiterndes Akzeptanz- oder Negativkriterium herstellen.
5. `FIX`: kleinsten wiederverwendenden Patch umsetzen.
6. `TARGETED`: Gate-spezifischen Test ausführen.
7. `NEGATIVE`: Fehlpfade und Safety prüfen.
8. `REGRESSION`: nur betroffene bestehende Suites ausführen.
9. `EVIDENCE`: Resultate, Hashes und Evidence-Stufe festhalten.
10. `GATE`: `PASS`, `PARTIAL`, `BLOCKED` oder `FAIL` entscheiden.
11. `CHECKPOINT`: nächsten Schritt speichern; bestandene Arbeit nicht wiederholen.

Bei einem unbekannten Problem wird nicht geraten. Es gilt [G11](11-brother-gpt-escalation.md).

## 7. Regeln für kleinere Modelle

- Immer nur ein Gate und ein kleinster Sub-Step gleichzeitig.
- Keine Architektur aus Chatverlauf rekonstruieren; diese Dokumente sind der Arbeitsindex.
- Keine neue Bibliothek oder Plattform, bevor vorhandene KGG-Komponenten geprüft wurden.
- Keine erfundenen Kommandos; Befehle aus Repo, Detaildokument oder Testregister ableiten.
- Keine Vollanalyse nach jedem Resume; nur Hashes und betroffene Checkpoints prüfen.
- Kein `PASS` ohne Evidence-Link, ausgeführten Test und geforderte Evidence-Stufe.
- Bei Unsicherheit genau einen gezielten Read; danach Brother-Handoff statt Schleife.
- Keine Mikrofreigaben innerhalb eines bereits aktivierten bounded Envelopes.

## 8. Zugehörige Steuerdateien

- Maschinenlesbarer Gate-Stand: [gate-status.json](gate-status.json)
- G04-Checkpoint-Capsule: [CP_G04_REAL_BROWSER.json](CP_G04_REAL_BROWSER.json)
- G05-Checkpoint-Capsule: [CP_G05_VISUAL_LOOP.json](CP_G05_VISUAL_LOOP.json)
- G06-Checkpoint-Capsule: [CP_G06_REAL_FLOWS.json](CP_G06_REAL_FLOWS.json)
- G03-Aktivierungs-Runbook: [03a-g03-transport-activation-runbook.md](03a-g03-transport-activation-runbook.md)
- G03-Human-Gate-Paket: [G03_HUMAN_GATE_REQUEST_20260921.json](G03_HUMAN_GATE_REQUEST_20260921.json)
- G03-Runtime-Key-Gate: [G03_RUNTIME_KEY_GATE_20260921.json](G03_RUNTIME_KEY_GATE_20260921.json)
- G07-A/B/C-Capability-Matrix: [A_B_C_CAPABILITY_MATRIX_V1.md](A_B_C_CAPABILITY_MATRIX_V1.md)
- G07-Dual-Surface-Audit-Runbook: [07a-dual-surface-ui-audit-runbook.md](07a-dual-surface-ui-audit-runbook.md)
- G07-Dual-Surface-Execution-Envelope-Template: [G07_DUAL_SURFACE_EXECUTION_ENVELOPE_TEMPLATE_20260921.json](G07_DUAL_SURFACE_EXECUTION_ENVELOPE_TEMPLATE_20260921.json)
- G07-Checkpoint-Capsule: [CP_G07_SURFACE_MATRIX_20260921.json](CP_G07_SURFACE_MATRIX_20260921.json)
- G07-Host-Boundary-Preflight: [G07_HOST_BOUNDARY_PREFLIGHT_20260921.json](G07_HOST_BOUNDARY_PREFLIGHT_20260921.json)
- G07-Synthetic-B-Host-UI-Audit: [G07_SYNTHETIC_B_HOST_UI_AUDIT_20260922.json](G07_SYNTHETIC_B_HOST_UI_AUDIT_20260922.json)
- Current operational reconciliation: [CURRENT_OPERATIONAL_RECONCILIATION_20260922.json](CURRENT_OPERATIONAL_RECONCILIATION_20260922.json)
- G08/G09-Safety-/Provenance-Checkpoint: [CP_G08_G09_LOCAL_SAFETY_PROVENANCE_20260921.json](CP_G08_G09_LOCAL_SAFETY_PROVENANCE_20260921.json)
- G10-Stabilitäts-/Replay-Checkpoint: [CP_G10_STABILITY_REPLAY_20260921.json](CP_G10_STABILITY_REPLAY_20260921.json)
- G12-Final-Acceptance: [CP_G12_FINAL_ACCEPTANCE_20260921.json](CP_G12_FINAL_ACCEPTANCE_20260921.json)
- Kriterien- und Betriebsübersicht: [project-readiness.md](project-readiness.md)
- Einheitliches Sub-Dokument-Schema: [gate-template.md](gate-template.md)
- Ausführbarer driftfester Auftrag: [kgg-project-completion-goal-prompt.md](kgg-project-completion-goal-prompt.md)
- Brother-Handoff und Herkunftsregeln: [G11](11-brother-gpt-escalation.md)
