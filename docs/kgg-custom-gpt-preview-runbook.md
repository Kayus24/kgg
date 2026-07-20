# KGG Custom GPT Preview Runbook

Use this order for every Preview/Test-HTML/Test-APK request.

Canonical order: `dispatch -> run status -> logs -> tests -> artifact -> meta -> html -> Test-APK -> Max acceptance -> Admin beta merge`.

## Run order

1. Load live context, bug lessons, action schema, negative examples and area routes.
2. Build the smallest modular v2 payload with `patch_content`; do not send `replace_exact`, `operations` or direct `kgg-update/index.html` paths.
3. Dispatch `validate_only` first.
4. If `validate_only` fails, report the failed step and exact error. Do not publish.
5. If validation succeeds, dispatch `publish_preview`.
6. Use `listKggPreviewGateRuns` and the workflow run name/request id to find the GitHub run.
7. Use `getKggPreviewGateRun` until `status` is `completed`.
8. If the run fails, use `getKggPreviewGateJobs` and report the failed job/step and exact visible error context.
9. If the run succeeds, verify artifact, `meta.json` and HTML URL.
10. If the request targets the Test-APK, verify that the Preview/Test-APK channel is updated.
11. Tell Max that the Preview/Test-APK is ready for his review.
12. If Max rejects the Test-APK result, document `human_preview_fail`, add/update the regression fixture and restart at `validate_only`.
13. Use `create_pr` only after Max explicitly accepts the same Preview and only a PR is requested.
14. Use `publish_admin_beta` only when Max explicitly wants a real Haupt-App/Admin-Beta push. Success requires a merged `[admin-beta]` PR, updated `android_update_manifest.json` on `main`, and HTTP 200 for the new Admin HTML.

## Required verified fields

Every successful Preview report must include:

- `run_id`
- `conclusion`
- `failed_step` or `none`
- `meta_url`
- `html_url`
- `artifact_name`
- Test-APK/channel status when APK preview is involved
- Max acceptance status before any PR
- Admin beta merge status when Haupt-App push is involved

## Failure wording

Use direct wording:

- `Keine Preview verfuegbar: Run rot.`
- `Failed step: <step name>.`
- `Fehler: <exact error>.`
- `CI-Tooling fehlt: <tool>.`

Do not use vague wording:

- `kommt gleich`
- `Manifest wartet noch`
- `wahrscheinlich noch nicht sichtbar`

These are allowed only when the run is still actually in progress.

If `critical` fails with `Missing tool pdftoppm`, `Missing tool pdfinfo`, `poppler-utils` or another runner dependency, classify it as `ci_tooling`. Do not blame the UI patch until the failed subtest log proves an app assertion failed.
