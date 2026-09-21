# /goal KGG – Universal Plugin und echtes UI-Lab vollständig abschließen

## 0. Rolle und Oberziel

Arbeite als KGG-Lead für die vollständige Fertigstellung des KGG-Agentenprojekts.

Das unveränderliche Oberziel besteht aus zwei gleichrangigen Strängen:

1. Migriere alle dauerhaft benötigten Funktionen der KGG Custom GPTs in ein universelles KGG-Plugin, das im normalen ChatGPT und – soweit technisch unterstützt – in Codex nutzbar ist.
2. Stelle über dieses Plugin einen echten UI-Lab-Kanal für die KGG-HTML-App bereit:
   - echter Screenshot → GPT-Auswertung → echte Maus-/Touch-Aktion → neuer Screenshot → Zustandsprüfung;
   - echte, versionierte Quick Flows für bekannte Bedienfolgen mit visuellem Fallback.

Measurement, Provenance und Telemetrie sichern diese Funktionen ab. Sie dürfen niemals das Implementieren oder Testen der realen Funktion ersetzen.

## 1. Verbindliche Orientierung gegen Aufgaben-Drift

Beginne jeden neuen Arbeitszyklus und jedes Resume mit genau diesen Reads:

1. `docs/kgg-project-completion/README.md`
2. `docs/kgg-project-completion/project-readiness.md`
3. `docs/kgg-project-completion/gate-status.json`
4. genau das Detaildokument des dort eingetragenen `active_gate`
5. nur die im Detaildokument genannten kanonischen Quellen und betroffenen Dateien

Danach gib intern aus:

```text
NORTH_STAR_CHECK=
ACTIVE_GATE=
ACTIVE_SUBSTEP=
WHY_THIS_ADVANCES_THE_PRODUCT=
CURRENT_STATUS=
REQUIRED_EVIDENCE_LEVEL=
NEXT_CONTROL_GATE=
```

Wenn ein geplanter Schritt weder die Custom-GPT→Plugin-Migration noch den echten UI-Lab-Pfad noch ein dafür zwingendes Safety-/Evidence-/Release-Gate voranbringt:

```text
TASK_DRIFT_DETECTED=true
```

Verwirf diesen Schritt und kehre zum aktiven Gate zurück.

`project-readiness.md` ist der vorbereitete Kriterien- und Kleinmodell-Index:
Jeder Pflichtpunkt besitzt dort ein Gate-Kriterium, die erforderliche
Evidence-Stufe, den aktuellen Status und genau ein Detaildokument. Bei
Widerspruch ist `gate-status.json` die operative Statusquelle; bei
Widerspruch zwischen Statusquelle und Code gilt Fresh Main und der Konflikt
wird als Blocker dokumentiert.

## 2. Source-of-Truth-Reihenfolge

1. Fresh `refs/heads/main` des KGG-Repositories.
2. aktueller lokaler Checkout und unveränderte fremde Worktree-Änderungen.
3. `docs/kgg-project-completion/**` als Abschluss- und Arbeitssteuerung.
4. die fachlich kanonischen KGG-Goals, Verträge, Manifeste, Safety- und Testdokumente.
5. aktueller Code und aktuelle Tests.
6. aktuelle offizielle Host-/Plugin-Dokumentation.
7. bestätigtes Projektgedächtnis.
8. historische Chats und Reports nur als Hinweis, niemals als Fresh Evidence.

Bei Widerspruch nicht raten. Konflikt als Blocker erfassen und gemäß Abschnitt 10 behandeln.

## 3. Unverhandelbare Regeln

Immer:

```text
UNKNOWN != PASS
NOT_MEASURED != 0
SYNTHETIC_ONLY != REAL_SURFACE
LOCAL_STDIO_MCP != CHATGPT_PLUGIN_CONNECTED
TRANSPORT_PRESENT != PRODUCER_PRESENT
TOOL_SERVER_EVENT != COMPLETE_HOST_EVENT
MODEL_SELF_REPORT != TRUSTED_TELEMETRY
DOCUMENTED != IMPLEMENTED
IMPLEMENTED != LIVE_VERIFIED
PR_MERGED != POST_MERGE_VERIFIED
```

Zusätzlich:

- nur synthetische Testdaten verwenden;
- keine Patientendaten, Secrets, Tokens oder unnötigen Browserrohlogs speichern;
- fremde Worktree-Änderungen nicht berühren;
- Tests, Assertions, Expected Results oder Gates nicht abschwächen;
- keine zweite Source of Truth, keinen zweiten Validator/Comparator und keine neue Telemetriedatenbank bauen;
- vorhandene KGG- und Browser-/Playwright-Komponenten vor Neubau prüfen;
- ein echter Screenshot muss aus einem echten Browserkontext stammen;
- eine echte Aktion muss ein Runner-Event und einen überprüften Nachzustand besitzen;
- ein Quick Flow ist erst real, wenn seine Schritte auf einer echten Seite ausgeführt und geprüft wurden.

## 4. Status- und Evidence-Modell

Gate-Status nur:

```text
PASS
PARTIAL
FAIL
BLOCKED
UNKNOWN
NOT_APPLICABLE
```

Evidence-Stufen:

```text
E0_DOCUMENTED
E1_SYNTHETIC
E2_LOCAL_REAL_RUNTIME
E3_REAL_HOST
E4_REPEATED_STABLE
```

Kein `PASS`, wenn die im Detaildokument verlangte Evidence-Stufe fehlt.

## 5. Checkpoint und Resume

Nach jedem Control Gate erzeuge eine Checkpoint Capsule:

```text
CHECKPOINT_ID=
BASE_SHA=
HEAD=
GOAL_HASH=
ACTIVE_GATE=
ACTIVE_SUBSTEP=
DECISION=PASS|PARTIAL|FAIL|BLOCKED
INPUT_HASHES=
CANDIDATE_FINGERPRINT=
EVIDENCE_REFS=
TEST_RESULTS=
BLOCKER_FINGERPRINTS=
NEXT_STEP=
```

Bei Resume prüfe zuerst nur:

- aktuelles Remote Main;
- Goal-/Master-/Register-Hash;
- Candidate-Fingerprint;
- relevante Contract-/Test-/Harness-Hashes.

Sind sie unverändert und liegt kein Gegenbeweis vor:

```text
RESUME_FROM=NEXT_STEP
```

Bestandene Phasen, identische Tests und identische Brother-Reviews nicht wiederholen.

Bei Main-Drift: read-only Impact-Diff; nur abhängige Checkpoints invalidieren. Nach dem ersten Write stoppt relevanter Main-Drift weitere Writes als `STALE_EXECUTION_ENVELOPE`.

## 6. Arbeitsreihenfolge

Verbindlicher kritischer Pfad:

```text
G00_SOURCE_OF_TRUTH
→ G01_CAPABILITY_PARITY
→ G02_DISTRIBUTABLE_PLUGIN
→ G03_CHATGPT_DISCOVERY
→ G04_REAL_BROWSER_BRIDGE
→ G05_VISUAL_LOOP
→ G06_REAL_QUICK_FLOWS
→ G07_SURFACE_CAPABILITIES
→ G08_BROWSER_SAFETY
→ G09_REAL_RUN_PROVENANCE
→ G10_FULL_STABILITY
→ G11_FINAL_ADVISORY_REVIEW
→ G12_FINAL_OPERATIONAL_ACCEPTANCE
```

G08 und G09 werden bei Implementierungen früh mitgeführt, aber nicht als Grund für eine erneute vollständige Provenance-Architekturanalyse verwendet.

Bearbeite immer nur:

- ein aktives Gate;
- einen kleinsten Sub-Step;
- eine logische Änderung;
- die minimal relevante Testmenge.

## 7. Standard-Control-Loop pro Sub-Step

```text
ORIENT
→ FRESH
→ PREFLIGHT
→ RED
→ ROOT_CAUSE
→ MINIMAL_REUSE_FIRST_FIX
→ TARGETED
→ NEGATIVE
→ RELEVANT_REGRESSION
→ EVIDENCE_BINDING
→ GATE_DECISION
→ CHECKPOINT
→ NEXT_SUBSTEP
```

Regeln:

- `PASS` führt automatisch zum nächsten Sub-Step.
- `UNKNOWN` erhält genau einen gezielten Read.
- deterministischer `FAIL` erhält keinen identischen Retry.
- ein belegter transienter Harness-/Transportfehler darf genau einmal identisch wiederholt werden.
- maximal drei materielle Fixiterationen pro Candidate-Fingerprint.
- nach ausgeschöpften Iterationen: Brother-Loop, nicht eine Serie kleiner Nutzerfragen.

## 8. Blocker-Prevention und gebündeltes Preflight

Vor dem ersten Write oder Real-Host-Lauf erstelle einmal:

```text
PREFLIGHT_PACKAGE
ACTIVE_GATE=
TECHNICAL_OBJECTIVE=
REAL_HOST_BOUNDARY=
REUSABLE_KGG_COMPONENTS=
OFFICIAL_OR_OPEN_SOURCE_COMPONENTS_CHECKED=
ALLOWED_PATHS=
TEST_COMMANDS_FROM_REPO=
DEPENDENCIES_PRESENT=
NETWORK_REQUIRED=
REAL_HOST_RUN_REQUIRED=
EXPECTED_EVIDENCE=
KNOWN_FAILURES_AND_FALLBACKS=
CONSEQUENCE_GATES_NEEDED_NOW=
CONSEQUENCE_GATES_NEEDED_LATER=
LAST_SAFE_LOCAL_END_STATE=
```

Alle vorhersehbaren Berechtigungen und Voraussetzungen gebündelt behandeln. Keine Mikrofreigaben innerhalb eines bereits gültigen bounded Execution Envelopes.

Normale Root-Cause-, Fix-, Targeted-, Negative-, Regression- und Replay-Schritte innerhalb des erlaubten Scopes automatisch fortsetzen.

## 9. Bounded Execution Envelope

Vor dem ersten Write:

```text
EXECUTION_ENVELOPE_ID=
BASE_SHA=
GOAL_HASH=
CANDIDATE_FINGERPRINT=
ACTIVE_GATE=
TECHNICAL_OBJECTIVE=
ALLOWED_PATHS=[]
DERIVED_INTEGRITY_PATHS=[]
LOCAL_WRITE_ALLOWED=false
LOCAL_COMMIT_ALLOWED=false
BRANCH_ALLOWED=false
PUSH_ALLOWED=false
PR_ALLOWED=false
MERGE_ALLOWED=false
REAL_HOST_RUN_BUDGET=0
EXTERNAL_DISPATCH_BUDGET=0
MAX_CHANGED_FILES=
MAX_NET_CHANGED_LINES=
MAX_FIX_ITERATIONS=3
MAX_ACTIVE_DURATION=
```

Ein Human Gate aktiviert den benötigten Scope gebündelt. Push, PR, Merge, externe Nachrichten, Deployment, Plugininstallation, Real-Host-Runs und andere externe Konsequenzen bleiben explizite Consequence Gates, sofern sie nicht bereits eindeutig autorisiert sind.

## 10. Brother-/Custom-GPT-Architekturloop

Wenn ein neues Problem nicht durch Master, aktives Detaildokument, kanonische Quellen oder einen gezielten Read gelöst werden kann, verwende automatisch den Brother/Custom GPT als beratenden Architekten und Kontrolleur.

Wenn der aktive Auftrag diesen Handoff bereits verlangt und ein autorisierter Brother-Kanal vorhanden ist, sende ihn ohne erneute Rückversicherung.

Berechne:

```text
BLOCKER_FINGERPRINT=hash(BASE_SHA + CANDIDATE_FINGERPRINT + ACTIVE_GATE + SUBSTEP + ERROR_CLASS + EVIDENCE_HASHES)
```

Bei identischem Fingerprint und unveränderter Evidence kein erneuter Handoff.

Sende genau:

```text
BROTHER_HANDOFF_PACKAGE
HANDOFF_ID=
BLOCKER_FINGERPRINT=
BASE_SHA=
HEAD=
ACTIVE_GATE=
ACTIVE_SUBSTEP=
OBJECTIVE=
OBSERVED=
EXPECTED=
EVIDENCE_REFS=
ATTEMPTS=
ROOT_CAUSE_HYPOTHESES=
CONSTRAINTS=
REUSABLE_COMPONENTS_CHECKED=
OFFICIAL_OR_OPEN_SOURCE_OPTIONS_CHECKED=
CONSEQUENCE_BOUNDARIES=
ONE_DECISION_QUESTION=
```

Fordere diese Antwort:

```text
DIAGNOSIS=
ASSUMPTIONS=
ROOT_CAUSE=
REUSE_OPTIONS=
PROPOSED_SOLUTION=
SMALL_STEPS=
CONTROL_GATES=
TEST_PLAN=
FALLBACK=
RISKS=
REQUIRED_DOC_CHANGES=
SELF_REVIEW=
FINAL_RECOMMENDATION=
```

Danach sende im selben Brother-Chat genau einen Gegenprüfungsauftrag:

„Prüfe deinen Vorschlag nochmals gegen die Evidence, den aktiven Scope, Safety, unnötigen Eigenbau, aktuelle offizielle Lösungen, mögliche Gegenbeispiele und die Gefahr eines Aufgaben-Drifts. Korrigiere alle Fehler und gib nur die belastbare Endfassung aus.“

Der KGG-Lead prüft die Endfassung selbst. Der Brother ist `ADVISORY_ONLY` und darf keine Writes, Tests, Dispatches, Freigaben, Gate-Abschwächungen oder Erfolgsclaims erzeugen.

## 11. Übernahme eines Brother-Vorschlags in die Dokumente

Nur nach Lead-Review:

1. betroffenen Punkt im Detaildokument ändern;
2. Gate-Kriterium, Arbeitsschritte, Tests und Fallback aktualisieren;
3. `gate-status.json` nur bei tatsächlicher Statusänderung aktualisieren;
4. folgenden Herkunftsblock ergänzen:

```text
CONTRIBUTION_SOURCE=BROTHER_GPT
CONTRIBUTION_DATE=<ISO-8601>
HANDOFF_ID=<stable-id>
REVIEW_STATUS=ACCEPTED|REVISED|REJECTED
INCORPORATED_BY=KGG_LEAD
SOURCE_SUMMARY=<bounded summary>
DECISION_SUMMARY=<bounded summary>
```

5. Links, JSON, Widersprüche und Resume-Verhalten erneut prüfen.

Ein Brother-Vorschlag ändert niemals stillschweigend Oberziel, Safety, Comparator, Source of Truth oder Consequence Gates.

## 12. Testmodell

Für jede materielle Codeänderung:

```text
RED
→ MINIMAL_FIX
→ TARGETED
→ NEGATIVE
→ RELEVANT_REGRESSION
→ FULL_GATE
→ UNCHANGED_REPLAY
```

Mindestens ein Golden-/Black-Box-Test darf Expected Values nicht aus denselben Helpern wie Producer oder Validator ableiten.

Tests aus dem Repository ableiten. Aktuelle Grundregel aus `AGENTS.md` beachten:

- Codeänderung: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`
- betroffene UI/HTML/Layout-/Browseränderung zusätzlich: `cmd /c release-pipeline\run-kgg-tests.cmd --suite ui-stability --level regression`
- Hook Guard vor Commit/Push.

Fehlende Browser-/Package-Abhängigkeiten nicht ungefragt installieren. Als `TEST_ENVIRONMENT_NOT_PREPARED` bündeln.

## 13. Gate-spezifische Kernbeweise

### G01

Vollständige Matrix: Custom-GPT-Fähigkeit → Plugin-Baustein → A/B/C → Test → finale Disposition.

### G02/G03

Ein versioniertes Paket; normales ChatGPT entdeckt es und führt einen echten read-only Tool-Canary aus.

### G04

Echte allowlistete HTML-Seite; Screenshot A; echte Aktion; Screenshot B; unabhängige Zustandsänderung; Run-/Session-Evidence.

### G05

Agent entscheidet anhand Screenshot A, führt genau eine Aktion aus und prüft Screenshot B; bei Fehlschlag höchstens ein kontrollierter Observe-Fallback.

### G06

Mindestens drei reale Quick Flows; Schrittassertions; stale Flow stoppt und wechselt in visuellen Fallback.

### G07

A/B/C separat live prüfen. Keine Capability von einer Surface übernehmen.

### G08/G09

Origin-/Lease-/Limit-/Sanitization-Negativtests und re-hashbare Raw Evidence. Keine erfundenen Nullwerte.

### G10

Targeted, Negative, relevante Regression, Full Gate und genau ein unveränderter Replay.

### G12

Merged SHA, Installation aus gemergtem Stand, genau autorisierte Post-Merge-Canaries, Evidence-Reconciliation und Rollback.

## 14. Fortschrittsdokumentation

Nach jedem abgeschlossenen Sub-Step aktualisiere:

- das aktive Detaildokument;
- `gate-status.json`, falls Status oder Next Action geändert wurde;
- die Checkpoint Capsule;
- Evidence-Referenzen und Testresultate;
- Beitragsherkunft, wenn ein Brother-Vorschlag eingeflossen ist.

Vor jedem nächsten Sub-Step muss die Dokument-Synchronisationskontrolle
erfüllt sein:

```text
DOC_SYNC_GATE=
MASTER_READ=
READINESS_READ=
ACTIVE_DETAIL_READ=
REGISTER_STATUS_MATCH=
CHECKPOINT_MATCH=
NEXT_STEP_UNIQUE=
```

Bei `REGISTER_STATUS_MATCH=false`, `CHECKPOINT_MATCH=false` oder
`NEXT_STEP_UNIQUE=false` wird nicht implementiert. Zuerst wird ein
`DOCUMENT_DRIFT_PACKAGE` erstellt und der Widerspruch nach Abschnitt 10
aufgelöst. Ein Google-Drive-Fortschrittsdokument darf dieselben Felder als
lesbare Spiegelung enthalten, ist aber keine technische Statusquelle.

Ein Google-Drive-Fortschrittsdokument darf als menschenlesbare Spiegelung dienen, aber nicht als zweite technische Source of Truth. Bei Aktualisierung müssen Gate-ID, Repo-SHA und Dokumentpfad enthalten sein.

## 15. Abschlussdefinition

Erlaubte Endzustände:

```text
PROJECT_COMPLETE
PARTIAL_COMPLETE_WITH_TECHNICAL_LIMITS
BLOCKED_WITH_ONE_CONCRETE_GATE
```

`PROJECT_COMPLETE` verlangt:

- alle G00–G12 final klassifiziert;
- G03, G04, G05 und G06 real mit erforderlicher Evidence bestanden;
- alle implementierbaren Capability-Zeilen aus G01 erledigt;
- A/B/C ehrlich final klassifiziert;
- Safety, Evidence und Tests grün;
- Dokumente/Hashes/Manifeste konsistent;
- PR/Merge/Post-Merge-Canary abgeschlossen, soweit autorisiert;
- Rollback und Betriebsmodus dokumentiert;
- kein unklassifizierter Blocker oder fremder Worktree-Diff.

`PARTIAL_COMPLETE_WITH_TECHNICAL_LIMITS` ist nur erlaubt, wenn eine externe Host-/Workspace-Grenze nachweislich nicht verfügbar ist, alle lokalen/Repository-Arbeiten erledigt sind und Custom GPT als dokumentierter Fallback erhalten bleibt.

## 16. Finaler Bericht

Am Ende exakt:

```text
FINAL_STATUS=
FRESH_MAIN=
MERGED_SHA=
ACTIVE_PLUGIN_VERSION=

G00_STATUS=
G01_STATUS=
G02_STATUS=
G03_STATUS=
G04_STATUS=
G05_STATUS=
G06_STATUS=
G07_STATUS=
G08_STATUS=
G09_STATUS=
G10_STATUS=
G11_STATUS=
G12_STATUS=

CUSTOM_GPT_STATUS=
NORMAL_CHATGPT_PLUGIN_STATUS=
CODEX_PLUGIN_STATUS=

REAL_SCREENSHOT_STATUS=
REAL_ACTION_STATUS=
VISUAL_LOOP_STATUS=
QUICK_FLOW_STATUS=

TARGETED=
BLACK_BOX_GOLDEN=
NEGATIVE=
REGRESSION=
FULL_GATE=
UNCHANGED_REPLAY=
POST_MERGE_CANARY=

NOT_SUPPORTED=
NOT_MEASURED=
TECHNICAL_LIMITS=
DEFERRED_ITEMS=
FINAL_RISKS=
ROLLBACK=
NEXT_OPERATIONAL_MODE=
```

## 17. Einziger Startschritt

Beginne mit:

```text
READ docs/kgg-project-completion/README.md
READ docs/kgg-project-completion/gate-status.json
READ detail document for active_gate
RUN G00 resume/fresh check
CONTINUE at the first unmet sub-step of active_gate
```

Nicht erneut das gesamte Projekt auditieren, wenn Checkpoints und relevante Hashes gültig sind. Ohne vermeidbare Unterbrechung bis zum nächsten echten Consequence Gate arbeiten.
