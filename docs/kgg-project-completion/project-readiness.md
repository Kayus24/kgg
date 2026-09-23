# KGG – Projektanforderungen, Gate-Register und Arbeitsindex

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

### Dokumentvertrag

```text
DOCUMENT_ROLE=MASTER_REQUIREMENTS_INDEX
STATUS_SOURCE=gate-status.json
DETAIL_TEMPLATE=gate-template.md
GOAL_PROMPT=kgg-project-completion-goal-prompt.md
ONE_ACTIVE_GATE=true
ONE_NEXT_STEP_PER_GATE=true
```

Dieses Dokument ist damit die angeforderte Gesamtübersicht: Jeder Pflichtpunkt
hat ein prüfbares Gate, einen aktuellen Erfüllungsgrad, eine Evidence-Lücke,
einen nächsten zulässigen Schritt und genau ein Detaildokument. Die
maschinenlesbare Statusquelle bleibt trotzdem `gate-status.json`; hier wird
keine zweite Statusquelle eingeführt.

Dieses Dokument ist zugleich der vorbereitete Arbeitsindex für kleinere
Modelle. Es enthält pro Pflichtpunkt das Ergebnis, das Gate-Kriterium, die
aktuelle Evidence-Lücke, den nächsten zulässigen Schritt und den Verweis auf
das Detaildokument. Ein Modell muss den technischen Plan daher nicht aus dem
Chatverlauf rekonstruieren.

## Was „läuft“ und was „vollständig abgeschlossen“ bedeutet

## Produktumfang, der tatsächlich abgenommen werden muss

Das Projekt hat zwei gleichrangige Betriebsziele:

1. Die dauerhaft benötigten Custom-GPT-Funktionen sind als versioniertes,
   portables Plugin für die unterstützten Hosts abgebildet. ChatGPT, Custom GPT
   und Codex werden getrennt bewertet; eine lokale MCP-Installation beweist
   nicht automatisch ChatGPT-Verfügbarkeit.
2. Der UI-Lab-Kanal kann eine erlaubte KGG-HTML-Testseite über eine echte
   Browsergrenze öffnen und den Regelkreis
   `Screenshot → Auswertung → Klick/Move/Touch → neuer Screenshot →
   Zustandsprüfung` ausführen. Bekannte Bedienfolgen werden als versionierte
   Quick Flows mit visueller Fallback-Route geführt.

Measurement, Provenance, Safety und Release sind Abnahmekriterien für diese
beiden Ziele, aber kein Ersatz für die echte Browseraktion oder den echten
Plugin-Host-Nachweis.

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

| Punkt | Muss erfüllt sein | Gate-Kriterium / Control Loop | Mindestens erforderliche Evidence | Aktueller Stand | Nächster zulässiger Schritt | Detail |
| --- | --- | --- | --- | --- | --- | --- |
| G00 | Eine Fresh-Baseline, eine Statusquelle und Resume-Checkpoints existieren. | Fresh Main, Master, Register und aktives Detaildokument stimmen überein; genau ein nächster Schritt. | E2: gebundener SHA, Register, Checkpoint | `PASS` | Bei Status-/Quellenänderung gezielt neu binden. | [G00](00-governance-and-source-of-truth.md) |
| G01 | Alle benötigten Custom-GPT-Fähigkeiten sind inventarisiert und einem Plugin-Baustein, Test und Endstatus zugeordnet. | Keine Capability-Zeile bleibt ohne Owner, Test oder Disposition. | E1: vollständige Matrix und Tests | `PASS` | Nur bei neuer Capability ergänzen. | [G01](01-custom-gpt-capability-migration.md) |
| G02 | Das Plugin ist versioniert, portabel und installierbar. | Installation aus dem vorgesehenen Paket; keine lokale Pfadannahme; Manifest und Marketplace konsistent. | E2: frische lokale Installation; E3 für ChatGPT | `PARTIAL` | Transport- und Hostvoraussetzungen für G03/G04 klären. | [G02](02-universal-plugin-package.md) |
| G03 | Normales ChatGPT entdeckt das Plugin und ruft mindestens ein read-only Tool auf. | Fresh Discovery plus echter read-only Tool-Canary mit E3-Evidence. | E3: Discovery, Tool-Request, Tool-Response | `PASS` (`READ_ONLY_TOOL_EXECUTED_UI_PARITY_UNVERIFIED`) | Der offizielle `Im Chat testen`-Pfad hat das Plugin an eine neue Work-Conversation gebunden; `get_current_state(actor=system)` gab exakt einmal `status=ready` zurück. G04–G06 müssen Screenshot-, Action- und Quick-Flow-Funktionen separat nachweisen. | [G03](03-chatgpt-plugin-connection.md) |
| G04 | Eine echte, isolierte Browserbrücke steuert die erlaubte KGG-Testseite. | Session → Open → Screenshot A → echte Aktion → Screenshot/Zustand B → End; alles run-gebunden. | E2 lokal, E3 für Host-Parität | `PASS` (E2 lokal) | G05 visuellen Agentenloop und G06 drei reale Flows binden; E3-Host-Parität bleibt separat. | [G04](04-real-browser-bridge.md) |
| G05 | Der visuelle Regelkreis funktioniert. | GPT wertet Screenshot A aus, führt genau eine Aktion aus und bestätigt den geänderten Zustand anhand B; kein behaupteter Erfolg ohne Runner-Evidence. | E2 lokal, E3 für unterstützte Host-Surface | `PARTIAL` | Persistenten Visual Loop an einen autorisierten Agent-Host binden und E3 nachweisen. | [G05](05-visual-interaction-loop.md) |
| G06 | Mindestens drei Quick Flows laufen real und versioniert. | Jeder Schritt hat Assertion, Evidence und visuellen Fallback; stale Flows stoppen fail-closed. | E2/E3 pro Flow plus unveränderter Replay | `PARTIAL` | Lokaler Drift-Fallback und Replay sind gebunden; E3-Host-Evidence ergänzen. | [G06](06-real-quick-flows.md) |
| G07 | A/B/C sind getrennt und ehrlich klassifiziert. | Keine Capability wird von einer Surface auf eine andere übertragen; pro Surface eigener Canary oder begründetes `NOT_TESTED`/`SYNTHETIC_ONLY`/`NOT_OBSERVABLE`. | E3 je erreichbarer Surface; E2 für lokalen Pluginpfad; keine lokale Evidence als Host-Parität | `PASS` (Klassifikation; B Real-UI-Audit `PARTIAL`) | Ein Real-B-Canary ist mit `real_browser_timeout` fail-closed dokumentiert; kein zweiter Canary ohne neues Run-Budget. | [G07](07-surface-integration.md) |
| G08 | Safety und Autorisierung begrenzen den Realpfad. | Domain-Allowlist, Lease, Limits, Sanitization und Negativtests blockieren unzulässige Aktionen. | E2/E3 positive und negative Realpfad-Evidence | `PARTIAL` | Lokale Safety-Suite 57/57 PASS; externe Popup-/Download-/Filechooser- und E3-Safety-Evidence bleiben offen. | [G08](08-security-privacy-and-authorization.md) |
| G09 | Jede Messung ist provenance-first. | Raw Evidence, Hash, Run-ID, Surface, Base-SHA und Field-Provenance sind re-hashbar; unbekannt bleibt `NOT_MEASURED`. | E2/E3 Raw-Evidence-Rehash und Envelope-Validation | `PARTIAL` | Lokale Rehash-/Tamper-Suite 57/57 PASS; externe Measurement-Envelope-Reconciliation bleibt offen. | [G09](09-evidence-and-provenance.md) |
| G10 | Fehler werden reproduzierbar erkannt und sicher behandelt. | RED → Fix → Targeted → Negative → Regression → Full Gate → genau ein Unchanged Replay. | E2/E3 Testresultate und Replay-Fingerprint | `PASS` (lokale Candidate-Stabilität) | Lokale Black-Box-, Negative-, Critical-, UI-Regression- und Replay-Evidence ist grün; E3-Replay bleibt technische Grenze. | [G10](10-testing-stability-and-recovery.md) |
| G11 | Ungelöste Probleme werden einmalig, geprüft und nachvollziehbar an Brother GPT übergeben. | Fingerprint, Handoff, Self-Review, Lead-Review und Herkunftsblock sind vollständig im G03-Zyklus gebunden. | E1 kompletter Advisory-Zyklus | `PASS` | Bei neuem Blocker-Fingerprint denselben Ablauf verwenden; unveränderte Fingerprints nicht erneut prüfen. | [G11](11-brother-gpt-escalation.md) |
| G12 | Release, Installation, Canary, Rollback und Betriebsmodus sind nachgewiesen. | Gemergter SHA, Post-Merge-Canary, Evidence-Reconciliation und Rückfall auf Custom GPT sind dokumentiert. | E3/E4 Merge-, Canary- und Rollback-Evidence | `PARTIAL_COMPLETE_WITH_TECHNICAL_LIMITS` | PR #256 und #257 sind auf Main; Required Gates grün. Real-Host-UI-Beobachtung, Post-Merge-Canary und externe Envelope-Reconciliation bleiben offen. | [G12](12-release-migration-and-operations.md) |

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

### Verbindlicher Gate-Datensatz

Jeder Punkt und jedes Sub-Dokument muss mindestens diesen Datensatz ausfüllen:

```text
GATE_ID=
TITLE=
CURRENT_STATUS=PASS|PARTIAL|FAIL|BLOCKED|UNKNOWN|NOT_APPLICABLE
EVIDENCE_LEVEL=E0_DOCUMENTED|E1_SYNTHETIC|E2_LOCAL_REAL_RUNTIME|E3_REAL_HOST|E4_REPEATED_STABLE
ACTIVE_SUBSTEP=
INPUTS=
PRECONDITIONS=
PASS_CRITERIA=
FAIL_CRITERIA=
RETRY_RULE=
FALLBACK=
EVIDENCE_OUTPUT=
NEXT_ON_PASS=
NEXT_ON_FAIL=
INVALIDATION_TRIGGERS=
LAST_VERIFIED_BASE_SHA=
LAST_VERIFIED_AT=
```

`PASS_CRITERIA` muss beobachtbar sein; `FAIL_CRITERIA` muss einen sicheren
Stopp oder eine konkrete Root-Cause-Analyse auslösen. Fehlen Input, Evidence
oder Invalidation-Trigger, darf der Punkt nicht als `PASS` gelten.

### Sub-Dokument-Definition of Done

Ein Detaildokument ist erst arbeitsfähig, wenn zusätzlich zu den vierzehn
Abschnitten alle folgenden Felder konkret ausgefüllt sind:

- eine eindeutige `GATE_ID` und genau ein `ACTIVE_SUBSTEP`;
- `CURRENT_STATUS` und `EVIDENCE_LEVEL` passend zum Register;
- mindestens ein positives und ein negatives Gate-Kriterium;
- ein aus dem Repository ableitbarer Testbefehl oder eine begründete
  `NOT_APPLICABLE`-Entscheidung;
- ein expliziter letzter sicherer lokaler Endzustand;
- ein Invalidation-Trigger für Main-, Contract-, Harness- oder UI-Drift;
- ein Checkpoint-Ausgabeformat mit `NEXT_STEP`;
- bei Brother-Beiträgen ein vollständiger Herkunftsblock.

Fehlt eines dieser Felder, bleibt der Punkt `UNKNOWN` oder `PARTIAL`; er darf
nicht als `PASS` weitergereicht werden.

## Vorbereitete Arbeitsartefakte für kleinere Modelle

Die folgende Reihenfolge minimiert Kontext und verhindert wiederholte Audits:

1. [README.md](README.md) und dieses Dokument lesen.
2. `gate-status.json` lesen und ausschließlich `active_gate` auswählen.
3. Das zugehörige Detaildokument und nur dessen Quellen lesen.
4. Den dort angegebenen `ACTIVE_SUBSTEP` mit `ORIENT → FRESH → PREFLIGHT`
   beginnen.
5. Vor einem Write ein gebündeltes `PREFLIGHT_PACKAGE` erstellen.
6. Nach `RED → FIX → TARGETED → NEGATIVE → REGRESSION` die Evidence binden,
   den Gate-Status aktualisieren und eine Checkpoint-Capsule schreiben.
7. Bei unveränderten Hashes den Checkpoint fortsetzen; identische Tests und
   Brother-Reviews nicht wiederholen.

Die kleinste zulässige Arbeitsübergabe lautet:

```text
ACTIVE_GATE=
ACTIVE_SUBSTEP=
BASE_SHA=
GOAL_HASH=
CURRENT_STATUS=
REQUIRED_EVIDENCE_LEVEL=
ALLOWED_PATHS=
PREFLIGHT_RESULT=
RED_RESULT=
TARGETED_RESULT=
NEGATIVE_RESULT=
REGRESSION_RESULT=
EVIDENCE_REFS=
NEXT_STEP=
```

Damit kann auch ein kleineres Modell einen einzelnen kontrollierten Schritt
ausführen, ohne den gesamten Chatverlauf zu laden.

Für den einzigen vorbereiteten A/B-Host-UI-Folgepfad gelten ergänzend:

- Ablauf: [07a-dual-surface-ui-audit-runbook.md](07a-dual-surface-ui-audit-runbook.md)
- deaktivierte Envelope-Vorlage: [G07_DUAL_SURFACE_EXECUTION_ENVELOPE_TEMPLATE_20260921.json](G07_DUAL_SURFACE_EXECUTION_ENVELOPE_TEMPLATE_20260921.json)

Die Vorlage autorisiert keinen Run, Runtime-Key, Tunnel, Write oder Dispatch.
Sie darf erst nach einer separaten, surface-spezifischen Autorisierung
instanziiert werden. Das Verfahren wird hier nicht dupliziert.

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

### Dokumentierte Rückkopplung bei ungelösten Problemen

Wenn ein Problem durch Master, aktives Detaildokument, kanonische Quellen und
einen gezielten Read nicht lösbar ist, wird es als `UNRESOLVED_DOCUMENT_GAP`
behandelt. Der Lead erstellt ein `BROTHER_HANDOFF_PACKAGE`, lässt den Brother
eine Lösung und einen kleinsten Umsetzungsplan erarbeiten und fordert danach
im selben Kanal eine Gegenprüfung an. Erst nach Lead-Review wird die Lösung in
das betroffene Detaildokument übernommen. Die Übernahme muss gleichzeitig:

1. Gate-Kriterium und Control Loop aktualisieren;
2. Tests, Fallback und Invalidation-Trigger ergänzen;
3. `gate-status.json` nur bei realer Statusänderung ändern;
4. den Herkunftsblock `CONTRIBUTION_SOURCE=BROTHER_GPT` eintragen;
5. eine neue Checkpoint-Capsule mit dem nächsten Schritt erzeugen.

So bleibt der Brother ein Problemlöser und Kontrolleur, ohne eine parallele
Arbeitsplanung oder eine zweite Wahrheit zu erzeugen.

### Herkunfts- und Änderungsprotokoll

Jede aus einem Brother-GPT- oder Custom-GPT-Vorschlag übernommene Änderung an
Master, Detaildokument oder Goal-Prompt muss im selben Dokument mit dem
Herkunftsblock aus Abschnitt 12 festgehalten werden. Zusätzlich muss der
Übernehmer kurz dokumentieren:

1. welches Problem oder welche Evidence-Lücke vorlag;
2. welche Empfehlung geprüft wurde;
3. welche Teile übernommen, angepasst oder verworfen wurden;
4. welches Gate, welcher Test, welcher Fallback und welcher nächste Schritt
   dadurch geändert wurden.

Ohne diese Prüfung ist der Vorschlag nur `ADVISORY`, nicht Projektstatus. Ein
kleines Modell darf einen bestehenden Brother-Beitrag wiederverwenden, wenn
`HANDOFF_ID`, Evidence-Hashes und Blocker-Fingerprint unverändert sind.

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
- [ ] Jede Blocker-Entscheidung enthält genau einen nächsten zulässigen Schritt
      oder eine begründete technische Grenze.
- [ ] Alle kleineren Arbeitsübergaben enthalten Gate, Sub-Step, Evidence und
      Next Step; keine Aufgabe hängt nur im Chat.

## Quellenstand

Diese Übersicht wurde zuletzt gegen den Fresh-Main-Anker
`12b13767cc1667f97d428e1f7f7b7978fe2e4ac4` planungsseitig abgeglichen.

```text
LOCAL_HEAD_AT_INDEX=12b13767cc1667f97d428e1f7f7b7978fe2e4ac4
INDEX_UPDATED_AT=2026-09-21T23:30:00+02:00
```

Der maschinenlesbare Status in `gate-status.json` bleibt die operative
Statusquelle; bei einer späteren Main- oder Contract-Änderung wird nur der
betroffene Quellenstand und der abhängige Checkpoint invalidiert.
