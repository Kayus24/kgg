# G01 Arbeitsmatrix – Custom GPT → universelles Plugin

Status: vorbereiteter Kandidat, noch nicht Gate-PASS.

Regel: `DOC` oder `SYNTHETIC` zählt nicht als Real-Host-Nachweis.

## 1. Ziel

Diese Matrix zerlegt die Migration so weit, dass ein kleineres Modell zeilenweise arbeiten kann. Jede Zeile endet mit genau einer Disposition und einem Akzeptanztest.

## 2. Warum dieses Gate erforderlich ist

Ohne eine explizite Matrix können vorhandene Custom-GPT-Funktionen vergessen oder UI-Lab-Attrappen irrtümlich als fertige Plugin-Funktion gewertet werden.

## 3. Scope und Nicht-Ziele

Erfasst werden derzeit bekannte produktive Fähigkeiten. Vor `PASS` muss die Matrix mechanisch gegen aktuelle Instructions, Resource Manifest, operationIds, Skills und Expected Results vollständig geprüft werden.

## 4. Abhängigkeiten

G00 und die in G01 genannten kanonischen Quellen.

## 5. Aktueller Stand

- `IMPLEMENTATION_STATUS=DRAFT_MATRIX`
- `LIVE_EVIDENCE_STATUS=MIXED`
- `GATE_STATUS=PARTIAL`
- `EVIDENCE_LEVEL=E1_SYNTHETIC`
- `LAST_VERIFIED_BASE_SHA=8d1193cbb19e5ec63f597aa8a2e29fd22687369f`
- `LAST_VERIFIED_AT=2026-09-21T10:02:47+02:00`

## 6. Bestehende Evidence

| ID | Fähigkeit | Aktuelle Quelle | Zielbaustein | A Custom GPT | B ChatGPT+Plugin | C Codex+Plugin | Aktuelle Lücke | Disposition | Pflichtnachweis |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CAP-01 | Fresh Main/Projektkontext lesen | Actions, Playbook | MCP read tool + Skill | `READY` | `NOT_TESTED` | `PARTIAL` | gemeinsamer Canary fehlt | `VERIFY` | derselbe SHA-Read pro Surface |
| CAP-02 | Versionen/Manifeste/Source-Hinweise lesen | Actions/Knowledge | MCP read tool + Skill | `READY` | `NOT_TESTED` | `PARTIAL` | Plugin-Transport B fehlt | `IMPLEMENT` | Fresh Resource Read mit Version |
| CAP-03 | Ticketanalyse und Minimalplan | Instructions/Knowledge | `kgg-supervisor`, `kgg-operations` | `READY` | `NOT_TESTED` | `PARTIAL` | Live-Parität fehlt | `VERIFY` | identischer synthetischer Ticketfall |
| CAP-04 | Safety-/Scope-Klassifikation | Knowledge/Safety | `kgg-safety` + Tool-Policy | `READY` | `NOT_TESTED` | `PARTIAL` | Real-Browser-Policy fehlt | `FIX` | erlaubter + verweigerter Zugriff |
| CAP-05 | Preview-Payload validieren | GitHub Action | MCP/Action-Adapter | `READY` | `NOT_TESTED` | `NOT_TESTED` | universeller Toolzugriff fehlt | `VERIFY` | validate-only ohne Write |
| CAP-06 | Preview-Auto-Run starten und pollen | GitHub Actions | Remote MCP action | `READY` | `NOT_TESTED` | `NOT_TESTED` | Consequence-/Authpfad fehlt | `DEFER_WITH_REASON` | autorisierter Preview-Canary |
| CAP-07 | Main Gate/PR vorbereiten | GitHub Actions | Remote MCP action | `READY` | `NOT_TESTED` | `NOT_TESTED` | externe Konsequenz | `DEFER_WITH_REASON` | separater PR-/Merge-Gate-Test |
| CAP-08 | Project Memory lesen | Memory Actions | MCP read tool + Skill | `READY` | `NOT_TESTED` | `NOT_TESTED` | Auth/Plugintransport | `IMPLEMENT` | index + genau ein Pack |
| CAP-09 | Project Memory sicher schreiben | Memory Action | Remote MCP action | `PARTIAL` | `NOT_TESTED` | `NOT_TESTED` | Konflikt-/Write-Gate | `DEFER_WITH_REASON` | konfliktfreier synthetischer Record |
| CAP-10 | Agentenkoordination lesen/schreiben | Coordination Actions | MCP tools + Skill | `PARTIAL` | `NOT_TESTED` | `NOT_TESTED` | Host-/Queue-Vertrag | `VERIFY` | read-only + autorisierter Eventfall |
| CAP-11 | Brother-GPT-Eskalation | Prozess/Skill | `kgg-escalation` | `PARTIAL` | `PARTIAL` | `PARTIAL` | dokumentierte End-to-End-Übernahme fehlt | `FIX` | G11-Trockenlauf mit Self-Review |
| CAP-12 | Plugin Health/Version/Capabilities | fehlt als universeller Canary | MCP read tool | `MISSING` | `MISSING` | `PARTIAL` | standardisierter Healthpfad fehlt | `IMPLEMENT` | Tool Discovery + Versionsantwort |
| CAP-13 | UI-Session starten/beenden | synthetischer MCP | MCP real runner | `MISSING` | `MISSING` | `SYNTHETIC_ONLY` | echte Host-/Runnerbindung fehlt | `IMPLEMENT` | echte Session/Lease/Lifecycle |
| CAP-14 | echten Screenshot aufnehmen | synthetischer MCP | MCP browser tool | `MISSING` | `MISSING` | `SYNTHETIC_ONLY` | real capture fehlt | `IMPLEMENT` | re-hashbarer Browser-Screenshot |
| CAP-15 | Koordinaten-Move/Click/Touch | nicht exponiert | MCP browser tool | `MISSING` | `MISSING` | `MISSING` | Tool und Runnerpfad fehlen | `IMPLEMENT` | sichtbare Zustandsänderung |
| CAP-16 | semantischer Click/Type | Playwright-Smokes intern | MCP browser tool | `MISSING` | `MISSING` | `MISSING` | vorhandene Runnerlogik nicht exponiert | `IMPLEMENT` | Locator-Aktion + Nachzustand |
| CAP-17 | Scroll/Swipe/Wait/Reload/Back | teilweise Playwright intern | MCP browser tool | `MISSING` | `MISSING` | `MISSING` | Toolvertrag fehlt | `IMPLEMENT` | je Operation positiver/negativer Test |
| CAP-18 | visueller Screenshot-Regelkreis | ursprüngliches UI-Lab-Ziel | Skill + MCP browser tools | `MISSING` | `MISSING` | `MISSING` | G04/G05 fehlen | `IMPLEMENT` | Screenshot A → Aktion → Screenshot B |
| CAP-19 | Quick Flows | synthetischer MCP | Skill + versionierter Runner | `MISSING` | `MISSING` | `SYNTHETIC_ONLY` | echte Flows fehlen | `IMPLEMENT` | drei reale Flows + Fallback |
| CAP-20 | Device-/Viewportprofile | UI-Lab-Contract | MCP browser session | `MISSING` | `MISSING` | `SYNTHETIC_ONLY` | Realbrowser-Bindung fehlt | `IMPLEMENT` | Phone/Tablet-Profilnachweis |
| CAP-21 | Raw Evidence und Measurement | Measurement + Raw Capture | vorhandene Envelope/Provenance | `PARTIAL` | `MISSING` | `PARTIAL` | Browser-Evidence fehlt | `FIX` | Raw Screenshot/Event → Evidence Ref |
| CAP-22 | unabhängiger Qualitätscheck | Measurement Contracts | Evaluator-Harness | `PARTIAL` | `NOT_TESTED` | `PARTIAL` | Realoutput-Bindung fehlt | `FIX` | sichtbarer Output, kein Self-Score |
| CAP-23 | Fault/Recovery/Replay | Test Batteries | `kgg-testing` + Harness | `PARTIAL` | `NOT_TESTED` | `PARTIAL` | Real-Bridge-Fälle fehlen | `FIX` | Negative Matrix + unchanged replay |
| CAP-24 | Installation/Disable/Rollback | Plugin Distribution | Plugin Lifecycle | `NOT_APPLICABLE` | `MISSING` | `PARTIAL` | ChatGPT-Lifecycle fehlt | `IMPLEMENT` | install, discover, disable, reinstall |
| CAP-25 | Fresh Main/Run-Status/Artifact lesen | `getKggMainCommit`, Run-/Artifact-Actions | MCP read tools + Skill | `READY` | `NOT_TESTED` | `PARTIAL` | gemeinsamer read-only Transport fehlt | `VERIFY` | SHA/Run/Artifact-Read je Surface |
| CAP-26 | Device-Test-Station anfordern und prüfen | `submitKggDeviceTest`, `listKggDeviceTestRuns` | Remote action adapter | `READY` | `NOT_TESTED` | `NOT_TESTED` | externe Consequence/Auth-Grenze | `DEFER_WITH_REASON` | autorisierter synthetischer Device-Canary |
| CAP-27 | Admin-Editor-Sync vorbereiten/PR | Admin-Editor Actions | Remote action adapter | `READY` | `NOT_TESTED` | `NOT_TESTED` | PR-/Merge-Gate | `DEFER_WITH_REASON` | validate-only ohne Merge |
| CAP-28 | Patienten-Preview aus Admin anstoßen/prüfen | Patient Preview Actions | Remote action adapter | `READY` | `NOT_TESTED` | `NOT_TESTED` | Patient-/Release-Gate | `DEFER_WITH_REASON` | nur synthetische Preview mit explizitem Gate |
| CAP-29 | Run-/Job-/Artifact-Reconciliation | `getKggPreviewGateRun`, Jobs, Artifacts, Status | MCP read tools + Skill | `READY` | `NOT_TESTED` | `PARTIAL` | B-Transport fehlt | `VERIFY` | identische run_id bis Terminalstatus |
| CAP-30 | Knowledge-/Action-/Source-Freshness prüfen | Resource Manifest + Bootstrap | Skill + read tools | `READY` | `NOT_TESTED` | `PARTIAL` | universeller Manifest-Reader fehlt | `IMPLEMENT` | Hash-/Version-Drift fail-closed |

## 7. Lücke und Root Cause

Die schwerwiegendsten offenen Zeilen sind CAP-12 bis CAP-20. Sie bilden den fehlenden Transport-, Real-Browser- und Quick-Flow-Pfad. CAP-21 bis CAP-23 dürfen erst dann als Real-Evidence-Gates gelten.

### 7.1 Kanonische Source-Coverage

| Quelle | Aktueller Nachweis | Matrixabdeckung |
| --- | --- | --- |
| `docs/kgg-custom-gpt-goal-prompt.md` | gelesen, Produkt-/Safety-/Action-/Workflow-Ziel | CAP-01–CAP-24 |
| `docs/kgg-ui-lab-v1-goal-prompt.md` | gelesen, ursprünglicher Real-UI-Lab-Scope | CAP-13–CAP-20 |
| `docs/kgg-custom-gpt-editor-bootstrap.md` | gelesen, Editor-/Knowledge-/Action-Bootstrap | CAP-02, CAP-24, CAP-30 |
| `docs/kgg-custom-gpt-resource-manifest.json` | gelesen, vier Knowledge-Dateien und zwei Action-Schemas; Resource-Audit-Self-Test grün | CAP-02, CAP-08, CAP-30 |
| `docs/kgg-custom-gpt-action-api-openapi.yaml` | 30 `operationId`s einzeln unten abgebildet | CAP-01, CAP-02, CAP-05–CAP-10, CAP-25–CAP-30 |
| `docs/kgg-custom-gpt-action-schema.md` | gelesen, Action-/Safety-Grenzen | CAP-04–CAP-07, CAP-30 |
| `kgg-plugin/.codex-plugin/plugin.json` | gelesen, Plugin-Metadaten/Skills/MCP | CAP-03, CAP-12–CAP-24 |
| `kgg-plugin/.mcp.json` | gelesen, lokaler stdio-MCP-Transport | CAP-12–CAP-20 |
| `kgg-plugin/mcp/server.py` | 10 synthetische UI-Lab-Tools; Realstatus explizit belegt | CAP-12–CAP-20 |
| `kgg-plugin/skills/**/SKILL.md` | fünf Skills: supervisor, operations, safety, testing, escalation | CAP-03, CAP-04, CAP-10, CAP-11, CAP-23 |

### 7.2 Action-operationId-Abdeckung

| operationId | Matrixzeile | Disposition |
| --- | --- | --- |
| `getKggMainCommit` | CAP-01, CAP-25 | `VERIFY` |
| `submitKggReadOnlyValidation` | CAP-05 | `VERIFY` |
| `listKggReadOnlyValidationRuns` | CAP-25, CAP-29 | `VERIFY` |
| `submitKggPreviewAuto` | CAP-06 | `DEFER_WITH_REASON` |
| `submitKggDeviceTest` | CAP-26 | `DEFER_WITH_REASON` |
| `listKggDeviceTestRuns` | CAP-26 | `VERIFY` |
| `submitKggMainGate` | CAP-07 | `DEFER_WITH_REASON` |
| `listKggMainGateRuns` | CAP-25, CAP-29 | `VERIFY` |
| `listKggPreviewAutoRuns` | CAP-25, CAP-29 | `VERIFY` |
| `getKggPreviewGateRun` | CAP-29 | `VERIFY` |
| `getKggPreviewGateJobs` | CAP-29 | `VERIFY` |
| `getKggPreviewGateArtifacts` | CAP-29 | `VERIFY` |
| `submitKggAdminEditorSyncPreflight` | CAP-27 | `DEFER_WITH_REASON` |
| `submitKggAdminEditorSyncSnapshotPr` | CAP-27 | `DEFER_WITH_REASON` |
| `submitKggPatientPreviewFromAdmin` | CAP-28 | `DEFER_WITH_REASON` |
| `listKggPatientPreviewRunsFromAdmin` | CAP-28, CAP-29 | `VERIFY` |
| `getKggMemoryIndex` | CAP-08 | `IMPLEMENT` |
| `getKggMemoryPack` | CAP-08 | `IMPLEMENT` |
| `getKggMemoryRecord` | CAP-08 | `IMPLEMENT` |
| `getKggMemoryHistory` | CAP-08 | `IMPLEMENT` |
| `getKggAgentCoordinationIndex` | CAP-10 | `VERIFY` |
| `getKggAgentCoordinationThread` | CAP-10 | `VERIFY` |
| `getKggAgentCoordinationBridgeTask` | CAP-10 | `VERIFY` |
| `submitKggAgentCoordinationEvent` | CAP-10 | `DEFER_WITH_REASON` |
| `listKggAgentCoordinationRuns` | CAP-10 | `VERIFY` |
| `submitKggMemoryUpdate` | CAP-09 | `DEFER_WITH_REASON` |
| `listKggMemoryUpdateRuns` | CAP-09 | `VERIFY` |
| `getKggMemoryUpdateRun` | CAP-09 | `VERIFY` |
| `getKggMemoryUpdateStatus` | CAP-09 | `VERIFY` |
| `getKggMemoryUpdateArtifacts` | CAP-09 | `VERIFY` |

`operationId`-Vollständigkeit ist damit eine mechanisch prüfbare G01-Bedingung; der Resource-Audit verwendet kanonische LF-normalisierte SHA-256-Werte. Die Disposition `VERIFY` oder `DEFER_WITH_REASON` bedeutet nicht, dass die Funktion bereits im Plugin live parity-fähig ist.

## 8. Kleinschrittiger Arbeitsplan

1. Matrix gegen aktuelle operationIds und Skills auf fehlende Zeilen prüfen. ✅ alle 30 operationIds einzeln abgebildet.
2. Resource-Manifest-SHA-/Existenzprüfung und Payload-Preflight-Self-Test ausführen. ✅ beide grün.
3. CAP-12 abschließen.
4. CAP-13 bis CAP-17 als kleinsten Real-Runner-Pfad umsetzen.
5. CAP-18 und CAP-19 darauf aufbauen.
6. CAP-20 bis CAP-23 anbinden.
7. CAP-01 bis CAP-11 je Surface live verifizieren.
8. CAP-24 nach G02/G03 abschließen.

## 9. CONTROL_LOOP_GATE

- `GATE_ID=G01A_MATRIX_COMPLETENESS`
- `INPUT=Instructions, Resource Manifest, Actions, Skills, Expected Results, UI-Lab-Goal`
- `PROCEDURE=jede Quelle gegen Matrix-IDs abgleichen; Duplikate zusammenführen; fehlende Fähigkeit ergänzen`
- `PASS_CRITERIA=Jede benötigte Fähigkeit und jede aktuelle operationId besitzt Zielbaustein, A/B/C-Status, Disposition und Pflichtnachweis`
- `FAIL_CRITERIA=unzugeordnete operationId, Skill-Funktion oder Custom-GPT-Pflichtfähigkeit`
- `RETRY_RULE=ein gezielter Read der unklaren Quelle`
- `FALLBACK=UNKNOWN-Zeile statt Annahme`
- `EVIDENCE_OUTPUT=CAPABILITY_MIGRATION_MATRIX_V1`
- `NEXT_ON_PASS=G02`
- `NEXT_ON_FAIL=G11`
- `INVALIDATION_TRIGGERS=Instructions, Manifest, Actions, Skills oder UI-Lab-Vertrag ändern sich`

## 10. Tests

- operationId-Liste gegen Matrix.
- Skill-Liste gegen Matrix.
- Resource-Manifest-Komponenten gegen Matrix.
- Negativ: CAP-14/CAP-19 dürfen bei Synthetic-only nicht READY werden.

## 11. Safety und Datenschutz

Keine Capability darf über weitergehende Rechte migriert werden als ihre Quelle. Browserfähigkeiten verwenden ausschließlich synthetische Testdaten.

## 12. Brother-GPT-Eskalation

Nur für eine einzelne unklare Matrixzeile mit konkreter Architekturfrage; kein gesamtes Re-Audit bei jedem Eintrag.

## 13. Abschlussartefakte

Vollständige, reviewte Matrix sowie verknüpfte Tests und Detailgates.

## 14. Beitragsherkunft

`CONTRIBUTION_SOURCE=HUMAN_AND_CODEX`, `REVIEW_STATUS=PENDING`.
