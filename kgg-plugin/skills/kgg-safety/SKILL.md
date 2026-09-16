---
name: kgg-safety
description: Enforce KGG privacy, authorization, provenance, and release-boundary rules while skills and UI-Lab runners handle synthetic ticket scenarios.
---

# KGG safety

Read `docs/kgg-custom-gpt-knowledge-safety.md` and the repository's privacy
rules before handling a ticket. Treat skills as guidance, never as the security
boundary: trusted runtime/MCP code must enforce actor binding, lease validity,
permissions, Fresh Main and app SHAs, replay protection, append-only events,
and tamper-evident evidence. Use synthetic data exclusively. Refuse or pause
when a request would expose patient data, secrets, raw browser/QR content, or
cross a PR, merge, live, editor, or release gate. Explain the failed gate and
return a bounded remediation or escalation plan; do not silently weaken a
check.

Candidate snapshot hashes (SHA-256): `docs/kgg-custom-gpt-knowledge-safety.md` =
`886d16e8b5776ad41979fb2d075c28e9b4eb24341026b4b70b64b40d669c1af6`;
`release-pipeline/kgg_ui_lab_contract.py` =
`4ea5e4a411b7b6efceb256023d3d2cc56ceb9fbf3003869600e48a2ad8076cd7`.
