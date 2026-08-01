# KGG Patient GPT Live Context

Authoritative live repository context for the private KGG Patienten-App Update-Agent.
Reload before every diagnosis involving current code and before every Preview, PR or live request.

## Repository

- Repository: `https://github.com/Kayus24/kgg`, branch `main`.
- Live patient app: `https://kayus24.github.io/kgg/`.
- Current patient PWA version from `service-worker.js`: `v72`.
- Recovery: `https://kayus24.github.io/kgg/update-recovery.html`.
- Isolated preview host: `https://kayus24.github.io/kgg-patient-preview/`.
- Pre-authorized Patient Preview workflow: `.github/workflows/kgg-patient-gpt-preview-only.yml`.
- Consequential Patient PR/live workflow: `.github/workflows/kgg-patient-gpt-preview-gate.yml`.
- Guard implementation: `release-pipeline/kgg_patient_gpt_write_gate.py`.
- Private project memory: `Kayus24/kgg-project-memory`.
- Private cross-agent coordination: `coordination/index.json` and guarded append-only threads.

## Patient Source Files

- `APP_BOUNDARIES.md`
- `index.html`
- `service-worker.js`
- `update-recovery.html`
- `manifest.json`
- `collapse-cards.js`
- `numpad-ui-fix.js`
- `manifest-v64.webmanifest`
- `patient-card-progress.js`
- `patient-card-settings.js`
- `patient-day-history.js`
- `patient-extra-info-display.js`
- `patient-install-guide.js`
- `patient-install-prompt.js`
- `patient-ios-large-pad-force.js`
- `patient-last-value-hints.js`
- `patient-media-retry-cache_v2.js`
- `patient-multiplan-db.js`
- `patient-numpad-card-guard.js`
- `patient-numpad-visibility-fix.js`
- `patient-plan-delete.js`
- `patient-qr-fullscreen.js`
- `patient-set-summary-groups.js`
- `patient-start-scan.js`
- `patient-start-values-day1.js`
- `patient-ui-micro-polish.js`
- `patient-version-label.js`

## Hard Rules

- Work in German, make one smallest safe patch and preserve existing hooks.
- Never write directly to `main`; use exact Preview hash, PR and protected live approval.
- Reads, validate_only, publish_preview, evidence checks and safe coordination responses are pre-authorized; do not ask after every step.
- Patient PR/live requires Max' exact phrase `Gut für PAT live`.
- Patient output never exposes raw JSON, Base64, KGGH2/KGGD1 or debug payloads.
- Preview fixtures are synthetic and contain no patient data.
- Version, cache name, Recovery release, version label and changelog are owned by the gate.
- QR/hash/storage changes use `risk_class=interface` and stay backward compatible.
- Breaking interface changes, therapist app, PDF and Android/APK stay outside this agent.
- A Custom GPT supplies the Preview URL but does not claim to control the Codex in-app browser.

## Required Evidence

- `validate_only` before `publish_preview` with identical payload.
- Successful workflow run, jobs, artifact, meta.json, Preview URL and Recovery URL.
- Max accepts the Preview in the in-app browser before PR or live mode.
- Live mode additionally needs Required Checks, patient-live Environment approval, merge and live version verification.
