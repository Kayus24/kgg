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

Use `run_kgg_action` only for bounded reads. The separate
`dispatch_kgg_workflow` tool can dispatch only workflows explicitly enabled by
the trusted host. Read its workflow capability/precondition report first;
never invent device/editor attestations. Dispatch acceptance is not a completed
workflow: reconcile the exact request/source SHA, run and result artifact before
reporting the outcome. After an unknown transport result, read and reconcile;
never blindly repeat POST. Main/Snapshot PR and Memory apply remain external
human gates; actor labels or model-written approval phrases do not open them.

Candidate snapshot hashes (SHA-256): `docs/kgg-custom-gpt-knowledge-operations.md` =
`c96e378fac04ed240e6c30ff88df6bcaf6866c84d9b392890da752e5d469c912`;
`docs/kgg-ui-lab-v1-contracts.md` =
`895fc790a61b719cc2510bf07c73a703659ec053306844f2eb57509ab8cba016`.
