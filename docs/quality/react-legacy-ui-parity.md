# KGG Patient UI – Legacy/React parity and video review

Status: **candidate / not an acceptance certificate**
First baseline: `main` at `b223fcfe6c5a27d32def04542df2d008cdec897e`

## Goal

Move repeated micro-acceptance checks from the human reviewer into a deterministic CI workflow, so the final human test is a single **end-to-end acceptance**. A passing result never proves all possible behaviors are safe.

The current recorder covers the **patient NumPad pair/transfer journey, center transfer, LR-side isolation, seconds-only input and stored values after reload**, not the entire patient app or therapist app. Extend by explicit feature IDs and synthetic scripts; do not treat it as full coverage until every required workflow has a grounded test.

## Test pyramid

**Click behavior (hard gate):** Playwright drives identical steps in independent Legacy and React browser contexts. It compares training-state writes, active field, drafts/dirty flags, displayed inputs, transfer options, pad state, scroll and geometry.

**Visual (hard gate for unchanged regions):** Full viewport PNG screenshots support review; the legacy NumPad buttons and OK/Cancel area are cropped and compared pixel by pixel. The intentionally redesigned React header is **not** required to match Legacy pixels. Accept only explicitly documented visual changes.

**Video (evidence and additional diagnostic):** Playwright records short WebM videos for each variant at phone and tablet sizes. The automated Gemini review compares only the **phone Legacy and React clips** as an advisory verdict; transient single-frame flashes can escape low-fps model video sampling and remain covered by deterministic frame/scroll tests.

**Human (final gate):** The user receives one aggregated report, a preview, and outstanding/high-confidence visual findings. The user performs one full-flow acceptance after the automatic gates pass, not one approval per component.

## Current deterministic scripted steps

On a synthetic KGGH2 plan with two sets and prior values 15 kg / 12 Wdh:
1. Open kg, inspect three transfer segments.
2. Switch to Wdh; pad stays open.
3. Transfer 12 Wdh; the remaining kg segment is offered.
4. Transfer 15 kg and close the completed pair.
5. Open second-set kg, enter 7, backspace, explicit 0.
6. Cancel, ensuring no accidental commit.
7. Reopen kg, explicitly enter 0, confirm OK.
8. Transfer both prior values with the center button (25 kg / 9 Wdh).
9. Transfer left values (11 / 8), verify right is still empty; then transfer right values (13 / 9) independently.
10. Transfer 45 seconds without creating a weight value.
11. Reload and verify all expected stored values persist.

Each checkpoint has an independent expected-result oracle; equal but wrong Legacy/React outputs are rejected. Visible React values and buttons are checked against the authoritative display. A normal-motion, per-frame sample of the kg/Wdh switch checks that the pad stays open and neither window nor internal main scroll jumps. This is DOM/geometry frame evidence, not a guarantee against every compositor-only flash.

Per-set pain was already fixed and covered by PR #304 / PAT-PAIN-004 on main; the existing regression is reused in both browser jobs instead of building a duplicate pain subsystem.

Runs independently in Chromium and WebKit at **390×844 and 768×1024**, with local synthetic data. The test blocks external network requests.

Artifact layout: `report.json`, full-view PNGs, cropped screenshots, `phone-legacy.webm`, `phone-react.webm`, `tablet-legacy.webm`, `tablet-react.webm`.

`PASS` means all covered checks passed. `FAIL` means a reproducible regression or a recorder issue requiring diagnosis. `INCOMPLETE`/missing artifacts are **not** PASS.

## Optional video review: separate workstream

This pull request is deliberately limited to a **deterministic, secret-free parity recorder**.
It does not install a trusted GitHub workflow_run uploader, accept Gemini API keys,
make external video-analysis requests, or automatically upload media to third parties.
The offline HTML, PNG and WebM artifacts are available for local manual review.

Optional subscription-based Gemini Web video analysis is tracked separately in
[PR #305](https://github.com/Kayus24/kgg/pull/305). It is NOT_CONFIGURED
until a dedicated browser profile, login, user-approved upload and complete result
are independently verified. It is never a required CI pass or merge authority.
No patient data may be used for these synthetic test journeys.

## Security and costs

- CI runs with read-only repository permissions, including on fork pull requests.
- No API keys, protected environment secrets, paid model calls or external video uploads.
- External network requests are aborted by the synthetic browser recorder.
- Reports, screenshots and videos expire after 3 days.
- Separate browser contexts isolate Legacy and React synthetic fixtures.
- Missing artifacts or inconclusive evidence are never recorded as a pass.

## Acceptance criteria

The component may be proposed for final human acceptance only after current-source
required CI, phone/tablet Chromium/WebKit parity and frame/scroll checks pass.
Optional external video review is outside this test-only PR, is not a merge
prerequisite, and may not override deterministic failures.

The user then performs a **single overall acceptance**, preferably on the Oppo, focused on realistic training flows and any flagged differences. Merge approval is separate from automated test results. iOS/Safari hardware remains untested until a suitable device/test service exists.

## Verification note (2026-10-11 continuation)

The synthetic expected-value oracle has Node built-in negative tests for
matched-but-wrong state, phantom load and unintended cancel commits. The parity
gallery reports hard checks separately from observed-only absolute scroll offsets.
Normal-motion videos are recorded; static screenshots normalize animation only at
checkpoints. No Gemini/video-upload unit or integration test is included in this
deterministic parity PR.
