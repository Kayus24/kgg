# KGG Gemini Web video QA (no API key)

## Status (2026-10-12)
**READY_FOR_LOGIN / NOT REVIEWED.** No API key, Gemini upload, paid call, production release or patient data. The dedicated Chrome profile was opened read-only at gemini.google.com/app: it shows **Anmelden**. KGG login is not yet established, so a real Gemini verdict cannot be claimed.

**Deterministic video evidence prepared:** Chromium parity artifact 11760587590 from GitHub run 38279941046 (expires 2026-10-15), candidate SHA abc3af3e4253c77b5b777c2ecde28e251193f2b2. It contains 352 hard PASS checks, 40 observations and two verified synthetic phone WebM videos; no unexpected differences. The report's gitSha may identify GitHub's synthetic merge and must not replace candidateSha in the prepared proof.

**Implementation:** the API-free adapter verifies the complete report, source SHA, videos and browser observation/nonce before accepting any advisory verdict. Nine Node built-in negative/positive tests PASS and are registered in the existing Critical test battery. A dedicated Codex MCP entry **kgg_gemini_web** was installed locally with its own Chrome profile (Fahrklar profile unchanged). Execution instructions are in .agents/skills/kgg-gemini-web-video-review/SKILL.md. A real Web review still requires one-time KGG-profile login and verified Pro/Thinking UI; otherwise UNAVAILABLE.

## Reuse
Fahrklar already has a working Playwright MCP browser profile under the Codex server name `fahrklar_gemini_web`. The Fahrklar source of truth is Google Drive document `00_MEMORY – Fahrklar Gemini Video-QA Integration` (ID `1r6r0IHVz3C3LueAoeHHpyoZuFxzH2lHZdLcjLL9OAoc`). Reuse its **prepare → web browser → finalize** architecture, not its traffic-specific prompts.

Do **not** attach a second simultaneous browser to the Fahrklar Chrome profile. For KGG use a separate persistent profile with a separate MCP server and one-time login. Do not copy Chrome cookies, profiles or tokens between projects. Playwright MCP pinned to `@playwright/mcp@0.0.83` as in Fahrklar.

## KGG pipeline
1. Existing `kgg_patient_ui_parity_capture.js` produces synthetic Legacy/React WebM and report.json.
2. Prepare: hash both videos (SHA256), verify the report is PASS, engine=chromium, syntheticOnly=true, regular local files, size caps. Produce a fixed comparison prompt with known expected differences.
3. Web: dedicated Playwright MCP drives gemini.google.com through the user's existing browser subscription. Check login, select available Pro/Thinking mode, upload both files via file chooser, confirm attachment chips, submit prompt. Poll UI state with bounded waits; never infer completion from a fixed sleep. If login, model, upload, quota or UI state is unclear: UNAVAILABLE.
4. Finalize: parse JSON, validate verdict/confidence/findings, bind both SHA256 hashes and scenario ID, and record timestamps. Suspected visual regression means REVIEW_REQUIRED; inconclusive or failed means UNAVAILABLE, never PASS.
5. Cross-check with Playwright's deterministic click, state, pixel, geometry and scroll assertions.
6. A combined report is prepared for one human end-to-end acceptance. Gemini is advisory, never a sole release authority.

## Security / limits
- No API key, no Gemini API billing, no secret in Git/Drive/logs.
- No real patient data. Use only the synthetic fixtures.
- Gemini Web UI may change and subscription quotas may block automation. Respect Google usage rules; do not evade login challenges, rate limits or anti-bot protections.
- No unattended upload before the login/profile and consent preflight succeeds.
- Browser-side video review is NOT a GitHub-hosted CI job unless an authenticated runner is explicitly available. The local Codex/desktop orchestration performs this step; GitHub CI remains deterministic.
- Keep the old API-only reviewer disabled and label its output NOT_CONFIGURED, never PASS.
- No independent second permanent worker/chat.

## Gate
The adapter is NOT COMPLETE until one pair of synthetic WebM videos is submitted and a structured answer is received and validated. A successful Fahrklar smoke test is not evidence of a successful KGG review.
