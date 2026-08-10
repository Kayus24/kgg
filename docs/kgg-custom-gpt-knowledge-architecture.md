# Kgg Gpt Architecture

Generated production knowledge for live app structure, source routing and current release context.

Source digest: `d6f052ac5e6c9424`

## Usage Rules

- Reload this pack before KGG patch, Preview/Test-APK, Admin-Beta or run-diagnosis work.
- If this pack conflicts with live GitHub files, trust the live source files and report stale knowledge.
- Read current cycle and run status from GitHub Actions, not from this static pack.
- Do not claim Preview, Test-APK or Admin-Beta success without run/artifact/HTTP evidence.
- Treat `ci_tooling` separately from app patch failures.
- Positive E2E push-test means both `publish_preview` and `publish_admin_beta` succeeded.

## Source Files

- `docs/kgg-gpt-context.md`
- `docs/kgg-gpt-area-routes.md`

---

# Source: docs/kgg-gpt-context.md

# KGG GPT Live Context

This file is the live repo context for the private KGG Update-Agent Custom GPT.
Reload it before answering repo-, version-, patch-, beta-HTML- or test-related questions.
If this file conflicts with `kgg-update/version.json` or `therapist-app/android_update_manifest.json`, trust the JSON source files and tell Max.

## Repository

- GitHub repo: `https://github.com/Kayus24/kgg`.
- Source branch: `main`.
- Modular Admin source: `kgg-update/src`.
- Generated public Admin HTML: `kgg-update/index.html`.
- Web update metadata: `kgg-update/version.json`.
- Android/Web release manifest: `therapist-app/android_update_manifest.json`.
- Release pipeline docs: `release-pipeline/README.md`.
- Custom GPT playbook: `docs/kgg-custom-gpt-playbook.md`.
- Custom GPT editor bootstrap: `docs/kgg-custom-gpt-editor-bootstrap.md`.
- Custom GPT action schema: `docs/kgg-custom-gpt-action-schema.md`.
- Custom GPT combined Action OpenAPI: `docs/kgg-custom-gpt-action-openapi.yaml`.
- Custom GPT API-only Action OpenAPI for the current split editor setup: `docs/kgg-custom-gpt-action-api-openapi.yaml`.
- Custom GPT negative examples: `docs/kgg-custom-gpt-negative-examples.md`.
- Custom GPT preview runbook: `docs/kgg-custom-gpt-preview-runbook.md`.
- Custom GPT preview report template: `docs/kgg-custom-gpt-preview-report-template.md`.
- Custom GPT Wissen/Knowledge pack: `docs/kgg-custom-gpt-knowledge-pack.md`.
- Curated production Knowledge: `docs/kgg-custom-gpt-knowledge-{architecture,operations,safety,testing}.md`.
- Custom GPT model/capability/resource contract: `docs/kgg-custom-gpt-resource-manifest.json`.
- Blind full-app Repair-Lab: `docs/kgg-custom-gpt-repair-lab.md`, workflow `.github/workflows/kgg-gpt-repair-lab.yml`.
- Isolated Eval-GPT Knowledge: `docs/kgg-custom-gpt-eval-knowledge.md`; never upload production fixtures to this GPT.
- Custom GPT stabilization cycle report: `docs/kgg-custom-gpt-cycle-report.md`.
- Bug-history lessons: `docs/kgg-gpt-bug-lessons.md`, `docs/kgg-gpt-bug-index.json`, `docs/kgg-gpt-patch-patterns.md`.
- Source routing: `docs/kgg-gpt-area-routes.md`, `docs/kgg-gpt-area-routes.json`.
- Source chunks for GPT patch planning: `docs/kgg-gpt-source-index.json` and `docs/kgg-gpt-source/chunk-*.md`.
- GPT eval fixtures: `docs/kgg-custom-gpt-test-prompts.md`, `docs/kgg-custom-gpt-expected-results.md`, `docs/kgg-custom-gpt-test-report.md`.
- GPT stabilization runner: `release-pipeline/kgg_gpt_stabilize.py`.
- Blind Repair-Lab runner: `release-pipeline/kgg_gpt_repair_lab.py`; acceptance tracker: `release-pipeline/kgg_gpt_repair_stabilize.py`.
- GPT preview channel branch: `gpt-preview`, files below `previews/`.
- Private project memory: `Kayus24/kgg-project-memory`; load `memory/index.json` first and then only the smallest matching pack.
- Private agent coordination: load `coordination/index.json` first and only relevant open threads; the queue never stores patient data or raw QR payloads.
- Limited Patient-App context/actions: `docs/kgg-patient-gpt-context.md`, Patient source chunks and isolated Patient Preview-only gate.
- The Custom GPT may write app changes only through `KGG GPT Preview Gate` and durable knowledge only through `KGG Project Memory Gate`; other direct writes and direct merges stay forbidden.

## Current Versions

- Source web version: v65 / `1.0.65-source-control-char-guard`.
- Source index URL: `index.html?v=65`.
- Source notes: v065: Ersetzt vier versehentliche U+0008-Zeichen durch Regex-Wortgrenzen, repariert den fehlkodierten SJIS-Prüfwert und blockiert C0-, C1- sowie DEL-Steuerzeichen in editierbaren Source-Teilen.
- Live Admin release: `r0425` / `1.0.62-tablet-recent-package-shell-geometry`.
- Live Admin URL: `https://kayus24.github.io/kgg/therapist-app/releases/web/r0425/admin.html`.
- Live colleague release: `r0397` / `1.0.29-camera-touch-parser-fix`.
- Live colleague URL: `https://kayus24.github.io/kgg/therapist-app/releases/web/r0397/colleague.html`.
- Latest Android shell: `v401`.
- Latest colleague APK: `https://kayus24.github.io/kgg/therapist-app/releases/v401/android/KGG_ANDROID_KOLLEGEN_v401_share_apk_provider_debug.apk`.
- Latest Admin APK: `https://kayus24.github.io/kgg/therapist-app/releases/v401/android/KGG_ANDROID_ADMIN_v401_share_apk_provider_debug.apk`.

## Hard Rules For The GPT

- Work with Max in German: pragmatic, direct, few questions.
- Do not rebuild the app and do not refactor unless Max explicitly asks.
- Make the smallest safe patch and only one logical change per patch.
- Never hardcode API keys or place secrets in GitHub, HTML, JS, JSON, tests or handoff files.
- Never expose patient JSON, raw Base64 or debug payloads as normal patient output.
- Treat `KGGDataStore.currentPlan` as the central plan-state source.
- Do not touch PDF, QR/patient app, scan/OCR, parser, plan-state, media/upload, API-key logic, Android/APK, GitHub manifest or phone layout unless Max explicitly asks.
- Existing uncommitted local changes belong to Max or another run. Do not reset them.
- Automatically add confirmed durable decisions and lessons to the private project memory, but never overwrite an active instruction without Max' explicit approval.
- Do not store chats, patient data, secrets or transient debug output in the project memory.
- Reads, one submitKggPreviewAuto dispatch, evidence checks, safe new memory records and coordination events are pre-authorized; do not ask after every step.
- Admin PR/Main requires Max' exact phrase `Gut für Main`; Patient PR/Live requires `Gut für PAT live`.

## Patch Routing

- Before planning a patch, load `docs/kgg-custom-gpt-playbook.md` and determine the real basis from `main`, the manifest and the target profile.
- Before proposing or dispatching a patch, load the bug-history lessons and look for similar symptoms.
- Before producing a patch payload, load `docs/kgg-gpt-area-routes.md` and then only the source chunks needed for the requested area.
- If a known bug-history lesson matches, reuse its caution, do-not-touch rules and tests.
- Run payload JSON through `python release-pipeline/kgg_gpt_payload_preflight.py --payload-file <file>` before dispatching.
- New GPT patches use payload v2 with `patch_content`; direct operations against `kgg-update/index.html` are forbidden because `index.html` is generated output.
- Explicit QR/Scanner coordination uses only `protected_scope: cross-app-qr-preview`; it cannot authorize Android/APK, PDF, Parser, Plan-State, Medien, Secrets or Manifest.
- Do not assume the newest local HTML is live.
- If Max asks for a beta, dispatch `submitKggPreviewAuto` exactly once. The workflow enforces `validate_only -> publish_preview`; do not create a PR until Max explicitly accepts the Test-App/Preview-APK result.
- If Max asks for Test-APK review, publish only through the Preview/Test-APK channel and wait for Max' Test-APK acceptance before PR/main steps.
- If Max says the preview is good, use `create_pr` only with the same `request_id` and patch hash unless Max explicitly requests the real Admin-Beta/Haupt-App push.
- A positive end-to-end push test requires both `publish_preview` for Test-App/Preview-App and `publish_admin_beta` for Admin-Beta merge to `main`.
- If critical fails with `Missing tool pdftoppm`, `Missing tool pdfinfo`, `poppler-utils`, `adb` or emulator tooling, classify it as `ci_tooling`, not as an app/UI patch failure.
- If a Preview run fails, report the failed step and the actual error before checking `meta.json` or manifest URLs.
- If the Custom GPT cannot load this context, it must say that repo context is unavailable instead of guessing or asking Max for old basis filenames.
- Before each real GPT test cycle verify the highest Actions-compatible model and capability/Knowledge hashes against `docs/kgg-custom-gpt-resource-manifest.json`.
- The isolated Eval GPT must not receive Web Search, production Actions, production Knowledge, intact main HTML, golden source, sample repairs or hidden assertions.
- A Repair-Lab PASS is evaluation evidence only and never authorizes Preview/Test-App, PR, Admin-Beta or main.

## Required Tests

- Every code change: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`.
- UI, HTML, flicker, phone, tablet, card drag or layout changes: also `cmd /c release-pipeline\run-kgg-tests.cmd --suite ui-stability --level regression`.
- GPT playbook, routing, payload or bug-knowledge changes: also `python release-pipeline\kgg_gpt_payload_preflight.py --self-test` and `python release-pipeline\kgg_gpt_eval.py`.
- Custom GPT stabilization changes: also `python release-pipeline\kgg_gpt_stabilize.py --self-test`, `python release-pipeline\kgg_custom_gpt_knowledge_pack.py --check` and update `docs/kgg-custom-gpt-cycle-report.md`.
- Repair-Lab changes: also `python release-pipeline\kgg_gpt_repair_lab.py --self-test`, `python release-pipeline\kgg_gpt_repair_stabilize.py --self-test` and `python release-pipeline\kgg_custom_gpt_resource_audit.py --check`.
- Parser or text-block changes: also `cmd /c release-pipeline\run-kgg-tests.cmd --suite textblocks --level regression`.
- Sync, bank, package or peer changes: also `cmd /c release-pipeline\run-kgg-tests.cmd --suite sync --level regression`.
- Android sync bridge changes: also `cmd /c release-pipeline\run-kgg-tests.cmd --suite native-sync --level regression`.
- Cross-App Kamera/QR changes: also `cmd /c release-pipeline\run-kgg-tests.cmd --suite camera-qr --level regression` and `cmd /c release-pipeline\run-kgg-tests.cmd --suite patient-scan --level regression`.
- `mobile-inbox-live` is never automatic because it intentionally creates a new Admin beta.

## GitHub Guardrails

- `main` is protected and must not be written directly.
- Required status check: `KGG Required Gate / required-gate`.
- Admin beta auto-merge requires green checks plus the explicit `kgg-auto-merge` label.
- Pre-authorized Admin Preview access uses `.github/workflows/kgg-gpt-preview-only.yml`; PR/Main stays on the separate consequential gate.
- Pre-authorized Patient Preview access uses `.github/workflows/kgg-patient-gpt-preview-only.yml`; Patient PR/Live stays separate.
- The isolated Eval GPT may dispatch only `.github/workflows/kgg-gpt-repair-lab.yml`; that workflow cannot create Preview, PR, Admin-Beta or main changes.
- Project-memory write access is limited to workflow dispatch for `Kayus24/kgg-project-memory/.github/workflows/kgg-memory-gate.yml`.
- Cross-agent coordination write access is limited to `kgg-agent-coordination-gate.yml`; it cannot modify either app.
- Memory reads must start with `getKggMemoryIndex`, then use only matching packs; history and records are on-demand only.
- A memory update uses `validate_only` before `apply`; `needs_approval` must stop until Max explicitly approves the superseding record.
- GPT Actions split pre-authorized Preview-only operations from consequential PR/Main operations and expose run/job/artifact status reads.
- Current GPT editor setup uses split Actions; paste the API-only schema into `api.github.com` to avoid duplicate `raw.githubusercontent.com` domains.
- Preview writes go only to branch `gpt-preview`; production writes are PR-only and never auto-merge.

## Update Mechanism

- This file is generated by `release-pipeline/kgg_gpt_context.py`.
- Bug-history knowledge is generated by `release-pipeline/kgg_bug_knowledge.py`.
- Source chunk and area-route context is generated by `release-pipeline/kgg_gpt_source_context.py`.
- Custom GPT knowledge pack is generated by `release-pipeline/kgg_custom_gpt_knowledge_pack.py`.
- Custom GPT resource hashes are generated by `release-pipeline/kgg_custom_gpt_resource_audit.py`.
- Run `python release-pipeline/kgg_gpt_context.py --write` after changing version, release, workflow, test or durable project-rule context.
- Run `python release-pipeline/kgg_bug_knowledge.py --write` after changing bug/debug docs, patch lessons or known failure rules.
- Run `python release-pipeline/kgg_gpt_source_context.py --write` after changing `kgg-update/src`, generated source routing rules or modular patch behavior.
- Run `python release-pipeline/kgg_gpt_eval.py` after changing Custom GPT playbook, prompts, expected results, routing or preflight behavior.
- Run `python release-pipeline/kgg_custom_gpt_knowledge_pack.py --write` after changing Custom GPT docs that should be uploaded to GPT Wissen.
- Run `python release-pipeline/kgg_gpt_stabilize.py --write-report` after running a GPT stabilization cycle.
- CI runs GPT context, bug knowledge and source context freshness checks in the required gate so stale GPT context cannot silently merge.

---

# Source: docs/kgg-gpt-area-routes.md

# KGG GPT Area Routes

Generated from `kgg-update/src` modular source. Use this before loading source chunks.

## tablet-layout

- Triggers: `tablet`, `layout`, `splitter`, `spaltenbreite`, `uebungsdatenbank`, `planbereich`
- Source chunks: `docs/kgg-gpt-source/chunk-004.md`, `docs/kgg-gpt-source/chunk-006.md`, `docs/kgg-gpt-source/chunk-007.md`, `docs/kgg-gpt-source/chunk-008.md`, `docs/kgg-gpt-source/chunk-013.md`, `docs/kgg-gpt-source/chunk-055.md`, `docs/kgg-gpt-source/chunk-056.md`, `docs/kgg-gpt-source/chunk-057.md`
- Tests: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`; `cmd /c release-pipeline\run-kgg-tests.cmd --suite ui-stability --level regression`
- Notes: Plus/Minus controls scale; horizontal drag controls the left column width.
- Markers:
  - `tabletLayoutFreeTools`: `docs/kgg-gpt-source/chunk-006.md` line 2790
  - `tabletLayoutResizeHandle`: `docs/kgg-gpt-source/chunk-006.md` line 2729
  - `--kgg-tablet-left-col`: `docs/kgg-gpt-source/chunk-006.md` line 2828
  - `--kgg-tablet-ui-scale`: `docs/kgg-gpt-source/chunk-004.md` line 1759
  - `updateTabletLayoutHandle`: `docs/kgg-gpt-source/chunk-055.md` line 23221
  - `initTabletLayoutControls`: `docs/kgg-gpt-source/chunk-055.md` line 23357

## phone-layout

- Triggers: `phone`, `handy`, `dock`, `drawer`, `scan button`, `759`
- Source chunks: `docs/kgg-gpt-source/chunk-002.md`, `docs/kgg-gpt-source/chunk-004.md`, `docs/kgg-gpt-source/chunk-008.md`, `docs/kgg-gpt-source/chunk-009.md`, `docs/kgg-gpt-source/chunk-010.md`, `docs/kgg-gpt-source/chunk-012.md`, `docs/kgg-gpt-source/chunk-060.md`, `docs/kgg-gpt-source/chunk-061.md`
- Tests: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`; `cmd /c release-pipeline\run-kgg-tests.cmd --suite ui-stability --level regression`
- Notes: Do not change the 759/760 px breakpoint incidentally.
- Markers:
  - `kggPhoneAdminMenu`: `docs/kgg-gpt-source/chunk-060.md` line 25337
  - `phonePhotoMenuToggle`: `docs/kgg-gpt-source/chunk-060.md` line 25337
  - `kggPhoneHasPlan`: `docs/kgg-gpt-source/chunk-060.md` line 25371
  - `phoneTextFocus`: `docs/kgg-gpt-source/chunk-008.md` line 3685
  - `max-width:759px`: `docs/kgg-gpt-source/chunk-002.md` line 939

## qr-patient

- Triggers: `qr`, `patient`, `patienten-app`, `plan qr`
- Source chunks: `docs/kgg-gpt-source/chunk-001.md`, `docs/kgg-gpt-source/chunk-047.md`, `docs/kgg-gpt-source/chunk-050.md`, `docs/kgg-gpt-source/chunk-051.md`, `docs/kgg-gpt-source/chunk-054.md`, `docs/kgg-gpt-source/chunk-056.md`, `docs/kgg-gpt-source/chunk-057.md`, `docs/kgg-gpt-source/chunk-061.md`, `docs/kgg-gpt-source/chunk-064.md`
- Tests: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`; `cmd /c release-pipeline\run-kgg-tests.cmd --suite patient-scan --level regression`
- Notes: Patient output must not expose raw JSON, Base64 or debug payloads.
- Markers:
  - `finishWithPatientApp`: `docs/kgg-gpt-source/chunk-051.md` line 21444
  - `KGGH2`: `docs/kgg-gpt-source/chunk-001.md` line 514
  - `tryApplyKggSetupFromHash`: `docs/kgg-gpt-source/chunk-047.md` line 19751
  - `openKggTherapistAppOnlyQr`: `docs/kgg-gpt-source/chunk-056.md` line 23763
  - `handleQrRaw`: `docs/kgg-gpt-source/chunk-054.md` line 23084

## camera-qr

- Triggers: `kamera`, `camera`, `automatischer qr`, `zoom`, `webview`, `barcode detector`
- Source chunks: `docs/kgg-gpt-source/chunk-054.md`, `docs/kgg-gpt-source/chunk-055.md`, `docs/kgg-gpt-source/chunk-063.md`, `docs/kgg-gpt-source/chunk-064.md`
- Tests: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`; `cmd /c release-pipeline\run-kgg-tests.cmd --suite ui-stability --level regression`; `cmd /c release-pipeline\run-kgg-tests.cmd --suite camera-qr --level regression`; `cmd /c release-pipeline\run-kgg-tests.cmd --suite patient-scan --level regression`
- Notes: Browser QR logic and Android WebView video permission are separate contracts. Never force zoom or audio.
- Markers:
  - `KGGNativeCamera`: `docs/kgg-gpt-source/chunk-054.md` line 23015
  - `getCameraCapabilities`: `docs/kgg-gpt-source/chunk-055.md` line 23114
  - `handleQrRaw`: `docs/kgg-gpt-source/chunk-054.md` line 23084
  - `LIVE_VARIANTS`: `docs/kgg-gpt-source/chunk-063.md` line 26868
  - `getUserMedia`: `docs/kgg-gpt-source/chunk-055.md` line 23115

## pdf

- Triggers: `pdf`, `druck`, `trainingsplan`
- Source chunks: `docs/kgg-gpt-source/chunk-013.md`, `docs/kgg-gpt-source/chunk-048.md`, `docs/kgg-gpt-source/chunk-050.md`, `docs/kgg-gpt-source/chunk-051.md`, `docs/kgg-gpt-source/chunk-056.md`, `docs/kgg-gpt-source/chunk-062.md`
- Tests: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`
- Notes: PDF changes need bounded thumbnail/card behavior.
- Markers:
  - `finishWithPdf`: `docs/kgg-gpt-source/chunk-051.md` line 21426
  - `KGGOfflineJsPDF`: `docs/kgg-gpt-source/chunk-013.md` line 5648
  - `attachKggPdfExerciseThumbnails`: `docs/kgg-gpt-source/chunk-048.md` line 20559

## android-apk

- Triggers: `apk`, `android`, `preview app`, `icon`
- Source chunks: `docs/kgg-gpt-source/chunk-041.md`, `docs/kgg-gpt-source/chunk-046.md`, `docs/kgg-gpt-source/chunk-047.md`
- Tests: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`; `GitHub android-wrapper-check must build assemblePreviewDebug when APK output matters.`
- Notes: Android/APK is protected unless Max explicitly asks for it.
- Markers:
  - `KGGAndroidPdf`: not found
  - `KGGNativeSync`: `docs/kgg-gpt-source/chunk-041.md` line 17558
  - `PREVIEW_MANIFEST_URL`: not found

## sync

- Triggers: `sync`, `paket`, `uebungsbank`, `peer`, `kollegen`
- Source chunks: `docs/kgg-gpt-source/chunk-040.md`, `docs/kgg-gpt-source/chunk-041.md`, `docs/kgg-gpt-source/chunk-046.md`, `docs/kgg-gpt-source/chunk-047.md`
- Tests: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`; `cmd /c release-pipeline\run-kgg-tests.cmd --suite sync --level regression`
- Notes: Sync export must exclude patients and secrets.
- Markers:
  - `KGGDataStore`: `docs/kgg-gpt-source/chunk-040.md` line 16837
  - `kgg_sync_bundle`: `docs/kgg-gpt-source/chunk-047.md` line 19853
  - `nativeExerciseBankSync`: not found
  - `KGGNativeSync`: `docs/kgg-gpt-source/chunk-041.md` line 17558

## parser-textblocks

- Triggers: `parser`, `textblock`, `satz`, `ocr`
- Source chunks: `docs/kgg-gpt-source/chunk-044.md`, `docs/kgg-gpt-source/chunk-053.md`
- Tests: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`; `cmd /c release-pipeline\run-kgg-tests.cmd --suite textblocks --level regression`
- Notes: Parser and text-block behavior must not create bogus Satz cards.
- Markers:
  - `parseExerciseText`: not found
  - `textBlocks`: not found
  - `scanState`: `docs/kgg-gpt-source/chunk-044.md` line 18641

## preview-gate

- Triggers: `preview`, `beta`, `test-html`, `custom gpt`, `write gate`
- Source chunks: `docs/kgg-gpt-source/chunk-000.md`, `docs/kgg-gpt-source/chunk-001.md`, `docs/kgg-gpt-source/chunk-002.md`
- Tests: `python release-pipeline\kgg_gpt_payload_preflight.py --self-test`; `python release-pipeline\kgg_gpt_eval.py`
- Notes: A missing preview URL is not success; inspect the GitHub run first.
- Markers:
  - `kgg-gpt-preview-banner`: not found
  - `kgg-source-truth`: `docs/kgg-gpt-source/chunk-000.md` line 59
  - `kgg-changelog`: `docs/kgg-gpt-source/chunk-000.md` line 207
