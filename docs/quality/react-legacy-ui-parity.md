# KGG Patient UI â€“ Legacy/React parity and video review

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

Runs independently in Chromium and WebKit at **390Ã—844 and 768Ã—1024**, with local synthetic data. The test blocks external network requests.

Artifact layout: `report.json`, full-view PNGs, cropped screenshots, `phone-legacy.webm`, `phone-react.webm`, `tablet-legacy.webm`, `tablet-react.webm`.

`PASS` means all covered checks passed. `FAIL` means a reproducible regression or a recorder issue requiring diagnosis. `INCOMPLETE`/missing artifacts are **not** PASS.

## Gemini setup (one-time, intentionally off by default)

The Gemini review runs in a separate **trusted** GitHub Actions `workflow_run` job, not inside an untrusted PR checkout. This avoids exposing Gemini credentials to PR code.

To enable, an authorized repository administrator must configure these **in GitHub Settings â†’ Secrets and variables â†’ Actions**:

- Repository secret: `GEMINI_API_KEY` â€” generated separately in Google AI Studio.
- Repository variable: `KGG_GEMINI_VIDEO_AUTOREVIEW=true`.
- Environment variable `KGG_GEMINI_VIDEO_UPLOAD_APPROVED=true` records explicit permission for synthetic video uploads. A key alone does not authorize uploads. Configure environment protection/review rules appropriate to the project before enabling.
- Optional repository variable: `KGG_GEMINI_VIDEO_MODEL` (default: `gemini-3.5-flash-lite`).

Do not paste the API key into a chat, PR, code file, or logs. Gemini API charges/quotas are **separate** from a consumer Gemini subscription; review pricing and budgets before enabling.

Only when the parity workflow succeeds for a same-repository PR and auto-review is enabled, the trusted workflow downloads the **data-only Chromium artifact** into `RUNNER_TEMP`, validates it, and sends two synthetic short WebM files to Gemini via inline video input. No Files API persistence. No patient data, real names, access tokens or externally navigated sites may appear in fixtures.

The configured request explicitly samples 5 frames/second and includes bounded approximate checkpoint times, rather than relying on default low-frequency video sampling. The response must be consistent (a no-difference verdict cannot contain major findings); malformed responses and timeouts are inconclusive errors, never automatic passes. The artifact candidate SHA must match the upstream workflow SHA.

Gemini writes an advisory `gemini-review.json` and Markdown summary. Findings must identify unexpected changes and approximate steps/timestamps, distinguish expected header design differences, and mark uncertainty. Gemini can hallucinate or miss fast flicker. It **never** authorizes an automatic merge or changes code itself.

## Security and costs

- CI permissions default to read-only.
- PR capture workflow has **no Gemini secret**.
- Trusted `workflow_run` checks out only reviewed `main` code; untrusted artifacts are treated strictly as data, not executable files.
- Capture artifacts expire after **3 days**, advisory report after **7 days**.
- Separate browser contexts and synthetic test values only.
- No media uploads to Gemini until the user enables the repository variable and secret.
- If no configured secret, Gemini status remains `NOT_CONFIGURED`, not PASS.
- No unattended nightly video review or API cost without explicit repository configuration.

## Acceptance criteria

The component may be proposed for final human acceptance only after current-source required CI, phone/tablet Chromium/WebKit parity and frame/scroll checks pass. Gemini should report `no_unexpected_difference` or its findings must be explained. A low-confidence or missing Gemini result is reported as `INCONCLUSIVE`.

The user then performs a **single overall acceptance**, preferably on the Oppo, focused on realistic training flows and any flagged differences. Merge approval is separate from automated test results. iOS/Safari hardware remains untested until a suitable device/test service exists.

## Verification note (2026-10-11 continuation)

The pure synthetic expected-value oracle and the Gemini handoff have Node built-in negative tests, including matched-but-wrong state, phantom load, unintended cancel commit, false-green model verdict and request authorization. Unit tests mock network; they do not constitute a real Gemini review. The parity gallery reports hard checks separately from observed-only absolute scroll offsets. Normal-motion videos are recorded; static screenshots normalize animation only at checkpoints.
