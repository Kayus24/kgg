# VERBINDLICHER ZIELAUFTRAG

## KGG UI Lab V1 + Plugin-Candidate + Custom-GPT-Control

Dieser Auftrag integriert den bisherigen UI-Lab-/Custom-GPT-Zielauftrag mit
der neuen Plugin-Perspektive. Er ersetzt nicht die bestehenden Gates und ist
noch kein Nachweis, dass der Plugin-Candidate bereits produktionsfähig ist.

## Oberziel

Baue und vergleiche eine gemeinsame KGG-Agenteninfrastruktur, in der:

- das UI Lab die deterministische Test-Runtime für Browser, später Android,
  Sessions, Quick Flows und Evidenz bleibt;
- ein KGG-Plugin-Candidate die wiederverwendbare Agenten-/Workflow-Schicht aus
  Skills und kontrollierten MCP-Tools bildet;
- der bestehende KGG Custom GPT zunächst die Production-Control und der
  begrenzte Codex-Ersatz für kleine Admin-Tickets bleibt;
- Codex + Plugin später als dritte Vergleichsoberfläche geprüft werden kann;
- ein Bruder-GPT ausschließlich als begrenzter, nicht-leitender Fallback-Berater
  über den bestehenden Handoff-/Browser-Relay-Weg eingebunden wird.

Die zentrale Frage lautet nicht „Plugin statt Custom GPT um jeden Preis“,
sondern: Welche Oberfläche nutzt dieselbe KGG-Infrastruktur am zuverlässigsten,
und kann die Plugin-Schicht gleichzeitig ChatGPT und Codex verbessern?

## Unveränderliche Grenzen

- Fresh Main, Manifest, Knowledge-/Action-Hashes und realer Editorstatus werden
  vor jedem Vergleich neu ermittelt; historische Werte sind nur Baseline-
  Evidenz.
- Repository, Tickets, Projekt-Memory und Testresultate behalten jeweils ihre
  bestehende Source of Truth. Keine doppelte Statusdatenbank.
- Nur synthetische Daten; keine echten Patienten-, Praxis-, Browserroh- oder
  Geheimdaten an andere GPTs oder Tools übertragen.
- UI Lab und Plugin dürfen Main, Live, Patient-Live, PR, Merge oder Editor-
  Änderungen niemals an den bestehenden Human-Gates vorbei ausführen.
- Skills dokumentieren Regeln, sind aber keine Sicherheitsgrenze. Actor-,
  Lease-, SHA-, Replay-, Berechtigungs-, Evidence- und Release-Gates bleiben in
  der Runtime bzw. am vertrauenswürdigen MCP-/Workflow-Rand.
- Der Bruder-GPT ist kein Lead, darf keine weiteren GPTs rekursiv öffnen, keine
  Tests entfernen, keine Hashes oder Gates schwächen und keinen Write auslösen.
- Ein echter externer GPT-Versand oder Editor-/Ticket-Write ist eine eigene,
  unmittelbar zu bestätigende Aktion.

## Verbindliche Testschleife für jeden Schritt

1. Ausgangszustand und erwartetes Verhalten mit Fresh-State festhalten.
2. Reproduzierbaren roten Test oder belegten Ist-Zustand erzeugen.
3. Root Cause und betroffene Schicht bestimmen.
4. Kleinste Änderung umsetzen.
5. Engsten Test grün ausführen.
6. Change-aware Regression und danach vollständiges Critical-Gate ausführen.
7. Den ursprünglichen Fall ohne Änderungen unverändert wiederholen.
8. Laufzeit, Reads, Actions, Retries, Fehlerklasse und Evidenz dokumentieren.
9. Erst bei vollständigem Nachweis zur nächsten Phase gehen.

Vor jedem externen Production-Control-Lauf ist lokal der deklarative
Preflight `release-pipeline/kgg_production_control_preflight.py` gegen
`docs/kgg-ui-lab-v1-production-control-readonly-contract.json` auszuführen.
Das Profil muss ausdrücklich gewählt werden: `baseline_no_dispatch` für den
Kontrolllauf oder `read_only_validation_runner` nur bei separat bestätigtem
Read-only-Runner-Dispatch. Fehlt eine erforderliche Action, liegt eine
Schemaüberschneidung vor oder fehlt die datierte externe Editorbeobachtung,
stoppt der Preflight vor dem Modellstart. Ein GPT darf den realen
Editorstatus nicht durch statische Repository-Dateien ersetzen.

Round 2 darf keine Änderung an Code, Skill, Knowledge, Schema, Test,
Expected-Result oder Harness enthalten. Bei einer Abweichung beginnt Round 1
neu.

## Phasen und Reihenfolge

### Phase 0A – Canonical Freeze

- `git status`, Branch, HEAD und frisch abgefragtes `origin/main` erfassen.
- Relevante Architektur-, Safety-, Rollen-, Action-, Memory-, Preview- und
  Testdokumente sowie Editor-Snapshots lesen.
- Für jede bestehende Komponente `KEEP | IMPROVE | MERGE | REPLACE | REMOVE`
  begründen.
- Den Goal-Text selbst im Repository versionieren; der Editorstatus bleibt eine
  getrennte externe Wahrheit.

### Phase 0B – #180 Control-Baseline

Ticket #180 (`tablet-splitter-scale-drag`) bleibt der vorläufige Benchmark,
aber sein historischer SHA-/Fehlerbefund wird nicht als aktuell angenommen.
Gegen den frisch ermittelten Main-SHA wird der bestehende Ablauf unverändert
reproduziert und gemessen:

- Ergebnisqualität und Root-Cause-Qualität;
- Reads, Kontextmenge und Rückfragen;
- Action-Aufrufe, Dispatches, Duplikate und Retries;
- Laufzeit, Fehlerklasse, Testauswahl und Belegqualität.

Dieser Lauf ist der Control-Punkt für Custom GPT, Plugin-Candidate und später
Codex + Plugin. Kein Fix, kein Dispatch, kein Ticket-Write ist Teil der
Baseline.

### Phase 1 – Gemeinsame Contracts und Plugin-Mapping

Die bestehenden UI-Lab-Contracts bleiben Grundlage. Ergänzend entsteht eine
Mapping-Tabelle ohne neue Produktregeln:

| Bestehend | Plugin-Candidate |
| --- | --- |
| Custom-GPT-Core/Bootstrap | `skills/kgg-supervisor/SKILL.md` |
| Knowledge Architecture | `references/architecture/` + Skill |
| Knowledge Operations | `skills/kgg-operations/` |
| Knowledge Safety | Skill-Hinweise + serverseitige Gates |
| Knowledge Testing | `skills/kgg-testing/` |
| Actions/OpenAPI | MCP-Tool-Schemas |
| GitHub-/Memory-Reads | bestehender Gateway, zunächst read-only |
| UI-Lab-API | MCP-UI-Lab-Adapter |
| Repair-/Stabilization-Lab | Plugin-Eval-/Regression-Harness |
| Bruder-Handoff | `skills/kgg-escalation/` + `handoff-v2` |
| Source Chunks | kanonische Repo-Daten |

Zusätzliche Negativtests decken `skill_missing`, Versions-/Hash-Drift,
`mcp_unavailable`, `mcp_auth_denied`, `mcp_stale_main`,
`duplicate_tool_request`, `hook_reject`, Capability-Drift und
surface-spezifische Nichtverfügbarkeit ab.

### Phase 2 – Minimaler Plugin-Candidate

Erzeuge ein lokales, validierbares Skelett:

```text
kgg-plugin/
├── .codex-plugin/plugin.json
├── skills/
│   ├── kgg-supervisor/
│   ├── kgg-operations/
│   ├── kgg-testing/
│   ├── kgg-safety/
│   └── kgg-escalation/
├── references/
├── scripts/eval/
└── mcp/
```

Jede Skill-/Reference-Datei nennt ihre bestehende kanonische Quelle und einen
Hash. Zuerst werden nur `current_state`, `ticket_plan` und `safe_canary` als
exakte, lokale `read_only`-Paritäts-Fixtures gespiegelfähig gemacht. Diese drei
Namen sind in Phase 2 bewusst noch keine zusätzlichen MCP-Tools; die einzige
initiale MCP-Oberfläche ist die explizite Liste in Phase 3. Noch keine
Produktmigration und keine neue Write-Logik.

### Phase 3 – MCP-/Skill-Integration

Expose zunächst nur dünne, read-only bzw. preview-sichere Werkzeuge:

`get_current_state`, `get_ticket_state`, `start_ui_session`,
`set_device_profile`, `run_quick_flow`, `capture_screenshot`,
`run_width_sweep`, `get_test_evidence`, `get_session_status`.

Jede Operation führt serverseitig Schema-, Actor-, Lease-, SHA-, Replay-,
Capability-, Timeout- und Evidence-Prüfungen aus. Schreiben, Dispatch,
Editor-Sync und Patient-Live bleiben separate, bestehende Gates.

### Phase 4 – UI-Lab-Runtime

Das UI Lab bleibt unterhalb des Plugins und wird nicht in Skills dupliziert:

```text
KGG Plugin / Custom GPT / Codex + Plugin
                 │ semantische Tool-Aufrufe
                 ▼
          UI-Lab-MCP-Adapter
                 ▼
          UI-Lab-Runtime
       SessionStore / RunnerRegistry
       QuickFlowRegistry / Actor-Lease
       SHA-Replay / Evidence / Fallback
                 ▼
          Browser, später Android
```

Die Runtime erhält zuerst den minimalen Browser-Runner für Admin-/Patient-
Preview, Screenshot, Klick/Tap, Text, Scroll, Reload, Back, begrenztes Wait
und Tab-S9-/Oppo-/freies Viewportprofil. Quick Flows referenzieren nur
semantische Labels; Selektoren bleiben Runner-Interna.

Genau drei Quick Flows werden zuerst zertifiziert:

1. Admin-App starten und Ausgangszustand prüfen.
2. Pilotbereich öffnen und #180-Verhalten reproduzieren.
3. Admin-/Patient-Preview mit ausschließlich synthetischem QR-Bild koppeln.

Jeder Flow hat nummerierte Schritte, Vorbedingungen, erwarteten Zustand,
relevante Screenshots, PASS-/FAIL-Grund und Cleanup.

### Phase 5 – Agent Candidate Comparison

Drei getrennte Läufe bearbeiten denselben synthetischen Auftrag:

- A: bestehender Custom GPT (Control);
- B: KGG Plugin-Candidate;
- C: Codex + KGG Plugin, sofern die Oberfläche verfügbar ist.

Der Custom GPT bleibt im Codex-Ersatzmodus auf kleine, klar abgegrenzte
Admin-Tickets beschränkt: Fresh Main/Manifest lesen, begrenzten Kontext laden,
Root Cause bestimmen, modularen Payload erzeugen, `validate_only`, genau einen
Preview-Dispatch, Run/Artefakte prüfen, UI-Lab-Flow ausführen und am Human-Gate
stoppen. Große Refactorings oder freie Terminalarbeit werden nicht versprochen.

### Phase 6 – Fallback-Leiter

Fehlerklassen bleiben die elf bestehenden Klassen. Reihenfolge:

1. Fresh Context, Status und Belege lesen.
2. Bei Timeout/HTTP-Fehlern per Request-ID und SHA reconciliieren.
3. Einen materiell anderen technischen Ansatz versuchen.
4. Nach zwei gescheiterten Ansätzen, widersprüchlichen Belegen oder `unknown`
   einen Bruder-Handoff vorbereiten.
5. Bei persistierender Fehlerklasse alle Writes stoppen und Blocker belegen.

Der Handoff bleibt `handoff-v2`, bereinigt, gehasht und zunächst lokal. Ein
Bruder darf Diagnose, kleine Fixpläne, zusätzliche Tests, Reihenfolge und
taktische Goal-Änderungen vorschlagen. Protected Änderungen liefern nur
`MAX_REQUIRED`; der Lead darf sie nicht automatisch übernehmen.

### Phase 7 – A/B und Fault Injection

Custom GPT, Plugin und Codex + Plugin werden auf identischem Auftrag verglichen.
Zusätzlich werden Browser-Timeout, Broker-Neustart, Runner-Abbruch, doppelte
Request-ID, stale Main, fehlendes Screenshot, widersprüchliche Belege,
fehlender Bruder, ungültige Bruder-Antwort, MCP-/Hook-Ausfall und unerlaubte
Goal-Erweiterung injiziert.

### Phase 8 – Stabilisierung

Nach vollständigem Grün: Round 1, keine Änderungen, identische Round 2. Beide
Runden müssen inklusive Plugin-/UI-Lab-/Fallback-Contracts grün sein. Eine neue
Fehlerklasse oder Abweichung setzt Round 1 zurück.

### Phase 9 – Migration Gate

Der Custom GPT wird erst dann Legacy/Fallback, wenn alle fünf unabhängigen Gates
belegt sind:

- `PARITY_PASS` – heutige relevante Supervisor-Funktionen vorhanden;
- `SAFETY_PASS` – kein Gate schwächer;
- `EFFICIENCY_PASS` – messbarer Vorteil ohne Qualitätsverlust;
- `CROSS_SURFACE_PASS` – benötigte Funktionen in ChatGPT und Codex belegt;
- `STABILITY_PASS` – Fault Injection plus unveränderte Round 1/2 grün.

Bis dahin bleibt:

```text
Custom GPT = Production-Control / Fallback
Plugin      = Candidate
UI Lab      = gemeinsame Runtime
Codex       = optionale Entwicklungsoberfläche
```

## Abschlusskriterien

`COMPLETE` ist erst erlaubt, wenn der ursprüngliche UI-Lab-Zielauftrag und die
Plugin-Erweiterung gemeinsam nachgewiesen sind: alle Contracts/Negativtests,
drei reproduzierbare Quick Flows, aktueller #180-Pilot zweimal unverändert
grün, kein Duplicate Dispatch, sicher simulierter Bruder-Fallback,
nachweislich blockierte unerlaubte Goal-Änderung, synthetische Daten,
unveränderte Preview-/Main-/Patient-Gates, vollständige Messwerte sowie
`PARITY_PASS`, `SAFETY_PASS`, `EFFICIENCY_PASS`, `CROSS_SURFACE_PASS` und
`STABILITY_PASS`. Kein Main-, Live- oder Patient-Release ist Bestandteil dieses
Auftrags.
