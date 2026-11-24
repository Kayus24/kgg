# Task: Safe React/shadcn preparation and repository cleanup

Status: ACTIVE
Started: 2026-10-07
Last verified main SHA: `0587ee0933a94ce047521c2d0130d11890d7ef64`

## Goal

Prepare KGG for a gradual, test-protected React/shadcn migration in selected patient-app UI islands while improving repository navigation for humans and LLMs.

No full rewrite.

## Current phase

P2 — semantic repository cleanup and navigation.

This phase changes documentation/metadata only. It must not change patient, therapist/admin, Android, PWA, QR, storage, release, or runtime behavior.

## Allowed scope for P2

- `PROJECT_STATE.md`
- `docs/README.md`
- `docs/repo-map.json`
- task/navigation documentation
- later, if separately verified: lightweight documentation metadata such as generated/history markers

## Out of scope for P2

- `index.html`
- `patient-*.js`
- `collapse-cards.js`
- `service-worker.js`
- `kgg-update/src/**`
- generated `kgg-update/index.html`
- QR/storage/media/scanner/Android behavior
- physical file moves
- release artifact deletion/relocation
- React runtime dependencies

## Safety invariants

- Fresh repository state outranks this task file.
- `KGGDataStore.currentPlan` remains the central plan-state source.
- Patient and therapist/admin surfaces stay separate.
- Generated/historical files are not patch bases.
- No direct app/release write to `main`.
- Existing uncommitted work is never reset.
- Every later product migration must preserve legacy rollback until parity is proven.

## P2 deliverables

- [x] Create `PROJECT_STATE.md` as a short current-state router.
- [x] Create `docs/README.md` as a curated documentation index.
- [x] Create `docs/repo-map.json` as a machine-readable area/source/test map.
- [ ] Validate paths and JSON against current tree.
- [ ] Run secret/diff hygiene.
- [ ] Open documentation-only draft PR.
- [ ] Let Required Gate / Validate Build decide remotely before any merge.

## Next phases after P2

P3: define/implement one UI-input owner without creating a second persistence source.

P4: isolated React/Vite/shadcn skeleton with no visible product behavior change.

P5: Base UI vs React Aria interaction spike.

P6+: shadow mode, first compact NumPad/transfer React island, then gradual expansion only after parity gates.

## Related baseline work

Draft PR #286 addresses an existing Playwright timing-contract issue in the compact-transfer baseline. It is intentionally separate from this documentation task.

Do not merge either PR automatically from this task.
