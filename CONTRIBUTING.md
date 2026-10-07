# Contributing to KGG

Use this file as the human contribution checklist. Repository rules in `AGENTS.md`, runtime routing, app boundaries, fresh source, manifests, and required tests remain authoritative.

## Before changing anything

1. Read `PROJECT_STATE.md` for the current project/router context.
2. Read `AGENTS.md` and `TOOL_ROUTING.md`; then use the runtime-specific routing file.
3. Classify the change:
   - patient app,
   - therapist/admin app,
   - Android,
   - tooling/release,
   - shared contract,
   - documentation only.
4. Open the canonical editable source for that surface.
5. Do not use generated or historical artifacts as patch bases.
6. In a fresh clone/worktree run:
   `python release-pipeline/kgg_hook_guard.py --install`
   and verify with:
   `python release-pipeline/kgg_hook_guard.py --check`

## Source-of-truth rules

- Patient runtime: `index.html`, `patient-*.js`, `collapse-cards.js`, PWA files.
- Therapist/admin editable source: `kgg-update/src/**`.
- `kgg-update/index.html` is generated output and must not be edited directly.
- Candidate identity: `kgg-update/version.json`.
- Canonical published channels/APK metadata: `therapist-app/android_update_manifest.json`.
- `therapist-app/releases/**` is immutable historical evidence, not a patch base.
- Cross-app boundary: `APP_BOUNDARIES.md`.
- Navigation metadata: `docs/repo-map.json`; it never outranks fresh source/manifests.

## Patch discipline

- Work on a branch; do not write app/release/upload changes directly to `main`.
- Make the smallest safe logical change.
- Do not reset unrelated or uncommitted work.
- Do not mix layout cleanup, refactoring, and behavior changes unless the task explicitly requires all of them.
- Preserve existing public hooks/contracts until their replacement has parity and rollback evidence.
- Use synthetic test data only.
- Never place secrets, patient data, credentials, raw private browser output, or API keys in commits, logs, fixtures, screenshots, or PR descriptions.

## Testing

Every code change:
`cmd /c release-pipeline\run-kgg-tests.cmd --level critical`

UI/HTML/layout changes also:
`cmd /c release-pipeline\run-kgg-tests.cmd --suite ui-stability --level regression`

Run the smallest focused regression first, then the required broader gate.

For patient NumPad/compact-value work, include the relevant targeted tests from `docs/repo-map.json` and the current patient feature/regression contract.

## Pull requests

A PR must identify:
- affected surface,
- canonical source used,
- protected contracts / relevant PAT IDs when applicable,
- focused tests,
- required broader gates,
- preview / real-device evidence when needed,
- security/data-boundary impact,
- rollback path.

Do not claim PASS without evidence. Mark blocked, partial, or not-tested states explicitly.

## Generated files

Generated files may be committed when the repository workflow requires them, but edit their source/generator instead of hand-patching output.

GitHub diff classification marks the largest generated source views as generated to reduce review noise. That classification is navigation/review metadata only and does not change runtime behavior.
