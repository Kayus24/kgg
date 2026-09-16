---
name: kgg-operations
description: Apply the KGG operational workflow for small admin tickets, including source checks, minimal edits, evidence capture, and safe handoff to the UI Lab runtime.
---

# KGG operations

Follow the operational conventions in `docs/kgg-custom-gpt-knowledge-operations.md`
and the contracts in `docs/kgg-ui-lab-v1-contracts.md`. Inspect status, branch,
Fresh Main, affected files, and relevant docs first. Use synthetic data only.
Prefer a narrow, reversible change and the repository's own test commands. A
browser or editor action is a separate, explicit step and must remain behind
the trusted runtime's session, lease, capability, and permission checks. Record
reads, actions, retries, failures, and artifact references; do not put patient
data, secrets, raw browser output, or credentials into logs or handoffs.

Candidate snapshot hashes (SHA-256): `docs/kgg-custom-gpt-knowledge-operations.md` =
`c96e378fac04ed240e6c30ff88df6bcaf6866c84d9b392890da752e5d469c912`;
`docs/kgg-ui-lab-v1-contracts.md` =
`8c602f0adeab4068b64bcb327a827d4fc36dff08f9a6cf6648e289d880ae9079`.
