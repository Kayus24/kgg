# Kgg Gpt Operations

Generated production knowledge for modular payloads, Actions, Preview/Test-App and Admin-Beta operations.

Source digest: `d4686961f56e87d5`

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

1. Lade `docs/kgg-gpt-context.md`.
2. Lade `docs/kgg-custom-gpt-action-schema.md`.
3. Lade bei Patchfragen `docs/kgg-gpt-area-routes.md` und die passenden Source-Chunks.
4. Lade `docs/kgg-gpt-bug-lessons.md` und `docs/kgg-gpt-patch-patterns.md`.
5. Wenn Kontext oder Schema nicht geladen werden kann: stoppen, keinen Payload raten.
6. Bei Analysefragen nur Diagnose/Handoff schreiben; kein `submitKggPreviewGate`.
7. Bei Preview/Test-App-Wunsch immer `validate_only -> publish_preview`.
8. Nach `publish_preview` wartet der Prozess auf Max' Test-App/Test-APK/Preview-APK-Freigabe.
9. Erst nach Max-Freigabe `create_pr` oder, wenn Max Haupt-App verlangt, `publish_admin_beta`.

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

This is the canonical payload shape for `KGG GPT Preview Gate`.
The Custom GPT must follow this shape exactly.

The public app still loads `kgg-update/index.html`, but that file is generated output.
The GPT must patch the modular source through the gate; it must not request direct edits to `kgg-update/index.html`.

## Modes

- `validate_only`: validate JSON, scaffold the modular patch in memory, verify build invariants. Writes nothing.
- `publish_preview`: validate, create a module under `kgg-update/src/patches/`, rebuild generated HTML, run tests, build Preview APK, publish HTML/meta to `gpt-preview`.
- `create_pr`: only after Max accepts the matching Test-App/Test-APK/Preview-APK. Creates a PR, never merges.
- `publish_admin_beta`: only after Max accepts the matching Test-App/Test-APK/Preview-APK and asks for Haupt-App/Admin-Beta. Creates an `[admin-beta]` PR, labels it `kgg-auto-merge`, waits for required checks and merges the Admin beta to `main`.

## Valid modular payload

```json
{
  "request_id": "kgg-v061-tablet-split-scale",
  "title": "Tablet Splitter und Skalierung trennen",
  "summary": "Tablet Splitter liegt auf der Spaltengrenze; Plus/Minus bleibt reine Skalierung.",
  "version_slug": "tablet-split-scale",
  "touched_areas": ["Tablet-Layout"],
  "required_tests": [
    "cmd /c release-pipeline\\run-kgg-tests.cmd --level critical",
    "cmd /c release-pipeline\\run-kgg-tests.cmd --suite ui-stability --level regression"
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

- `submitKggPreviewGate` must allow `mode` values `validate_only`, `publish_preview`, `create_pr` and `publish_admin_beta`.
- `listKggPreviewGateRuns` must be available so the GPT can find the run for a `request_id`.
- `getKggPreviewGateRun` must be available so the GPT can verify `status` and `conclusion`.
- `getKggPreviewGateJobs` must be available so the GPT can report failed job/step names.
- `getKggPreviewGateArtifacts` must be available so the GPT can verify the Preview artifact exists and is not expired.

## Custom GPT Editor Domains

- Use the API-only Action schema for `api.github.com`.
- Do not create duplicate action domains for `raw.githubusercontent.com`; raw URLs are verified through the GitHub run/artifact/meta checks.
- If the editor reports duplicate action domains, stop and fix the Action schema before dispatching.

---

# Source: docs/kgg-custom-gpt-preview-runbook.md

# KGG Custom GPT Preview Runbook

Use this order for every Preview/Test-HTML/Test-APK request.

Canonical order: `dispatch -> run status -> logs -> tests -> artifact -> meta -> html -> Test-APK -> Max acceptance -> Admin beta merge`.

## Run order

1. Load live context, bug lessons, action schema, negative examples and area routes.
2. Build the smallest modular v2 payload with `patch_content`; do not send `replace_exact`, `operations` or direct `kgg-update/index.html` paths.
3. Dispatch `validate_only` first.
4. If `validate_only` fails, report the failed step and exact error. Do not publish.
5. If validation succeeds, dispatch `publish_preview`.
6. Use `listKggPreviewGateRuns` and the workflow run name/request id to find the GitHub run.
7. Use `getKggPreviewGateRun` until `status` is `completed`.
8. If the run fails, use `getKggPreviewGateJobs` and report the failed job/step and exact visible error context.
9. If the run succeeds, verify artifact, `meta.json` and HTML URL.
10. If the request targets the Test-APK, verify that the Preview/Test-APK channel is updated.
11. Tell Max that the Preview/Test-APK is ready for his review.
12. If Max rejects the Test-APK result, document `human_preview_fail`, add/update the regression fixture and restart at `validate_only`.
13. Use `create_pr` only after Max explicitly accepts the same Preview and only a PR is requested.
14. Use `publish_admin_beta` only when Max explicitly wants a real Haupt-App/Admin-Beta push. Success requires a merged `[admin-beta]` PR, updated `android_update_manifest.json` on `main`, and HTTP 200 for the new Admin HTML.

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
