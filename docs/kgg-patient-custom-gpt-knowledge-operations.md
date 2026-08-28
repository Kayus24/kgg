# KGG Patient GPT Knowledge: Operations

Generated retrieval pack. Source digest: `97114e298e75ebb6`.

Live GitHub context and source files override this static Knowledge pack.

---

# Source: docs/kgg-patient-custom-gpt-playbook.md

# KGG Patient Custom GPT Playbook

## Brain-Relay-Worker-Workflow v2

Der gemeinsame, additive Rollen- und Handoff-Vertrag steht in
`docs/kgg-brain-relay-worker-workflow.md`. Jeder frische Direktchat ist
`STANDALONE`; normale Fragen, Diagnose, Tests, `validate_only`, Preview und
bestehende Freigaben verwenden keinen PC-Runtime-/Bridge-Workflow. Nur das
exakt validierte `kgg-custom-gpt-workflow-start/v1`-Envelope aktiviert
`WORKFLOW`; eine ungültige Aktivierung wird `WORKFLOW_BLOCKED`, eine
Statusabfrage liest höchstens read-only. Der Patient-Lead bleibt das einzige
Patient-Hauptgehirn; Admin GPT und Patient GPT werden nie vermischt.

- Pro Ticket genau ein Patient-Lead-GPT. Im aktivierten `WORKFLOW` gilt der
  vollstaendige Weg `Luna Manager -> Lead GPT -> optionale GPT-Unter-Chats ->
  Lead-Synthese -> Luna Relay -> Luna-Max-Worker -> Relay -> derselbe Lead ->
  CI/Abnahme`; Standalone-Aufträge bleiben bei den bestehenden Patient-
  Actions.
- Hoechstens vier Unter-Chats, drei Luna-Max-Worker plus ein Verifier,
  disjunkte Scopes und keine Rekursion. Der Relay transportiert nur und darf
  Requirements, Hashes oder Tests nicht veraendern.
- Luna Manager, Relays, Ticket Master und Cricket sind `GPT-5.6 Luna` Low;
  Worker und Verifier `GPT-5.6 Luna` Max. Terra bleibt ausgeschlossen.
- Nach zwei unterschiedlichen Luna-Versuchen folgt Lead-Review; `NEEDS_SOL`
  braucht danach Cricket. Rotation: Vorbereitung bei 35, harter frischer
  Chatwechsel bei 40 oder fruehem Generation-/Revision-Drift.
- Completion/Blocker werden append-only ueber die bestehende Coordination
  Action gemeldet. Der Browser-Fallback bleibt Transport, wartet bis 30 Minuten
  ohne Statusprompt und versucht hoechstens einmal frisch erneut.
- Coordination-v2 hat im API-Schema genau einen sicheren Read-Weg:
  `getKggAgentCoordinationBridgeTask` für
  `coordination-bridge/tasks/{task_id}.json`. Task Capsule, Handoff und Cricket
  bleiben in der vollständigen lokalen PC-Runtime. Die bestehende append-only
  `submitKggAgentCoordinationEvent`-Action bleibt der einzige
  Koordinations-Schreibweg. Admin-Threads werden nie als Patient-Threads
  verarbeitet.

## Auftrag und Grenze

Der Agent diagnostiziert und repariert die Root-PWA fuer Patient:innen. Er darf `index.html`, `service-worker.js`, `update-recovery.html`, Manifest-Dateien, `patient-*.js`, `collapse-cards.js` und `numpad-ui-fix.js` ueber das Patient Preview Gate bearbeiten.

Nicht erlaubt sind Therapeut:innen-App, PDF, Android/APK, API-Key-Logik, binaere Icons sowie ein Breaking Change an KGGH2, KGGD1 oder Patientenspeicher. Schnittstellenaenderungen muessen additiv und rueckwaertskompatibel sein.

## Arbeitsfolge

1. Resource-Manifest, Live-Kontext und dieses Playbook live laden; den zentralen Workflow-Vertrag nur nach gültiger Workflow-Aktivierung laden.
2. Bug-Lessons und Source-Index laden.
3. Symptom reproduzierbar beschreiben.
4. Hoechstens drei Hypothesen mit unterscheidenden Tests aufstellen.
5. Bestaetigte Ursache und kleinsten Fix bestimmen.
6. Mit `getKggPatientMainCommit` die aktuelle Main-SHA laden und den Payload gegen diese SHA sowie aktuelle Dateihashes bauen.
7. `validate_only` ausfuehren und erfolgreichen Run pruefen.
8. Identischen Payload mit `publish_preview` ausfuehren.
9. Preview-Metadaten, Artefakt, Test-URLs und den service-worker-unabhaengigen First-Load-Smoke pruefen.
10. Max testet den Preview-Link im internen Browser.
11. Bei Ablehnung: `human_preview_fail`, Lektion festhalten und mit neuer `request_id` bei Schritt 1 beginnen.
12. Bei Zustimmung: `create_pr` oder nur auf ausdruecklichen Live-Auftrag `publish_patient_live`.

Die Schritte 7 bis 9 sind vorab freigegeben und laufen ohne Zwischenfrage. PR und Live erfordern die exakte Phrase `Gut für PAT live`. Nur echte Mehrdeutigkeit, ein Memory-Konflikt oder ein Breaking Interface rechtfertigt vorher eine Rueckfrage.

Offene Cross-App-Anfragen stehen im privaten Koordinationsindex. Der Patient-Agent liest nur passende Threads, antwortet append-only und speichert dort weder Patientendaten noch echte Plan-/QR-Payloads. Eine Queue-Antwort startet den anderen GPT nicht automatisch. Die Queue ist fuer Interface-/Cross-App-Arbeit Pflicht. Bei rein visuellen Patient-UI-Patches darf ein Queue-Ausfall als `coordination_unavailable` protokolliert werden, ohne einen ansonsten frisch belegten Patch zu blockieren.

Ein abgeschlossener ChatGPT-Antwortzug kann keinen neuen Read-/Action-Zug selbst
starten. Bei einer leeren, abgebrochenen oder zeitlimitierten Antwort
dokumentiert Codex den kompakten Handoff (`Zeit`, `GPT`, `Auftrag/Ziel`,
`Vorheriger sichtbarer Zustand/Run-ID`, `Beleg`, `Auswirkung`,
`Reaktivierungsaktion`, `Ergebnis`, `Folgeaktion`) im bestehenden
`docs/bug-debug/`-Log. Bei Reaktivierung zuerst Resource-Manifest,
Live-Kontext, Playbook und Main-SHA auffrischen und danach nur den vorhandenen
Run, Jobs und Artifacts lesen; niemals einen zweiten Preview-Dispatch erzeugen.
Einzelne Laufzeitereignisse gehoeren nicht ins Project Memory; sie aendern niemals Regeln automatisch. Bei Editor-/Knowledge-/Action-Drift oder fehlendem
Live-Beleg ist `stale_context` ein sicherer Stopp: Der Server blockiert
`publish_preview`, PR und Live bis der passende Snapshot `live-synced` ist.
Der kompatible Legacy-Preview-only-Weg prueft bei `publish_preview` auch den
Admin-Snapshot, damit ein aelteres Admin-Action-Schema den Write nicht umgeht.
Read-Actions und `validate_only` bleiben fuer Diagnose und lokale
Payload-Pruefung erlaubt.

Wenn ein Patient-Feature generierten Context, Source-Chunks oder Knowledge
aendert, bleibt dessen Ressourcen-Aenderungsbranch
`target-pending-live-editor-sync`: zuerst Feature-PR mergen, dann den Editor
gegen die neuen Artefakte und Live-Reads synchronisieren und erst danach den
`live-synced`-Snapshot in einem separaten Commit/PR festhalten. Nie einen alten Live-Sync in einem Ressourcen-Aenderungsbranch behalten; ein alter Live-Sync in einem Ressourcen-Aenderungsbranch ist kein gueltiger Nachweis.

Ein sichtbarer Browser-Button `Antwort stoppen` beweist nicht allein, dass ein
Vorgang noch laeuft; Completion folgt nur aus Antwortinhalt, Action-Ergebnis,
Run-Beleg oder stabilem Textzustand. Abweichende Editor-/Preview-Modelllabels
sind `model_ui_ambiguous`, kein bewiesener Modellwechsel. Vor Kosten- oder
Performanceaussagen immer die echte Editor-Auswahl und das Action-Verhalten
pruefen.

## Payload v1

```json
{
  "request_id": "patient-example-20260729-a",
  "base_sha": "40-character-main-sha",
  "title": "Kurzer Patchtitel",
  "summary": "Konkrete Verhaltensaenderung ohne Patientendaten.",
  "version_slug": "short-cache-slug",
  "risk_class": "standard",
  "touched_areas": ["patient-ui"],
  "required_tests": ["patient-pwa", "patient-browser"],
  "operations": [
    {
      "type": "replace_exact",
      "path": "patient-example.js",
      "old_sha256": "64-character-source-sha256",
      "old_text": "exact existing text",
      "new_text": "small replacement"
    }
  ]
}
```

Regeln:

- Maximal vier Operationen und pro Datei hoechstens eine.
- `old_text` muss genau einmal vorkommen.
- `old_sha256` muss zum vollstaendigen aktuellen Dateiinhalt passen.
- Keine No-ops, Pfad-Traversal, neuen Dateien oder Testabschwächungen.
- `risk_class=interface` fuer KGGH2, KGGD1, QR-/Hash-Parsing, Rueckgabe-QR oder Storage-Schluessel.
- Version, Cache-Name, Script-Versionen, Recovery-Release und Changelog nicht in Operationen aufnehmen.

## Tests

Jeder publizierte Preview- oder PR-Lauf prueft:

- kritische KGG-Batterie;
- PWA- und Update-Recovery-Vertrag;
- Kartenfortschritt, Installation, Planloeschung und Summary;
- mobilen synthetischen Browser-Flow;
- direkten Preview-First-Load ohne Service-Worker-Controller; Scanner-Modul und No-Plan-Rettungsbutton muessen ohne Reload funktionieren;
- bei Interface-Risiko oder einer Aenderung an `patient-start-scan.js` zusaetzlich Patient-Scan/QR-Regression;
- fuer `patient-start-scan.js` zusaetzlich den Full-Frame-Fall mit breitem und hohem synthetischen Kamerastream.

Fehlende Runner-Werkzeuge sind `ci_tooling`, kein bewiesener App-Fehler. Ein fehlgeschlagener App-Test ist kein Preview-Erfolg.

## Preview-Belege

Erfolg erfordert:

- Workflow `conclusion=success`;
- passender `requestId`, `patchHash` und `baseSha`;
- numerische neue Patientenversion;
- Artefakt `kgg-patient-preview-<request_id>`;
- Preview- und Recovery-URL unter `kayus24.github.io/kgg-patient-preview`;
- Preview-`index.html` enthaelt die kanonischen Patient-Module genau einmal und funktioniert beim ersten Aufruf ohne Service-Worker-Reload;
- ausschliesslich synthetischer Plan.

## Live-Belege

Live-Erfolg erfordert:

- exakt akzeptierter Preview-Hash;
- PR aus demselben `baseSha`;
- gruene Required Checks;
- Max' GitHub-Environment-Freigabe;
- gemergter PR;
- Live-`service-worker.js` meldet die erwartete Patientenversion.

---

# Source: docs/kgg-patient-custom-gpt-action-schema.md

# KGG Patient Custom GPT Action Contract

## Read Action

Die oeffentliche Read-Action unter `raw.githubusercontent.com` liefert:

- Patient Resource Manifest;
- Live-Kontext und Playbook;
- Bug-Lessons und Bug-Index;
- Patient Source-Index und einzelne Source-Chunks;
- Patient Preview-Index und einzelne Preview-Metadaten.

Live-Dateien haben Vorrang vor Knowledge.

## Authenticated API Action

Die Action unter `api.github.com` verwendet Bearer-Authentifizierung und stellt bereit:

- `submitKggPatientPreviewGate`;
- Run-, Job- und Artifact-Abfragen fuer den Patient Preview Gate Workflow;
- kleinen privaten Memory-Index und einzelne Packs;
- `submitKggMemoryUpdate` sowie Run-/Artifact-Nachweise.
- privaten Koordinationsindex, einzelne Threads und `submitKggAgentCoordinationEvent`.

## Modi

- `validate_only`: Payload, Allowlist, Source-Hashes und naechste Version pruefen; kein Repository-Write.
- `publish_preview`: identischen validierten Payload anwenden, Tests ausfuehren und isolierte GitHub-Pages-PWA publizieren.
- `create_pr`: nur nach akzeptiertem identischem Preview einen PR erstellen; nie mergen.
- `publish_patient_live`: nur nach Max' ausdruecklicher Preview-Freigabe einen PR erstellen; Merge wartet auf Required Checks und `patient-live` Environment Approval.

Server-Preflight: Jeder Preview-, PR- oder Live-Write verlangt einen Patient-Editor-Snapshot mit `live-synced`. Der kompatible Preview-only-Workflow prueft bei `publish_preview` zusaetzlich den Admin-Snapshot, damit ein aelteres Admin-Action-Schema den Write nicht umgehen kann. Read-Actions und `validate_only` bleiben fuer Diagnose und lokale Payload-Pruefung verfuegbar.

`submitKggPatientPreviewGate` ist Preview-only und vorab freigegeben. `submitKggPatientMainGate` ist getrennt, consequential und akzeptiert PR/Live nur mit `approval_phrase: "Gut für PAT live"`.

## Konsequenz

Preview-only- und abgesicherte Koordinations-Actions sind vorab freigegeben und nicht consequential. Main-/Live-Actions bleiben consequential. Memory-Konflikte bleiben mechanisch zustimmungspflichtig.

Die Action darf keine Patientendaten, echten Planpayloads, Secrets oder Roh-Base64 uebertragen. Preview-Plaene werden ausschliesslich im Gate synthetisch erzeugt.

## Brain-Relay-Worker Coordination-v2

Die bestehenden Operation-IDs `getKggAgentCoordinationIndex`,
`getKggAgentCoordinationThread`, `submitKggAgentCoordinationEvent` und
`listKggAgentCoordinationRuns` bleiben unveraendert. Das Patient-API-Schema
stellt für v2 genau den read-only Weg
`getKggAgentCoordinationBridgeTask` bereit. Er liest ausschließlich
`coordination-bridge/tasks/{task_id}.json` mit der exakten
`kgg-coordination-bridge-v1`-Allowlist. Task Capsule, Handoff und Cricket
bleiben in der vollständigen lokalen PC-Runtime und erhalten keine eigenen
v2-Pfade auf GitHub. Der Kurzpass kann keinen Patient-Write, keinen Admin-Write
und keinen Livegang ausloesen.

Ein frischer Direktchat ist `STANDALONE`; normale Fragen, Diagnose, Tests,
`validate_only`, Preview und bestehende Freigaben brauchen keine PC-Runtime und
keine Bridge. Erst das exakt validierte
`kgg-custom-gpt-workflow-start/v1`-Envelope aktiviert den zentralen Workflow;
eine ungültige Aktivierung wird `WORKFLOW_BLOCKED` und nicht als Standalone-
Auftrag ausgeführt. Eine Statusabfrage darf read-only Bridge-Status lesen,
aktiviert aber nichts. Der Patient-Lead bleibt pro aktiviertem Ticket das
einzige Patient-Hauptgehirn; Requirements, Tests, Generation, Revision und
Hashes bleiben unverändert. Details stehen ausschließlich im zentralen
Workflow-Vertrag.

---

# Source: docs/kgg-brain-relay-worker-workflow.md

# KGG Brain-Relay-Worker-Workflow v2

Dieses Dokument ist der gemeinsame KGG-Vertrag fuer Brain, Relay und Worker.
Es beschreibt nur die KGG-seitige Koordination. Die Produktfunktionen, das
Patient-Planformat, QR/PDF, Plan-State, Android und Releases bleiben unveraendert
und werden von diesem Workflow weder gelesen noch geschrieben, wenn sie nicht
im jeweiligen bestehenden Gate ausdruecklich freigegeben sind.

Die maschinelle Pruefung liegt in
`release-pipeline/kgg_brain_relay_worker.py`. Dieses Dokument ist die kanonische
Erklaerung. Die vollstaendige Runtime bleibt lokal auf dem PC; der optionale
GitHub-Kurzpass ist in `docs/kgg-brain-relay-worker-bridge.md` beschrieben.
Die bestehenden v1-Coordination-Operationen bleiben kompatibel, aber v2 legt
keine Task-, Handoff- oder Cricket-Dateien auf GitHub ab.

## 0. Zentrale Modusregel

Jeder frische Direktchat startet in `STANDALONE`. Normale Fragen, Diagnose,
Tests sowie `validate_only`, Preview und bestehende Freigaben bleiben in diesem
Modus unverändert und benötigen weder die lokale PC-Runtime noch die Bridge.
Eine reine Workflow-Statusabfrage darf den Bridge-Kurzpass lesen, aktiviert
aber keinen Workflow.

Nur eine Nachricht mit dem exakten Schema
`kgg-custom-gpt-workflow-start/v1` darf auf `WORKFLOW` umschalten. Sie hat
genau diese fünf Felder:

```json
{
  "schema": "kgg-custom-gpt-workflow-start/v1",
  "profile": "admin",
  "bridge": {
    "schema_version": "kgg-coordination-bridge-v1",
    "task_id": "<task_id>",
    "role": "lead-gpt",
    "generation": 1,
    "revision": 1,
    "status": "PASS",
    "requirements_sha256": "<64 lowercase hex characters>",
    "handoff_sha256": "<64 lowercase hex characters>",
    "next_action": "<short single-line action>"
  },
  "requirements_text": "<canonical requirements text>",
  "handoff": {
    "schema": "kgg-brain-relay-worker/handoff-v2",
    "event_id": "<event_id>",
    "sequence": 1,
    "event_type": "<event_type>",
    "task_id": "<task_id>",
    "generation": 1,
    "revision": 1,
    "from_role": "<from_role>",
    "to_role": "<to_role>",
    "requirements_sha256": "<same requirements hash>",
    "transport_only": true,
    "summary": "<short summary>",
    "evidence": [],
    "handoff_sha256": "<same current handoff hash>",
    "append_only": true
  }
}
```

Der Bridge-Pass enthält exakt die bestehenden neun Felder. Sein `role` ist in
dieser Aktivierung ausschließlich `lead-gpt`, `lead-synthesis` oder
`gpt-subchat`; das lokale `handoff-v2` wird zusätzlich unverändert gegen die
aktuelle Task Capsule geprüft. Requirements- und Handoff-SHA256,
Task-ID, Profil, Generation und Revision müssen übereinstimmen. History,
Worklogs, Patientendaten und Secrets gehören nicht in das Envelope.
Vor der Aktivierung liest das GPT den aktuellen Pass mit
`getKggAgentCoordinationBridgeTask` und vergleicht alle neun Felder exakt mit
dem Envelope. Fehlt der Read oder weicht ein Feld ab, bleibt der Auftrag
`WORKFLOW_BLOCKED`.

Die maschinelle Prüfung und das Routing liefern `STANDALONE`, `WORKFLOW` oder
`WORKFLOW_BLOCKED`. Eine ungültige explizite Aktivierung wird immer
`WORKFLOW_BLOCKED`; ihr enthaltener Auftrag darf nicht als Standalone-Auftrag
ausgeführt werden. Ein gültiger Start bindet den Chat an Task-ID, Profil,
Generation und Revision. Ein anderer Auftrag in diesem Chat verweist auf einen
frischen Chat. Ein Bridge-Ausfall blockiert nur die explizit angeforderte
Workflow-Aktivierung, niemals die normale Standalone-Nutzung.

## 1.1 PC-Runtime und GitHub-Kurzpass

Task Capsule, Handoff, Worker, Verifier, Cricket und Logs werden vollständig
auf dem PC verarbeitet. GitHub darf für v2 höchstens
`coordination-bridge/tasks/<task_id>.json` als kurzen, nicht sensiblen Statuspass
enthalten. Dieser Pass hat exakt neun Felder: `schema_version`, `task_id`,
`role`, `generation`, `revision`, `status`, `requirements_sha256`,
`handoff_sha256` und `next_action`. Für direkte Codex-Vermittlung muss die
lokale PC-Runtime laufen; der GitHub-Pass ersetzt sie nicht.

## 1. Vertrauensgrenzen und Hauptgehirne

Es gibt zwei getrennte Hauptgehirne:

- **KGG Admin GPT** fuehrt Admin-/Therapeut:innen-Preview-Aufgaben innerhalb des
  bestehenden Admin-Gates.
- **KGG Patient GPT** fuehrt Patient:innen-PWA-Aufgaben innerhalb des
  bestehenden Patient-Preview-Gates.

Admin GPT und Patient GPT teilen keine Chatgeneration, keine Ergebnisannahme und
keine produktive Schreibberechtigung. Ein Cross-App-Thema wird nur ueber die
bestehende private Coordination Action mit nicht sensiblen Fakten uebergeben.
Eine Queue-Antwort startet den jeweils anderen GPT nicht automatisch.

Pro Ticket gibt es genau **einen** Lead-GPT. Der Lead gehoert immer zu genau
einem Profil (`admin` oder `patient`), synthetisiert optionale Unter-Chats und
nimmt deren Ergebnis ab. Es gibt hoechstens vier sauber getrennte Custom-GPT-
Unter-Chats pro Ticket. Ein Unter-Chat darf keine Anforderungen umdeuten oder
den Lead ersetzen.

## 2. Verbindlicher Routinggraph (nur in WORKFLOW)

Nach einer gültigen Aktivierung läuft die Entwicklungsaufgabe in dieser
Reihenfolge:

```text
Luna Manager
  -> genau ein Lead-GPT
  -> optional 1 bis 4 getrennte GPT-Unter-Chats
  -> derselbe Lead-GPT: Synthese und Abnahme
  -> Luna Relay
  -> Luna-Max-Worker (bis zu 3 disjunkte Worker-Scopes, optional ein Verifier)
  -> Luna Relay
  -> derselbe Lead-GPT
  -> CI und menschliche Abnahme
```

Die Unter-Chats koennen parallel laufen, bleiben aber innerhalb einer einzelnen
Task Capsule und werden vor der Lead-Synthese zusammengefuehrt. Der Relay ist
ein Transport- und Kompressionsknoten. Er darf keine Anforderungen veraendern,
keine neue grosse Aufgabe loesen und keine fehlende Entscheidung erfinden.

Eine reine Statusabfrage bleibt `STANDALONE`, ist read-only und darf weder Task
Capsule noch Scope, Ticket oder Ziel verändern.

## 3. Rollen und Modellregel

| Rolle | Modell/Modus | Darf | Darf nicht |
| --- | --- | --- | --- |
| Luna Manager | `GPT-5.6 Luna`, Low | Auftrag klassifizieren, Lead bestimmen, Capsule anlegen | programmieren, Ticket schliessen, Scope vergroessern |
| Admin Lead-GPT | KGG Admin GPT | Admin-Kontext lesen, Unter-Chats beauftragen, synthetisieren und abnehmen | Patient-GPT ersetzen oder Main-Gate freischalten |
| Patient Lead-GPT | KGG Patient GPT | Patient-Kontext lesen, Unter-Chats beauftragen, synthetisieren und abnehmen | Admin-GPT ersetzen oder Patient-Live freischalten |
| GPT-Unter-Chat | passendes Custom GPT | genau einen abgegrenzten Analyse-/Vorschlags-Scope liefern | Lead-Annahme oder Gate-Aufruf vortaeuschen |
| Luna Relay | `GPT-5.6 Luna`, Low | Capsule/Ergebnis verlustarm transportieren und komprimieren | Anforderungen, Testziele oder Hashes aendern |
| Luna-Max-Worker | `GPT-5.6 Luna`, Max | genau einen disjunkten Implementierungs-Scope bearbeiten | anderen Worker steuern oder rekursiv delegieren |
| Verifier | `GPT-5.6 Luna`, Max | eigenen Verifier-Scope und Belege pruefen | den Worker-Scope erweitern oder selbst delegieren |
| Cricket | `GPT-5.6 Luna`, Low | global beobachten, L0-L3 dokumentieren, Eskalation markieren | Projektproblem loesen oder Code schreiben |
| Ticket Master | `GPT-5.6 Luna`, Low | lesen, Dubletten pruefen, ueber Memory Gate anlegen | programmieren, schliessen oder etwas erfinden |
| Sol Endboss | `GPT-5.6 Sol`, Ultra | nur eine explizit freigegebene Endboss-Entscheidung | Code, Repo-Grossanalyse, Debug, Test, Repair, Micromanagement |

Terra wird fuer diese Rollen nicht verwendet. Modelllabels in der UI sind kein
Beweis fuer einen tatsaechlichen Lauf; es zaehlen nur sichtbare Action-, Run-
und Ergebnisbelege.

## 4. Task Capsule

Die Task Capsule ist die unveraenderliche Arbeitsgrundlage fuer alle Handoffs.
Sie wird bei einer Anforderung erstellt und bei jeder Generation/Revision
neu als neue Capsule referenziert; alte Generationen werden nicht umgeschrieben.

Pflichtfelder:

| Feld | Vertrag |
| --- | --- |
| `schema` | exakt `kgg-brain-relay-worker/v2` |
| `task_id` | stabile Kleinbuchstaben-ID, 6 bis 64 Zeichen |
| `ticket` | `ticket_id`, `duplicate_checked: true`, `source: private-memory-gate`; keine erfundene ID |
| `profile` | genau `admin` oder `patient` |
| `lead` | genau ein Lead mit Profil, Chat-ID, Generation und Revision |
| `generation` | positive Generation des Chats; nur frischer Nachfolgechat erhoeht sie |
| `revision` | positive Capsule-Revision innerhalb der Generation |
| `requirements` | Nutzeranforderung plus `sha256`; diese Zeichenkette bleibt identisch |
| `acceptance` | nicht leere, beobachtbare Abnahmekriterien |
| `scope` | `allowed` und `forbidden`; keine implizite Scope-Ausweitung |
| `sub_chats` | null bis vier eindeutige Chats mit eigenem Scope |
| `workers` | hoechstens drei `luna-max-worker` plus hoechstens ein `verifier` |
| `route` | der verbindliche Routinggraph oder der Status-Read-Sonderweg |
| `retry` | maximal zwei substantielle Luna-Versuche vor Lead-Eskalation |
| `rotation` | 35/40-Event-Grenzen sowie Generation-/Revision-Drift |
| `locks` | Merge, Release, Deploy, Ticketabschluss und Scope-Ausweitung bleiben gesperrt |

Ein minimales synthetisches Beispiel sieht so aus:

```json
{
  "schema": "kgg-brain-relay-worker/v2",
  "task_id": "kgg-brain-example-001",
  "ticket": {
    "ticket_id": "kgg-ticket-example-001",
    "duplicate_checked": true,
    "source": "private-memory-gate"
  },
  "profile": "admin",
  "generation": 1,
  "revision": 1,
  "lead": {
    "role": "lead-gpt",
    "profile": "admin",
    "chat_id": "kgg-admin-lead-example",
    "generation": 1,
    "revision": 1
  },
  "requirements": {
    "text": "Nur die KGG-Koordination dokumentieren; Produktcode bleibt ausserhalb.",
    "sha256": "580833556747fc63032232cee6b15f3db79486b5eb3bdafdf61335cfc4bc145d"
  },
  "acceptance": [
    "Jede aktivierte Workflow-Entwicklungsaufgabe verwendet den vollstaendigen Routinggraphen.",
    "Ein Handoff behaelt requirements.sha256 bytegleich."
  ],
  "scope": {
    "allowed": ["Playbooks", "Actions", "Koordinationsvertrag", "synthetische Tests"],
    "forbidden": ["Patientdaten", "Produktcode", "Releases", "Main-/Live-Gates"]
  },
  "sub_chats": [],
  "workers": [
    {
      "worker_id": "worker-contract",
      "role": "luna-max-worker",
      "scope": "KGG-Vertrag und lokale Tests",
      "generation": 1,
      "revision": 1
    },
    {
      "worker_id": "verifier-contract",
      "role": "verifier",
      "scope": "Vertrags- und Sicherheitspruefung",
      "generation": 1,
      "revision": 1
    }
  ],
  "route": [
    "luna-manager", "lead-gpt", "lead-synthesis", "luna-relay",
    "luna-max-worker", "luna-relay", "lead-gpt", "ci-acceptance"
  ],
  "retry": {
    "luna_attempts": 0,
    "max_luna_attempts": 2,
    "after_exhaustion": "lead-gpt",
    "sol_gate": "cricket-one-time"
  },
  "rotation": {
    "meaningful_events": 0,
    "prepare_at": 35,
    "hard_at": 40,
    "role_drift": false,
    "revision_drift": false,
    "successor": "fresh-chat",
    "codex_successor": "fresh-chat",
    "custom_gpt_successor": "browser-new-chat",
    "fork_allowed": false,
    "old_generation": "ACTIVE"
  },
  "locks": {
    "merge": true,
    "release": true,
    "deploy": true,
    "ticket_close": true,
    "scope_expansion": true
  }
}
```

Die Anforderungen werden nicht aus einem Relay-Text rekonstruiert. Jeder
Relay-Handoff fuehrt den gleichen `requirements.sha256`-Wert und die gleiche
`task_id`, Generation und Revision. Bei Abweichung gilt `stale_generation`
oder `requirements_changed`; der Lead muss neu synthetisieren.

## 5. Handoff- und Ergebnisformat

Die vollstaendige Coordination-v2-Runtime liest und verarbeitet Task, Handoff
und Cricket-Fakten lokal auf dem PC. Der optionale GitHub-Read ist für v2 auf
`coordination-bridge/tasks/{task_id}.json` mit der exakten Neun-Felder-Allowlist
begrenzt. Dort stehen keine Patientendaten, QR-Rohdaten, Secrets, Prompts oder
Logs. Die bestehenden vier v1-Operationen bleiben unveraendert; es gibt keine
separaten v2-Task-, Handoff- oder Cricket-Pfade.

Ein Handoff traegt mindestens:

```json
{
  "schema": "kgg-brain-relay-worker/handoff-v2",
  "event_id": "kgg-event-example-001",
  "sequence": 1,
  "event_type": "worker_result",
  "task_id": "kgg-brain-example-001",
  "generation": 1,
  "revision": 1,
  "from_role": "luna-max-worker",
  "to_role": "luna-relay",
  "requirements_sha256": "580833556747fc63032232cee6b15f3db79486b5eb3bdafdf61335cfc4bc145d",
  "transport_only": true,
  "summary": "Der abgegrenzte Vertragsscope wurde umgesetzt.",
  "evidence": [{"kind": "test", "name": "brain-relay-selftest", "status": "PASS"}],
  "handoff_sha256": "8465bcf6557676415e235a8826f8fe0c79ac7c5db1bbd52024ad3cebc43feff4",
  "append_only": true
}
```

Das standardisierte Ergebnisformat ist fuer Worker, Verifier, Relay, Lead und
CI gleich. `status` ist genau einer von `PASS`, `FAIL`, `BLOCKED`, `PENDING`,
`NEEDS_LEAD` oder `NEEDS_SOL`. Ein Ergebnis nennt immer Scope, Versuch,
Anforderungs-Hash, kurze Zusammenfassung, sichtbare Belege und die naechste
Aktion. `COMPLETE` wird nur vom Lead/CI nach gruener Abnahme und ueber ein
Coordination-Completion-Event gemeldet.

Blocker benoetigen `blocker.level` (L0-L3), `blocker.code`, `blocker.owner`
und `blocker.next_action`. `NEEDS_SOL` ist erst nach zwei substantiell
unterschiedlichen Luna-Versuchen, Lead-Review und Cricket-Eskalation zulaessig.
Ein Ergebnis ohne Beleg ist kein Abschluss.

## 6. Retry- und Parallelregel

- Luna darf hoechstens zwei substantiell unterschiedliche Versuche liefern.
- Unterschiedlich bedeutet: anderer technischer Ansatz und eigener
  Ansatz-Hash, nicht nur ein anderer Text oder eine neue ID.
- Nach Versuch zwei geht der Fall an denselben Lead zur Synthese/Entscheidung.
- Erst danach darf ein Lead mit Cricket einen `NEEDS_SOL`-Blocker markieren.
- Es laufen hoechstens drei Luna-Max-Worker und ein Verifier parallel.
- Worker-Scopes sind paarweise disjunkt; ein Worker darf keinen anderen Worker
  starten oder sich rekursiv erneut delegieren.
- Ein Verifier ist kein vierter Implementierungs-Worker und darf den Scope nicht
  erweitern.

## 7. Chatrotation und Generationen

Ein **meaningful event** ist ein sichtbares Handoff, Ergebnis, Retry, Blocker,
Cricket-Ereignis oder eine CI-/Abnahmeentscheidung. Reine Heartbeats und
identische Statusabfragen werden nicht gezählt.

- Bei 35 meaningful events: `PREPARE_ROTATION`; Capsule einfrieren und
  Nachfolge-ID vorbereiten.
- Bei 40 events: harter Wechsel; die alte Generation wird `RETIRED`.
- Ein frueher Rollen-, Profil-, Requirements- oder Revisions-Drift erzwingt
  sofort den harten Wechsel.
- Ein Codex-Nachfolger ist frisch, niemals ein Fork.
- Ein Custom-GPT-Nachfolger entsteht browsergesteuert ueber **Neuer Chat**.
  Vor dem ersten Handoff werden Task-ID, Generation, Revision und Handoff-Hash
  gegenseitig bestaetigt.
- Die alte Generation darf nur noch lesend fuer die Migration geoeffnet werden
  und erhaelt den Zustand `RETIRED`.

### Kanonische Chatnamen

```text
KGG Admin GPT | <task_id> | Lead | g<generation>-r<revision>
KGG Patient GPT | <task_id> | Lead | g<generation>-r<revision>
KGG GPT Sub | <task_id> | Scope-<n> | g<generation>-r<revision>
KGG Luna Relay | <task_id> | <direction> | g<generation>-r<revision>
KGG Max Worker | <task_id> | Scope-<n> | g<generation>-r<revision>
KGG Verifier | <task_id> | Scope-<n> | g<generation>-r<revision>
RETIRED | <old-name> | g<generation>-r<revision>
```

Die vorhandenen Kandidaten `KGG Update-Agent` und `KGG Patienten-App
Update-Agent` werden nur als Admin- beziehungsweise Patient-Lead-Kandidaten
uebernommen, wenn Profil, Task-ID und Zweck eindeutig passen. Die Migration
setzt keine alte Unterhaltung fort: Sie erstellt einen frischen Chat, legt die
Capsule als erste Nachricht ab und bestaetigt die vier Identitaetswerte. Bei
unklarem Kandidaten wird nichts umbenannt. Unrelated Chats werden niemals
angefasst.

## 8. Browser-Relay und Fallback

Fuer bis zu vier Custom-GPT-Unter-Chats gilt ein gemeinsamer Browser-Relay-Lauf:

- Nachrichten werden in einem Lauf versendet.
- Danach wird ohne Statusprompt auf Ergebnis oder Timeout gewartet.
- Harte Zeitgrenze: 30 Minuten.
- Es gibt hoechstens einen frischen Retry; der Retry bekommt eine neue
  Generation/Revision und denselben unveraenderten Requirements-Hash.
- Completion und Blocker werden ueber die bestehende Coordination Action als
  append-only Event geschrieben.
- Ist die Action nicht verfuegbar, darf der Browser-Fallback nur denselben
  nicht sensiblen Eventinhalt transportieren. Er ist kein neuer Schreibvertrag,
  kein Ticketabschluss und keine Freigabe.

Ein sichtbarer Button oder ein UI-Label beweist weder laufende Arbeit noch
Completion. Nur sichtbarer Antworttext, Action-Ergebnis, Run-Beleg oder stabiler
Textzustand darf als Nachweis verwendet werden.

## 9. Cricket-Watchdog und L0-L3

Cricket beobachtet global und dokumentiert Fakten, ohne das Projektproblem zu
loesen:

| Stufe | Bedeutung | Aktion |
| --- | --- | --- |
| L0 | Hinweis/Beobachtung ohne Blockierung | sichtbares Ereignis notieren |
| L1 | technischer Vertragsverstoss, lokal beweisbar | Write/Weiterleitung blockieren, Code nennen |
| L2 | wiederholter oder koordinierter Blocker | Lead und Manager informieren, naechsten Beleg verlangen |
| L3 | zwei unterschiedliche Luna-Versuche plus Lead-Review ohne Loesung | `NEEDS_SOL` zur einmaligen Endboss-Entscheidung markieren |

Jedes Cricket-Ereignis unterscheidet:

- **technisches Enforcement**: maschinell pruefbar, zum Beispiel stale
  Generation, mehr als vier Unter-Chats, ueberlappende Scopes, falsche Route,
  falscher Hash oder ein unzulaessiger Sol-Request;
- **Policy-only**: eine Prozessregel ohne lokale technische Durchsetzung; sie
  wird als solche markiert und nicht als Beweis einer Kontrolle ausgegeben;
- **Proxy**: ein sichtbarer Indikator fuer einen Zustand, zum Beispiel UI-Label,
  Browser-Button oder Chatname; er beweist nicht den unsichtbaren Zustand.

Es gibt keine Schein-Kontrolle fuer hidden CoT, unsichtbare Agenten, exakte
Token-/Creditwerte oder nicht vorhandene Stop-Funktionen. Sol bleibt `SLEEPING`.
Code, Repo-Grossanalyse, Debug, Test, Repair und Micromanagement sind fuer Sol
gesperrt. Interne Sol-Agenten sind nur nach einer einmaligen, expliziten
Cricket-Eskalationsfreigabe zulaessig und koennen dadurch keine Produkt- oder
Release-Aktion erhalten.

## 10. Ticket Master und Locks

Der Ticket Master:

1. liest den privaten Memory-Router;
2. prueft vor einer Anlage auf Dubletten;
3. legt ein nicht sensibles Ticket ausschliesslich ueber das private Memory
   Gate an;
4. uebergibt `ticket_id` und Capsule an den Manager.

Er programmiert nicht, schliesst kein Ticket und erfindet weder IDs noch
Anforderungen. Ticketabschluss, Merge, Release, Deploy und Scope-Ausweitung
bleiben gesperrte Aktionen. Es gibt keine staendigen OK-Fragen innerhalb des
freigegebenen Scopes; nur echte Mehrdeutigkeit, Memory-Konflikt, stale Context,
Breaking Interface oder ein finales Gate stoppt den Ablauf.

## 11. Einfache Runbooks und Startprompts

### Luna Manager

Runbook: Auftrag lesen -> Status oder Entwicklungsaufgabe unterscheiden ->
Profil bestimmen -> genau einen Lead benennen -> Capsule mit Anforderungen,
Scope, Tests, Generation und Locks anlegen -> an Lead uebergeben.

Startprompt:

> Lies den Auftrag unveraendert. Erzeuge eine `coordination-v2` Task Capsule,
> fuehre den Dublettencheck ueber den Ticket Master an, bestimme genau einen
> passenden Admin- oder Patient-Lead und starte den verbindlichen Routinggraphen.
> Bei einer reinen Statusfrage nutze nur den Read-Weg. Programmiere nicht,
> schliesse kein Ticket und erweitere keinen Scope.

### Luna Relay

Runbook: Capsule und Requirements-Hash pruefen -> Zielrolle pruefen -> Inhalt
komprimieren -> Hash, Generation, Revision und Scope unveraendert transportieren
-> einen append-only Handoff melden.

Startprompt:

> Transportiere diese Capsule verlustarm an die angegebene Zielrolle. Veraendere
> keine Anforderung, keinen Test, keinen Hash und keinen Scope. Loese die grosse
> Aufgabe nicht selbst. Bei Abweichung melde `stale_generation` oder
> `requirements_changed` an den Lead.

### Cricket

Runbook: sichtbare Events lesen -> L0-L3 klassifizieren -> Enforcement,
Policy-only und Proxy trennen -> nur Blocker/Eskalation dokumentieren -> keine
Reparatur und keine neue Aufgabe starten.

Startprompt:

> Beobachte nur den sichtbaren Coordination-Zustand. Dokumentiere L0-L3 mit
> Beleg, unterscheide technische Durchsetzung von Policy-only und Proxy und
> markiere erst nach zwei verschiedenen Luna-Versuchen plus Lead-Review einen
> moeglichen `NEEDS_SOL`-Fall. Loese kein Projektproblem.

### Ticket Master

Runbook: Memory-Index lesen -> passende Packs minimal laden -> Dublettencheck ->
bei Bedarf ein nicht sensibles Ticket ueber das Memory Gate anlegen -> Resultat
an Manager senden.

Startprompt:

> Arbeite nur als Ticket Master. Lies und pruefe auf Dubletten. Lege nur nach
> erfolgreichem Check ueber das private Memory Gate an. Programmiere nicht,
> schliesse nicht und erfinde keine ID, Anforderung oder Prioritaet.

### Admin Lead-GPT

Runbook: aktuellen Admin-Kontext und Action-Hashes laden -> Capsule pruefen ->
optional bis zu vier disjunkte GPT-Unter-Chats beauftragen -> Antworten
synthetisieren und als derselbe Lead abnehmen -> Relay/Worker anweisen ->
Worker-Ergebnis nach Relay erneut pruefen -> bestehende CI-/Preview-Gates
verwenden.

Startprompt:

> Du bist der einzige Admin-Lead fuer diese Capsule. Halte Task-ID, Generation,
> Revision und Requirements-Hash fest. Nutze hoechstens vier abgegrenzte
> Unter-Chats, synthetisiere selbst und bestaetige nichts ohne sichtbare
> Belege. Admin- und Patient-GPT bleiben getrennt; Main-/Release-Gates bleiben
> gesperrt.

### Patient Lead-GPT

Runbook: aktuellen Patient-Kontext und Action-Hashes laden -> Capsule und
Patient-Scope pruefen -> optional bis zu vier disjunkte GPT-Unter-Chats
beauftragen -> selbst synthetisieren/abnehmen -> Relay/Worker anweisen ->
Ergebnis nach Relay und die bestehenden Patient-Preview-Belege pruefen.

Startprompt:

> Du bist der einzige Patient-Lead fuer diese Capsule. Veraendere nur den
> freigegebenen Patient-Scope und niemals Admin-/Release-Bereiche. Bewahre
> Requirements-Hash, Generation und Revision, nutze hoechstens vier
> Unter-Chats und melde Completion oder Blocker nur mit sichtbaren Belegen.

### Luna-Max-Worker

Runbook: genau einen disjunkten Scope uebernehmen -> Capsule-Hash pruefen ->
kleinste Umsetzung im freigegebenen KGG-Scope liefern -> sichtbare Tests/Belege
notieren -> Ergebnis an Relay zurueckgeben.

Startprompt:

> Bearbeite ausschliesslich Scope `<scope>` in Task `<task_id>`. Aendere keine
> Anforderungen und starte keinen weiteren Agenten. Liefere ein Ergebnis mit
> Versuch, Requirements-Hash, Belegen und naechster Aktion an den Relay.

### Verifier

Runbook: eigenen Verifier-Scope pruefen -> Anforderungen und Worker-Beleg
gegenlesen -> keine Reparatur ausserhalb des eigenen Scopes -> PASS/FAIL oder
BLOCKED an Relay melden.

Startprompt:

> Verifiziere nur den angegebenen Scope und die sichtbaren Belege. Erfinde keine
> Tests, erweitere den Scope nicht und delegiere nicht rekursiv. Melde bei
> Abweichung `NEEDS_LEAD` mit konkretem Beleg.

### Sol Endboss

Runbook: standardmaessig schlafen -> nur einen Cricket-L3-Blocker lesen -> eine
einmalige Freigabe pruefen -> hoechstens eine Endboss-Entscheidung formulieren;
keinen Code, keine Grossanalyse, keinen Test und keinen Repair ausfuehren.

Startprompt:

> Bleibe `SLEEPING`. Akzeptiere nur eine explizite einmalige Cricket-
> Eskalationsfreigabe fuer eine Endboss-Entscheidung. Schreibe keinen Code,
> analysiere kein grosses Repo, debugge, teste oder repariere nicht und fuehre
> kein Micromanagement aus. Keine Produkt-, Merge-, Release- oder Deploy-
> Entscheidung simulieren.

## 12. Abschluss- und Blockerbericht

Jeder Coordination-Abschluss verwendet dieses Format:

```text
Status: PASS | BLOCKED | NEEDS_SOL | PENDING
Task-ID: <task_id>
Ticket-ID: <ticket_id oder nicht angelegt>
Profil: admin | patient
Lead: <chat_id>
Generation/Revision: g<generation>-r<revision>
Route: <sichtbare Route>
Versuch: <0, 1 oder 2 Luna-Versuche>
Handoff-Hash: <sha256 oder nicht berechnet>
Requirements-Hash: <sha256>
Belege:
- <Action/Run/Test/CI-Beleg mit Status>
Blocker: <code und L0-L3, falls vorhanden>
Naechste Aktion: <konkreter read-only oder freigegebener Handoff>
Locks: Merge=gesperrt, Release=gesperrt, Deploy=gesperrt, Ticketabschluss=gesperrt
```

`PASS` bedeutet nur Lead-/CI-Abnahme mit den passenden sichtbaren Belegen.
`BLOCKED` nennt den technischen oder menschlichen Grund. `NEEDS_SOL` nennt
zusaetzlich die beiden unterschiedlichen Luna-Ansatz-Hashes und die Cricket-
Freigabe. Ein Completion-Event wird zuerst validiert und dann identisch als
append-only Event ueber die bestehende Coordination Action angewendet.
