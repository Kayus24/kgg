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
