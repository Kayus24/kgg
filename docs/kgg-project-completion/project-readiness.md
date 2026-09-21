# KGG – Betriebsfähigkeit und Erfüllungskriterien

## Zweck und Autorität

Dieses Dokument ist die kompakte Arbeitsansicht für die Frage: **Welche
Voraussetzungen müssen erfüllt sein, damit das KGG-Projekt zuverlässig läuft
und als abgeschlossen gelten darf?**

Es definiert keine zweite Statusquelle. Die aktuelle Wahrheit steht in
[`gate-status.json`](gate-status.json); der Master beschreibt Reihenfolge und
Abschlussregeln in [`README.md`](README.md). Dieses Dokument erklärt die
Kriterien, den aktuellen Erfüllungsgrad und verweist auf genau ein
Detaildokument je Punkt.

Historische Chats, alte Runs und frühere SHAs ersetzen keine Fresh-Evidence.
Bei Widerspruch gilt Fresh Main plus `gate-status.json`.

## Was „läuft“ und was „vollständig abgeschlossen“ bedeutet

### Mindest-Betriebsfähigkeit

Der lokale KGG-Pfad gilt erst als betriebsfähig, wenn mindestens folgende
Fähigkeiten real nachgewiesen sind:

1. das versionierte Plugin-Paket kann installiert und geladen werden;
2. eine erlaubte KGG-HTML-Testseite kann über eine echte Browsergrenze geöffnet
   werden;
3. ein echter Screenshot wird zurückgegeben;
4. mindestens eine echte semantische oder Koordinaten-Aktion verändert die
   Seite;
5. ein zweiter Screenshot oder eine unabhängige Zustandsprüfung bestätigt die
   Änderung;
6. Safety-, Lease-, Domain- und Schrittgrenzen greifen fail-closed;
7. Raw-Evidence ist Run-/Session-gebunden, erneut hashbar und nicht aus
   Model-Self-Reports erzeugt.

### Vollständiger Projektabschluss

Für `PROJECT_COMPLETE` müssen zusätzlich alle G00–G12 final klassifiziert,
die Custom-GPT-, normale-ChatGPT-Plugin- und Codex+Plugin-Surfaces ehrlich
bewertet, die erforderlichen Test- und Replay-Loops grün sowie Release,
Rollback und Betriebsdokumentation abgeschlossen sein. Eine nicht zugängliche
externe Hostgrenze darf als dokumentiertes `NOT_OBSERVABLE` enden; sie darf
aber keine fehlende Kernfunktion wie echte Browseraktionen kaschieren.

## Kriterienregister

Statuswerte sind aus dem Register zu lesen und werden hier nur erklärt:

`PASS` = Kriterium mit geforderter Evidence erfüllt · `PARTIAL` = verwertbare
Teile vorhanden, Pflichtlücke bleibt · `FAIL` = vorhandene Implementierung
widerspricht dem Kriterium · `BLOCKED` = genau eine externe Voraussetzung oder
ein Consequence Gate fehlt · `UNKNOWN` = autoritative Prüfung fehlt ·
`NOT_APPLICABLE` = nachweislich nicht relevant.

| Punkt | Muss erfüllt sein | Gate-Kriterium / Control Loop | Aktueller Stand | Nächster zulässiger Schritt | Detail |
| --- | --- | --- | --- | --- | --- |
| G00 | Eine Fresh-Baseline, eine Statusquelle und Resume-Checkpoints existieren. | Fresh Main, Master, Register und aktives Detaildokument stimmen überein; genau ein nächster Schritt. | `PASS` | Bei Status-/Quellenänderung gezielt neu binden. | [G00](00-governance-and-source-of-truth.md) |
| G01 | Alle benötigten Custom-GPT-Fähigkeiten sind inventarisiert und einem Plugin-Baustein, Test und Endstatus zugeordnet. | Keine Capability-Zeile bleibt ohne Owner, Test oder Disposition. | `PASS` | Nur bei neuer Capability ergänzen. | [G01](01-custom-gpt-capability-migration.md) |
| G02 | Das Plugin ist versioniert, portabel und installierbar. | Installation aus dem vorgesehenen Paket; keine lokale Pfadannahme; Manifest und Marketplace konsistent. | `PARTIAL` | Transport- und Hostvoraussetzungen für G03/G04 klären. | [G02](02-universal-plugin-package.md) |
| G03 | Normales ChatGPT entdeckt das Plugin und ruft mindestens ein read-only Tool auf. | Fresh Discovery plus echter read-only Tool-Canary mit E3-Evidence. | `BLOCKED` | Genau einen autorisierten HTTPS-/Secure-MCP-Endpunkt bereitstellen, danach Discovery erneut prüfen. | [G03](03-chatgpt-plugin-connection.md) |
| G04 | Eine echte, isolierte Browserbrücke steuert die erlaubte KGG-Testseite. | Session → Open → Screenshot A → echte Aktion → Screenshot/Zustand B → End; alles run-gebunden. | `PASS` (E2 lokal) | G05 visuellen Agentenloop und G06 drei reale Flows binden; E3-Host-Parität bleibt separat. | [G04](04-real-browser-bridge.md) |
| G05 | Der visuelle Regelkreis funktioniert. | GPT wertet Screenshot A aus, führt genau eine Aktion aus und bestätigt den geänderten Zustand anhand B; kein behaupteter Erfolg ohne Runner-Evidence. | `BLOCKED` | Erst G04 real bestehen. | [G05](05-visual-interaction-loop.md) |
| G06 | Mindestens drei Quick Flows laufen real und versioniert. | Jeder Schritt hat Assertion, Evidence und visuellen Fallback; stale Flows stoppen fail-closed. | `PARTIAL` | Flows an die reale Browserbrücke binden. | [G06](06-real-quick-flows.md) |
| G07 | A/B/C sind getrennt und ehrlich klassifiziert. | Keine Capability wird von einer Surface auf eine andere übertragen; pro Surface eigener Canary oder `NOT_SUPPORTED`. | `PARTIAL` | Nach G03/G04/G06 unabhängige Canaries durchführen. | [G07](07-surface-integration.md) |
| G08 | Safety und Autorisierung begrenzen den Realpfad. | Domain-Allowlist, Lease, Limits, Sanitization und Negativtests blockieren unzulässige Aktionen. | `PARTIAL` | Browser-spezifische Negativtests am Realpfad ergänzen. | [G08](08-security-privacy-and-authorization.md) |
| G09 | Jede Messung ist provenance-first. | Raw Evidence, Hash, Run-ID, Surface, Base-SHA und Field-Provenance sind re-hashbar; unbekannt bleibt `NOT_MEASURED`. | `PARTIAL` | Reale Screenshot-/Action-Evidence an den bestehenden Envelope binden. | [G09](09-evidence-and-provenance.md) |
| G10 | Fehler werden reproduzierbar erkannt und sicher behandelt. | RED → Fix → Targeted → Negative → Regression → Full Gate → genau ein Unchanged Replay. | `PARTIAL` | Realpfad-Black-Box- und Stability-Tests ergänzen. | [G10](10-testing-stability-and-recovery.md) |
| G11 | Ungelöste Probleme werden einmalig, geprüft und nachvollziehbar an Brother GPT übergeben. | Fingerprint, Handoff, Self-Review, Lead-Review und Herkunftsblock sind vollständig. | `PARTIAL` | Einen vollständigen synthetischen Advisory-Zyklus validieren. | [G11](11-brother-gpt-escalation.md) |
| G12 | Release, Installation, Canary, Rollback und Betriebsmodus sind nachgewiesen. | Gemergter SHA, Post-Merge-Canary, Evidence-Reconciliation und Rückfall auf Custom GPT sind dokumentiert. | `BLOCKED` | Erst alle technischen Pflicht-Gates finalisieren und Consequence Gates bündeln. | [G12](12-release-migration-and-operations.md) |

## Einheitliches Schema für jedes Sub-Dokument

Jedes Gate-Detaildokument muss dieselben Abschnitte enthalten und darf keinen
Punkt nur im Chat erklären:

1. Ziel
2. Warum das Gate erforderlich ist
3. Scope und Nicht-Ziele
4. Abhängigkeiten
5. Aktueller Stand mit `IMPLEMENTATION_STATUS`, `LIVE_EVIDENCE_STATUS`,
   `GATE_STATUS`, `EVIDENCE_LEVEL`, `LAST_VERIFIED_BASE_SHA` und Datum
6. Bestehende Evidence
7. Lücke und Root Cause
8. kleinschrittiger Arbeitsplan
9. `CONTROL_LOOP_GATE` mit Input, Procedure, Pass/Fail, Retry, Fallback,
   Evidence-Output, nächstem Schritt und Invalidation-Trigger
10. Tests
11. Safety und Datenschutz
12. Brother-GPT-Eskalation
13. Abschlussartefakte
14. Beitragsherkunft

Neue Punkte werden aus [`gate-template.md`](gate-template.md) erzeugt. Ein
Sub-Dokument gilt erst als vollständig, wenn alle vierzehn Abschnitte vorhanden
sind und sein Registereintrag auf dasselbe Detail verweist.

## Arbeitsweise für kleine Modelle

Ein neuer Lauf liest nur:

1. dieses Dokument oder den Master;
2. `gate-status.json`;
3. das Detaildokument des `active_gate`;
4. die dort ausdrücklich genannten Quellen.

Danach arbeitet er genau einen Sub-Step mit folgendem Loop:

`ORIENT → FRESH → PREFLIGHT → RED → ROOT_CAUSE → MINIMAL_FIX → TARGETED → NEGATIVE → REGRESSION → EVIDENCE → GATE → CHECKPOINT`

Bestandene Checkpoints und identische Tests werden bei unveränderten Hashes
nicht wiederholt. `UNKNOWN` erhält genau einen gezielten Read; danach wird der
Brother-GPT-Handoff verwendet oder ein konkreter Human-Gate-Blocker gemeldet.

## Brother-GPT-Regel

Der Brother ist beratender Architekt und Kontrolleur, nicht ausführender Agent.
Er erhält nur ein minimales technisches `BROTHER_HANDOFF_PACKAGE` ohne Tokens,
Patientendaten oder unnötige Rohlogs. Seine Lösung wird im selben Chat einmal
gegen Evidence, Scope, Safety, Open-Source-Reuse und Aufgaben-Drift geprüft.
Übernommen wird sie erst nach Lead-Review und mit diesem Herkunftsblock:

```text
CONTRIBUTION_SOURCE=BROTHER_GPT
CONTRIBUTION_DATE=<ISO-8601>
HANDOFF_ID=<stable-id>
REVIEW_STATUS=ACCEPTED|REVISED|REJECTED
INCORPORATED_BY=KGG_LEAD
SOURCE_SUMMARY=<bounded summary>
DECISION_SUMMARY=<bounded summary>
```

Bei identischem Blocker-Fingerprint und unveränderter Evidence wird kein
zweiter Brother-Lauf gestartet. Brother darf keine Gates abschwächen, keine
Writes/Tests/Dispatches ausführen und weder Goal noch Comparator ändern.

## Abschluss-Checkliste

- [ ] Jeder Registerpunkt hat genau einen Status und ein Detaildokument.
- [ ] Jeder Status verweist auf Fresh Evidence oder ist ausdrücklich als
      `BLOCKED`, `PARTIAL`, `FAIL` oder `NOT_OBSERVABLE` begründet.
- [ ] Keine synthetische Fixture wird als Real-Surface-Evidence ausgegeben.
- [ ] Alle implementierbaren Kernpfade und Negativpfade sind getestet.
- [ ] Dokumentation, Register, Hashes und Checkpoints sind konsistent.
- [ ] Brother-Beiträge sind geprüft und gekennzeichnet.
- [ ] Release-/Merge-/Canary-/Rollback-Status ist getrennt vom lokalen PASS.
- [ ] Ein finaler Endzustand und ein sicherer nächster Betriebsmodus sind
      dokumentiert.

## Quellenstand

Diese Übersicht wurde gegen den Fresh-Main-Anker `1e6c6e3e28603f28bfbad3b127c688e722c823f5` erstellt. Der maschinenlesbare Status in `gate-status.json` bleibt die operative Statusquelle; bei einer späteren Main-Änderung muss nur dieser Quellenstand aktualisiert werden.
