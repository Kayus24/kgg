# Historical implementation plan ? deterministic Legacy/React parity

This checklist documents the original preparation work for PR #303; it is not
an ongoing merge or deployment instruction. The authoritative current status
comes from GitHub PR/commit checks and docs/quality/react-legacy-ui-parity.md.

Implemented deterministic coverage: synthetic phone/tablet Chromium and WebKit,
12 fixed checkpoints, independent expected values, React/Legacy click parity,
field selection, transfer, left/right, seconds, reload, frame/scroll, screenshot,
video and offline HTML evidence. Reuses PAT-PAIN-004 from main.

Security decision at review: the secret-free parity job runs for same-repo and
fork PRs. The privileged Gemini API workflow and its untrusted artifact uploader
were removed from PR #303. Separate opt-in Gemini Web preparation remains in
PR #305 and cannot be called an acceptance pass without a real user-approved test.

Before integration: exact-candidate Required Gate, parity CI, Build, review threads,
and changes vs fresh main must all pass. Automated parity does not replace final
physical phone/iPhone tests or approve any patient-app live release.
