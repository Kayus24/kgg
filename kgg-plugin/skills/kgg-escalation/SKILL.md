---
name: kgg-escalation
description: Prepare a bounded Bruder-GPT fallback handoff for an unrecoverable KGG test failure and safely apply only an approved tactical response.
---

# KGG escalation

Use `release-pipeline/kgg_ui_lab_runtime.py`,
`release-pipeline/kgg_brain_relay_worker.py`, and
`docs/kgg-ui-lab-v1-goal-prompt.md` as the escalation contract. Classify the
failure first. Retry only transient failures within the declared budget; send
protected failures directly to a maximum-required pause. A Bruder handoff is a
local, user-confirmable queue item with safe summaries and evidence references,
not an automatic external message and not a new lead agent.

Accept from the Bruder response only tactical fields such as retry budget,
timeout, step order, evidence fields, or a named Quick Flow. Reject scope,
goal, safety, permission, hash, test-removal, release, recursive-agent, or
external-send changes. Re-run the failed case and the unchanged replay after an
accepted tactical adjustment; otherwise return `MAX_REQUIRED` with the exact
blocking evidence.

Candidate snapshot hashes (SHA-256): `release-pipeline/kgg_ui_lab_runtime.py` =
`b3c845b02341b0773a4a922c98feb6f3085993cf7c2e76f58c4da221fa54154f`;
`release-pipeline/kgg_brain_relay_worker.py` =
`33aa926607e46fa0525dff72637c6d1976562c6227ef6134ce6077b18b57b4bf`.
