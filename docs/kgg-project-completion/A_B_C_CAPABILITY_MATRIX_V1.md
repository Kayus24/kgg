# G07 – A/B/C Capability Matrix v1

Stand: 2026-09-21
Fresh Main: `1e6c6e3e28603f28bfbad3b127c688e722c823f5`
Lokaler HEAD: `211d6a2677926839fa79ba69eb09ed1389e2aa3b`

Diese Matrix trennt die drei Surfaces. Ein Ergebnis auf A, B oder C wird nicht
auf eine andere Surface übertragen. `PASS` in dieser Datei bedeutet nur, dass
die jeweilige Capability-Zeile für die konkrete Surface nachweisbar ist; es ist
kein globaler G07-PASS.

## Evidence-Bindings

| Kürzel | Bedeutung | Evidence-Stufe |
| --- | --- | --- |
| `A-CANARY` | Custom-GPT-Chat führte genau einen read-only `getKggMainCommit`-Aufruf aus und gab die Fresh-Main-SHA `1e6c6e3e28603f28bfbad3b127c688e722c823f5` zurück. | E3_REAL_HOST |
| `B-G03` | Verbundene ChatGPT-App `KGG UI Lab Private`; genau ein read-only `get_current_state(actor=system)` mit `status=ready`, `main_sha=not_bound`; Tunnel-Client danach gestoppt. | E3_REAL_HOST |
| `C-STDIO` | Lokaler stdio-MCP-Initialize plus `get_current_state(actor=codex)`; Server `kgg-ui-lab` 1.0.0, `status=ready`, `main_sha=not_bound`. | E2_LOCAL_REAL_RUNTIME |
| `C-LOCAL` | Bestehende lokale G04/G06-Browser-, Flow- und Evidence-Prüfungen; sie belegen den lokalen Runner, nicht automatisch Codex-Host-Parität. | E2_LOCAL_REAL_RUNTIME |
| `CONFIG` | Read-only Editor-, Plugin- und Action-Konfiguration; Konfiguration allein ist kein Live-Nachweis. | E1_SYNTHETIC |

Statuswerte in der Tabelle: `PASS`, `PARTIAL`, `SYNTHETIC_ONLY`, `NOT_TESTED`,
`NOT_SUPPORTED`. `NOT_TESTED` bedeutet nicht „fehlt“, sondern „in diesem
Checkpoint nicht live nachgewiesen“.

## Capability-Matrix

| ID | Capability | A Custom GPT | B ChatGPT + Plugin | C Codex + Plugin | Evidence / Grenze |
| --- | --- | --- | --- | --- | --- |
| CAP-01 | Fresh Main/Projektkontext lesen | `PASS` | `NOT_TESTED` | `PARTIAL` | A-CANARY; C-STDIO liefert keinen gebundenen SHA |
| CAP-02 | Versionen/Manifeste/Source-Hinweise lesen | `PARTIAL` | `NOT_TESTED` | `PARTIAL` | CONFIG bzw. lokale Plugin-Quellen; kein gleicher Live-Reader |
| CAP-03 | Ticketanalyse und Minimalplan | `NOT_TESTED` | `NOT_TESTED` | `NOT_TESTED` | kein Surface-übergreifender Live-Fall in G07 |
| CAP-04 | Safety-/Scope-Klassifikation | `NOT_TESTED` | `NOT_TESTED` | `PARTIAL` | lokale KGG-Safety-/Skill-Evidence, kein gleicher Host-Canary |
| CAP-05 | Preview-Payload validieren | `NOT_TESTED` | `NOT_TESTED` | `NOT_TESTED` | Action-Konfiguration ist kein Ausführungstest |
| CAP-06 | Preview-Auto-Run starten und pollen | `NOT_TESTED` | `NOT_TESTED` | `NOT_TESTED` | externe Consequence nicht ausgeführt |
| CAP-07 | Main Gate/PR vorbereiten | `NOT_TESTED` | `NOT_TESTED` | `NOT_TESTED` | externe Consequence nicht ausgeführt |
| CAP-08 | Project Memory lesen | `NOT_TESTED` | `NOT_TESTED` | `NOT_TESTED` | kein G07-Live-Read |
| CAP-09 | Project Memory sicher schreiben | `NOT_TESTED` | `NOT_TESTED` | `NOT_TESTED` | Write-Gate nicht Bestandteil des Canarys |
| CAP-10 | Agentenkoordination lesen/schreiben | `NOT_TESTED` | `NOT_TESTED` | `NOT_TESTED` | kein G07-Live-Read |
| CAP-11 | Brother-GPT-Eskalation | `PARTIAL` | `PARTIAL` | `PARTIAL` | G11-Trockenlauf; keine neue Surface-Eskalation erforderlich |
| CAP-12 | Plugin Health/Version/Capabilities | `NOT_SUPPORTED` | `PARTIAL` | `PARTIAL` | B-G03 Tool-Health; C-STDIO Server/Tool-Health; A hat Actions statt Plugin-Health |
| CAP-13 | UI-Session starten/beenden | `NOT_TESTED` | `NOT_TESTED` | `SYNTHETIC_ONLY` | C-Server default in-memory; C-LOCAL ist separater Runner |
| CAP-14 | echten Screenshot aufnehmen | `NOT_TESTED` | `NOT_TESTED` | `SYNTHETIC_ONLY` | kein Screenshot aus B/C-Plugin-Host in diesem Lauf |
| CAP-15 | Koordinaten-Move/Click/Touch | `NOT_TESTED` | `NOT_TESTED` | `SYNTHETIC_ONLY` | kein Plugin-Host-Aktionsnachweis |
| CAP-16 | semantischer Click/Type | `NOT_TESTED` | `NOT_TESTED` | `SYNTHETIC_ONLY` | kein Plugin-Host-Aktionsnachweis |
| CAP-17 | Scroll/Swipe/Wait/Reload/Back | `NOT_TESTED` | `NOT_TESTED` | `SYNTHETIC_ONLY` | kein Plugin-Host-Aktionsnachweis |
| CAP-18 | visueller Screenshot-Regelkreis | `NOT_TESTED` | `NOT_TESTED` | `SYNTHETIC_ONLY` | lokale G05-Evidence nicht als C-Host-Evidence übernommen |
| CAP-19 | Quick Flows | `NOT_TESTED` | `NOT_TESTED` | `SYNTHETIC_ONLY` | lokale G06-Replays nicht als Plugin-Host-Evidence übernommen |
| CAP-20 | Device-/Viewportprofile | `NOT_TESTED` | `NOT_TESTED` | `SYNTHETIC_ONLY` | kein gleicher Host-Session-Nachweis |
| CAP-21 | Raw Evidence und Measurement | `PARTIAL` | `PARTIAL` | `PARTIAL` | A/B/C haben nur begrenzte bzw. lokale Evidence; keine vollständige Envelope |
| CAP-22 | unabhängiger Qualitätscheck | `NOT_TESTED` | `NOT_TESTED` | `PARTIAL` | vorhandene lokale Evaluator-Verträge, kein gleicher Real-Output |
| CAP-23 | Fault/Recovery/Replay | `NOT_TESTED` | `NOT_TESTED` | `PARTIAL` | C-LOCAL negative/replay Evidence; kein B/A-Replay |
| CAP-24 | Installation/Disable/Rollback | `NOT_TESTED` | `PARTIAL` | `PARTIAL` | B-App verbunden, aber Lifecycle nicht vollständig geprüft; C lokal installiert |
| CAP-25 | Fresh Main/Run-Status/Artifact lesen | `PASS` | `NOT_TESTED` | `PARTIAL` | A-CANARY nur Main-SHA; C kein gebundener Main-SHA |
| CAP-26 | Device-Test-Station anfordern und prüfen | `NOT_TESTED` | `NOT_TESTED` | `NOT_TESTED` | Consequence-Gate nicht ausgeführt |
| CAP-27 | Admin-Editor-Sync vorbereiten/PR | `NOT_TESTED` | `NOT_TESTED` | `NOT_TESTED` | Consequence-Gate nicht ausgeführt |
| CAP-28 | Patienten-Preview aus Admin anstoßen/prüfen | `NOT_TESTED` | `NOT_TESTED` | `NOT_TESTED` | keine Patientendaten; Consequence-Gate nicht ausgeführt |
| CAP-29 | Run-/Job-/Artifact-Reconciliation | `PARTIAL` | `NOT_TESTED` | `PARTIAL` | A action surface konfiguriert; C lokale Reconciliation; kein gleicher B-Nachweis |
| CAP-30 | Knowledge-/Action-/Source-Freshness prüfen | `PARTIAL` | `NOT_TESTED` | `PARTIAL` | CONFIG und lokale Manifest-/Hash-Prüfungen; kein gemeinsamer Live-Reader |

## G07-Entscheidung

```text
A_TOOL_CANARY=PASS
B_TOOL_DISCOVERY_AND_HEALTH=PASS_PARTIAL
C_LOCAL_PLUGIN_HEALTH=PASS_PARTIAL
A_B_C_FULL_PARITY=NOT_PROVEN
REAL_SCREENSHOT_FROM_B_OR_C_PLUGIN_HOST=NOT_PROVEN
REAL_ACTION_FROM_B_OR_C_PLUGIN_HOST=NOT_PROVEN
G07_STATUS=PASS
G07_SCOPE=surface_classification_only
```

Die G03-Evidence wird wiederverwendet; es wurde kein zweiter Tunnel- oder
Runtime-Key-Canary ausgeführt. `main_sha=not_bound` wird fail-closed behandelt
und nicht zu einem Fresh-Main-Nachweis aufgewertet.

Der aktuelle lokale Real-Bridge-Test
`python -B -m unittest release-pipeline/test_kgg_real_browser_bridge.py -v`
lief mit 8/8 Tests erfolgreich. Er bestätigt den lokalen Real-Browser- und
Visual-Loop-Code, hebt aber wegen der getrennten Host-Grenze keine B- oder
Codex-Host-Zeile auf `PASS`.

## Nächster Control-Gate-Schritt

G07 ist als Klassifikations-Gate `PASS`. Das bedeutet nicht, dass B oder C
bereits vollständige Screenshot-/Action-Producer sind: diese Capability-Zeilen
bleiben in der Matrix ausdrücklich `NOT_TESTED` oder `SYNTHETIC_ONLY`, weil der
aktuelle Transport keinen aktiven Real-Browser-Host-Hook besitzt. Die
Paritäts- und Real-Host-Grenzen bleiben für G05/G06/G08/G09 offen.

Der nächste Control-Gate-Schritt ist G08/G09 lokale Safety- und
Provenance-Härtung; ein neuer Runtime-Key oder Tunnel-Canary ist dafür nicht
erforderlich.

`PRODUCTION_CONTROL=PILOT_INCOMPLETE`
`A_B=NOT_COMPARABLE`
`replacement_eligible=false`

CONTRIBUTION_SOURCE=KGG_LEAD
REVIEW_STATUS=PENDING
