---
name: kgg-testing
description: Drive KGG red-to-green, unchanged replay, negative, and regression loops and report deterministic evidence for UI-Lab and Custom GPT comparisons.
---

# KGG testing

Use `docs/kgg-custom-gpt-knowledge-testing.md`,
`docs/kgg-custom-gpt-expected-results.md`, and
`release-pipeline/kgg_test_battery.py` as the testing authorities. For every
step capture the Fresh-State expectation, reproduce the red case, isolate the
root cause, make the smallest change, run the narrow test, then the
change-aware regression and full Critical gate. Repeat the original case with
no changes for Round 2. Include failure class, timing, retries, runner,
application SHA, device/viewport, and evidence hashes. Add negative coverage
for missing capability, stale SHA, expired lease, replay, malformed evidence,
and unavailable MCP; a green result is not a waiver of a failed safety gate.

## Fast single-turn UI-Lab control loop

Treat one authorized user test request as one bounded run: proceed through
Fresh Main/readiness, start_ui_session, observe_visual_state, one permitted
execute_visual_action, get_test_evidence, and get_session_status without
asking for "weiter" after each step. In a real-browser session, prefer
the exact stable labels returned in observation.controls; do not invent a
label, coordinates, screenshot interpretation, or a successful state.
Check a fresh observation ID, unique visible enabled target, expected
before/after state, and independently reread evidence. Require a confirmed
PASS action plus distinct before/after screenshot hashes; otherwise report
FAIL or BLOCKED with the exact failing gate in the same response. Use at
most one causally distinct recovery attempt. An UNKNOWN state, missing
image content, failed tool binding, or exhausted lease is never PASS.
No unapproved app writes, patient data, push, merge, deploy or host rollout.
A completed local loop does not certify the installed ChatGPT plugin or
physical devices; those require separate explicit verification.

Candidate snapshot hashes (SHA-256): `docs/kgg-custom-gpt-knowledge-testing.md` =
`526435598da7fdf5a2081588cf18103c839389ea81fc8109ab8e7142a6348688`;
`release-pipeline/kgg_test_battery.py` =
`4edb060acb989bd93a4941085b627f56d168801495b3e30b5e6e8a9b3eb27913`.
