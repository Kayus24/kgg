# KGG Patient GPT Knowledge: Operations

Generated retrieval pack. Source digest: `9d04ad0e3691d22e`.

Live GitHub context and source files override this static Knowledge pack.

---

# Source: docs/kgg-patient-custom-gpt-playbook.md

# KGG Patient Custom GPT Playbook

## Auftrag und Grenze

Der Agent diagnostiziert und repariert die Root-PWA fuer Patient:innen. Er darf `index.html`, `service-worker.js`, `update-recovery.html`, Manifest-Dateien, `patient-*.js`, `collapse-cards.js` und `numpad-ui-fix.js` ueber das Patient Preview Gate bearbeiten.

Nicht erlaubt sind Therapeut:innen-App, PDF, Android/APK, API-Key-Logik, binaere Icons sowie ein Breaking Change an KGGH2, KGGD1 oder Patientenspeicher. Schnittstellenaenderungen muessen additiv und rueckwaertskompatibel sein.

## Arbeitsfolge

1. Resource-Manifest, Live-Kontext und dieses Playbook live laden.
2. Bug-Lessons und Source-Index laden.
3. Symptom reproduzierbar beschreiben.
4. Hoechstens drei Hypothesen mit unterscheidenden Tests aufstellen.
5. Bestaetigte Ursache und kleinsten Fix bestimmen.
6. Mit `getKggPatientMainCommit` die aktuelle Main-SHA laden und den Payload gegen diese SHA sowie aktuelle Dateihashes bauen.
7. `validate_only` ausfuehren und erfolgreichen Run pruefen.
8. Identischen Payload mit `publish_preview` ausfuehren.
9. Preview-Metadaten, Artefakt und Test-URLs pruefen.
10. Max testet den Preview-Link im internen Browser.
11. Bei Ablehnung: `human_preview_fail`, Lektion festhalten und mit neuer `request_id` bei Schritt 1 beginnen.
12. Bei Zustimmung: `create_pr` oder nur auf ausdruecklichen Live-Auftrag `publish_patient_live`.

Die Schritte 7 bis 9 sind vorab freigegeben und laufen ohne Zwischenfrage. PR und Live erfordern die exakte Phrase `Gut für PAT live`. Nur echte Mehrdeutigkeit, ein Memory-Konflikt oder ein Breaking Interface rechtfertigt vorher eine Rueckfrage.

Offene Cross-App-Anfragen stehen im privaten Koordinationsindex. Der Patient-Agent liest nur passende Threads, antwortet append-only und speichert dort weder Patientendaten noch echte Plan-/QR-Payloads. Eine Queue-Antwort startet den anderen GPT nicht automatisch. Die Queue ist fuer Interface-/Cross-App-Arbeit Pflicht. Bei rein visuellen Patient-UI-Patches darf ein Queue-Ausfall als `coordination_unavailable` protokolliert werden, ohne einen ansonsten frisch belegten Patch zu blockieren.

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

`submitKggPatientPreviewGate` ist Preview-only und vorab freigegeben. `submitKggPatientMainGate` ist getrennt, consequential und akzeptiert PR/Live nur mit `approval_phrase: "Gut für PAT live"`.

## Konsequenz

Preview-only- und abgesicherte Koordinations-Actions sind vorab freigegeben und nicht consequential. Main-/Live-Actions bleiben consequential. Memory-Konflikte bleiben mechanisch zustimmungspflichtig.

Die Action darf keine Patientendaten, echten Planpayloads, Secrets oder Roh-Base64 uebertragen. Preview-Plaene werden ausschliesslich im Gate synthetisch erzeugt.
