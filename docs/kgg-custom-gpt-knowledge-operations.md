# Kgg Gpt Operations

Generated production knowledge for modular payloads, Actions, Preview/Test-App and Admin-Beta operations.

Source digest: `3b99bd9cc717776d`

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
- `docs/kgg-custom-gpt-preview-runbook.md`
- `docs/kgg-custom-gpt-preview-report-template.md`

---

# Source: docs/kgg-custom-gpt-playbook.md

# KGG Custom GPT Playbook

## Arbeitsreihenfolge

1. Lade Ressourcenmanifest, `docs/kgg-gpt-context.md`, dieses Playbook und die exakte Main-SHA.
2. Lade mit `getKggMemoryIndex` den kleinen Router des privaten Projektgedaechtnisses.
3. Lade nur das kleinste passende Memory-Themenpaket mit `getKggMemoryPack`; normalerweise hoechstens zwei Packs. Einzelne Records nur fuer Begruendung, Historie oder Konflikte laden.
4. Lade `docs/kgg-custom-gpt-action-schema.md`.
5. Lade bei Patchfragen `docs/kgg-gpt-area-routes.md` und die passenden Source-Chunks.
6. Lade `docs/kgg-gpt-bug-lessons.md` und `docs/kgg-gpt-patch-patterns.md`.
7. Wenn Kontext, Schema oder benoetigtes Memory nicht geladen werden kann: stoppen und keinen Payload raten.
8. Bei Analysefragen nur Diagnose/Handoff schreiben; kein `submitKggPreviewAuto`.
9. Bei Preview/Test-App-Wunsch genau einmal `submitKggPreviewAuto` aufrufen. Der Workflow erzwingt intern `validate_only -> publish_preview` mit identischem Payload.
10. Nach `publish_preview` wartet der Prozess auf Max' Test-App/Test-APK/Preview-APK-Freigabe.
11. Keinen zweiten Preview-Dispatch und keine Zwischenfrage senden. Der Auto-Workflow setzt die Kette selbst fort; Run und Belege pruefen.
12. `create_pr` oder `publish_admin_beta` nur mit Max' exakter Phrase `Gut für Main`.

## Autonomie ohne Bestaetigungsschleife

- Vorab freigegeben: Reads, Diagnose, Tests, ein `submitKggPreviewAuto`-Dispatch, Run-/Artifact-Pruefung, konfliktfreie neue Memory-Eintraege und private Koordinations-Events.
- Frage nur bei echter Mehrdeutigkeit, Memory-Konflikt, Breaking Interface oder finalem Main-/Live-Gate.
- Ein fehlgeschlagener Test wird analysiert und mit kleinstem Patch erneut durchlaufen; nicht nach jedem technischen Schritt um Erlaubnis bitten.
- Nach einem Dispatch bei `queued` oder `in_progress` nicht auf Max' "Und?" warten. Der GitHub-Workflow laeuft ohne weiteren GPT-Aufruf automatisch durch Validierung und Publish. Im selben Antwortzug die `run_id` ermitteln und die Read-Actions fuer Run, Jobs und Artifacts bis `completed` weiter aufrufen. Endet das technische Action-Zeitfenster vorher, den belegten Zwischenstand nennen und auf die automatische Test-App-/GitHub-Benachrichtigung verweisen; niemals Fertigstellung behaupten.
- ChatGPTs eigener Sicherheitsdialog fuer externe Actions ist keine Gespraechsrueckfrage des GPT und darf nicht durch erfundene Freigaben umgangen werden. Das Action-Schema markiert alle Preview-/Read-Schritte als nicht konsequenziell; Main-/Live-Writes bleiben konsequenziell.
- Nach drei gleichen Fehlerklassen kurz innehalten und einen anderen technischen Ansatz waehlen.

## Begrenzte Patient-App-Koordination

- Bei QR, Scanner, Storage oder Patient/Admin-Schnittstellen Patient-Kontext, Patient-Playbook und gezielte Patient-Source-Chunks live laden.
- Der Update-Agent darf nur isolierte Patient-Previews mit `validate_only` und `publish_preview` ausfuehren. Kein Patient-PR und kein Patient-Live.
- `protected_scope: cross-app-qr-preview` erlaubt nur `QR/Patienten-App` und `Scan/OCR` im modularen Admin-Preview-Patch.
- Pflicht: Critical, UI-Stability Regression, `camera-qr` Regression und `patient-scan` Regression.
- Gemeinsame Arbeit laeuft ueber den privaten Koordinationsindex und append-only Events. Die Queue startet keinen GPT automatisch.
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
- `submitKggPatientPreviewFromAdmin` exposes only isolated Patient `validate_only` and `publish_preview`.
- Coordination uses `getKggAgentCoordinationIndex`, one selected thread and guarded append-only events.

The public status channel is `gpt-preview/status/latest.json`, with per-request history under `gpt-preview/status/requests/<request_id>.json`. It contains only request/run state and no payload, patient data or secret. The Preview app polls it while open and through WorkManager in the background. This status channel is progress evidence, but final success still requires the run, tests, artifact, `meta.json`, HTML and Preview index.

## Custom GPT Editor Domains

- Use the API-only Action schema for `api.github.com`.
- Do not create duplicate action domains for `raw.githubusercontent.com`; raw URLs are verified through the GitHub run/artifact/meta checks.
- If the editor reports duplicate action domains, stop and fix the Action schema before dispatching.

## KGG Project Memory Gate

The private repository `Kayus24/kgg-project-memory` stores curated durable decisions. It does not store app code, patient data, secrets or full chat transcripts.

Read in this order:

1. `getKggMemoryIndex`.
2. Only the smallest matching file via `getKggMemoryPack` (normally one or two packs).
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
