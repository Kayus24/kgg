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

## Modi

- `validate_only`: Payload, Allowlist, Source-Hashes und naechste Version pruefen; kein Repository-Write.
- `publish_preview`: identischen validierten Payload anwenden, Tests ausfuehren und isolierte GitHub-Pages-PWA publizieren.
- `create_pr`: nur nach akzeptiertem identischem Preview einen PR erstellen; nie mergen.
- `publish_patient_live`: nur nach Max' ausdruecklicher Preview-Freigabe einen PR erstellen; Merge wartet auf Required Checks und `patient-live` Environment Approval.

## Konsequenz

Dispatch-Actions und Memory-Updates sind consequential. Read-, Run-, Job- und Artifact-Actions sind nicht consequential.

Die Action darf keine Patientendaten, echten Planpayloads, Secrets oder Roh-Base64 uebertragen. Preview-Plaene werden ausschliesslich im Gate synthetisch erzeugt.
