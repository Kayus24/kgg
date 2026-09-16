---
name: kgg-supervisor
description: Coordinate a small KGG ticket across the shared goal, source-of-truth documents, Fresh Main, and the UI-Lab test loop without changing scope or bypassing human gates.
---

# KGG supervisor

Use this skill to turn a small ticket into an observable, bounded run. Read the
integrated goal and the current Custom GPT control documents before proposing
steps:

- `docs/kgg-ui-lab-v1-goal-prompt.md`
- `docs/kgg-custom-gpt-goal-prompt.md`
- `docs/kgg-custom-gpt-editor-bootstrap.md`
- `docs/kgg-custom-gpt-resource-manifest.json`

Keep Fresh Main, the repository, ticket state, and the editor snapshot as
separate sources of truth. State assumptions explicitly. Plan one smallest
change at a time, require a red observation before changing code, and preserve
the unchanged replay for Round 2. Skills only coordinate; runtime and trusted
MCP boundaries enforce actor, lease, SHA, permission, evidence, and release
gates. Never claim a release, editor update, or ticket write from this skill.

Candidate snapshot hashes (SHA-256): `docs/kgg-ui-lab-v1-goal-prompt.md` =
`acb020319cf38870f3cd54bd5ab3018a3fbd0351f0361fad677d4bd0eb628f82`;
`docs/kgg-custom-gpt-goal-prompt.md` =
`1b497af0c7ba712dc4b0a38aa21c711dcf5aa9ddcb8b7035709d075faffea67e`.
