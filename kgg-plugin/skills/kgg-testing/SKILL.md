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

Candidate snapshot hashes (SHA-256): `docs/kgg-custom-gpt-knowledge-testing.md` =
`526435598da7fdf5a2081588cf18103c839389ea81fc8109ab8e7142a6348688`;
`release-pipeline/kgg_test_battery.py` =
`4edb060acb989bd93a4941085b627f56d168801495b3e30b5e6e8a9b3eb27913`.
