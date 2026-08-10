# KGG Module Sandbox

This repository is an isolated, local-only modularization sandbox.

- Baseline commit: `e96b259812a44053e48d70c1f198ead01920e8c0`
- Baseline app: `v059 / 1.0.59-ui-scaler-push-canary`
- Baseline HTML SHA-256: `74974ab424eac0cbe1a7c178e188ddff9a0d28d393b49a3c71d8e7a7bc20b509`
- Baseline Admin beta: `r0422`

The repository intentionally has no Git remote. Do not publish from this
sandbox, run a live Mobile-Inbox smoke, build a production APK, or edit public
release manifests. Proven changes must be ported to a fresh production branch
and retested there after explicit approval.

The modular build gate is transactional and writes reports only below
`tmp/kgg-selftest/`. A tracked pre-commit hook runs full certification for
module/build changes. `release-pipeline/kgg_export_handoff.py` can create a
review-only bundle after a clean, fully certified commit; it never publishes.
