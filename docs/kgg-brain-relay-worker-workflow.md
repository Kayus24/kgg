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

### 2.1 Entry-Modi und modellneutrale Strategiephase (Revision 1)

Die zentrale Modusregel bleibt unveraendert: `BOSS_FIRST` und
`SUPERVISOR_FIRST` sind keine Alternativen zur expliziten
`STANDALONE -> WORKFLOW`-Aktivierung.

- `SUPERVISOR_FIRST` ist Standard. Luna Manager bestimmt genau einen operativen `lead-gpt`.
- `BOSS_FIRST` bedeutet, dass derselbe eine `lead-gpt` vor der operativen
  Zerlegung eine modellneutrale strategische Planungsphase ausfuehrt.
- Es gibt keine zweite Lead-Rolle und keine neue Sol-Rolle.
- `sol-endboss` bleibt `SLEEPING` und nur ueber Cricket-L3 zulaessig.

Work-Modes:

```text
reasoning:
  Luna Manager -> Lead GPT -> GPT-Unter-Chat -> Lead-Synthese
  -> derselbe Lead GPT -> CI/Abnahme

implementation:
  Luna Manager -> Lead GPT -> Lead-Synthese -> Luna Relay
  -> Luna-Max-Worker -> Luna Relay -> derselbe Lead GPT -> CI/Abnahme

mixed:
  Luna Manager -> Lead GPT -> GPT-Unter-Chat -> Lead-Synthese -> Luna Relay
  -> Luna-Max-Worker -> Luna Relay -> derselbe Lead GPT -> CI/Abnahme
```

`reasoning` hat 1-4 GPT-Unter-Chats und keine Implementierungsworker.
`implementation` hat 1-3 Implementierungsworker und keine GPT-Unter-Chats.
`mixed` hat mindestens einen GPT-Unter-Chat und mindestens einen Worker.
Der Verifier bleibt separat und ist kein vierter Implementierungsworker.

Kompatibilitaetsregel: Bestehende v2-Capsules ohne `entry_mode` und
`work_mode` werden strukturell unveraendert validiert und behalten exakt den
bisherigen vollstaendigen Development-Routenvertrag. Nur ein explizites
`work_mode` aktiviert die neuen Rev1-Routenregeln. Ein fehlendes
`entry_mode` wird semantisch als `SUPERVISOR_FIRST` interpretiert, aber nicht
in die Capsule hineingeschrieben.

### 2.2 Lokale Supervisor-State-Machine und 60-Sekunden-Read

Die State-Machine gehoert nur zur lokalen PC-Runtime und erweitert weder
Bridge-Allowlist noch `TASK_STATES`.

Lokale Zustaende:
`PLANNING`, `DISPATCH_READY`, `CHILD_RUNNING`, `RESULT_PENDING`,
`LEAD_REVIEW`, `WAITING_MAX`, `IDLE_NEEDS_LEAD`, `VERIFYING`, `COMPLETE`,
`BLOCKED`.

`IDLE_NEEDS_LEAD` ist nur zulaessig, wenn Acceptance nicht erfuellt ist,
kein Blocker/`WAITING_MAX` vorliegt, kein Child laeuft, kein Ergebnis wartet,
kein Workitem dispatchbereit und kein Lead-Review ausstehend ist. Beim ersten
Eintritt wird genau ein `NEEDS_LEAD` angefordert. Unveraenderte Folge-Polls
erzeugen keine weitere Nachricht und kein meaningful event.

Der lokale Supervisor darf alle 60 Sekunden read-only pruefen. Reine Polls
erzeugen keine Chat-Statusprompts und zaehlen nicht als meaningful events.
`WAITING_MAX` bleibt still. 30-Minuten-Browserlimit und maximal ein frischer
Retry bleiben unveraendert.


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
| `entry_mode` | optional: `SUPERVISOR_FIRST` oder `BOSS_FIRST`; fehlt das Feld, gilt semantisch `SUPERVISOR_FIRST`, ohne die Legacy-Capsule zu veraendern |
| `work_mode` | optional bei Development: `reasoning`, `implementation` oder `mixed`; fehlt das Feld, gilt exakt der bestehende v2-Legacy-Routenvertrag |
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
