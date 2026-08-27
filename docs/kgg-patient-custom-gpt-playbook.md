# KGG Patient Custom GPT Playbook

## Brain-Relay-Worker-Workflow v2

Der gemeinsame, additive Rollen- und Handoff-Vertrag steht in
`docs/kgg-brain-relay-worker-workflow.md`. Lade ihn fuer echte Aufgaben neben
diesem Patient-Playbook. Der Patient-Lead bleibt das einzige Patient-
Hauptgehirn; Admin GPT und Patient GPT werden nie vermischt.

- Pro Ticket genau ein Patient-Lead-GPT. Echte Aufgaben verwenden den
  vollstaendigen Weg `Luna Manager -> Lead GPT -> optionale GPT-Unter-Chats ->
  Lead-Synthese -> Luna Relay -> Luna-Max-Worker -> Relay -> derselbe Lead ->
  CI/Abnahme`; nur reine Statusabfragen duerfen GPT ueberspringen.
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
- Coordination-v2 ergaenzt nur sichere Lesewege: `getKggAgentCoordinationTask`,
  `getKggAgentCoordinationHandoff` und `getKggAgentCricketEvent`. Die bestehende
  append-only `submitKggAgentCoordinationEvent`-Action bleibt der einzige
  Koordinations-Schreibweg. Admin-Threads werden nie als Patient-Threads
  verarbeitet.

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
