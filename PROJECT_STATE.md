# PROJECT_STATE

Last verified: 2026-10-07
Verified main SHA: `0587ee0933a94ce047521c2d0130d11890d7ef64`

## Goal

KGG is a combined repository for the patient PWA, therapist/admin app, Android wrapper, release/test tooling, KGG plugin/UI-Lab, and immutable release evidence.

The current modernization goal is to improve repository readability for humans and LLMs and to prepare a low-risk React/shadcn migration for selected patient-app UI islands without changing existing product contracts by accident.

## Current state

- Patient app editable source: `index.html`, `patient-*.js`, `collapse-cards.js`, `service-worker.js`, and related PWA assets.
- Therapist/admin editable source: `kgg-update/src/**`.
- Therapist candidate artifact: generated `kgg-update/index.html`; do not patch directly.
- Candidate identity: `kgg-update/version.json` currently reports v95 / `1.0.95-cockpit-responsive-entry`.
- Canonical live/release identity: `therapist-app/android_update_manifest.json`; do not infer live state from this file if the manifest has changed since Last verified.
- Historical immutable release evidence: `therapist-app/releases/**`.
- Patient/therapist boundary contract: `APP_BOUNDARIES.md`.
- Runtime tool routing: `TOOL_ROUTING.md` plus the runtime-specific ChatGPT/Codex file.

## Active work

`tasks/2026-10-07-safe-react-shadcn-repo-cleanup.md`

Current phase: repository navigation / machine-readable source map before any React product migration.

Related draft PR: #286 is a test-only baseline-contract fix and is not part of this documentation branch.

## Current blockers / gates

- Do not start React product writes until the patient NumPad/compact-transfer baseline is accepted for the working branch or explicitly carried as a known baseline condition.
- Keep patient and therapist/admin source ownership separate.
- Any product code change must follow the tests required by `AGENTS.md`.
- Documentation files are not a substitute for fresh repository, manifest, PR, or CI state.

## Canonical sources

1. Fresh `main` and `AGENTS.md`.
2. `TOOL_ROUTING.md` plus the runtime-specific routing file.
3. `APP_BOUNDARIES.md`.
4. Active source/manifests listed above.
5. `docs/repo-map.json` for navigation only.
6. `Kayus24/kgg-project-memory` for durable decisions/rationale, never live app state.
7. Drive for long-running plans and work logs, never live code/release state.

## Tests

Primary entry point:
`cmd /c release-pipeline\run-kgg-tests.cmd`

See `release-pipeline/README.md` and `AGENTS.md` for required levels/suites.

## Parked

- Full patient-app React rewrite.
- Physical movement of patient root files.
- Relocation/removal of immutable historical releases.
- Broad replacement of existing storage, QR, scanner, service-worker, media, or Android contracts.

These parked items must not influence current work unless explicitly reactivated.

## Retrieval notes

Read the smallest relevant source first. Prefer `docs/README.md` and `docs/repo-map.json` for orientation, then open the actual canonical source. Treat historical docs and release artifacts as evidence, not current instructions.
