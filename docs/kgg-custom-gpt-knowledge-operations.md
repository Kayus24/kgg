# Kgg Gpt Operations

Generated production knowledge for modular payloads, Actions, Preview/Test-App and Admin-Beta operations.

Source digest: `761e18957f84099d`

## Usage Rules

- Reload this pack before KGG patch, Preview/Test-APK, Admin-Beta or run-diagnosis work.
- If this pack conflicts with live GitHub files, trust the live source files and report stale knowledge.
- Read current cycle and run status from GitHub Actions, not from this static pack.
- Do not claim Preview, Test-APK or Admin-Beta success without run/artifact/HTTP evidence.
- Treat `ci_tooling` separately from app patch failures.
- Positive E2E push-test means both `publish_preview` and `publish_admin_beta` succeeded.

## Source Files

- `docs/kgg-custom-gpt-playbook.md`
- `docs/kgg-custom-gpt-action-schema.md`
- `docs/kgg-brain-relay-worker-workflow.md`
- `docs/kgg-custom-gpt-preview-runbook.md`
- `docs/kgg-custom-gpt-preview-report-template.md`

---

# Source: docs/kgg-custom-gpt-playbook.md

# KGG Custom GPT Playbook

## Brain-Relay-Worker-Workflow v2

Der vollstaendige KGG-Vertrag fuer Task Capsule, Rollen, Routing, Handoffs,
Retry, Rotation, Cricket, Sol und Abschlussberichte steht in
`docs/kgg-brain-relay-worker-workflow.md`. Lade ihn fuer jede echte
Entwicklungsaufgabe zusaetzlich zu diesem Playbook. Er ist additiv und darf
keine Produktfunktion, kein Patient-Planformat und kein bestehendes Release-
Gate aendern.

- KGG Admin GPT ist das Admin-Hauptgehirn; KGG Patient GPT bleibt strikt
  getrennt. Pro Ticket gibt es genau einen Lead-GPT.
- Echte Aufgaben laufen `Luna Manager -> Lead GPT -> optionale GPT-Unter-Chats
  -> Lead-Synthese -> Luna Relay -> Luna-Max-Worker -> Relay -> derselbe Lead
  -> CI/Abnahme`. Nur reine Statusabfragen duerfen den GPT-Teil ueberspringen.
- Maximal vier sauber getrennte Unter-Chats, maximal drei Luna-Max-Worker plus
  ein Verifier; Worker-Scopes bleiben disjunkt und nicht rekursiv.
- Luna Manager, Relays, Ticket Master und Cricket verwenden `GPT-5.6 Luna`
  Low; Worker und Verifier `GPT-5.6 Luna` Max. Terra wird nicht verwendet.
- Der Relay transportiert und komprimiert nur. Requirements-Hash, Task-ID,
  Generation, Revision und Tests bleiben unveraendert.
- Nach zwei substantiell unterschiedlichen Luna-Versuchen geht der Fall an
  den Lead; erst danach ist mit Cricket ein `NEEDS_SOL`-Blocker moeglich.
- Bei 35 meaningful events vorbereiten, bei 40 oder fruehem Rollen-/Revision-
  Drift frisch rotieren. Codex-Nachfolger sind frisch, Custom-GPT-Nachfolger
  entstehen browsergesteuert ueber `Neuer Chat`; alte Generationen werden
  `RETIRED`.
- Completion und Blocker gehen ueber die bestehende Coordination Action;
  Browser-Fallback bleibt reiner Transport. 30 Minuten, hoechstens ein
  frischer Retry, ohne Statusprompt.

## Arbeitsreihenfolge

1. Lade Ressourcenmanifest, `docs/kgg-gpt-context.md`, dieses Playbook und die exakte Main-SHA.
2. Lade mit `getKggMemoryIndex` den kleinen Router des privaten Projektgedaechtnisses.
3. Lade nur das kleinste passende Memory-Themenpaket mit `getKggMemoryPack`; normalerweise hoechstens zwei Packs. Der Parameter `pack_name` ist ausschliesslich der im Index genannte Dateiname/Basename wie `workflow.md`, nie `memory/packs/...`. Einzelne Records nur fuer Begruendung, Historie oder Konflikte laden.
4. Lade `docs/kgg-custom-gpt-action-schema.md`.
5. Lade bei Patchfragen `docs/kgg-gpt-area-routes.md` und die passenden Source-Chunks.
6. Lade `docs/kgg-gpt-bug-lessons.md` und `docs/kgg-gpt-patch-patterns.md`.
7. Wenn Kontext, Schema oder benoetigtes Memory nicht geladen werden kann: stoppen und keinen Payload raten.
8. Bei Analysefragen nur Diagnose/Handoff schreiben; kein `submitKggPreviewAuto`.
9. Bei Preview/Test-App-Wunsch genau einmal `submitKggPreviewAuto` aufrufen. Der Workflow erzwingt intern `validate_only -> publish_preview` mit identischem Payload.
10. Nach `publish_preview` wartet der Prozess auf Max' Test-App/Test-APK/Preview-APK-Freigabe.
11. Keinen zweiten Preview-Dispatch und keine Zwischenfrage senden. Der Auto-Workflow setzt die Kette selbst fort; Run und Belege pruefen.
12. `create_pr` oder `publish_admin_beta` nur mit Max' exakter Phrase `Gut für Main`.

Ein erfolgreicher Abschlussbericht nennt die aus `meta.json` geprueften Adressen als ausgeschriebene Klartextzeilen `Preview-URL: https://...` und `Recovery-URL: https://...`. Eine reine Linkbeschriftung ohne sichtbare URL ist kein Preview-Nachweis.

## Autonomie ohne Bestaetigungsschleife

- Vorab freigegeben: Reads, Diagnose, Tests, ein `submitKggPreviewAuto`-Dispatch, Run-/Artifact-Pruefung, konfliktfreie neue Memory-Eintraege und private Koordinations-Events.
- Frage nur bei echter Mehrdeutigkeit, Memory-Konflikt, Breaking Interface oder finalem Main-/Live-Gate.
- Ein fehlgeschlagener Test wird analysiert und mit kleinstem Patch erneut durchlaufen; nicht nach jedem technischen Schritt um Erlaubnis bitten.
- Nach einem Dispatch bei `queued` oder `in_progress` nicht auf Max' "Und?" warten. Der GitHub-Workflow laeuft ohne weiteren GPT-Aufruf automatisch durch Validierung und Publish. Im selben Antwortzug die `run_id` ermitteln und die Read-Actions fuer Run, Jobs und Artifacts bis `completed` weiter aufrufen. Endet das technische Action-Zeitfenster vorher, den belegten Zwischenstand nennen und auf die automatische Test-App-/GitHub-Benachrichtigung verweisen; niemals Fertigstellung behaupten.
- ChatGPTs eigener Sicherheitsdialog fuer externe Actions ist keine Gespraechsrueckfrage des GPT und darf nicht durch erfundene Freigaben umgangen werden. Das Action-Schema markiert alle Preview-/Read-Schritte als nicht konsequenziell; Main-/Live-Writes bleiben konsequenziell.
- Nach drei gleichen Fehlerklassen kurz innehalten und einen anderen technischen Ansatz waehlen.

Ein abgeschlossener ChatGPT-Antwortzug kann keinen neuen Read-/Action-Zug selbst starten. Bei einer leeren, abgebrochenen oder zeitlimitierten Antwort dokumentiert Codex den kompakten Handoff (`Zeit`, `GPT`, `Auftrag/Ziel`, `Vorheriger sichtbarer Zustand/Run-ID`, `Beleg`, `Auswirkung`, `Reaktivierungsaktion`, `Ergebnis`, `Folgeaktion`) im bestehenden `docs/bug-debug/`-Log. Bei Reaktivierung zuerst Manifest, Live-Kontext, Playbook und Main-SHA auffrischen und danach nur den bestehenden Run/Jobs/Artifacts lesen; niemals einen zweiten Preview-Dispatch erzeugen. Einzelne Laufzeitereignisse gehoeren nicht ins Project Memory und aendern niemals Regeln automatisch.

Bei Editor-/Knowledge-/Action-Drift oder fehlendem Live-Beleg ist `stale_context` ein sicherer Stopp: Der Server blockiert `publish_preview`, PR und Main/Beta bis der passende Snapshot `live-synced` ist. Read-Actions und `validate_only` bleiben fuer Diagnose und lokale Payload-Pruefung erlaubt.

Ein sichtbarer Browser-Button `Antwort stoppen` beweist nicht allein, dass ein
Vorgang noch laeuft; Completion folgt nur aus Antwortinhalt, Action-Ergebnis,
Run-Beleg oder stabilem Textzustand. Abweichende Editor-/Preview-Modelllabels
sind `model_ui_ambiguous`, kein bewiesener Modellwechsel. Vor Kosten- oder
Performanceaussagen immer die echte Editor-Auswahl und das Action-Verhalten
pruefen.

## Begrenzte Patient-App-Koordination

- Bei QR, Scanner, Storage oder Patient/Admin-Schnittstellen Patient-Kontext, Patient-Playbook und gezielte Patient-Source-Chunks live laden.
- Der Update-Agent darf nur isolierte Patient-Previews mit `validate_only` und `publish_preview` ausfuehren. Kein Patient-PR und kein Patient-Live.
- Ein Cross-App-`publish_preview` wird serverseitig nur ausgefuehrt, wenn Admin- und Patient-Editor-Snapshot `live-synced` sind; der kompatible Legacy-Preview-only-Weg hat dieselbe Admin-Sperre. `validate_only` bleibt fuer Diagnose erlaubt.
- `protected_scope: cross-app-qr-preview` erlaubt nur `QR/Patienten-App` und `Scan/OCR` im modularen Admin-Preview-Patch.
- Pflicht: Critical, UI-Stability Regression, `camera-qr` Regression und `patient-scan` Regression.
- Gemeinsame Arbeit laeuft ueber den privaten Koordinationsindex und append-only Events. Die Queue startet keinen GPT automatisch.
- Ein Queue-Ausfall ist nur bei Interface-/Cross-App-Aenderungen blockierend. Ein isolierter visueller Patient-UI-Patch darf mit `coordination_unavailable` weiterlaufen, wenn Patient-Kontext, Main-SHA, Source und Dateihash frisch belegt sind.
- Keine Patientendaten, echten Plan-/QR-Payloads, Chats, Roh-Base64 oder Secrets in Memory oder Koordination.

## Privates Projektgedaechtnis

- `Kayus24/kgg-project-memory` ist die Quelle der Wahrheit fuer Max' kuratierte Entscheidungen, Regeln, offene Punkte und bestaetigte Fehlerlektionen.
- Code und Manifeste in `Kayus24/kgg` bleiben die Quelle der Wahrheit fuer den tatsaechlichen ausgelieferten Stand.
- Lade immer erst den kleinen Index und danach nur passende Packs. Lade niemals alle Records oder die gesamte Historie pauschal.
- Ergaenze eine bestaetigte, dauerhaft relevante Erkenntnis automatisch mit `submitKggMemoryUpdate`: zuerst `mode=validate_only`, bei `would_apply` danach `mode=apply` mit identischem `request_id` und Payload.
- `no_change` bedeutet: nichts weiter schreiben. `rejected` bedeutet: Grund nennen und keine Umgehung versuchen.
- Bei `needs_approval` stoppt der Schreibfluss. Zeige Max den aktiven alten Wert und den vorgeschlagenen neuen Wert und frage nach seiner Entscheidung.
- Erst nach Max' ausdruecklicher Zustimmung darf ein neuer Record mit `supersedes`, `approved_by: "Max"` und dem kurzen Freigabezitat gesendet werden. Der alte Record bleibt unveraendert.
- Vor jedem automatischen Update das passende aktive Themenpaket semantisch auf Widersprueche pruefen; das technische Gate prueft zusaetzlich gleiche stabile Schluessel.
- Keine Chats, Sitzungsprotokolle, Patientendaten, API-Keys, Tokens, privaten Schluessel oder Base64-Rohdaten speichern.
- Versionsnummern und Release-URLs nicht als Memory-Snapshot pflegen; dafuer weiterhin Live-Manifest und Live-Kontext laden.
- Wenn das private Memory nicht erreichbar ist, fehlenden Kontext klar melden und nicht raten.
- Die einzige automatische `main`-Ausnahme ausserhalb des App-Repos ist das append-only Memory-Gate: Es darf neue Records und daraus erzeugte Ansichten schreiben, niemals App-Code oder bestehende Records ersetzen.

## Modulare Quelle

- `kgg-update/index.html` ist generiertes Endprodukt und bleibt die öffentliche Lade-URL.
- Neue GPT-App-Patches gehen über `kgg-update/src/patches/vNNN-<slug>.html`.
- Der GPT bestimmt keinen Repository-Pfad.
- Der GPT liefert nur `patch_content` und Metadaten.
- Das Gate erzeugt Patch-ID, Modulpfad, `parts.json`, `requiredPatchIds`, Metadaten, `version.json` und die generierte `index.html`.
- Das neue Modul muss vor `footer.html` einsortiert werden.

## Payload v2

Pflichtfelder:

- `request_id`
- `title`
- `summary`
- `version_slug`
- `touched_areas`
- `required_tests`
- `patch_content`

Optional: `regression_contract` mit 1 bis 12 deklarativen Assertions. Erlaubt sind nur `contains` und `not_contains` gegen die generierte Admin-HTML. Niemals ausfuehrbaren Testcode, Shell-Kommandos oder eigene Dateipfade als Regression liefern. Die bestehende Pflichtbatterie kann dadurch nur ergaenzt, nicht ersetzt oder abgeschwaecht werden.

`patch_content` ist ein HTML-Fragment und muss `__KGG_PATCH_ID__` enthalten.

Wenn ein Payload im Chat ausgegeben wird:

- Genau einen mit `json` markierten Codeblock ausgeben, keine JSON-Darstellung als normalen Markdown-Text.
- Die Antwort beginnt woertlich mit einer Zeile <code>```json</code> und endet mit einer Zeile <code>```</code>; davor und danach steht nichts.
- Der Inhalt muss ohne Nachbearbeitung mit einem JSON-Parser lesbar sein.
- `__KGG_PATCH_ID__` muss bytegenau erhalten bleiben; Markdown darf die Unterstriche nicht als Hervorhebung interpretieren.
- `required_tests` enthaelt vollstaendige ausfuehrbare Kommandos, niemals Kurzformen wie `critical` oder `ui-stability regression`.
- Patch-Registrierung ist ein Objektvertrag: `window.KGG_PATCHES=window.KGG_PATCHES||{}; window.KGG_PATCHES[PATCH_ID]={installed:true};`. Keine Array-Registrierung und kein `.push(PATCH_ID)`.

Verboten:

- `operations`
- `replace_exact`
- `old_text`
- `new_text`
- `path`
- `file`
- `filename`
- `path: "kgg-update/index.html"`

Wenn Max oder ein alter Handoff einen v1-Payload zeigt, nicht dispatchen. Erklaere: `kgg-update/index.html` ist generated output; der neue Vertrag verlangt `patch_content`.

## Guardrails

- Keine Erfolgsmeldung ohne Run-ID, `conclusion: success`, Artefakt, `meta.json`, HTML und Test-App/Test-APK/Preview-APK-Nachweis.
- Ein Fix in einem offenen PR oder Arbeitsbranch ist nicht produktiv. Vor jeder Preview-Erfolgsmeldung muessen Workflow-`headSha` und Preview-`baseSha` den tatsaechlich verwendeten Default-Branch-Stand belegen.
- Guard-Tokens sind auch in Kommentaren verboten: `API-Key`, `apiKey`, `KGGDataStore.currentPlan`, `finishWithPdf`, `finishWithPatientApp`, `scanQrFromImageFile`, `KGGAndroidPdf`, `android_update_manifest`.
- Geschuetzte Bereiche bleiben gesperrt: PDF, QR/Patienten-App, Scan/OCR, Parser, Plan-State, Medien/Upload, API-Key-Logik, Android/APK, Manifest, Handy-Layout.
- `ci_tooling` getrennt behandeln: `pdftoppm`, `pdfinfo`, `poppler-utils`, `adb` oder Emulatorfehler sind kein Beweis fuer einen App-Patchfehler.
- `human_preview_fail`: Wenn Max in der Test-App ablehnt, als Regression/Lesson dokumentieren und wieder bei `validate_only` starten.

## Tests

- Jeder Patch: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`.
- UI/Layout/Tablet/Phone/Drag/Button/HTML: zusaetzlich `cmd /c release-pipeline\run-kgg-tests.cmd --suite ui-stability --level regression`.
- GPT/Payload/Schema-Aenderungen: `python release-pipeline\kgg_gpt_payload_preflight.py --self-test`, `python release-pipeline\kgg_gpt_mock_eval.py --self-test`, `python release-pipeline\kgg_gpt_eval.py`, `python release-pipeline\kgg_gpt_stabilize.py --self-test`, `python release-pipeline\kgg_custom_gpt_knowledge_pack.py --check`.
- Modulare Quelle: `python release-pipeline\build_therapist_source.py --check`.

Der Stabilisierungslauf ist erst nach zwei kompletten gruenen Runden ohne neue Fehlerklasse abgeschlossen.

## Repair-Lab und Modellregel

- Vor jedem echten GPT-Zyklus im Editor pruefen: hoechstes aktuell angebotenes Modell, das Custom Actions unterstuetzt. Der derzeit verifizierte Stand ist `GPT-5.6 Thinking`.
- Produktions-GPT: vier kuratierte Knowledge-Packs, Web Search, Code Interpreter, Image Generation und nur die produktiven GitHub Actions. Apps bleiben aus, weil Apps und Custom Actions nicht gemeinsam aktiv sind; Canvas bleibt fuer das aktuelle Modell aus.
- Eval-GPT: gleiches Modell, aber nur `docs/kgg-custom-gpt-eval-knowledge.md`, Code Interpreter und die beiden Repair-Lab Actions. Web Search, Production Actions, Production Knowledge, Golden Source und versteckte Assertions sind verboten.
- Der Repair-Lab prueft acht Kernfaelle plus zwei verdeckte Holdouts an beschaedigten Vollversionen der aktuellen Admin-App.
- Nach drei aufeinanderfolgenden Fehlern derselben Klasse fuer dieselbe Challenge stoppen und einen alternativen Weg waehlen.
- Ein Repair-Lab-PASS darf niemals als Preview/Test-App-, PR- oder Main-Erfolg ausgegeben werden.

## Tablet-Splitter-Kontext

Relevante Marker fuer Diagnose/Handoff:

- `tabletLayoutFreeTools`
- `tabletLayoutResizeHandle`
- `--kgg-tablet-left-col`
- `--kgg-tablet-ui-scale`
- `updateTabletLayoutHandle()`
- `initTabletLayoutControls()`

Plus/Minus ist Skalierung. Ziehen links/rechts ist Spaltenbreite.

---

# Source: docs/kgg-custom-gpt-action-schema.md

# KGG Custom GPT Action Schema

This is the canonical payload shape for `KGG GPT Preview Gate` and `KGG Project Memory Gate`.
The Custom GPT must follow this shape exactly.

The public app still loads `kgg-update/index.html`, but that file is generated output.
The GPT must patch the modular source through the gate; it must not request direct edits to `kgg-update/index.html`.

## Preview automation and release modes

- `submitKggPreviewAuto`: the only production GPT Preview write. One dispatch runs `validate_only` and, only after success, the identical payload as `publish_preview`. It also publishes status JSON and a final GitHub notification. It cannot create a PR or change `main`.
- `validate_only`: internal first stage of the automatic Preview workflow. It writes nothing.
- `publish_preview`: internal second stage. It creates a module under `kgg-update/src/patches/`, rebuilds generated HTML, runs tests, builds Preview APK and publishes HTML/meta to `gpt-preview`.
- `create_pr`: only after Max accepts the matching Test-App/Test-APK/Preview-APK. Creates a PR, never merges.
- `publish_admin_beta`: only after Max accepts the matching Test-App/Test-APK/Preview-APK and asks for Haupt-App/Admin-Beta. Creates an `[admin-beta]` PR, labels it `kgg-auto-merge`, waits for required checks and merges the Admin beta to `main`.
- Server preflight: every Preview or release write requires the Admin editor snapshot to pass `--require-live-synced`. Read operations and `validate_only` stay available for diagnosis and local payload validation.

## Valid modular payload

```json
{
  "request_id": "kgg-v061-tablet-split-scale",
  "title": "Tablet Splitter und Skalierung trennen",
  "summary": "Tablet Splitter liegt auf der Spaltengrenze; Plus/Minus bleibt reine Skalierung.",
  "version_slug": "tablet-split-scale",
  "protected_scope": "none",
  "touched_areas": ["Tablet-Layout"],
  "required_tests": [
    "cmd /c release-pipeline\\run-kgg-tests.cmd --level critical",
    "cmd /c release-pipeline\\run-kgg-tests.cmd --suite ui-stability --level regression"
  ],
  "regression_contract": [
    {"kind": "contains", "value": "tabletLayoutResizeHandle"},
    {"kind": "not_contains", "value": "unsafe-global-touch-rule"}
  ],
  "patch_content": "<style id=\"__KGG_PATCH_ID__-style\">...</style>\n<script id=\"__KGG_PATCH_ID__\">...</script>\n"
}
```

## Required payload fields

- `request_id`: stable lowercase id matching `[a-z0-9][a-z0-9-]{5,63}`.
- `title`, `summary`, `version_slug`: non-empty; `version_slug` uses lowercase words separated by single hyphens.
- `touched_areas`: non-empty list. Protected areas are rejected unless Max explicitly authorizes a separate guarded path.
- `required_tests`: non-empty list. UI-like payloads must include `critical` and `ui-stability regression`.
- `patch_content`: HTML fragment only. It must include `__KGG_PATCH_ID__`; the gate replaces it with the generated Patch-ID.
- `protected_scope`: optional, default `none`. Only `cross-app-qr-preview` is additionally allowed.
- `regression_contract`: optional list of 1-12 declarative `contains`/`not_contains` assertions against the generated Admin HTML. It can extend the battery without executing GPT-provided test code.

## Cross-App QR Preview scope

`cross-app-qr-preview` is Max' durable Preview-only authorization for Admin/Patient QR scanner coordination. It allows only `QR/Patienten-App` and `Scan/OCR`, never Android/APK, PDF, Parser, Plan-State, Medien, Secrets or Manifest. It requires all four exact commands: Critical, UI-Stability Regression, `camera-qr` Regression and `patient-scan` Regression.

## Forbidden payload fields

- Do not send `operations`, `replace_exact`, `old_text`, `new_text`, `path`, `file`, `filename` or `target`.
- Do not send `path: "kgg-update/index.html"`. That is generated output and is rejected.
- Do not patch `const VERSION`, `KGG_BUILD_INFO`, `kgg-source-truth`, `kgg-changelog`, `base-app.html`, `base-head.html` or existing modules.
- Do not include protected tokens such as `API-Key`, `KGGDataStore.currentPlan`, `finishWithPdf`, `finishWithPatientApp`, `scanQrFromImageFile`, `KGGAndroidPdf` or `android_update_manifest`.

## Gate-owned outputs

The gate creates all of these:

- next `versionCode` and `versionName`
- `patchId`
- `kgg-update/src/patches/vNNN-<slug>.html`
- `kgg-update/src/parts.json` entry before `footer.html`
- `requiredPatchIds`
- source-truth/changelog metadata
- generated `kgg-update/index.html`
- `kgg-update/version.json` hash
- optional gate-owned `release-pipeline/gpt-regressions/<request_id>.json`

## Preview artifact response checklist

The GPT may say a Preview is available only after it has verified:

- GitHub run conclusion is `success`.
- `critical` completed successfully.
- `ui-stability regression` completed successfully for UI/Layout changes.
- Artifact exists and is not expired.
- `meta.json` returns HTTP 200 and contains `patchFile`.
- Preview HTML returns HTTP 200.
- Test-App/Test-APK/Preview-APK channel is updated.
- Max accepts the Test-APK result before Admin-Beta/Main is allowed.
- Max accepts the Test-App result before `create_pr` or `publish_admin_beta` is used.
- A Haupt-App push counts positive only after `publish_admin_beta` is verified on `main`.

## Required GPT Action operations

- `submitKggPreviewAuto` exposes the single pre-authorized `.github/workflows/kgg-gpt-preview-auto.yml` dispatch. Its inputs do not contain `mode`.
- `submitKggMainGate` exposes only `create_pr` and `publish_admin_beta` and requires `approval_phrase: "Gut für Main"`.
- `listKggPreviewAutoRuns` must be available so the GPT can find the one orchestrator run for a `request_id`.
- `getKggPreviewGateRun` must be available so the GPT can verify `status` and `conclusion`.
- `getKggPreviewGateJobs` must be available so the GPT can report failed job/step names.
- `getKggPreviewGateArtifacts` must be available so the GPT can verify the Preview artifact exists and is not expired.
- `submitKggPatientPreviewFromAdmin` exposes only isolated Patient `validate_only` and `publish_preview`. Its server workflow requires both Admin and Patient snapshots to be `live-synced` before a cross-app Preview write; `validate_only` remains available. The legacy Patient Preview-only workflow enforces the same Admin preflight, so an older Admin Action schema cannot bypass it.
- Coordination uses `getKggAgentCoordinationIndex`, one selected thread and guarded append-only events.

## Brain-Relay-Worker Coordination-v2 Actions

Die vier bestehenden Coordination-Operationen bleiben unveraendert und
rueckwaertskompatibel: `getKggAgentCoordinationIndex`,
`getKggAgentCoordinationThread`, `submitKggAgentCoordinationEvent` und
`listKggAgentCoordinationRuns`. Fuer die neue Task Capsule gibt es nur drei
zusaetzliche read-only Wege im authentifizierten API-Schema:

- `getKggAgentCoordinationTask` liest genau eine Task Capsule;
- `getKggAgentCoordinationHandoff` liest genau einen Handoff;
- `getKggAgentCricketEvent` liest genau ein Cricket-Ereignis.

Alle drei Wege lesen `coordination-v2` unter `main`, sind nicht consequential
und veraendern weder App-Code noch Gates. Es gibt weiterhin genau einen
Schreibweg: `submitKggAgentCoordinationEvent` mit `validate_only` und danach
identischem `apply` fuer ein einzelnes nicht sensibles append-only Event.

Das Routing lautet fuer echte Aufgaben Manager -> genau ein Lead-GPT -> null
bis vier Unter-Chats -> derselbe Lead zur Synthese -> Relay -> Luna-Max-Worker
-> Relay -> derselbe Lead -> CI/Abnahme. Status-Reads duerfen GPT ueberspringen.
Requirements-Hash, Generation, Revision und Handoff-Hash muessen bei jedem
Relay gleich bleiben. Admin- und Patient-GPT nutzen getrennte Profiles,
Snapshots und Gates.

The public status channel is `gpt-preview/status/latest.json`, with per-request history under `gpt-preview/status/requests/<request_id>.json`. It contains only request/run state and no payload, patient data or secret. The Preview app polls it while open and through WorkManager in the background. This status channel is progress evidence, but final success still requires the run, tests, artifact, `meta.json`, HTML and Preview index.

## Custom GPT Editor Domains

- Use the API-only Action schema for `api.github.com`.
- Do not create duplicate action domains for `raw.githubusercontent.com`; raw URLs are verified through the GitHub run/artifact/meta checks.
- If the editor reports duplicate action domains, stop and fix the Action schema before dispatching.

## KGG Project Memory Gate

The private repository `Kayus24/kgg-project-memory` stores curated durable decisions. It does not store app code, patient data, secrets or full chat transcripts.

Read in this order:

1. `getKggMemoryIndex`.
2. Only the smallest matching file via `getKggMemoryPack` (normally one or two packs). Pass only the basename from the index, for example `workflow.md`; never pass `memory/packs/...` as `pack_name`.
3. `getKggMemoryRecord` or `getKggMemoryHistory` only for rationale, history or conflicts.

Valid memory payload:

```json
{
  "request_id": "memory-example-001",
  "record": {
    "kind": "decision",
    "key": "example.stable-key",
    "topic": "project",
    "title": "Short title",
    "summary": "Compact routing summary.",
    "value": "The durable instruction or fact.",
    "source_refs": ["user:2026-07-20"],
    "supersedes": []
  }
}
```

- Use `submitKggMemoryUpdate` with `mode=validate_only` first.
- Continue with `mode=apply` only for `would_apply`, using the identical `request_id` and payload.
- `no_change` is terminal and must not create another request.
- `needs_approval` means the active old value and candidate value must be shown to Max; write nothing until he explicitly approves.
- After approval, append a new record with `supersedes`, `approved_by: "Max"` and `approval_quote`. Never edit or delete the old record.
- `rejected` must be reported and never bypassed.
- The GPT must semantically compare the candidate with the matching active pack before dispatch. The workflow also blocks same-key value changes mechanically.

Required memory operations:

- `getKggMemoryIndex`
- `getKggMemoryPack`
- `getKggMemoryRecord`
- `getKggMemoryHistory`
- `submitKggMemoryUpdate`
- `listKggMemoryUpdateRuns`
- `getKggMemoryUpdateRun`
- `getKggMemoryUpdateStatus`
- `getKggMemoryUpdateArtifacts`

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
Erklaerung; die bestehende Coordination Action bleibt der einzige append-only
Schreibweg.

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

## 2. Verbindlicher Routinggraph

Jede echte Entwicklungsaufgabe laeuft in dieser Reihenfolge:

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

Nur eine reine Statusabfrage darf den GPT-Teil ueberspringen. Ein Status-Read
ist read-only und darf weder Task Capsule noch Scope, Ticket oder Ziel veraendern.

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
    "sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
  },
  "acceptance": [
    "Alle echten Aufgaben verwenden den vollstaendigen Routinggraphen.",
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

Coordination-v2 liest Task, Handoff und Cricket-Fakten ueber sichere GitHub-
Reads. Schreiben ist weiterhin auf eine bestehende append-only Coordination
Action beschraenkt. Es gibt keinen zweiten Schreibweg und keine Update-/Delete-
Operation fuer alte Ereignisse.

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
  "requirements_sha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "transport_only": true,
  "summary": "Der abgegrenzte Vertragsscope wurde umgesetzt.",
  "evidence": [{"kind": "test", "name": "brain-relay-selftest", "status": "PASS"}],
  "handoff_hash": "wird-vom-kanonischen-hasher-berechnet",
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

---

# Source: docs/kgg-custom-gpt-preview-runbook.md

# KGG Custom GPT Preview Runbook

Use this order for every Preview/Test-HTML/Test-APK request.

Canonical order: `single auto dispatch -> validating status -> publish status -> tests -> artifact -> meta -> html -> Test-APK notification -> Max acceptance -> Admin beta merge`.

## Run order

1. Load live context, bug lessons, action schema, negative examples and area routes.
2. Build the smallest modular v2 payload with `patch_content`; do not send `replace_exact`, `operations` or direct `kgg-update/index.html` paths.
3. Dispatch `submitKggPreviewAuto` exactly once. Do not provide a mode.
4. The orchestrator runs `validate_only` first and automatically blocks publish on failure.
5. After green validation, the orchestrator automatically runs the identical payload as `publish_preview`.
6. Use `listKggPreviewAutoRuns` and the workflow run name/request id to find the one GitHub run.
7. Use `getKggPreviewGateRun` until `status` is `completed`.
8. Verify that run `headSha` and Preview `baseSha` contain the expected Default-Branch fix. An open PR is not production evidence.
9. If the run fails, use `getKggPreviewGateJobs` and report the failed job/step and exact visible error context.
10. If the run succeeds, verify artifact, `meta.json` and HTML URL.
11. If the request targets the Test-APK, verify that the Preview/Test-APK channel is updated.
12. Tell Max that the Preview/Test-APK is ready for his review.
13. If Max rejects the Test-APK result, document `human_preview_fail`, add/update the regression fixture and start one new auto run.
14. Use `create_pr` only after Max explicitly accepts the same Preview and only a PR is requested.
15. Use `publish_admin_beta` only when Max explicitly wants a real Haupt-App/Admin-Beta push. Success requires a merged `[admin-beta]` PR, updated `android_update_manifest.json` on `main`, and HTTP 200 for the new Admin HTML.

## Required verified fields

Every successful Preview report must include:

- `run_id`
- `conclusion`
- `failed_step` or `none`
- `meta_url`
- `html_url`
- `artifact_name`
- Test-APK/channel status when APK preview is involved
- Max acceptance status before any PR
- Admin beta merge status when Haupt-App push is involved

## Failure wording

Use direct wording:

- `Keine Preview verfuegbar: Run rot.`
- `Failed step: <step name>.`
- `Fehler: <exact error>.`
- `CI-Tooling fehlt: <tool>.`

Do not use vague wording:

- `kommt gleich`
- `Manifest wartet noch`
- `wahrscheinlich noch nicht sichtbar`

These are allowed only when the run is still actually in progress.

If `critical` fails with `Missing tool pdftoppm`, `Missing tool pdfinfo`, `poppler-utils` or another runner dependency, classify it as `ci_tooling`. Do not blame the UI patch until the failed subtest log proves an app assertion failed.

## Automatic status channel

- `status/latest.json` and `status/requests/<request_id>.json` are updated to `validating`, `publishing`, then `success` or `failure`.
- The open Preview app checks about every 30 seconds. Android WorkManager checks in the background at the platform minimum interval of about 15 minutes.
- The final workflow state also comments on the persistent `KGG Preview Status` issue and mentions Max for GitHub Mobile push delivery.
- Status JSON never contains the patch payload, patient data or secrets.
- These notifications remove the need for an "Und?" message; they do not weaken final artifact verification or Max' Main gate.

---

# Source: docs/kgg-custom-gpt-preview-report-template.md

# KGG Custom GPT Preview Report Template

Use this exact report shape after Preview-Gate runs.

## Success

```text
base source used: main/kgg-update/src, version <version>
generated module: kgg-update/src/patches/vNNN-<slug>.html
generated output: kgg-update/index.html
request_id: <request_id>
run_id: <run_id>
conclusion: success
failed_step: none
artifact_name: <artifact_name>
meta_url: <meta_url>
html_url: <html_url>
patch_id: <kgg-vNNN-slug>
patch_file: <patches/vNNN-slug.html>
test_apk_channel: <updated|not involved>
max_acceptance: <accepted|pending>
admin_beta_pr: <url|not requested>
admin_beta_merge: <merged|not requested|pending>
admin_html_url: <url|not requested>
visible_scaler_canary: <verified|not involved|pending>

changes:
- <short behavior summary>

smoke test:
- critical: green
- ui-stability regression: green
- Preview APK build: green
- artifact/meta/html: verified
- Test-APK review: pending Max acceptance, unless Max already accepted
- Admin beta merge: verified when `publish_admin_beta` was requested
- Admin HTML: HTTP 200 when `publish_admin_beta` was requested

risks:
- <specific risk>
- not touched: <protected areas>
```

## Failure

```text
base source used: main/kgg-update/src, version <version>
generated module: none published
generated output: none published
request_id: <request_id>
run_id: <run_id>
conclusion: failure
failed_step: <failed step>
artifact_name: none
meta_url: not available
html_url: not available
patch_id: not available
patch_file: not available
test_apk_channel: not updated
max_acceptance: not requested
admin_beta_pr: not created
admin_beta_merge: not attempted
admin_html_url: not available
visible_scaler_canary: not verified

smoke test:
- not green; stopped at <failed step>

error:
- <exact error>

next step:
- <specific correction>
```
