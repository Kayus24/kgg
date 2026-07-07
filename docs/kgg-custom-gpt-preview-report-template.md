# KGG Custom GPT Preview Report Template

Use this exact report shape after Preview-Gate runs.

## Success

```text
base file used: main/kgg-update/index.html, version <version>
changed file: kgg-update/index.html
request_id: <request_id>
run_id: <run_id>
conclusion: success
failed_step: none
artifact_name: <artifact_name>
meta_url: <meta_url>
html_url: <html_url>
test_apk_channel: <updated|not involved>
max_acceptance: <accepted|pending>
admin_beta_pr: <url|not requested>
admin_beta_merge: <merged|not requested|pending>
admin_html_url: <url|not requested>
visible_scaler_canary: <verified|not involved|pending>

changes:
- <short behavior summary>

smoke test:
- critical: green
- ui-stability regression: green
- Preview APK build: green
- artifact/meta/html: verified
- Test-APK review: pending Max acceptance, unless Max already accepted
- Admin beta merge: verified when `publish_admin_beta` was requested
- Admin HTML: HTTP 200 when `publish_admin_beta` was requested

risks:
- <specific risk>
- not touched: <protected areas>
```

## Failure

```text
base file used: main/kgg-update/index.html, version <version>
changed file: none published
request_id: <request_id>
run_id: <run_id>
conclusion: failure
failed_step: <failed step>
artifact_name: none
meta_url: not available
html_url: not available
test_apk_channel: not updated
max_acceptance: not requested
admin_beta_pr: not created
admin_beta_merge: not attempted
admin_html_url: not available
visible_scaler_canary: not verified

smoke test:
- not green; stopped at <failed step>

error:
- <exact error>

next step:
- <specific correction>
```
