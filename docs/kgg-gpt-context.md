# KGG GPT Live Context

This file is the live repo context for the private KGG Update-Agent Custom GPT.
Reload it before answering repo-, version-, patch-, beta-HTML- or test-related questions.
If this file conflicts with `kgg-update/version.json` or `therapist-app/android_update_manifest.json`, trust the JSON source files and tell Max.

## Repository

- GitHub repo: `https://github.com/Kayus24/kgg`.
- Source branch: `main`.
- Primary Admin source: `kgg-update/index.html`.
- Web update metadata: `kgg-update/version.json`.
- Android/Web release manifest: `therapist-app/android_update_manifest.json`.
- Release pipeline docs: `release-pipeline/README.md`.
- Custom GPT playbook: `docs/kgg-custom-gpt-playbook.md`.
- Custom GPT action schema: `docs/kgg-custom-gpt-action-schema.md`.
- Custom GPT negative examples: `docs/kgg-custom-gpt-negative-examples.md`.
- Custom GPT preview runbook: `docs/kgg-custom-gpt-preview-runbook.md`.
- Custom GPT preview report template: `docs/kgg-custom-gpt-preview-report-template.md`.
- Bug-history lessons: `docs/kgg-gpt-bug-lessons.md`, `docs/kgg-gpt-bug-index.json`, `docs/kgg-gpt-patch-patterns.md`.
- Source routing: `docs/kgg-gpt-area-routes.md`, `docs/kgg-gpt-area-routes.json`.
- Source chunks for GPT patch planning: `docs/kgg-gpt-source-index.json` and `docs/kgg-gpt-source/chunk-*.md`.
- GPT eval fixtures: `docs/kgg-custom-gpt-test-prompts.md`, `docs/kgg-custom-gpt-expected-results.md`, `docs/kgg-custom-gpt-test-report.md`.
- GPT preview channel branch: `gpt-preview`, files below `previews/`.
- The Custom GPT may only write through `KGG GPT Preview Gate`; direct repo writes, direct main writes and direct merges stay forbidden.

## Current Versions

- Source web version: v56 / `1.0.56-patient-qr-root-query`.
- Source index URL: `index.html?v=56`.
- Source notes: v056: Patienten-QRs nutzen die Root-Patienten-App mit ?plan=KGGH2-Payload; Root-App importiert Query-Plan direkt.
- Live Admin release: `r0420` / `1.0.56-patient-qr-root-query`.
- Live Admin URL: `https://kayus24.github.io/kgg/therapist-app/releases/web/r0420/admin.html`.
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
- Do not assume the newest local HTML is live.
- If Max asks for a beta, use `KGG GPT Preview Gate` in `validate_only` mode first, then `publish_preview` after green validation; do not create a PR until Max explicitly accepts the preview.
- If Max says the preview is good, use `create_pr` only with the same `request_id` and patch hash.
- If a Preview run fails, report the failed step and the actual error before checking `meta.json` or manifest URLs.
- If the Custom GPT cannot load this context, it must say that repo context is unavailable instead of guessing or asking Max for old basis filenames.

## Required Tests

- Every code change: `cmd /c release-pipeline\run-kgg-tests.cmd --level critical`.
- UI, HTML, flicker, phone, tablet, card drag or layout changes: also `cmd /c release-pipeline\run-kgg-tests.cmd --suite ui-stability --level regression`.
- GPT playbook, routing, payload or bug-knowledge changes: also `python release-pipeline\kgg_gpt_payload_preflight.py --self-test` and `python release-pipeline\kgg_gpt_eval.py`.
- Parser or text-block changes: also `cmd /c release-pipeline\run-kgg-tests.cmd --suite textblocks --level regression`.
- Sync, bank, package or peer changes: also `cmd /c release-pipeline\run-kgg-tests.cmd --suite sync --level regression`.
- Android sync bridge changes: also `cmd /c release-pipeline\run-kgg-tests.cmd --suite native-sync --level regression`.
- `mobile-inbox-live` is never automatic because it intentionally creates a new Admin beta.

## GitHub Guardrails

- `main` is protected and must not be written directly.
- Required status check: `KGG Required Gate / required-gate`.
- Admin beta auto-merge requires green checks plus the explicit `kgg-auto-merge` label.
- Custom GPT write access is limited to workflow dispatch for `.github/workflows/kgg-gpt-preview-gate.yml`.
- Preview writes go only to branch `gpt-preview`; production writes are PR-only and never auto-merge.

## Update Mechanism

- This file is generated by `release-pipeline/kgg_gpt_context.py`.
- Bug-history knowledge is generated by `release-pipeline/kgg_bug_knowledge.py`.
- Source chunk and area-route context is generated by `release-pipeline/kgg_gpt_source_context.py`.
- Run `python release-pipeline/kgg_gpt_context.py --write` after changing version, release, workflow, test or durable project-rule context.
- Run `python release-pipeline/kgg_bug_knowledge.py --write` after changing bug/debug docs, patch lessons or known failure rules.
- Run `python release-pipeline/kgg_gpt_source_context.py --write` after changing `kgg-update/index.html` or source routing rules.
- Run `python release-pipeline/kgg_gpt_eval.py` after changing Custom GPT playbook, prompts, expected results, routing or preflight behavior.
- CI runs GPT context, bug knowledge and source context freshness checks in the required gate so stale GPT context cannot silently merge.
