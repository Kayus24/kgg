# KGG Custom GPT Preview Runbook

Use this order for every Preview/Test-HTML/Test-APK request.

Canonical order: `dispatch -> run status -> logs -> tests -> artifact -> meta -> html -> Test-APK -> Max acceptance`.

## Run order

1. Load live context, bug lessons, action schema, negative examples and area routes.
2. Build the smallest `replace_exact` payload.
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
13. Use `create_pr` only after Max explicitly accepts the same Preview.

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

## Failure wording

Use direct wording:

- `Keine Preview verfuegbar: Run rot.`
- `Failed step: <step name>.`
- `Fehler: <exact error>.`

Do not use vague wording:

- `kommt gleich`
- `Manifest wartet noch`
- `wahrscheinlich noch nicht sichtbar`

These are allowed only when the run is still actually in progress.
