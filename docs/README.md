# KGG Documentation Index

Status: active navigation document
Last verified: 2026-10-07
Verified main SHA: `0587ee0933a94ce047521c2d0130d11890d7ef64`

This file is a router, not a runtime source of truth. When a linked source conflicts with fresh code, manifests, or repository rules, the fresh canonical source wins.

## Start here

- Project snapshot and active work: `../PROJECT_STATE.md`
- Repository/agent rules: `../AGENTS.md`
- Runtime routing: `../TOOL_ROUTING.md`
- Patient vs therapist/admin boundary: `../APP_BOUNDARIES.md`
- Machine-readable repository map: `repo-map.json`
- Test/release entry points: `../release-pipeline/README.md`

## Patient app

Editable runtime surface:
- `../index.html`
- `../patient-*.js`
- `../collapse-cards.js`
- `../service-worker.js`
- PWA manifests/assets in repository root

Important active contracts:
- `../PATIENT_LINK_STANDARD_v1.md`
- `../CHANGELOG_PATIENT_APP.md`

Do not use generated GPT source chunks as the first patch source.

## Therapist/admin app

Editable source:
- `../kgg-update/src/**`

Generated candidate:
- `../kgg-update/index.html` — generated, do not patch directly
- `../kgg-update/version.json` — candidate identity

Canonical release/live metadata:
- `../therapist-app/android_update_manifest.json`

Historical aliases and immutable releases are not patch bases.

## Android

- Source: `../android-wrapper/**`
- Release/test integration: `../release-pipeline/**`

## KGG plugin / UI-Lab / browser bridge

- Implementation and contracts: `../kgg-plugin/**`
- GPT/UI-Lab knowledge and generated source indexes: `kgg-gpt-*.md`, `kgg-gpt-*.json`, and generated source directories

Generated/retrieval-oriented source folders such as `kgg-gpt-source/**` and `kgg-patient-gpt-source/**` should not be treated as primary editable application source.

## Design system

- `design-system/README.md`
- `design-system/design-tokens.json`
- `design-system/gesture-contract.md`

Use these as existing design/gesture evidence before introducing new React/shadcn tokens or interaction primitives.

## Testing and release

- Primary test documentation: `../release-pipeline/README.md`
- Required repository rules: `../AGENTS.md`
- Workflows: `../.github/workflows/**`

Any UI/layout change must preserve the relevant patient/therapist regression gates and use the current repository rules.

## Debug / lessons / history

- Curated bug-debug index: `bug-debug/README.md`
- Individual bug/debug records: `bug-debug/**`
- Older context/history: `archive/**`
- Immutable release artifacts: `../therapist-app/releases/**`

History is evidence. It is not current instruction unless a fresh source explicitly re-adopts it.

## Generated or heavy documentation

The following areas may be large or generated and should not be loaded recursively by default:
- `kgg-gpt-source/**`
- `kgg-patient-gpt-source/**`
- changelog archives
- immutable therapist release artifacts

Use `.rgignore`, explicit paths, and the machine-readable repo map to keep searches bounded.
