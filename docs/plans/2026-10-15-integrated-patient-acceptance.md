# KGG integrated patient acceptance ? 2026-10-15

Goal: consolidate verified Legacy/P7/P8 work into one pinned, synthetic-only acceptance candidate. No main merge or live activation is authorized by this plan.

## Architecture and scope
- Base: P8 #322 ebe4670fd7c24cf7e4d52fa468c96a167b319f8d; main a237aa2a9737a5b83eb6bb069f820cb8ce8653fd.
- Reuse old comprehensive acceptance from #320 and test-only children #324?327. Preserve newer English code and P8 recorder. Fix #317 and candidate #328 require exact regression evidence before integration.
- Legacy owns training, buffer, commits, QR and persistence. P8 stays URL opt-in; no independent business state.
- Preserve existing report generators, figure/video evidence, pinned SHA/browser identity, fail-closed gates. Never turn incomplete reports into a success badge.

## Ordered work
1. Refresh refs, copy isolated source/test changes with three-way comparison, preserve dirty prior workspaces.
2. Demonstrate active-delete and synchronous-English regressions, apply minimal existing fixes, regenerate only required resources.
3. Extend existing full-acceptance contract tests for required three-mode suites and execution evidence before extending reporter.
4. One bounded runner: original core capture first, old parity proofs, settings/progression/scanner/preview-lightbox, retained regression suites. Separate logs, finite per-process deadlines, resumable check manifest.
5. Consolidate all 111 unique manifest IDs: comparison scope, existing regression mapping, unresolved hardware/backlog; no arithmetic-only PASS counts.
6. Test shared candidate, source/build alignment, Critical and UI stability, browser acceptance. Publish only an isolated Draft/preview after checks; retain exact test provenance.
7. Reconcile/report true blockers: real-device availability, #308 grey frames, hardware camera and any persistent failures. Supply one grouped acceptance rather than repeated per-feature requests.

## Boundaries
Generated preview uses synthetic plans. SW-blocked tests are not offline certification. WebKit is not physical iPhone Safari. No production patients, secrets, paid Gemini inference, or admin-app releases.

## Recovery
Source refs are in docs/quality/patient-integration-sources-20261015.json. Private work directory is separate from all prior dirty clones. Every long test returns a PID, writes a log and has a timeout; inspect state before retrying. Final result requires current candidate SHA and matching evidence, never old branch CI alone.
