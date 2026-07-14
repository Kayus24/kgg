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
- Custom GPT action schema: `docs/kgg-custom-gpt-action-schema.md`.
- Custom GPT combined Action OpenAPI: `docs/kgg-custom-gpt-action-openapi.yaml`.
- Custom GPT API-only Action OpenAPI for the current split editor setup: `docs/kgg-custom-gpt-action-api-openapi.yaml`.
- Custom GPT negative examples: `docs/kgg-custom-gpt-negative-examples.md`.
- Custom GPT preview runbook: `docs/kgg-custom-gpt-preview-runbook.md`.
- Custom GPT preview report template: `docs/kgg-custom-gpt-preview-report-template.md`.
- Custom GPT Wissen/Knowledge pack: `docs/kgg-custom-gpt-knowledge-pack.md`.
- Custom GPT stabilization cycle report: `docs/kgg-custom-gpt-cycle-report.md`.
- Bug-history lessons: `docs/kgg-gpt-bug-lessons.md`, `docs/kgg-gpt-bug-index.json`, `docs/kgg-gpt-patch-patterns.md`.
- Source routing: `docs/kgg-gpt-area-routes.md`, `docs/kgg-gpt-area-routes.json`.
- Source chunks for GPT patch planning: `docs/kgg-gpt-source-index.json` and `docs/kgg-gpt-source/chunk-*.md`.
- GPT eval fixtures: `docs/kgg-custom-gpt-test-prompts.md`, `docs/kgg-custom-gpt-expected-results.md`, `docs/kgg-custom-gpt-test-report.md`.
- GPT stabilization runner: `release-pipeline/kgg_gpt_stabilize.py`.
- GPT preview channel branch: `gpt-preview`, files below `previews/`.
- The Custom GPT may only write through `KGG GPT Preview Gate`; direct repo writes, direct main writes and direct merges stay forbidden.

## Current Versions

- Source web version: v60 / `1.0.60-tablet-html-release-label`.
- Source index URL: `index.html?v=60`.
- Source notes: v060: Zeigt Release, HTML-Build und geladenen Dateinamen unten rechts im ausgefahrenen Tablet-Menue.
- Live Admin release: `r0424` / `1.0.60-tablet-html-release-label`.
- Live Admin URL: `https://kayus24.github.io/kgg/therapist-app/releases/web/r0424/admin.html`.
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

## Patch Routing

- Before planning a patch, load `docs/kgg-custom-gpt-playbook.md` and determine the real basis from `main`, the manifest and the target profile.
- Before proposing or dispatching a patch, load the bug-history lessons and look for similar symptoms.
- Before producing a patch payload, load `docs/kgg-gpt-area-routes.md` and then only the source chunks needed for the requested area.
- If a known bug-history lesson matches, reuse its caution, do-not-touch rules and tests.
- Run payload JSON through `python release-pipeline/kgg_gpt_payload_preflight.py --payload-file <file>` before dispatching.
- New GPT patches use payload v2 with `patch_content`; direct operations against `kgg-update/index.html` are forbidden because `index.html` is generated output.
- Do not assume the newest local HTML is live.
- If Max asks for a beta, use `KGG GPT Preview Gate` in `validate_only` mode first, then `publish_preview` after green validation; do not create a PR until Max explicitly accepts the Test-App/Preview-APK result.
- If Max asks for Test-APK review, publish only through the Preview/Test-APK channel and wait for Max' Test-APK acceptance before PR/main steps.
- If Max says the preview is good, use `create_pr` only with the same `request_id` and patch hash unless Max explicitly requests the real Admin-Beta/Haupt-App push.
- A positive end-to-end push test requires both `publish_preview` for Test-App/Preview-App and `publish_admin_beta` for Admin-Beta merge to `main`.
- If critical fails with `Missing tool pdftoppm`, `Missing tool pdfinfo`, `poppler-utils`, `adb` or emulator tooling, classify it as `ci_tooling`, not as an app/UI patch failure.
- If a Preview run fails, report the failed step and the actual error before checking `meta.json` or manifest URLs.
- If the Custom GPT cannot load this context, it must say that repo context is unavailable instead of guessing or asking Max for old basis filenames.

## Required Tests

- Every code change: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`.
- UI, HTML, flicker, phone, tablet, card drag or layout changes: also `cmd /c release-pipeline\run-kgg-tests.cmd --suite ui-stability --level regression`.
- GPT playbook, routing, payload or bug-knowledge changes: also `python release-pipeline\kgg_gpt_payload_preflight.py --self-test` and `python release-pipeline\kgg_gpt_eval.py`.
- Custom GPT stabilization changes: also `python release-pipeline\kgg_gpt_stabilize.py --self-test`, `python release-pipeline\kgg_custom_gpt_knowledge_pack.py --check` and update `docs/kgg-custom-gpt-cycle-report.md`.
- Parser or text-block changes: also `cmd /c release-pipeline\run-kgg-tests.cmd --suite textblocks --level regression`.
- Sync, bank, package or peer changes: also `cmd /c release-pipeline\run-kgg-tests.cmd --suite sync --level regression`.
- Android sync bridge changes: also `cmd /c release-pipeline\run-kgg-tests.cmd --suite native-sync --level regression`.
- `mobile-inbox-live` is never automatic because it intentionally creates a new Admin beta.

## GitHub Guardrails

- `main` is protected and must not be written directly.
- Required status check: `KGG Required Gate / required-gate`.
- Admin beta auto-merge requires green checks plus the explicit `kgg-auto-merge` label.
- Custom GPT write access is limited to workflow dispatch for `.github/workflows/kgg-gpt-preview-gate.yml`.
- GPT Action schema must expose `validate_only`, `publish_preview`, `create_pr`, `publish_admin_beta` and run/job/artifact status reads.
- Current GPT editor setup uses split Actions; paste the API-only schema into `api.github.com` to avoid duplicate `raw.githubusercontent.com` domains.
- Preview writes go only to branch `gpt-preview`; production writes are PR-only and never auto-merge.

## Update Mechanism

- This file is generated by `release-pipeline/kgg_gpt_context.py`.
- Bug-history knowledge is generated by `release-pipeline/kgg_bug_knowledge.py`.
- Source chunk and area-route context is generated by `release-pipeline/kgg_gpt_source_context.py`.
- Custom GPT knowledge pack is generated by `release-pipeline/kgg_custom_gpt_knowledge_pack.py`.
- Run `python release-pipeline/kgg_gpt_context.py --write` after changing version, release, workflow, test or durable project-rule context.
- Run `python release-pipeline/kgg_bug_knowledge.py --write` after changing bug/debug docs, patch lessons or known failure rules.
- Run `python release-pipeline/kgg_gpt_source_context.py --write` after changing `kgg-update/src`, generated source routing rules or modular patch behavior.
- Run `python release-pipeline/kgg_gpt_eval.py` after changing Custom GPT playbook, prompts, expected results, routing or preflight behavior.
- Run `python release-pipeline/kgg_custom_gpt_knowledge_pack.py --write` after changing Custom GPT docs that should be uploaded to GPT Wissen.
- Run `python release-pipeline/kgg_gpt_stabilize.py --write-report` after running a GPT stabilization cycle.
- CI runs GPT context, bug knowledge and source context freshness checks in the required gate so stale GPT context cannot silently merge.
